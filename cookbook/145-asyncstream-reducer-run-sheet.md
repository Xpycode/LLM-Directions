# 145 — Consume an engine's `AsyncThrowingStream` into `@Observable` UI via a reducer + run sheet

**Best for:** a SwiftUI macOS app that drives a long, multi-phase operation (copy → verify →
geotag, build, export, batch transcode) whose engine already streams progress as
`AsyncThrowingStream<Event, Error>`, and you need a live progress UI then a final report. The
engine stays headless and `Sendable`; the UI is thin.

**Pairs with:** #35 (the **producer** side — bounded fan-out emitting the stream; this is the
**consumer/UI** side), #143 (mount monitoring inside the same `@Observable` model), #00 (app shell),
#12 (activity/progress).

---

## The shape

The engine emits a stream of *facts* (`fileCopied`, `geotagging`, `finished(report)`). The UI needs
*state*. The clean bridge is a tiny **reducer** — `apply(_ event:)` — that folds each event into
plain `@Observable` fields. The view never sees an event; it only reads fields.

```swift
@Observable @MainActor
final class RunModel {
    enum RunState: Equatable { case idle, running, finished, failed(String) }
    enum RunPhase: Equatable { case preparing, copying, finishing, done }

    private(set) var runState: RunState = .idle
    private(set) var runPhase: RunPhase = .preparing
    private(set) var done = 0, total = 0          // seed `total` from the plan up front
    private(set) var currentItem: String?
    private(set) var report: Report?
    private var runTask: Task<Void, Never>?

    func start(plan: Plan) {
        guard runState != .running else { return }
        runState = .running; runPhase = .preparing
        done = 0; total = plan.willCreateCount     // denominator known before any I/O
        report = nil
        runTask?.cancel()
        // The Task inherits @MainActor isolation, so every apply() lands on the
        // main thread with no await/locking — while the heavy work runs OFF main
        // inside the engine's own Sendable struct.
        runTask = Task { [weak self] in
            do {
                for try await event in Engine().run(plan: plan) {
                    guard let self, !Task.isCancelled else { return }
                    self.apply(event)
                }
            } catch {
                self?.runState = .failed(error.localizedDescription)   // preflight throw lands here
            }
        }
    }

    private func apply(_ event: Event) {            // pure state mutation, no I/O
        switch event {
        case .started:                 runPhase = .copying
        case .itemDone(let name, let n, let t):
            runPhase = .copying; done = n; total = t; currentItem = name
        case .finishing(let count):    runPhase = .finishing; /* set finishing total */ _ = count
        case .finished(let r):         report = r; runPhase = .done; runState = .finished
        }
    }

    func dismiss() { runTask?.cancel(); runState = .idle; report = nil }
}
```

## Two-segment progress bar (the bursty-final-phase trap)

A multi-phase run often has one phase that ticks smoothly (per-item events) and a final phase that
is a **single batch** whose results all arrive at once (e.g. one ExifTool invocation over N files).
A naive `done / total` bar **freezes** during the batch, then **snaps** to 100%. Split the bar:

```swift
var progressFraction: Double {
    switch runPhase {
    case .preparing:  return 0
    case .copying:
        let f = total > 0 ? Double(done) / Double(total) : 1
        return f * (expectsFinalPhase ? 0.9 : 1.0)   // copy fills 0…0.9 (or all of it)
    case .finishing:
        let f = finishTotal > 0 ? Double(finishDone) / Double(finishTotal) : 1
        return 0.9 + f * 0.1                          // batch fills 0.9…1.0
    case .done:       return 1
    }
}
```

`expectsFinalPhase` is derived from the plan **before** the run, so a run with no final phase gives
the smooth phase the whole bar instead of stalling at the split point.

## Present as a modal sheet keyed off `runState`

```swift
.sheet(isPresented: Binding(
    get: { model.runState != .idle },
    set: { if !$0 { model.dismiss() } }
)) {
    Group {
        switch model.runState {
        case .running:           ProgressView(value: model.progressFraction) /* + label */
        case .finished:          model.report.map { ReportView(report: $0, onDone: model.dismiss) }
        case .failed(let msg):   ErrorView(message: msg, onClose: model.dismiss)
        case .idle:              EmptyView()
        }
    }
    .interactiveDismissDisabled(model.runState == .running)   // can't escape mid-run
}
```

---

## Gotchas

1. **Actor inheritance is the whole trick.** `start()` is on a `@MainActor` model, so the unstructured
   `Task {}` it spawns inherits main-actor isolation. `apply(event)` mutates state on the main thread
   with zero `await`/locking. The heavy work never touches main — it lives in the engine's `Sendable`
   struct, reached only through the `for try await`.
2. **Seed the denominator from the plan, not the first event.** The bar needs a `total` on frame one;
   the plan already knows it. The engine's per-event `total` then just confirms it.
3. **Cancelling the consumer does NOT cancel the producer.** If the engine spawns its own `Task`
   inside the `AsyncThrowingStream` closure (the #35 fan-out shape), cancelling `runTask` stops you
   *listening* but copies keep running. So either (a) don't ship a Cancel button that lies, or (b)
   thread real cancellation through the engine (`continuation.onTermination` + `Task.isCancelled`
   checks in the fan-out). If the operation is idempotent (verified copy skips identical files), (a)
   is honest and fine — a half-run is safe to resume.
4. **The preflight throw is the `catch`.** An engine that validates (disk space, permissions) before
   emitting any event throws *before* the first `yield`; the `for try await` surfaces it in `catch` →
   `.failed`, which the sheet renders as the error arm. No event is ever emitted for that path.
5. **Reducer events ≠ report rows.** Skips/failures may not advance the progress bar (it counts only
   the smooth-phase completions) but must still appear in the final report's counts. Let the engine
   build the report; the reducer only drives the *live* view.

*Source: PhotoIngest `IngestModel.swift` (run spine: `startImport`/`apply`/`progressFraction`),
`IngestProgressView.swift`, `IngestReportView.swift`, `ContentView.swift` (.sheet) — T6.3, 2026-06-30.*
