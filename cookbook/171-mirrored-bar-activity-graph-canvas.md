# 171 — Mirrored bar activity graph in a SwiftUI Canvas

**Tags:** Canvas, GraphicsContext, sparkline, bar chart, mirrored graph, two series, rolling peak, normalization, ring buffer, history buffer, iStat Menus, network graph, disk IO graph, Swift Charts alternative, jitter-free width

**Extracted from:** QuickStatsPanel (2026-07-27, D-025)

## What this is for

A live two-series history graph — upload above a baseline, download below — small enough for a
34pt HUD slot and legible enough for a detail card. The form iStat Menus uses for Network and
Disk. Hand-drawn in `Canvas`; no chart library.

## Why not Swift Charts

Swift Charts brings axes, insets, gridlines and animation curves that read as *system chrome*.
Against a flat self-drawn surface it looks pasted in. It is also an order of magnitude past what
this needs: a comparable production `TrendChart.swift` with least-squares regression ran 437 lines
for an analytics window. The Canvas version below is the whole renderer.

## The three non-obvious parts

**1. Normalize each series to its OWN peak, and print that peak.**
Real measurement: a link doing **34.0 MB/s** down and **124 KB/s** up — a 274× spread. On a shared
scale the upload series is a fraction of a pixel and shows nothing. Per-series scaling makes both
readable, but it means the y-axis is *unlabelled and rebasing*, so a flat idle graph and a flat
saturated graph look identical. Printing the peak in a legend beside the graph is what makes that
honest — it is not decoration, it is the axis.

Percentage stats (CPU/GPU/memory) go the other way: fix the ceiling at 100, never rebase.

**2. The mirror is an accessibility feature, not just a style.**
Two series above/below a shared baseline are distinguished by **position**, so the graph survives
a greyscale/monochrome theme with no hue at all. A stacked or overlaid line chart cannot.

**3. Name the series by WHERE THEY DRAW, not by priority.**
`primary`/`secondary` collides with "which value the tile headlines" — for Network that's Download,
but the reference draws Upload on top. Two orderings under one word is how a graph ships mirrored
backwards. Use `upper`/`lower`.

## Renderer

```swift
struct GraphSeries {
    let values: [Double]          // oldest → newest, natural units
    let peak: Double              // value mapping to a full-height bar; never 0
    let peakFormatted: String?    // printed in the legend; nil for fixed-ceiling stats
}
struct GraphData { let upper: GraphSeries; let lower: GraphSeries? }

struct ActivityGraphView: View {
    let data: GraphData
    let width: CGFloat, height: CGFloat
    var barWidth: CGFloat = 2, barGap: CGFloat = 1

    var body: some View {
        Canvas { ctx, size in
            let slots = max(1, Int(size.width / (barWidth + barGap)))
            // Mirrored → baseline down the middle; single → baseline on the floor.
            let baseY = data.lower != nil ? size.height / 2 : size.height
            let halfH = data.lower != nil ? size.height / 2 : size.height

            var line = Path()
            line.move(to: CGPoint(x: 0, y: baseY))
            line.addLine(to: CGPoint(x: size.width, y: baseY))
            ctx.stroke(line, with: .color(.gray.opacity(0.4)),
                       style: StrokeStyle(lineWidth: 1, dash: [1, 2]))

            draw(data.upper, in: &ctx, slots: slots, baseY: baseY,
                 maxH: halfH, up: true, color: .pink)
            if let lower = data.lower {
                draw(lower, in: &ctx, slots: slots, baseY: baseY,
                     maxH: halfH, up: false, color: .blue)
            }
        }
        .frame(width: width, height: height)
        .accessibilityHidden(true)   // the value it annotates is already announced
    }

    private func draw(_ s: GraphSeries, in ctx: inout GraphicsContext, slots: Int,
                      baseY: CGFloat, maxH: CGFloat, up: Bool, color: Color) {
        let visible = s.values.suffix(slots)
        let firstSlot = slots - visible.count      // right-align: newest at the right edge
        for (i, v) in visible.enumerated() {
            let f = min(max(v / s.peak, 0), 1)
            guard f > 0 else { continue }
            let h = max(f * maxH, 1)               // floor: sub-pixel bars vanish entirely
            let x = CGFloat(firstSlot + i) * (barWidth + barGap)
            ctx.fill(Path(CGRect(x: x, y: up ? baseY - h : baseY,
                                 width: barWidth, height: h)), with: .color(color))
        }
    }
}
```

## Gotchas that bit

- **Guard `peak > 0` in the series initializer.** An idle series is all zeros → divide by zero →
  NaN bar heights → nothing renders and no error is raised.
- **Right-align, don't left-align.** A partly-filled buffer must grow leftward from "now", or the
  newest sample drifts rightward across the view as history accumulates.
- **Fixed width, derived bar count.** Deriving width from sample count makes the graph *grow* for
  the first minute after launch — which shifts every sibling view in a horizontal strip.
- **Size the history buffer by duration ÷ interval, not a fixed count.** With a user-configurable
  refresh interval, 60 samples means 60s at 1s and 5 minutes at 5s. Clear the buffer when the
  interval changes: splicing points from two time bases draws an x-axis that silently changes scale.
- **Peak state cannot live in the view.** Any strategy with memory across ticks (decay, session
  ratchet) needs storage outside the view, since SwiftUI rebuilds views every pass. Put it in the
  store — and note it will be called once per *body pass*, not once per sample, so a per-call decay
  step runs at a rate set by how many views are open. Idempotent strategies (window max, `max()`
  ratchet) are immune; decay needs a tick counter.

## Peak strategy — pick deliberately

When a spike scrolls off the left edge, `windowMax` drops in one tick and every remaining bar jumps
taller: a surge that never happened.

| Strategy | Behavior |
|---|---|
| `windowMax` | Always fills the height, best detail when quiet; phantom rescale, idle looks like saturated |
| decay toward `windowMax` | No phantom surge; reads slightly high for a second after a spike, needs a tick counter |
| `max(windowMax, previous)` | Stable and comparable session-wide; one huge burst flattens everything after it |
