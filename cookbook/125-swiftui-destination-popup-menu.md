# SwiftUI "destination popup" — a `Menu` (not `Picker`) as a save-location chooser with a default + a "Choose…" escape hatch

**Tags:** SwiftUI Menu vs Picker, NSOpenPanel, save destination, gridColumnAlignment, Menu fitting size, checkmark Label, truncationMode

**Source:** VideoContainerSwitcher — `01_Project/VideoContainerSwitcher/Views/FileQueueView.swift` (`OutputDestinationMenu`) + its `GridRow` in `ContentView.swift` (2026-06-21).

You have a setting that is **"a sensible default, OR a thing the user picks from a file panel"** — an output folder ("Same as input" / a chosen directory), a save location, a target device, an account. The naïve UI is three controls fighting over one piece of state: a read-only field showing the current value, a checkbox for the default, and a `Browse…` button. That's redundant — the field already shows "Same as input", so the checkbox restates it, and the button is a fourth thing to align. Collapse all of it into **one popup menu whose label IS the current choice** — the native macOS save-location idiom (Screenshot.app's "Save to", export sheets).

**The whole pattern:**

```swift
/// One inline popup replacing a read-only field + a "use default" checkbox + a Browse button.
struct OutputDestinationMenu: View {
    @Environment(RemuxViewModel.self) private var vm

    var body: some View {
        Menu {
            menuItem("Same as input", active: vm.sameAsInput) {
                vm.sameAsInput = true
            }
            if let dir = vm.outputDirectory {            // a previously-picked folder, if any
                Divider()
                menuItem(dir.lastPathComponent, active: !vm.sameAsInput) {
                    vm.sameAsInput = false
                }
            }
            Divider()
            Button("Choose folder…") { vm.chooseOutputDirectory() }   // ← the escape hatch: opens NSOpenPanel
        } label: {
            Text(displayText)                            // the label IS the current choice
                .foregroundColor(vm.sameAsInput ? Theme.secondaryText : Theme.primaryText)
                .lineLimit(1)
                .truncationMode(.middle)
                .frame(maxWidth: .infinity, alignment: .leading)   // ← see gotcha 2
        }
        .disabled(vm.isConverting)
    }

    /// A menu row that shows a checkmark only when it's the active choice (gotcha 3).
    @ViewBuilder
    private func menuItem(_ title: String, active: Bool, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            if active { Label(title, systemImage: "checkmark") }
            else      { Text(title) }
        }
    }

    private var displayText: String {
        if vm.sameAsInput { return "Same as input" }
        return vm.outputDirectory?.path ?? "Choose a folder…"
    }
}
```

`chooseFolder` is the usual `NSOpenPanel` (`canChooseDirectories = true`); on `.OK` it sets `outputDirectory` **and** flips the default off (`sameAsInput = false`) so picking a folder implies you want it. State is unchanged from the old 3-control version — the menu only removes UI surfaces, it doesn't add model state.

In the `Grid`, span the column and pin it left (gotcha 2):

```swift
GridRow {
    label("Output to:")
    OutputDestinationMenu()
        .frame(maxWidth: .infinity, alignment: .leading)
        .gridColumnAlignment(.leading)
}
```

**Gotchas**

- **Use `Menu`, not `Picker` — this is the whole reason.** A `Picker` binds its selection to a *fixed* option set; it cannot host an action item that opens an `NSOpenPanel`. A `Menu` is just a container of `Button`s, so "Choose folder…" can run arbitrary code (open the panel, then update state). If your chooser only ever picks from a static list, a `Picker` is fine — the moment one option means "go get something from outside the list," you need `Menu`.
- **A `Menu` reports a *fitting* (content) size, so in a `Grid`/`HStack` it gets centered and shrunk** to its label width — it looks like it's floating mid-row instead of filling the cell. A sibling with a greedy background (a `RoundedRectangle` fill) fills the column and makes the menu look even more orphaned. Fix: `.frame(maxWidth: .infinity, alignment: .leading)` on the **`Menu`** (not just its label) + `.gridColumnAlignment(.leading)` on the cell. Putting `maxWidth: .infinity` only on the inner label `Text` does **not** stretch the popup.
- **You lose `Picker`'s automatic checkmark.** A `Menu` of `Button`s shows no "current selection" tick. Render it yourself: `Label(title, systemImage: "checkmark")` on the active row, plain `Text(title)` on the rest — the `@ViewBuilder` helper above keeps that one-lining. Don't pass an empty `systemImage: ""` to fake alignment; branch the view instead.
- **Truncate the label, middle-style, for paths.** A chosen folder path can be long; `.lineLimit(1).truncationMode(.middle)` keeps the popup from blowing out the row while still showing the meaningful tail.
- **Decide the "unpick the default" UX deliberately.** Here, picking a folder auto-unsets the default and there's no explicit "clear" — the menu's "Same as input" row *is* the way back. If you need a third state (no choice yet), add a disabled/placeholder label rather than leaving the menu showing a stale path.

**Best for:** a settings control that is "a good default plus an escape-hatch picker" — output/save folders, export destinations, a target device/printer/account, "default vs custom" anything — on macOS, where the native feel is a popup whose label is the live value. Collapses field+checkbox+Browse into one control and removes a form row. Pairs with **#05** (the `NSOpenPanel`/`NSSavePanel` the "Choose…" item drives), **#03** (`NSPopUpButton` if you'd rather drop to AppKit), **#70** (data-driven control strips in the same form), **#00** (App Shell `Theme`/form context).
