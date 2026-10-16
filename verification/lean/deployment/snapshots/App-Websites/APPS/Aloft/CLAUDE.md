# Aloft Website — CLAUDE.md

## Project

Dedicated marketing/product website for **Aloft** (formerly ClipSmart), a macOS clipboard manager.
- **URL:** aloft.lucesumbrarum.com — **LIVE** (freemium: free tier + **15 € Pro**)
- **Brand:** Luces Umbrarum / Xpycode
- **App tagline:** "Your clipboard, always overhead."
- **App one-liner:** A clipboard manager that comes to your cursor instead of your menu bar.
- **Version:** 1.2.1 / build 1210 (shipped 2026-07-27 by the app project) · **Min macOS:** 15.0 (Sequoia)
- **Portal:** listed as **LU-019** (first freemium entry → `FREE + PRO` badge, driven by `price.pro`).

## Style Reference — the instrument-datasheet design system

Aloft is a **PAID-variant datasheet site** (blush paper). It inherits the shared system; the
normative rules live in the monorepo, do **not** re-derive them here:
- **`docs/STYLE-BIBLE.md`** (repo root `docs/`) — page anatomy, the PAID dual-CTA rule (§2.5), tokens.
- **`docs/OPERATIONS.md`** — Aloft's status of record + the site-specific watch-outs below in one place.
- Verify with **`./check-invariants.sh`** at the repo root before shipping.

Shared, byte-identical across the dedicated sites (do **not** diverge — put per-site changes in
`css/aloft.css`): `css/site.css`, `css/datasheet.css`, `js/lightbox.js`.

Per-site theming (`css/aloft.css`):
- **Fonts: self-hosted** `Instrument Serif` (display) + `Inter` (body) + `JetBrains Mono` (`--mono`),
  all `@font-face` in **`datasheet.css`** with woff2 in `01_Source/fonts/`. **Zero `googleapis`**
  (GDPR / German imprint). *(Was Google Fonts pre-datasheet-port; the CDN link is gone.)*
- **Accent: Apple blue** `--accent: #0a84ff` — set on `.sheet` (see the accent-resolution watch-out
  below). *(Was the inherited terracotta `#D9846A`.)*
- **PAID dual CTA** (§2.5): green download `.rule .dl` (`#4F7A28` = "the download is free") **plus**
  a blue `.rule .buy` BUY PRO button. The nav carries **no** CTA (§2.2 — removed 2026-07-19).

## Site Structure (all **LIVE**)

| Page | Path | Notes |
|------|------|-------|
| Landing | `01_Source/index.html` | dochead + PAID dual CTA + numbered datasheet sections + pricing tiers |
| Changelog | `01_Source/changelog.html` | 1.2.1 / 1.2.0 / 1.1.0 / 1.0.2 history (v1.0 cap claims kept, marked superseded) |
| Privacy | `01_Source/privacy.html` | Germany jurisdiction; Creem MoR disclosure is prose, not a button |
| Terms | `01_Source/terms.html` | Creem merchant-of-record terms |
| Support | `01_Source/support.html` | hand-authored support/contact page |
| Help | `01_Source/help/index.html` | **generated** by `scripts/build-help.js` — see the watch-out |
| Imprint | `01_Source/imprint.html` | §5 TMG imprint |

## Purchase (Creem — merchant of record)

- **Two** BUY buttons only, both `index.html`, both → the same Creem product
  `prod_69nYTj19mdXcJWl5RxuMn4`: `.rule .buy` (spec strip) and `.btn-buy` (Pro pricing tier).
  Kept deliberately — the tier button is the Pro column's action, mirroring Free's download; §2.2's
  "one path" rule targets nav CTAs, not the pricing table.
- **Still pending for full release:** confirm the Creem product is finalized; build + deploy the
  in-app **`/api/license` Strato proxy** (see `1-macOS/ClipSmart/05_Proxy/`).

## Site-specific watch-outs (full list → `docs/OPERATIONS.md`)

- **The deploy must NOT publish the DMG.** `deploy.sh` passes `--exclude-glob '*.dmg'` because the
  app's release runbook uploads the notarized artifact directly. The local `downloads/aloft.dmg` is a
  stale working copy; without the exclusion `mirror -R` lets it win and reverts the live download to
  an updater-less build (this stranded downloaders 2026-07-03 → 07-15). **Never** promote the
  exclusion to `_deploy-common.sh` — every other site relies on the mirror to publish its DMG.
- **All pages share the current header and PAID sheet.** Load `site.css`, then `datasheet.css`,
  then `aloft.css` on every page, including generated Help. The app icon, full responsive navigation,
  blush paper and readable interior-page typography live in `aloft.css`; do not restore Help's
  legacy `tint-dusk`/serif hero or the old monogram header. Blue is scoped to `.sheet` and the header.
- **The help page (`help/index.html`) is generated** by `scripts/build-help.js` — edit the generator,
  not the output. It once shipped in fallback fonts because the CDN link was stripped without adding
  `datasheet.css` (which carries the `@font-face`); `check-invariants.sh` tests only for the absent
  CDN link, so it passed. Confirm the woff2s are actually **requested**, don't trust the green check.
- **Real screenshots still TODO** — no `public/img/screenshots/aloft-hero.webp` on the portal yet, so
  Aloft's featured card renders icon+text while its neighbours lead with an app window. Dropping the
  webp in fills it with no code change (Sim is supplying them).
- **Stylesheet cache versions** — `deploy.sh` stamps `css/site.css`, `css/datasheet.css` and
  `css/aloft.css` at deploy (mirrors the portal); the Help generator also emits their current
  content hashes on local rebuilds. Preview: `DRY_RUN=1 ./deploy.sh`.

## Tech Stack

- Static HTML/CSS/JS, no build step (except `scripts/build-help.js` for the help page).
- PHP: `dl.php` (download counter, `?app=aloft`), `feedback-submit.php` (support form).
- Deploy: `./deploy.sh` → lftp mirror `01_Source/` → server `ALOFT/` (shared `_deploy-common.sh`,
  `~/.netrc` + ROOT `.env`, `--exclude-glob '*.dmg'`). Preview: `DRY_RUN=1 ./deploy.sh`.

## App Reference

- **Source:** `/Users/sim/ProgrammingProjects/1-macOS/ClipSmart/` — **the source folder is still
  named `ClipSmart`** (the product renamed to Aloft; `1-macOS/Aloft/` only holds `demo-sites`).
- **Project state:** `1-macOS/ClipSmart/docs/PROJECT_STATE.md`
- **License proxy:** `1-macOS/ClipSmart/05_Proxy/`
- **Min macOS:** 15.0 (Sequoia) · **Updates:** Sparkle appcast on the app side.
- **Known app-side leftover:** `Views/ProGate.swift` still shows the old "ClipSmart Pro" name in the
  activation-limit message (tracked in the repo-root `docs/TASKS.md`).

## Directions

Monorepo Directions at the repo root `docs/` (`docs/00_base.md`). This site is one of six under `APPS/`.
