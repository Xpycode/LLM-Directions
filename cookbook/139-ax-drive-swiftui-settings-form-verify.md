## Drive & verify a SwiftUI Settings Form headlessly via the Accessibility API

**Source:** SearchAway — `docs/verification/settings_forms_harness.swift` (AX-driven, asserts against `scopes.json` / `saved-searches.json`). Companion to the CGEvent HUD driver `bugD_harness.swift` / `ac5_harness.swift` (#73). Added 2026-06-28.

**Use case:** You want to *prove*, in the real shipped build, that a SwiftUI Settings **Form** works — an add-rule form writes the right row to disk, a "New → Save" form persists the right record. A single text field (a HUD search bar) is drivable with blind `CGEventPost` keystrokes (#73), but a **Form is a tree of buttons + fields** where Tab order is unreliable and there's no obvious place to click. The robust approach: locate controls by role+title via the **Accessibility API** (`AXUIElement`) and press them; enter text by AX-focusing the field then pasting; and use the **on-disk JSON the form writes** as the oracle. The host process just needs Accessibility trust (the same trust that lets you `CGEventPost` — a terminal running the harness usually has it).

### The four traps (each one silently makes the test pass-looking but wrong)

**1. Focus the `TextField` via `kAXFocusedAttribute`, NOT a computed-coordinate click.** Clicking at the element's AX frame centre missed and focused a *button* instead (`focusedRole == "AXButton"`), so the subsequent paste went nowhere and the field stayed empty. Setting `kAXFocusedAttribute = true` on the field element makes it first responder reliably:

```swift
AXUIElementSetAttributeValue(field, kAXFocusedAttribute as CFString, kCFBooleanTrue)
// then verify it took, fall back to a click only if it didn't:
if focusedRole() != "AXTextField" { _ = clickElement(field) }
```

**2. Enter text by PASTING, never by setting `kAXValueAttribute`.** A direct `AXUIElementSetAttributeValue(field, kAXValueAttribute, "x")` makes the field's AX value *read back* as the text while SwiftUI's `@State` binding stays empty — so the field **looks** filled but the submit button stays **disabled** and the save is a no-op. Only a real paste keystroke (`Cmd-V` to the focused field) drives the binding:

```swift
func pasteText(_ s: String) {
    let pb = NSPasteboard.general
    pb.clearContents(); pb.setString(s, forType: .string); usleep(40_000)
    post(0, flags: .maskCommand)   // Cmd-A (clear any existing)
    post(9, flags: .maskCommand)   // Cmd-V
}
```

**3. Assert success on the submit button's ENABLED state, not the field's AX value.** Because of trap #2, the field's `AXValue` is a liar. The trustworthy signal that the binding actually updated is `kAXEnabledAttribute` on the "Add" / "Save" button (these forms gate the button on `!field.trimmed.isEmpty`). Check it before pressing — if it's still `false`, your text never reached the binding:

```swift
let addEnabled = button(exact: "Add").map { axCopy($0, kAXEnabledAttribute as String) as? Bool ?? false } ?? false
```

**4. Match buttons by `AXDescription` too, not only `AXTitle`.** A SwiftUI `Button { Label("Add", …) }.buttonStyle(.plain)` often exposes its label via **`AXDescription`** with a *nil* `AXTitle` — so a title-only search finds nothing while the button is right there. Match either, and use **exact** match for short labels (`"Add"`) so a `contains` doesn't also grab `"Add Rule"`:

```swift
func button(exact title: String) -> AXUIElement? {
    allControls().first {
        axRole($0) == "AXButton" &&
        (axStr($0, kAXTitleAttribute as String) == title || axStr($0, kAXDescriptionAttribute as String) == title)
    }
}
```

### The AX toolkit (reusable across any SwiftUI macOS app)

```swift
import Cocoa
import ApplicationServices

var appEl: AXUIElement!   // AXUIElementCreateApplication(pid)

func axCopy(_ el: AXUIElement, _ attr: String) -> AnyObject? {
    var v: AnyObject?
    return AXUIElementCopyAttributeValue(el, attr as CFString, &v) == .success ? v : nil
}
func axStr(_ el: AXUIElement, _ a: String) -> String? { axCopy(el, a) as? String }
func axRole(_ el: AXUIElement) -> String { axStr(el, kAXRoleAttribute as String) ?? "" }
func axChildren(_ el: AXUIElement) -> [AXUIElement] { (axCopy(el, kAXChildrenAttribute as String) as? [AXUIElement]) ?? [] }
func axDescendants(_ el: AXUIElement, _ d: Int = 0) -> [AXUIElement] {
    guard d < 60 else { return [] }
    return [el] + axChildren(el).flatMap { axDescendants($0, d + 1) }
}
func allControls() -> [AXUIElement] {
    ((axCopy(appEl, kAXWindowsAttribute as String) as? [AXUIElement]) ?? []).flatMap { axDescendants($0) }
}
func axPress(_ el: AXUIElement) -> Bool { AXUIElementPerformAction(el, kAXPressAction as CFString) == .success }
func focusedRole() -> String { axCopy(appEl, kAXFocusedUIElementAttribute as String).map { axRole($0 as! AXUIElement) } ?? "none" }
func textFields() -> [AXUIElement] { allControls().filter { axRole($0) == "AXTextField" } }
```

```swift
appEl = AXUIElementCreateApplication(app.processIdentifier)
// Some SwiftUI apps only expose a full AX tree once this is set:
AXUIElementSetAttributeValue(appEl, "AXManualAccessibility" as CFString, kCFBooleanTrue)
```

### Shape of the whole flow

1. Launch the **Release** binary via `Process` (keep the handle so you can `terminate()`); `AXUIElementCreateApplication(pid)`; set `AXManualAccessibility`.
2. Open Settings the way the app does — for an `LSUIElement` HUD app (#71) there's no menu bar, so summon the HUD (global hotkey) then `Cmd-,` (keycode 43). Confirm you reached it by finding a known control (`button(contains: "Add Rule")`).
3. `axPress` the button that reveals the inline form → sleep for the SwiftUI re-render → grab the new `AXTextField`(s). For multiple fields, match by `kAXPlaceholderValueAttribute` (`"Name"` vs `"Query"`), falling back to tree order.
4. For each field: AX-focus → `pasteText`. Then assert the submit button is **enabled**.
5. `axPress` submit → sleep for the async `Task { try? await store.persist() }` → read the JSON file and assert the new row's exact shape (`kind`/`ruleType`/`isDefault`, or `name`/`queryText`).
6. **Back up the store files to `/tmp` before, restore after** (and on every early-exit path) — the forms write to the user's real `~/Library/Application Support/<bundle-id>/` data.

### Why JSON-as-oracle beats screenshotting

The form's whole job is to write a record; reading that record back is a precise, fast, deterministic check that needs no Screen-Recording permission and no pixel diffing. It also catches the field/binding mismatch (trap #2) that a screenshot would miss — a screenshot of a filled field tells you nothing about whether `Save` actually persisted.

**Pairs with #73** (drive a HUD / `LSUIElement` app from a sandboxed shell — the CGEvent half of the same verification family), **#111** (the hotkey-recorder field these forms sit beside — a `TextField` whose `AXValue` you'd similarly mistrust), **#71** (the self-managed `LSUIElement` Settings window being driven), **#138** (rebuild **Release** before verifying — drive the binary the user runs, not a Debug build), **#65** (the cursor-anchored panel that summons Settings), **#00** (App Shell Standard / `Theme`).
