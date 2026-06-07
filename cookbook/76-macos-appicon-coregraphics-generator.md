# 76 · macOS app icon from a design spec — native Core Graphics generator

**Problem.** You have a vector icon design (gradient squircle shell + simple
shapes) specified in a web prototype (CSS/JSX, often with `oklch` colors), and you
need a real `AppIcon.appiconset` — all 10 macOS sizes + `Contents.json` — without
firing up Sketch/Figma/Icon Composer. You want it reproducible from source and
crisp at 16px.

**Solution.** A standalone Swift script (`swift GenerateAppIcon.swift <out-dir>`)
that draws the icon with Core Graphics **at each target pixel size** (not one
master PNG downscaled — downscaling smears 1px hairlines/bevels at 16–32px) and
emits the `.appiconset`. First-class on macOS (`import AppKit`), zero deps.

Used for: **QuickStatsPanel** ("Abstract bars" icon, from a design-handoff prototype).

---

## Three gotchas this solves

### 1. `oklch` → sRGB (CG and asset catalogs don't speak oklch)
Convert by hand once, hardcode the sRGB result with a comment. OKLab→linear→gamma:
`oklch(0.78 0.13 175)` → `rgb(65, 210, 179)` (cyan-green);
`oklch(0.80 0.14 92)` → `rgb(222, 186, 66)` (amber).
(If you have many, script it; for 2–3 accents, hand-convert and leave the oklch in
a comment so the source of truth is traceable.)

```swift
// oklch(L,C,H) → sRGB, for reference when adding new accents:
//   a=C·cos(H°), b=C·sin(H°)
//   l_=L+0.3963377774a+0.2158037573b; m_=L−0.1055613458a−0.0638541728b; s_=L−0.0894841775a−1.2914855480b
//   (l,m,s)=(l_,m_,s_)³
//   rLin=+4.0767416621l−3.3077115913m+0.2309699292s  (g,b rows similarly)
//   sRGB = lin≤0.0031308 ? 12.92·lin : 1.055·lin^(1/2.4)−0.055
let accent = NSColor(srgbRed: 65/255, green: 210/255, blue: 179/255, alpha: 1)
```

### 2. Render per-size, not downscaled
Make a fresh bitmap context per pixel size and draw with proportions scaled to that
size. The macOS continuous-corner ratio is **0.2237 × size**.

```swift
func renderPNG(pixelSize: Int) -> Data {
    let ctx = CGContext(data: nil, width: pixelSize, height: pixelSize,
        bitsPerComponent: 8, bytesPerRow: 0, space: CGColorSpaceCreateDeviceRGB(),
        bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue)!
    ctx.setAllowsAntialiasing(true); ctx.interpolationQuality = .high
    drawIcon(size: CGFloat(pixelSize), into: ctx)        // all metrics scale off `size`
    let rep = NSBitmapImageRep(cgImage: ctx.makeImage()!)
    return rep.representation(using: .png, properties: [:])!
}
```

Inside `drawIcon`, derive a unit scale `u = size / <prototype reference edge>` and
multiply the prototype's px constants by `u` (corner radius uses `0.2237 * size`
directly). **CG's y-axis is bottom-up** — the icon's *top* is `y = size`, so a
top→bottom CSS gradient runs `start:(x, size) → end:(x, 0)`.

### 3. Emit the full macOS set + both `Contents.json`
macOS needs 10 entries (px = pt × scale): 16@1,16@2,32@1,32@2,128@1,128@2,256@1,
256@2,512@1,512@2 → pixels 16,32,32,64,128,256,256,512,512,1024.

```swift
struct Entry { let size: Int; let scale: Int; let px: Int }
let entries = [Entry(16,1,16),Entry(16,2,32),Entry(32,1,32),Entry(32,2,64),
  Entry(128,1,128),Entry(128,2,256),Entry(256,1,256),Entry(256,2,512),
  Entry(512,1,512),Entry(512,2,1024)]   // (use a memberwise init)
// write one PNG per entry; images[] = {idiom:"mac", size:"NxN", scale:"Mx", filename}
// then JSONSerialization → AppIcon.appiconset/Contents.json
```
Also write the **catalog-level** `Assets.xcassets/Contents.json`
(`{"info":{"author":"xcode","version":1}}`) or Xcode won't see the catalog.

---

## Wiring into an xcodegen project
1. Put `Assets.xcassets/` under a path already in the target's `resources:`
   (e.g. `Sources/<App>/Resources/`). No `project.yml` `resources` change needed if
   the parent dir is already globbed.
2. Add the build setting (this is the bit people miss):
   ```yaml
   targets:
     <App>:
       settings:
         base:
           ASSETCATALOG_COMPILER_APPICON_NAME: AppIcon
   ```
3. `xcodegen generate` → build. Verify: `actool` logs
   `Emplaced .../AppIcon.icns`, and the built `Contents/Info.plist` has
   `CFBundleIconName = AppIcon` (`PlistBuddy -c "Print :CFBundleIconName"`).

## Notes
- **`LSUIElement` (agent) apps don't show the icon in Dock or Cmd-Tab** — it
  appears in Finder / Get Info only. Still worth shipping.
- The generator is re-runnable, so design tweaks are a one-line edit + re-run, and
  the `.swift` source stays in the repo as the icon's source of truth (e.g.
  `02_Design/icon-gen/GenerateAppIcon.swift`).
- Drop CSS-only effects that don't apply to an opaque raster icon (`backdrop-filter`
  blur, prototype's ~1.5× display scale).

## See also
- `67-swiftui-jitter-free-numeric-readout.md`, `70-swiftui-data-driven-tile-strip.md` (same app)
- `77-jsx-prototype-to-png-webkit-playwright.md` — render the design prototype itself to PNGs
