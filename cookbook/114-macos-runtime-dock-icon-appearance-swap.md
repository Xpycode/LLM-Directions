# 114 — macOS light/dark Dock icon: swap at RUNTIME, the bundle icon can't vary by appearance

**Problem.** A designer ships a macOS app icon in two appearances (dark + light surround, constant
brand mark) and a HANDOFF that says *"set the AppIcon image set to Appearances: Any, Dark and macOS
swaps automatically with the system theme."* You wire a combined `AppIcon.appiconset` (light PNGs in
"Any", dark PNGs as `luminosity: dark`)… and the Dock icon never changes with the system theme.

**Why — the bundle app icon on macOS is appearance-agnostic; the handoff advice is iOS-only.**
`actool` compiles a macOS app icon to a **single** representation. The dark renditions are silently
dropped — the build log says:

```
warning: The app icon set "AppIcon" has 10 unassigned children.
```

and the emitted `Assets.car` carries only the "Any" images. **Verify it yourself** (don't trust the
warning's wording, prove the cause):

```sh
assetutil --info "<App>.app/Contents/Resources/Assets.car" \
  | python3 -c 'import json,sys; [print(e.get("Appearance","(none)"), e.get("RenditionName")) \
      for e in json.load(sys.stdin) if str(e.get("Name","")).startswith("AppIcon")]'
# → every line prints "(none)"; no luminosity:dark rendition exists.
```

iOS 18 added dark/tinted app icons; **macOS never did** for the Dock/Finder tile. So "Appearances:
Any, Dark" on a *macOS* app-icon set is a no-op (it works for ordinary in-app **image** assets, just
not the app icon). Two different slots are in play:

- **Bundle icon** (`Assets.car` / `.icns`) — shown in **Finder and when the app isn't running**. One
  image, period. Pick the brand default (Conjoyn ships **dark**).
- **Running-app Dock tile** (`NSApplication.shared.applicationIconImage`) — settable at **runtime**,
  and the *only* thing you can vary by appearance.

**Fix — drive the running tile yourself from a persisted preference, tracking effective appearance.**
Give the user a `Match System / Light / Dark` control (independent of the UI-theme picker), bundle
**both** icons as loadable `.icns` resources, and set `applicationIconImage` at launch + on change +
whenever the effective appearance flips.

```sh
# Build the two runtime icns from the delivered iconsets (NOT the appiconset):
iconutil -c icns Conjoyn.iconset       -o Resources/ConjoynIcon-Dark.icns
iconutil -c icns Conjoyn-Light.iconset -o Resources/ConjoynIcon-Light.icns
# Drop them in the source tree so the build copies them to Contents/Resources
# (xcodegen: a recursive `sources: - path: App` picks up *.icns as resources — re-run xcodegen).
```

```swift
enum IconPreference: String, CaseIterable, Identifiable {
    case auto, light, dark
    var id: String { rawValue }
    var title: String { switch self { case .auto: "Match System"; case .light: "Light"; case .dark: "Dark" } }
}

@MainActor
final class AppIconController: ObservableObject {
    private var preference: IconPreference = .auto
    private var appearanceObserver: NSKeyValueObservation?
    private lazy var darkIcon  = Self.load("ConjoynIcon-Dark")
    private lazy var lightIcon = Self.load("ConjoynIcon-Light")

    func start(with preference: IconPreference) {           // call once at launch (.task)
        self.preference = preference
        // KVO fires on the main thread when the resolved appearance changes — a System dark-mode
        // flip OR the theme picker mutating NSApp.appearance (see #113). assumeIsolated bridges the
        // non-isolated KVO closure into this @MainActor type under Swift 6 strict concurrency.
        appearanceObserver = NSApp.observe(\.effectiveAppearance) { [weak self] _, _ in
            MainActor.assumeIsolated { self?.apply() }
        }
        apply()
    }
    func update(_ preference: IconPreference) { self.preference = preference; apply() }   // .onChange

    private func apply() {
        let isDark = NSApp.effectiveAppearance.bestMatch(from: [.aqua, .darkAqua]) == .darkAqua
        let icon: NSImage? = switch preference {
            case .auto:  isDark ? darkIcon : lightIcon
            case .light: lightIcon
            case .dark:  darkIcon
        }
        if let icon { NSApp.applicationIconImage = icon }   // nil would reset to the bundle icon
    }
    private static func load(_ name: String) -> NSImage? {
        Bundle.main.url(forResource: name, withExtension: "icns").flatMap(NSImage.init(contentsOf:))
    }
}
```

```swift
// App scene: persist the choice, start once, apply on change.
@AppStorage("iconPreference") private var iconPreference: IconPreference = .auto
@StateObject private var iconController = AppIconController()

ContentView()
    .task { iconController.start(with: iconPreference) }                 // initial apply + KVO
    .onChange(of: iconPreference) { _, p in iconController.update(p) }   // menu picks

// Menu — a second inline-radio section under a divider (SwiftUI Commands):
CommandMenu("Appearance") {
    Picker(selection: $appearance)     { … } label: { EmptyView() }.pickerStyle(.inline)  // UI theme (#113)
    Divider()
    Picker(selection: $iconPreference) { ForEach(IconPreference.allCases){ Text($0.title).tag($0) } }
        label: { Text("App Icon") }.pickerStyle(.inline)                 // labelled 2nd section
}
```

**Gotchas / notes.**
- **`.auto` should track `NSApp.effectiveAppearance`, not the raw System setting** — then one KVO
  observer covers *both* a System dark-mode flip and an in-app theme switch (#113 drives
  `effectiveAppearance` via `NSApp.appearance`), and the Dock tile always matches what the user sees.
- **Finder / not-running Dock can't be themed** — they show the static bundle `.icns`. That's an
  inherent macOS limit, not a bug; even apps that swap their running tile can't vary the Finder icon.
  Set the bundle default to the brand-primary appearance.
- **Bundle the two icons as `.icns`, not loose PNGs** — `.icns` is multi-resolution so the Dock picks
  the crisp size; an `NSImage` from a single 1024 PNG scales softly at small Dock sizes.
- **Don't keep the dark PNGs in the appiconset** — they only re-trigger the "unassigned children"
  warning. The app-icon set is one appearance; the runtime variants live as separate resources.
- **`@AppStorage` enum** persists fine when `RawValue == String`.
- **Verify:** App Icon → Light flips the running tile; Match System + theme=Match System, then flip
  macOS appearance in System Settings → the tile follows.

**Source.** Conjoyn `01_Project/Conjoyn/AppIconController.swift` + `ConjoynApp.swift`
(`IconPreference`, `@AppStorage` + `.task`/`.onChange`, `AppearanceCommands` divider section), commit
`945ff4d`. Pairs with **#113** (the UI-theme picker via `NSApp.appearance` — same menu, drives the
`effectiveAppearance` this observes), **#76** (the Core-Graphics app-icon generator — the *bundle*
icon source of truth), #00 (App Shell Standard / `Theme`), #06 (scene/lifecycle wiring).
