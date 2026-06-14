# #106 — `xcodebuild` "Cycle inside <target>" from an in-place re-sign script phase

**Extracted from:** Penumbra (2026-06-14)

A Run Script build phase that **modifies a bundle file in place** — the classic case is
re-signing an embedded helper binary (`ffmpeg`, `ffprobe`, a sidecar tool) with Hardened
Runtime after it's copied into `Contents/Resources` — declares that same file as **both** an
`inputPath` **and** an `outputPath`. That is a self-referential dependency: "to run, I need
`ffmpeg`; I also produce `ffmpeg`." The build graph can't order a node against itself, so it
errors. Worse, because the declared output lives inside the app bundle, **App Intents metadata
extraction** (and other bundle-consuming tasks) are forced to depend on it too, widening the
loop.

The trap: **Xcode.app's GUI build scheduler tolerates the cycle** (it resolves the ordering
leniently), so the project builds fine in the IDE for months. **`xcodebuild` on the CLI does
not** — it aborts every `build` and `test`. So this surfaces the first time you build in CI, a
`git worktree`, a fresh clone, or any headless/scripted build.

---

## Symptoms

```
error: Cycle inside Penumbra; building could produce unreliable results.
This usually can be resolved by moving the shell script phase
'Re-sign embedded ffmpeg/ffprobe with Hardened Runtime' so that it runs before
the build phase that depends on its outputs.

… CYCLE POINT …
node: …/Penumbra.app/Contents/Resources/ffmpeg ->
command: PhaseScriptExecution Re-sign embedded ffmpeg/ffprobe …
```

- Builds **in Xcode.app**, fails on **`xcodebuild build`/`test`** with `** BUILD FAILED **`.
- The cycle trace names your re-sign script phase and a bundle resource it both reads and writes.
- The error's own suggestion ("move the phase earlier") is usually a red herring — the real
  problem is the **output declaration**, not phase order.

---

## The fix

In the `PBXShellScriptBuildPhase`, declare **only an external stamp file** as the output — never
the in-place-modified bundle file. The script already writes a `.stamp` to `$(DERIVED_FILE_DIR)`;
make that the sole `outputPaths` entry.

```diff
   inputPaths = (
     "$(TARGET_BUILD_DIR)/$(UNLOCALIZED_RESOURCES_FOLDER_PATH)/ffmpeg",
     "$(TARGET_BUILD_DIR)/$(UNLOCALIZED_RESOURCES_FOLDER_PATH)/ffprobe",
   );
   outputPaths = (
-    "$(TARGET_BUILD_DIR)/$(UNLOCALIZED_RESOURCES_FOLDER_PATH)/ffmpeg",
-    "$(TARGET_BUILD_DIR)/$(UNLOCALIZED_RESOURCES_FOLDER_PATH)/ffprobe",
-    "$(TARGET_BUILD_DIR)/$(UNLOCALIZED_RESOURCES_FOLDER_PATH)/ffmpeg.cstemp",
-    "$(TARGET_BUILD_DIR)/$(UNLOCALIZED_RESOURCES_FOLDER_PATH)/ffprobe.cstemp",
     "$(DERIVED_FILE_DIR)/ffmpeg-ffprobe-resign.stamp",
   );
```

The script keeps `alwaysOutOfDate = 1` (runs every build) and still `codesign --force --options
runtime`s both tools in place — **no runtime or signing behavior changes**, only the build-graph
*declaration*. CLI `xcodebuild build` + `test` then succeed.

---

## Why this works

- An **output** declaration tells the build system "this file did not exist until I produced it,"
  which manufactures a dependency edge with whoever copied/created it → a loop when the script also
  lists it as input. A file modified **in place** is not an output in the graph's sense.
- A **stamp** in `$(DERIVED_FILE_DIR)` is the correct dependency anchor: it lives **outside** the
  bundle, so it tracks "did this phase run" without entangling any bundle consumer (App Intents
  extraction, downstream signing). The `inputPaths` still order the phase **after** the resources
  are copied, which is all you need.
- Drop the `.cstemp` outputs too — they're transient files `codesign` creates/deletes inside the
  Resources folder, and listing anything in that folder as an output re-creates the entanglement.

---

## When this applies

Any macOS/iOS target with a **Run Script phase that mutates a bundle file in place** and lists
that file as an output: Hardened-Runtime re-signing of embedded binaries (FFmpeg, ExifTool,
yt-dlp, a sidecar XPC tool), in-place `install_name_tool`/`strip`/`plutil` rewrites, asset
post-processing. Tell: it builds in the IDE but a CI/worktree/clean `xcodebuild` reports
"Cycle inside <target>".

**Raw `.pbxproj` projects:** edit `outputPaths` directly. **xcodegen projects:** set the script's
`outputFiles:` to the stamp only and `xcodegen generate`. (For the *resource-copy* sandbox/dep
variant — a script that **copies** files in, needing `inputFiles` + `outputFiles` — see **#58**;
that one wants real outputs, this one must not declare the in-place file as one.)

Verify with `xcodebuild`, not Xcode.app or LSP diagnostics — the whole point is that the GUI hides
this. Note embedded binaries are often **gitignored** (large), so a fresh worktree/CI checkout
must copy them in before the build, or the re-sign phase (and bundle-presence tests) fail for a
*different* reason.

Related: **#58** (xcodegen postBuildScripts resource-copy: needs both input+output files) ·
**#00** (app shell / build setup).
