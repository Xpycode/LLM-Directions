# TimeCodeEditor Website — CLAUDE.md

## Project

Dedicated marketing/product website for **TimeCodeEditor**, a native macOS app that finds video
files whose **embedded SMPTE timecode** disagrees with **when the file was actually recorded**, then
rewrites the correct timecode in via a **lossless ffmpeg stream copy** — in batch, non-destructively,
and verified.
- **URL:** timecodeeditor.lucesumbrarum.com (subdomain — pointed at `/TIMECODEEDITOR/`)
- **Brand:** Luces Umbrarum
- **App tagline:** "Make the timecode match reality."
- **App one-liner:** Flags where a file's embedded timecode and its creation time disagree, then
  rewrites the right timecode in — losslessly, in batch, with a ✓/⚠/✗ verification on every job.

## Style Reference

**Inherits the shared design system** (`css/site.css`, the Luces Umbrarum standard — byte-identical
across Aloft/DiskVerdict/Conjoyn). Do **not** diverge `site.css`; put all per-site changes in
`css/timecodeeditor.css`.

**Design system: the instrument datasheet, variant FLAGSHIP** (ported 2026-07-15 — see
`docs/STYLE-BIBLE.md`, the normative contract). Three CSS layers, and the link order matters:
`site.css` (chrome) → `timecodeeditor.css` (per-site values) → `datasheet.css` (LAST — it pins the
light tokens globally). `datasheet.css` + `js/lightbox.js` are **byte-identical** across every
dedicated site — never hand-edit a copy; edit once and re-copy, then `./check-invariants.sh`.

Per-site theming (the one thing that differs between sites):
- Fonts: **self-hosted** in `fonts/` — no Google Fonts anywhere (GDPR; this site carries a German
  imprint). Note the wiring: `site.css` only *names* `Instrument Serif` / `Inter`, while
  **`datasheet.css` is the file that `@font-face`-hosts them**. That's why this site needed the
  datasheet port to stop calling Google — the two were one act, not two.
- **Accent: gold** `--accent: #FFB23E` — the app's `Theme.acc1` ("highlight" accent). Set twice in
  `css/timecodeeditor.css`: on `:root` (chrome) and re-asserted on `.sheet` — the latter is required
  because `datasheet.css` loads *after* and its `:root{--accent:#D9846A}` terracotta would otherwise
  win by source order. Custom props inherit from the nearest ancestor, so `.sheet` beats it without
  `!important` or reordering links.
  > NB: chosen over the app's `acc2` orange `#F0622A` on purpose — that hue is identical to the
  > Conjoyn site, which would make the two look like twins. Gold is distinct and still from the
  > app's own palette. **Because gold is light, accent-on-accent text uses dark ink, not white:**
  > `datasheet.css` hardcodes `.rule .dl { color:#fff }`, which measures **1.80:1** on this gold —
  > so `.sheet .rule .dl { color:#241F18 }` (**9.10:1**) overrides it. The old `.nav-cta` that
  > carried this same call is gone: under the datasheet anatomy the rule strip is the sole download
  > path (STYLE-BIBLE §2.2), so the contrast problem moved to `.dl` with it.
- **No dark mode.** The `@media (prefers-color-scheme: dark)` block was removed at the port —
  datasheet pages are light-only and `check-invariants.sh` FAILs if one reappears. Do NOT re-add.
