# Closure-bridged AppKit from a model-layer `@MainActor` ObservableObject

**Source:** `1-macOS/_Published/syncthingStatus/` — `Client.swift::StuckDeletesController` + `App.swift::StuckDeletesWindowController` (2026-04-29, v1.6.0).

When a SwiftUI view bound to an `ObservableObject` controller needs to **trigger AppKit behaviour** (close the hosting window, open a System Settings deep-link, reveal in Finder, present an `NSAlert`), the obvious move is to make the controller hold an AppKit reference:

```swift
@MainActor
final class MyController: ObservableObject {
    weak var window: NSWindow?            // ⚠️ forces `import AppKit`
    weak var workspace: NSWorkspace?      // ⚠️ same
    func close() { window?.close() }
}
```

That works, but it bleeds AppKit into your model layer — a file like `Client.swift` that was happily importing only `Foundation`/`Combine` now needs `import AppKit`, and any UI primitive becomes a transitive dependency of every consumer of the controller.

Fix: inject closures from the window controller (or whichever AppKit object owns the view), set them after `super.init` completes.

```swift
@MainActor
final class StuckDeletesController: ObservableObject {
    // No AppKit types in the controller's interface.
    var dismissAction: (() -> Void)?
    var openFDASettingsAction: (() -> Void)?

    func close()              { dismissAction?() }
    func openFDASettings()    { openFDASettingsAction?() }
}

final class StuckDeletesWindowController: NSWindowController {
    init(folder: SyncthingFolder, syncthingClient: SyncthingClient) {
        let stuckController = StuckDeletesController(folder: folder, client: syncthingClient)
        let view = StuckDeletesView(controller: stuckController)
        let window = NSWindow(...)
        window.contentView = NSHostingView(rootView: view)
        super.init(window: window)

        // Wire AppKit-touching closures *after* super.init. Weak `window`
        // capture in `dismissAction` avoids a retain cycle.
        stuckController.dismissAction = { [weak window] in
            window?.close()
        }
        stuckController.openFDASettingsAction = {
            if let url = URL(string: "x-apple.systempreferences:com.apple.preference.security?Privacy_AllFiles") {
                NSWorkspace.shared.open(url)
            }
        }
    }

    @available(*, unavailable)
    required init?(coder: NSCoder) { fatalError("init(coder:) not supported") }
}
```

The view calls `controller.close()` / `controller.openFDASettings()` — same call site as the AppKit-coupled version, but the controller's *file* never imports AppKit.

---

## Why this matters more than aesthetics

- **Compile-time enforcement of layer boundaries.** A model file that imports only `Foundation` *cannot* accidentally call `NSWorkspace`, `NSAlert`, or `NSWindow` APIs. The next time someone adds a feature to the controller, the path of least resistance is to extend the closure surface, not reach for AppKit directly.
- **Testability.** Stubbing `NSWindow` in unit tests is awkward; assigning a closure that records calls is trivial:
  ```swift
  var dismissed = false
  controller.dismissAction = { dismissed = true }
  controller.close()
  XCTAssertTrue(dismissed)
  ```
- **Cross-platform potential.** If the model layer is ever shared with iOS or a CLI, the closures simply remain `nil` (the `?.()` calls become no-ops); without closures, every AppKit symbol becomes a `#if os(macOS)` fence.

---

## When to reach for this

- Controller is an `ObservableObject` consumed by SwiftUI but lives in a **non-UI file** (`Client.swift`, `Models.swift`, networking layer).
- The action it needs to trigger is **owned by an outer AppKit object** — a window, the system workspace, NSAlert presentation, an NSSavePanel.
- You don't want consumers of the controller to need `import AppKit` either (e.g., your view's preview block uses a fake controller).

---

## When NOT to reach for it

- The controller is *already* AppKit-coupled because it bridges to `NSTableView`/`NSCollectionView` data sources. Adding closures on top of an existing AppKit dependency is just ceremony.
- The action is purely SwiftUI (e.g., dismiss a sheet via `@Environment(\.dismiss)`) — let the View handle it directly with no controller involvement.

---

## Companion patterns

- **#19 swift6-concurrency** (`@MainActor` + `@Observable`): the closures are called on the main actor, matching the controller's actor isolation. No bridging dance.
- **#28 commandgroup-observation**: similar shape — model-layer state drives AppKit/SwiftUI behaviour without the model holding AppKit refs.

---

*Drafted 2026-04-29 from refactoring `weak var window: NSWindow?` out of `StuckDeletesController` after the field forced `import AppKit` into `Client.swift`. The closure form took 8 lines of boilerplate in the window controller and removed an entire framework dependency from the networking file.*
