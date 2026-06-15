# Cursor-anchored non-activating `NSPanel` HUD with permission-free dismiss

**Source:** `1-macOS/QuickStatsPanel/` — `Panel/PanelWindowController.swift` + `AppDelegate.swift` (2026-06-04, v0.1.0). Lineage: MousePlus `RingWindowController`.

You want a transient overlay — a stats strip, a quick action bar, a HUD — that **appears over whatever app is focused without stealing focus**, anchors near the cursor (or a fixed spot), stays fully on-screen, and dismisses when the user clicks away. Three pieces make it behave:

**1. A borderless, non-activating panel.** `.nonactivatingPanel` + `orderFrontRegardless()` shows it without making your app active. `level = .floating` keeps it above normal windows; `canJoinAllSpaces` + `fullScreenAuxiliary` make it appear over full-screen apps too. Draw the rounded background in SwiftUI (panel `backgroundColor = .clear`) so corner radius is yours to control.

```swift
private func makePanel(size: NSSize) -> NSPanel {
    let panel = NSPanel(contentRect: NSRect(origin: .zero, size: size),
                        styleMask: [.borderless, .nonactivatingPanel],
                        backing: .buffered, defer: false)
    panel.isOpaque = false
    panel.backgroundColor = .clear          // SwiftUI draws the rounded shape
    panel.level = .floating
    panel.collectionBehavior = [.canJoinAllSpaces, .fullScreenAuxiliary]
    panel.isMovable = false
    panel.hasShadow = true
    panel.isFloatingPanel = true
    panel.hidesOnDeactivate = false
    panel.becomesKeyOnlyIfNeeded = true     // only steal key focus if a control needs it
    panel.acceptsMouseMovedEvents = true    // so onContinuousHover / tracking works later
    return panel
}
```

**2. First click isn't swallowed.** A non-activating panel eats the *first* click just to raise itself, so SwiftUI never sees it. Subclass the hosting view to accept first mouse:

```swift
private final class FirstMouseHostingView<Content: View>: NSHostingView<Content> {
    override func acceptsFirstMouse(for event: NSEvent?) -> Bool { true }
}
```

**3. Cursor anchor, clamped on-screen.** `NSEvent.mouseLocation` is global, bottom-left origin. Center the panel on the cursor (here, just below it) then clamp into the cursor's screen `visibleFrame` — and pin to the min edge if the panel is larger than the screen in a dimension (avoids an inverted clamp range).

```swift
enum Anchor { case cursor; case fixed(NSPoint) }

private func origin(forSize size: NSSize, anchor: Anchor) -> NSPoint {
    switch anchor {
    case .fixed(let p): return clamp(origin: p, size: size, on: screen(containing: p))
    case .cursor:
        let c = NSEvent.mouseLocation
        let raw = NSPoint(x: c.x - size.width / 2, y: c.y - size.height - 18 /*gap*/)
        return clamp(origin: raw, size: size, on: screen(containing: c))
    }
}
private func clamp(origin: NSPoint, size: NSSize, on screen: NSScreen?) -> NSPoint {
    guard let v = screen?.visibleFrame else { return origin }
    var o = origin
    o.x = v.width  >= size.width  ? min(max(o.x, v.minX), v.maxX - size.width)  : v.minX
    o.y = v.height >= size.height ? min(max(o.y, v.minY), v.maxY - size.height) : v.minY
    return o
}
private func screen(containing p: NSPoint) -> NSScreen? {
    NSScreen.screens.first { $0.frame.contains(p) } ?? NSScreen.main
}
```

**4. Permission-free dismiss.** Re-pressing the summon hotkey toggles it. For *click-away*, use a global **mouse** monitor — unlike a keyboard monitor, `NSEvent.addGlobalMonitorForEvents(.leftMouseDown)` needs **no permission**, and a global monitor only fires for clicks in *other* apps (i.e. outside your panel), which is exactly the click-away case:

