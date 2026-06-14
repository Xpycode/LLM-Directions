# 81 — A floating HUD that drives synthetic paste into another app

**Problem.** You have a floating control panel (a "paste queue" emitter, a snippet sender, a macro HUD) that must **stay visible while it pastes into whatever app the user is working in**. The user clicks a button on your HUD → you write the pasteboard → you synthesize ⌘V into the frontmost app. It "kinda works": the HUD's counter advances, but **nothing actually pastes**. Or pastes drop intermittently. Or the pasted strings reappear in your own clipboard history.

Three distinct gotchas hide here. All three bit a real Paste Queue HUD (Aloft/ClipSmart, 2026-06-06).

---

## Gotcha 1 — a key panel steals keyboard focus; frontmost-app ≠ key-window

**Symptom:** clicking the HUD's "Next" button advances the cursor (so `paste()` thinks it succeeded — no refusal) but the ⌘V lands nowhere. `NSWorkspace.frontmostApplication` still correctly reports the *target* app.

**Cause:** the HUD reused an `NSPanel` subclass that overrode `canBecomeKey = true` (common — borderless `.nonactivatingPanel`s need that override to host a *text field*). A `.nonactivatingPanel` decouples two focus concepts:
- **frontmost application** — clicking a non-activating panel does **not** activate your app, so `frontmostApplication` keeps reporting the target. ✅
- **key window** — but the panel *can still become key*, taking **keyboard focus** away from the target (this is exactly how Spotlight types into itself without deactivating Finder). ❌

