# Magpie Website — CLAUDE.md

## Project

Dedicated marketing/product website for **Magpie**, a free, native, **open-source** macOS app for
downloading video. It's a friendly Mac front-end for the maintained **`yt-dlp`** engine that runs
entirely on the user's Mac, with subtitles, thumbnail saving, SponsorBlock and chapter split — the
modern, maintained alternative to the abandoned ClipGrab.
- **URL:** magpie.lucesumbrarum.com (subdomain — pointed at `/MAGPIE/`)
- **Brand:** Luces Umbrarum
- **App tagline:** "Download video on your Mac. Free, native, done."
- **App one-liner:** Paste a link, pick a quality, get the file — a free, open-source `yt-dlp`
  front-end that runs locally, with subtitles / thumbnail / SponsorBlock / chapter split.
- **Licence:** **MIT** for Magpie's own source (changed 2026-07-04 from GPL-3.0-or-later — see the
  app repo's `docs/decisions.md`). Magpie bundles `ffmpeg` (GPL-3.0-or-later, `--enable-gpl`) and
  `yt-dlp` (Unlicense) as separate subprocess-only executables, not linked, so their licences don't
  propagate to Magpie's own code. This is the ONLY open-source app in the monorepo; the site
  features that honestly.

## Style Reference

**Inherits the shared design system** (`css/site.css`, the Luces Umbrarum standard — byte-identical
across Aloft/DiskVerdict/Conjoyn/TimeCodeEditor). Do **not** diverge `site.css`; put all per-site
changes in `css/magpie.css`.

Per-site theming (the one thing that differs between sites):
- Fonts: `Instrument Serif` (display) + `Inter` (body) via Google Fonts — shared.
- **Accent: teal** `--accent: #1F9BA6` (light) / `#33BBC6` (dark) — the app's `Theme.accent`, the
  iridescent magpie-tail teal. Lives at the top of `css/magpie.css`. To recolor the whole site,
  change `--accent` / `--accent-soft` and their dark-mode twins — nothing else.
  > NB: teal is deep enough that the nav-CTA pill uses **white** text (≈3.3:1 — better than the
  > orange sibling sites), so there's no dark-ink override like TimeCodeEditor's lighter gold needed.
  > The app icon keeps its **orange beak** as a spark, but the site leads with the teal.
- Icon: **REAL** — `img/icons/magpie-icon.png` + the favicon set are generated from the app's actual
  AppIcon (`Assets.xcassets/AppIcon.appiconset/icon_512x512@2x.png`, 1024px). The icon is a squircle,
  so one PNG serves both light and dark (no `<picture>` scheme swap). Regenerate via the recipe in
  the "Real icon" note below if the app icon changes.

## Site Structure

| Page | Path | Status |
|------|------|--------|
| Landing | `01_Source/index.html` | **LIVE** — v1.1.1 deployed 2026-07-12; real screenshots wired in same day |
| Imprint | `01_Source/imprint.html` | done (§5 TMG + a GPL "Software licence" section) |

There's also a Magpie-only **`.oss-strip`** (open-source row) under the fact band in `index.html`,
styled in `magpie.css` — states the GPL licence and links the source.

## Outstanding (blockers to go-live)

- [ ] **DMG** — none yet (`04_Exports` empty app-side; the app is in ship phase). Stage the notarized
      release at `01_Source/downloads/magpie.dmg` (gitignored; deploy mirrors the working tree).
      Bundle id `com.lucesumbrarum.Magpie`, team `FDMSRXXN73`. The M4-Pro is the ship Mac (has the
      Developer ID Application cert + `~/.netrc`); a `notarytool` credential + `build-dmg.sh` are
      the app-side to-dos.
