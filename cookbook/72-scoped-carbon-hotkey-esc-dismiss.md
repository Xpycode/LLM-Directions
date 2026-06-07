# Permission-free Esc-to-dismiss via a *scoped* Carbon hotkey (+ ID-filtered multi-instance `HotKeyService`)

**Source:** `1-macOS/QuickStatsPanel/` — `Services/HotKeyService.swift`, `AppDelegate.swift`, `Panel/PanelWindowController.swift` (2026-06-05, v0.2.0).

You have a non-activating HUD panel (#65) that **never becomes key** (so the user keeps typing in their real app), and you want **Esc to dismiss it**. The trap everyone hits: a non-key panel never receives `keyDown` / SwiftUI `.onKeyPress` — Esc goes to whatever app actually has focus. A global *keyboard* monitor would catch it but needs **Input-Monitoring permission** (this is what #65 originally said made Esc "not free").

It *is* free. Register **bare Escape as a Carbon hotkey (#64) only while the panel is visible**, and unregister the instant it hides. Carbon is permission-free and fires regardless of focus — the one mechanism that works for a window that never becomes key. The toggle hotkey stays the primary dismiss; Esc + click-away are conveniences.

Two non-obvious requirements make it correct:

### 1. A second `HotKeyService` instance must filter by `EventHotKeyID`

Carbon dispatches **every** hotkey press to **all** installed app-level handlers. The naïve single-hotkey service fires `onTrigger` unconditionally, so adding a second instance makes the toggle hotkey *also* fire the dismiss action. Read the fired id and match a per-instance id:

```swift
private let id: UInt32                 // 1 = toggle, 2 = dismiss
init(id: UInt32 = 1) { self.id = id }

static let escape = Binding(keyCode: UInt32(kVK_Escape), modifiers: 0)  // bare Esc

// inside the InstallEventHandler C callback:
{ _, event, userData -> OSStatus in
    guard let userData else { return noErr }
    var firedID = EventHotKeyID()
    GetEventParameter(event, EventParamName(kEventParamDirectObject),
                      EventParamType(typeEventHotKeyID), nil,
                      MemoryLayout<EventHotKeyID>.size, nil, &firedID)
    Task { @MainActor in
        let svc = Unmanaged<HotKeyService>.fromOpaque(userData).takeUnretainedValue()
        if firedID.id == svc.id { svc.onTrigger?() }      // ← only my own hotkey
    }
    return noErr
}
// register with: EventHotKeyID(signature: 0x51535450 /* 'QSTP' */, id: id)
```

### 2. Drive register/unregister from the *window's own* visibility, not the caller's toggle

The panel hides via **three** routes — toggle hotkey, click-away (a global mouse monitor), and Esc itself. If you register/unregister Esc inside `AppDelegate.togglePanel()`, a **click-away** dismissal bypasses it and leaves Esc captured system-wide forever. Tie teardown to the *resource's* lifecycle instead:

```swift
// PanelWindowController — one signal, fired by every show/hide path:
var onVisibilityChanged: ((Bool) -> Void)?
func show(...) { /* … */ panel.orderFrontRegardless(); onVisibilityChanged?(true) }
func hide() {
    guard panel != nil else { return }   // guard so redundant hides don't double-fire
    panel?.orderOut(nil); panel = nil; hosting = nil
    onVisibilityChanged?(false)
}

// AppDelegate — Esc lives exactly as long as the panel is on screen:
private let dismissHotKey = HotKeyService(id: 2)
panel.onVisibilityChanged = { [weak self] visible in
    guard let self else { return }
    if visible { self.dismissHotKey.register(.escape) { [weak self] in self?.panel.hide() } }
    else       { self.dismissHotKey.unregister() }
}
```

**Gotchas**
- **System-wide capture while visible.** A bare Escape hotkey swallows Esc for *every* app until the panel hides. Acceptable for a transient HUD; don't do this for a long-lived window.
- **Filter by id or two services collide** — see §1. This is a latent bug even with one hotkey the moment you add a second.
- **Lifecycle-driven, not call-site-driven** — see §2. The bug it prevents (click-away leaves Esc captured) is invisible until you test the *non-toggle* hide paths.
- Same Carbon cleanup rules as #64 (explicit `unregister()` from `applicationWillTerminate`, no `deinit`).

**Best for:** giving a non-activating `NSPanel` HUD (#65) / `LSUIElement` agent app a permission-free Esc-to-dismiss without making it key. Pairs with #64 (base Carbon hotkey), #65 (the HUD panel), #71 (the opposite case — a window you *do* make key), and #73 (how to verify all of this without Screen-Recording permission).
