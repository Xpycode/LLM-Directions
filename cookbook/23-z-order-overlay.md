## Z-Order Overlay Dimming

**Source:** `1-macOS/CropBatch/` — `CropEditorView.swift` (v1.5)

When interactive content (blur regions, annotations, etc.) can extend outside a valid area (crop boundaries, selection, etc.), use z-order to visually communicate "this part is excluded" without explicit badges or warnings.

```swift
ZStack {
    // Layer 1: The image
    scaledImageView

    // Layer 2: Interactive content (blur regions with live preview)
    BlurEditorView(...)      // Can draw/move/resize regions here

    // Layer 3: Semi-transparent overlay darkening excluded areas
    CropOverlayView(...)     // .allowsHitTesting(false) internally!

    // Layer 4: Primary controls on top (crop handles)
    CropHandlesView(...)     // Takes gesture priority
}
```

**Key rules:**

1. The overlay (Layer 3) MUST have `.allowsHitTesting(false)` so gestures pass through to interactive content below
2. Primary controls (Layer 4) sit on top of everything and take gesture priority
3. Interactive content below the overlay remains fully functional — drag, resize, tap all work through the overlay

**Before (badges):**
```
[Blur Region] ⚠️ "Partially outside crop"
[Blur Region] ❌ "Fully outside crop"
```

**After (z-order dimming):**
- Region inside crop: fully visible with live blur preview
- Region partially outside: visible part bright, excluded part naturally dimmed
- Region fully outside: entirely dimmed under dark overlay

**Why it works:** Users intuitively understand "dark = excluded." No cognitive load from reading badge icons. The visual feedback is continuous (partial dimming) rather than binary (badge/no badge).

**Anti-pattern:** Don't put interactive content ON TOP of the overlay — it fights with primary controls for gesture priority. Keep it underneath and let the overlay be visual-only.

**Trigger:** Any time you have interactive overlays that can extend beyond a valid boundary (crop area, artboard, selection mask, viewport, etc.).

---

*Generated from production code across Penumbra, Phosphor, Directions, MusicServer, AppUpdater, CropBatch, QuickMotion, WindowMind, and other projects.*
