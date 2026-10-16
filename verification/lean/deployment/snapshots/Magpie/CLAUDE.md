# Magpie — Project Context for Claude

> **Read this at the start of every session.** It's the entry point. For deeper structure, see `docs/00_base.md`.

## What this project is

A free, simple, **Apple Silicon-only** macOS app that downloads YouTube and other videos by wrapping `yt-dlp`. Aims to be a maintained alternative to ClipGrab (abandoned for modern Macs), without the price tag of PullTube/Downie.

**Non-goals:** Mac App Store distribution (YouTube ToS makes this category effectively unshippable on MAS), Intel support, mobile platforms, browser extensions (the browser→app handoff is a `magpie://` URL scheme + bookmarklet instead — see `docs/decisions.md`, 2026-06-17).

## Stack & architecture

| Area | Choice |
|------|--------|
| Language | Swift 6 (strict concurrency) |
| UI | SwiftUI (window app) + AppKit bridges where needed (drag-drop on Dock icon) |
| Min macOS | macOS 15 Sequoia (or 14 Sonoma — to confirm in spec) |
| Architecture | arm64 only |
| Project | Xcode project at `01_Project/Magpie.xcodeproj` |
| Engine | Bundled `yt-dlp` (Python-free single-binary build) + `ffmpeg`, executed via `Process` |
| Self-update | Sparkle 2 with EdDSA, appcast hosted on GitHub Pages or Releases |
| yt-dlp update | Check on launch + manual button; download to `~/Library/Application Support/Magpie/bin/` |
| Distribution | Developer ID-signed + notarized DMG via GitHub Releases |
| App sandbox | **Off** (yt-dlp + ffmpeg need exec + arbitrary network + filesystem; sandbox would also block the binaries we ship) |

## Locked-in decisions (see `docs/decisions.md` for rationale)

1. **UI surface:** Window + Dock drop target. No menu-bar mode.
2. **yt-dlp delivery:** Bundled inside `.app`, auto-updates on launch to `Application Support`. Bundled copy is the offline fallback.
3. **App self-update:** Sparkle 2 with EdDSA signing.
4. **Distribution:** Developer ID + notarization, DMG via GitHub Releases. **Not MAS.**

## Folder structure

```
Magpie/
├── 01_Project/                      ← All Xcode stuff
│   └── Magpie/
│       ├── Magpie.xcodeproj/          ← (generated next session)
│       ├── Magpie/                    ← App target source
│       │   ├── Views/               ← SwiftUI views
│       │   ├── Models/              ← @Observable models, value types
│       │   ├── Services/            ← yt-dlp wrapper, downloader, updater
│       │   └── Resources/           ← yt-dlp + ffmpeg drop here at build
│       │                              (binaries are gitignored)
│       ├── MagpieTests/               ← Unit tests
│       └── MagpieUITests/             ← UI tests
├── 02_Design/                       ← Affinity sources, icon exports
│   └── Exports/
│       └── AppIcon.appiconset/
├── 03_Screenshots/                  ← Marketing / README shots
├── 04_Exports/                      ← DMGs (gitignored)
├── scripts/                         ← Build-time helpers
│                                       (fetch-ffmpeg.sh, fetch-ytdlp.sh,
│                                        build-dmg.sh, notarize.sh)
├── specs/                           ← Feature specs with acceptance criteria
│   └── 01-core-download.md
├── docs/                            ← Directions reference docs + project state
│   ├── 00_base.md                   ← Directions entry point
│   ├── PROJECT_STATE.md             ← Current funnel position
│   ├── decisions.md                 ← Architecture choices log
│   └── sessions/                    ← Per-day session logs
└── CLAUDE.md                        ← This file
```

**Pattern alignment:** Inner `01_Project/Magpie/Magpie/` matches Xcode's default new-project layout (used in Penumbra and ViME) — `Resources/` lives inside the source folder, which is what Xcode bundles into the `.app`'s `Contents/Resources/` automatically.

## Working agreements

- **Branching:** Never commit to `main` directly. Branch names: `feature/`, `fix/`, `experiment/`. Remind me before coding.
- **Backpressure (must pass before commit):** `xcodebuild build` clean, no SwiftLint errors, tests green.
- **Build hygiene:** Always kill running app, clean DerivedData, then build (per global CLAUDE.md "Xcode Build Behavior").
- **Decisions logged:** Append to `docs/decisions.md` whenever an architectural choice is made.
- **Session logs:** Update `docs/sessions/YYYY-MM-DD.md` after meaningful progress.
- **Apple credentials:** Team ID, signing identity, etc. live in `~/.claude/apple-developer.md` — never ask me for them.

## Key references inside `docs/`

| Trigger | Doc |
|---------|-----|
| Sandbox, bookmark, notarization | `22_macos-platform.md` |
| SwiftUI view-not-updating, state | `20_swiftui-gotchas.md` |
| Git workflow, branching | `32_git-workflow.md` |
| Production / ship checklist | `30_production-checklist.md` |
| Security, secrets, signing keys | `54_security-rules.md` |
| Stuck / debugging | `25_troubleshooting.md` |

## Triggers for global skills

- SwiftUI work → `swiftui-expert-skill`
- Concurrency / async / Swift 6 → `swift-concurrency`
- SwiftUI visual check → `/preview Path/To/MyView.swift`
