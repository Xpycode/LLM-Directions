# CommandGroup That Updates From `@Published`

**Use when:** a SwiftUI menu item needs to display live state from an `ObservableObject`
(e.g., "Current Temp: <volume>", "Project: <name>", enabled-based-on-selection), but
the naive `.commands { CommandGroup(...) }` approach doesn't refresh.

**Source:** `1-macOS/P2toMXF/` — `P2toMXFApp.swift`, `TempDirectoryManager.swift`.

---

## The problem

```swift
@main
struct MyApp: App {
    var body: some Scene {
        WindowGroup { ContentView() }
            .commands {
                CommandGroup(after: .newItem) {
                    // BUG: This Text ignores changes to MyManager.shared.currentValue.
                    Text("Current: \(MyManager.shared.currentValue)")
                    Divider()
                    Button("Change…") { /* ... */ }
                }
            }
    }
}
```

The button works, but the `Text` shows whatever `currentValue` was at app launch and
never updates when the user changes it via the button. Attempts to inject an
`@ObservedObject` or `@StateObject` at the App struct level don't propagate into the
closure — the commands closure is evaluated once.

This is a **known SwiftUI limitation** (Apple Developer Forums threads 667768,
671721). The `.commands` builder doesn't participate in the normal view-update graph
when its content reads from `ObservableObject` publishers declared outside itself.

## The pattern

Extract the commands into a dedicated `Commands`-conforming struct that owns its own
`@ObservedObject`. That struct IS a proper observation root, so published changes
propagate.

```swift
struct FileMenuCommands: Commands {
    @ObservedObject private var manager = MyManager.shared

    var body: some Commands {
        CommandGroup(after: .newItem) {
            // Informational status item (disabled buttons or Text render as greyed-out labels).
            Text("Current: \(manager.currentValue)")
            Divider()

            Button("Change…") {
                NotificationCenter.default.post(name: .changeValue, object: nil)
            }
            .keyboardShortcut("c", modifiers: [.command, .shift])

            Button("Reset") {
                manager.reset()
            }
            .disabled(!manager.hasCustomValue)  // Live-disables from published state.
        }
    }
}

@main
struct MyApp: App {
    var body: some Scene {
        WindowGroup { ContentView() }
            .commands {
                FileMenuCommands()
            }
    }
}
```

Now open the menu, change the value, open the menu again — the `Text` reflects the new
value, and `Reset` enables/disables correctly.

## Key requirements

- **`@ObservedObject`, not `@StateObject`** — the manager is a singleton you don't own;
  you're just observing it. `@StateObject` is for when the view creates and owns the
  object.
- **Don't inject into `.commands {}` closure** — pass the manager into the struct via
  `@ObservedObject` on the struct itself. The Commands struct, not the App, is the
  observation root.
- **`Text` and disabled `Button` both render as informational** — `Text(...)` inside a
  CommandGroup produces a non-interactive label item. `Button(...).disabled(true)`
  produces the same visual treatment but retains a button shape. Pick whichever feels
  right for the context; `Text` is visually lighter.

## Bridge to ContentView via NotificationCenter

A common pattern: menu actions need to trigger things inside `ContentView` (opening
an `NSOpenPanel`, showing a sheet, etc.) where the manager singleton doesn't live.
Use `NotificationCenter` as the bridge — the menu posts, the view listens.

```swift
// In Notification.Name extension:
static let chooseTempFolder = Notification.Name("chooseTempFolder")

// In the Commands struct:
Button("Temp Folder…") {
    NotificationCenter.default.post(name: .chooseTempFolder, object: nil)
}

// In ContentView body, alongside other modifiers:
.onReceive(NotificationCenter.default.publisher(for: .chooseTempFolder)) { _ in
    let panel = NSOpenPanel()
    // ... configure and run panel ...
}
```

The manager handles state mutation; the view handles UI presentation. The menu does
neither — it just announces the intent.

## When not to use this pattern

If the menu state is derived from something the ContentView already owns (e.g., the
currently-focused window's state), use the SwiftUI `.focusedSceneValue` API and the
matching `@FocusedValue` in the Commands struct — that's the system-sanctioned way to
pass per-window state into menus. The `@ObservedObject` on a Commands struct is for
**app-wide** singletons where focus isn't relevant.
