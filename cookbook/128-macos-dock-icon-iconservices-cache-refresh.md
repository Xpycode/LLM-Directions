# 128 · Freshly-built macOS app shows a generic Dock icon — it's the IconServices cache, not the build

**Tags:** Dock icon generic, IconServices cache, lsregister, CFBundleIconName, iconservices.store, killall Dock, DARWIN_USER_CACHE_DIR, actool Emplaced

**Problem.** You generated `AppIcon.appiconset`, the build *succeeded*, `actool` logged
`Emplaced … AppIcon.icns` — but the app launches with the **generic/placeholder** icon in the
Dock (and Cmd-Tab, Finder). The instinct is "the icon didn't build" → you regenerate the asset
catalog, re-run `xcodegen`, clean-build… and it still shows generic. The build was never the
problem: macOS's **LaunchServices / IconServices cache** is showing stale data, and a Debug app
run straight from the deep `~/Library/Developer/Xcode/DerivedData/…` path (not `/Applications`)
is especially prone to it.

**First: prove the icon is actually in the bundle** — so you don't chase a phantom. If these two
checks pass, the build is fine and the problem is 100% the cache:

```bash
APP=$(find ~/Library/Developer/Xcode/DerivedData/<App>-*/Build/Products/Debug/<App>.app -maxdepth 0 | head -1)
/usr/libexec/PlistBuddy -c "Print :CFBundleIconName" "$APP/Contents/Info.plist"   # → AppIcon
ls -l "$APP/Contents/Resources/AppIcon.icns"                                       # → exists, non-trivial size
```

`CFBundleIconName` present + `AppIcon.icns` emplaced = the icon will display correctly anywhere
LaunchServices reads it fresh (a clean Mac, a notarized DMG, `/Applications`). What you're seeing
is a *local cache* artifact, nothing that ships.

**Fix: refresh the caches — do NOT rebuild.**

```bash
APP=$(find ~/Library/Developer/Xcode/DerivedData/<App>-*/Build/Products/Debug/<App>.app -maxdepth 0 | head -1)
touch "$APP"                                                   # bump mtime so LS re-reads
/System/Library/Frameworks/CoreServices.framework/Versions/A/Frameworks/LaunchServices.framework/Versions/A/Support/lsregister -f "$APP"
rm -rf "$(getconf DARWIN_USER_CACHE_DIR)com.apple.iconservices.store"   # the icon cache itself
killall Dock iconservicesagent                                 # force both to re-read
open "$APP"
```

Note `getconf DARWIN_USER_CACHE_DIR` returns a path **with a trailing slash**, so concatenate
`com.apple.iconservices.store` directly (no extra `/`).

## Why it happens
- IconServices memoizes icons keyed by bundle path + mtime. A rebuild that lands at the *same*
  DerivedData path can reuse the stale entry; the generic placeholder gets cached the first time
  the app is registered with no resolvable icon and then sticks.
- Apps outside `/Applications` (DerivedData, a random folder) are second-class to LaunchServices'
  icon resolution — it sometimes clings to the placeholder until forcibly re-registered.

## Gotchas
- **Don't clean-build to fix this.** A clean build re-emplaces the same `.icns` and the cache still
  wins — you'll conclude (wrongly) that the icon is broken. Verify-in-bundle first, then reset cache.
- **The real ship target is fine.** Once the app is in a notarized DMG / dragged to `/Applications`,
  the icon resolves correctly — the cache quirk is a dev-loop annoyance, not a release bug. To force
  it locally without the cache dance, just drag the built `.app` to `/Applications` once.
- **Verify in the *built* Info.plist, not `project.yml`/the catalog.** `CFBundleIconName` is what
  proves the wiring landed; an asset catalog can compile while `ASSETCATALOG_COMPILER_APPICON_NAME`
  is unset, leaving the app icon-less with a green build (see #76).
- `killall Dock` is harmless (the Dock relaunches instantly); `iconservicesagent` likewise.

## See also
- `76-macos-appicon-coregraphics-generator.md` — generate the `AppIcon.appiconset` in the first
  place (and the `ASSETCATALOG_COMPILER_APPICON_NAME` build-setting gotcha).
- Source: VideoContainerSwitcher, 2026-06-22 — blue swap-ring icon emplaced + `CFBundleIconName`
  confirmed, Dock still generic until the cache reset above.
