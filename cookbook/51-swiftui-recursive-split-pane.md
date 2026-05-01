# Pattern #51 — SwiftUI Recursive Split Pane

**Source project:** MyOwnTerminal  
**Best for:** Terminal emulators, code editors, or any app needing user-resizable H/V split layouts with arbitrary nesting depth.

---

## Problem

SwiftUI has no built-in recursive split pane. You need a tree data model that can represent arbitrary nesting and a view that renders itself recursively — but `switch` statements directly in `body` confuse the Swift compiler's result builder.

## Solution

1. `indirect enum SplitNode` — value-type tree (copy-on-write safe)  
2. `SplitPaneView` with a `@ViewBuilder` helper to satisfy the result builder  
3. `HSplitView`/`VSplitView` for AppKit-backed drag-to-resize (free, native)

---

## Code

### SplitNode.swift
```swift
import Foundation

enum SplitDirection {
    case horizontal  // side by side — HSplitView
    case vertical    // stacked — VSplitView
}

indirect enum SplitNode {
    case leaf(YourSession)                                           // terminal/editor pane
    case split(SplitNode, SplitNode, direction: SplitDirection, ratio: CGFloat)
}

extension SplitNode {
    var sessions: [YourSession] {
        switch self {
        case .leaf(let s): return [s]
        case .split(let a, let b, _, _): return a.sessions + b.sessions
        }
    }

    // Split the leaf that owns targetId; new session goes to the right/bottom
    func inserting(newSession: YourSession, splitting targetId: UUID, direction: SplitDirection) -> SplitNode {
        switch self {
        case .leaf(let s):
            return s.id == targetId
                ? .split(self, .leaf(newSession), direction: direction, ratio: 0.5)
                : self
        case .split(let a, let b, let dir, let ratio):
            return .split(
                a.inserting(newSession: newSession, splitting: targetId, direction: direction),
                b.inserting(newSession: newSession, splitting: targetId, direction: direction),
                direction: dir, ratio: ratio
            )
        }
    }

    // Remove a leaf; collapses branch when one child is removed
    func removing(sessionId: UUID) -> SplitNode? {
        switch self {
        case .leaf(let s):
            return s.id == sessionId ? nil : self
        case .split(let a, let b, let dir, let ratio):
            switch (a.removing(sessionId: sessionId), b.removing(sessionId: sessionId)) {
            case (nil, let n?): return n
            case (let n?, nil): return n
            case (let a?, let b?): return .split(a, b, direction: dir, ratio: ratio)
            case (nil, nil): return nil
            }
        }
    }
}
```

### SplitPaneView.swift
```swift
import SwiftUI

struct SplitPaneView: View {
    var node: SplitNode
    @Bindable var manager: YourManager   // owns selectedSessionId + splitRoot

    var body: some View {
        content()                        // switch goes in @ViewBuilder helper, not body
    }

    @ViewBuilder
    private func content() -> some View {
        switch node {
        case .leaf(let session):
            leafView(session: session)
        case .split(let a, let b, let direction, _):
            if direction == .horizontal {
                HSplitView {
                    SplitPaneView(node: a, manager: manager)
                    SplitPaneView(node: b, manager: manager)
                }
            } else {
                VSplitView {
                    SplitPaneView(node: a, manager: manager)
                    SplitPaneView(node: b, manager: manager)
                }
            }
        }
    }

    @ViewBuilder
    private func leafView(session: YourSession) -> some View {
        let isActive = manager.selectedSessionId == session.id
        ZStack(alignment: .topLeading) {
            YourContentView(session: session)
                .id(session.id)                  // forces view identity on session swap
            if isActive {
                // 1px accent border — does not intercept input
                RoundedRectangle(cornerRadius: 0)
                    .stroke(Color.accentColor.opacity(0.4), lineWidth: 1)
                    .allowsHitTesting(false)
            }
        }
        .contentShape(Rectangle())
        .onTapGesture { manager.selectedSessionId = session.id }
    }
}
```

### SessionManager — split operations
```swift
@Observable final class YourManager {
    var sessions: [YourSession] = []
    var selectedSessionId: UUID?
    var splitRoot: SplitNode

    init() {
        let initial = YourSession()
        sessions = [initial]
        selectedSessionId = initial.id
        splitRoot = .leaf(initial)
    }

    func splitActive(direction: SplitDirection) {
        guard let activeId = selectedSessionId else { return }
        let newSession = YourSession()
        sessions.append(newSession)
        splitRoot = splitRoot.inserting(newSession: newSession, splitting: activeId, direction: direction)
        selectedSessionId = newSession.id
    }

    func closeSplitPane(sessionId: UUID) {
        guard let session = sessions.first(where: { $0.id == sessionId }) else { return }
        sessions.removeAll { $0.id == sessionId }
        splitRoot = splitRoot.removing(sessionId: sessionId)
            ?? sessions.first.map { .leaf($0) }
            ?? splitRoot
        if selectedSessionId == sessionId {
            selectedSessionId = splitRoot.sessions.first?.id
        }
    }
}
```

### Wire into ContentView
```swift
// Replace single content view with the tree renderer
SplitPaneView(node: manager.splitRoot, manager: manager)
```

### Keyboard shortcuts (SplitCommands.swift)
```swift
struct SplitCommands: Commands {
    var manager: YourManager

    var body: some Commands {
        CommandMenu("View") {
            Button("Split Horizontally") { manager.splitActive(direction: .horizontal) }
                .keyboardShortcut("d", modifiers: .command)
            Button("Split Vertically")   { manager.splitActive(direction: .vertical) }
                .keyboardShortcut("d", modifiers: [.command, .shift])
            Divider()
            Button("Close Pane") {
                if let id = manager.selectedSessionId { manager.closeSplitPane(sessionId: id) }
            }
            .keyboardShortcut("w", modifiers: .command)
            .disabled(manager.sessions.count <= 1)
        }
    }
}

// In App:
WindowGroup { ... }
    .commands { SplitCommands(manager: sessionManager) }
```

---

## Key gotchas

- **`switch` in `body` fails** — SwiftUI's result builder doesn't support `switch` directly in `body`. Always delegate to a `@ViewBuilder` helper (`content()` above).
- **`indirect` is mandatory** — without it, `SplitNode` containing `SplitNode` has infinite size and won't compile.
- **`HSplitView`/`VSplitView` are AppKit-backed** — drag-to-resize is free; no custom gesture code needed.
- **`.id(session.id)` on leaf views** — forces SwiftUI to tear down and recreate the view when the session changes, preventing stale terminal state.
- **Keep `splitRoot` in sync** — every operation that adds/removes sessions (`addSession`, `closeSession`, `removeSession`) must also update `splitRoot` or the tree and array diverge.
- **`ratio` is advisory for SwiftUI** — `HSplitView`/`VSplitView` manage their own divider position; the stored ratio is mainly useful if you serialize layout or implement programmatic resizing.
