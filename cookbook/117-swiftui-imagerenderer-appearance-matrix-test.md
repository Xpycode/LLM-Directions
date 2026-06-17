# 117 — ImageRenderer appearance/theme snapshot testing (verify a Theme system PAINTS the right tokens)

**Best for:** proving a SwiftUI theme system (Light/Dark × presets) actually *renders* the right colors —
not just that the resolver returns them. A pure-function test (`make(scheme:preset:) == expected`) proves
the resolver; this proves the next link: the **real views**, wired through the **real environment-injection
path**, paint those tokens. Permission-free, deterministic, headless XCTest via `ImageRenderer`. Reusable
across any Theme-based macOS app (Penumbra, ClipSmart, Aloft, LaunchAway).

**Source:** LaunchAway `01_Project/LaunchAwayTests/AppearanceMatrixRenderTests.swift` (Bug-2 Wave 7).

---

## Why ImageRenderer

`ImageRenderer` renders a SwiftUI tree off-screen with **no window** and **no Screen-Recording
permission**, and it **honors `.environment` overrides** — so you can drive the appearance per combo and
sample the result. Because theme tokens are explicit sRGB `Color`s (not semantic `.primary` etc.), a
sampled pixel is directly comparable to the resolver value regardless of the renderer's own appearance.

It is the headless-verification sibling of #73 (verify HUD without screen recording): when you can't (or
don't want to) drive the live app, render the view tree and inspect pixels.

---

## The four hard-won gotchas (each cost real time)

### 1. Headless render has a ~0.035 gamma bias → don't assert absolute pixels tightly; lead with bias-immune checks
A near-white token (`#F4F5F7`, green 0.961) samples back as green ~0.930 — **red exact, green/blue ~0.035
low**, consistently, *tracking the token* (all light presets shift identically). It is a **measurement
artifact**, not app error. So:
- **Lead with luminance polarity** — a Light surface MUST be bright (`>0.5`), a Dark surface MUST be dim
  (`<0.2`). This is exactly the original "Light renders Dark" bug, and luminance is immune to a G/B hue bias.
- **Use a differential for translucent fills** — render selected-vs-rest over the same backdrop and assert
  the *delta* (cancels the systematic bias). A teal `selectionFill` raises green & blue more than red; a
  white `hoverFill` raises all three equally — so `(ΔG − ΔR) > 0.03 && (ΔB − ΔR) > 0.03` proves it's the
  teal token and not the wrong one, in both schemes, without any absolute color match.
- **Compute contrast (AC6) from resolved tokens, not sampled pixels** — WCAG luminance/ratio on the
  `make()` values; catches white-on-light-fill class bugs deterministically.
- Absolute token asserts are still useful as corroboration, but at a tolerance sized to the measured bias
  (~0.06), which is still ≪ the ~0.87 Light↔Dark distance, so a wrong scheme/preset still fails hard.

### 2. ImageRenderer can't render `NSViewRepresentable` or lazy containers headless
`TextField` (NSTextField-backed) and `NSVisualEffectView` render as an AppKit **"unsupported" placeholder**
(a yellow bar / circle-slash), and `ScrollView` + `LazyVStack` materializes **nothing** (no viewport).
- For **pixel asserts**: render leaf views directly (`ResultRowView` at a fixed frame), not inside the
  ScrollView; render the surface with an *empty* state so no lazy list is needed.
