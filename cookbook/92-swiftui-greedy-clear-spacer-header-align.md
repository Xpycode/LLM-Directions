# 92 — Greedy `Color.clear`/`Spacer` balloons a row; pad-based inset to align a header over list columns

**Problem.** You're adding a Finder-style **clickable column header** above a custom list (each row is
an `HStack` of checkbox · disclosure · thumbnail · flexible title · fixed meta columns). Two things
go wrong:

1. **The header bar balloons vertically.** You reserved the left slots with
   `Color.clear.frame(width: 14)` (and friends) so the header's first label lines up with the row
   title. The bar suddenly fills half the pane, labels floating in a tall band.
2. **A header label wraps** ("DURATION" → "DURATI/ON") because the label is wider than the narrow
   numeric column it sits over.

**Why (1) happens.** `Color.clear` and `Spacer` are **greedy in any axis you don't constrain**.
`Color.clear.frame(width: 14)` pins *width* to 14 but leaves *height* unbounded → the view expands to
the full height its parent offers. In an `HStack`, the tallest child sets the row height, so one
unbounded-height `Color.clear` drags the whole bar to fill the available vertical space (and the real
labels get centered in the void). Same trap with `Spacer()` used as a vertical strut.

## Pattern — reserve the leading inset with **padding**, not greedy spacers; share column widths; cap lines

Don't reserve horizontal slots with greedy fillers. Compute the leading inset once (sum of the row's
leading element widths + gaps) and apply it as `.padding(.leading, …)`. Share every column width
between the header and the rows through one constants enum, so they can't drift. Add `.lineLimit(1)`
and size the numeric columns wide enough for their header word.

```swift
/// One source of truth for column geometry — header and rows both read it, so a width change moves
/// both together (no drift).
enum RowMetrics {
    static let checkbox: CGFloat = 14
    static let chevron:  CGFloat = 18
    static let thumb:    CGFloat = 38 * 16 / 9     // must equal the row's thumbnail width
    static let lead:     CGFloat = 12              // HStack spacing between leading slots
    static let rowPadH:  CGFloat = 16              // row + header horizontal padding
    static let metaSpacing: CGFloat = 18
    static let filesCol:    CGFloat = 60
    static let durationCol: CGFloat = 80           // wide enough for "DURATION" + the sort arrow
    static let sizeCol:     CGFloat = 64

    /// Content-edge → row-title offset: everything left of the title, plus the gaps.
    static let leadingInset = checkbox + lead + chevron + lead + thumb + lead
}

struct ColumnHeaderBar: View {
    var body: some View {
        HStack(spacing: 0) {
            HStack(spacing: 14) {                  // left cluster — sits over the flexible title
                SortLabel(.name, "Name")
                SortLabel(.date, "Date")           // a row sub-line, not its own column → grouped here
            }
            Spacer(minLength: 8)
            HStack(spacing: RowMetrics.metaSpacing) {   // right cluster — pixel-aligns over the rows
                Text("FILES").frame(width: RowMetrics.filesCol, alignment: .trailing)
                SortLabel(.duration, "Duration", width: RowMetrics.durationCol)
                SortLabel(.size,     "Size",     width: RowMetrics.sizeCol)
            }
        }
        .lineLimit(1)                              // never wrap a header word
        // Padding (NOT Color.clear) reserves the leading slot — no greedy vertical growth.
        .padding(.leading, RowMetrics.rowPadH + RowMetrics.leadingInset)
        .padding(.trailing, RowMetrics.rowPadH)
        .padding(.vertical, 5)
        .background(Color.black.opacity(0.12))
        .overlay(alignment: .bottom) { Divider() }
    }
}
```

The right cluster aligns because both the header and each row end with the **same fixed-width columns,
same spacing, same trailing padding** — so their right edges coincide regardless of the flexible
middle. The left labels align because the header's leading padding equals the row's leading element
stack. A column whose *header word* is wider than its *data* (a numeric column under "DURATION") just
gets a wider shared width — the data stays right-aligned inside it.

## Gotchas

- **If you must use `Color.clear` as a spacer, give it a finite height** (`.frame(width: 14, height: 0)`
  or a fixed bar height). Width-only `.frame` leaves height greedy.
- The header can only align to **fixed-width** row columns. A flexible/`maxWidth: .infinity` title
  column has no fixed position, so don't try to pin a header label over it — group those labels on the
  left and pad to where the title *starts*.
- Keep the thumbnail width identical in `RowMetrics` and the actual thumbnail view, or the left inset
  drifts by a few points.
- Mixing two spacings in one `HStack` isn't possible (one `spacing:` value) — use nested `HStack`s
  (tight inner spacing for grouped labels, wider for the meta cluster).

## When to reach for it

Any custom (non-`Table`) SwiftUI list that wants Finder-style sortable/aligned column headers, or any
time a header/footer row must line up with row columns. Also the first thing to check whenever a
`VStack`/`HStack` element is **mysteriously too tall or too wide** — look for a `Color.clear` or
`Spacer` with an unconstrained axis.

— Extracted from Conjoyn (`Views/RecordingsList.swift`, sortable recordings columns, 2026-06-12).
