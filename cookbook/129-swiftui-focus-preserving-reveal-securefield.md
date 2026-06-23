# 129 — A reveal/hide password field that keeps focus and text: cross-fade `SecureField` ⇄ `TextField` in a `ZStack`, never `if/else`

**Extracted from:** Passwordy (2026-06-23)

You want a password field with an eye button that toggles between masked (`SecureField`) and
plaintext (`TextField`). The obvious implementation swaps the two with a conditional:

```swift
// ❌ Drops focus and sometimes the text on every toggle.
if isRevealed {
    TextField(prompt, text: $text)
} else {
    SecureField(prompt, text: $text)
}
```

Each toggle **destroys one view and constructs the other**, so SwiftUI tears down the field that
had keyboard focus. The cursor jumps out, the user has to click back in, and on some macOS versions
the in-progress text resets. It feels broken every time you click the eye.

## Why it happens

`if/else` (and `.opacity` applied to a *single* conditionally-chosen field) changes **structural
identity**: SwiftUI sees "the SecureField is gone, here is a new TextField" and does a full
teardown/build. `@FocusState` is bound to a view that no longer exists, so focus is lost. A text
field's first-responder status and edit session live on the *identity* of the field — change the
identity and you lose them.

## The fix — both fields always exist; switch which one is visible/hittable

Keep **both** fields alive in a `ZStack` at all times. They share the same `$text` binding and the
same `@FocusState`. Toggling `isRevealed` only flips `.opacity` and `.allowsHitTesting` — neither
field is ever created or destroyed, so focus and text survive. Re-assert focus in `.onChange` so the
caret lands in the now-visible field.

```swift
struct RevealableSecureField: View {
    @Binding var text: String
    @Binding var isRevealed: Bool
    var prompt: String = ""

    @FocusState private var focused: Bool

    var body: some View {
        ZStack {
            // Masked: visible when NOT revealed.
            SecureField(prompt, text: $text)
                .textFieldStyle(.plain)
                .focused($focused)
                .opacity(isRevealed ? 0 : 1)
                .allowsHitTesting(!isRevealed)

            // Plaintext: visible when revealed.
            TextField(prompt, text: $text)
                .textFieldStyle(.plain)
                .focused($focused)
                .opacity(isRevealed ? 1 : 0)
                .allowsHitTesting(isRevealed)
        }
        .onChange(of: isRevealed) { _, _ in
            // Move the caret to the field that just became visible.
            if focused { focused = true }
        }
    }
}
```

Both fields bind the **same** `$text`, so typing in either is identical state. Only one is hittable
at a time (`allowsHitTesting`), so taps/clicks never reach the hidden one. The single `@FocusState`
is shared, so re-asserting `focused = true` after the toggle reattaches the caret without a click.

## Rules to internalize

- **Reveal/hide = visibility change, not a structural change.** Two persistent views cross-faded by
  `.opacity` keep identity; an `if/else` that picks one destroys identity (and focus, and sometimes
  text). This is the same identity rule as #98 — `.opacity` toggles preserve it, conditional view
  construction breaks it.
- **Gate hit-testing alongside opacity.** An `.opacity(0)` view still receives clicks; add
  `.allowsHitTesting(false)` to the hidden field so taps only reach the visible one.
- **Share one `@FocusState` across both fields and re-assert it on toggle** — that's what moves the
  caret to the newly-visible field without the user clicking back in.
- **Keep the eye button *outside* this view.** Letting the caller own `isRevealed` (and the eye
  glyph) keeps the field a pure, reusable control and lets a parent reset reveal-state per selection
  (e.g. via `.id(entry.id)` on the container — see #98).
- **Security pairing:** masking is the default; plaintext shows only while `isRevealed`. The field
  must never log its `text`. In read-only contexts you don't even need this control — a plain
  `Text("••••")` ⇄ `Text(value)` is enough; reach for this only for the *editable* secret field.

Source: Passwordy `01_Project/Passwordy/App/Vault/RevealableSecureField.swift`. Pairs with #98
(`.id`/identity controls view reuse), #00 (App Shell Standard), #130 (the unsaved-edits switch
prompt that drives this field's edit mode).
