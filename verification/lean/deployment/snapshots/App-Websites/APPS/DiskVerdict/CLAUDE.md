# DiskVerdict Website — CLAUDE.md

## Project

Dedicated marketing/product website for **DiskVerdict**, a native macOS app that runs a real
read/write benchmark on any volume and **interprets** the result — grading the drive for the
workflows you actually care about (video, photo, code, databases, VMs, audio, media server).
- **URL:** diskverdict.lucesumbrarum.com (subdomain — point at `/DISKVERDICT/` to go live)
- **Brand:** Luces Umbrarum / Xpycode
- **App tagline:** "Know what your drive is good for."
- **App one-liner:** Measures the real read/write speed of any volume, then tells you what it's
  actually good for — with the single statistic that decided each verdict.

## Style Reference

**Inherits the shared design system** (`css/site.css`, copied verbatim from Aloft —
the Luces Umbrarum standard). Do **not** diverge `site.css`; put all per-site changes in
`css/diskverdict.css`.

Per-site theming (the one thing that differs between sites):
- Fonts: `Instrument Serif` (display) + `Inter` (body) via Google Fonts — shared.
- **Accent: warm orange** `--accent: #E68033` (light) / `#F2944A` (dark) — DiskVerdict's own brand
  color (`ThemeManager.brandOrange`). Lives at the top of `css/diskverdict.css`. To recolor the
  whole site, change `--accent` / `--accent-soft` and their dark-mode twins — nothing else.
  > NB: close in hue to Conjoyn's `#F0622A` (both warm orange) — deliberate, pulled from the app.
- Icon: `img/icons/diskverdict-cream.svg` (light) + `diskverdict-plum.svg` (dark), copied from
  `1-macOS/DiskVerdict/02_Design/Icon/assets/svg/`. **The dochead icon is PINNED to the dark/plum
  variant** (2026-07-19) — a single `<img>`, no `<picture>` swap. Reason: the datasheet page is
  light-only, so swapping the icon on the *viewer's* OS scheme served no purpose and left a washed-out
  cream icon on cream paper for light-mode visitors. Pinned dark to match the portal carousel and the
  other sites. The `<link rel="icon">` also points at plum. **Still cream-derived:** the raster set
  (`favicon.ico`, `favicon-16/32.png`, `apple-touch-icon.png`) — regenerate from `-plum.svg` if the
  browser-tab icon should match. Do **not** re-add a `<picture>` swap to the dochead.
  > The three *screenshot* `<picture>` swaps are untouched and must stay — DiskVerdict's light and
  > dark captures are genuinely different images (verified by hash), unlike its icon.

## Site Structure

| Page | Path | Status |
|------|------|--------|
| Landing | `01_Source/index.html` | **draft** (built 2026-06-16) — not deployed |
| Changelog | `01_Source/changelog.html` | todo |
| Privacy / Support | — | todo (mirror Aloft if needed) |

## Outstanding (blockers to go-live)

- [x] **DMG** — `01_Source/downloads/diskverdict.dmg` staged (5,210,719 B, gitignored). Validated
      2026-06-17: v1.0.0 / build 1000, bundle `com.xpycode.DiskVerdict`, **notarized** + valid
      Developer ID signature (GREGOR MÜLLER, FDMSRXXN73), `SUFeedURL` → this site's appcast.
      Minor: the `.app` isn't stapled (spctl still accepts it as Notarized Developer ID).
- [x] **Strato pointing** — `diskverdict.lucesumbrarum.com` registered + pointed at `/DISKVERDICT/`
      (subfolder created). Confirmed by `DRY_RUN=1 ./deploy.sh` mapping cleanly to `:/DISKVERDICT/`.
- [x] **Pricing confirmation** — **Free** (JSON-LD `offers` price 0). Consistent with the portal.
- [x] **appcast.xml** — present at `/appcast.xml`; **Ed25519 signature cryptographically VERIFIED**
      against the app's baked-in `SUPublicEDKey` (via OpenSSL 3 `pkeyutl -rawin`). length matches DMG.
- [x] **Favicons** — generated 2026-06-17 from `diskverdict-cream.svg` via QuickLook + ImageMagick:
      `favicon.ico` (16/32/48), `favicon-16.png`, `favicon-32.png`, `apple-touch-icon.png` (180) at
      the site root; wired into `index.html` (mirrors Aloft).
- [ ] **Dark-mode screenshots** — THE ONLY REMAINING GATE. The `-dark.webp` slots are still
      byte-identical copies of the light shots (placeholders). The app defaults to dark and the real
      benchmark data is saved (`~/Library/Application Support/DiskVerdict/results.json`), so this is a
      ~2-min capture. Capture three dark PNGs → run `./finish-dark-screenshots.sh` (recipe inside it).

## Screenshot mapping (light → webp, via `cwebp -q 80 -resize 1600 0`)

- **hero** ← `verdicts-light.png` (sidebar + 8 workflow verdicts, all graded — the money shot)
- **detail** ← `verdict-detail-light.png` (an expanded verdict with reasoning + deciding statistic)
- **measurements** ← `measurements-light.png` (raw numbers + sustained-write trace)

OG image: `img/og/diskverdict.jpg` (1200×630) from `verdicts-light.png` on a cream pad (`#F4F4F4`).

## Tech Stack

- Static HTML/CSS/JS (no build step) — same as Aloft/Penumbra/Conjoyn.
- PHP: `dl.php` (app-agnostic download counter via `?app=diskverdict`).
- Deploy: `./deploy.sh` → lftp mirror `01_Source/` → server `DISKVERDICT/`
  (shared `_deploy-common.sh`, `~/.netrc` + ROOT `.env`). Preview: `DRY_RUN=1 ./deploy.sh`.

## App Reference

- **Source:** `/Users/sim/ProgrammingProjects/1-macOS/DiskVerdict/`
- **Design handoff:** `1-macOS/DiskVerdict/02_Design/DESIGN_HANDOFF.md`
- **Bundle id:** `com.xpycode.DiskVerdict` · **Min macOS:** 14.0 (Sonoma)
- **Updates:** Sparkle — appcast at `https://diskverdict.lucesumbrarum.com/appcast.xml`
  (the appcast.xml itself is NOT in this draft yet).
