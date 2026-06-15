# 110 — Deep-linking into macOS System Settings panes (`x-apple.systempreferences:`) and verifying the bundle ids against the installed ExtensionKit registry

**Extracted from:** LaunchAway (2026-06-15)

You want a launcher / menu-bar utility / onboarding flow to jump straight to a System Settings pane — type "wifi", land on Wi-Fi. The mechanism is a URL:

```swift
NSWorkspace.shared.open(URL(string: "x-apple.systempreferences:com.apple.wifi-settings-extension")!)
```

The catch: the trailing identifier is the pane's **extension bundle id**, and on macOS 13+ (Ventura's settings rewrite, and very much macOS 26 Tahoe) each pane is an **ExtensionKit app extension** whose id is **not** guessable from the pane's display name and **drifts across OS releases**. Guess wrong and the URL silently no-ops or dumps the user on the Settings landing page — which in a quick click-test looks like "it opened *something*," hiding the mis-route. You need a deterministic way to (a) discover the correct id and (b) verify it on the machine you're shipping to.

## The catalog pattern

Model each pane as a `LaunchTarget` whose action is the URL open. Curate a static list — the panes don't change between launches, so there's nothing to enumerate at runtime:

```swift
@MainActor
enum SettingsPaneCatalog {
    private struct PaneDefinition {
        let displayName: String
        let symbolName: String        // SF Symbol for the row icon
        let urlString: String         // "x-apple.systempreferences:<bundle-id>"
        let aliases: [String]         // search keys: ["Wi-Fi", "WiFi", "Wireless", "Network"]
    }

    static func panes() -> [LaunchTarget] {
        definitions.map { def in
            LaunchTarget(
                id: def.urlString,
                displayName: def.displayName,
                searchKeys: def.aliases,
                icon: NSImage(systemSymbolName: def.symbolName, accessibilityDescription: def.displayName),
                kind: .settingsPane(url: URL(string: def.urlString)!)
            )
        }
    }
    private static let definitions: [PaneDefinition] = [ /* … */ ]
}
```

Aliases matter: users type "wifi" and "wireless" and "network" for the same pane — fold them all into `searchKeys` so the fuzzy matcher hits.

## Verifying / discovering the bundle id — read the OS's own extension registry

On Tahoe the panes live as `.appex` bundles in `/System/Library/ExtensionKit/Extensions/`. **The folder names are display-named, not the bundle id** — `UsersGroups.appex`, `Touch ID & Password.appex`, `Wi-Fi.appex` — so you can't read the directory listing and call it done. The id the `x-apple.systempreferences:<id>` URL actually routes to is the `CFBundleIdentifier` inside each bundle's `Info.plist`:

```bash
cd /System/Library/ExtensionKit/Extensions/
for ext in "Wi-Fi" "Bluetooth" "Touch ID & Password" "UsersGroups"; do
  id=$(/usr/libexec/PlistBuddy -c "Print :CFBundleIdentifier" "$ext.appex/Contents/Info.plist" 2>/dev/null)
  echo "$ext.appex  ->  $id"
done
# Wi-Fi.appex             -> com.apple.wifi-settings-extension
# Bluetooth.appex         -> com.apple.BluetoothSettings
# Touch ID & Password.appex -> com.apple.Touch-ID-Settings.extension
# UsersGroups.appex       -> com.apple.Users-Groups-Settings.extension
```

Match each catalog `urlString` against this and you've **proven** the deep link resolves — without clicking. This beats a manual walk two ways: a click-test can't distinguish "Wi-Fi opened" from "Wi-Fi-typed-but-landed-on-Network," and it can't tell you *why* a broken pane broke. Reading the declared id removes the ambiguity. (Belt-and-suspenders: still live-open one or two to confirm the `x-apple.systempreferences:` scheme itself is wired, then trust the registry match for the rest.)

To **discover** an id you don't have yet, grep the whole registry by display name:

```bash
for p in /System/Library/ExtensionKit/Extensions/*.appex; do
  printf '%s\t%s\n' \
    "$(/usr/libexec/PlistBuddy -c 'Print :CFBundleIdentifier' "$p/Contents/Info.plist" 2>/dev/null)" \
    "$(basename "$p")"
done | grep -i bluetooth
```

## Notes / caveats

- **The id naming is inconsistent — do not pattern-match it.** Most panes follow `com.apple.<Name>-Settings.extension` (e.g. `com.apple.Network-Settings.extension`), but Bluetooth is `com.apple.BluetoothSettings` (no `.extension`, no hyphens) and Wi-Fi is `com.apple.wifi-settings-extension` (lowercase, different word order). There is no rule — read each from disk.
- **These drift across major macOS versions.** Treat the verification as having a shelf life: re-run the loop each OS bump and leave a dated "verified on macOS NN" comment next to each id (and a reminder to re-check), so the next person knows exactly what to re-run when a pane breaks after an update.
- **Pre-Ventura was different.** Old System Preferences used `x-apple.systempreferences:com.apple.preference.<name>` (`.sound`, `.network`) backed by `.prefPane` bundles in `/System/Library/PreferencePanes/`. The ExtensionKit registry is the Ventura+/Tahoe replacement; if you support older OSes you need both id sets keyed by `if #available`.
- **Anchors (sub-panes) are separate and fragile.** Some links take a `?…` fragment to deep-link within a pane (e.g. a specific Privacy category). Those anchor strings aren't in the bundle and are even more version-sensitive — verify by opening, not by registry.
- **No special entitlement** to open these from a non-sandboxed app; `NSWorkspace.shared.open` is enough. Under the App Sandbox, opening `x-apple.systempreferences:` URLs is restricted — another reason LaunchAway ships sandbox-off.

Source: LaunchAway `01_Project/LaunchAway/Index/SettingsPaneCatalog.swift` (`SettingsPaneCatalog.panes()`, the curated `definitions` list). Pairs with #96 (the sibling app-bundle indexer — both build a `LaunchTarget` candidate set), #74/#75 (permission-free macOS enumeration), #65 (the cursor-anchored panel that surfaces these results), #00 (App Shell Standard).
