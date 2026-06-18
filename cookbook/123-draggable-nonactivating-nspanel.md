# Make a non-activating `NSPanel` overlay draggable (Raycast/Alfred-style), position remembered for the session

**Source:** LaunchAway — `Panel/LauncherPanel.swift` + `Panel/LauncherPanelController.swift` (2026-06-18). Extends **#65** (the cursor-anchored non-activating `NSPanel` HUD + its top-anchored growing-panel section — read that first; this only adds the drag).

You have a #65-style summoned overlay (command palette / launcher / HUD) and the user wants to **drag it to a preferred spot**, the way Raycast and Alfred let you reposition their bar. Four pieces, and three of them exist only to stop the drag from fighting the panel's own repositioning logic.

**1. Enable background dragging.** One switch on the panel:

```swift
// LauncherPanel.configure()
isMovableByWindowBackground = true   // was false
```

AppKit starts a window drag when the mouse-down lands on a **non-control background** region. SwiftUI's `TextField` and the tappable result rows consume their own clicks, so only the empty chrome around them initiates a drag — exactly Alfred's feel (drag by the bar, type/click as normal). The non-activating panel is still **key** while visible, so it receives the drag events without `NSApp.activate` — focus stays with the app behind it.

**2. Tell a user drag apart from your own `setFrame`.** A growing panel (#65) calls `setFrame` on every keystroke to resize. `setFrame` **also** fires `windowDidMove` — so if you naively save every move, your own resize re-captures as a "drag", and you get a `resize → "move" → re-anchor → resize` feedback loop. The fix: route **all** programmatic placement through one helper that records the origin first, then in the delegate ignore moves that match it.

```swift
@MainActor
final class LauncherPanelController: NSObject, NSWindowDelegate {   // NSObject so it can be a delegate
    private var lastPlacedOrigin: NSPoint = .zero

    // every programmatic frame change goes through here
    private func place(_ rect: NSRect, display: Bool) {
        lastPlacedOrigin = rect.origin          // record BEFORE setFrame…
        panel.setFrame(rect, display: display)  // …so the guard holds whether windowDidMove is sync or async
    }

    func windowDidMove(_ notification: Notification) {
        let origin = panel.frame.origin
        guard abs(origin.x - lastPlacedOrigin.x) > 0.5
           || abs(origin.y - lastPlacedOrigin.y) > 0.5 else { return }   // our own move → ignore

        let topLeft = NSPoint(x: panel.frame.minX, y: panel.frame.maxY)  // user drag
        sessionDraggedTopLeft = topLeft
        anchorTopLeft         = topLeft
        if let screen = NSScreen.screens.first(where: { $0.visibleFrame.contains(topLeft) }) {
            anchorVF = screen.visibleFrame       // re-anchor growth to wherever it now lives
        }
        lastPlacedOrigin = origin                // so the next programmatic resize from here is ignored
    }
}
```

Set the panel's delegate once in `init` (after `super.init()`): `panel.delegate = self`.

**3. Promote the growth anchor from a top-Y scalar to a top-LEFT point.** This is the non-obvious one. #65's growing panel stores only `anchorTopY` and re-derives x by **centering** in `frame(forHeight:)`. That's invisible until you add dragging: the moment results change (the next keystroke), the centering snaps the panel back to the horizontal middle, undoing the drag. Store the full corner instead and read both axes from it:

```swift
private var anchorTopLeft: NSPoint = .zero   // x = left edge, y = top edge (was: anchorTopY scalar)

private func frame(forHeight height: CGFloat) -> NSRect {
    let vf = anchorVF == .zero ? mouseScreen().visibleFrame : anchorVF
    let width = Self.panelWidth
    let h = min(height, vf.height)

    var originY = anchorTopLeft.y - h                 // top edge pinned; list unfurls downward
    if originY < vf.minY     { originY = vf.minY }
    if originY + h > vf.maxY { originY = vf.maxY - h }

    var originX = anchorTopLeft.x                      // centered by default, OR wherever the user dragged it
    originX = width <= vf.width ? min(max(originX, vf.minX), vf.maxX - width) : vf.minX

    return NSRect(x: originX, y: originY, width: width, height: h)
}
```

**4. Remember the drop spot for the session.** Keep an in-memory `sessionDraggedTopLeft: NSPoint?` (set in `windowDidMove`). On summon, reuse it if present, else compute the default; route the open through `place(...)`:

```swift
func summon() {
    let mouse = mouseScreen()
    if let dragged = sessionDraggedTopLeft {
        let screen = NSScreen.screens.first { $0.visibleFrame.contains(dragged) } ?? mouse
        anchorVF = screen.visibleFrame                 // clamp growth to that corner's screen
        anchorTopLeft = dragged
    } else {
        anchorVF = mouse.visibleFrame
        anchorTopLeft = NSPoint(x: anchorVF.midX - Self.panelWidth / 2,
                                y: anchorVF.maxY - anchorVF.height * 0.20)   // default: centered, ~20% down
    }
    place(frame(forHeight: Self.compactHeight), display: false)
    panel.makeKeyAndOrderFront(nil)
    installClickAwayMonitor()
}
```

Because the controller instance lives for the whole app session and this is a plain stored property (no `UserDefaults`), the position **resets to default on relaunch** for free — "remember until quit."

**Gotchas**
- **The feedback loop is the whole reason for `lastPlacedOrigin`.** Skip it and the panel jitters / drifts: each resize looks like a drag, re-anchors, resizes again. Update `lastPlacedOrigin` in **both** places — in `place()` before every `setFrame`, and at the end of `windowDidMove` after capturing a real drag — so the next programmatic move from the dragged spot is recognized as yours.
- **Order matters in `place()`:** set `lastPlacedOrigin` *before* `setFrame`. `windowDidMove` for your own move may be delivered synchronously (inside `setFrame`) or on a later turn; recording first makes the guard correct either way.
- **Don't let `frame(forHeight:)` re-center x.** If it still computes `originX = vf.midX - width/2`, a dragged panel jumps horizontally back to center on the next keystroke. The `anchorTopLeft.x` read is the fix — easy to miss because the bug only shows after you type, not on the drag itself.
- **`NSWindowDelegate` needs `NSObject`.** A bare `@MainActor final class` can't be a window delegate — inherit `NSObject` and call `super.init()` in your generic `init`. On the macOS 26 SDK `NSWindowDelegate` is MainActor-isolated, so a `@MainActor` class satisfies `windowDidMove` with **no** concurrency friction (no `nonisolated`/`Task` hop needed).
- **Phantom SourceKit cascade after the `NSObject` conversion.** Mid-edit, live diagnostics screamed *"Cannot find type 'LauncherPanel'"* and *"'panel' is a method"* across the file — all bogus, gone once the type fully resolved. `xcodebuild` was clean. Build is authoritative; don't chase SourceKit cascades during a structural edit (same lesson as #47).
- **Persistence is a real product choice — pick deliberately.** *Session-only* (in-memory, here) matches "put it where I want for now" and sidesteps the multi-monitor stale-position edge cases and the need for any settings UI. *Across-restarts* (persist the top-left to `UserDefaults`, clamp to a currently-visible screen on summon, fall back to default if the saved spot is off all screens) is the fuller Raycast/Alfred behavior but costs that clamp logic. *Only-this-summon* (don't store at all) is simplest but isn't the feel users mean when they say "like Raycast." Ask before building.
- **Multi-monitor:** the dragged corner is absolute screen coords. On re-summon, find the screen whose `visibleFrame` contains it and clamp growth to that — so the panel grows down *its* screen, not the mouse screen. If the corner is off every screen (display unplugged), fall back to the mouse screen.

**Best for:** making a #65-style hotkey overlay — launcher, command palette, quick switcher, stats HUD — repositionable like Raycast/Alfred in an `LSUIElement` app. Pairs with **#65** (the panel shell + growing-panel section this directly extends), #64 (Carbon global hotkey), #72 (scoped Esc-dismiss on a non-key panel), #71 (self-managed Settings window), #70 (data-driven result strip).
