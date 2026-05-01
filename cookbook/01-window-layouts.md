## Window Layouts

### 2-Column: NavigationSplitView (Sidebar + Detail)

**Source:** `Directions/DirectionsFeature/Views/MainView.swift`

```swift
NavigationSplitView(columnVisibility: $columnVisibility) {
    SidebarView(
        manager: manager,
        searchText: $searchText
    )
    .navigationSplitViewColumnWidth(min: 200, ideal: 250, max: 350)
} detail: {
    DetailView(manager: manager)
}
.navigationSplitViewStyle(.balanced)
```

**Best for:** App navigation with hierarchy, master-detail patterns.

---

### 2-Pane: HSplitView (Simple)

**Source:** `TextScannerForVideo/ContentView.swift`

```swift
HSplitView {
    // Left side: Video Player
    videoPlayerPanel
        .frame(minWidth: 400)

    // Right side: Extracted Text List
    textListPanel
        .frame(minWidth: 250, idealWidth: 300)
}
.toolbar {
    toolbarContent
}
.frame(minWidth: 700, minHeight: 450)
```

**Best for:** Video/media + list, two equal-ish panes.

---

### 2-Pane: HSplitView (Preview + Sidebar)

**Source:** `FCPWorkspaceEditor/Views/ContentView.swift`

```swift
HSplitView {
    // Left: Visual Preview
    VStack(spacing: 0) {
        PreviewHeader(workspace: $viewModel.workspace)
        WorkspacePreview(workspace: $viewModel.workspace, viewModel: viewModel)
            .padding()
    }
    .frame(minWidth: 500)

    // Right: Panel Controls
    PanelControlsView(viewModel: viewModel)
        .frame(minWidth: 280, maxWidth: 350)
}
.toolbar { ... }
.frame(minWidth: 900, minHeight: 600)
```

**Best for:** Editor interfaces, preview + controls.

---

### 3-Section: HSplitView (Sidebar with Header/Content/Footer)

**Source:** `AppUpdater/ContentView.swift`

```swift
HSplitView {
    sidebar
        .frame(minWidth: 300, idealWidth: 350, maxWidth: 500)
    detailView
        .frame(minWidth: 400, maxWidth: .infinity, maxHeight: .infinity)
}
.frame(minWidth: 900, minHeight: 600)

private var sidebar: some View {
    VStack(spacing: 0) {
        // Stats header
        statsHeader
            .padding()
            .background(.bar)

        // Filter/action bar
        actionBar
            .padding(.horizontal)
            .padding(.vertical, 8)
            .background(.bar)

        // App list with selection
        List(filteredApps, selection: $selectedApp) { app in
            AppRowView(app: app)
                .tag(app)
        }
        .listStyle(.inset)
        .frame(maxHeight: .infinity)

        // Bottom bar
        bottomBar
            .padding()
            .background(.bar)
    }
    .frame(minWidth: 300, maxHeight: .infinity)
}
```

**Best for:** Sidebar with stats/filters/actions, detail view.

---

### Complex: HSplitView (Preview + Timeline + Sidebar)

**Source:** `Phosphor/ContentView.swift`

```swift
HSplitView {
    // Left column: Preview (top) + Toolbar + Timeline (bottom)
    GeometryReader { geometry in
        VStack(spacing: 0) {
            // Preview area
            PreviewPane(appState: appState, settings: appState.exportSettings)
                .frame(minHeight: 300)

            Divider()

            // Timeline section with darker background
            VStack(spacing: 0) {
                UnifiedToolbar(...)
                Divider()
                TimelinePane(appState: appState, onImport: showImportPanel)
                    .frame(minHeight: 120)
            }
            .background(Color(nsColor: .windowBackgroundColor).opacity(0.6))
        }
    }
    .frame(minWidth: 600)

    // Right sidebar: Settings
    SettingsSidebar(appState: appState)
        .frame(minWidth: 280, maxWidth: 400)
}
.frame(minWidth: 1080, minHeight: 700)
```

**Best for:** Video editors, complex multi-section layouts.

---

### Multi-Window App with Menu Bar

