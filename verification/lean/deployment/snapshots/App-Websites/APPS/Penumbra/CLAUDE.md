# Penumbra-Website

Marketing / landing + download site for **Penumbra** — a professional **macOS
video-culling / clip-curation tool**.

App project lives at: `/Users/sim/ProgrammingProjects/1-macOS/Penumbra`

## What Penumbra is

Editors import footage, preview it with fast keyboard-driven playback
(Metal-accelerated), mark the best parts with IN/OUT points, flag clips
Favorite/Reject, apply tags, and queue selections for **batch export** with
naming presets and quality templates (FFmpeg). Session state autosaves with
crash recovery. Native SwiftUI + Metal.

- **Tagline:** "Professional macOS video curation — review, mark, and export the keepers."
- **Audience:** professional video editors, colorists, documentary/content creators, VFX dailies review.
- **Privacy story:** standard macOS sandbox, user-selected file access only (security-scoped bookmarks), **no data collection, no special permissions**.

## App facts (for site copy — verify at ship)

| Field | Value |
|-------|-------|
| Version | 0.1.0 (010.beta) → bumping to 1.0 |
| Bundle ID | `LucesUmbrarum.Penumbra` |
| Min macOS | 26.0 |
| Category | Video |
| Auto-update | Sparkle 2, appcast at `penumbra.lucesumbrarum.com` |

## Brand tokens (from app `ThemeManager.swift`)

- Accent (orange): `#E68033`
- Primary bg: `#1A1A1A` · Secondary bg: `#262626`
- Text: `#FFFFFF` · Secondary text: `#A6A6A6`
- Dark-mode-first, minimalist, warm accent.

## Brand assets (source paths in the app project)

| Asset | Path |
|-------|------|
| Current app icon PNG (1024) | `…/Penumbra/01_Project/Penumbra/Penumbra/Assets.xcassets/AppIcon.appiconset/icon_1024.png` |
| Full app mockup | `…/Penumbra/02_Design/PenumbraUI-mockup/Penumbra-UI-APP.png` |
| Player / Timeline / Queue shots | `…/Penumbra/02_Design/PenumbraUI-mockup/Penumbra-UI-{2-Player,3-Timeline,7-Queue}.png` |

(Full `…` = `/Users/sim/ProgrammingProjects/1-macOS/Penumbra`)

Use the active app asset catalog for icon updates. The older `02_Design` icon exports
and website `penumbra-icon.svg` are legacy artwork. The website and local study use
`02_Frontend/assets/img/penumbra-icon-1024.png`, copied directly from the app catalog.

## Tech stack (confirmed 2026-06-10)

- **Frontend:** static HTML + CSS + vanilla JS (no framework)
- **Backend (thin):** PHP + flat-file JSON — download counter + feedback/bug form
- **Hosting:** Strato (`docs/29_web-strato-hosting.md`)
- **Deploy:** plain file upload, no build step

## Page sections (single-page landing)

hero · features · screenshots (lightbox) · download · FAQ / feedback

## Relevant cookbook patterns

| Need | Cookbook entry |
|------|----------------|
| Hero with floating app-icon constellation | `41-web-hero-floating-icons.md` |
| Screenshot gallery / click-to-zoom lightbox | `42-web-native-dialog-lightbox.md` |
| Per-app download counter (PHP + flat JSON) | `46-web-php-download-counter.md` |
| Feedback / bug-report form + admin UI | `49-web-php-feedback-form-with-admin.md` |
| Design tokens / fluid type | `39-design-tokens.md` |

## Folder structure

- `01_Source/` — source assets, copy, content originals
- `02_Frontend/` — HTML/CSS/JS (the deployable site)
- `03_Scripts/` — build/deploy/utility scripts
- `04_Data/` — server-managed flat-file data (gitignored)
- `docs/` — Directions docs + session logs + decisions

## Directions

Start at **`docs/00_base.md`**. State: **`docs/PROJECT_STATE.md`**. Decisions: **`docs/decisions.md`**.

## Website Help preview

- The app’s `Help/help-manifest.json` and Markdown are the source for all 14 website Help topics.
- Run `npm --prefix APPS/Penumbra ci`, then `npm --prefix APPS/Penumbra run build:help` from the monorepo root.
- Override the app Help location with `PENUMBRA_HELP_DIR` when needed.
- Edit `scripts/help-template.html` for the page shell; do not hand-edit generated `demos/penumbra-help.html`.
- `scripts/help-captures.json` maps shared capture IDs to Help topics and feature pages. Place approved WebP captures in `demos/penumbra-captures/` using the listed filenames, then rebuild Help; absent captures render labelled placeholders. Feature-page references in that map identify where to reuse the same files during the production port.
- The web preview preserves bundled Help wording and adds availability notes for disabled tagging and pending verification acceptance. Resolve discrepancies in the app Help source before release.
