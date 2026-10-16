# Conjoyn Website — CLAUDE.md

## Project

Dedicated marketing/product website for **Conjoyn**, a native macOS app that losslessly
re-joins split DJI drone / action-camera recordings back into single files.
- **URL:** conjoyn.lucesumbrarum.com (subdomain configured; repoint to `/CONJOYN/` to go live)
- **Brand:** Luces Umbrarum / Xpycode
- **App tagline:** "Split recordings, made whole."
- **App one-liner:** Finds the pieces of a card-split recording and joins them back into one
  lossless file — fixing the date, timecode, and telemetry automatically.

## Style Reference

**Inherits the shared design system** (`css/site.css`, copied verbatim from Aloft —
the Luces Umbrarum standard). Do **not** diverge `site.css`; put all per-site changes in
`css/conjoyn.css`.

Per-site theming (the one thing that differs between sites):
- Fonts: `Instrument Serif` (display) + `Inter` (body) via Google Fonts — shared.
- **Accent: molten-weld orange** `--accent: #F0622A` (light) / `#FF7A45` (dark) — Conjoyn's
  own brand color (Aloft is Apple blue). Lives at the top of `css/conjoyn.css`. To recolor the
  whole site, change `--accent` / `--accent-soft` and their dark-mode twins — nothing else.
- Icon: `img/icons/conjoyn.svg` (copied from
  `1-macOS/Conjoyn/02_Design/conjoinAppIcon/export/Conjoyn-Icon-Master.svg`).

## Site Structure

| Page | Path | Status |
|------|------|--------|
| Landing | `01_Source/index.html` | **live** (2026-06-16) |
| Changelog | `01_Source/changelog.html` | todo |
| Privacy / Support | — | todo (mirror Aloft if needed) |

## Outstanding

- [x] **Screenshots — dark set** (2026-06-16) — `conjoyn-{hero,groups,queue}-dark.webp` from the app's
      bundled Help captures (`main-loaded` → hero, `recordings-expanded` → groups, `queue-running` →
      queue). Source PNGs at `1-macOS/Conjoyn/01_Project/Conjoyn/Help/`. These are composited
      floating-window shots (transparent pad; the `.shot` card's `--surface-card` shows through).
- [x] **Screenshots — light set** (2026-07-10) — the app gained a **light mode**, so the `-light.webp`
      slots now hold real light captures (previously byte-identical dark placeholders). Mapping:
      hero ← `Conjoyn-LiteMode-5` (queue money shot — job Done ✓ + byte-exact verify + telemetry),
      groups ← `LiteMode-1` (Splits auto-detected & pre-selected), queue ← `LiteMode-4` (Verifying —
      true twin of the dark queue slot). Source PNGs at `1-macOS/Conjoyn/03_Screenshots/`. Hero `<img>`
      alt updated to match the money shot (dark hero still shows the recordings list — a deliberate
      light≠dark call). Then **composited to match the dark set's floating-window treatment**: window
      at 91.7% width, rounded corners (r≈40px), soft drop shadow + transparent margins → **1600×1080
      alpha WebP**. Geometry measured off the `-dark.webp` (window 1468×1185 in a 1600×1310 canvas;
      margins L/R=66, T=45, B=80; shadow bleed ~40px). Recipe: `magick <png> -resize 1467x946! \(
      -size 1467x946 xc:black -fill white -draw 'roundrectangle 0,0,1466,945,40,40' -alpha off \)
      -compose CopyOpacity -composite -compose Over \( +clone -background black -shadow 45x16+0+16 \)
      +swap -background none -layers merge +repage -gravity center -background none -extent 1600x1080`
      → `cwebp -q 80 -alpha_q 90`. **Gotcha:** the `-compose Over` reset is required — `CopyOpacity`
      leaks into `-layers merge` and blanks the whole image otherwise.
- [x] **OG image** (2026-06-16) — `img/og/conjoyn.jpg` (1200×630) made from `main-loaded.png` on a
      dark pad (`magick … -extent 1200x630`).
- [x] **Strato cutover** — not needed; `conjoyn.lucesumbrarum.com` was **already pointed** at
      `/CONJOYN/` (it 404'd only because the folder was empty). Deploying content made it live.
- [x] **Favicons** (2026-07-05) — generated `favicon.ico` (16/32/48), `favicon-16.png`, `favicon-32.png`
      and `apple-touch-icon.png` (180) from `img/icons/conjoyn.svg` via **QuickLook** (`qlmanage` — plain
      `magick` renders this SVG as a black square) then ImageMagick downscale. Wired into `index.html`
      + `imprint.html`, matching DiskVerdict/Aloft.
- [x] **Pricing** (2026-06-16) — **Free forever** + Ko-fi tip jar (not "during beta"). Copy says
      just "Free". Conjoyn stays in the free/tip-jar bucket; paid apps are Aloft & Penumbra only.
- [ ] **appcast.xml** — Sparkle appcast at `/appcast.xml` not yet on the site (in-app updates).

## Tech Stack

- Static HTML/CSS/JS (no build step) — same as Aloft/Penumbra.
- PHP: `dl.php` (download counter, app-agnostic via `?app=conjoyn`).
- Deploy: `./deploy.sh` → lftp mirror `01_Source/` → server `CONJOYN/`
  (shared `_deploy-common.sh`, `~/.netrc` + ROOT `.env`). Preview: `DRY_RUN=1 ./deploy.sh`.

## App Reference

- **Source:** `/Users/sim/ProgrammingProjects/1-macOS/Conjoyn/`
- **Design handoff / prototype:** `1-macOS/Conjoyn/02_Design/design_handoff_conjoyn/`
- **Bundle id:** `com.lucesumbrarum.conjoyn` · **Version:** 1.0 · **Min macOS:** 14.0 (Sonoma)
- **Updates:** Sparkle — appcast at `https://conjoyn.lucesumbrarum.com/appcast.xml`
  (the appcast.xml itself is NOT in this draft yet).
