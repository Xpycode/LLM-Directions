## swift-subprocess `.strings()` deadlocks on a huge single line — use `.unbounded`

**Source:** zPackages — `Sources/ProcessKit/ProcessRunner.swift` + `RunSpec.swift` (ProcessKit, the `swift-subprocess` wrapper). Surfaced while **proving ProcessKit in Magpie** (the released yt-dlp app). Added 2026-06-27.

**Use case:** You wrap Apple's [`swift-subprocess`](https://github.com/swiftlang/swift-subprocess) to stream a child process's output line-by-line, reading `execution.standardOutput.strings()` inside the `Subprocess.run { execution in … }` closure. It works on every test (`echo`, small command output) and then **hangs forever** the first time a real tool emits a very large line with no newline — e.g. `yt-dlp -J` returns a **single ~580 KB JSON blob on one line**. The process never exits; the consuming `for try await` never ends. No error, no crash — a pure deadlock.

### Why it deadlocks

`.strings()` defaults its back-pressure policy to **`.maxLineLength(128 * 1024)`** — a 128 KB cap per line:

```swift
// swift-subprocess: SubprocessOutputSequence.strings(...)
public func strings(
    separatedBy separator: ... = .lineBreaks,
    bufferingPolicy: ... = .maxLineLength(128 * 1024)   // ← 128 KB default cap
) -> StringSequence<UTF8> { ... }
```

When a line exceeds the cap, the line splitter **stops pulling from the pipe** (waiting for a line-break that will let it emit a bounded line). The OS pipe buffer (~64 KB) fills, the child **blocks on `write()`**, and the newline that would release the splitter never comes — because the child can't write it. Reader waits for the writer, writer waits for the reader: classic pipe deadlock. (The doc comment claims it "throws an error if a line exceeds this limit" — in practice the oversized-line path stalls rather than throwing.)

The cap exists to bound memory against a hostile/runaway stream. But it's exactly wrong for a **trusted tool** that legitimately emits huge single-line output.

### The fix — default to `.unbounded`, make the cap opt-in

`BufferingPolicy` has two cases: `.maxLineLength(Int)` and **`.unbounded`** ("adds to the buffer without imposing a limit on line length"). Pass `.unbounded` for trusted tools. Expose it on your spec so an untrusted caller can still opt back into a fail-fast cap:

```swift
// RunSpec.swift — nil means "no cap"
public var maxLineLength: Int?   // default nil

// ProcessRunner.swift — map the spec to a policy, apply to BOTH streams
let lineBuffering: SubprocessOutputSequence.StringSequence<UTF8>.BufferingPolicy =
    spec.maxLineLength.map { .maxLineLength($0) } ?? .unbounded   // ← default: no cap

// ...inside the run closure:
for try await line in execution.standardOutput.strings(bufferingPolicy: lineBuffering) {
    continuation.yield(.stdout(line))
}
for try await line in execution.standardError.strings(bufferingPolicy: lineBuffering) {
    continuation.yield(.stderr(line))
}
```

Note the nested type name: the policy is `SubprocessOutputSequence.StringSequence<UTF8>.BufferingPolicy` (it's nested on `SubprocessOutputSequence`, *not* on `AsyncBufferSequence`). Or skip the annotation and inline `spec.maxLineLength.map { .maxLineLength($0) } ?? .unbounded` into each `strings(bufferingPolicy:)` call so `.maxLineLength`/`.unbounded` infer from the parameter type.

### The trap

```swift
// ❌ Green on every small-output test, deadlocks on the first big single line:
for try await line in execution.standardOutput.strings() { ... }   // default .maxLineLength(128 KB)
```

The danger is that it is **invisible to a normal unit suite**. ProcessKit had **17 passing tests** — all using `echo`/`/bin/sh` with small, newline-terminated output — and was still wrong for the one workload that mattered. The bug only appears with (a) a *large* output that is (b) on a *single line* (no newline to flush the splitter under the cap). yt-dlp `-J`, a `cat` of a big minified JSON/CSV, a base64 blob, a `jq -c` of a large document — all hit it.

### Pin it with a regression test

A single newline-free line bigger than the old cap must stream to completion:

```swift
func testHugeSingleLineDoesNotDeadlock() async throws {
    let byteCount = 600_000   // ~4.7× the old 128 KB cap, on ONE newline-free line
    let spec = RunSpec(
        executablePath: "/bin/sh",
        arguments: ["-c", "head -c \(byteCount) /dev/zero | tr '\\000' 'a'"],
        terminationGrace: .seconds(1))
    var stdout = ""
    var last: RunEvent?
    for try await event in runner.run(spec) {
        if case .stdout(let line) = event { stdout += line }
        last = event
    }
    XCTAssertEqual(stdout.utf8.count, byteCount)   // whole oversized line arrived intact
    XCTAssertEqual(last, .exit(.code(0)))
}
```

Run it under a timeout (`timeout 90 swift test …`) so a regression fails the suite instead of hanging CI.

### Why it matters

This is the canonical payoff of the **"a package isn't proven until a real app exercises it"** discipline (cookbook theme: the build→prove funnel). The defect was undetectable from inside the package — it took the first real consumer's first real workload (Magpie's metadata probe) to surface it in minutes. Any subprocess wrapper that line-splits output inherits this: a CI-log streamer, a `git` porcelain reader, an ffmpeg `-progress` parser, anything that might see one long line.

### Composes with

- **swift-subprocess teardown** — the same `ProcessRunner` uses `PlatformOptions.teardownSequence` (`.gracefulShutDown`) for declarative SIGTERM→grace→SIGKILL on cancel; `RunSpec.terminationGrace` sets the window. The line-cap fix and the teardown both live in the same thin `Subprocess.run` adapter.
- **Prove-in-app generally** — same lesson as lifting a renderer into a package (#136): the failure mode lives at the seam between the reusable code and its first real environment.

### Reference implementation

`Sources/ProcessKit/ProcessRunner.swift` (`lineBuffering`) + `Sources/ProcessKit/RunSpec.swift` (`maxLineLength`) + `Tests/ProcessKitTests/ProcessRunnerTests.swift` (`testHugeSingleLineDoesNotDeadlock`) in zPackages. Adoption narrative: zPackages `docs/sessions/2026-06-27.md` (ProcessKit proven in Magpie).
