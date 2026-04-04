## Timecode Display Typography

**Source:** `1-macOS/Penumbra/` (TimecodeView, ControlsRow, CurrentSelectionView)
**Use case:** Any video app displaying SMPTE timecode (HH:MM:SS:FF)

### The Problem

SF Mono (`.design(.monospaced)`) uses **slashed zeros** to distinguish `0` from `O`. This is correct for code editors but looks wrong in video timecode displays — professional NLEs like Final Cut Pro use clean round zeros.

### The Solution: SF Pro + `.monospacedDigit()`

```swift
// BAD — SF Mono, slashed zeros, too "code-like"
.font(.system(size: 32, weight: .light, design: .monospaced))

// GOOD — SF Pro with fixed-width digits, clean round zeros (FCP-style)
.font(.system(size: 32, weight: .thin).monospacedDigit())
```

### Weight Hierarchy for TC Displays

| Display | Weight | Rationale |
|---------|--------|-----------|
| Main TC (large, ~32pt) | `.thin` | Doesn't dominate the UI |
| Secondary TC (IN/OUT/DURATION, ~body) | `.light` | Readable at smaller size |
| Dimmed leading zeros | `.ultraLight` + `opacity(0.7)` | Subtle de-emphasis of `00:00:` prefix |

### NSFont Width Calculation (AppKit)

When using per-character layout with fixed-width frames, the `NSFont` for width measurement must match the rendered font:

```swift
// If rendering SF Pro .monospacedDigit(), measure with systemFont (NOT monospacedSystemFont)
let nsFont = NSFont.systemFont(ofSize: fontSize, weight: fontWeight.toNSFontWeight())
let digitWidth = NSAttributedString(string: "0", attributes: [.font: nsFont]).size().width
```

### Key Rule

**Timecode = `.monospacedDigit()`, Code = `.monospaced`**. Never use SF Mono for timecode in video apps.

---

