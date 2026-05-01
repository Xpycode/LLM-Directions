# AsyncStream with bounded-concurrency TaskGroup (drain-and-refill)

**Source:** `1-macOS/AvidMXFPeek/` — `MXFFolderScanner.scan(folder:)` (2026-04-20)

Fan out N expensive async operations across a large input without spawning N tasks at once. Bound the in-flight count; stream results out as they complete. The drain-and-refill loop is the subtle bit — a naive `addTask` per input spawns everything upfront and queues them behind the executor.

---

## When to use

You have:
- A large input collection (hundreds to tens of thousands of items)
- Each item is processed async (subprocess call, network request, disk I/O)
- You want results to stream out as they finish, not block until all are done
- You need to cap concurrency for resource reasons (CPU, file descriptors, API rate limits, subprocess count)

Typical shapes: scanning a folder and running `mxf2raw`/`ffprobe`/`exiftool` per file; fanning out thousands of HTTP requests with a concurrency cap; running a worker pool over a queue of jobs with streamed progress.

---

## The pattern

```swift
struct FolderScanner {
    var maxConcurrent: Int = 8

    func scan(folder: URL) -> AsyncStream<ResultInfo> {
        let files = Self.discover(under: folder)   // synchronous enumeration — cheap
        let concurrency = max(1, maxConcurrent)

        return AsyncStream<ResultInfo> { continuation in
            let task = Task.detached(priority: .userInitiated) {
                if files.isEmpty {
                    continuation.finish()
                    return
                }

                await withTaskGroup(of: ResultInfo.self) { group in
                    var index = 0

                    // 1. Seed the group up to the concurrency cap.
                    let initialBatch = min(concurrency, files.count)
                    while index < initialBatch {
                        let url = files[index]
                        group.addTask { await process(url) }
                        index += 1
                    }

                    // 2. Drain and refill: yield each completion, enqueue the next
                    //    from the backlog. The group stays near `concurrency` wide
                    //    until the backlog empties.
                    while let result = await group.next() {
                        if Task.isCancelled { break }
                        continuation.yield(result)
                        if index < files.count {
                            let url = files[index]
                            group.addTask { await process(url) }
                            index += 1
                        }
                    }
                }
                continuation.finish()
            }

            // 3. Stream drop / consumer disappeared → cancel the scan.
            continuation.onTermination = { _ in task.cancel() }
        }
    }
}
```

---

## Why not the naive version

```swift
// BAD — spawns all N tasks upfront
await withTaskGroup(of: ResultInfo.self) { group in
    for url in files {
        group.addTask { await process(url) }    // all N tasks enqueued immediately
    }
    for await result in group {
        continuation.yield(result)
    }
}
```

Swift's TaskGroup doesn't queue tasks at the type level — adding one schedules it. For 10k files:
- 10k pending tasks all live in the group's storage at once
- 10k closures all captured in memory at once
- The executor runs them as workers free up, but you've lost the chance to cap concurrency cleanly
- Cancellation signals propagate oddly when there are tens of thousands of parked tasks

The drain-and-refill version keeps only `maxConcurrent` tasks alive at any moment.

---

## Choosing `maxConcurrent`

Rule of thumb by resource type:

| Resource | Starting point | Ceiling |
|----------|----------------|---------|
| Subprocess / `exec` | 8 | `ProcessInfo.processInfo.activeProcessorCount` (each process uses ~1 core) |
| CPU-bound pure compute | `activeProcessorCount` | same |
| HTTP / network | 4–16 | what the server tolerates (rate limits, QPS budget) |
| File reads (SSD) | 16–32 | 64 — beyond that, IOPS saturates |
| File reads (spinning disk / network mount) | 1–4 | 4 — more = seek thrashing |

Tune upward while watching CPU idle; downward if thermal pressure or I/O wait shows up. Expose as a property on the scanner (as here — `var maxConcurrent: Int = 8`) so callers can override per-use.

---

## Gotchas

**`Task.detached` not `Task { ... }`.** The detached form doesn't inherit the caller's actor context (e.g. `@MainActor`). If a SwiftUI view calls `scanner.scan(folder:)`, plain `Task { ... }` would bind the whole scan to the MainActor and serialize every subprocess behind the UI thread — the exact opposite of what you want. Detached breaks free of that.

**`continuation.onTermination` is the cleanup hook.** When the consumer (a SwiftUI `.task { for await r in stream { ... } }`) disappears — view navigates away, user cancels — the stream is dropped and `onTermination` fires. Propagate the cancel to the scan task; without this your workers keep running after the UI stopped caring.

**`Task.isCancelled` check inside the drain loop.** The task-group's subtasks inherit cancellation from the outer task, so `process(url)` will throw or short-circuit on cancel. But the `while let result = await group.next()` loop itself needs to bail explicitly or it'll keep yielding the already-in-flight completions after cancellation.

**Per-file errors should be values, not throws.** For a 10k-file scan, `withThrowingTaskGroup` forces you to decide on every error whether to tear down the whole group. Instead, make `process(url)` return a result type that encodes errors (`MXFHeaderInfo.failed(reason:)` in the AvidMXFPeek case) — then `withTaskGroup` suffices and per-file failures just become rows with error text. See **Related: `result-types-over-throws.md`** (if captured as its own pattern).

**The scanner's worker fresh-per-task rule.** If `process(url)` uses some shared object with mutable state (a `Wrapper` with a cancellation flag, say), creating one instance per subtask avoids sharing-concerns even if the hot path is technically self-contained. Cheap objects, simpler reasoning:
```swift
group.addTask {
    let wrapper = Wrapper()   // fresh per call — no shared cancel/process state
    return await wrapper.info(url: url)
}
```

**Ordering is completion-order, not input-order.** Clients identify results by their own ID (URL, primary key), never by arrival index. If strict input-order output is required, buffer and reorder on the consumer side — don't try to make the scanner serialize.

---

## When NOT to use

- **Each operation is already very fast** (< 1ms) — TaskGroup overhead dominates; use a plain `for` loop
- **Caller wants all results before acting** — use `scanAll(...)` convenience that collects to `[Result]`; no streaming needed; consider `[T].concurrentMap(concurrency:)` if you're already using `AsyncAlgorithms`
- **You need priority ordering** — TaskGroup doesn't guarantee priority across added tasks. For priority queues, use a custom actor-based worker pool

---

## Related patterns

- [11-drag-drop.md](11-drag-drop.md) — uses `withTaskGroup` for concurrent drop handling (different shape — all-upfront is fine there because N is small)
- [19-swift6-concurrency.md](19-swift6-concurrency.md) — `@MainActor + @Observable` for the UI side that consumes the stream
- [32-nsworkspace-asyncstream.md](32-nsworkspace-asyncstream.md) — another AsyncStream pattern (system events rather than file fan-out)
- [14-subprocess-url.md](14-subprocess-url.md) — subprocess URL pitfalls if `process(url)` is an `exec` call
