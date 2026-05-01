## Keyboard Shortcuts

Pro apps are keyboard-first. Four tiers from simplest to most advanced — pick the lightest tier that covers your needs.

---

### Tier 1: SwiftUI Commands (Menu-Bar Shortcuts)

**Source:** `VideoScout/VideoScoutApp.swift`, `Penumbra/App/PenumbraApp.swift`
**Use case:** Standard menu commands with keyboard accelerators (Cmd+I, Cmd+Shift+E, etc.)

```swift
struct AppCommands: Commands {
    @FocusedValue(\.actions) private var actions

    var body: some Commands {
        // Replace built-in menu items
        CommandGroup(replacing: .newItem) {
            Button("Import Videos…") {
                actions?.importVideos()
            }
            .keyboardShortcut("i")
            .disabled(actions == nil)
        }

        // Add a custom menu
        CommandMenu("Scan") {
            Button("Detect Shots") {
                actions?.detectShots()
            }
            .keyboardShortcut("d", modifiers: [.command, .shift])
            .disabled(!(actions?.canDetectShots ?? false))

            Divider()

            Button("Export as CSV…") {
                actions?.exportCSV()
            }
            .keyboardShortcut("e", modifiers: [.command, .shift])
        }
    }
}

// Wire into the app:
@main
struct MyApp: App {
    var body: some Scene {
        WindowGroup { ContentView() }
            .commands { AppCommands() }
    }
}
```

**FocusedValue pattern** for dispatching actions to the active view:

```swift
// Define the focused value key
struct ActionsKey: FocusedValueKey {
    typealias Value = AppActions
}

extension FocusedValues {
    var actions: AppActions? {
        get { self[ActionsKey.self] }
        set { self[ActionsKey.self] = newValue }
    }
}

// Protocol for actions any view can provide
protocol AppActions {
    func importVideos()
    func detectShots()
    func exportCSV()
    var canDetectShots: Bool { get }
}

// Publish from your view:
ContentView()
    .focusedValue(\.actions, viewModel)
```

**Best for:** Standard app commands that appear in the menu bar. Automatic discoverability (users see them in menus). Accessibility built-in.

---

### Tier 2: `.onKeyPress` (View-Level Keys, macOS 14+)

**Source:** `QuickMotion/ContentView.swift`, `VideoScout/Views/Content/ShotGridView.swift`
**Use case:** Keyboard-driven interaction within a specific view — JKL shuttle, arrow navigation, single-key triggers.

```swift
var body: some View {
    VStack(spacing: 0) {
        ViewerPane(player: player)
        TimelinePane(project: project)
    }
    .onKeyPress { keyPress in
        guard appState.hasVideo else { return .ignored }

        switch keyPress.characters {
        case "j", "J":
            appState.decreaseSpeed(big: keyPress.modifiers.contains(.shift))
            return .handled
        case "k", "K":
            appState.togglePlayPause()
            return .handled
        case "l", "L":
            appState.increaseSpeed(big: keyPress.modifiers.contains(.shift))
            return .handled
        case "i", "I":
            appState.setInPoint()
            return .handled
        case "o", "O":
            appState.setOutPoint()
            return .handled
        default:
            return .ignored
        }
    }
}
```

For arrow keys, use the typed overload:

```swift
.onKeyPress(.leftArrow) {
    navigateShot(direction: -1)
    return .handled
}
.onKeyPress(.rightArrow) {
    navigateShot(direction: 1)
    return .handled
}
.onKeyPress(.space) {
    togglePlayback()
    return .handled
}
```

**Key rules:**
- Return `.handled` to consume the key, `.ignored` to pass it through
- Respects text field focus automatically — if a text field is active, keys go there instead
- Modifier detection via `keyPress.modifiers.contains(.shift)` etc.
- Only fires when the view has focus — attach to the outermost content view

**Best for:** JKL shuttle controls, single-key triggers (I/O for in/out points), arrow navigation. Clean, modern, no setup/teardown.

---

### Tier 3: `NSEvent.addLocalMonitorForEvents` (App-Window Level)

**Source:** `Penumbra/KeyInputView.swift`, `VideoWallpaper/App/AppDelegate.swift`
**Use case:** Intercept keys across the entire app window, consume events to prevent system beeps, handle keyUp.

```swift
struct KeyInputView: NSViewRepresentable {
    static let eventMonitor = KeyboardEventMonitor()

    func makeNSView(context: Context) -> NSView {
        Self.eventMonitor.start()
        let view = NSView()
        view.frame = .zero
        return view
    }

    func updateNSView(_ nsView: NSView, context: Context) {}
}

class KeyboardEventMonitor {
    private var monitor: Any?

    func start() {
        monitor = NSEvent.addLocalMonitorForEvents(matching: [.keyDown, .keyUp]) { event in
            // Skip when text input is focused
            if let firstResponder = event.window?.firstResponder,
               firstResponder is NSTextView {
                return event  // pass through
            }

            if event.type == .keyDown {
                return self.handleKeyDown(event)
            } else if event.type == .keyUp {
                return self.handleKeyUp(event)
            }
            return event
        }
    }

    func stop() {
        if let monitor { NSEvent.removeMonitor(monitor) }
        self.monitor = nil
    }

    private func handleKeyDown(_ event: NSEvent) -> NSEvent? {
        let hasModifiers = !event.modifierFlags
            .intersection([.command, .control, .option]).isEmpty

        // Consume unmodified single-key shortcuts
        if !hasModifiers {
            switch event.keyCode {
            case 38:  // J
                NotificationCenter.default.post(name: .shuttleReverse, object: nil)
                return nil  // consume — no system beep
            case 40:  // K
                NotificationCenter.default.post(name: .shuttlePause, object: nil)
                return nil
            case 37:  // L
                NotificationCenter.default.post(name: .shuttleForward, object: nil)
                return nil
            default:
                break
            }
        }
        return event  // pass through
    }

    private func handleKeyUp(_ event: NSEvent) -> NSEvent? {
        // Handle key release (e.g., stop shuttle on J/L release)
        return event
    }
}

// Embed in your root view (invisible, zero-frame):
var body: some View {
    ZStack {
        KeyInputView()
        ContentView()
    }
}
```

