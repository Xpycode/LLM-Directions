# 109 — A non-key floating HUD that ALSO needs bare-key verbs: gate `canBecomeKey` dynamically

**Problem.** Cookbook #81 establishes the rule for a floating HUD that pastes into the user's frontmost app: it must be **non-key**, or the synthetic ⌘V is delivered to *your* panel instead of the target. So you ship a plain `.nonactivatingPanel` (`canBecomeKey == false`) and the mouse path works blink-free.

Then you want **keyboard verbs** on that same HUD — bare keys to drive it (Space = paste next, R = reverse, Esc = stop) without reaching for the mouse. But a local `NSEvent` keyDown monitor only fires while the panel is the **key window**. You're stuck between two requirements that #81 framed as mutually exclusive: *non-key so paste lands*, vs *key so the monitor fires*.

The naive fix — make the subclass `override var canBecomeKey: Bool { true }` so you *can* `makeKey()` on demand — **silently breaks the mouse path**, and the failure is subtle. (Aloft/ClipSmart Paste Queue HUD, 2026-06-14.)

---

## The trap: a static `canBecomeKey = true` self-promotes on a SwiftUI button click

The plan assumed `becomesKeyOnlyIfNeeded = true` (or leaving `needsPanelToBecomeKey` at its default `false`) would keep a *button* click from promoting the panel to key — only a text field "needs" key. **It does not.** Live `isKeyWindow` probe on a Developer-ID-signed build: clicking a **hosted SwiftUI `Button`** inside an `NSHostingView` promotes a static-`canBecomeKey=true` `.nonactivatingPanel` to key **anyway**, on the very first click, on a HUD that was never deliberately engaged.

