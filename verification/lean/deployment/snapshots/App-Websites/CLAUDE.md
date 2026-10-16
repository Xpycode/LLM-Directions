# App-Websites — Monorepo of App Marketing & Download Sites

This ROOT folder holds **all of Sim's app websites** under `APPS/` (sibling subfolders), with
the shared monorepo Directions in `docs/`. It mirrors the intended layout on Strato shared hosting
(one webspace, many document roots).

## The sites

| Folder | Domain | Type | Backend |
|--------|--------|------|---------|
| `APPS/apps.lucesumbrarum.com/` | apps.lucesumbrarum.com | Multi-app **download portal** (13 apps: CropBatch, LaunchAway, Manifest, NetworkQuality, P2toMXF, ProjectProgressTracker, QuickMotion, Sigil, SyncthingStatus, Tachograph, VideoContainerSwitcher, VideoScreensaver, VideoWallpaper) | PHP: `dl.php` download counter, `feedback-submit.php`, admin UI |
| `APPS/Penumbra/` | penumbra.lucesumbrarum.com | Single-app marketing site (paid via Creem; **not yet released**) | — (git remote: github.com/Xpycode/Penumbra-Website) |
| `APPS/Aloft/` | aloft.lucesumbrarum.com | Single-app marketing site (paid via Creem; **not yet released**) | — |
| `APPS/Conjoyn/` | conjoyn.lucesumbrarum.com | Single-app marketing site — **live** (free) | — |
| `APPS/DiskVerdict/` | diskverdict.lucesumbrarum.com | Single-app marketing site — **live** (free) | — |
| `APPS/TimeCodeEditor/` | timecodeeditor.lucesumbrarum.com | Single-app marketing site — **scaffold**, not deployed | — |
| `APPS/Magpie/` | magpie.lucesumbrarum.com | Single-app marketing site — **LIVE (v1.1.1, deployed 2026-07-12; v1.2.0 staged 2026-08-25, deploy pending)**; free/**open-source (MIT; bundles GPL-3.0 FFmpeg)** yt-dlp video downloader | — (git remote: github.com/Xpycode/Magpie) |

> **Not in scope:** `lucesumbrarum.com` itself is Sim's **photo/video website** — unrelated to apps.
> The apps portal merely lives on a *subdomain* (`apps.`) of that domain. The photo site stays
> separate and is **not** part of this monorepo.

## How this maps to Strato

One SFTP user scoped to this parent → each domain/subdomain points at its own site's document
root under `APPS/`. **Rule: no domain ever points at this parent or at `APPS/`, and no
document root is nested inside another** (the sites are siblings under `APPS/`). See
`docs/PLAN-multisite-strato.md` for the full hosting + deploy + SFTP plan.

## Conventions

- Each site deploys via its own `deploy.sh` (lftp mirror to Strato). Deploy creds are git-ignored
  and being migrated out of the scripts (see plan → Security).
- `.fastembed_cache/`, `node_modules/`, `_legacy/`, `_backup_originals/`, DMGs → never in git.
- Directions docs for the *whole monorepo* live in `docs/`. Individual sites may keep their own
  `docs/` for app-specific history.

## Start here

- `docs/STYLE-BIBLE.md` — **normative design-system rules** (page classes → variants, tokens,
  shared-file invariants; verify with `./check-invariants.sh`; tune variants in
  `demos/style-bible-lab.html`)
- `docs/PLAN-multisite-strato.md` — the organizational plan (the thing to execute)
- `docs/PROJECT_STATE.md` — current phase / focus / blockers
- `docs/OPERATIONS.md` — **per-site status of record + operational watch-outs** (read before
  deploying, before adding an app to `apps.json`, or when touching shared files)
- `docs/00_base.md` — Directions system
- `docs/29_web-strato-hosting.md` — Strato hosting reference
