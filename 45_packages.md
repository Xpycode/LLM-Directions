<!--
TRIGGERS: package, SPM, reusable, extract, shared code, zPackages, ShortcutKit, MediaKit, "could be a package", "another app already does this", monorepo
PHASE: any (especially Spec + Implement)
LOAD: full
-->

# Shared Packages (zPackages) — Think Package-First

*Before hand-rolling a capability, check whether it already exists as a shared
package, exists in another app worth extracting, or should be a new package.*

---

## The reflex

When you're about to implement something in an app, ask in this order:

1. **Is it already a zPackages package?** → add the local-path dependency, don't rewrite.
2. **Does another app already do this well?** → extract it into a package, then both use it.
3. **Is it generically useful (≥2 apps would want it)?** → build it *as* a package from the start.
4. **Is there a mature OSS package?** → adopt it; don't maintain your own (see ADOPT list).

A solo dev's leverage is **write-once, reuse-everywhere**. Copy-paste across apps is debt.

## Canonical source of truth

**`/Users/sim/ProgrammingProjects/1-macOS/zPackages/docs/PACKAGE-CATALOG.md`** —
the living list of available packages, build candidates, adopt-existing verdicts,
the app×package adoption matrix, and per-app roles. Keep it updated when you extract
or adopt. The monorepo itself is at `…/1-macOS/zPackages` (consume via local path:
`.package(path: "../zPackages")`).

## Available now

| Package | What | 
|---|---|
| **ShortcutKit** | Recordable, persisted, customizable keyboard shortcuts, generic over an app action enum |

## Top build candidates (as of 2026-05-30 survey)

- **MediaKit** ⭐ — AV probe + thumbnailer + frame extraction + cache (6 apps reimplement it).
- **FolderAccessKit** — security-scoped bookmarks + folder picker (5 apps).
- **ImageIOKit** — multi-format encode/save, full-res PNG, thumbnail cache, perceptual hash (5 apps).
- **VisionOCRKit** — Vision OCR + bounding boxes + Vision↔SwiftUI coordinate flip (2 apps, verbatim dup).
- **ProcessKit** — thin wrapper over `swift-subprocess` + bundled-tool resolution + progress parsing (6 apps).
- Smaller: **GlobalEventMonitors**, **SystemMetricsKit**, **MacUIKit** grab-bag.

## Adopt existing — do NOT build

| Need | Adopt |
|---|---|
| Subprocess core | swiftlang/swift-subprocess (Swift 6.2) |
| Launch-at-login | sindresorhus/LaunchAtLogin-Modern |
| SMPTE timecode | orchetect/TimecodeKit (+TimecodeKitAV) |
| Settings/UserDefaults | sindresorhus/Defaults |
| Self-update | Sparkle |

## Extraction playbook (the ShortcutKit pattern)

1. Find the seam: separate the **generic engine** from **app-specific bits**.
2. Make the engine generic over an app-supplied **protocol or closures** (e.g. an
   action `enum`, an `onAction` handler, a `shouldConsume` predicate) — never bake in
   app types, singletons, or NotificationCenter names.
3. Inject side-effects (logging, bundle ID) rather than importing the app's `Logger.shared`.
4. Build + test the package standalone, then **wire the source app first** as the proof.
5. Update `PACKAGE-CATALOG.md` and the app's `docs/PACKAGE-NOTES.md`.

## Fixing a bug you find in a package (while using it in an app)

Decide by **blocking × size**, then obey one hard rule.

| Situation | Do |
|---|---|
| **Blocking + small/well-understood** | Fix it now — but on a **zPackages branch**, as the package's **own commit, with a regression test**. Then continue the app. Local-path dep means the app picks it up instantly. |
| **Non-blocking, or large/needs design** | **Log it in `zPackages/docs/ISSUES.md`** (not the app's blockers), work around it, and fix in a **focused package session** with a clean context. |

**Hard rule (always):** a package fix **never rides in an app commit.** Separate repo, separate branch, separate commit, its own tests. History stays honest and other consumers inherit the fix cleanly.

**Matrix-check rule:** before changing anything **public** in a package, open the adoption matrix in `PACKAGE-CATALOG.md` and check every consumer — the app in front of you is not the only one. A fix fans out to all adopters, so it must read as a standalone package improvement, not "needed for App X." Verify you didn't break VAM while fixing Penumbra.

Mechanics: add a test reproducing the bug → `swift test` in zPackages → confirm the app's repro is gone (instant via local path) → commit to the package → then continue/commit the app. Log package bugs in **zPackages**, never in an app's `/blockers` (other adopters would never see them).

## Per-app signal

Each app's `docs/PACKAGE-NOTES.md` records what that app can **adopt** and what it's
a **source** for. It's surfaced at session start alongside `PROJECT_STATE.md` — so when
you open an app, proactively flag: *"this could be a package"* or *"we could extract this
from app X"* or *"adopt package Y here."*
