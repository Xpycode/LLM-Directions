# #57 — Overriding `⌘W` (System Close Window) in SwiftUI macOS Apps

**Extracted from:** MyOwnTerminal (2026-04-25)

When a multi-tab/multi-pane macOS app needs `⌘W` to close the **active tab or pane** (not the whole window), the system default `File > Close Window` keeps stealing the shortcut whenever your replacement button is `.disabled`. The fix is `CommandGroup(replacing: .saveItem)` + a button that is **never** `.disabled` and handles all three cases internally (close pane → close tab → spawn fresh tab to keep window non-empty).

---

## Why naive approaches fail

### Approach 1 — `CommandMenu` with `.disabled` falls through

```swift
.commands {
    CommandMenu("View") {
        Button("Close Pane") { closePane() }
            .keyboardShortcut("w", modifiers: .command)
            .disabled(activeTab.panes.count <= 1)   // ← the trap
    }
}
```

When `count <= 1` the button is greyed-out — and SwiftUI **falls through to the system default**, which is `File > Close Window`. Result: `⌘W` closes the entire window when there's only one pane, but closes a pane when there are multiple. Confusing and wrong.

### Approach 2 — Conditional shortcut binding doesn't exist

There is no `if condition { .keyboardShortcut("w") }` — the shortcut is attached unconditionally to the menu item, and the system installs its own item if yours is unavailable.

### Approach 3 — Intercepting via `NSEvent` monitor

Works, but you're now bypassing the menu system, which means no menu indicator, no accessibility, no localization, and the standard `File > Close Window` item is still in the menu confusing users.

---

## The fix — replace the `.saveItem` group

```swift
struct AppCommands: Commands {
    var sessionManager: SessionManager
    @Binding var pendingCloseFromShortcut: Bool

    var body: some Commands {
        // Replace the entire File > Save/Close group so the system default
        // close-window can never inherit ⌘W when our button is unavailable.
        CommandGroup(replacing: .saveItem) {
            Button("Close") {
                if sessionManager.activeNeedsConfirmation {
                    pendingCloseFromShortcut = true
                } else {
                    sessionManager.closeActive()
                }
            }
            .keyboardShortcut("w", modifiers: .command)
            // NEVER .disabled — closeActive() handles every state.
        }
    }
}
```

Key invariant: **`closeActive()` always does something safe**, so the button is always enabled and never falls through.

```swift
extension SessionManager {
    func closeActive() {
        guard let tab = selectedTab else { return }

        // 1. If there's more than one pane, close just the active pane.
        if tab.panes.count > 1 {
            tab.removeActivePane()
            return
        }

        // 2. Otherwise close the whole tab.
        closeTab(tab.id)
        // ↑ closeTab itself handles "if this was the last tab, spawn a fresh one"
        //   so the WindowGroup never has zero tabs.
    }

    func closeTab(_ tabId: UUID) {
        guard let idx = tabs.firstIndex(where: { $0.id == tabId }) else { return }
        tabs.remove(at: idx)
        if tabs.isEmpty { addTab() }                         // invariant
        else if selectedTabId == tabId {
            selectedTabId = tabs[max(0, idx - 1)].id
        }
    }
}
```

---

## Wiring the confirmation dialog

`activeNeedsConfirmation` returns true if any session in the active pane/tab is `.running`. The shortcut sets a `Bool` binding; the `.confirmationDialog` lives at the app root:

```swift
@main
struct MyApp: App {
    @State private var sessionManager = SessionManager()
    @State private var pendingCloseFromShortcut: Bool = false

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environment(sessionManager)
                .confirmationDialog(
                    "A process is still running.",
                    isPresented: $pendingCloseFromShortcut,
                    titleVisibility: .visible
                ) {
                    Button("Close", role: .destructive) {
                        sessionManager.closeActive()
                    }
                    Button("Cancel", role: .cancel) {}
                }
        }
        .commands {
            AppCommands(
                sessionManager: sessionManager,
                pendingCloseFromShortcut: $pendingCloseFromShortcut
            )
        }
    }
}
```

Why `.confirmationDialog` not `NSAlert`: `NSAlert.runModal()` from a SwiftUI command can be invoked inside a transaction and Apple logs `[General] -[NSAlert runModal] may not be invoked inside of transaction begin/commit pair`. `.confirmationDialog` is the SwiftUI-native, transaction-safe equivalent.

---

## Why `.saveItem` and not `.singleWindow`?

The `CommandGroupPlacement` candidates for `⌘W` overrides:

| Placement | What it replaces | Verdict |
|-----------|------------------|---------|
| `.saveItem` | The Save/Save As/Close trio in File menu | ✅ correct — `Close` lives here |
| `.singleWindow` | Bring-to-front Window menu items | ❌ wrong menu |
| `.windowList` | Window menu list of open windows | ❌ wrong menu |
| `.newItem` | New File / New Window items | ❌ replaces wrong items |

Empirically: `.saveItem` is the only placement that wins over the system default `File > Close Window` for the ⌘W shortcut. Putting your Close button under any other group leaves the system default in the menu and you get **two** close items both bound to ⌘W (your button works, but the menu is confusing).

---

## "Never empty" invariant matters

If your `closeTab` doesn't auto-spawn a fresh tab when the last one is closed, the user can now `⌘W` themselves into a window with **zero tabs**. The WindowGroup keeps the window alive (it's not document-based), so the user sees an empty UI and has to manually click `+` to recover. Auto-spawning a blank tab matches Terminal.app and iTerm2 behavior.

Alternative: detect "last tab closed" and call `NSApp.keyWindow?.performClose(nil)` to close the actual window. Simpler in single-window apps; in multi-window apps (with detachable windows), you usually want auto-spawn so the main window persists while detached windows close themselves.

---

## When NOT to use this pattern

- **Document-based apps** (`DocumentGroup`) — ⌘W there really does mean "close this document window" and the system handling is correct.
- **Single-pane single-tab apps** — there's nothing to differentiate from "close window".
- **Apps where ⌘W should always close the window** — like a settings-style window. Don't override a shortcut just because you can.

---

## Composes with

- **#28 (commandgroup-observation)** — for menu items that need to display live state, e.g. "Close Tab \"foo\"" where `foo` updates from `@Observable`. Wrap your `Button` label as a `Text` reading the observed value.
- **#50 (detachable-windows)** — closing the last tab in a *detached* window can call `windowManager.closeDetachedWindow(_:)` instead of auto-spawning a tab, since detached windows are expected to close themselves.

---

## Quick checklist

- [ ] Use `CommandGroup(replacing: .saveItem)`, not `CommandMenu` or `.newItem`
- [ ] Button is **never** `.disabled` — `closeActive()` handles every state
- [ ] `closeTab` auto-spawns a fresh tab when last one is closed (or closes the window in detached-only apps)
- [ ] Confirmation goes through `@Binding<Bool>` + `.confirmationDialog`, not `NSAlert.runModal`
- [ ] Verify in running app: ⌘W with multiple panes closes pane; with one pane closes tab; with one tab spawns fresh tab (does not close window)