```swift
clickAwayMonitor = NSEvent.addGlobalMonitorForEvents(
    matching: [.leftMouseDown, .rightMouseDown]
) { [weak self] _ in
    Task { @MainActor in
        guard let self, self.panel.isVisible else { return }
        self.panel.hide()
    }
}
// removeMonitor(_:) on teardown.
```

**Gotchas**
- **Shadow: AppKit's `hasShadow` vs a SwiftUI `.shadow` — and the clipping trap.** `panel.hasShadow = true` is simplest, but on a `backgroundColor = .clear` panel the system shadow can trace the panel's *rectangular* frame (a faint 1px box around your rounded content) instead of the rounded shape. The alternative — `hasShadow = false` and draw the shadow in SwiftUI with `.shadow(...)` — gives you a rounded shadow but introduces a clipping trap: **`.shadow(radius:)` is the Gaussian *blur radius*, not the shadow's reach. The visible tail spreads ~2.5–3× that value**, and the `NSPanel` frame (sized to `hostingView.fittingSize`, which *excludes* shadow spread) hard-clips it into a sharp straight line at the panel edge. Fix: wrap the shadowed view in a transparent margin large enough to contain the tail — `padding ≥ radius * 3 + |yOffset|` — and **derive that margin from the shadow params** so they can't drift out of sync:
  ```swift
  private static let shadowRadius:  CGFloat = 10
  private static let shadowYOffset: CGFloat = 4
  // visible blur tail ≈ 2.5–3× radius; offset adds to the bottom edge
  private static var shadowMargin: CGFloat { shadowRadius * 3 + abs(shadowYOffset) }
  // ...
  .shadow(color: .black.opacity(0.28), radius: Self.shadowRadius, x: 0, y: Self.shadowYOffset)
  .padding(Self.shadowMargin)   // transparent ring so the tail fades *inside* the frame
  ```
  Keep the margin tight, not arbitrarily large: it doubles as a **click-away dead zone** — clicks anywhere in the panel frame (including this transparent ring) don't reach the global mouse monitor, so they won't dismiss the HUD. (Source: DeskFlow `HUDView.swift`, 2026-06-06.)
- **Esc-to-dismiss needs care (but is still permission-free).** The panel is non-activating so it isn't key — `keyDown` / `.onKeyPress` never reach it, and the obvious global *keyboard* monitor needs Input-Monitoring permission. The permission-free fix is **#72**: register bare Escape as a *scoped* Carbon hotkey only while the panel is visible. (Hotkey-toggle + click-away dismiss are free regardless.)
- **`hide()` should drop the panel + hosting view** (`orderOut`, then nil them) so the next summon rebuilds with fresh content and current geometry.
- **`orderFrontRegardless()` not `makeKeyAndOrderFront`** — the latter activates your app and defeats the whole non-activating point.
- This is the HUD-overlay shell; it is deliberately **not** the App Shell Standard (HSplitView). Don't run shell-check against an app built this way.
- **Auto-dismiss + hover-pause needs a real-cursor failsafe, or the HUD can stick forever.** The usual design pauses the dismiss timer on `onHoverChange(true)` and resumes on `onHoverChange(false)`. But SwiftUI `.onHover` rides **mouse-moved tracking**, and a non-activating panel can *miss the exit event*: the cursor leaves via `CGWarpMouseCursorPosition` (no moved event), a fast flick, or the panel appears **under a stationary cursor** (enter fires, exit never does). The dismiss task stays cancelled and the HUD is stranded on screen — with no max-lifetime guard, the pause is unbounded. Add a watchdog that runs *only while paused* and polls the **real** cursor against the panel frame; resume dismissal once it's genuinely outside (a small outset gives hysteresis so an active hover-to-drag is never yanked):
  ```swift
  private func startHoverWatchdog() {
      hoverWatchdog?.cancel()
      hoverWatchdog = Task { [weak self] in            // @MainActor-inherited (class is @MainActor)
          while !Task.isCancelled {
              try? await Task.sleep(for: .milliseconds(500))
              guard let self, let panel = self.panel, panel.isVisible else { return }
              if !panel.frame.insetBy(dx: -2, dy: -2).contains(NSEvent.mouseLocation) {
                  self.startDismiss()                  // exit was dropped → resume countdown + cancel watchdog
                  return
              }
          }
      }
  }
  ```
  `NSEvent.mouseLocation` and `panel.frame` are both global, bottom-left screen coords, so the containment check is correct **across displays** (no flipping). Arm it from `pauseDismiss()`, cancel it from `startDismiss()`. (Source: QuickScreenShot `CaptureHUDController.swift`, 2026-06-14.)