So the synthetic ⌘V (posted via `.cgSessionEventTap`) is delivered to the **key window = your HUD**, not the target. The overlay/picker pattern (#65) gets away with `canBecomeKey = true` only because it **closes before pasting**, handing key status back. A HUD that stays open during paste must **never take key**.

**Fix:** use a plain `NSPanel` (a borderless `.nonactivatingPanel` defaults to `canBecomeKey == false`), and make the SwiftUI buttons clickable while your app is inactive via a first-mouse hosting view:

```swift
// A HUD with NO text fields never needs to be key. Do NOT use the OverlayPanel
// subclass that forces canBecomeKey = true.
let panel = NSPanel(
    contentRect: NSRect(origin: .zero, size: NSSize(width: 320, height: 80)),
    styleMask: [.borderless, .nonactivatingPanel, .fullSizeContentView],
    backing: .buffered, defer: false
)
panel.level = .floating
panel.hidesOnDeactivate = false
panel.collectionBehavior = [.canJoinAllSpaces, .fullScreenAuxiliary]
panel.isMovableByWindowBackground = true

// First click must reach the SwiftUI button while the app is inactive — a
// non-activating panel otherwise swallows the first click just to raise itself.
let host = FirstMouseHostingView(rootView: MyHUD())
host.autoresizingMask = [.width, .height]
panel.contentView = host          // set contentView directly (no controller)

private final class FirstMouseHostingView<Content: View>: NSHostingView<Content> {
    override func acceptsFirstMouse(for event: NSEvent?) -> Bool { true }
}
```

Show it with `orderFrontRegardless()` — **never** `makeKeyAndOrderFront`, which would re-introduce the focus theft. The keyboard focus stays with the target app, so `paste()` delivers ⌘V there.

**Tell:** the HUD's progress advances but the paste doesn't land, *and* `frontmostApplication` is correct → your panel is taking key. Make it non-key.

---

## Gotcha 2 — a synthesized Return inherits a stale Command flag → fires as ⌘Return

If the HUD also presses Return after each paste ("send each as a separate chat message / line"), a naive `pressReturn()` posts the key with **no explicit flags**, so the `CGEvent` inherits `CGEventSource(stateID: .combinedSessionState)` — which can still carry the **Command flag bleeding from the ⌘V you posted ~60 ms earlier**. The result is **⌘Return**, a no-op in a text editor. Symptom: "the line break never appears."

**Fix:** clear the flags explicitly.

```swift
let down = CGEvent(keyboardEventSource: source, virtualKey: CGKeyCode(kVK_Return), keyDown: true)
let up   = CGEvent(keyboardEventSource: source, virtualKey: CGKeyCode(kVK_Return), keyDown: false)
down?.flags = []          // a PLAIN Return, never ⌘Return
up?.flags = []
down?.post(tap: .cgSessionEventTap)
up?.post(tap: .cgSessionEventTap)
```

Mirror the same `setLocalEventsFilterDuringSuppressionState(...)` the ⌘V path uses.

---

## Gotcha 3 — sequential pastes race; the pasteboard is one shared slot

Posting ⌘V is **asynchronous** — the target reads the pasteboard later, on *its* run-loop turn. If your HUD writes the next item's content before the previous ⌘V was consumed, the pasteboard is overwritten and a paste is lost (while a Return that needs no pasteboard still fires → "fewer text lines than line-breaks", and inconsistent run-to-run).

**Fix:** serialize each emit with a re-entrancy lock + settle delays; disable the trigger button while the lock is held so rapid taps give feedback instead of silently racing.

```swift
@Published private(set) var isEmitting = false
private static let returnSettle: TimeInterval = 0.15   // ⌘V → Return
private static let lockRelease:  TimeInterval = 0.12    // last keystroke → unlock

func pasteNext() -> Bool {
    guard !isFinished, !isEmitting else { return false }
    writeToPasteboard(current)                 // see Gotcha 4
    if let refusal = AutoPasteService.paste() { lastRefusal = refusal; return false } // no lock on refusal → instant retry
    isEmitting = true
    cursor += 1
    let after = sendAfterEach ? Self.returnSettle : 0
    DispatchQueue.main.asyncAfter(deadline: .now() + after) { [weak self] in
        guard let self else { return }
        if self.sendAfterEach { _ = AutoPasteService.pressReturn() }
        DispatchQueue.main.asyncAfter(deadline: .now() + Self.lockRelease) { [weak self] in
            self?.isEmitting = false
        }
    }
    return true
}
// In the view: .disabled(queue.isFinished || queue.isEmitting)
```

---

## Gotcha 4 — a clipboard *manager* must suppress its own paste echo

If your app *is* a clipboard manager, every pasteboard write it makes looks identical to a user copy — so its own poller re-captures each emitted item into history, *and* that capture can clobber the in-flight pasteboard (Gotcha 3 again). Stamp the change-count after every outgoing write so the poller treats it as already-seen:

```swift
func writeOutgoingText(_ text: String) {
    pasteboard.clearContents()
    pasteboard.setString(text, forType: .string)
    changeCount = pasteboard.changeCount     // ← the anti-recapture stamp
}
```

Route **every** outgoing path (plain string, item, file-URL) through a writer that does this — a raw `NSPasteboard.general.setString` skips the stamp and the echo returns.

---

## Bonus — mode toggles need explicit ON chrome in a non-key panel

SwiftUI's `.toggleStyle(.button)` renders its accent highlight only in a **key/active** window — which your HUD deliberately is not (Gotcha 1). A mode toggle will look permanently OFF. Use hard-coded fill/foreground instead of the system accent:

```swift
.foregroundStyle(isOn ? Color.white : Color.primary)
.background(RoundedRectangle(cornerRadius: 5)
    .fill(isOn ? Color.accentColor : Color.secondary.opacity(0.18)))
```

---

**Pairs with** #65 (cursor-anchored non-activating panel — the *key* sibling that closes-before-pasting), #08 (keyboard/event synthesis), #10 (selection/multi-select), #04 (NSHostingView), **#109 (the sequel — when the same HUD ALSO needs bare-key verbs, gate `canBecomeKey` dynamically instead of going back to a static `true`)**.

**One-line tell:** *a floating HUD that pastes into other apps must be non-key, post flag-cleared keystrokes, serialize its emits, and stamp its own pasteboard writes.*
