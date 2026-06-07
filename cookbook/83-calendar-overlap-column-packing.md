# Overlapping calendar events: cluster, then first-free-column with a half-open free test

**Source:** `1-macOS/MyOwnCalendar/` — `Kernel/TimeGridLayout.swift` (2026-06-07). Week time-grid; 8/8 unit tests.

**Problem:** a day/week time-grid has to place overlapping events side-by-side without collisions, and *without* needlessly narrowing events that have no neighbours. Apple Calendar does this; everyone who builds a calendar, Gantt chart, or resource timeline re-derives it. The naïve "one column per event" wastes horizontal space; "shrink everything to the day's max concurrency" makes a single 8 AM clash shrink your 3 PM solo meeting to half-width.

**The shape that works — two passes, both keyed on the same half-open overlap rule:**

1. **Cluster** the sorted events into runs of *transitively* overlapping events. A cluster's width is local to itself — a lone event later in the day is its own cluster and stays full width.
2. **Assign columns** *within* each cluster by first-free-column (greedy lane reuse). `columnCount` is derived per-cluster, so every card in a cluster shares one width denominator and they tile to a clean edge.

The single decision that drives both passes: **overlap is half-open** — `a.start < b.end`. Back-to-back events (`a.end == b.start`) *touch* but do not *overlap*, so they land in separate clusters (full width) and can reuse a lane. Get this wrong (`<=`) and every touching pair spuriously shares width.

## Pass 1 — cluster (the width-grouping pass)

```swift
// events pre-sorted by (start, end, id) — stable & deterministic
var clusters: [[E]] = []
var current: [E] = []
var runningEnd: Date?
for e in sorted {
    if let end = runningEnd, e.start < end {      // half-open: overlaps cluster so far
        current.append(e)
        runningEnd = max(end, e.end)              // cluster end = max, not last — handles nesting
    } else {                                      // gap → close cluster, open a new one
        if !current.isEmpty { clusters.append(current) }
        current = [e]
        runningEnd = e.end
    }
}
if !current.isEmpty { clusters.append(current) }
```

`runningEnd = max(...)`, not `= e.end`, is what makes clustering **transitive** and nesting-safe: a long event A (9:00–12:00) that swallows a short B (10:00–10:30) keeps the cluster open for a later C (11:00–...) that overlaps A but not B.

## Pass 2 — first-free-column (the lane-assignment pass)

```swift
static func assignColumns<E: EventLike>(_ cluster: [E]) -> [Int] {
    var columns = [Int](repeating: 0, count: cluster.count)
    var columnEnds: [Date] = []   // running end-time of the last event in each lane
    for (i, e) in cluster.enumerated() {
        // leftmost lane already free by the time this event starts
        // (half-open: touching == free, hence `>=` not `>`)
        if let lane = columnEnds.firstIndex(where: { e.start >= $0 }) {
            columns[i] = lane
            columnEnds[lane] = e.end
        } else {
            columns[i] = columnEnds.count   // no free lane → open one on the right
            columnEnds.append(e.end)
        }
    }
    return columns
}
```

Then the caller derives the shared denominator and emits placements:

```swift
let columns = assignColumns(cluster)
let columnCount = (columns.max() ?? 0) + 1
for (i, e) in cluster.enumerated() {
    result.append(PositionedEvent(event: e, column: columns[i], columnCount: columnCount))
}
```

The view layer turns each placement into a frame — pure arithmetic, no layout logic:

```swift
x     = CGFloat(p.column) / CGFloat(p.columnCount) * dayWidth
width = dayWidth / CGFloat(p.columnCount)
// y / height come from GridMetrics (points-per-hour), orthogonal to columns
```

## Why this composition works

- **`firstIndex(where:)` left→right = packing + reuse in one line.** A freed lane is reclaimed before a new one is opened, so the cluster stays as narrow as its true max-concurrency (the A-B-C chain where C drops back into A's vacated column 0 instead of forcing a third lane).
- **`>=` is the entire half-open contract** — one operator. With `>`, an event starting exactly when a lane frees up can't reuse it, inflating `columnCount` and shrinking every card in the cluster. Touching ≠ overlapping, consistently across both passes.
- **`columnCount` per cluster, not per day.** Width is local: a busy 9 AM cluster never narrows an isolated 3 PM event. This is the whole point — "trailing expansion" falls out for free because a lone event is a cluster of one → `columnCount == 1` → full width.
- **Deterministic sort `(start, end, id)`** makes layout reproducible and the tests stable.

## The decoupling that makes it testable

The kernel positions a **protocol, not an EventKit type** — no `import EventKit`, no `import SwiftUI`:

```swift
protocol EventLike {
    var id: String { get }
    var start: Date { get }
    var end: Date { get }
    // title / isAllDay / calendarColor for the view, not the math
}
struct PositionedEvent<E: EventLike>: Equatable { let event: E; let column: Int; let columnCount: Int }
```

Because layout is pure value logic over `EventLike`, the full suite (clustering + packing edge cases) runs headless in milliseconds with a tiny `TestEvent` struct — **no simulator, no calendar permission, no window**. The hard correctness lives in tested code; the SwiftUI view just multiplies fractions. This is the general lesson: push the geometry brain behind a minimal protocol so it can be unit-tested away from the framework that produces the data.

**Test the edges, they're where it breaks:** no-overlap (all full width), two-overlap (½ each), back-to-back (half-open → *not* shared), transitive A-B-C (C reuses A's lane), nested short-inside-long, three-mutually-overlapping (3 lanes), lone-event-beside-cluster (stays full width), every-input-placed-once.

Pairs with #21 (coordinate-systems / time-grid geometry — `GridMetrics` supplies the y-axis this splits the x-axis of), #04 (keep heavy layout out of SwiftUI body).
