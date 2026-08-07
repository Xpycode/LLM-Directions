# 177 — Coalescing a hot progress callback into a rate a UI can survive

**Tags:** progress, throttle, coalesce, debounce, AsyncStream, MainActor, bufferingNewest, per-chunk callback, byte progress, NSLock, DispatchTime, monotonic clock, retry, phase

**Extracted from:** MediaIngest (2026-08-07)

## The problem

A long file operation reports nothing until it finishes, so the UI shows "0 of 18" for minutes and
looks hung. The fix is per-chunk progress — and the naive version replaces one bug with two.

A real run: 18 clips, ~180 GB, 1 MB chunks, read back to verify. That is ~370,000 callbacks feeding a
`MainActor` consumer over an unbounded `AsyncStream`. Nothing *drops* them, so the UI just falls
further behind the work and stops redrawing. Worse, the retry path re-reads the whole file, so a
running byte total sails past 100%.

## Throttle at the emit side, not by re-buffering the stream

The tempting one-line fix is a lossy buffering policy:

```swift
// WRONG — .bufferingNewest is free to drop ANY element, including the
// terminal one every end-of-run action depends on.
AsyncStream(bufferingPolicy: .bufferingNewest(1)) { ... }
```

Progress events are droppable; the completion event is not, and the policy cannot tell them apart.
Coalesce **before** you yield, so nothing that matters is ever a candidate for loss.

## The lock-box

The callback fires from N worker threads at once and must be synchronous — an `await` inside a copy
loop suspends it on every chunk. So the state lives in a reference type wrapping an `NSLock`, which
also lets `@Sendable` closures capture it as a `let`:

```swift
final class ProgressThrottle: @unchecked Sendable {
    private struct FileState { var phase: Phase; var bytes: Int64; var lastEmit: UInt64 }
    private let lock = NSLock()
    private var states: [URL: FileState] = [:]
    private let intervalNanos: UInt64
    private let now: @Sendable () -> UInt64   // injectable; see below

    /// - Returns: the cumulative figure to publish, or nil to swallow this tick.
    func tick(source: URL, phase: Phase, delta: Int64) -> Int64? {
        lock.lock(); defer { lock.unlock() }
        let stamp = now()

        // A phase change ALWAYS emits, un-throttled: it resets the total, and
        // swallowing it freezes the bar at the previous phase's last value.
        guard var state = states[source], state.phase == phase else {
            states[source] = FileState(phase: phase, bytes: delta, lastEmit: stamp)
            return delta
        }

        state.bytes += delta
        // `&-` so an injected clock that goes backwards can't trap on overflow.
        let due = (stamp &- state.lastEmit) >= intervalNanos
        if due { state.lastEmit = stamp }
        states[source] = state
        return due ? state.bytes : nil
    }

    func forget(_ source: URL) { lock.lock(); defer { lock.unlock() }; states[source] = nil }
}
```

10 Hz **per item** — with six items in flight that's ~60 events/s: survivable, and already finer than
a display refresh. Throttle per item, not globally, or one busy item starves every other bar.

## Three decisions that carry the pattern

**Callbacks report deltas; the throttle owns the total.** That is what makes a reset possible — a
callback reporting cumulative totals can only ever go up.

**Totals are cumulative within a *phase*, not within an item.** Multi-leg work (write then verify,
download then unpack) reports a phase alongside the bytes. If both legs cover the same byte count,
**one denominator sizes a bar for either leg** — no second measurement needed, and the consumer is
free to weight them (85% / 15%) instead of concatenating.

**A retry needs an explicit reset signal, not just a phase.** Make it a phase case carrying **zero**
bytes, emitted *before* the retry moves a byte:

```swift
if attemptsMade > 1 { onBytes(0, .restarted, src) }   // discard what you have
```

## Grafting the sink onto an injected collaborator

The worker is usually injected once at construction, while the progress sink closes over *one run's*
event continuation. Don't have the run construct a fresh worker — that silently discards whatever
seam the test injected. Copy it instead:

```swift
func reportingBytes(to onBytes: @escaping @Sendable (Int64, Phase, URL) -> Void) -> Self {
    Self(transformChunk: transformChunk, onBytes: onBytes)   // keeps the test seam
}
```

## Testing it

Inject a **monotonic** clock (`DispatchTime.now().uptimeNanoseconds`, never `Date()` — a wall-clock
jump backwards stalls every bar). Injectable, it makes the rate cap provable without sleeping; a
sleeping test cannot distinguish "coalesced" from "the machine was busy".

Assert the **count**, not just the sum. `sum == fileSize` passes happily when you report one lump at
the end — the exact bug the pattern exists to prevent. Mutation-check both: reporting per file
instead of per chunk broke the count assertion; throttling the phase change broke five tests across
two suites; dropping the reset signal broke three.
