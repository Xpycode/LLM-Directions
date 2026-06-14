# 107 — A `.disabled()` SwiftUI control drops out of hit-testing → taps fall THROUGH to an ancestor gesture

**Problem.** A container view has a catch-all gesture — `.contentShape(Rectangle()).onTapGesture { … }` on the background — *and* an interactive child control (a `Button`) layered on top. Normally the `Button` consumes its own click and the background gesture never sees it. But when that button is **`.disabled(…)`**, clicking it does something surprising: the tap **passes through** to the ancestor's `.onTapGesture`, silently firing the background action the user never aimed at.

Real incident (Aloft Paste Queue HUD). The HUD's ▶ "Paste next" button was `.disabled(queue.isFinished || queue.isEmitting)`. After each paste, an `isEmitting` re-entrancy lock held for ~0.27s and the button went disabled. The HStack behind it had `.onTapGesture { engagePasteQueueKeyboard() }` (a deliberate "click the body to enter keyboard mode" affordance). A user clicking ▶ **rapidly** landed a click during the disabled window → the tap fell through to the body gesture → the HUD entered keyboard mode → it became the key window → every subsequent synthetic ⌘V routed into the HUD instead of the target app (**system beep**, see #81/#82). Symptom as reported: *"enqueued 7, first ~4 pasted, the rest just beep as if focus was lost."* It looked like a paste/focus bug; the actual trigger was a UI hit-testing leak two layers up.

---

## Why it happens

`.disabled(true)` sets `EnvironmentValues.isEnabled = false`. A disabled control is **removed from hit-testing** — it doesn't just grey out and swallow clicks, it becomes transparent to the gesture system. So a tap at that point continues to the next eligible responder, which includes an **ancestor's** `.onTapGesture` whose `.contentShape` covers the same area. Enabled child controls win over an ancestor tap gesture; disabled ones don't participate, so the ancestor wins by default.

The trap needs three ingredients that are each individually reasonable:
1. An ancestor catch-all tap gesture (a "click anywhere on the body" affordance).
2. A child control sitting inside that gesture's `contentShape`.
3. That control toggling to `.disabled()` based on transient state (a lock, a loading flag, "nothing to do right now").

Rapid or mistimed clicks during the disabled window are all it takes.

---

## Fix — keep the control hit-testing; gate the *action*, not the *control*

Don't use `.disabled()` for a transient "busy / nothing to do" state when there's an ancestor gesture behind it. Keep the button **enabled** so it always consumes its own click, no-op inside the action when the precondition fails, and convey the disabled look with `.opacity` (or a style change) instead:

```swift
Button {
    // Guard INSIDE the action: staying enabled keeps the button consuming its
    // own clicks, so a tap during the busy window can't fall through to the
    // ancestor's .onTapGesture.
    guard !queue.isFinished, !queue.isEmitting else { return }
    queue.pasteNext()
} label: {
    Image(systemName: "play.fill")
}
.opacity(queue.isFinished || queue.isEmitting ? 0.4 : 1.0)   // visual "disabled", still hit-testing
```

Trade-off: a genuinely disabled control no longer gets the system's automatic dimming, VoiceOver "dimmed" trait, or pointer treatment — you're re-implementing the *appearance* of disabled while keeping the *hit target* live. That's the right call **only** when an ancestor gesture would otherwise capture the fall-through. For a control with nothing interactive behind it, plain `.disabled()` is still correct and preferable.

Belt-and-suspenders for the incident above: also **reset the state the fall-through corrupts** at a natural boundary — Aloft's `closePasteQueueHUD()` now resets `keyboardModeEngaged = false` so even a stray engage can't persist into the next queue. Fixing the leak is the cause; resetting the latched state bounds the blast radius.

---

## Alternatives (when you can't restyle the button)

- **Move the ancestor gesture off the shared area.** Put `.onTapGesture` only on the parts that should be tappable (the title label / spacer), not a full-bleed `.contentShape(Rectangle())` that sits under every control.
- **`.allowsHitTesting(false)` on the background** while a control is busy — but that's harder to scope than just keeping the button enabled.
- **A high-priority/simultaneous gesture** to disambiguate — usually overkill versus the opacity approach.

---

## Tells & rules

- **Tell:** a background/whole-view action fires "by itself" only when a foreground control is in its disabled state; works fine when the control is enabled. The bug is intermittent and timing-dependent (it needs the disabled window).
- **Rule:** `.disabled()` removes a view from hit-testing — taps pass to whatever is behind/around it, **including an ancestor `.onTapGesture`**. Never rely on a disabled control to "block" an ancestor gesture.
- **Rule:** for a *transient* busy state under a catch-all gesture, gate the action inside the closure + dim with `.opacity`, don't `.disabled()`.
- **Rule:** when a fall-through can latch persistent state (a mode flag, a key-window promotion), also reset that state at a lifecycle boundary so one stray tap can't poison later interactions.

Source: Aloft (ClipSmart) `Views/PasteQueueHUD.swift` + `ClipSmartApp.closePasteQueueHUD()`. Pairs with **#81** (non-key HUD synthetic paste — the downstream beep), **#82** (key-panel reactivate-on-self-refusal), **#70** (data-driven control strip), **#65** (cursor-anchored NSPanel HUD).
