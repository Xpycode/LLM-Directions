# 119 — Rename a macOS app in place (xcodegen) when the app's name is derived from the third-party engine it wraps

**Problem.** You need to rebrand a macOS app — folders, Xcode target/scheme/project, bundle id,
`PRODUCT_NAME`, the on-screen name, the data dir, a feedback slug — and the app's old name is a
lightly-disguised version of a **third-party binary it bundles**. Here: **YTdl** (the app) wraps
**yt-dlp** (the engine), with Swift types `YTDLPRunner` / `YTDLPUpdater`, a `yt-dlp.entitlements`,
and a `fetch-ytdlp.sh`. The reflex — `grep -rl YTdl | xargs sed -i 's/YTdl/Magpie/g'` — **also
rewrites the engine** (`YTDLPRunner` → `MagpieRunner`, `fetch-ytdlp.sh` paths, the entitlements
that let the bundled binary's Python.framework load) and silently breaks downloads. The app name
and the engine name are near-homographs; a blind rename can't tell them apart.

**Why the case split is the whole trick.** The app token is mixed-case **`YTdl`**; the engine
tokens are **`yt-dlp`** (lowercase + hyphen) and **`YTDLP`** (all-caps). A *case-sensitive*
`s/YTdl/Magpie/` **cannot match either engine form** — `YTDL` ≠ `YTdl`, `yt-dl` ≠ `YTdl`. So the
exact-case token *is* the identity boundary: replace `YTdl`, leave everything else, and the engine
survives untouched. Prove it before and after with a categorising grep that subtracts the engine:

```sh
# Everything that's the APP (engine excluded). This is your work-list AND your final check.
grep -rIn 'YTdl' --include='*.swift' --include='*.yml' --include='*.plist' \
     --include='*.entitlements' --include='*.sh' . \
  | grep -v '/build/' | grep -v '/.git/' \
  | grep -vi 'yt-dlp\|YTDLP\|ytdlp'        # ← the engine subtraction; must be exhaustive
# After the rename, the same command must print NOTHING. Then confirm the engine is STILL there:
grep -rIl 'YTDLP\|yt-dlp' --include='*.swift' --include='*.sh' .   # ← must still list files
```

**Fix — `git mv` for identity, regenerate for the project, case-safe `sed` for content.**

1. **Branch.** `git checkout -b rename/<newname>`. This touches ~100 files; you want one revert.

2. **Drop generated artifacts first**, so the moves only carry tracked source:
   ```sh
   rm -rf 01_Project/OldName/build                       # gitignored
   git rm -r --quiet 01_Project/OldName/OldName.xcodeproj # tracked, but xcodegen regenerates it
   rm -rf 01_Project/OldName/OldName.xcodeproj            # sweep gitignored remnants (xcworkspace)
   ```

3. **`git mv` folders + app-named files** (history preserved — outer dir first, then inner):
   ```sh
   git mv 01_Project/OldName 01_Project/NewName
   git mv 01_Project/NewName/OldName       01_Project/NewName/NewName        # inner source dir
   git mv 01_Project/NewName/OldNameTests  01_Project/NewName/NewNameTests
   git mv .../OldNameApp.swift .../NewNameApp.swift
   git mv .../OldName.entitlements .../NewName.entitlements
   # DO NOT move the engine-named files: yt-dlp.entitlements, YTDLP*.swift, scripts/fetch-ytdlp.sh
   ```

4. **Rewrite `project.yml`** (xcodegen is the source of truth, so the `.pbxproj` churn is
   throwaway): `name`, every `target:` key, the `scheme`, `PRODUCT_BUNDLE_IDENTIFIER`(s),
   `PRODUCT_NAME`, all `sources:`/`Resources` paths, `TEST_HOST`/`TEST_TARGET_NAME`, the
   `CODE_SIGN_ENTITLEMENTS` path, and `info.properties` `CFBundleURLName`. Then `xcodegen generate`
   → confirm `xcodebuild -list` shows the new scheme.

5. **Case-safe `sed` for file *content*** (after Edits to the structured files):
   ```sh
   # Files with ONLY app tokens (no engine string) → blanket replace is safe:
   sed -i '' 's/YTdl/Magpie/g'  HelpFile.swift TestFiles.swift CLAUDE.md scripts/*.sh
   # @testable import OldName → NewName (module = PRODUCT_NAME) is the build-critical one in tests.
   ```
   Hand-edit (don't blanket) anything that *also* contains engine strings or your own prose. Cover:
   type names (`OldNameApp`→`NewNameApp`), the **feedback/telemetry slug**, **`os.Logger`
   subsystems**, the **`~/Library/Application Support/OldName/` data dir**, the **UserDefaults key
   prefix**, the window title, and every Help/About/Settings string.

6. **Verify the built bundle's identity** (not just "build succeeded"):
   ```sh
   APP=$(find ~/Library/Developer/Xcode/DerivedData/NewName-*/Build/Products/Debug -name 'NewName.app' | head -1)
   /usr/libexec/PlistBuddy -c 'Print :CFBundleName'       "$APP/Contents/Info.plist"  # NewName
   /usr/libexec/PlistBuddy -c 'Print :CFBundleIdentifier' "$APP/Contents/Info.plist"  # com.x.NewName
   ls "$APP/Contents/MacOS/"                                                            # executable = NewName
   ```
   Plus the normal clean build + tests.

7. **Outward (after the local build is green):** `gh repo rename NewName -R Owner/OldName --yes`
   then `git remote set-url origin …/NewName.git`; merge to `main`; push.

**Gotchas.**

- **The engine-homograph trap is the entire reason this is a pattern.** If the app name were
  unrelated to anything it bundles, a blanket rename would just work. Always check first whether the
  name encodes a dependency.
- **Pre-release ⇒ no migration shim; post-ship ⇒ you need one.** Renaming the **bundle id** moves
  `UserDefaults` to a fresh domain and renaming the **Application Support dir** orphans the old one.
  Harmless before you've shipped (delete the stale `~/Library/Application Support/OldName/` by hand).
  After real users exist, write a one-time migrate-on-launch (copy old prefs/data dir → new) or you
  silently wipe their history.
- **`sed` will eat your own prose.** A docs line "scheme updated from `old://` to `new://`" becomes
  "from `new://` to `new://`" after `s/old/new/g`. Re-read changed prose; fix by hand.
- **Cross-repo coupling fails *silently*.** If a server-side allowlist keys on the app's slug
  (e.g. a self-hosted feedback endpoint, see #49), the app posting the **new** slug gets rejected
  ("Please choose an app from the list") until that *other* repo's `apps.json` is updated **and
  deployed**. Deploy ≠ `git push` — a static site uploads via SFTP/`rsync`; committing the slug
  change does nothing for the live server. Treat "update slug" and "deploy site" as two steps, and
  note when the deploy can't run from the current Mac (missing `~/.netrc` etc.).
- **`git mv` on a directory leaves gitignored children behind** (the `build/` dir, the
  `*.xcodeproj/project.xcworkspace/`). They get dragged along or stranded — `rm -rf` them; xcodegen
  + xcodebuild rebuild everything.
- **Rename the top-level repo folder LAST.** If the working directory itself is named after the app,
  renaming it mid-session breaks the agent's cwd, the memory path, and serena/MCP project roots. Do
  it as a final manual step and reopen in the new path. (Git itself doesn't care about the container
  folder name.)
- **The icon and design briefs are separate work.** A name change doesn't redraw the icon; if the
  old icon's *concept* was tied to the old name, commission a new one (#76 regenerates the asset
  catalogue from a re-runnable generator — re-run it, don't hand-edit PNGs).

**Source:** Magpie (née YTdl) — full rebrand 2026-06-17, branch `rename/magpie`, commit
`94d3b3b` (94 `git mv` renames + 7 content edits, 91 tests green). `decisions.md` "Rename the app
from YTdl to Magpie" has the name-selection rationale.

Pairs with **#34** (clone-and-rename a *different* Xcode project — the sibling when you're forking,
not renaming in place), **#47 / #58** (xcodegen + post-build-script setup this regenerates),
**#76** (the Core-Graphics app-icon generator — re-run after the rename), **#49** (the PHP feedback
server whose `apps.json` slug allowlist is the cross-repo coupling that breaks silently), **#00**
(App Shell Standard / `Theme`).