**Spotlight-style growing panel (top-anchored dynamic height).** A search/command palette should open as a *bare search bar* and grow downward as results arrive (Spotlight/Alfred/Raycast), not be a fixed box with empty space. Two rules make it clean:

- **Let the SwiftUI content report a deterministic height; the controller resizes the window.** Don't measure SwiftUI's `fittingSize` and feed it back — that risks a layout feedback loop. Instead pin fixed metrics (search-bar height, row height, max visible rows → then scroll) so the view can *compute* its total height and hand it to the controller via a closure:
  ```swift
  // View: fixed metrics → exact height, no measurement
  private var contentHeight: CGFloat {
      let n = min(results.count, maxVisibleRows)
      let list = n == 0 ? 0 : CGFloat(n) * rowH + CGFloat(n - 1) * rowGap + 2 * listPad
      return searchBarH + (list > 0 ? dividerH + list : 0)
  }
  // report on appear + whenever results change (results recompute on every keystroke)
  .onAppear { onHeightChange(contentHeight) }
  .onChange(of: results) { _, _ in onHeightChange(contentHeight) }
  ```
- **Anchor the TOP edge, not the center — macOS origin is bottom-left, so grow by *dropping* `origin.y`.** Capture the anchor once per summon (so it doesn't drift if the cursor moves while typing); recompute the frame for each reported height, keeping the top pinned:
  ```swift
  func summon() {
      anchorVF   = mouseScreen().visibleFrame
      anchorTopY = anchorVF.maxY - anchorVF.height * 0.20   // bar sits ~20% down (Spotlight spot)
      panel.setFrame(frame(forHeight: compactHeight), display: false)   // open as bare bar
      panel.makeKeyAndOrderFront(nil); installClickAwayMonitor()
  }
  func setContentHeight(_ h: CGFloat) {                      // called by the view via the owner
      guard panel.isVisible else { return }                 // offscreen reset → next summon re-bases
      panel.setFrame(frame(forHeight: h), display: true)
  }
  private func frame(forHeight h0: CGFloat) -> NSRect {
      let vf = anchorVF, h = min(h0, vf.height)
      var y = anchorTopY - h                                 // top fixed, list unfurls downward
      if y < vf.minY { y = vf.minY }; if y + h > vf.maxY { y = vf.maxY - h }
      let x = min(max(vf.midX - panelWidth/2, vf.minX), vf.maxX - panelWidth)
      return NSRect(x: x, y: y, width: panelWidth, height: h)
  }
  ```
  Set the hosting view's `autoresizingMask = [.width, .height]` so the SwiftUI content fills each new size. Open at `compactHeight` (the query resets to empty on dismiss, so every summon starts as a bare bar). Pairs with the empty-query = no-results model in the search engine. (Source: LaunchAway `LauncherView.swift` + `LauncherPanelController.swift`, 2026-06-15.)

**Best for:** a hotkey-summoned overlay (stats HUD, command palette, quick switcher, search launcher) in an `LSUIElement` app with no menu bar. Pairs with #64 (Carbon global hotkey), #57 (⌘W override), #60 (closure-bridged AppKit), #71 (self-managed Settings window + ⌘, routing).
