# 162 — LSUIElement Dock app that surfaces its window without stealing focus on launch

**Tags:** LSUIElement, NSApp.setActivationPolicy, NSApp.activate, orderFrontRegardless, makeKeyAndOrderFront, accessory, regular, Dock icon, applicationDidFinishLaunching, launch focus steal, login item, WindowGroup
**Extracted from:** QuickScreenShot (2026-07-13)

## Problem

You want a normal **Dock app** (Dock icon + a real window), but you don't want it to
**yank itself to the front** when it launches — e.g. as a login item, or any time it
cold-launches while the user is working in another app. The window should appear; focus
should stay where the user left it.

## Why it's hard / the gotcha

A normal (non-`LSUIElement`) app is **auto-activated by LaunchServices** on launch — the OS
fronts it for you, so you fight the platform to *not* take focus. The clean fix is to invert
the default:

- Mark the app **`LSUIElement: true`** (Info.plist) so it is **born `.accessory`**.
  LaunchServices then does **not** auto-front it.
- In `applicationDidFinishLaunching`, flip to `.regular` for the Dock icon — **but do not call
  `NSApp.activate()`**. With nothing left to front the app, it stays in the background.
- Surface the window with **`orderFrontRegardless()`** (visible, non-key), **not**
  `makeKeyAndOrderFront()` (which activates). SwiftUI's `WindowGroup` also auto-opens the
  launch window, so it appears regardless; the router just guarantees visibility without focus.

Net: window visible, app not key, focus stays with the user's prior app — even on a *manual*
double-click. Keep **user-initiated** opens (Dock-icon click, a menu-bar "Open" item) on the
activating path so those still come forward.

```swift
// Info.plist / project.yml:  LSUIElement: true   → app is born .accessory

// AppDelegate.applicationDidFinishLaunching(_:)
if AppSettings.shared.backgroundModeEnabled {
    hideInitialWindowForBackgroundLaunch()          // menu-bar-only: stay windowless
} else {
    // Normal Dock app: Dock icon, but DON'T steal focus. Because we're LSUIElement,
    // launch doesn't auto-front us, so simply omitting NSApp.activate() is enough.
    NSApp.setActivationPolicy(.regular)
    WindowRouter.shared.showMainWindow(activate: false)   // no activate() here
}

// WindowRouter.showMainWindow(activate:)  — one method, two intents
func showMainWindow(activate: Bool) {
    let wasAccessory = NSApp.activationPolicy() == .accessory
    if wasAccessory { NSApp.setActivationPolicy(.regular) }   // a visible window needs a Dock icon

    if let window = mainWindow {                              // reuse a live/hidden window
        if activate {
            NSApp.activate()
            window.makeKeyAndOrderFront(nil)                 // user asked for it → take focus
        } else {
            window.orderFrontRegardless()                    // auto-surface → visible, NOT key
        }
        return
    }
    // No window (SwiftUI released a truly-closed WindowGroup): recreate via the captured
    // openWindow(id:) action; only call NSApp.activate() when activate == true.
}
```

`activate: false` is the same non-stealing route used for the post-capture "show the result
window" surface; `activate: true` is reserved for explicit user opens.

## Verifying it (objective, no eyeballing)

Front a known app, launch yours, then read the frontmost process — **but only after the app
fully settles** (~2–3 s). A too-early read right after `killall` + relaunch catches a
launch/Space transition and returns a bogus frontmost + 0 windows.

```bash
osascript <<'EOF'
tell application "Finder" to activate
delay 0.6
do shell script "open -g '/path/to/YourApp.app'"   # -g ≈ login-item launch; plain open ≈ double-click
delay 2.5
tell application "System Events"
  set f to name of first application process whose frontmost is true
  set w to (count of windows of application process "YourApp")
end tell
return "frontmost=" & f & " windows=" & w   -- want: frontmost=Finder windows=1
EOF
```

## Gotchas

- **Only clean because it's `LSUIElement`.** A regular app can't get "Dock app that doesn't
  front on launch" this simply — LaunchServices re-fronts it.
- Clicking the window still makes it key (standard AppKit) — the app stays fully usable.
- After an `.accessory → .regular` flip, activation lands a beat late (Sonoma+); defer
  `activate()`/`makeKeyAndOrderFront` ~100 ms on the *activating* path only.
- Pairs with #71 (LSUIElement Settings no-op), #81/#123 (non-key HUD panels).