**Source:** `WindowMind/WindowMindApp.swift`

```swift
@main
struct WindowMindApp: App {
    @NSApplicationDelegateAdaptor(AppDelegate.self) var appDelegate
    @StateObject private var windowManager = WindowManager.shared
    @StateObject private var layoutManager = LayoutManager.shared

    var body: some Scene {
        // Main window (hidden by default for menu bar apps)
        WindowGroup {
            ContentView()
                .environmentObject(windowManager)
                .environmentObject(layoutManager)
                .frame(minWidth: 900, minHeight: 600)
        }
        .windowStyle(.hiddenTitleBar)
        .windowResizability(.contentSize)

        // Settings window
        Settings {
            SettingsView()
                .environmentObject(windowManager)
                .environmentObject(layoutManager)
        }
    }
}

class AppDelegate: NSObject, NSApplicationDelegate {
    var statusItem: NSStatusItem?
    var popover: NSPopover?

    func applicationDidFinishLaunching(_ notification: Notification) {
        setupMenuBar()
        WindowManager.shared.startMonitoring()
    }

    func setupMenuBar() {
        statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.squareLength)
        if let button = statusItem?.button {
            button.image = NSImage(systemSymbolName: "brain.head.profile",
                                   accessibilityDescription: "WindowMind")
            button.action = #selector(togglePopover)
            button.target = self
        }

        popover = NSPopover()
        popover?.contentSize = NSSize(width: 360, height: 500)
        popover?.behavior = .transient
        popover?.contentViewController = NSHostingController(rootView: MenuBarView())
    }

    @objc func togglePopover() {
        if let button = statusItem?.button, let popover = popover {
            if popover.isShown {
                popover.performClose(nil)
            } else {
                popover.show(relativeTo: button.bounds, of: button, preferredEdge: .minY)
            }
        }
    }
}
```

**Best for:** Menu bar utilities, background apps with occasional UI.

---

### Autosave Divider Positions

**Source:** `Penumbra/Utils/View+SplitViewAutosave.swift`, `VCR/Views/AppKit/View+SplitViewAutosave.swift`

```swift
private struct SplitViewAutosaveHelper: NSViewRepresentable {
    let autosaveName: String

    func makeNSView(context: Context) -> NSView {
        let view = NSView()
        DispatchQueue.main.async {
            var parent = view.superview
            while parent != nil {
                if let splitView = parent as? NSSplitView {
                    splitView.autosaveName = autosaveName
                    return
                }
                parent = parent?.superview
            }
        }
        return view
    }

    func updateNSView(_ nsView: NSView, context: Context) {}
}

extension View {
    /// Enables divider position autosaving for HSplitView or VSplitView
    func autosaveSplitView(named name: String) -> some View {
        self.background(SplitViewAutosaveHelper(autosaveName: name))
    }
}

// Usage:
HSplitView { ... }
    .autosaveSplitView(named: "MainSplitView")
```

**Best for:** Remember user's preferred pane sizes across launches.

---

### Anti-Pattern: Avoid HSplitView Layout Bugs

**From Analysis:** HSplitView on macOS doesn't properly fill vertical space in all configurations.

**Solution:** Use HStack + Divider instead for more predictable behavior:

```swift
// Instead of HSplitView, use:
HStack(spacing: 0) {
    leftPane
        .frame(minWidth: 300)

    Divider()

    rightPane
        .frame(minWidth: 400)
}
```

---

### NSTableView in SwiftUI (NSViewRepresentable)

**Source:** `VCR/Views/AppKit/FileTableView.swift`

When SwiftUI `List` doesn't cut it — you need column headers, cell reuse, or native drag-drop — wrap `NSTableView` in `NSViewRepresentable`. Key pattern: `@MainActor Coordinator` for Swift 6 strict concurrency, smart diffing in `updateNSView` for flicker-free updates.

