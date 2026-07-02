# 151 · Wire an Icon Composer `.icon` as a macOS app icon (Xcode 26, via xcodegen)

**Tags:** Icon Composer, .icon, type: file, ASSETCATALOG_COMPILER_APPICON_NAME, actool, Liquid Glass, CFBundleIconName, Assets.car

**Problem.** You designed the app icon in **Icon Composer** (Xcode 26) — a `Foo.icon` bundle
(`icon.json` describing gradient fills + layer transforms, plus `Assets/*.png` layers). You want to
ship *that* as the app icon and get the macOS 26 **Liquid Glass** appearance variants
(Default / Dark / Tinted / Clear) — **not** hand-export a flat `AppIcon.appiconset` (cookbook 76) and
lose the layers/variants. And you're generating the project with **xcodegen**, which doesn't know the
`.icon` extension.

**Solution.** Reference the `.icon` bundle directly as a **single file wrapper** in `project.yml` and
name it via the app-icon build setting. Xcode 26's `actool` compiles it into `Assets.car` (every size
+ all appearance variants) and emits an `.icns` fallback for older deployment targets.

Used for: **TimeCodeEditor** (`02_Design/icon.icon`, wired 2026-07-01).

---

## The two lines that matter

```yaml
# project.yml — the app target
targets:
  Foo:
    sources:
      - path: Foo                       # normal source glob
      - path: ../02_Design/Foo.icon     # the icon — a repo-relative path is fine (keeps one source of truth)
        type: file                      # ← CRITICAL: treat the .icon bundle as ONE wrapper
    settings:
      base:
        ASSETCATALOG_COMPILER_APPICON_NAME: Foo   # ← the .icon BASE name (Foo.icon → "Foo")
```

### Gotcha 1 — `type: file` (the whole trick)
A `.icon` is a **directory bundle**. Without `type: file`, xcodegen descends into it and adds
`icon.json` + every `Assets/*.png` as **loose resources** (and the app icon silently doesn't build).
`type: file` forces a single file-wrapper reference — xcodegen routes it to the resources phase and the
asset compiler picks it up. (xcodegen needn't "know" `.icon`; `type: file` overrides its guessing.)

### Gotcha 2 — the setting takes the *base name*, not `AppIcon`
`ASSETCATALOG_COMPILER_APPICON_NAME` must equal the `.icon` filename without extension
(`Foo.icon` → `Foo`). It does **not** have to be `AppIcon`, and there is **no `.xcassets`** involved —
`.icon` files are standalone (they replaced the appiconset for app icons in Xcode 26).

---

## Verify (don't trust "BUILD SUCCEEDED")

Build log should show actool driving the `.icon`, then emplacing a `.car` + fallback `.icns`:

```
actool … --app-icon Foo …/Foo.icon
note: Emplaced …/Foo.app/Contents/Resources/AppIcon.icns
note: Emplaced …/Foo.app/Contents/Resources/Assets.car
note: Emplaced …/Foo.app/Contents/Resources/Foo.icns
```
```bash
APP=…/Foo.app
/usr/libexec/PlistBuddy -c "Print :CFBundleIconName" "$APP/Contents/Info.plist"   # → Foo
ls "$APP/Contents/Resources"/*.icns "$APP/Contents/Resources/Assets.car"          # → present
```

### Gotcha 3 — a missing app icon is a **warning**, not an error
If the catalog/`.icon` is absent or misnamed, `actool` emits a **warning** and emplaces nothing — the
build still **succeeds** and the test suite stays green. So a plain `BUILD SUCCEEDED` (or 164 passing
tests) will **not** catch a missing app icon. Catch it with `/minimums` (cookbook 33) or by grepping
the build for `Emplaced …AppIcon.icns`.

---

## Notes
- **Toolchain:** requires **Xcode 26 / macOS SDK 26** for the `.icon` format. With a lower deployment
  target (e.g. `macOS 14.0`) it still builds — macOS 14–15 show the flat `.icns`; the glass variants
  light up on macOS 26.
- **Single source of truth:** keep the `.icon` in `02_Design/` and reference it (repo-relative path).
  Editing in Icon Composer + a rebuild is the whole loop — **no re-export step**, no PNG set to resync.
- **Dock caches icons** aggressively; relaunch the app (or `killall Dock`) if a change doesn't show.
- The `.icon` bundle (`icon.json` + `Assets/*.png`) is now a **build dependency** — commit it, or a
  fresh clone / second Mac can't build.

## See also
- `76-macos-appicon-coregraphics-generator.md` — the older/flat path: generate a full `AppIcon.appiconset`
  with Core Graphics per-size (use when you have *no* `.icon` source or must support pre-Xcode-26).
- `33_app-minimums.md` — the checklist that flags a missing icon.
