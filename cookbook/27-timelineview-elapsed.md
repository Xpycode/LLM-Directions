# TimelineView for Elapsed-Time UIs

**Use when:** a view needs to display elapsed / remaining / wall-clock time that
ticks while other state (from `@Published` or `@Observable`) is unreliable or
sparse. Replaces manual `Timer.scheduledTimer` + `objectWillChange.send()` plumbing.

**Source:** `1-macOS/P2toMXF/` — `ProgressControlPanel.swift`, `QueueListView.swift`.

---

## The problem

You have a progress panel that shows `0:00 → 0:01 → 0:02 …` elapsed time during a
long-running task. The elapsed count is derived from `Date().timeIntervalSince(startTime)`.
SwiftUI needs a reason to re-render the view every second.

The traditional approach — own a `Timer.scheduledTimer` in the view model and call
`objectWillChange.send()` in the tick closure — works but has issues:

- Every tick invalidates the **whole** `ObservableObject`, re-rendering every view that
  observes it (not just the elapsed label).
- Manual `invalidate()` cleanup on task-finish or view-disappear is error-prone.
- Needs an `@MainActor` hop inside the closure.
- Tests and previews don't honor it naturally.

## The pattern

Wrap the time-dependent subview in `TimelineView(.periodic(from: .now, by: 1.0))`,
read `context.date` inside the closure, and derive elapsed from the stored `startTime`.

```swift
import SwiftUI

struct ProgressMetrics {
    var progress: Double = 0.0
    var startTime: Date?
    // ... other fields

    /// Elapsed, measured at a caller-supplied reference date.
    /// The reference date lets us drive updates from TimelineView without relying on
    /// Date() inside the computed property (which wouldn't re-evaluate on a schedule).
    func elapsedSeconds(at referenceDate: Date) -> TimeInterval {
        guard let start = startTime else { return 0 }
        return referenceDate.timeIntervalSince(start)
    }

    func formattedElapsed(at referenceDate: Date) -> String {
        formatHMS(elapsedSeconds(at: referenceDate))
    }

    /// Remaining, if we have enough progress to estimate (>5%).
    func estimatedRemainingSeconds(at referenceDate: Date) -> TimeInterval? {
        guard progress > 0.05 else { return nil }
        let elapsed = elapsedSeconds(at: referenceDate)
        guard elapsed > 0 else { return nil }
        return max(0, elapsed / progress - elapsed)
    }
}

struct ProgressControlPanel: View {
    let metrics: ProgressMetrics

    var body: some View {
        VStack {
            // Progress bar updates via @Published — no need for TimelineView here.
            ProgressView(value: metrics.progress)

            // Time readouts tick on their own cadence.
            TimelineView(.periodic(from: .now, by: 1.0)) { context in
                HStack {
                    Label(metrics.formattedElapsed(at: context.date), systemImage: "clock")
                    if let r = metrics.estimatedRemainingSeconds(at: context.date) {
                        Label("~\(formatHMS(r))", systemImage: "hourglass")
                    }
                }
                .monospacedDigit()
            }
        }
    }
}
```

## Why this works

- **`TimelineView.Context.date`** is the authoritative reference time. Use it instead of
  `Date()` so computations stay in sync with the schedule even if the main thread briefly
  stalls (TimelineView "catches up" using the schedule's tick, not wall-clock drift).
- **Only the closure's subtree re-renders.** The outer progress bar, phase text, etc.
  keep their normal `@Published` cadence.
- **Automatic lifecycle.** Gate the TimelineView with `if isProcessing` — when conversion
  ends, SwiftUI tears it down and the schedule stops. No `invalidate()` needed.
- **Composable.** Multiple TimelineViews in different subtrees (e.g., queue header and
  footer progress panel) don't conflict; each has its own independent schedule.

## Pitfalls

- **Don't call `Date()` inside the closure** — use `context.date`. `Date()` reads the
  wall clock; `context.date` reads the scheduled tick. If the main thread stalled for
  500 ms, `Date()` would return the current moment and your elapsed display would
  skip ahead; `context.date` would return the scheduled 1-second increment and stay
  accurate to the TimelineView schedule.
- **Don't set schedule interval too small.** `by: 1.0` is right for elapsed timers.
  Below ~0.25s you'll rack up unnecessary renders; use `.animation` schedule for that
  case (which coordinates with SwiftUI's animation system).
- **The schedule can't be dynamically modified.** If the schedule depends on state,
  wrap the TimelineView in an `if` so SwiftUI creates a fresh one when the condition
  changes.
- **Date-parameterized methods, not computed properties.** If `elapsedSeconds` is a
  computed property that calls `Date()` internally, the TimelineView's closure re-run
  won't help — SwiftUI only observes properties, not `Date()`. The parameter must come
  from `context.date` so the closure is what changes, not the underlying struct.

## Real-world use: two TimelineViews in one app

P2toMXF has two independent TimelineViews:
- Footer progress panel — full `elapsed / remaining / speed` readout
- Queue panel header — secondary "remaining" countdown for the active job

Both schedule at 1 Hz, both read the same `job.progress` / `job.startedAt`, neither
invalidates the other. This is the test: multiple TimelineViews composing cleanly is
the hallmark of a primitive that scales.

## Migration from Timer+objectWillChange

Remove, in order:

1. The `elapsedTimer: Timer?` property.
2. The `Timer.scheduledTimer` closure that calls `objectWillChange.send()`.
3. The `stopTimer()` call in `deinit` or task completion.
4. Any parameterless `elapsedSeconds` / `formattedElapsed` computed properties that
   called `Date()`. Replace with `func elapsedSeconds(at: Date) -> TimeInterval`.

Then wrap the display call site in `TimelineView(.periodic(from: .now, by: 1.0))` and
pass `context.date` into the new method. The timer plumbing evaporates; the view ticks
on its own.
