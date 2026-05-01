# #58 — `xcodegen` postBuildScripts: sandbox-safe + dependency-analysis-friendly

**Extracted from:** MyOwnTerminal (2026-04-25)

A `postBuildScripts` entry that copies resources at build time fails in two ways out of the box:

1. **"Run script will be run during every build because it does not specify any outputs"** — Xcode warning; the phase re-runs on every incremental build because dependency analysis has nothing to compare.
2. **`Sandbox: bash(NNNNN) deny(1) file-read-data /path/to/source/Resources`** — under Xcode's sandboxed build system, scripts can't read source files outside `$TARGET_BUILD_DIR` unless declared as inputs.

Both are fixed by adding `inputFiles` + `outputFiles` to the script entry. The fix composes; you need both.

---

## Symptoms

```
warning: Run script build phase 'Copy Hack Fonts' will be run during every build
because it does not specify any outputs. To address this issue, either add
output dependencies to the script phase, or configure it to run in every build
by unchecking "Based on dependency analysis" in the script phase.
```

```
PhaseScriptExecution Copy\ Hack\ Fonts ...
Sandbox: bash(83756) deny(1) file-read-data
  /Users/.../Resources/Fonts
Command PhaseScriptExecution failed with a nonzero exit code
```

If you only fix #1 (add `outputFiles`), the warning goes away but the sandbox deny still kills the build. If you only fix #2 (add `inputFiles`), the sandbox lets through but the phase still re-runs every build. **Both keys must be set.**

---

## The fix

```yaml
# project.yml
targets:
  MyApp:
    postBuildScripts:
      - name: Copy Hack Fonts
        script: |
          FONTS_SRC="${PROJECT_DIR}/MyApp/Resources/Fonts"
          FONTS_DST="${TARGET_BUILD_DIR}/${CONTENTS_FOLDER_PATH}/Resources/Fonts"
          mkdir -p "$FONTS_DST"
          cp "$FONTS_SRC"/*.ttf "$FONTS_DST/"
        inputFiles:
          - $(PROJECT_DIR)/MyApp/Resources/Fonts/Hack-Regular.ttf
          - $(PROJECT_DIR)/MyApp/Resources/Fonts/Hack-Bold.ttf
          - $(PROJECT_DIR)/MyApp/Resources/Fonts/Hack-Italic.ttf
          - $(PROJECT_DIR)/MyApp/Resources/Fonts/Hack-BoldItalic.ttf
        outputFiles:
          - $(TARGET_BUILD_DIR)/$(CONTENTS_FOLDER_PATH)/Resources/Fonts/Hack-Regular.ttf
          - $(TARGET_BUILD_DIR)/$(CONTENTS_FOLDER_PATH)/Resources/Fonts/Hack-Bold.ttf
          - $(TARGET_BUILD_DIR)/$(CONTENTS_FOLDER_PATH)/Resources/Fonts/Hack-Italic.ttf
          - $(TARGET_BUILD_DIR)/$(CONTENTS_FOLDER_PATH)/Resources/Fonts/Hack-BoldItalic.ttf
```

Then `cd 01_Project && xcodegen generate`. xcodegen maps `inputFiles`/`outputFiles` directly into the generated `.pbxproj`'s `PBXShellScriptBuildPhase` `inputPaths` and `outputPaths`.

---

## What each list does

### `inputFiles` — sandbox permission grant
Each path is added to the sandbox profile for the script's bash process. Without it, any `cat`/`cp`/`head`/`stat` against a source path outside `$TARGET_BUILD_DIR` triggers a `deny(1) file-read-data`. Globs (`$(PROJECT_DIR)/MyApp/Resources/Fonts/*.ttf`) **don't** work — the sandbox profile needs concrete paths.

### `outputFiles` — dependency analysis hint
Xcode compares each output file's mtime against the corresponding input. If all outputs exist and are newer than all inputs, the phase is **skipped on incremental builds**. On clean builds the phase runs. On a font swap the phase reruns once.

Without `outputFiles`, the build system has no idea what the script produces, so it has to assume the script must run every time — that's the warning.

---

