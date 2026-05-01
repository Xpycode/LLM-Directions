# Pattern #50 — Detachable Windows (WindowGroup for UUID)

**Source project:** MyOwnTerminal  
**Best for:** Apps with tabs or items that users want to pop out into their own independent window — each with its own state manager.

---

## Problem

SwiftUI's `WindowGroup` shares a single `@State` environment across all instances. If you want detached windows that each own their own data (their own `SessionManager`, their own tab list), you need a second scene that accepts typed data and looks up the right manager.

## Solution

Use `WindowGroup(for: UUID.self)` as a second scene. A global `WindowManager` maps UUIDs → individual managers. When you call `openWindow(value: windowId)`, SwiftUI opens the typed scene and passes the UUID to the body closure.

---

## Code

### WindowManager.swift
```swift
import Foundation
import Observation

@Observable
final class WindowManager {
    var detachedWindows: [UUID: SessionManager] = [:]

    func detachSession(_ session: TerminalSession, from source: SessionManager) -> UUID {
        source.removeSession(session)            // move out of source (no cleanup)
        let newManager = SessionManager(existingSession: session)
        let windowId = UUID()
        detachedWindows[windowId] = newManager
        return windowId
    }

    func closeDetachedWindow(_ windowId: UUID) {
        detachedWindows.removeValue(forKey: windowId)
    }
}
```

### SessionManager — two extra members
```swift
// Move-out initializer (no new session created)
init(existingSession: TerminalSession) {
    sessions = [existingSession]
    selectedSessionId = existingSession.id
}

// Remove without closing (session stays alive, no cleanup)
func removeSession(_ session: TerminalSession) {
    guard let index = sessions.firstIndex(where: { $0.id == session.id }) else { return }
    sessions.remove(at: index)
    if selectedSessionId == session.id {
        selectedSessionId = sessions.isEmpty ? nil : sessions[max(0, index - 1)].id
    }
}
```

### MyOwnTerminalApp.swift — two scenes
```swift
@main
struct MyOwnTerminalApp: App {
    @State private var sessionManager = SessionManager()
    @State private var windowManager  = WindowManager()

    var body: some Scene {
        // Main window
        WindowGroup {
            ContentView()
                .environment(sessionManager)
                .environment(windowManager)
        }
        .windowStyle(.hiddenTitleBar)

        // Detached windows — each gets its own SessionManager
        WindowGroup(for: UUID.self) { $windowId in
            if let id = windowId,
               let manager = windowManager.detachedWindows[id] {
                ContentView()
                    .environment(manager)
                    .environment(windowManager)
            }
        }
        .windowStyle(.hiddenTitleBar)
    }
}
```

### Trigger from a context menu
```swift
// In SidebarView or TabItemView caller:
@Environment(WindowManager.self) var windowManager
@Environment(\.openWindow) var openWindow

// ...
Button("Move to New Window") {
    let windowId = windowManager.detachSession(session, from: manager)
    openWindow(value: windowId)
}
```

---

## Cross-window drag (bonus)

To drag a tab from one window's sidebar to another's, use SwiftUI `Transferable` carrying just the UUID:

```swift
// Declare a custom UTType
extension UTType {
    static let terminalSession = UTType(exportedAs: "com.myapp.terminal-session")
}

// Transfer wrapper (UUID only — the live object stays in memory)
struct SessionTransfer: Transferable, Codable {
    let sessionId: UUID
    static var transferRepresentation: some TransferRepresentation {
        CodableRepresentation(contentType: .terminalSession)
    }
}

// Drag source
TabItemView(...)
    .draggable(SessionTransfer(sessionId: session.id))

// Drop target (on the List in SidebarView)
List(...) { ... }
    .dropDestination(for: SessionTransfer.self) { items, _ in
        guard let transfer = items.first else { return false }
        let allManagers = [manager] + Array(windowManager.detachedWindows.values)
        for source in allManagers {
            if let s = source.sessions.first(where: { $0.id == transfer.sessionId }),
               source !== manager {
                source.removeSession(s)
                manager.sessions.append(s)
                manager.selectedSessionId = s.id
                return true
            }
        }
        return false
    }
```

**Note:** Add the UTType to `project.yml` under `info.properties`:
```yaml
UTExportedTypeDeclarations:
  - UTTypeIdentifier: com.myapp.terminal-session
    UTTypeDescription: MyApp Session
    UTTypeConformsTo:
      - public.data
```

Also: `Transferable`/`CodableRepresentation` live in CoreTransferable. Files that don't already `import SwiftUI` must add `import CoreTransferable` explicitly.

---

## Key gotchas

- `WindowGroup(for: UUID.self)` body receives `Binding<UUID?>` — always nil-check before lookup
- `@Environment(\.openWindow)` must be called from a View, not a service
- Do NOT use `closeSession` for moves — it clears state (rules engine buffers, etc.). Use `removeSession` which only removes from the array
- Each detached window shares the same `hudController` (HUD is app-global), but gets its own `SessionManager`