**Key rules:**
- Return `nil` to consume the event (prevents system beep on unhandled keys)
- Return `event` to pass it through to the normal responder chain
- **Always guard for text field focus** — check `firstResponder is NSTextView`
- Clean up with `NSEvent.removeMonitor` in `applicationWillTerminate` or view disappear
- Only works when your app is focused (not system-wide)

**Best for:** Single-key shortcuts (J/K/L, Space, I/O) that must work anywhere in the app, not just in a specific view. Essential when you need to consume events to prevent beeps.

---

### Tier 4: Custom KeyboardShortcutManager (User-Customizable)

**Source:** `Penumbra/KeyboardShortcutManager.swift`
**Use case:** User-recordable shortcuts, centralized action dispatch, conflict detection.

```swift
final class KeyboardShortcutManager {
    static let shared = KeyboardShortcutManager()

    var isRecordingShortcut = false
    private var keysPressed: Set<UInt16> = []

    // User-configurable shortcut storage
    private let shortcutSettings = ShortcutSettings.shared

    func handleKeyDown(with event: NSEvent) {
        guard !isRecordingShortcut else { return }
        guard !event.isARepeat else { return }

        keysPressed.insert(event.keyCode)

        let modifiers = event.modifierFlags
            .intersection([.command, .option, .control, .shift])
        let keyCode = Int(event.keyCode)

        // Match against user-configured shortcuts
        for (action, shortcut) in shortcutSettings.shortcuts {
            if shortcut.keyCode == keyCode &&
               shortcut.modifiers.rawValue == modifiers.rawValue {
                perform(action)
                return
            }
        }
    }

    func handleKeyUp(with event: NSEvent) {
        keysPressed.remove(event.keyCode)
    }

    private func perform(_ action: ShortcutAction) {
        switch action {
        case .stepForward1:
            NotificationCenter.default.post(name: .playerStepFrames, object: 1)
        case .stepForward10:
            NotificationCenter.default.post(name: .playerStepFrames, object: 10)
        case .stepBackward1:
            NotificationCenter.default.post(name: .playerStepFrames, object: -1)
        case .markIn:
            NotificationCenter.default.post(name: .playerMarkInPoint, object: nil)
        case .markOut:
            NotificationCenter.default.post(name: .playerMarkOutPoint, object: nil)
        case .togglePlay:
            NotificationCenter.default.post(name: .playerTogglePlay, object: nil)
        // ... more actions
        }
    }
}
```

**ShortcutSettings** for persistence and a settings UI:

```swift
@Observable
class ShortcutSettings {
    static let shared = ShortcutSettings()

    struct Shortcut: Codable, Equatable {
        var keyCode: Int
        var modifiers: NSEvent.ModifierFlags

        var displayString: String {
            var parts: [String] = []
            if modifiers.contains(.control) { parts.append("⌃") }
            if modifiers.contains(.option) { parts.append("⌥") }
            if modifiers.contains(.shift) { parts.append("⇧") }
            if modifiers.contains(.command) { parts.append("⌘") }
            parts.append(Self.keyCodeToString(keyCode))
            return parts.joined()
        }
    }

    // Persisted via UserDefaults or JSON file
    var shortcuts: [ShortcutAction: Shortcut] = [:]

    func setShortcut(_ shortcut: Shortcut, for action: ShortcutAction) {
        // Check for conflicts
        if let conflict = shortcuts.first(where: {
            $0.key != action && $0.value == shortcut
        }) {
            // Remove conflicting binding
            shortcuts[conflict.key] = nil
        }
        shortcuts[action] = shortcut
        save()
    }
}
```

**Wiring:** Tier 4 sits on top of Tier 3 — the `KeyInputView` event monitor calls `KeyboardShortcutManager.shared.handleKeyDown(with:)` instead of handling keys directly.

**Best for:** Pro apps where users expect to customize every shortcut (video editors, DAWs). Adds complexity — only use when you genuinely need user-configurable bindings.

---

### Choosing a Tier

| Need | Tier | Example |
|---|---|---|
| Standard menu commands (Cmd+S, Cmd+I) | **1: Commands** | Import, Export, Settings |
| View-specific keys, modern API | **2: `.onKeyPress`** | Arrow nav in a grid, JKL in viewer |
| App-wide single keys, must consume events | **3: Local Monitor** | Space for play/pause, J/K/L anywhere |
| User-customizable, recordable shortcuts | **4: Custom Manager** | Penumbra-style shortcut prefs |

**Combine tiers:** Most pro apps use Tier 1 for menu commands + Tier 3 for single-key shortcuts. Tier 4 only if you ship a shortcut editor in preferences.

---

