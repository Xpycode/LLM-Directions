# Clone-and-rename an existing Xcode project

**Source:** `1-macOS/AvidMXFPeek/` (forked from `1-macOS/P2toMXF/`, 2026-04-20)

When a new app needs the same toolchain bundling, entitlements, Run Script phases, and codesigning setup as an existing app, **clone the working `.xcodeproj` instead of scaffolding from Xcode's template**. Build-phase archaeology is the failure mode you're avoiding.

---

## When to use

Spinning up app B that needs:
- Bundled CLI tools (ffmpeg, mxf2raw, yt-dlp, etc.) with `@executable_path` dylib rewiring
- Run Script phases that `ditto` `Resources/lib/` into the `.app` bundle
- Non-trivial entitlements (`disable-library-validation`, `allow-unsigned-executable-memory`, sandbox off)
- `UIDesignRequiresCompatibility = true` in Info.plist (cookbook 00)
- Hardened runtime + codesign ordering that took weeks to get right the first time

...and app A already has all of that working. Don't re-derive; clone.

**Not for:** a brand-new category of app with different frameworks/entitlements — use Xcode's template there.

---

## The recipe

Assume source is `1-macOS/AppA/01_Project/AppA.xcodeproj` (target `AppA`, bundle `com.foo.AppA`) and target is `1-macOS/AppB/01_Project/AppB.xcodeproj` (target `AppB`, bundle `com.bar.AppB`, display name `"App B"`).

```bash
set -e
SRC=/Users/you/XcodeProjects/1-macOS/AppA/01_Project
DST=/Users/you/XcodeProjects/1-macOS/AppB/01_Project

# 1. Copy source + Resources/ + dylibs + entitlements + Info.plist
cp -R "$SRC/AppA"            "$DST/AppB"
# 2. Copy the project file
cp -R "$SRC/AppA.xcodeproj"  "$DST/AppB.xcodeproj"
# 3. Strip user-specific state (breadcrumbs, schemes you don't want to carry)
rm -rf "$DST/AppB.xcodeproj/xcuserdata"
rm -rf "$DST/AppB.xcodeproj/project.xcworkspace/xcuserdata"
# 4. Rename the app entry file and entitlements file
mv "$DST/AppB/AppAApp.swift"      "$DST/AppB/AppBApp.swift"
mv "$DST/AppB/AppA.entitlements"  "$DST/AppB/AppB.entitlements"
# 5. The sed sweep (BSD sed — note the empty '' after -i)
PBX="$DST/AppB.xcodeproj/project.pbxproj"
sed -i '' 's/AppA/AppB/g' "$PBX"
sed -i '' 's/com\.foo\.AppA/com.bar.AppB/g' "$PBX"
sed -i '' 's/MARKETING_VERSION = 1\.2;/MARKETING_VERSION = 1.0;/g' "$PBX"
sed -i '' 's/CURRENT_PROJECT_VERSION = 1200;/CURRENT_PROJECT_VERSION = 1;/g' "$PBX"
# Display name WITH SPACES — the quotes are important
sed -i '' 's/INFOPLIST_KEY_CFBundleDisplayName = AppB;/INFOPLIST_KEY_CFBundleDisplayName = "App B";/g' "$PBX"
# 6. Same sweep on Swift sources (app struct name, namespace strings, etc.)
find "$DST/AppB" -name "*.swift" -exec sed -i '' 's/AppA/AppB/g' {} \;
# 7. Blank any hard-coded URLs that don't apply (Sparkle feed, analytics, etc.)
```

After: `cd 01_Project && xcodebuild -list -project AppB.xcodeproj`. Xcode auto-generates a scheme from the target if none was checked in, so the first `xcodebuild -scheme AppB build` just works.

---

## Gotchas

**BSD sed vs. GNU sed.** On macOS, `sed -i` requires an empty extension arg: `sed -i '' 's/.../.../' file`. Linux users bitten by this forget and get `sed -i` silently eating their first positional arg.

**Display name with spaces needs quotes in pbxproj.** `INFOPLIST_KEY_CFBundleDisplayName = App B;` is a syntax error; the quoted form `= "App B";` is required. This is ONLY true when the name has whitespace — single-word names go unquoted.

**`xcuserdata` contains absolute paths and breadcrumb state.** If you leave it in, the new project will re-open with the OLD project's last-open tabs, debugger state, etc. Always delete.

**`com.foo.AppA` → `com.bar.AppB`: the domain changes, not just the app name.** Verify via `grep PRODUCT_BUNDLE_IDENTIFIER "$PBX"` after the sed that the result is exactly what you expect. Partial substitutions are the subtle failure mode.

**Swift source references, not just the pbxproj.** `UserDefaults` keys (`"AppA.somePref"`), Application Support folder names (`appSupport.appendingPathComponent("AppA")`), log prefixes (`"[AppA]"`), power-assertion reason strings — all hand-embedded strings need the rename. `grep -rc "AppA" "$DST/AppB" --include="*.swift" | grep -v ":0$"` finds them before build time.

**SPM dependencies survive the clone intact.** Sparkle, Lottie, etc. that are added as SwiftPM packages keep working — the dep is listed in pbxproj but its resolution state is in `*.xcodeproj/project.xcworkspace/` which you're keeping. First `xcodebuild` will re-resolve silently.

**If the old project has `xcschemes/*.xcscheme` shared** (not in `xcuserdata`), they'll carry over too — inspect and either rename-sweep or delete them so Xcode regenerates fresh.

---

## Verifying the clone

```bash
cd "$DST"
xcodebuild -scheme AppB -project AppB.xcodeproj -configuration Debug \
  -destination "platform=macOS" clean build 2>&1 | \
  grep -E "error:|warning:|\*\* (BUILD|build)"
```

Should print `** BUILD SUCCEEDED **` and zero errors. If errors, they're almost always one of:
- Dangling `Notification.Name.oldAppSpecific` references — a forgotten hand-embedded string; stub as legacy or rewrite
- `Info.plist` keys that referred to bundled assets you didn't copy over
- Codesign failure because the old project used a different Developer ID than the new machine has — either switch teams or turn off automatic signing for the first build

Launch the `.app` after the build to verify runtime. Build success is necessary but not sufficient.

---

## When NOT to use

- **Fundamentally different app category** (iOS vs. macOS, extensions, unit-test-only) — Xcode's template is closer to where you want to end up
- **You need to clean up the source app's accumulated cruft** — cloning preserves every weird decision. A cleaner option: use the source's Info.plist + entitlements + build-phase XML as a **reference** while configuring a fresh Xcode-template project
- **Source project is under active development** — if AppA changes its build config two days after you fork, AppB will silently diverge. Freeze AppA at a known-good commit (or vendor the reference files into AppB's `docs/`) so future-you knows what was cloned

---

## Related patterns

- [00-app-shell.md](00-app-shell.md) — what the retrofitted views should look like after the clone
- [06-app-lifecycle.md](06-app-lifecycle.md) — `@main` entry + service initialization
- [16-sparkle-auto-updates.md](16-sparkle-auto-updates.md) — if the cloned project had Sparkle, re-wiring it to a new feed
- [33-managed-developer-id.md](33-managed-developer-id.md) — codesigning the clone when your team has moved to managed IDs