- [ ] **appcast.xml** — an **empty, valid** appcast is present (`<channel>` with **no `<item>`** →
      Sparkle reports "up to date", so the feed can go live before the first DMG). NB: this file
      arrived from **outside the 2026-06-25 build session** (another Mac / Syncthing — it was never in
      git history); kept as-is because it's correct (title=Magpie, 0 items, enclosures resolve to this
      doc root). Add the **first release `<item>`** app-side once the DMG exists, so `edSignature` +
      `length` are real and match the DMG; verify vs the baked-in `SUPublicEDKey` (OpenSSL 3
      `pkeyutl -rawin` — LibreSSL can't do Ed25519). Magpie ALREADY has its own dedicated Sparkle EdDSA
      key (public key in `Info.plist`; private at the app repo's `99-AUTH/magpie-sparkle-private.key`)
      — **do NOT generate a new one**. **App-side companion:** set the app's `SUFeedURL` to
      `https://magpie.lucesumbrarum.com/appcast.xml` (currently blank → updater inert) and flip
      `SUEnableAutomaticChecks`. *This site is on the app's ship critical path — it hosts the feed.*
- [x] **Real screenshots — DONE 2026-07-12.** The teal placeholders are replaced by three real
      captures: `magpie-hero.webp` (a video loaded — Dark-2-Loaded), `magpie-detail.webp` (a download
      in progress — Dark-11-Downloading), `magpie-queue.webp` (History + "+8 chapters" badge —
      Dark-9-History). **Decision (Sim):** only the DARK set has real content states (the light
      captures are all empty-window), so we ship the dark shots and serve them in BOTH modes — the
      dark window floats on the light page (Conjoyn/DiskVerdict look). Each slot is now a single
      `<img>` (no `<picture>`); `magpie.css` `.frame--shot` / `.shot` overrides strip the card chrome
      so the window's baked shadow floats and isn't clipped. `img/og/magpie.jpg` refreshed from the
      loaded hero (real window on the cream bg). Verified locally in Safari, light + simulated dark.
      Captures are 1× (~1012 px) so slightly soft on Retina — recapture at 2× to sharpen later.
      Regenerate via `./make-screenshots.sh` (now maps the three dark PNGs, native size, no upscale).
- [ ] **Repo public (voluntary, no longer a GPL obligation)** — `github.com/Xpycode/Magpie` is
      currently **private**; `LICENSE` (MIT) now exists in the app repo as of 2026-07-04. Since the
      relicense to MIT (see app repo `docs/decisions.md`, 2026-07-04), publishing the repo is a choice,
      not a GPL requirement — only the bundled `ffmpeg` binary is still GPL, and its own
      source-availability obligation is satisfied by pointing to unmodified upstream FFmpeg source
      (see imprint.html), no app-repo disclosure needed. Decision (Sim, 2026-06-25, reaffirmed
      2026-07-04): still **make the repo public + feature it** (the site's hero/footer/imprint already
      link it) — it's just a marketing/openness choice now. **Before flipping:** audit the full git
      history for secrets (the app repo references a `99-AUTH/` key dir — make sure no private key /
      token / netrc was ever committed).
- [x] **Strato pointing** — `magpie.lucesumbrarum.com` subdomain pointed at `/MAGPIE/`, verified live
      (2026-07-04). The 2026-06-25 entry was wrong: the panel bound the subdomain to an empty
      `/Magpie/` (mixed-case) folder auto-created when the subdomain was first set up, while
      `deploy.sh` uploads to `/MAGPIE/` (all-caps, per `deploy_mirror ... "MAGPIE"`) — case-sensitive
      Linux paths, two distinct dirs. Site 404'd end-to-end (index + appcast) until repointed; the
      stray `/Magpie/` folder has since been deleted. Re-verify with
      `curl -I https://magpie.lucesumbrarum.com/appcast.xml` after any future subdomain change.
- [x] **Pricing** — **Free** (JSON-LD `offers` price 0, `isAccessibleForFree`).
- [x] **Icon + favicons** — real, generated from the app's AppIcon.
- [x] **OG image** — `img/og/magpie.jpg` (1200×630). Placeholder card; refresh from the real hero
      screenshot when captured.

## Tech Stack

- Static HTML/CSS/JS (no build step) — same as Aloft/Penumbra/Conjoyn/DiskVerdict/TimeCodeEditor.
- PHP: `dl.php` (app-agnostic download counter via `?app=magpie`).
- Deploy: `./deploy.sh` → lftp mirror `01_Source/` → server `MAGPIE/`
  (shared `_deploy-common.sh`, `~/.netrc` + ROOT `.env`). Preview: `DRY_RUN=1 ./deploy.sh`.
- Reminder: `deploy_mirror` has **no `--delete`** — renamed/removed files linger on the server.

## App Reference

- **Source:** `/Users/sim/ProgrammingProjects/1-macOS/Magpie/` (separate repo, `Xpycode/Magpie`).
- **Bundle id:** `com.lucesumbrarum.Magpie` · **Min macOS:** 14.0 (Sonoma) · **Apple Silicon only**
  (`ARCHS: arm64`, `EXCLUDED_ARCHS: x86_64`) — NOT Universal.
- **Engine:** wraps **`yt-dlp`** (Unlicense) + a static **GPL** build of **FFmpeg** → app is GPL-3.0.
- **Updates:** Sparkle — appcast at `https://magpie.lucesumbrarum.com/appcast.xml`.
- **Feedback slug:** `magpie` (already live in the portal `apps.json`; off-portal `portalPage:false`).
- **Shipped features featured on the site:** quality picker (to 4K+/MP3, custom format), subtitles,
  thumbnail save, SponsorBlock, chapter split, app + engine self-update. **NOT featured** (unmerged
  at build time): the browser→app handoff (bookmarklet + clipboard watcher) — add once it lands.
