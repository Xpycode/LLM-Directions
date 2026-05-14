<!--
TRIGGERS: code signing, signing certificate, "no signing certificate found", "Mac Development", DEVELOPMENT_TEAM, team ID, Debug.local.xcconfig, per-machine, second Mac, M-series, handoff, SourceKit, "Cannot find type", "No such module", false positive, indexer, stale index, mid-edit errors, xcodebuild vs Xcode, freshly regenerated xcodeproj, SPM modules not resolving
PHASE: implementation, bootstrap-on-new-machine
LOAD: when starting work on a new Mac, or when Xcode shows errors that xcodebuild doesn't
-->

# Xcode Signing & SourceKit Gotchas

*Two Xcode-environment patterns that have eaten time across at least 6 projects. Both fall under one rule: **`xcodebuild` is the source of truth — not what the editor shows you.***

---

## Pattern 1: Per-machine signing via `Debug.local.xcconfig`

### Symptom

On a fresh Mac (or a second/third dev machine), `xcodebuild` fails with:

```
error: No "Mac Development" signing certificate matching team ID "FDMSRXXN73" with a private key was found.
```

The original Mac builds fine; the new one doesn't. Manually editing the `.xcodeproj` to swap signing settings works once but bakes machine-specific data into a tracked file — and the next sync from the original Mac overwrites it.

### Why it happens

Apple's `DEVELOPMENT_TEAM` build setting works fine cross-machine (Team ID is the same everywhere), but `CODE_SIGN_IDENTITY` ultimately resolves to a **certificate SHA-1** in the local keychain. SHA-1s differ across machines because each Mac has its own copy of the development cert. The `.xcodeproj` can't carry both.

### The fix: split signing into a gitignored xcconfig

**1. In the project root**, create `Config/Debug.local.xcconfig` (or wherever your xcconfigs live):

```xcconfig
// Per-machine signing overrides. Gitignored. Each Mac has its own.
CODE_SIGN_STYLE = Manual
DEVELOPMENT_TEAM = FDMSRXXN73
CODE_SIGN_IDENTITY = Apple Development: Your Name (XXXXXXXXXX)
PROVISIONING_PROFILE_SPECIFIER =
```

(Find your identity string with `security find-identity -v -p codesigning` — copy the `"Apple Development: …"` part exactly, including the trailing team-member ID in parens.)

**2. In the project's main `Debug.xcconfig`** (tracked), include the local one with the optional-include syntax:

```xcconfig
// At the top, before any other settings
#include? "Debug.local.xcconfig"
```

The `?` after `#include` means **"include if it exists, silently skip if it doesn't"** — so the project still builds in CI / on a freshly cloned Mac that hasn't been bootstrapped yet (it'll fall back to whatever the `.xcodeproj` declares).

**3. In `.gitignore`:**

```
*.local.xcconfig
```

**4. Bootstrap script for a new Mac** (optional but worth it):

```bash
#!/usr/bin/env bash
# bootstrap-signing.sh — run once per Mac
set -euo pipefail

IDENTITY=$(security find-identity -v -p codesigning | grep "Apple Development" | head -1 | sed -E 's/.*"(.+)".*/\1/')
TEAM_ID="FDMSRXXN73"

cat > Config/Debug.local.xcconfig <<EOF
CODE_SIGN_STYLE = Manual
DEVELOPMENT_TEAM = ${TEAM_ID}
CODE_SIGN_IDENTITY = ${IDENTITY}
PROVISIONING_PROFILE_SPECIFIER =
EOF

echo "Wrote Config/Debug.local.xcconfig with identity: ${IDENTITY}"
```

### Verifying

```bash
xcodebuild -showBuildSettings -scheme YourScheme -configuration Debug \
  | grep -E 'CODE_SIGN_IDENTITY|DEVELOPMENT_TEAM'
```

Both lines should show your local values, not the empty/default ones from the tracked xcconfig.

### Source

MousePlus, sessions `2026-04-29-d` and `2026-05-02-a`. Pattern recurred when bootstrapping on a new M-series Mac and again on Spaces (`2026-05-09-build-4-5`).

---

## Pattern 2: SourceKit false positives — *the index is lying*

### Symptom

Xcode (or any IDE that talks to SourceKit-LSP) shows red squigglies that have no business being there:

