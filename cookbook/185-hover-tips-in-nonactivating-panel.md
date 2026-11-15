# 185 — Hover tips in a non-activating `NSPanel` HUD

**Tags:** tooltip, toolTip, .help, NSPanel, nonactivatingPanel, NSTrackingArea, activeAlways, hover, HUD, inactive app

**Extracted from:** LLM-UsageStatus — `01_Project/Sources/Features/UsageStatus/Views/HoverTip.swift` (2026-11-15). Pairs with [#65](65-cursor-anchored-nspanel-hud.md) (the HUD panel itself).

## Problem

A HUD built as `[.borderless, .nonactivatingPanel]` + `orderFrontRegardless()` (see #65) keeps the
user's frontmost app active — so **your app is almost never active while the HUD is on screen**.
In the source app, native tool tips (`NSView.toolTip` and SwiftUI `.help`) did not appear while
the app was inactive. It looked intermittent: tips did appear while
the app happens to be active (e.g. its Settings window is open), which makes it easy to misdiagnose
as nested `.help` or a layout change.

**Diagnostic check:** open one of the app's normal windows so the app becomes active, then hover the HUD and compare.
Confirm the behavior on the target OS before replacing native tips.

Don't fix it by activating the app on hover — that steals focus from the user's app, which is
the whole point of a non-activating HUD.

## Fix

Track the pointer yourself with an `.activeAlways` tracking area and show your own tip window:

- **Overlay `NSView`** per tip area via `NSViewRepresentable`; `hitTest` returns `nil` so clicks,
  gestures and window dragging still reach the SwiftUI content (tracking areas don't depend on hit
  testing).
- **One controller** keeps the hovered views; the **smallest hovered area wins** (inner gauge beats its
  enclosing section — robust even when enter events arrive in either order).
- **Tip window:** `NSPanel` `[.borderless, .nonactivatingPanel]`, `ignoresMouseEvents = true`,
  `hidesOnDeactivate = false`, level above the HUD, `.canJoinAllSpaces/.transient`, shown with
  `orderFrontRegardless()` after ~0.6 s; clamp to the pointer's screen `visibleFrame`.
- Dismiss all tips from the HUD's `hide()`; a local `NSEvent` monitor (mouse down / scroll — local
  monitors still see events for the inactive app's panel) suppresses until the pointer leaves.
- Keep `.accessibilityHint(text)` so VoiceOver doesn't lose what `.help` provided.

```swift
extension View {
    func hoverTip(_ text: String) -> some View {
        overlay(HoverTipArea(text: text)).accessibilityHint(text)
    }
}

private struct HoverTipArea: NSViewRepresentable {
    let text: String
    func makeNSView(context: Context) -> HoverTipTrackingView { let v = HoverTipTrackingView(); v.text = text; return v }
    func updateNSView(_ v: HoverTipTrackingView, context: Context) { v.text = text }
}

final class HoverTipTrackingView: NSView {
    var text = "" { didSet { if text != oldValue { HoverTipController.shared.textChanged(self) } } }
    private var area: NSTrackingArea?

    override func hitTest(_ point: NSPoint) -> NSView? { nil }          // click-through
    override func updateTrackingAreas() {
        super.updateTrackingAreas()
        if let area { removeTrackingArea(area) }
        let a = NSTrackingArea(rect: .zero,
                               options: [.mouseEnteredAndExited, .mouseMoved, .activeAlways, .inVisibleRect],
                               owner: self, userInfo: nil)
        addTrackingArea(a); area = a
    }
    override func mouseEntered(with e: NSEvent) { HoverTipController.shared.enter(self) }
    override func mouseExited(with e: NSEvent) { HoverTipController.shared.exit(self) }
    // An area created/moved under a resting pointer gets no enter event; the next move fixes it.
    override func mouseMoved(with e: NSEvent) {
        bounds.contains(convert(e.locationInWindow, from: nil))
            ? HoverTipController.shared.enter(self) : HoverTipController.shared.exit(self)
    }
    override func viewDidMoveToWindow() { if window == nil { HoverTipController.shared.exit(self) } }
}

// Controller (sketch): hovered views → winner = smallest bounds area with non-empty text and a
// visible window → after a 600 ms Task.sleep, set the tip panel's NSHostingView rootView, size it to
// fittingSize, place below-right of NSEvent.mouseLocation, orderFrontRegardless(). Switching
// between tips skips the delay; while one tip is up, live text updates keep its position.
```

## Gotchas

- **`ImageRenderer` can't draw the AppKit overlay.** Gate it with an environment flag
  (`@Entry var hoverTipsEnabled = true`) and turn it off in snapshot/fixture renders.
- Don't use a SwiftUI `.overlay`/`.popover` for the tip itself in a panel that sizes to its content —
  it clips or resizes the HUD; a separate tip window doesn't.
- Normal (activating) windows like Settings can keep plain `.help`.
