# 87 — Insert a token at the caret of a SwiftUI text field (wrap `NSTextField`, restore caret across the binding bounce)

**Problem.** A token/pattern editor — rename-pattern field, snippet editor, template builder — has buttons that should insert `{date}`, `:emoji:`, `${var}` **at the text caret**, replacing any selection, then leave focus + caret right after the inserted token so the user keeps typing. SwiftUI's `TextField` makes this impossible: it exposes **neither the selection range nor the field editor**, so a button can only append to the end (`text += token`) — which drops the token in the wrong place and blows away the user's cursor. The handoff for Conjoyn's "Rename Joined Files" popover specified true caret insertion; SwiftUI alone can't do it.

## Pattern — `NSViewRepresentable` over `NSTextField` + a controller that owns the field editor

Drop to AppKit for the one field. An `NSTextField`'s **field editor** (`currentEditor()`, an `NSText`) carries `selectedRange` — that's the caret. Wrap the field in `NSViewRepresentable`, register it with a small `ObservableObject` controller, and route every token tap through `controller.insert(_:)`. Two non-obvious bits make it actually work: **read the selection from the live field editor** (not from a SwiftUI `@State`, which lags), and **restore the caret on the *next* runloop tick** because pushing the new string back through the SwiftUI `Binding` re-sets `stringValue` and parks the caret at the end.

```swift
/// Bridges a SwiftUI button tap into the NSTextField's live caret. Replaces the current
/// selection with `token`, then restores focus + caret after it. Appends when unfocused.
final class CaretFieldController: ObservableObject {
    fileprivate weak var textField: NSTextField?

    func insert(_ token: String, currentText: String, set: (String) -> Void) {
        guard let textField else { set(currentText + token); return }   // not yet made

        let ns = currentText as NSString
        // Selection from the FIELD EDITOR when focused; else append at the end.
        let sel = textField.currentEditor()?.selectedRange
            ?? NSRange(location: ns.length, length: 0)
        let newText = ns.replacingCharacters(in: sel, with: token)
        let caret = sel.location + (token as NSString).length

        set(newText)   // push through the SwiftUI Binding (parks caret at end)
        // Restore focus + caret NEXT tick, after SwiftUI has re-applied stringValue.
        DispatchQueue.main.async { [weak textField] in
            guard let textField else { return }
            textField.window?.makeFirstResponder(textField)
            textField.currentEditor()?.selectedRange = NSRange(location: caret, length: 0)
        }
    }
}

struct CaretTextField: NSViewRepresentable {
    @Binding var text: String
    let controller: CaretFieldController
    let font: NSFont

    func makeNSView(context: Context) -> NSTextField {
        let f = NSTextField(string: text)
        f.delegate = context.coordinator
        f.font = font
        f.isBordered = false; f.drawsBackground = false; f.focusRingType = .none
        f.usesSingleLineMode = true; f.cell?.wraps = false; f.cell?.isScrollable = true
        controller.textField = f                    // register for insert()
        return f
    }

    func updateNSView(_ v: NSTextField, context: Context) {
        if v.stringValue != text { v.stringValue = text }   // guard: don't fight live typing
        v.font = font
        controller.textField = v
    }

    func makeCoordinator() -> Coordinator { Coordinator(self) }

    final class Coordinator: NSObject, NSTextFieldDelegate {
        private let parent: CaretTextField
        init(_ parent: CaretTextField) { self.parent = parent }
        func controlTextDidChange(_ n: Notification) {            // user typing → binding
            (n.object as? NSTextField).map { parent.text = $0.stringValue }
        }
    }
}
```

Use it: a `@StateObject var caret = CaretFieldController()`, the field as `CaretTextField(text: $pattern, controller: caret, font: .monospacedSystemFont(ofSize: 12, weight: .regular))`, and each token button as `caret.insert("{date}", currentText: pattern) { pattern = $0 }`.

## Why each piece

- **Selection from `currentEditor()`, not a cached `@State` range.** SwiftUI state is a tick behind the live caret; only the field editor knows where the cursor *is right now*. When the field isn't first responder there's no editor, so default to end-of-string = append (matches the JS `else` fallback the design came from).
- **`set(newText)` then restore caret async.** Writing the binding makes SwiftUI call `updateNSView`, which sets `stringValue` and drops the caret to the end. You can't pre-empt that synchronously — so make-first-responder + set `selectedRange` on the next `DispatchQueue.main.async` tick, after the bounce. (This is the AppKit analogue of the JS `requestAnimationFrame(() => el.setSelectionRange(...))` the handoff used.)
- **`updateNSView` guards `stringValue != text`.** Without it, every keystroke's binding update re-assigns `stringValue` mid-edit and fights the user (caret jumps, characters drop).
- **A controller object, not a `@Binding` selection.** The token buttons live in SwiftUI but the caret lives in AppKit; an `ObservableObject` holding a `weak var textField` is the clean seam — no `Coordinator` plumbing leaks into the parent view, and `weak` avoids a retain cycle with the representable.

## Gotchas

- Field editor is **shared per window** — `currentEditor()` is non-nil only while the field is first responder. Always handle the nil (unfocused) case.
- Use `NSString` for ranges — `selectedRange` is UTF-16; bridging through `String.Index` for a known-ASCII token is needless and breaks on emoji tokens.
- `makeFirstResponder` then set `selectedRange` (in that order) — selecting before the field is key window silently no-ops.
- Single-line: set `usesSingleLineMode` + `cell?.isScrollable` or a long pattern wraps/clips oddly inside the SwiftUI frame.

**Best for:** a SwiftUI text field that needs insert-token-at-cursor buttons (pattern/template/snippet/mention editors) — anywhere you need the caret or selection that `TextField` won't give you. Source: Conjoyn `Views/RenamePopover.swift` (`CaretTextField` + `CaretFieldController`). Pairs with the design-token reskin (#39) and native-control-in-popover patterns.
