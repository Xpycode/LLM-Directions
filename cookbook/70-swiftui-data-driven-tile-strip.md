# Data-driven SwiftUI tile strip — descriptor array kills the type-checker timeout

**Source:** `1-macOS/QuickStatsPanel/` — `Model/StatDescriptor.swift` + `Views/StatsStripView.swift` (2026-06-04, v0.1.1).

A row of N hardcoded subviews (stat tiles, toolbar chips, badges) plus a conditional one eventually trips:

> *The compiler is unable to type-check this expression in reasonable time; try breaking up the expression…*

**Why:** SwiftUI infers one giant generic type for the container's content — `TupleView<(A, B, C, D, …)>`. Each literal child and every `if` widens that tuple type; the inference cost grows super-linearly. Five tiles + a conditional is enough to feel it.

**Fix:** replace the literal children with a `ForEach` over a homogeneous `[Descriptor]`. The content type collapses to a single `ForEach<…>` — trivial to infer — and you gain stable identity (enables reorder/filter/selection later) for free.

**1. A `kind` enum (stable identity + display order) and a UI-agnostic descriptor:**

```swift
enum StatKind: String, CaseIterable, Identifiable, Sendable {
    case cpu, memory, disk, network, battery     // declaration order = display order
    var id: String { rawValue }
}

struct StatDescriptor: Identifiable {            // no SwiftUI types — view applies color
    let kind: StatKind
    let symbol: String
    let value: String
    let widestValue: String                      // fixed-width template (see #67)
    let loadPercent: Double
    let detail: [(String, String)]
    var id: String { kind.id }
}
```

**2. One mapping chokepoint** — store → descriptors, with availability filtering in the same place (e.g. battery absent on desktops, #69). `compactMap` drops the unavailable:

```swift
extension StatsStore {
    var visibleStats: [StatDescriptor] {         // read in a body → Observation tracks samples
        StatKind.allCases.compactMap(descriptor(for:))
    }
    private func descriptor(for kind: StatKind) -> StatDescriptor? {
        switch kind {
        case .battery:
            guard battery.isPresent else { return nil }   // desktop Macs: no tile
            return StatDescriptor(kind: .battery, symbol: battery.symbolName, …)
        case .cpu:    return StatDescriptor(kind: .cpu, …)
        // …
        }
    }
}
```

**3. The view collapses to a `ForEach`** — dividers via `if index > 0` so N tiles yield N−1 separators, self-correcting when a tile is filtered out:

```swift
HStack(spacing: Theme.Metrics.tileSpacing) {
    ForEach(Array(store.visibleStats.enumerated()), id: \.element.id) { index, stat in
        if index > 0 { divider }
        StatTileView(symbol: stat.symbol, value: stat.value,
                     widestValue: stat.widestValue,
                     loadPercent: stat.loadPercent, detail: stat.detail)
    }
}
```

**Gotchas**
- **Keep SwiftUI types out of the descriptor** (`String`/`Double`/tuples only). Apply `Theme.loadColor(forPercent:)` etc. in the *view*, so the model stays UI-agnostic and testable.
- **Read `visibleStats` inside the `body`**, not cached in `init` — `@Observable` only tracks property access that happens *during* body evaluation, so calling the builder there is what keeps the strip live as samples tick.
- **`if index > 0 { divider }`** beats interleaving divider elements or `.padding`/overlays: one rule, no off-by-one, and it adapts when `compactMap` removes a tile.
- **`ForEach(Array(_.enumerated()), id: \.element.id)`** — enumerate to get the index for the divider rule; key on the element's stable `id`, never the array index (index keys break animations/state on reorder).
- This is the seam a **settings "stat selection"** feature hooks into: persist `[StatKind]` (enabled + order) and apply it in `visibleStats` — the views never change again.

**Best for:** any SwiftUI row/grid of structurally-identical items that's grown past ~4–5 literal children, especially when you'll later let users toggle/reorder them. Pairs with #66/#68/#69 (the stats it renders) and #67 (fixed-width `widestValue` templates per tile).
