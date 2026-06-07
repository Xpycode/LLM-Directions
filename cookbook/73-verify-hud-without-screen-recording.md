# Verifying a non-activating HUD / agent app without Screen-Recording permission

**Source:** `1-macOS/QuickStatsPanel/` — verification session for #72 (2026-06-05). Test scripts are ephemeral `swift /tmp/*.swift` one-shots; this captures the *technique*.

You need to verify a HUD panel / `LSUIElement` agent app actually shows, hides, and captures a global hotkey — but you're driving from a sandboxed shell (Claude Code, CI) where `screencapture` is blocked ("could not create image from display" = no Screen-Recording permission) and there's no visible UI to click. You can still get **deterministic, pixel-free** proof.

### Observe window visibility — no Screen-Recording needed

`CGWindowListCopyWindowInfo` returns owner + geometry without Screen-Recording permission (only window *names* are redacted). Filter by owner name:

```swift
func panelRect() -> CGRect? {
    let wins = (CGWindowListCopyWindowInfo(.optionOnScreenOnly, kCGNullWindowID) as? [[String:Any]]) ?? []
    for w in wins where (w[kCGWindowOwnerName as String] as? String ?? "").contains("MyApp") {
        if let b = w[kCGWindowBounds as String] as? [String:Any], let x = b["X"] as? CGFloat,
           let y = b["Y"] as? CGFloat, let ww = b["Width"] as? CGFloat, let hh = b["Height"] as? CGFloat {
            return CGRect(x: x, y: y, width: ww, height: hh)
        }
    }
    return nil   // nil == panel not on screen
}
```

### Drive the app with synthetic events — posting needs *no* permission

`CGEventPost` works without Accessibility and Carbon `RegisterEventHotKey` catches the synthetic key (same path BetterMouse uses). Summon, then dismiss:

```swift
func postKey(_ c: CGKeyCode, _ f: CGEventFlags) {
    let s = CGEventSource(stateID: .hidSystemState)
    let d = CGEvent(keyboardEventSource: s, virtualKey: c, keyDown: true)!;  d.flags = f; d.post(tap: .cghidEventTap)
    let u = CGEvent(keyboardEventSource: s, virtualKey: c, keyDown: false)!; u.flags = f; u.post(tap: .cghidEventTap)
}
postKey(CGKeyCode(kVK_ANSI_Q), [.maskControl, .maskAlternate, .maskCommand])  // ⌃⌥⌘Q summon
postKey(CGKeyCode(kVK_Escape), [])                                             // Esc dismiss
```

### Measure hotkey *capture* with a consumption tap (the only correct way)

To prove "the hotkey is captured **only** while visible / released after hide", measure event **consumption**, not registration. A listen-only `cgAnnotatedSessionEventTap` sits at the app-delivery point: if a Carbon hotkey consumed the key upstream, it never arrives → `delivered == 0`; otherwise `delivered > 0`. (Tap creation needs Accessibility — which a shell often *does* have even when Screen-Recording is denied.)

```swift
let tap = CGEvent.tapCreate(tap: .cgAnnotatedSessionEventTap, place: .headInsertEventTap,
    options: .listenOnly, eventsOfInterest: CGEventMask(1 << CGEventType.keyDown.rawValue),
    callback: { _,_,e,_ in if e.getIntegerValueField(.keyboardEventKeycode) == Int64(kVK_Escape) { bump() }
                           return Unmanaged.passUnretained(e) }, userInfo: nil)!
CFRunLoopAddSource(CFRunLoopGetCurrent(), CFMachPortCreateRunLoopSource(nil, tap, 0), .commonModes)
CGEvent.tapEnable(tap: tap, enable: true)
// Expected matrix: hidden→delivered=1 · visible→delivered=0 (consumed)+panel hides · after-hide→delivered=1
```

### Click safely on a live screen — target a point inside no normal window

To exercise a click-away path without mis-clicking the user's UI, click a point provably inside no `kCGWindowLayer == 0` (normal app) window — the same window-list data that *observes* the panel also tells you where it's *safe* to click. Restore the cursor after.

```swift
func emptyPoint(in disp: CGRect, avoiding extra: [CGRect]) -> CGPoint? {
    let occ = /* layer-0 onscreen window rects */ + extra
    var y = disp.minY + 40
    while y < disp.maxY - 90 {            // dodge menu bar + Dock band
        var x = disp.minX + 8
        while x < disp.maxX - 8 {
            let p = CGPoint(x: x, y: y)
            if !occ.contains(where: { $0.insetBy(dx:-2,dy:-2).contains(p) }) { return p }
            x += 40
        }; y += 40
    }
    return nil
}
let home = CGEvent(source: nil)?.location          // save cursor
CGWarpMouseCursorPosition(target); /* post leftMouseDown+Up at target */
CGWarpMouseCursorPosition(home!)                    // restore cursor
```

**Gotchas**
- **A `RegisterEventHotKey` conflict probe is useless cross-process.** Carbon does **not** reject cross-process duplicate hotkeys — `eventHotKeyExistsErr` only fires for a duplicate within the *same* event-dispatcher target. So "can I register Esc?" always succeeds and tells you nothing about whether another app holds it. Measure **consumption** (the tap), not registration.
- `screencapture` failing with "could not create image from display" = no Screen-Recording grant for the controlling shell; window-list + taps still work, so don't give up on automation.
- `CGEventPost` (posting) needs no permission; `CGEvent.tapCreate` (observing) needs Accessibility — test it (`tapCreate(...) == nil` ⇒ denied) and fall back to window-list-only + guided manual steps.
- Add ~400–700 ms `usleep` after each post: the app hops `Task { @MainActor }` before show/hide/register.

**Best for:** headless / sandboxed verification of HUD show-hide and global-hotkey capture (#64, #65, #72) when you can't see or screenshot the screen. Pairs with #72, #65, #64.
