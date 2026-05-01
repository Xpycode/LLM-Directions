# Subprocess fire-and-collect (`waitUntilExit` + `readDataToEndOfFile`)

**Source:** `1-macOS/AvidMXFPeek/` — `BMXWrapper.runAndCollect(at:arguments:)` (2026-04-20)

For short-lived subprocess invocations where you need a single discrete stdout blob at the end — not streaming progress — use `waitUntilExit() + readDataToEndOfFile()`, not `readabilityHandler`. Simpler code, no handler-cleanup dance, no tail-byte race at the process-termination boundary.

---

## When to use

Your code matches all of:
- Invoke a subprocess with argv (e.g. `ffprobe`, `exiftool`, `openssl`, `sha256sum`, `xcrun`, `git rev-parse`, anything shell-ish)
- Run time is short (milliseconds to a few seconds)
- Output is bounded and consumed *as a whole* after the process finishes — you don't want progress lines as they print
- You care about the exit code and stderr on failure, but not about interleaving with ongoing UI

Typical shapes:
- Reading file metadata (`ffprobe -show_format`, `exiftool -json`, `mediainfo --Output=JSON`)
- One-shot hash / checksum calls (`shasum`, `md5`, `crc32`)
- Git state lookups (`git rev-parse`, `git status --porcelain`)
- Codec / format probes
- Cryptographic signing / verification with a single input

**Don't use this pattern** when you're running a long subprocess and need to stream logs or update a progress bar as the child writes — that's what `readabilityHandler` is actually for. Examples where the handler is right: `ffmpeg` transcoding with `-progress pipe:`, `rsync` with `--info=progress2`, `xcodebuild` with live log tailing.

---

## The pattern

```swift
/// Run a subprocess to completion, returning stdout as Data.
/// Throws on process-launch failure OR on non-zero exit (includes stderr).
/// `Task.detached` keeps the blocking reads off the caller's actor.
private func runAndCollect(at executable: URL, arguments: [String]) async throws -> Data {
    try await Task.detached(priority: .userInitiated) { () throws -> Data in
        let process = Process()
        process.executableURL = executable
        process.arguments = arguments

        let stdoutPipe = Pipe()
        let stderrPipe = Pipe()
        process.standardOutput = stdoutPipe
        process.standardError = stderrPipe

        try process.run()
        let stdoutData = stdoutPipe.fileHandleForReading.readDataToEndOfFile()
        let stderrData = stderrPipe.fileHandleForReading.readDataToEndOfFile()
        process.waitUntilExit()

        if process.terminationStatus != 0 {
            let message = String(data: stderrData, encoding: .utf8)?
                .trimmingCharacters(in: .whitespacesAndNewlines)
                ?? "exit \(process.terminationStatus)"
            throw SubprocessError.failed(message)
        }
        return stdoutData
    }.value
}
```

Call site:
```swift
let data = try await runAndCollect(at: ffprobe, arguments: [
    "-v", "error", "-show_format", "-show_streams", "-of", "json", url.path
])
let report = try JSONDecoder().decode(FFProbeReport.self, from: data)
```

---

## Why this beats `readabilityHandler` for this shape of work

`readabilityHandler` + `terminationHandler` is the textbook "stream subprocess output" pattern. It's correct for long-running processes where you genuinely want each chunk as it arrives. But for fire-and-collect it adds real problems:

### 1. Tail-byte race
`terminationHandler` can fire before `readabilityHandler` has delivered the process's final write. On macOS, if you do:

```swift
pipe.fileHandleForReading.readabilityHandler = { handle in
    collected.append(handle.availableData)
}
process.terminationHandler = { _ in
    pipe.fileHandleForReading.readabilityHandler = nil   // ← closes the door
    continuation.resume(returning: collected)
}
```

there's a window where: child exits → kernel flushes stdout → terminationHandler fires → you nil the handler → the final `availableData` delivery never happens. Small stdouts (< pipe buffer ≈ 64 KB on macOS) usually fit in one read and get it right anyway; larger outputs silently lose their tail.

`readDataToEndOfFile()` reads synchronously until the pipe hits EOF. The child exits → kernel closes the write end → `read(2)` returns 0 → we're done. No race.

### 2. Handler-cleanup boilerplate
Every `readabilityHandler` path needs the same dance: set handler → ensure it's nil'd on success, on failure, and on launch-error. Miss any one and you leak the handler closure (which captures `self` through the collector). Fire-and-collect needs none of that.

