# Jitter-free numeric readout — hidden worst-case template + monospaced digits

**Source:** `1-macOS/QuickStatsPanel/` — `Views/StatTileView.swift` (2026-06-04, v0.1.0). Simpler, general form of Penumbra's `TimecodeView`.

A live-updating number (stat readout, timecode, countdown, rate) makes its container **resize and shift every time the value changes width** — "9,2 GB" → "284,76 GB", "7%" → "100%". In a content-sized window/panel that means the whole layout dances; even in a fixed layout, neighbouring elements jump. Two cheap pieces stop it cold:

**1. Monospaced digits** so digits don't shimmy as they change (`111` and `888` occupy the same width). `.monospacedDigit()` on the font — but note this only equalizes *digit* width, **not** digit *count*; "9 GB" and "284 GB" still differ.

**2. A reserved worst-case field** so the count can't change the width either. Stack a **hidden** `Text(widestValue)` behind the real value: the hidden template sizes the field to the worst case, the visible value rides on top.

```swift
ZStack(alignment: .leading) {
    Text(widestValue).hidden()        // e.g. "888,88 GB" or "100%" — reserves max width
    Text(value)                       // the live value, left-aligned in the reserved field
}
.font(Theme.Fonts.value)              // ...with .monospacedDigit()
.foregroundStyle(Theme.Colors.primaryText)
```

Pass the worst-case string per field — `"100%"` for a percentage, `"888,88 GB"` for a byte readout at GB scale (`ByteCountFormatter` switches GB→TB before 1000 GB, so 3 integer digits is the max; a narrower "8,88 TB" fits the same field). The field then holds constant width regardless of the value, so the container (and everything after it) never moves.

**Why the hidden-template trick beats manual measurement:** Penumbra's `TimecodeView` measures glyph widths with `NSAttributedString(...).size()` and frames each character — precise but verbose, and it must recompute on every font change. The hidden `Text` is one line, lives in the same font (so it auto-rescales if you change the font/size), and needs no `@State` or `onChange`. Use per-glyph framing only when you need individual characters to align across rows (a true timecode grid); for a single value field, the template is enough.

**Composes with content-sized panels.** If the panel/window sizes itself to its content (e.g. `NSHostingView.fittingSize`), fixed-width fields make that measurement **stable** — the panel still auto-grows when you *add* a field, but never jitters as values change. The two techniques are complementary, not alternatives.

**Gotchas**
- **`.monospacedDigit()` alone is not enough** — it fixes digit width, not string length. You need the reserved field for the count, and the field for the shimmer. Both.
- **Only digits are monospaced** — the separator (`,`/`.`), space, and unit letters ("GB") stay proportional, so the template must use the *same* non-digit characters as the real value for an exact width match (negligible in practice — digits dominate).
- **Worst-case = some trailing whitespace** when the value is short (reserving "888,88 GB" but showing "17 GB"). That's the deliberate trade: positional stability for a little dead space. Tighten the template to the actual range (e.g. "88,88 GB") if you control the data bounds and want it snugger — at the cost of jitter if the value ever exceeds it.
- **Right-align** the value in the field (`alignment: .trailing`) if you want units to line up in a vertical column; **left-align** if the field sits inline in a row and you'd rather the gap fall at the trailing edge.

**Best for:** any HUD/strip/menu-bar readout with live numbers, timecodes, or rates where the surrounding layout must stay still. Pairs with #65 (NSPanel HUD), #66 (disk stats that feed the readout), #27 (TimelineView elapsed/countdown), #39 (design tokens for the font).