- Icon: `img/icons/timecodeeditor-{light,dark}.png` (real, from the app's `.icns` — 2026-07-18).
  **The dochead icon is PINNED to the dark variant** (2026-07-19) — a single `<img>`, no `<picture>`
  swap. Reason: the datasheet page is light-only, so swapping the icon on the *viewer's* OS scheme
  served no purpose and left a washed-out light icon on pale paper for light-mode visitors. Pinned
  dark to match the portal carousel and DiskVerdict. The `<link rel="icon">` also points at `-dark`.
  **Still light-derived:** the raster set (`favicon.ico`, `favicon-16/32.png`, `apple-touch-icon.png`)
  — regenerate from `-dark.png` if the browser-tab icon should match. Do **not** re-add a `<picture>`
  swap to the dochead.
  > The three *screenshot* `<picture>` swaps are a separate matter — see the screenshots gate below;
  > for TCE those pairs are currently byte-identical, unlike DiskVerdict's.

## Site Structure

| Page | Path | Status |
|------|------|--------|
| Landing | `01_Source/index.html` | **datasheet ✓** (ported 2026-07-15) — not deployed |
| Support | `01_Source/support.html` | **datasheet ✓** (created 2026-07-15 — STYLE-BIBLE §1: every dedicated site gets one) |
| Imprint | `01_Source/imprint.html` | **datasheet ✓** (`body.util`; §5 TMG, mirrors the other sites) |
| Changelog | — | todo (mirror Aloft if wanted) |
| Release notes | `01_Source/TimeCodeEditor-1.0.html` | live — Sparkle shows this in the update dialog |

> ⚠️ **`TimeCodeEditor-1.0.html` has DIVERGED from the app project's copy** (2026-07-19). The website
> copy gained a *"Light or dark — an Appearance menu sets the interface to Match System, Light, or
> Dark"* bullet, because build 1001 shipped that feature while the notes still read as a plain "first
> public release". The app project's `04_Exports/appcast/TimeCodeEditor-1.0.html` does **not** have
> it. **Do not blind-`cp` that file over this one on the next release** — it would silently drop the
> bullet. Either port the bullet upstream or re-apply it here.

## Verified specs (from the shipped 1.0 binary — do NOT restate these from memory)

Re-checked 2026-07-19 against the shipped **build 1001** `TimeCodeEditor-1.0.dmg` (every claim below
re-verified against the new binary, not carried over from build 1000); the datasheet's §04 table
quotes them:
`lipo` → **arm64 only** (Apple Silicon, *not* Universal) · `LSMinimumSystemVersion` **14.0** ·
`CFBundleShortVersionString` **1.0** (build **1001**) · `spctl` → **Notarized Developer ID**
(GREGOR MÜLLER, FDMSRXXN73) · bundled **FFmpeg 8.1** at `Contents/Resources/Helpers/ffmpeg`, whose
configure line carries **no `--enable-gpl`** → the **LGPL** claim is correct (Magpie's is GPL-3.0;
don't copy that across). **LICENSE cell = `© Luces Umbrarum`** — the repo is private with no LICENSE
file (`gh api repos/Xpycode/TimeCodeEditor/license` → 404), and a proprietary app never shows a fake
OSS licence. **MODEL = LU-018**, reserved for this site by the `apps.json` ledger.

## Outstanding (blockers to go-live)

- [x] **DMG** — **build 1001 shipped + LIVE 2026-07-19.** **26,355,878 B**, SHA-256
      `b35830d6a4657089d364f0f39e9e53d4f76d5d4d1d9640587049e1ad76d42988`, at BOTH paths byte-for-byte
      the same file: site-root `01_Source/TimeCodeEditor-1.0.dmg` (the appcast enclosure) **and**
      `01_Source/downloads/timecodeeditor.dmg` (what `dl.php` serves). *Both* must land on every
      future bump or Sparkle auto-update breaks — the same invariant Magpie carries. v1.0/build 1001,
      bundle `com.lucesumbrarum.timecodeeditor`, **notarized** Developer ID (GREGOR MÜLLER,
      FDMSRXXN73), arm64-only. Live-verified by hashing the *downloaded bytes* at both URLs.
      > **Build 1000 (23,613,356 B) is superseded** — it predated the Appearance menu and the icon
      > redesign. Old and new appcasts are **both exactly 993 bytes** and the DMGs share a filename,
      > so **never verify these by size or name — SHA-256 only.**
- [x] **appcast.xml** — 1.0 / **build 1001**, live 2026-07-19. **Ed25519 signature cryptographically
      VERIFIED 2026-07-19** against `SUPublicEDKey = 2QWiGTuXFDby+pnwQVuvDqgSPYoKGsRusg8N6kFHJ6c=`,
      itself re-read out of the **shipped 1001 binary's** `Info.plist` (so the chain closes: the key
      the app will actually use → verifies → the signature that ships → over the DMG bytes that ship).
      A one-byte-tampered copy correctly fails (negative control, so the check isn't vacuous).
      `length="26355878"` matches the DMG exactly. Recipe (LibreSSL can't do Ed25519 — use Homebrew
      OpenSSL 3): wrap the raw 32-byte key in the DER prefix `302a300506032b6570032100`, convert to
      PEM, then `openssl pkeyutl -verify -pubin -inkey pub.pem -rawin -in <dmg> -sigfile sig.bin`.
      Note `pkeyutl` takes **`-keyform`**, not `-inform` (that flag errors out).
- [x] **Datasheet port** — done 2026-07-15 (FLAGSHIP). `check-invariants.sh` FAIL-checks this site as
      a `DATASHEET_SITES` member and all 17 checks pass. See "Style Reference" above.
- [x] **Real screenshots — DONE 2026-07-18.** 3 of Sim's 7 real captures (Loaded/Verify/QueueCorrecting) fill all six slots via make-screenshots.sh (dark-only app: light==dark; no-upscale guard added); floating-window CSS override ported from magpie.css.
      > **Open follow-up (new as of build 1001):** the app is **no longer dark-only** — 1001 adds an
      > Appearance menu (Match System / Light / Dark). The three `<picture>` pairs in `index.html`
      > therefore still serve **byte-identical** files to both the light and dark `srcset` slots
      > (verified 2026-07-19 by SHA-256 — every visitor sees the dark UI). That was honest for a
      > dark-only app and is *not* currently wrong, but real **light-mode captures are possible for
      > the first time**. Either shoot them, or collapse each `<picture>` to a single `<img>`
      > (STYLE-BIBLE §2.7: a slot gets one `<img>` unless the app has REAL light/dark parity). Original gate text: The six
      `timecodeeditor-{hero,detail,queue}-{light,dark}.webp` are **branded placeholders**, literally
      captioned "placeholder — real screenshot pending", and they're on the **legacy cream** the
      FLAGSHIP re-theme superseded — so they visibly clash with the pale-blue sheet. Capture real
      ones: the Sources+Queue main window (hero), a source row with the embedded-vs-creation Δ
      (detail), and the queue running with verify seals (queue). Convert `cwebp -q 82` (the app is
      dark-by-default, so capture dark first; light needs LiteMode if the app has it, else reuse
      honestly). Per STYLE-BIBLE §2.7 real captures are **floating windows** (baked shadow on
      transparent margin) with **no CSS frame** — and a slot gets a single `<img>` unless the app has
      REAL light/dark parity; the current `<picture>` pairs assume a parity the placeholders only
      fake, so revisit that at capture time.
- [x] **Real icon — DONE 2026-07-18** (from the app's real `TimeCodeEditorIcon-{Light,Dark}.icns` → 256px PNGs referenced by the dochead `<picture>`; favicon set + apple-touch regenerated; placeholder SVGs deleted). Original gate text: — `timecodeeditor-{light,dark}.svg` + the favicon set are placeholders derived
      from them. Replace both SVGs with the real AppIcon export, then regenerate favicons
      (qlmanage 1024 → ImageMagick: `.ico` 16/32/48, `favicon-16/32.png`, `apple-touch-icon.png` 180).
- [x] **Strato pointing** — FIXED 2026-07-18: the doc-root actually pointed at the empty legacy `TimeCodeEditor` dir (case mismatch → Apache 404 despite a clean deploy); Sim repointed it to `TIMECODEEDITOR` in the Strato panel. The empty legacy dir still lingers (rmdir by hand).
- [x] **Pricing** — **Free** (JSON-LD `offers` price 0).
- [x] **OG image** — `img/og/timecodeeditor.jpg` (1200×630). Placeholder wordmark card; refresh from
      the real hero screenshot when captured.

## Tech Stack

- Static HTML/CSS/JS (no build step) — same as Aloft/Penumbra/Conjoyn/DiskVerdict.
- PHP: `dl.php` (app-agnostic download counter via `?app=timecodeeditor`).
- Deploy: `./deploy.sh` → lftp mirror `01_Source/` → server `TIMECODEEDITOR/`
  (shared `_deploy-common.sh`, `~/.netrc` + ROOT `.env`). Preview: `DRY_RUN=1 ./deploy.sh`.
- Reminder: `deploy_mirror` has **no `--delete`** — renamed/removed files linger on the server.

## App Reference

- **Source:** `/Users/sim/ProgrammingProjects/1-macOS/TimeCodeEditor/`
- **Spec:** `1-macOS/TimeCodeEditor/specs/timecode-corrector.md`
- **Bundle id:** `com.lucesumbrarum.timecodeeditor` · **Min macOS:** 14.0 (Sonoma) · **Apple Silicon
  only** (`ARCHS: arm64`) — NOT Universal.
- **Updates:** Sparkle — appcast at `https://timecodeeditor.lucesumbrarum.com/appcast.xml`.
- **Bundles:** a static **LGPL** build of FFmpeg (used for the stream-copy correction).
