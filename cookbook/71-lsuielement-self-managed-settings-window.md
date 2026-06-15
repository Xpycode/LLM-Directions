# Self-managed settings `NSWindow` for `LSUIElement` agent apps (`showSettingsWindow:` no-ops)

**Source:** `1-macOS/QuickStatsPanel/` — `Panel/SettingsWindowController.swift` + `AppDelegate.swift` + `QuickStatsPanelApp.swift` (2026-06-04, v0.1.0).

You have an agent app (`LSUIElement = YES`: no Dock icon, no menu bar) and want a real Settings window — opened from an in-app affordance like a gear button. The obvious SwiftUI path is a `Settings { … }` scene plus `NSApp.sendAction(Selector(("showSettingsWindow:")), …)`. **In an `LSUIElement` app this silently fails:** with no regular activation, the responder chain often can't reach the `Settings` scene's window manager, so the action no-ops. The telltale symptom: clicking the button **shifts focus** (because your `NSApp.activate` ran) but **no window appears**.

**Fix: don't use the `Settings` scene at all. Manage your own `NSWindow`.** You already drive AppKit windows in an agent app (the panel/overlay); manage this one the same way. Build it once, host the SwiftUI view in an `NSHostingController`, then `activate` + `makeKeyAndOrderFront`.

```swift
@MainActor
final class SettingsWindowController {
    private var window: NSWindow?

    func show() {
        if window == nil {
            let hosting = NSHostingController(rootView: SettingsView())
            let window = NSWindow(contentViewController: hosting)   // sizes to the view's fittingSize
            window.title = "MyApp Settings"
            window.styleMask = [.titled, .closable]
            window.isReleasedWhenClosed = false   // reuse across opens; don't dealloc on close
            window.center()
            self.window = window
        }
        // An accessory app must activate before a window can come forward AND become key.
        NSApp.activate(ignoringOtherApps: true)
        window?.makeKeyAndOrderFront(nil)
    }
}
```

Wire the in-app button to it, and reduce the SwiftUI scene to an empty placeholder so there's a single settings path:

```swift
// AppDelegate
private let settingsWindow = SettingsWindowController()
private func openSettings() { settingsWindow.show() }   // gear button calls this

// App entry — Settings scene is now just satisfying `some Scene`
var body: some Scene {
    Settings { EmptyView() }     // real settings live in SettingsWindowController
}
```

**Why `makeKeyAndOrderFront` here, the opposite of the HUD panel (#65).** The overlay panel deliberately uses `orderFrontRegardless()` to *avoid* stealing focus. A settings window is the opposite: it **must become key**, both so the user can type into fields and — critically — so an in-app **hotkey recorder** works. A recorder installs `NSEvent.addLocalMonitorForEvents(.keyDown)` (returning `nil` to swallow the keystroke), which only fires while one of your windows is key. The non-activating panel can never be key, so settings (and any key-capture UI) belong in a self-managed window that can. (Same source project: `Views/HotKeyRecorderView.swift`.)

`SettingsView` itself stays declarative by editing a shared `@Observable` settings singleton (`AppSettings.shared`, `UserDefaults`-backed): passive settings (anchor, size) are read where used, while settings needing an imperative reaction (refresh interval, hotkey binding) push side-effects through property `didSet` hooks the (non-view) `AppDelegate` wires up. That split keeps the view free of side-effect logic. (Same source project: `Model/AppSettings.swift`.)

**Gotchas**
- **`isReleasedWhenClosed = false`** — without it, an `NSWindow(contentViewController:)` is released when the user clicks the close box, and the next `show()` touches a freed object (crash) or rebuilds unexpectedly. Keep it and reuse the one instance.
- **`activate(ignoringOtherApps: true)` is required, not optional** — an accessory app is `.accessory` activation policy; the window won't come to the front or become key until the app activates.
- **If the window opens *behind* the frontmost app** despite activating, the app likely needs a momentary `NSApp.setActivationPolicy(.regular)` around the show (and `.accessory` again on close). Most apps don't need this; reach for it only if fronting genuinely fails.
- **Don't keep a `Settings { SettingsView() }` scene *and* a self-managed window** — you'd get two live `SettingsView` instances editing the same state. Pick the self-managed window; leave the scene `EmptyView()`.
- **Even `Settings { EmptyView() }` isn't inert — it hijacks ⌘,.** The SwiftUI `Settings` scene auto-installs a "Settings…" menu item bound to ⌘,. `NSApp.sendEvent` matches that **menu key equivalent against the main menu *before*** the keystroke reaches your key window's responder chain — so ⌘, opens the blank `EmptyView` scene as a stray light-mode window *and* shadows any in-app `.onKeyPress(⌘,)` handler you wrote to open the real window. Symptom: "⌘, does nothing useful and a blank window appears." Fix is one idiomatic line — **remove the command** so ⌘, falls through to your handler:
  ```swift
  var body: some Scene {
      Settings { EmptyView() }
      .commands {
          CommandGroup(replacing: .appSettings) { }   // drop the auto ⌘, "Settings…" item
      }
  }
  ```
  Then ⌘, reaches the panel/window's own `.onKeyPress(keys: [","])` handler (guard on `.command`) → `SettingsWindowController.show()`. Prefer this over runtime menu surgery (locating the item and clearing its `keyEquivalent`): no private `showSettingsWindow:` selector, no dependence on *when* SwiftUI builds the menu. (Source: LaunchAway `LaunchAwayApp.swift`, 2026-06-15.)
- `NSWindow(contentViewController:)` sizes to the hosting view's `fittingSize`, so give `SettingsView` a definite width (`.frame(width: 380)`) and let height fit (`.fixedSize(horizontal: false, vertical: true)`).

**Best for:** any `LSUIElement` menu-bar / agent / HUD app that needs a Settings (or About, or recorder) window opened from in-app UI. Pairs with #65 (non-activating HUD panel), #64 (Carbon global hotkey), #60 (closure-bridged AppKit).