### 3. Simpler reasoning
10 lines vs. 40. No `@unchecked Sendable` data-collector class with its own lock. No `CheckedContinuation` callback juggling. Easier to read, easier to test, easier to reason about cancellation and error paths.

### 4. Same performance for this workload
The subprocess does the same work either way. The only thing that changes is how you read stdout. For bounded outputs of a few KB to a few MB, `readDataToEndOfFile` finishes instantly after `waitUntilExit` returns.

---

## Threading

`Task.detached(priority: .userInitiated)` matters here:

- `readDataToEndOfFile()` **blocks the calling thread** until EOF. If you call `runAndCollect` from `@MainActor`, the main thread is pinned for however long the subprocess takes. That's unacceptable for any call > ~16 ms.
- `waitUntilExit()` blocks too — it's a `wait(2)` syscall.
- `Task.detached` moves both onto a cooperative-thread-pool worker. The caller's actor (main, or any custom actor) stays responsive.
- `.userInitiated` priority matches "user is waiting for this result" — you're not running it in the background, you're running it because the UI asked for it.

If you're fanning out many of these in parallel (as `withTaskGroup` → per-task `runAndCollect`), the detached task inside each `withTaskGroup` subtask is fine; `withTaskGroup` already bounded the concurrency.

---

## Error shape

Fire-and-collect has two error cases:
1. **Process couldn't launch** — `process.run()` throws. Usually `ENOENT` (bad executable path) or permissions.
2. **Process ran but exited non-zero** — `terminationStatus != 0`. Include stderr in the error message so the caller can show a useful diagnostic.

The pattern throws both through the same `throws` path. Callers that want to convert errors to values (e.g. "one bad file shouldn't kill a batch scan of 10k files") wrap with `do/catch` and return a domain-specific `.failed(reason:)` variant:

```swift
func info(url: URL) async -> MXFHeaderInfo {
    do {
        let data = try await runAndCollect(at: ffprobe, arguments: [...])
        return FFProbeMapper.map(jsonData: data, fileURL: url, ...)
    } catch {
        return .failed(url: url, reason: error.localizedDescription)
    }
}
```

---

## Stderr handling choices

- **Include on failure only** (the pattern above) — right for metadata probes: stderr only has content when something went wrong
- **Include always** — useful for tools that write warnings to stderr even on success. Concatenate to stdout before returning, or return a tuple.
- **Drain and discard** — unusual, but you still need to drain stderr. If you never read it and the child writes > 64 KB to stderr, the pipe fills, the child blocks on write, and `waitUntilExit` never returns. **Always read both pipes.**

---

## Cancellation

Per-call cancellation isn't built into this pattern. If the caller's `Task` is cancelled, the inner `Task.detached` is **not** automatically cancelled (detached tasks don't inherit cancellation). The subprocess runs to completion.

For a single short-lived invocation this is fine. For a scan of 10k files that wants cancel-mid-flight, you need a per-subprocess cancellation hook: store the `Process` somewhere the cancel path can see, call `process.terminate()` on cancel. Adds complexity; consider whether the actual wall-clock cost justifies it.

See `1-macOS/AvidMXFPeek/` known-issue #2 for a case where we chose NOT to add it: per-probe time is ~50 ms, worst case is 8 orphan ffprobes completing naturally within a second of cancel.

---

## Anti-pattern: don't mix the two

Don't combine a `readabilityHandler` for stdout with `waitUntilExit` as a "just in case." The handler will fire, then `waitUntilExit` returns, then the handler may or may not fire with a tail chunk — you're back to the race you started with. Pick one model per subprocess call.

---

## History

Previously used `readabilityHandler` in this project (`BMXWrapper.runBMX` from the P2toMXF inheritance) — that pattern is right for its actual use case there (long-running `ffmpeg`/`bmxtranswrap` with progress text to stream into a log view). When the Wave 2 Avid-MXF-info path copied the pattern for a short-lived `mxf2raw --info` call, it picked up the tail-byte race as a dormant bug (code review flagged it; Avid's tiny XML was too small to hit it in practice). The 2026-04-20 pivot from `mxf2raw` to `ffprobe` was a natural moment to swap the pattern; `runAndCollect` retired the hazard as a side effect.
