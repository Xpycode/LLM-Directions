# Info.plist build machinery: the INFOPLIST_KEY_ allowlist gotcha, and three ways to get a non-allowlisted key into the built plist

**Tags:** Info.plist, INFOPLIST_KEY_, allowlist, GENERATE_INFOPLIST_FILE, xcodegen info block, UIDesignRequiresCompatibility, INFOPLIST_FILE, PlistBuddy verify, Sparkle SUFeedURL

**Canonical home for this gotcha.** [00-app-shell.md](00-app-shell.md), [16-sparkle-auto-updates.md](16-sparkle-auto-updates.md), and [89-swiftui-native-toolbar-tahoe-glass-optout.md](89-swiftui-native-toolbar-tahoe-glass-optout.md) all hit this and now point here instead of re-explaining it.

## The core gotcha: `INFOPLIST_KEY_*` only honors Apple's allowlist

With `GENERATE_INFOPLIST_FILE = YES` (the modern xcconfig-only default — no physical Info.plist), the obvious way to inject a custom key is a build setting:

```yaml
INFOPLIST_KEY_UIDesignRequiresCompatibility: YES   # ← SILENTLY DOES NOTHING
```

**This fails silently.** The `INFOPLIST_KEY_*` mechanism only injects an **allowlist** of Apple-recognized keys (`CFBundleDisplayName`, `NSHumanReadableCopyright`, `LSApplicationCategoryType`, …). Anything off that list — `UIDesignRequiresCompatibility`, Sparkle's `SUFeedURL`/`SUPublicEDKey`, any other third-party key — is dropped with no build error. The build succeeds, the setting shows up in `xcodebuild -showBuildSettings`, and the final `.app`'s `Info.plist` simply doesn't have the key.

**Always verify on the built bundle, not build settings** (build settings lie):

```bash
/usr/libexec/PlistBuddy -c "Print :UIDesignRequiresCompatibility" \
  "$(xcodebuild -scheme YourApp -showBuildSettings | grep -m1 BUILT_PRODUCTS_DIR | awk '{print $3}')/YourApp.app/Contents/Info.plist"
# Missing key → "Does Not Exist". Present → "true".
```

Three fixes below, in order of how much of `GENERATE_INFOPLIST_FILE`'s convenience you keep.

## Method 1 — xcodegen `info:` block (owns the whole plist)

Point xcodegen at an explicit `info:` block instead of `GENERATE_INFOPLIST_FILE`. Everything under `info.properties` lands verbatim, with no allowlist filtering — but this block **owns and overwrites** the plist, so every key the app needs (including the ones `GENERATE_INFOPLIST_FILE` would normally synthesize) must be listed:

```yaml
targets:
  YourApp:
    type: application
    platform: macOS
    sources:
      - path: YourApp
    info:
      path: YourApp/Info.plist
      properties:
        CFBundleName: $(PRODUCT_NAME)
        CFBundleShortVersionString: $(MARKETING_VERSION)
        CFBundleVersion: $(CURRENT_PROJECT_VERSION)
        CFBundleIdentifier: $(PRODUCT_BUNDLE_IDENTIFIER)
        LSMinimumSystemVersion: $(MACOSX_DEPLOYMENT_TARGET)
        LSApplicationCategoryType: public.app-category.utilities
        NSHumanReadableCopyright: "© 2026 you"
        NSPhotoLibraryUsageDescription: "Reason string"   # only if using PhotoKit
        UIDesignRequiresCompatibility: true               # <-- non-allowlisted key lands here
        NSMainStoryboardFile: ""                          # empty — SwiftUI-only app
        NSPrincipalClass: NSApplication
        NSHighResolutionCapable: true
```

Gitignore the generated plist (`01_Project/YourApp/Info.plist`) alongside the `.xcodeproj` — it's derived from `project.yml`.

**Test target caveat:** unit-test targets don't warrant a custom `info:` block. If base settings no longer carry `GENERATE_INFOPLIST_FILE = YES`, set it per test target:

```yaml
  YourAppTests:
    type: bundle.unit-test
    platform: macOS
    sources: [YourAppTests]
    settings:
      base:
        GENERATE_INFOPLIST_FILE: YES
    dependencies:
      - target: YourApp
```

*Discovered 2026-04-19 during Mural M0 bootstrap: the initial build passed every `xcodebuild -showBuildSettings` check, but the flat-toolbar-button render regressed — `PlistBuddy` on the built app revealed `UIDesignRequiresCompatibility` missing despite being set in build settings. Switching to `info:` fixed it.*

## Method 2 — checked-in `.xcodeproj` (no xcodegen), explicit Info.plist

When the project is a committed `.xcodeproj` (e.g. an XcodeBuildMCP scaffold) with `GENERATE_INFOPLIST_FILE = YES`, there's no `info:` block; supply an explicit `Info.plist` and point the **app target** at it.

**1. Write an explicit `Info.plist`** in the app sources folder. Keep it DRY — reference xcconfig `$(BUILD_SETTING)` tokens rather than hard-coding them. The one key that *must* be a literal is the non-allowlisted one:

```xml
<key>CFBundleExecutable</key>       <string>$(EXECUTABLE_NAME)</string>
<key>CFBundleIdentifier</key>       <string>$(PRODUCT_BUNDLE_IDENTIFIER)</string>
<key>CFBundleName</key>             <string>$(PRODUCT_NAME)</string>
<key>CFBundleShortVersionString</key><string>$(MARKETING_VERSION)</string>
<key>CFBundleVersion</key>          <string>$(CURRENT_PROJECT_VERSION)</string>
<key>CFBundlePackageType</key>      <string>APPL</string>
<key>LSMinimumSystemVersion</key>   <string>$(MACOSX_DEPLOYMENT_TARGET)</string>
<key>NSHighResolutionCapable</key>  <true/>
<key>NSPrincipalClass</key>         <string>NSApplication</string>
<key>UIDesignRequiresCompatibility</key><true/>   <!-- literal: the allowlist drops it -->
```