Consequence: the next synthetic ⌘V routes (by key window) into the HUD, not the target → paste vanishes. Worse, `AutoPasteService.paste()` still *reports success* (the frontmost **app** is still the target — a nonactivating panel doesn't change that, so `wouldPasteIntoSelf` passes), so the cursor advances as if it pasted. You get "the counter went up but nothing pasted" — exactly #81 Gotcha 1, reintroduced by the capability you added for keyboard mode.

**Tell:** a HUD that pasted fine as a plain `NSPanel` starts misrouting ⌘V the moment you give its subclass `canBecomeKey = true` — even before you call `makeKey()` anywhere.

---

## The fix: `canBecomeKey` is **dynamic state**, not a static **capability**

Gate `canBecomeKey` on an explicit "engaged" flag. Default `false` → the panel behaves **exactly** like the plain `NSPanel` from #81 (no click can promote it, mouse paste stays blink-free). Flip it `true` only in the one method that deliberately opts into keyboard mode, immediately before `makeKey()`.

```swift
private final class KeyableHUDPanel: NSPanel {
    /// Default false → a borderless .nonactivatingPanel that no click can promote to
    /// key (identical to the plain NSPanel in #81). True ONLY right before makeKey().
    var keyboardModeEngaged = false
    override var canBecomeKey: Bool { keyboardModeEngaged }
}
```

```swift
/// The ONLY path that lets the HUD take key. Called from explicit engage gestures
/// (a dedicated hotkey, or a click on the HUD *body* — never a button click).
func engagePasteQueueKeyboard() {
    guard let panel = pasteQueuePanel, panel.isVisible else { return }
    closeOverlay()                       // two key-capable panels can't both be key
    panel.keyboardModeEngaged = true     // open the gate, THEN makeKey — canBecomeKey reads the flag
    panel.makeKey()
}
```

---

## While key, each keyboard paste still needs the orderOut → ⌘V → re-key dance

Once the HUD *is* key, a synthetic ⌘V routes back into it (the #81 problem again). Reuse the proven "pinned overlay" handoff: relinquish key (`orderOut`), let ⌘V dispatch to the target one run-loop hop later, then re-show + re-key for the next press.

```swift
func pasteQueueKeyHandoff() {
    guard let panel = pasteQueuePanel, panel.isVisible, panel.isKeyWindow else {
        _ = PasteQueueManager.shared.pasteNext(); return        // non-key → direct, blink-free
    }
    guard !PasteQueueManager.shared.isEmitting,
          !PasteQueueManager.shared.isFinished else { return }   // ignored press costs no blink
    panel.orderOut(nil)                                          // hand key back to the target
    DispatchQueue.main.async {
        _ = PasteQueueManager.shared.emitNext()                  // write + ⌘V → lands in target
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.25) {
            guard !PasteQueueManager.shared.isFinished else { return }  // last item auto-stopped → don't resurrect
            panel.keyboardModeEngaged = true                    // keep the gate open so re-makeKey takes
            panel.orderFrontRegardless()
            panel.makeKey()
        }
    }
}
```

---

## The gate must self-heal: reset the flag on `didResignKey`

Arm the local key-verb monitor on the panel's `didBecomeKey` and tear it down on `didResignKey` — and in the resign handler **also reset `keyboardModeEngaged = false`**. Otherwise a HUD that lost key (the user clicked back into the target) stays key-*capable*, and a later stray click could silently re-promote it → the misroute returns. Scope the observers to the panel object (the HUD has no delegate):

```swift
NotificationCenter.default.addObserver(self, selector: #selector(hudDidBecomeKey),
    name: NSWindow.didBecomeKeyNotification, object: panel)
NotificationCenter.default.addObserver(self, selector: #selector(hudDidResignKey),
    name: NSWindow.didResignKeyNotification, object: panel)

@objc func hudDidBecomeKey(_ n: Notification) { installKeyMonitor() }
@objc func hudDidResignKey(_ n: Notification) {
    removeKeyMonitor()
    pasteQueuePanel?.keyboardModeEngaged = false   // can't be silently re-promoted by a later click
}
```

Because the handoff's `orderOut` itself resigns key, this same path tears keyboard mode down whenever the user genuinely leaves — no separate "did the user click away?" detection. The +0.25 s re-key re-opens the gate and re-arms the monitor, so the mode survives across each paste blink but collapses the instant focus truly moves on.

The HUD-local monitor swallows the bare verb keys (`return nil`, no system beep) but passes `⌘`-combos through so ⌘Q / ⌘Tab still work; match **letters by `charactersIgnoringModifiers`** (layout-robust — see the QWERTZ ⌘Y lesson), Space/Esc by keyCode.

---

## Bonus — surfacing "keyboard mode is live" to a SwiftUI view

The accent ring telling the user bare keys are armed lives in SwiftUI, but `isKeyWindow` is AppKit-only. Bridge it through the HUD's already-observed `ObservableObject`: a `@Published var keyboardModeActive`, flipped from the same `didBecomeKey`/`didResignKey` handlers (`MainActor.assumeIsolated { manager.setKeyboardModeActive(true/false) }`). The view overlays an accent `RoundedRectangle.strokeBorder` when it's set. (If the panel's `contentView.layer.masksToBounds == true`, glue the glow `.shadow` to the **stroke shape**, not the whole view — an outward glow on the opaque silhouette is clipped at the panel edge; a shadow on the thin stroke leaves a visible inner bloom.)

---

**Pairs with** #81 (the non-key HUD synthetic-paste rule this evolves — read it first), #82 (key-panel reactivate-on-self-refusal), #107 (the `.disabled()` hit-test fall-through that can *accidentally* trigger the engage gesture), #65 (cursor-anchored NSPanel HUD), #72 (scoped Carbon hotkey / Esc-dismiss on a non-key panel), #08 (keyboard/event synthesis).

**One-line tell:** *a HUD that must be non-key for synthetic paste yet key for a verb monitor needs `canBecomeKey` as a dynamic flag (default false, true only right before an explicit `makeKey()`) — not a static `true`, which hosted SwiftUI buttons self-promote on click.*
