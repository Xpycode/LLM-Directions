# 130 — "You have unsaved changes" when clicking away mid-edit: intercept a `List(selection:)` switch by pinning the selection back, then commit after the dialog

**Extracted from:** Passwordy (2026-06-23)

A master/detail app edits the selected item in place. The user starts editing entry A, then clicks
entry B in the list **without saving**. You want the standard prompt: *Save / Discard / Cancel*,
where **Cancel keeps them on A still editing**. The problem: SwiftUI's `List(selection:)` has
**already changed** `selectedEntryID` to B by the time you find out, and if the detail view is keyed
`.id(selectedID)` it's already being torn down — the draft is gone before you can ask.

## Why it's awkward

`.onChange(of: selection)` fires **after** the binding flipped to B. There's no "selection will
change / return false to veto" hook like AppKit's `shouldSelect`. So you can't *prevent* the switch;
you can only *react* to it — which means the detail view for A may already be disappearing, taking
its `@State` draft with it.

## The fix — revert the selection synchronously, stash the target, prompt, then commit

Three pieces of state on the detail content (which is keyed `.id(entry.id)`, so it's per-selection):

```swift
@State private var draft: VaultEntry? = nil          // non-nil ⇒ editing
@State private var pendingSwitchID: UUID? = nil       // where the user tried to go
@State private var showUnsavedDialog = false

private var isEditing: Bool { draft != nil }
private var isDirty: Bool   { draft != nil && draft != entry }   // VaultEntry is Equatable
```

On selection change, if editing-and-dirty, **immediately write the selection back to the current
entry**. Because the binding is now pinned to A again, the `.id(A)` detail view is *not* torn down —
the draft survives — and you raise the dialog:

```swift
.onChange(of: browser.selectedEntryID) { _, newID in
    guard newID != entry.id else { return }            // ignore the revert we cause below
    if isEditing && isDirty {
        pendingSwitchID = newID                         // remember B
        browser.selectedEntryID = entry.id              // ← pin back to A (keeps this view alive)
        showUnsavedDialog = true
    } else if isEditing && !isDirty {
        draft = nil                                     // clean edit → let the switch through
    }
    // not editing → do nothing; parent re-resolves to B normally
}
```

The dialog resolves the stashed switch. `commitPendingSwitch()` is what finally moves to B:

```swift
.confirmationDialog("You have unsaved changes", isPresented: $showUnsavedDialog,
                    titleVisibility: .visible) {
    Button("Save") {
        guard let d = draft else { return }
        do { try manager.update(d); draft = nil; commitPendingSwitch() }
        catch { errorMessage = error.localizedDescription; pendingSwitchID = nil }  // abort switch on failure
    }
    Button("Discard Changes", role: .destructive) { draft = nil; commitPendingSwitch() }
    Button("Cancel", role: .cancel) { pendingSwitchID = nil }   // selection already reverted → stay on A
}

private func commitPendingSwitch() {
    if let id = pendingSwitchID { pendingSwitchID = nil; browser.selectedEntryID = id }
}
```

The `guard newID != entry.id else { return }` is load-bearing: writing the selection back to A
*re-fires* `.onChange`, and this guard swallows that echo so you don't recurse or re-prompt.

## Don't prompt on auto-lock / teardown — let the draft die silently

A password vault auto-locks on idle/sleep. **Do not** route that through this dialog — a modal that
blocks locking is a security hole. Locking clears the model and the parent swaps to the lock screen,
which tears this view down and **discards the draft for free**. No observer, no dialog:

```swift
// In the manager: lock() empties decodedEntries → ContentView shows LockView → detail view
// (and its @State draft) is deallocated. Unsaved secrets vanish with no user interaction.
```

## Rules to internalize

- **`onChange(of: selection)` is react-only — there's no veto.** Simulate a veto by **writing the
  selection back** synchronously, stashing the intended target, and committing it after the user
  decides.
- **Guard against the revert echo.** Re-assigning the selection re-triggers `onChange`; an early
  `guard newID != current` prevents recursion/double-prompts.
- **Pin-back only works if the detail view survives the pin.** Keying it `.id(currentID)` is
  compatible *because* the id doesn't change during editing (you keep reverting to it) — so the
  reveal-reset from #129/#98 and this prompt coexist. If you key on something that changes mid-edit,
  the view dies before you can prompt.
- **Distinguish dirty from merely-editing.** A clean edit (`draft == entry`) should let the switch
  through silently; only a real diff warrants the dialog. Make the model `Equatable` so `draft !=
  entry` is the dirty test.
- **Teardown paths (lock, quit, window close) must discard, never block.** Reserve the modal for
  *user-initiated* navigation; let lifecycle events drop the draft by deallocating the view.

Source: Passwordy `01_Project/Passwordy/App/Vault/EntryDetailView.swift` (`EntryDetailContent`).
Pairs with #129 (the focus-preserving secret field this edit mode drives), #98 (`.id`/identity and
view reuse), #00 (App Shell Standard).
