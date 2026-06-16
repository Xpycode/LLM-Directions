# 116 — A bare-letter `.keyboardShortcut` is swallowed by a focused `TextField` → hand focus off on a state change

**Problem.** You want a single-key accelerator for the primary action of a screen — `Q` to enqueue, `D` to download, `R` to run — the kind of bare-letter verb a power user expects once a result is on screen. You attach `.keyboardShortcut("q", modifiers: [])` to the action button and… nothing happens. The keystroke types a literal "q" somewhere instead of firing the button.

Real incident (YTdl preview card). The card has a URL `TextField` at the top and a **Download** button below. The user pastes a link, a probe runs, a preview appears, and we wanted `Q` to enqueue the previewed video. But the `TextField` still held keyboard focus from the paste, so every `Q` press went *into the field as text* and the button's shortcut never fired. The accelerator looked broken; the real cause was **focus**, two controls up.

---

## Why it happens

SwiftUI's `.keyboardShortcut(_:modifiers:)` registers a key equivalent that competes with the **first responder**. A focused `TextField` (an `NSTextView`/`NSTextField` under the hood) consumes plain character keystrokes *before* the key-equivalent machinery gets a look — that's correct behaviour, it's how you type "q" into a field. A shortcut **with a command/control modifier** (`⌘Q`) bypasses the field because the field doesn't claim modified combos; a **bare letter** does not. So:

- `.keyboardShortcut("q", modifiers: [.command])` → fires even while the field is focused.
- `.keyboardShortcut("q", modifiers: [])` → **only** fires when **no text field** owns focus.

The bare-letter verb is the nicer UX (no chord to learn), but it's mutually exclusive with a focused field. The fix is not to fight the responder chain — it's to **give focus away** at the moment the verb becomes relevant.

There's a second, smaller trap stacked on top: **a view takes only one `.keyboardShortcut`.** Chaining two (`.keyboardShortcut(.defaultAction).keyboardShortcut("q", …)`) does **not** bind both keys — the outer one wins and you silently lose Return. To have *both* Return (default action) and a bare letter, you need **two button instances**.

---

## Fix — drop field focus on the state change that surfaces the action; restore it when you go back

Drive focus from the screen's state machine, not from view lifecycle. When the state that *reveals* the action arrives (here: a successful probe), clear the field's `@FocusState`; when you return to the entry state (after the action consumes the input), restore it so the next `⌘V` still lands in the field.

```swift
struct URLInputView: View {
    @Binding var probeState: ProbeState
    @FocusState private var fieldFocused: Bool

    var body: some View {
        TextField("Paste URL…", text: $urlText)
            .focused($fieldFocused)
            // …
            // .onChange needs an Equatable value; ProbeState carries non-Equatable
            // payloads, so observe a payload-free phase key (see note below).
            .onChange(of: probeState.phase) { _, phase in
                switch phase {
                case .success: fieldFocused = false   // hand focus off → bare-key verb can land
                case .idle:    fieldFocused = true    // back to entry → next ⌘V pastes here
                case .probing, .failed: break         // keep focus; user may keep editing
                }
            }
    }
}
```

And the button side — keep Return on the visible control, route the bare letter through a **zero-opacity sibling** so both keys work:

```swift
Button("Download", action: onDownload)
    .keyboardShortcut(.defaultAction)               // Return (works once field yields focus)
    .help("Add to queue (Return or Q)")
    .background(                                     // a SECOND button: one shortcut per view
        Button("", action: onDownload)
            .keyboardShortcut("q", modifiers: [])    // bare Q
            .opacity(0)
            .accessibilityHidden(true)
    )
```

The hidden button stays in the view tree (so its shortcut is live) but is invisible and out of the a11y tree. Both call the same action; the focus handoff is what makes the bare `Q` actually reachable.

### The `.onChange` Equatable snag

`.onChange(of:)` requires the observed value be `Equatable`. An enum that carries non-`Equatable` payloads (a probe's metadata, an error) can't conform cheaply. Don't force `Equatable` across the whole payload graph — expose a **payload-free phase key** and observe that:

```swift
enum ProbeState {                 // payloads aren't Equatable
    case idle, probing
    case success(ProbeMetadata), failed(DownloadError)

    enum Phase: Equatable { case idle, probing, success, failed }
    var phase: Phase {
        switch self {
        case .idle: .idle; case .probing: .probing
        case .success: .success; case .failed: .failed
        }
    }
}
```

`.onChange(of: probeState.phase)` now fires on *transitions between phases* — exactly the granularity a focus handoff cares about, and it ignores payload churn within a phase.

---

## Why a focus handoff beats the alternatives

- **A global `NSEvent.addLocalMonitorForEvents(.keyDown)`** would catch the key regardless of focus, but it's heavier, needs `return nil` to swallow the event (else beep / stray char), and re-implements what `.keyboardShortcut` already does. Reserve monitors for *capture* UIs like a shortcut recorder (#111), not a single static verb.
- **Requiring a modifier** (`⌘D`) sidesteps the whole problem and is the right call when the field legitimately keeps focus. Use the bare letter only when the screen has a natural "input is done, now act" moment to hang the focus handoff on.
- **Defocusing in `.onAppear`** is too blunt — it fights the user the instant the view loads. Tie it to the state transition that *earns* it.

---

## Tells & rules

- **Tell:** a single-key accelerator types its letter into a field instead of firing; the same shortcut with `⌘` added works fine. → it's a focus problem, not a binding problem.
- **Rule:** a focused `TextField` swallows **bare-letter** `.keyboardShortcut`s; modified combos pass through. To use a bare letter, ensure no text field owns focus when the verb should fire.
- **Rule:** drive focus from the screen's **state machine** (clear on the state that surfaces the action, restore on return to entry) — not from `.onAppear`. Restoring on the way back keeps `⌘V`/typing working for the next round.
- **Rule:** **one `.keyboardShortcut` per view.** For two keys on one action (Return *and* a letter), add a second zero-opacity `Button` (`.opacity(0).accessibilityHidden(true)`) calling the same closure.
- **Rule:** `.onChange(of:)` needs `Equatable`; for an enum with non-`Equatable` payloads, observe a derived payload-free `Phase` key instead of forcing conformance.

Source: YTdl `Views/URLInputView.swift` (focus handoff) + `Views/PreviewPaneView.swift` (sibling-button bare-Q) + `Models/ProbeState.swift` (`Phase`). Pairs with **#08** (keyboard-shortcut tiers — when to escalate to an `NSEvent` monitor), **#111** (click-to-record hotkey field — the monitor approach, for *capturing* a binding rather than firing one verb), **#109** (dynamic `canBecomeKey` — the AppKit-panel cousin of "make focus follow intent"), **#71** (self-managed key window).