**2. Point only the app target's xcconfig at it.** With a shared xcconfig `#include`d by both app and test configs, put the override in the **app-only** configs (`Debug.xcconfig` / `Release.xcconfig`), NOT the shared one — otherwise the test target loses its generated plist and fails to build:

```
// Debug.xcconfig AND Release.xcconfig (NOT Shared.xcconfig / Tests.xcconfig):
GENERATE_INFOPLIST_FILE = NO
INFOPLIST_FILE = YourApp/Info.plist
```

**3. Exclude the plist from the target's auto-membership** (Xcode 16+ file-system-synchronized groups only). A `PBXFileSystemSynchronizedRootGroup` auto-adds every file in the folder — including `Info.plist` — to **Copy Bundle Resources**, producing the warning *"The Copy Bundle Resources build phase contains this target's Info.plist file"* and a stray plist in `Contents/Resources/`. Add a `membershipExceptions` entry so it isn't bundled as a resource:

```
/* in project.pbxproj — new exception set, referenced from the app folder's root group */
8B…F1F /* Exceptions for "YourApp" folder in "YourApp" target */ = {
    isa = PBXFileSystemSynchronizedBuildFileExceptionSet;
    membershipExceptions = ( Info.plist, );
    target = 8B…F00 /* YourApp */;
};
/* …then add to the YourApp PBXFileSystemSynchronizedRootGroup: */
exceptions = ( 8B…F1F /* … */, );
```

**Verify on the built bundle:**

```bash
APP="$(xcodebuild -scheme YourApp -showBuildSettings | grep -m1 ' BUILT_PRODUCTS_DIR' | awk '{print $3}')/YourApp.app"
/usr/libexec/PlistBuddy -c "Print :UIDesignRequiresCompatibility" "$APP/Contents/Info.plist"  # → true
ls "$APP/Contents/Resources/Info.plist"   # → No such file (good: not double-copied)
```

*Discovered 2026-06-13 during VEDC Phase 5: XcodeBuildMCP-scaffolded `.xcodeproj` with shared xcconfig + synchronized groups. Putting `INFOPLIST_FILE` in the shared xcconfig broke the test target; the synchronized group double-copied the plist into Resources until the `membershipExceptions` entry was added.*

## Method 3 — xcodegen build-setting merge (keeps `GENERATE_INFOPLIST_FILE` + all `INFOPLIST_KEY_*` settings)

Unlike Method 1 (which hands xcodegen full ownership of the plist), point `INFOPLIST_FILE` at a **minimal hand-managed base plist holding only the non-allowlisted key**, while keeping `GENERATE_INFOPLIST_FILE: YES`. Xcode uses the base file as the seed and **merges the generated/allowlisted keys on top** — both survive.

`project.yml`:
```yaml
settings:
  base:
    GENERATE_INFOPLIST_FILE: YES
    INFOPLIST_FILE: MyApp/Info.plist          # ← minimal base, see below
    INFOPLIST_KEY_CFBundleDisplayName: myapp  # ← still works, merged on top
    INFOPLIST_KEY_LSApplicationCategoryType: "public.app-category.video"
```

`MyApp/Info.plist` (the *entire* file — let Xcode generate everything else):
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>UIDesignRequiresCompatibility</key>
    <true/>
</dict>
</plist>
```

Regenerate, rebuild, **verify the merge** (both keys present proves it worked):
```bash
/usr/libexec/PlistBuddy -c "Print :UIDesignRequiresCompatibility" "$APP/Contents/Info.plist"  # → true
/usr/libexec/PlistBuddy -c "Print :CFBundleDisplayName"             "$APP/Contents/Info.plist"  # → myapp
```

**Don't combine with Method 1.** Do not also use xcodegen's `info: { path:, properties: }` block here unless dropping `GENERATE_INFOPLIST_FILE` and moving *all* `INFOPLIST_KEY_*` values into `properties` — that block makes xcodegen own and overwrite the plist, which fights the generate-and-merge approach (see #47 gotcha #2).

*Extracted from Conjoyn (2026-06-10g): migrating from a custom `HStack` titlebar to a native SwiftUI `.toolbar` on the macOS 26 SDK required this merge fix to opt the app out of Liquid Glass via `UIDesignRequiresCompatibility` without losing the app's existing `INFOPLIST_KEY_*` settings.*

## Sparkle: the same allowlist drop hits custom third-party keys too

`SUFeedURL` and `SUPublicEDKey` are custom keys, not Apple-recognized ones — `INFOPLIST_KEY_SUFeedURL` under `GENERATE_INFOPLIST_FILE = YES` is silently ignored the same way. **Symptom:** Sparkle reports "You must specify the URL of the appcast as the SUFeedURL key in either the Info.plist" even though the xcconfig sets it.

**Fix (Method 3 variant, multiple custom keys at once):** a partial `Info.plist` carrying just the custom keys, merged via `INFOPLIST_FILE` + `GENERATE_INFOPLIST_FILE = YES`:

```xml
<!-- Config/Info.plist -->
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>SUFeedURL</key>
    <string>https://example.com/appcast.xml</string>
    <key>SUPublicEDKey</key>
    <string>YOUR_PUBLIC_KEY_HERE</string>
</dict>
</plist>
```

```
// Shared.xcconfig
GENERATE_INFOPLIST_FILE = YES
INFOPLIST_FILE = Config/Info.plist
// Xcode merges both: generated Apple keys + your custom keys
```

---