- For an **eyeball montage**: swap the hostile views for static equivalents — a `Text` placeholder for the
  live `TextField`, a non-lazy `VStack` of the real rows, and a solid fill for a blur material (the live
  blur genuinely can't be shown headless — note that explicitly).

### 3. `scale = 1` so 1px == 1pt
`ImageRenderer.scale` defaults to the display scale (2 on Retina). Set `renderer.scale = 1` for assert
renders so your sample coordinates map directly to layout points. Use scale 2 only for crisp montage output.

### 4. An sRGB-context redraw leaving samples byte-identical is the *tell* that the shift is pipeline gamma
If you suspect a colorspace-*read* bug, redraw the CGImage through an explicit sRGB `CGContext` and
re-sample. If the numbers don't budge, the CGImage was already sRGB and the shift is render-pipeline gamma —
stop chasing colorspace, switch to the bias-immune checks above.

---

## Core helpers

```swift
import XCTest
import SwiftUI
import AppKit
@testable import YourApp

@MainActor
final class AppearanceMatrixRenderTests: XCTestCase {

    // Auto folds into {light,dark} — it's not a distinct palette, it RESOLVES to one at runtime.
    private let schemes: [ColorScheme] = [.light, .dark]
    private let presets: [ThemeManager.Preset] = [.graphite, .ink, .paper, .glass]

    /// Render → sRGB bitmap at scale 1 (1px == 1pt). The sRGB-context redraw normalizes the
    /// display-colorspace CGImage so samples are true sRGB (and proves gotcha #4).
    private func render<V: View>(_ view: V, width: CGFloat, height: CGFloat) throws -> NSBitmapImageRep {
        let r = ImageRenderer(content: view.frame(width: width, height: height))
        r.scale = 1
        guard let cg = r.cgImage else { throw Err.failed }
        let w = cg.width, h = cg.height
        guard let cs = CGColorSpace(name: CGColorSpace.sRGB),
              let ctx = CGContext(data: nil, width: w, height: h, bitsPerComponent: 8, bytesPerRow: 0,
                                  space: cs, bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue)
        else { throw Err.failed }
        ctx.draw(cg, in: CGRect(x: 0, y: 0, width: w, height: h))
        guard let out = ctx.makeImage() else { throw Err.failed }
        return NSBitmapImageRep(cgImage: out)
    }
    enum Err: Error { case failed }

    private func avg(_ rep: NSBitmapImageRep, _ pts: [(Int, Int)]) -> NSColor {
        var r = 0.0, g = 0.0, b = 0.0, n = 0.0
        for (x, y) in pts {
            guard let c = rep.colorAt(x: x, y: y)?.usingColorSpace(.sRGB) else { continue }
            r += Double(c.redComponent); g += Double(c.greenComponent); b += Double(c.blueComponent); n += 1
        }
        return n > 0 ? NSColor(srgbRed: r/n, green: g/n, blue: b/n, alpha: 1) : .clear
    }

    private func luminance(_ c: NSColor) -> Double {
        let s = c.usingColorSpace(.sRGB) ?? c
        func lin(_ v: CGFloat) -> Double { let d = Double(v); return d <= 0.03928 ? d/12.92 : pow((d+0.055)/1.055, 2.4) }
        return 0.2126*lin(s.redComponent) + 0.7152*lin(s.greenComponent) + 0.0722*lin(s.blueComponent)
    }
    private func contrast(_ a: NSColor, _ b: NSColor) -> Double {
        let la = luminance(a), lb = luminance(b); let hi = max(la, lb), lo = min(la, lb)
        return (hi + 0.05) / (lo + 0.05)
    }
}
```

## The three assertion shapes

```swift
// (A) Surface — luminance polarity is the bug guard; absolute token is corroboration (tol ~0.06).
func testPanelSurface() throws {
    for scheme in schemes {
        for preset in presets where preset != .glass {   // glass blur unrenderable headless; fallback == solid line
            let theme = ResolvedTheme.make(scheme: scheme, preset: preset)
            let rep = try render(RootView().environment(\.theme, theme), width: 600, height: 80)
            let lum = luminance(avg(rep, [(150,6),(300,6),(450,6)]))   // flat top band
            if scheme == .light { XCTAssertGreaterThan(lum, 0.5) } else { XCTAssertLessThan(lum, 0.2) }
        }
    }
}

// (B) Translucent fill — selected-vs-rest DIFFERENTIAL (cancels gamma bias, IDs the teal token).
func testSelectionFillIsTeal() throws {
    let pts = [(540,24),(560,24),(575,24)]
    for scheme in schemes { for preset in presets {
        let t = ResolvedTheme.make(scheme: scheme, preset: preset)
        let rest = avg(try render(rowOver(t, selected: false), width: 600, height: 48), pts)
        let sel  = avg(try render(rowOver(t, selected: true),  width: 600, height: 48), pts)
        let dR = Double(sel.redComponent - rest.redComponent)
        let dG = Double(sel.greenComponent - rest.greenComponent)
        let dB = Double(sel.blueComponent - rest.blueComponent)
        XCTAssertGreaterThan(max(abs(dR),abs(dG),abs(dB)), 0.02)   // a fill is drawn
        XCTAssertGreaterThan(dG - dR, 0.03)                        // teal, not white hover
        XCTAssertGreaterThan(dB - dR, 0.03)
    }}
}

// (C) Readability — WCAG contrast from RESOLVED tokens (not sampled), all combos incl. glass.
func testContrast() {
    for scheme in schemes { for preset in presets {
        let t = ResolvedTheme.make(scheme: scheme, preset: preset)
        XCTAssertGreaterThanOrEqual(contrast(NSColor(t.primaryText), NSColor(t.primaryBackground)), 4.5)
        XCTAssertGreaterThanOrEqual(contrast(NSColor(t.accent), NSColor(t.primaryBackground)), 3.0)
    }}
}
```

**ThemedRoot link:** to test the injector itself, drive `.environment(\.colorScheme, scheme)` on
`ThemedRoot { ThemeProbe() }` (set the global preset first, restore in `defer`) where `ThemeProbe`
fills with the injected `theme.primaryBackground` — proves colorScheme+preset → `make()` → injected.

**Montage for owner sign-off:** render each combo to an `NSImage`, tile into a labelled grid with
`NSImage.lockFocus()` + `NSAttributedString.draw`, write PNG. Gitignore the output dir (regenerates each
`xcodebuild test`).

---

**Pairs with:** #73 (headless verification mindset — verify without screen recording), #113
(`NSApp.appearance` is the real appearance axis), #00 (App Shell Standard / `Theme`), #70 (the data-driven
result strip these views render). **Folds into the routing fix it verifies:** route the light/dark axis
through `@Environment(\.theme)` injected by a `ThemedRoot` that reads `@Environment(\.colorScheme)` — a
`Theme.*` static that reads `NSApp.effectiveAppearance` is untracked and never repaints on a live OS toggle.
