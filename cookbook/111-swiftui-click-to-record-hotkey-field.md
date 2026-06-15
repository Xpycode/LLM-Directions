# SwiftUI click-to-record hotkey field (the field IS the control)

**Source:** `1-macOS/LaunchAway/` — `01_Project/LaunchAway/Settings/HotKeyRecorderView.swift` (2026-06-15, v1.0.0).

You want a Settings control where the user **records a keyboard shortcut** — click it, press ⌃⌥⌘Space, it saves. The reflex is a **read-only box showing the current combo + a separate "Record" button** beside it. That reflex produces two bugs, one visual and one behavioural:

**Visual trap — the Record button gets clipped.** Lay the row out as a `SettingsRow` with a fixed-width trailing label column (`Text(label).frame(width: 116, alignment: .trailing)`) + the recorder + a `Spacer()`, and the 116pt column shoves the combo box to mid-right; the recorder's own `box + Record button` then overflows the pane's right edge and the **button is clipped off entirely** — leaving a lone, empty-looking bordered box floating far from its label. (Owner reaction on first cut: "WTF… the record button looks shit.")

**The fix is the idiomatic macOS shortcut recorder: make the field itself the button.** No separate Record control to clip. Click the field → it arms capture ("Type a shortcut…", accent border + ✕ to cancel); the next valid combo commits; Esc/✕ cancels. This is how the popular `KeyboardShortcuts` package presents it. Lay the label **above** the field (form-style), not in a fixed-width column beside it.

Capture uses a **local** `NSEvent` keyDown monitor — it fires only while the Settings window is **key**, which is exactly right for a settings recorder and needs **no Input-Monitoring permission** (contrast #64's Carbon `RegisterEventHotKey`, which is the actual *system-wide registration* of the saved binding — this view only *captures* the binding to persist).

```swift
// The whole field is the control: click to arm, click again (or Esc/✕) to cancel.
var body: some View {
    Button(action: toggle) { field }          // field = rounded HStack(combo + glyph), fixed 240×34
        .buttonStyle(.plain)
        .onHover { isHovering = $0 }           // hover → accent border + pencil glyph (reads as editable)
        .onDisappear { removeMonitor() }
}
private func toggle() { isRecording ? stopRecording() : startRecording() }

private func startRecording() {
    state = .recording
    monitor = NSEvent.addLocalMonitorForEvents(matching: [.keyDown]) { @MainActor [self] e in
        handleKeyDown(e)                       // @MainActor closure → Swift 6 strict-concurrency clean
    }
}

@MainActor
private func handleKeyDown(_ event: NSEvent) -> NSEvent? {
    if event.keyCode == UInt16(kVK_Escape) {   // Esc cancels…
        stopRecording()
        return event                           // …and PROPAGATES (window cancel / panel dismiss)
    }
    let candidate = HotKeyBinding(
        keyCode:   UInt32(event.keyCode),                                  // ANSI keycode = PHYSICAL key,
        modifiers: HotKeyFormatter.carbonMask(from: event.modifierFlags))  // QWERTZ-safe; never match chars
    guard HotKeyService.isValid(candidate) else {                          // require ⌘ or ⌃…
        state = .error("Hotkey must include ⌘ or ⌃"); removeMonitor()      // …or it collides with typing
        return nil                             // swallow — don't beep / leak to the app
    }
    AppSettings.shared.hotKeyBinding = candidate
    stopRecording()
    return nil                                 // swallow the accepted combo — must NOT reach the app
}
```

**Why each piece matters**
- **Return `nil` to swallow** the accepted combo (and the invalid one) so the keypress never leaks to the app behind Settings (no beep, no stray character). **Return the event on Escape** so cancel still propagates to the window / a host panel's Esc-dismiss (#72).
- **`addLocalMonitorForEvents`, not global** — local fires only while the window is key, the correct scope for a Settings recorder; it needs no TCC permission. A *global* monitor would demand Input Monitoring and is the wrong tool here.
- **Validate `⌘`/`⌃` present** — a modifier-less binding (or plain Space) collides with normal typing the instant it's registered system-wide. Reject at capture time with a visible error state, not after saving.
- **Match by Carbon keyCode** (`kVK_ANSI_*` = physical key position), never by `event.characters` — keeps it correct on QWERTZ / non-US layouts. Convert `NSEvent.ModifierFlags → Carbon mask` once (`cmdKey|optionKey|controlKey|shiftKey`).
- **`@MainActor` on the monitor closure** — keyDown monitors fire on the main thread; annotating the closure lets all `@MainActor` state mutate without a hop and satisfies Swift 6 strict concurrency.
- **State machine `idle / recording / error`** drives fill + border + glyph: idle shows the formatted combo + a `pencil` (accent on hover); recording shows accent border + "Type a shortcut…" + an `xmark.circle.fill` to cancel; error shows a red border + message until the next click re-arms. A border-only pulse (`opacity` + `repeatForever` while recording) signals "listening" without layout shift.
- **Greedy-Shape footnote:** if the field's background is a `RoundedRectangle` in a `ZStack`, give the field a **fixed** frame (`240×34`) — a `Shape` is greedy and a min-only frame lets it balloon to fill the pane (the earlier sibling bug before the rewrite).

**Layout rule that prevents the clip:** label **above** the field in a leading `VStack`, helper text + a subtle "Reset to default" accent link below — all left-aligned. Do **not** put the recorder in a fixed-width-label row beside a trailing control; that's what pushed the (old) button off-pane.

Pairs with **#64** (the Carbon `RegisterEventHotKey` that actually registers the *saved* binding system-wide — this view only captures it), **#72** (scoped Carbon Esc-dismiss — why `handleKeyDown` returns the event on Escape), **#71** (the self-managed `LSUIElement` Settings window this lives in), **#00** (App Shell Standard / `Theme`), **#08** (keyboard shortcuts).