- `No such module 'SwiftTerm'` — for an SPM module that builds fine.
- `Cannot find type 'Foo' in scope` — for a type defined in a sibling file you just added.
- `'@main' attribute can only apply to top-level code` — on a file that hasn't moved.
- `Cannot find 'XPCService' in scope` — right after regenerating the `.xcodeproj`.

Meanwhile `xcodebuild build` succeeds without a single warning. The errors are noise, not signal — but they look identical to real errors.

### Why it happens

SourceKit maintains a per-file semantic index that's separate from the build. It's eventually consistent, not strongly consistent. The cache invalidates when:

- The `.xcodeproj` is regenerated (e.g. by Tuist, XcodeGen, or `swift package generate-xcodeproj`).
- Files are added/removed/renamed via Xcode 16's synced folders, especially in bulk.
- A multi-file refactor happens via shell/Edit tools while Xcode is open.
- An SPM dependency is added but the package graph hasn't reresolved yet.

While the index rebuilds (10s to several minutes), every file it hasn't reached yet shows as if its types/imports don't exist.

### What NOT to do

- ❌ **Don't chase the error.** Don't add imports, retype declarations, or rewrite the file based on what the editor is telling you. You'll be "fixing" code that already works.
- ❌ **Don't trust the editor's quick-fix suggestions** during this window — they'll suggest fabricating types that already exist elsewhere.
- ❌ **Don't run multi-file refactors based on these errors.** A wave of red squigglies after a multi-file change is the expected state, not a regression.

### What to do instead

**Run `xcodebuild` and check its exit code:**

```bash
xcodebuild build -scheme YourScheme -destination "platform=macOS" -quiet
echo "exit: $?"
```

If `xcodebuild` is green, the code is fine. The editor will catch up.

**To force a faster catch-up:**

```bash
# Quick: just nudge SourceKit
killall SourceKitService 2>/dev/null || true

# Heavier: nuke per-project index and let Xcode rebuild
rm -rf ~/Library/Developer/Xcode/DerivedData/YourProject-*/Index.noindex

# Heaviest: full rebuild (slow but always works)
killall Xcode 2>/dev/null
rm -rf ~/Library/Developer/Xcode/DerivedData/YourProject-*
open YourProject.xcodeproj
```

After re-opening, leave Xcode for 30–120 seconds before judging — the indexer status appears in the activity bar at the top of the window.

### Source

MenuBarPLUS `2026-05-09`, Spaces `2026-05-09-build-4-5`, MyOwnTerminal `2026-04-21`, GPSvideo `2026-05-12-night`, LEARNING-Helper `2026-05-02`, YTdl `2026-05-10`. Same pattern, six different sessions, six different rediscoveries — until now.

---

## The cross-cutting rule

> **`xcodebuild` is the source of truth. The Xcode editor is a UI on top of an eventually-consistent index. When they disagree, trust the build.**

Apply this whenever you do any of:

- Generate / regenerate an `.xcodeproj`
- Add or remove files via shell or Edit tools
- Bulk-rename or move types across files
- Add an SPM dependency
- Switch git branches with structural differences
- Open the project for the first time on a new Mac

In all of those cases, **build first, judge second.** If `xcodebuild` is green, ignore SourceKit complaints for ~60 seconds before reacting.

---

## Quick-reference cheatsheet

| Situation | First move |
|---|---|
| `No "Mac Development" signing certificate found` on a new Mac | Create `Debug.local.xcconfig` (see Pattern 1 recipe). |
| Multiple Macs, identity drift | Confirm `#include?` line is in the tracked xcconfig; bootstrap each Mac with its own local file. |
| `Cannot find type X` after multi-file change | Run `xcodebuild build` — if green, wait 30s, ignore. |
| Red squigglies after `.xcodeproj` regen | Expected. `killall SourceKitService` to nudge, or just wait. |
| `No such module` for SPM dep that built yesterday | `rm -rf ~/Library/Developer/Xcode/DerivedData/Project-*/Index.noindex` and reopen. |
| You've done all the above and `xcodebuild` *also* fails | Now it's a real error. Read the build log. |

---

*Related docs: `30_production-checklist.md` (pre-ship signing checks), `32_git-workflow.md` (gitignore patterns), `14_project-identity.md` (Team ID and bundle conventions).*
