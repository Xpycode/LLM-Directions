# 147 — A SwiftUI `.alert`/`.confirmationDialog`/`.sheet` attached to a **toolbar item** freezes the window; attach it to the content-view **body** instead

**Extracted from:** CompressPhotos (2026-06-30)

You add a toolbar button that should raise a confirmation. The natural-looking code hangs the button's
modifier right on the toolbar `Button`:

```swift
.toolbar {
    ToolbarItemGroup(placement: .navigation) {
        Button("Compress…") { showConfirm = true }
            .confirmationDialog("Run on the selected photo?", isPresented: $showConfirm) {  // ❌
                Button("Create + Verify") { runIt() }
                Button("Cancel", role: .cancel) {}
            }
    }
}
```

You click the button and **the whole window dims and stops responding** — but no dialog buttons ever
render. The app isn't crashed; it's stuck "presenting" a modal that has nowhere to draw. Pressing
Escape (or force-quit) is the only way out. The same thing happens with `.alert` and `.sheet`.

## Why it happens

`.alert` / `.confirmationDialog` / `.sheet` resolve their presentation against **the view they're
attached to**. A toolbar item does not live in the window's normal content hierarchy — it's hosted in
a separate context (the window's titlebar-accessory). So a modal anchored there enters the *presented*
state (which dims the content and captures input) but has no valid place in the content hierarchy to
lay out its chrome. Result: a live-but-invisible modal that soft-locks the window.

## The fix — toolbar button only mutates state; the presentation lives on the body

Move every presentation modifier down onto the main content view. The toolbar `Button` does nothing
but flip an `@State` flag:

```swift
@State private var showConfirm = false
@State private var resultMessage: String?

var body: some View {
    HSplitView { /* … real content … */ }
        .toolbar {
            ToolbarItemGroup(placement: .navigation) {
                Button("Compress…") { showConfirm = true }          // ✅ ONLY sets state
                    .disabled(selection.isEmpty)
            }
        }
        .toolbarRole(.editor)
        // Presentations on the BODY, not the toolbar item:
        .confirmationDialog("Run on the selected photo?", isPresented: $showConfirm,
                            titleVisibility: .visible) {
            Button("Create + Verify") { runIt() }
            Button("Cancel", role: .cancel) {}
        } message: {
            Text("Creates one copy and verifies it. Nothing is deleted.")
        }
        // A second, independent presentation for the result is fine — stack them:
        .alert("Result", isPresented: Binding(
            get: { resultMessage != nil },
            set: { if !$0 { resultMessage = nil } }
        )) {
            Button("OK", role: .cancel) { resultMessage = nil }
        } message: {
            Text(resultMessage ?? "")
        }
}
```

The button-sets-state / body-presents split is the load-bearing rule. It also keeps a clean separation:
toolbar items are *triggers*, the content view *owns* presentation. Stacking multiple presentation
modifiers on the body is fine as long as their `isPresented` bindings aren't both true at once
(here: confirm → run → result, strictly sequential).

## Rules to internalize

- **Never hang `.alert` / `.confirmationDialog` / `.sheet` / `.popover` off a `ToolbarItem` button.**
  The modal "presents" into a context with no content layout → window dims, input is captured, no
  buttons appear. It looks like a hang, not an error.
- **Toolbar buttons set state; the matching presentation modifier goes on the content body.** This is
  the reliable pattern on macOS (and avoids the same class of bug on iOS toolbars).
- **A spinner driven from a toolbar button is fine** — that's in-place content, not a presentation.
  Only the *presentation* modifiers misbehave from the toolbar.
- **Symptom → suspect:** "clicking a toolbar button dims the window and freezes input, no dialog" is
  almost always a presentation modifier on the wrong view. Move it to the body before debugging logic.

Source: CompressPhotos `01_Project/CompressPhotos/ContentView.swift` (DEBUG dry-run button + body-level
confirm/alert). Pairs with #00 (App Shell Standard — `.toolbarRole(.editor)`), #08 (keyboard shortcuts),
#71 (LSUIElement self-managed windows for when there is no content view to attach to).
