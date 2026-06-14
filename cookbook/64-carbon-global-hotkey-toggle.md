# Permission-free global hotkey via Carbon `RegisterEventHotKey`

**Source:** `1-macOS/QuickStatsPanel/` — `Services/HotKeyService.swift` (2026-06-04, v0.1.0).

You want a **system-wide hotkey** that fires no matter which app is focused — to summon a HUD, toggle an overlay, trigger an action. The reflex is `NSEvent.addGlobalMonitorForEvents(matching: .keyDown)`, but a global **keyboard** monitor requires the user to grant **Accessibility / Input Monitoring** permission (first-launch friction, and it can only *observe* — it can't consume the event). For a simple trigger you don't need any of that.

Carbon's `RegisterEventHotKey` registers a hotkey at the system level with **zero special permission**, fires regardless of focus, and even catches *synthesized* key events (e.g. a mouse button mapped to a key combo via BetterMouse / Karabiner). The API is old (Carbon) but fully supported on macOS 15.

The one trap: the event callback is a **C function pointer**, so it can't capture Swift context. Pass `self` through the `userData` pointer, and because the callback is *nonisolated* you must hop to the main actor before touching your `@MainActor` state.

```swift
import AppKit
import Carbon.HIToolbox

@MainActor
final class HotKeyService {
    struct Binding: Equatable {
        var keyCode: UInt32       // Carbon virtual keycode, e.g. kVK_ANSI_Q
        var modifiers: UInt32     // Carbon mask: controlKey | optionKey | cmdKey | shiftKey
        static let `default` = Binding(
            keyCode: UInt32(kVK_ANSI_Q),
            modifiers: UInt32(controlKey | optionKey | cmdKey)   // ⌃⌥⌘Q
        )
    }

    private var hotKeyRef: EventHotKeyRef?
    private var handlerRef: EventHandlerRef?
    private var onTrigger: (() -> Void)?

    func register(_ binding: Binding = .default, onTrigger: @escaping () -> Void) {
        unregister()
        self.onTrigger = onTrigger

        var spec = EventTypeSpec(eventClass: OSType(kEventClassKeyboard),
                                 eventKind: UInt32(kEventHotKeyPressed))
        let selfPtr = Unmanaged.passUnretained(self).toOpaque()
        InstallEventHandler(GetApplicationEventTarget(),
            { _, _, userData -> OSStatus in
                guard let userData else { return noErr }
                // C callback is nonisolated → hop to main before touching self.
                Task { @MainActor in
                    Unmanaged<HotKeyService>.fromOpaque(userData)
                        .takeUnretainedValue().onTrigger?()
                }
                return noErr
            },
            1, &spec, selfPtr, &handlerRef)

        let id = EventHotKeyID(signature: OSType(0x51535450) /* 'QSTP' */, id: 1)
        RegisterEventHotKey(binding.keyCode, binding.modifiers, id,
                            GetApplicationEventTarget(), 0, &hotKeyRef)
    }

    func unregister() {
        if let hotKeyRef { UnregisterEventHotKey(hotKeyRef); self.hotKeyRef = nil }
        if let handlerRef { RemoveEventHandler(handlerRef); self.handlerRef = nil }
        onTrigger = nil
    }
    // NB: no `deinit` cleanup — a @MainActor class's deinit is nonisolated under
    // Swift 6 and can't touch the non-Sendable Carbon pointers. Clean up via an
    // explicit unregister() from applicationWillTerminate instead.
}
```

**Gotchas**
- **Carbon keycodes ≠ ASCII.** `kVK_ANSI_Q` is `12`, not `"Q"`. Use the `kVK_*` constants from `Carbon.HIToolbox`. The modifier mask uses Carbon's `cmdKey`/`optionKey`/`controlKey`/`shiftKey` (Int), cast to `UInt32` — **not** `NSEvent.ModifierFlags`.
- **`signature` must be a unique `OSType`** (a four-char code). Collisions with another app's hotkey id can misroute events. A hex'd ASCII tag (`0x51535450` = `'QSTP'`) keeps it distinct.
- **Rebinding = unregister + register.** There's no "update in place"; tear down and re-create on a settings change.
- **Silent failure on conflict.** If another app already owns the combo, `RegisterEventHotKey` may not fire and gives no user-visible error — pair with a sensible default + an in-app rebind UI.
- Swift-6 strict concurrency: the trampoline `Task { @MainActor in … }` is what keeps `onTrigger` access legal from the C callback.
- **Multiple hotkeys on the shared app event target: a `noErr` handler starves its siblings.** Each `HotKeyService` instance installs its handler on the *same* `GetApplicationEventTarget()`. Carbon dispatches an event to those handlers **most-recently-installed-first**, and returning `noErr` means *"handled — stop propagation."* So if every handler returns `noErr`, only the **last-registered** hotkey ever fires: register window then region → region's handler runs first, returns `noErr` for *every* press (including the window id), and the window hotkey is silently dead. Each handler must read the fired id synchronously and **return `eventNotHandledErr` when it isn't its own**, so Carbon keeps propagating to the sibling that owns it. The id read needs `instanceID` to be `nonisolated let` so the C callback can touch it without an actor hop:
  ```swift
  nonisolated let instanceID: UInt32   // 1 = window, 2 = region, …
  // inside the C handler:
  var firedID = EventHotKeyID()
  GetEventParameter(event, EventParamName(kEventParamDirectObject),
                    EventParamType(typeEventHotKeyID), nil,
                    MemoryLayout<EventHotKeyID>.size, nil, &firedID)
  let svc = Unmanaged<HotKeyService>.fromOpaque(userData).takeUnretainedValue()
  guard firedID.id == svc.instanceID else { return OSStatus(eventNotHandledErr) } // not ours → let siblings see it
  Task { @MainActor in svc.onTrigger?() }
  return OSStatus(noErr)                                                          // ours → claim it
  ```
  This only bites with **N≥2** hotkeys, so a single-hotkey smoke test passes and the bug surfaces later. (Source: QuickScreenShot `HotKeyService.swift`, 2026-06-14.)

**Best for:** a menu-bar-less / `LSUIElement` utility that's summoned only by a hotkey, where requiring an Accessibility grant would be unacceptable friction. Pairs with #65 (cursor-anchored NSPanel HUD), #60 (closure-bridged AppKit).
