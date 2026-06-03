## macOS Favicon Generation — QuickLook Renders What ImageMagick Can't + Glyph-Only 16px

**Source:** `aloft.lucesumbrarum.com` — generating a favicon set from the app's icon SVG on a Mac with no `rsvg-convert`. Added 2026-06-03.

**Use case:** You have an app-icon SVG (squircle clip-path, gradients, fine detail) and need the standard favicon set — `favicon.ico`, `favicon-16.png`, `favicon-32.png`, `apple-touch-icon.png` — rendered at high fidelity, on macOS, without installing extra tooling or paying a favicon-generator site.

**When to reach for it:**
- macOS dev box; the icon is a real SVG with gradients / `clipPath` / masks (not flat shapes).
- ImageMagick is installed but `rsvg-convert` / Inkscape are not.
- The icon is detailed enough that a naive downscale produces a muddy 16×16.

**When *not* to use it:**
- Icon is trivial flat geometry — ImageMagick's built-in renderer may suffice; skip the QuickLook hop.
- You're on Linux/CI — install `librsvg` (`rsvg-convert`) or `resvg`; QuickLook is macOS-only.
- You have a designer-exported PNG master already — start from that, skip rendering entirely.

---

### Trap 1 — ImageMagick can't render real SVGs without a delegate

ImageMagick's SVG "support" is a delegate to `rsvg-convert`. If that binary is absent it silently falls back to the built-in **MSVG** renderer, which mishandles `clipPath` and gradients — you get a **near-empty PNG** (a few hundred bytes), not an error.

```bash
magick -list delegate | grep svg     # svg => "'rsvg-convert' …"  ← needs the binary
which rsvg-convert                    # …not found  → MSVG fallback → blank output
magick icon.svg -resize 1024x1024 master.png
ls -l master.png                      # 455 bytes = it rendered NOTHING. Red flag.
```

**Fix: render with QuickLook (WebKit) — the same engine a browser uses.** High fidelity, already on every Mac:

```bash
# -t thumbnail, -s size, -o output DIR (writes <name>.svg.png into that dir)
qlmanage -t -s 1024 -o /tmp/fav icon.svg
file /tmp/fav/icon.svg.png            # PNG image data, 1024 x 1024, RGBA  ✓
```

ImageMagick is still the right tool for the *raster* steps (downscaling with `-filter Lanczos`, packing `.ico`) — it just can't be the SVG *renderer*. Pipeline: **QuickLook renders → ImageMagick resizes/packs.**

---

### Trap 2 — a detailed icon turns to mush at 16px

A 1024px master downscaled to 16×16 collapses: the white card becomes a grey blob, the glyph washes out against a light tab. Inspect by upscaling nearest-neighbour (so you see actual pixels):

```bash
magick master.png -filter Lanczos -resize 16x16 favicon-16.png
magick favicon-16.png -filter point -resize 256x256 preview-16.png   # eyeball this
```

**Fix: author a separate, simplified source for 16px** — drop the card/text, keep one bold high-contrast glyph:

```xml
<!-- aloft-favicon-glyph.svg : bold I-beam only, on the linen squircle bg -->
<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 120 120">
  <defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#f8f6f0"/><stop offset="1" stop-color="#ece7db"/>
  </linearGradient></defs>
  <rect width="120" height="120" rx="27" fill="url(#bg)"/>   <!-- rx approximates the squircle at small size -->
  <g fill="#0a84ff">
    <rect x="52" y="28" width="16" height="64" rx="4"/>      <!-- stem -->
    <rect x="33" y="26" width="54" height="14" rx="5"/>      <!-- top bar -->
    <rect x="33" y="80" width="54" height="14" rx="5"/>      <!-- bottom bar -->
  </g>
</svg>
```

Commit this SVG — the favicon is then *reproducible*, not a mystery binary, and survives a brand-colour change.

---

### A `.ico` is a container, not an image — pack different sources per size

`.ico` holds multiple independent bitmaps; the OS/browser picks the closest. Most generators stuff the *same* downscaled image into every slot — that's how you get a muddy 16px. Pack the **glyph at 16, the full icon at 32/48**:

```bash
FULL=/tmp/fav/icon.svg.png
GLYPH=/tmp/fav/aloft-favicon-glyph.svg.png   # qlmanage-rendered

magick "$GLYPH" -filter Lanczos -resize 16x16 favicon-16.png        # 16 = glyph
magick "$FULL"  -filter Lanczos -resize 32x32 favicon-32.png        # 32 = full icon

# apple-touch: flatten onto opaque brand colour — iOS composites over BLACK,
# so the squircle's transparent corners would show as black notches otherwise.
magick "$FULL" -filter Lanczos -resize 180x180 -background "#f4f1ea" -flatten apple-touch-icon.png

# multi-image .ico: glyph-16 + full-32 + full-48
magick "$GLYPH" -filter Lanczos -resize 16x16 /tmp/fav/i16.png
magick "$FULL"  -filter Lanczos -resize 32x32 /tmp/fav/i32.png
magick "$FULL"  -filter Lanczos -resize 48x48 /tmp/fav/i48.png
magick /tmp/fav/i16.png /tmp/fav/i32.png /tmp/fav/i48.png favicon.ico

magick identify favicon.ico            # confirm 16x16, 32x32, 48x48 frames present
magick "favicon.ico[0]" -filter point -resize 256x256 check16.png   # verify [0] is the glyph
```

The HTML wiring (same on every page):

```html
<link rel="icon" href="/favicon.ico" sizes="any" />
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32.png" />
<link rel="icon" type="image/png" sizes="16x16" href="/favicon-16.png" />
<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png" />
```

---

### Why it works
- **QuickLook = WebKit** → renders SVG exactly as Safari would, including `clipPath` + gradients ImageMagick's MSVG can't.
- **`.ico` is a multi-resolution container** → exploiting it with a simpler 16px source is using the format as designed (same principle as road signs shedding detail at distance: legibility-at-size beats fidelity-to-original).
- **apple-touch flattening** → iOS applies its own mask over a black backdrop; an opaque brand-coloured fill prevents black-corner artefacts.

### Common mistakes
- **Trusting ImageMagick's exit code** → it "succeeds" producing a blank PNG. Always check output byte size / `file` dims after an SVG render.
- **One source for all `.ico` sizes** → muddy 16px. Pack a glyph at 16.
- **Transparent apple-touch-icon** → black corners on the iOS home screen. Flatten on an opaque colour.
- **Aggressive favicon caching** → browsers cache favicons hard; a post-deploy tab still showing the old/blank icon may just need a hard refresh or cache clear, not another rebuild.
- **`qlmanage` output naming** → it writes `<inputname>.svg.png` into the `-o` *directory*; don't pass a filename as `-o`.

### Pairs well with
- **#62 web auto dark theme** — same site/session; the favicon's accent matches the theme accent token.
- **#39 design-tokens** — the glyph SVG should use the brand's accent hex straight from the token palette.
