# Stop a streamed run by cancelling the PRODUCER, not the consumer (run-handle pattern)

**Tags:** AsyncStream, run handle, cancel producer, makeStream, Task.detached, .stopping phase, onTermination, #153, terminal event

**Source:** `1-macOS/CompressPhotos/` — `Services/CompressionRun.swift` (`Run` handle) +
`AppModel.swift` (`startRun`/`stopRun`) + `Views/RunProgressBar.swift` ("Stopping…" state) (2026-07-02)

A long-running engine streams progress over an `AsyncStream` and a held `Task` consumes it into
`@Observable` UI state. The obvious Stop wiring — cancel the consuming task — is a trap: the stream
dies **instantly**, so the UI declares the run over while the engine is still winding down
cooperatively in the background. Fix: hand the caller a **run handle** whose `stop()` cancels the
*producer* task; the consumer keeps iterating until the engine's own terminal event arrives.

---

## Why cancel-the-consumer is a bug (not just a lost summary)

Consumer-cancel → `for await` exits immediately → your "run finished" code runs → stream's
`onTermination` fires → producer gets a *cooperative* cancel and winds down (in-flight items finish;
a destructive engine may still commit its per-chunk transaction). Three real failures follow:

1. **The engine acts after the UI said it stopped.** In CompressPhotos, up to 8 in-flight photos
   finished create+verify and the chunk's batched delete still ran — so the **macOS delete dialog
   appeared after the "Run stopped" summary sheet**.
2. **Re-entry race.** If your only-one-run guard is keyed off the consumer (`runTask == nil`), it
   releases at Stop-time — the user can start a **second run concurrently** with the first's
   wind-down (double-processing, duplicate dialogs, store races).
3. **The true tally is lost.** The engine's final `.finished(summary)` is yielded into a dead
   stream. Whatever the wind-down actually did (deletes included!) is never reported.

`#153`'s original "Stop-race fallback" (`stoppedEarly(processed, total)`) treats symptom 3 only —
keep it as a *defensive* fallback, but it's not the design.

## The pattern

Producer side — return a handle, not a bare stream:

```swift
public enum CompressionRun {
    /// A live run: the progress-event stream plus a handle to ask it to stop.
    public struct Run: Sendable {
        /// Always ends with `.finished(summary)` — including after `stop()`, once the
        /// run has actually wound down.
        public let events: AsyncStream<RunEvent>
        let task: Task<Void, Never>              // the producer
        /// Cooperative stop: in-flight items finish, the current chunk still commits its
        /// transaction. Keep consuming `events` — the final summary reports the wind-down.
        public func stop() { task.cancel() }
    }

    public static func start(work: [WorkItem], …) -> Run {
        let (events, continuation) = AsyncStream.makeStream(of: RunEvent.self)
        let task = Task.detached(priority: .userInitiated) {
            await run(work: work, …, continuation: continuation)   // yields .finished, then finish()
        }
        continuation.onTermination = { _ in task.cancel() }   // safety net: dropped consumer ≠ leaked run
        return Run(events: events, task: task)
    }
}
```

Consumer side (`@MainActor @Observable` model) — Stop flips a visible "stopping" state and the
loop runs to the genuine end; the in-flight state doubles as the re-entry guard:

```swift
enum RunPhase: Equatable { case compressing(done: Int, total: Int), deleting, stopping }
private(set) var runPhase: RunPhase?          // nil ⇒ idle; non-nil blocks Scan/Run buttons
private var runTask: Task<Void, Never>?       // re-entry guard — cleared ONLY when the stream ends
private var activeRun: CompressionRun.Run?

func startRun(…) {
    guard runTask == nil else { return }
    let run = CompressionRun.start(work: work, …)
    activeRun = run
    runPhase = .compressing(done: 0, total: total)
    runTask = Task { [self] in
        var summary: RunSummary?; var processed = 0
        for await event in run.events {
            switch event {
            case .itemFinished: processed += 1
                if runPhase != .stopping { runPhase = .compressing(done: processed, total: total) }
            case .chunkDeleted: if runPhase != .stopping { runPhase = .deleting }
            case .finished(let final): summary = final
            }
        }
        runTask = nil; activeRun = nil; runPhase = nil
        lastResult = summary.map(RunResult.summary)
            ?? .stoppedEarly(processed: processed, total: total)   // defensive only — see below
    }
}

func stopRun() {
    guard runPhase != nil, runPhase != .stopping else { return }
    runPhase = .stopping          // UI: "Stopping — finishing photos already in progress…"
    activeRun?.stop()             // cancel the PRODUCER; keep consuming
}
```

## The subtle bits

- **Late progress events must not downgrade the "Stopping…" state.** In-flight items keep emitting
  `.itemFinished` during wind-down — gate the phase updates (`if runPhase != .stopping`) or the bar
  flips back to "Compressing…". Hide/disable the Stop button in the `.stopping` phase.
- **The producer must ALWAYS yield its terminal event** (`continuation.yield(.finished(summary));
  continuation.finish()`) on every exit path — that's the contract that lets the consumer wait.
- **Normalize the stop reason when cancel lands in the final chunk.** The chunk loop's
  top-of-loop `Task.isCancelled` check never runs after the last chunk, so a Stop that skipped
  items would report "completed". After the loop:
  `if summary.cancelledBeforeCreate > 0, case .completed = summary.stoppedReason { .cancelled }`.
  (If nothing was skipped, "completed" is the honest label — leave it.)
- **Keep `onTermination → producer.cancel()`** even with the handle: it's the leak-protection for a
  consumer that dies or drops the stream without calling `stop()`.
- **Keep a defensive `stoppedEarly` fallback** for a stream that somehow ends without its terminal
  event — but write its copy honestly (don't claim work was committed; you don't know).
- **Report the wind-down.** The final summary now includes what happened *after* Stop (e.g.
  originals the closing chunk still deleted) plus the "not processed — run stopped first" count —
  surface both.

## When the simpler designs are fine

- **No Stop button at all** (idempotent / short ops): #145's "honest no-Cancel" — don't offer a
  Stop you can't honor.
- **Consumer-cancel is acceptable** only when the producer commits nothing after the cancel
  (pure reads, no transactions) *and* nobody needs the final tally — rare for anything worth a
  progress bar.

Pairs with **#35** (the producer's bounded fan-out + `onTermination`), **#145** (consumer/reducer
into `@Observable` UI; its no-Cancel note is the zero-effort alternative), **#153** (the destructive
confirmation ladder around the same run — its Stop-race section defers here), **#12** (progress UI).