## Why `$(...)` not `${...}`

xcodegen passes these strings through as-is to the pbxproj. Xcode's pbxproj uses `$(VAR)` syntax for build settings, not shell `${VAR}`:

```yaml
# Correct — pbxproj-style
inputFiles:
  - $(PROJECT_DIR)/MyApp/Resources/Fonts/Hack-Regular.ttf

# Wrong — shell-style, gets passed literally to the build system
inputFiles:
  - ${PROJECT_DIR}/MyApp/Resources/Fonts/Hack-Regular.ttf
```

Inside the `script:` block itself, you're in shell, so `${PROJECT_DIR}` and `$(VAR)` both work — keep using `${VAR}` there for clarity.

---

## When you have many files

For a Resources/Fonts/ directory with 20 fonts, listing all 20 in YAML twice is annoying but correct. Three alternatives, in order of preference:

### Option A — `inputFileLists` / `outputFileLists` (xcfilelist)
Create a `Fonts.xcfilelist` file listing one path per line, and reference it in xcodegen:

```yaml
postBuildScripts:
  - name: Copy Hack Fonts
    script: |
      cp "${PROJECT_DIR}/MyApp/Resources/Fonts"/*.ttf \
         "${TARGET_BUILD_DIR}/${CONTENTS_FOLDER_PATH}/Resources/Fonts/"
    inputFileLists:
      - $(PROJECT_DIR)/MyApp/Resources/Fonts.input.xcfilelist
    outputFileLists:
      - $(PROJECT_DIR)/MyApp/Resources/Fonts.output.xcfilelist
```

Inside `Fonts.input.xcfilelist`:
```
$(PROJECT_DIR)/MyApp/Resources/Fonts/Hack-Regular.ttf
$(PROJECT_DIR)/MyApp/Resources/Fonts/Hack-Bold.ttf
…
```

### Option B — Generate file lists at xcodegen time
Use a small pre-build script that writes the .xcfilelist files from a glob, then runs xcodegen. Adds a step but keeps `project.yml` clean.

### Option C — Just bundle them as `resources:` instead
For static asset directories that don't have an obvious "binary that xcodegen ignores" reason, prefer letting xcodegen handle them as Copy Bundle Resources. Use a build script only when xcodegen can't auto-pick the file type — the canonical case is `.ttf` fonts (see #47).

---

## Verify the fix

```bash
xcodebuild -scheme MyApp -project MyApp.xcodeproj clean build 2>&1 | grep -E "(warning|error|Sandbox)"
# → no warnings, no Sandbox denies

# Second build (no source changes) — phase should skip:
xcodebuild -scheme MyApp -project MyApp.xcodeproj build 2>&1 | grep "Copy Hack Fonts"
# → no output (phase was skipped)

# Touch a source font, rebuild:
touch MyApp/Resources/Fonts/Hack-Regular.ttf
xcodebuild -scheme MyApp -project MyApp.xcodeproj build 2>&1 | grep "Copy Hack Fonts"
# → "PhaseScriptExecution Copy\ Hack\ Fonts ..." (phase ran)
```

---

## Composes with

- **#47 (xcodegen-swiftterm-setup)** — extends gotcha #1 (binary fonts not auto-included). Original entry showed the script phase; this entry adds the `inputFiles`/`outputFiles` keys it should have had from the start.
- **#34 (xcodeproj-clone-rename)** — when forking a project, the `inputFiles`/`outputFiles` arrays use absolute paths in the source `.pbxproj`. Either re-run xcodegen post-clone (preferred) or sed-rewrite the `inputPaths` / `outputPaths` arrays in the cloned `.pbxproj`.

---

## Quick checklist

- [ ] Both `inputFiles` AND `outputFiles` declared (one alone is insufficient)
- [ ] Use `$(VAR)`, not `${VAR}`, in xcodegen path entries
- [ ] List concrete paths — globs don't work for sandbox grants
- [ ] If list grows past ~10 entries, switch to `inputFileLists` / `outputFileLists` with `.xcfilelist` files
- [ ] After editing project.yml, **always** `xcodegen generate` before building