```swift
struct FileTableView: NSViewRepresentable {
    let entries: [FileEntry]
    @Binding var selectedFileID: UUID?
    var onScan: (UUID) -> Void
    var onRemove: (UUID) -> Void
    var onDropFiles: ([URL]) -> Void

    func makeNSView(context: Context) -> NSScrollView {
        let tableView = NSTableView()
        tableView.style = .plain
        tableView.usesAlternatingRowBackgroundColors = true
        tableView.rowHeight = 28

        // Add columns (fixed + flexible)
        let nameCol = NSTableColumn(identifier: .init("Name"))
        nameCol.title = "Name"
        nameCol.minWidth = 120
        nameCol.resizingMask = .autoresizingMask
        tableView.addTableColumn(nameCol)
        // ... more columns

        tableView.dataSource = context.coordinator
        tableView.delegate = context.coordinator
        tableView.registerForDraggedTypes([.fileURL])

        let scrollView = NSScrollView()
        scrollView.documentView = tableView
        scrollView.hasVerticalScroller = true
        context.coordinator.tableView = tableView
        return scrollView
    }

    func updateNSView(_ scrollView: NSScrollView, context: Context) {
        guard let tableView = scrollView.documentView as? NSTableView else { return }
        let coordinator = context.coordinator
        let oldIDs = coordinator.entries.map(\.id)
        let newIDs = entries.map(\.id)
        coordinator.entries = entries

        if oldIDs != newIDs {
            tableView.reloadData()  // Structural change
        } else {
            // Selective reload: only rows whose data changed
            var changed = IndexSet()
            for (i, new) in entries.enumerated() {
                let old = coordinator.entries[i]
                if old.isScanning != new.isScanning
                    || old.scanResult?.status != new.scanResult?.status {
                    changed.insert(i)
                }
            }
            if !changed.isEmpty {
                tableView.reloadData(forRowIndexes: changed,
                    columnIndexes: IndexSet(integersIn: 0..<tableView.numberOfColumns))
            }
        }

        // Selection sync (guard against infinite loops)
        if !coordinator.isUpdatingSelection {
            // ... sync selectedFileID → tableView.selectedRow
        }
    }

    func makeCoordinator() -> Coordinator { Coordinator(parent: self) }

    @MainActor
    final class Coordinator: NSObject, NSTableViewDataSource, NSTableViewDelegate,
        NSMenuDelegate
    {
        var entries: [FileEntry] = []
        var isUpdatingSelection = false
        weak var tableView: NSTableView?
        private let parent: FileTableView

        init(parent: FileTableView) { self.parent = parent }

        func numberOfRows(in tableView: NSTableView) -> Int { entries.count }

        func tableView(_ tableView: NSTableView, viewFor tableColumn: NSTableColumn?,
            row: Int) -> NSView? {
            // Cell factory: makeView(withIdentifier:owner:) for reuse
            let cell = tableView.makeView(withIdentifier: col, owner: nil)
                as? NSTableCellView ?? makeTextCell(identifier: col)
            cell.textField?.stringValue = entries[row].file.fileName
            return cell
        }

        func tableViewSelectionDidChange(_ notification: Notification) {
            guard !isUpdatingSelection else { return }
            isUpdatingSelection = true
            defer { isUpdatingSelection = false }
            let row = tableView?.selectedRow ?? -1
            parent.selectedFileID = row >= 0 ? entries[row].id : nil
        }

        // Drag-and-drop via validateDrop / acceptDrop
        // Context menu via NSMenuDelegate.menuNeedsUpdate
    }
}
```

**Key design decisions:**
- **Diff by ID first:** If the list of IDs changed (add/remove), full `reloadData()`. Same IDs → compare per-row properties for selective `reloadData(forRowIndexes:)`.
- **Selection guard:** `isUpdatingSelection` flag prevents `tableViewSelectionDidChange` → `updateNSView` → `selectRowIndexes` infinite loops.
- **`@MainActor Coordinator`:** Required for Swift 6 strict concurrency since all NSTableView callbacks run on main thread.
- **Cell reuse:** `makeView(withIdentifier:owner:)` returns cached cells, `NSTableCellView` created manually with Auto Layout only on first use.

**Best for:** File lists, media browsers, any table needing columns + headers + native AppKit behavior in a SwiftUI app.

---

