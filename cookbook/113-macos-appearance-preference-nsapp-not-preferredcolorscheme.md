# 113 — macOS appearance picker: drive `NSApplication.shared.appearance`, NOT `.preferredColorScheme`

**Problem.** A Light / Dark / **Match System** appearance menu (persisted via `@AppStorage`) wired the
obvious SwiftUI way — `.preferredColorScheme(pref.colorScheme)`, where Match System returns `nil`.
Symptom: **Dark → Match System leaves the UI dark** (when the OS is Light it should go light). Dark →
**Light** works; Light → Dark works; only the revert-to-system case is dead.

**Root cause — `.preferredColorScheme(nil)` does not clear a previously-forced `NSWindow.appearance`.**
On macOS, `.preferredColorScheme(.dark)` writes a **concrete** `NSWindow.appearance = darkAqua`. Passing
`nil` afterwards is a no-op against that already-pinned window appearance — SwiftUI never lifts it back to
"inherit from system". So the window stays `darkAqua`. Dark → Light only *looks* fixed because `.light`
writes a concrete `aqua` that overrides the prior concrete value; the **`nil` reset is the broken path**,
and Match System is the only preference that uses it.

This bites **twice as hard if your `Theme` is appearance-adaptive** (see #00): adaptive tokens built with
`NSColor(name: nil) { appearance in … }` resolve against the **window's live `NSAppearance`**. While that
window is stuck on `darkAqua`, every token keeps returning its dark value — so even a correct
`@Environment(\.colorScheme)` wouldn't save you; the *colors themselves* are reading a stale window
appearance.

**Fix — move the control up one level to `NSApplication.shared.appearance`, where `nil` DOES revert.**
App-level appearance with `nil` means "follow the system"; every window/view inherits via
`effectiveAppearance` (which is exactly what the `Theme` `NSColor(name:)` providers resolve against), and
SwiftUI's `@Environment(\.colorScheme)` still tracks correctly because it's derived from the effective
appearance. Apply it from `.onChange(of:initial:)` so the **persisted** preference also lands at launch.

```swift
// AppearancePreference.swift / wherever the enum lives — map to AppKit, not ColorScheme.
enum AppearancePreference: String, CaseIterable, Identifiable {
    case auto, light, dark
    var id: String { rawValue }
    var title: String {
        switch self {
        case .auto:  return "Match System"
        case .light: return "Light"
        case .dark:  return "Dark"
        }
    }

    /// The AppKit appearance to pin app-wide via `NSApplication.shared.appearance`; `nil` follows
    /// the system. Driven through `NSApp.appearance` rather than SwiftUI's `.preferredColorScheme`
    /// because the latter's `nil` case does not clear a previously-forced window appearance on macOS.
    var nsAppearance: NSAppearance? {
        switch self {
        case .auto:  return nil                          // <-- the load-bearing line
        case .light: return NSAppearance(named: .aqua)
        case .dark:  return NSAppearance(named: .darkAqua)
        }
    }
}
```

```swift
// App scene — apply on every change AND once at launch (initial: true), macOS 14+.
@AppStorage("appearancePreference") private var appearance: AppearancePreference = .dark

var body: some Scene {
    Window("MyApp", id: "main") {
        ContentView()
            .onChange(of: appearance, initial: true) { _, pref in
                NSApplication.shared.appearance = pref.nsAppearance
            }
    }
}
```

**Why this is the right altitude.** `.preferredColorScheme` pushes onto the **window's**
`NSWindow.appearance`; once a concrete value is written there, SwiftUI's `nil` can't unstick it. Setting
**`NSApp.appearance`** owns the choice at the application level, so a single `nil` makes the whole app
system-driven again and all windows fall back through `effectiveAppearance`. Don't try to keep
`.preferredColorScheme` *and* set `NSApp.appearance` — two owners of the same property fight; pick the app
level and remove the modifier.

**Gotchas / notes.**
- **`initial: true` is not optional.** Without it, the persisted preference (e.g. Light) doesn't apply
  until the user re-touches the menu; the app launches in whatever the system is. It fires the same
  closure on appear and on every change — one code path for launch + toggle.
- **Menu radio binding still works unchanged** — an inline `Picker(selection: $appearance)` /
  `CommandMenu` keeps the checkmark in sync off the same `@AppStorage`; only the *application* side moved
  from `.preferredColorScheme` to `NSApp.appearance`.
- **Don't reach for `NSWindow.appearance = nil` per-window** unless you have a specific window to fix —
  `NSApp.appearance` covers panels, sheets, and any future windows for free.
- **Verify the actual broken path:** set the **system** to Light, then in-app Dark → Match System and
  confirm it flips to light (not just that Light/Dark toggle). Then relaunch on Match System to confirm
  `initial: true` re-applies.

**Source.** Conjoyn `01_Project/Conjoyn/ConjoynApp.swift` (`AppearancePreference.nsAppearance` +
`.onChange(of: appearance, initial: true)`), fix commit `feb3c43`. Pairs with **#00** (App Shell Standard —
the adaptive `Theme` whose `NSColor(name:)` tokens resolve against the live `NSAppearance`, which is *why*
a stuck window appearance also freezes the colors), #06 (app lifecycle / scene wiring), #62 (the web
analogue — `prefers-color-scheme` token theming).
