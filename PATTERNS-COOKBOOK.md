# Swift/SwiftUI Patterns Cookbook

**Extracted from working production code across 15+ projects.**
**Last updated: 2026-03-01**

---

> **MANDATORY STANDARD — READ FIRST**
>
> Every macOS app MUST use the **App Shell Standard** below. This means:
> - `HSplitView` for panes (NOT `NavigationSplitView` — no Tahoe frosted sidebars)
> - `FCPToolbarButtonStyle` for toolbar buttons (NOT default round/capsule buttons)
> - `.windowStyle(.hiddenTitleBar)` + `.preferredColorScheme(.dark)` + `.toolbarRole(.editor)`
> - Custom dark `Theme` struct for consistent colors
>
> **Existing apps not using this pattern should be migrated.** When starting work on
> any macOS app, check whether it follows the App Shell Standard. If it doesn't,
> migrating to this standard is a prerequisite before adding new features.
>
> Reference implementation: `1-macOS/Penumbra/`

---

## Table of Contents

0. [App Shell Standard](#app-shell-standard) — **START HERE**
1. [Window Layouts](#window-layouts)
2. [Layout Templates](#layout-templates) — Pick an archetype for your app
3. [AppKit Controls](#appkit-controls)
4. [SwiftUI Performance](#swiftui-performance)
5. [Export & File Dialogs](#export--file-dialogs)
6. [App Lifecycle & Initialization](#app-lifecycle--initialization)
7. [MCP Memory Integration](#mcp-memory-integration)
8. [Agent Skills Integration](#agent-skills-integration)
9. [Web Development Patterns](#web-development-patterns)
10. [Subprocess & URL Patterns](#subprocess--url-patterns)
11. [Timecode Display Typography](#timecode-display-typography)
12. [Keyboard Shortcuts](#keyboard-shortcuts) — Four tiers from menu commands to custom managers
13. [Context Menus](#context-menus) — Per-pane right-click menus
14. [Quick Reference Table](#quick-reference-table)

---

## App Shell Standard

**Source:** `1-macOS/Penumbra/` (reference implementation)

The standard app shell for all macOS apps. Avoids macOS Tahoe's round capsule buttons, frosted sidebars, and default system chrome. Every new app starts with this. Every existing app migrates to this.

---

### 1. App Entry Point

```swift
@main
struct MyApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
                .frame(minWidth: 900, minHeight: 600)
                .preferredColorScheme(.dark)
        }
        .windowStyle(.hiddenTitleBar)     // no system title bar
        .commands {
            SidebarCommands()             // keep ⌘⇧S for sidebar toggle
        }

        Settings {
            SettingsView()
        }
    }
}
```

**Key decisions:**
- `.windowStyle(.hiddenTitleBar)` — removes the standard title bar chrome
- `.preferredColorScheme(.dark)` — forced dark mode, consistent across system settings
- No `.navigationTitle()` — title bar is hidden, so titles go in custom info strips or toolbars

---

### 2. Theme Struct

Centralized dark color palette. Use `Theme.xxx` everywhere instead of hardcoded colors.

```swift
import SwiftUI

@Observable
class ThemeManager {
    static let shared = ThemeManager()

    var accentColor: Color {
        didSet { saveColor(accentColor, forKey: "accentColor") }
    }

    private init() {
        self.accentColor = Self.loadColor(forKey: "accentColor")
            ?? Color(red: 0.9, green: 0.5, blue: 0.2)  // brand orange
    }

    private func saveColor(_ color: Color, forKey key: String) {
        let nsColor = NSColor(color)
        if let data = try? NSKeyedArchiver.archivedData(
            withRootObject: nsColor, requiringSecureCoding: false
        ) {
            UserDefaults.standard.set(data, forKey: key)
        }
    }

    private static func loadColor(forKey key: String) -> Color? {
        guard let data = UserDefaults.standard.data(forKey: key),
              let nsColor = try? NSKeyedUnarchiver.unarchivedObject(
                  ofClass: NSColor.self, from: data
              ) else { return nil }
        return Color(nsColor: nsColor)
    }
}

struct Theme {
    static var primaryBackground: Color { Color(white: 0.10) }
    static var secondaryBackground: Color { Color(white: 0.15) }
    static var accent: Color { ThemeManager.shared.accentColor }
    static var primaryText: Color { .white }
    static var secondaryText: Color { .white.opacity(0.65) }
}
```

**Usage:** `Theme.primaryBackground`, `Theme.accent`, `Theme.secondaryText` — never `Color.gray` or `.secondary` for backgrounds.

---

### 3. FCPToolbarButtonStyle (Flat Toolbar Buttons)

Replaces macOS default round/capsule toolbar buttons with flat, 4px-corner-radius buttons inspired by Final Cut Pro.

```swift
struct FCPToolbarButtonStyle: ButtonStyle {
    @Binding var isOn: Bool

    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .padding(.horizontal, 8)
            .padding(.vertical, 6)
            .foregroundColor(isOn ? .white : .primary)
            .background(
                ZStack {
                    if isOn {
                        Theme.accent
                    } else {
                        Color(nsColor: .gray.withAlphaComponent(0.2))
                    }
                    if configuration.isPressed {
                        Color.black.opacity(0.2)
                    }
                }
            )
            .cornerRadius(4)
            .overlay(
                RoundedRectangle(cornerRadius: 4)
                    .stroke(Color.black.opacity(0.2), lineWidth: 1)
            )
            .scaleEffect(configuration.isPressed ? 0.95 : 1.0)
            .animation(.easeInOut(duration: 0.1), value: configuration.isPressed)
            .animation(.spring(response: 0.3, dampingFraction: 0.5), value: isOn)
    }
}
```

For toolbar toggle buttons, wrap in a reusable view:

```swift
struct PaneToggleButton: View {
    @Binding var isOn: Bool
    let iconName: String
    let help: String

    var body: some View {
        Button(action: { withAnimation { isOn.toggle() } }) {
            Image(systemName: iconName)
                .resizable()
                .aspectRatio(contentMode: .fit)
                .frame(width: 16, height: 16)
        }
        .help(help)
        .buttonStyle(FCPToolbarButtonStyle(isOn: $isOn))
    }
}
```

**For non-toggle toolbar buttons**, pass `.constant(false)`:
```swift
Button(action: importFiles) {
    Image(systemName: "plus")
        .resizable().aspectRatio(contentMode: .fit)
        .frame(width: 16, height: 16)
}
.buttonStyle(FCPToolbarButtonStyle(isOn: .constant(false)))
```

---

### 4. Toolbar Configuration

```swift
.toolbar {
    ToolbarItemGroup(placement: .navigation) {
        // Left side — primary actions (import, add)
        PaneToggleButton(isOn: .constant(false), iconName: "plus", help: "Import")
    }

    ToolbarItemGroup(placement: .principal) {
        // Center — workspace/view mode switchers
        HStack {
            PaneToggleButton(isOn: $showGrid, iconName: "square.grid.3x3", help: "Grid")
            PaneToggleButton(isOn: $showList, iconName: "list.bullet", help: "List")
        }
        .buttonStyle(.borderless)
    }

    ToolbarItemGroup(placement: .primaryAction) {
        // Right side — pane visibility toggles
        HStack {
            PaneToggleButton(isOn: $showSidebar, iconName: "sidebar.left", help: "Sidebar")
            PaneToggleButton(isOn: $showInspector, iconName: "sidebar.right", help: "Inspector")

            Divider().frame(height: 20).padding(.horizontal, 4)

            PaneToggleButton(isOn: .constant(false), iconName: "terminal", help: "Console")
        }
        .buttonStyle(.borderless)
    }
}
.toolbarRole(.editor)  // editor-style toolbar, not browser-style
```

**Key:** `.toolbarRole(.editor)` prevents the back/forward navigation chrome that `.automatic` adds.

---

### 5. Pane Layout with HSplitView

```swift
var body: some View {
    VStack(spacing: 0) {
        // Optional: Info strip at top
        InfoStripView()
            .frame(height: 25)

        // Main content area
        HSplitView {
            if showSidebar {
                SidebarView()
                    .frame(minWidth: 220, idealWidth: 300, maxWidth: 500)
            }
            MainContentView()
                .frame(minWidth: 500)
            if showInspector {
                InspectorView()
                    .frame(minWidth: 220, idealWidth: 300, maxWidth: 500)
            }
        }
        .layoutPriority(1)
        .autosaveSplitView(named: "MainSplitView")

        // Optional: Bottom bar
        BottomBarView()
            .frame(height: 40)
    }
    .toolbar { /* ... */ }
    .toolbarRole(.editor)
}
```

**Pane visibility** is driven by `@AppStorage` bools toggled from the toolbar:
```swift
@AppStorage("showSidebar") private var showSidebar: Bool = true
@AppStorage("showInspector") private var showInspector: Bool = true
```

---

### 6. Button Style Guide (Non-Toolbar)

| Context | Style | Example |
|---------|-------|---------|
| Transport controls (play, pause, step) | `.buttonStyle(.plain)` | Icon-only, no background |
| Inline text actions (skip, dismiss) | `.buttonStyle(.borderless)` | Text link appearance |
| Secondary actions (Mark IN, Mark OUT) | `.buttonStyle(.bordered)` | Subtle bordered in dark mode |
| Primary CTA (Export, Submit) | `.borderedProminent` + `.tint(Theme.accent)` | Accent-colored, prominent |

---

### 7. Info Strip (Optional Top Bar)

Thin bar below the toolbar showing contextual info (file name, metadata, progress).

```swift
struct InfoStripView: View {
    var body: some View {
        HStack {
            Text("Current file info")
                .font(.caption)
            Spacer()
            Text("metadata")
                .font(.caption)
                .foregroundColor(.secondary)
        }
        .padding(.horizontal)
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .leading)
        .background(Color(nsColor: .windowBackgroundColor))
        .overlay(
            Rectangle().frame(height: 1)
                .foregroundColor(Color(nsColor: .separatorColor)),
            alignment: .bottom
        )
    }
}
```

---

### Migration Checklist

When migrating an existing app to the App Shell Standard:

- [ ] Replace `NavigationSplitView` with `HSplitView`
- [ ] Add `.windowStyle(.hiddenTitleBar)` to the `WindowGroup` scene
- [ ] Add `.preferredColorScheme(.dark)`
- [ ] Add `.toolbarRole(.editor)` to the main view
- [ ] Replace default toolbar buttons with `FCPToolbarButtonStyle`
- [ ] Add `Theme` struct, replace hardcoded colors
- [ ] Add `.autosaveSplitView(named:)` to split views
- [ ] Convert pane visibility to `@AppStorage` bools toggled from toolbar
- [ ] Remove any `NavigationTitle` calls (title bar is hidden)
- [ ] Verify: no round/capsule buttons remain in the toolbar

---

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

## Layout Templates

Named archetypes for common pro-app layouts. All build on the [App Shell Standard](#app-shell-standard) — hidden title bar, dark mode, FCPToolbarButtonStyle, Theme struct. **Pick the template closest to your app, then customize.**

Every template uses the same state pattern for pane visibility:

```swift
@AppStorage("showSidebar")   private var showSidebar: Bool = true
@AppStorage("showInspector") private var showInspector: Bool = false
@AppStorage("showTimeline")  private var showTimeline: Bool = true
```

---

### Template A: Browser (Sidebar + Grid + Viewer)

**Use for:** Media browsers, asset managers, file organizers, library apps.
**References:** FCP Browser, Lightroom Library, Penumbra, Lightweight Media Asset Manager

```
┌─────────────────────────────────────────────────────┐
│  Toolbar: [+Import]    [Grid|List]   [◧ ◨ Inspector] │
├────────┬──────────────────────┬─────────────────────┤
│        │                      │                     │
│ Source  │   Grid / List        │   Inspector         │
│ List    │   (main content)     │   (metadata,        │
│         │                      │    properties)      │
│         │                      │                     │
├────────┴──────────────────────┴─────────────────────┤
│  Status: 42 items  ·  3 selected  ·  12.4 GB        │
└─────────────────────────────────────────────────────┘
```

```swift
var body: some View {
    VStack(spacing: 0) {
        HSplitView {
            if showSidebar {
                SourceListView(selection: $selectedCollection)
                    .frame(minWidth: 180, idealWidth: 240, maxWidth: 350)
            }
            BrowserGridView(items: items, selection: $selectedItems)
                .frame(minWidth: 400)
            if showInspector {
                InspectorView(selection: selectedItems)
                    .frame(minWidth: 240, idealWidth: 300, maxWidth: 400)
            }
        }
        .autosaveSplitView(named: "BrowserSplit")

        StatusBarView(itemCount: items.count, selectionCount: selectedItems.count)
            .frame(height: 28)
    }
    .toolbar {
        ToolbarItemGroup(placement: .navigation) {
            PaneToggleButton(isOn: .constant(false), iconName: "plus", help: "Import")
        }
        ToolbarItemGroup(placement: .principal) {
            HStack {
                PaneToggleButton(isOn: $showGrid, iconName: "square.grid.3x3", help: "Grid")
                PaneToggleButton(isOn: $showList, iconName: "list.bullet", help: "List")
            }
            .buttonStyle(.borderless)
        }
        ToolbarItemGroup(placement: .primaryAction) {
            HStack {
                PaneToggleButton(isOn: $showSidebar, iconName: "sidebar.left", help: "Sidebar")
                PaneToggleButton(isOn: $showInspector, iconName: "sidebar.right", help: "Inspector")
            }
            .buttonStyle(.borderless)
        }
    }
    .toolbarRole(.editor)
}
```

**Key decisions:**
- Grid is the main content and always visible — sidebar and inspector toggle
- `SourceListView` is a flat list or grouped list of collections/folders, not a nav hierarchy
- Inspector shows metadata for the current selection (single or multi)
- Status bar at bottom replaces the need for an info strip at top

---

### Template B: Editor (Viewer + Timeline)

**Use for:** Video editors, audio editors, animation tools, anything with a timeline.
**References:** FCP main window, Phosphor, DaVinci Resolve edit page

```
┌──────────────────────────────────────────────────────┐
│  Toolbar: [◧ Sidebar]  [Viewer|Color]  [Inspector ◨] │
├─────────┬─────────────────────────┬──────────────────┤
│         │                         │                  │
│ Browser │      Viewer / Canvas    │   Inspector      │
│ (clips, │      (preview area)     │   (properties)   │
│  media) │                         │                  │
│         ├─────────────────────────┤                  │
│         │ ◀ ▶ ⏸  00:01:23:15     │                  │
│         ├─────────────────────────┤                  │
│         │   Timeline              │                  │
│         │   ████▓▓▓░░░░▓▓▓████   │                  │
│         │   ▓▓▓▓░░░░░░░░▓▓▓▓▓   │                  │
├─────────┴─────────────────────────┴──────────────────┤
│  Rendering: 45%  ████████░░░░░░░░  ·  01:23 remain   │
└──────────────────────────────────────────────────────┘
```

```swift
var body: some View {
    VStack(spacing: 0) {
        HSplitView {
            if showSidebar {
                BrowserPane(media: mediaLibrary, selection: $selectedClips)
                    .frame(minWidth: 200, idealWidth: 280, maxWidth: 400)
            }

            // Center: Viewer (top) + Timeline (bottom)
            GeometryReader { geo in
                VStack(spacing: 0) {
                    ViewerPane(player: player)
                        .frame(minHeight: 250)

                    Divider()

                    TransportBar(player: player)
                        .frame(height: 36)

                    if showTimeline {
                        Divider()
                        TimelinePane(project: project, player: player)
                            .frame(minHeight: 120)
                    }
                }
            }
            .frame(minWidth: 500)

            if showInspector {
                InspectorPane(selection: selectedClips)
                    .frame(minWidth: 240, idealWidth: 300, maxWidth: 400)
            }
        }
        .autosaveSplitView(named: "EditorSplit")

        ProgressBarView(renderProgress: renderState)
            .frame(height: 28)
    }
    .toolbarRole(.editor)
}
```

**Key decisions:**
- Center column uses `VStack` to stack viewer + timeline vertically, wrapped in `GeometryReader`
- Transport controls (play/pause/timecode) sit between viewer and timeline as a thin bar
- Timeline visibility is toggleable — hide it for a pure viewer/grading mode
- Browser pane on the left can show media clips, project bins, or effects library
- Bottom bar shows render/export progress when active, otherwise status info

---

### Template C: Organizer (Source List + Detail)

**Use for:** Settings apps, update managers, project managers, anything list → detail.
**References:** AppUpdater, System Preferences, Xcode Organizer

```
┌─────────────────────────────────────────────┐
│  Toolbar: [↻ Refresh]          [⚙ Settings] │
├──────────────┬──────────────────────────────┤
│  Stats       │                              │
│  ┌────────┐  │   Detail View                │
│  │ 12 apps│  │                              │
│  └────────┘  │   (content changes based     │
│  ──────────  │    on sidebar selection)      │
│  Filter bar  │                              │
│  ──────────  │                              │
│  ▸ Item 1    │                              │
│  ▸ Item 2  ← │                              │
│  ▸ Item 3    │                              │
│  ──────────  │                              │
│  Bottom bar  │                              │
├──────────────┴──────────────────────────────┤
│  Last checked: 2 hours ago                   │
└─────────────────────────────────────────────┘
```

```swift
var body: some View {
    VStack(spacing: 0) {
        HSplitView {
            // Sidebar with sections
            VStack(spacing: 0) {
                StatsHeaderView(stats: stats)
                    .padding()
                    .background(.bar)

                FilterBarView(filter: $currentFilter)
                    .padding(.horizontal)
                    .padding(.vertical, 8)
                    .background(.bar)

                List(filteredItems, selection: $selectedItem) { item in
                    ItemRowView(item: item)
                        .tag(item)
                }
                .listStyle(.inset)

                SidebarFooterView(actions: bulkActions)
                    .padding()
                    .background(.bar)
            }
            .frame(minWidth: 260, idealWidth: 320, maxWidth: 450)

            // Detail
            DetailView(item: selectedItem)
                .frame(minWidth: 400)
        }
        .autosaveSplitView(named: "OrganizerSplit")

        StatusBarView(lastUpdated: lastCheckDate)
            .frame(height: 28)
    }
    .toolbarRole(.editor)
}
```

**Key decisions:**
- Sidebar has structure: stats header → filter bar → list → footer. Not just a flat list
- No inspector pane — the detail view IS the inspector (full-width detail)
- Selection drives the detail view via binding
- Good for apps where you iterate a list and act on each item

---

### Template D: Dual Viewer (Compare / Side-by-Side)

**Use for:** Diff tools, before/after comparison, A/B preview, reference viewer.
**References:** FCP comparison view, Beyond Compare, Kaleidoscope

```
┌───────────────────────────────────────────────────┐
│  Toolbar: [A ▾ Source]  [Swap ⇄]  [B ▾ Source]    │
├───────────────────────┬───────────────────────────┤
│                       │                           │
│    Viewer A           │    Viewer B               │
│    (source/before)    │    (output/after)          │
│                       │                           │
│                       │                           │
├───────────────────────┴───────────────────────────┤
│  Info: A = Original (1920×1080)  B = Graded (UHD) │
└───────────────────────────────────────────────────┘
```

```swift
@AppStorage("compareLayout") private var layout: CompareLayout = .sideBySide

enum CompareLayout: String, CaseIterable {
    case sideBySide, overlay, split
}

var body: some View {
    VStack(spacing: 0) {
        switch layout {
        case .sideBySide:
            HSplitView {
                ViewerPane(source: sourceA, label: "A")
                    .frame(minWidth: 300)
                ViewerPane(source: sourceB, label: "B")
                    .frame(minWidth: 300)
            }
            .autosaveSplitView(named: "CompareSplit")

        case .overlay:
            ZStack {
                ViewerPane(source: sourceA, label: "A")
                ViewerPane(source: sourceB, label: "B")
                    .opacity(overlayOpacity)
            }

        case .split:
            SplitWipeView(sourceA: sourceA, sourceB: sourceB, position: $wipePosition)
        }

        CompareInfoBar(sourceA: sourceA, sourceB: sourceB)
            .frame(height: 28)
    }
    .toolbar {
        ToolbarItemGroup(placement: .principal) {
            Picker("Layout", selection: $layout) {
                ForEach(CompareLayout.allCases, id: \.self) { mode in
                    Text(mode.rawValue.capitalized).tag(mode)
                }
            }
            .pickerStyle(.segmented)
        }
    }
    .toolbarRole(.editor)
}
```

**Key decisions:**
- Three compare modes: side-by-side (HSplitView), overlay (ZStack + opacity), split wipe (custom drag divider)
- Toolbar shows source selectors and layout mode switcher
- Info bar at bottom shows metadata for both sources
- No sidebar or inspector — the entire window is comparison space

---

### Template E: Workspace (Tab-Switched Content)

**Use for:** Apps with distinct modes/workspaces the user switches between.
**References:** FCP browser/timeline/color tabs, Xcode editor/debug/source control

```
┌──────────────────────────────────────────────────┐
│  Toolbar: [◧]  [Import ▾ Edit ▾ Export]  [⚙ ◨]   │
├──────────────────────────────────────────────────┤
│                                                  │
│  Content changes entirely based on active tab:   │
│                                                  │
│  Import  → Browser template (A) layout           │
│  Edit    → Editor template (B) layout            │
│  Export  → Organizer template (C) layout         │
│                                                  │
└──────────────────────────────────────────────────┘
```

```swift
enum Workspace: String, CaseIterable {
    case importMedia = "Import"
    case edit = "Edit"
    case export = "Export"
}

@AppStorage("activeWorkspace") private var workspace: Workspace = .edit

var body: some View {
    VStack(spacing: 0) {
        switch workspace {
        case .importMedia:
            ImportWorkspaceView()     // uses Browser template
        case .edit:
            EditWorkspaceView()       // uses Editor template
        case .export:
            ExportWorkspaceView()     // uses Organizer template
        }
    }
    .toolbar {
        ToolbarItemGroup(placement: .principal) {
            HStack(spacing: 2) {
                ForEach(Workspace.allCases, id: \.self) { ws in
                    PaneToggleButton(
                        isOn: Binding(
                            get: { workspace == ws },
                            set: { if $0 { workspace = ws } }
                        ),
                        iconName: ws.icon,
                        help: ws.rawValue
                    )
                }
            }
            .buttonStyle(.borderless)
        }
        ToolbarItemGroup(placement: .primaryAction) {
            HStack {
                PaneToggleButton(isOn: $showSidebar, iconName: "sidebar.left", help: "Sidebar")
                PaneToggleButton(isOn: $showInspector, iconName: "sidebar.right", help: "Inspector")
            }
            .buttonStyle(.borderless)
        }
    }
    .toolbarRole(.editor)
}
```

**Key decisions:**
- Each workspace is a completely different layout — they can use different templates internally
- Workspace toggle reuses `PaneToggleButton` with a computed binding for mutual exclusivity
- Sidebar/inspector toggles persist per-workspace by keying `@AppStorage` with workspace name
- The workspace enum is `@AppStorage`-backed so the app reopens to the last-used mode

---

### Choosing a Template

| Your App Does | Template | Key Trait |
|---|---|---|
| Browse/organize a collection | **A: Browser** | Grid + optional inspector |
| Edit with a timeline or canvas | **B: Editor** | Viewer + timeline stacked vertically |
| Iterate a list, act on each | **C: Organizer** | Structured sidebar + full detail |
| Compare two things | **D: Dual Viewer** | Two viewers, multiple compare modes |
| Multiple distinct modes | **E: Workspace** | Tab-switched, each tab = own layout |

All templates compose — a Workspace (E) app might use Browser (A) for its import tab and Editor (B) for its edit tab.

---

## AppKit Controls

All interactive controls use AppKit wrappers via `NSViewRepresentable` instead of SwiftUI controls. SwiftUI's `.bordered` button style renders as rounded capsules; AppKit's `.rounded` bezel gives the classic ~4pt corner radius. This applies to every control — buttons, toggles, pickers, sliders, etc. See `41_apple-ui.md` → Project UI Conventions for the full mapping table.

**Convention:** Keep all wrappers in `Views/AppKit/` and reuse across the project.

### AppKitButton (NSButton)

**Replaces:** SwiftUI `Button`

```swift
struct AppKitButton: NSViewRepresentable {
    let title: String
    var bezelStyle: NSButton.BezelStyle = .rounded
    var keyEquivalent: String = ""
    let action: () -> Void

    func makeNSView(context: Context) -> NSButton {
        let button = NSButton(title: title, target: context.coordinator,
                              action: #selector(Coordinator.clicked))
        button.bezelStyle = bezelStyle
        button.keyEquivalent = keyEquivalent
        return button
    }

    func updateNSView(_ nsView: NSButton, context: Context) {
        nsView.title = title
        nsView.bezelStyle = bezelStyle
        nsView.keyEquivalent = keyEquivalent
    }

    func makeCoordinator() -> Coordinator { Coordinator(action: action) }

    class Coordinator: NSObject {
        let action: () -> Void
        init(action: @escaping () -> Void) { self.action = action }
        @objc func clicked() { action() }
    }
}

// Usage
AppKitButton(title: "Export", action: handleExport)
AppKitButton(title: "OK", bezelStyle: .rounded, keyEquivalent: "\r", action: confirm)
AppKitButton(title: "Delete", bezelStyle: .texturedSquare, action: delete)
```

**Bezel styles:** `.rounded` (standard), `.texturedSquare` (toolbar), `.regularSquare` (flat), `.recessed` (subtle)

**Best for:** Any tappable action — primary, secondary, destructive, toolbar buttons.

---

### AppKitCheckbox (NSButton, checkbox type)

**Replaces:** SwiftUI `Toggle`

```swift
struct AppKitCheckbox: NSViewRepresentable {
    let title: String
    @Binding var isOn: Bool

    func makeNSView(context: Context) -> NSButton {
        let checkbox = NSButton(checkboxWithTitle: title, target: context.coordinator,
                                action: #selector(Coordinator.toggled))
        checkbox.state = isOn ? .on : .off
        return checkbox
    }

    func updateNSView(_ nsView: NSButton, context: Context) {
        nsView.title = title
        nsView.state = isOn ? .on : .off
    }

    func makeCoordinator() -> Coordinator { Coordinator(isOn: $isOn) }

    class Coordinator: NSObject {
        let isOn: Binding<Bool>
        init(isOn: Binding<Bool>) { self.isOn = isOn }
        @objc func toggled(_ sender: NSButton) { isOn.wrappedValue = sender.state == .on }
    }
}

// Usage
AppKitCheckbox(title: "Show grid", isOn: $showGrid)
AppKitCheckbox(title: "Auto-save", isOn: $autoSave)
```

**Best for:** Boolean settings, preferences, feature toggles.

---

### AppKitPopup (NSPopUpButton)

**Replaces:** SwiftUI `Picker` with `.menu` style

```swift
struct AppKitPopup<T: Hashable>: NSViewRepresentable {
    let items: [T]
    let titleForItem: (T) -> String
    @Binding var selection: T

    func makeNSView(context: Context) -> NSPopUpButton {
        let popup = NSPopUpButton(frame: .zero, pullsDown: false)
        popup.target = context.coordinator
        popup.action = #selector(Coordinator.selected)
        return popup
    }

    func updateNSView(_ nsView: NSPopUpButton, context: Context) {
        nsView.removeAllItems()
        for item in items { nsView.addItem(withTitle: titleForItem(item)) }
        if let idx = items.firstIndex(of: selection) { nsView.selectItem(at: idx) }
    }

    func makeCoordinator() -> Coordinator { Coordinator(parent: self) }

    class Coordinator: NSObject {
        let parent: AppKitPopup
        init(parent: AppKitPopup) { self.parent = parent }
        @objc func selected(_ sender: NSPopUpButton) {
            let idx = sender.indexOfSelectedItem
            if idx >= 0 && idx < parent.items.count { parent.selection = parent.items[idx] }
        }
    }
}

// Usage
AppKitPopup(items: ExportFormat.allCases, titleForItem: \.rawValue, selection: $format)
```

**Best for:** Enum selection, format pickers, any dropdown menu.

---

### AppKitSegmented (NSSegmentedControl)

**Replaces:** SwiftUI `Picker` with `.segmented` style

```swift
struct AppKitSegmented<T: Hashable>: NSViewRepresentable {
    let items: [(title: String, value: T)]
    @Binding var selection: T

    func makeNSView(context: Context) -> NSSegmentedControl {
        let control = NSSegmentedControl(labels: items.map(\.title),
                                          trackingMode: .selectOne,
                                          target: context.coordinator,
                                          action: #selector(Coordinator.changed))
        if let idx = items.firstIndex(where: { $0.value == selection }) {
            control.selectedSegment = idx
        }
        return control
    }

    func updateNSView(_ nsView: NSSegmentedControl, context: Context) {
        if let idx = items.firstIndex(where: { $0.value == selection }) {
            nsView.selectedSegment = idx
        }
    }

    func makeCoordinator() -> Coordinator { Coordinator(parent: self) }

    class Coordinator: NSObject {
        let parent: AppKitSegmented
        init(parent: AppKitSegmented) { self.parent = parent }
        @objc func changed(_ sender: NSSegmentedControl) {
            let idx = sender.selectedSegment
            if idx >= 0 && idx < parent.items.count { parent.selection = parent.items[idx].value }
        }
    }
}

// Usage
AppKitSegmented(items: [("List", ViewMode.list), ("Grid", ViewMode.grid)], selection: $viewMode)
```

**Best for:** View mode switching, tab-like selection, mutually exclusive options.

---

### AppKitSlider (NSSlider)

**Replaces:** SwiftUI `Slider`

```swift
struct AppKitSlider: NSViewRepresentable {
    @Binding var value: Double
    var minValue: Double = 0
    var maxValue: Double = 1

    func makeNSView(context: Context) -> NSSlider {
        let slider = NSSlider(value: value, minValue: minValue, maxValue: maxValue,
                              target: context.coordinator, action: #selector(Coordinator.changed))
        slider.isContinuous = true
        return slider
    }

    func updateNSView(_ nsView: NSSlider, context: Context) {
        nsView.doubleValue = value
        nsView.minValue = minValue
        nsView.maxValue = maxValue
    }

    func makeCoordinator() -> Coordinator { Coordinator(value: $value) }

    class Coordinator: NSObject {
        let value: Binding<Double>
        init(value: Binding<Double>) { self.value = value }
        @objc func changed(_ sender: NSSlider) { value.wrappedValue = sender.doubleValue }
    }
}

// Usage
AppKitSlider(value: $opacity, minValue: 0, maxValue: 1)
AppKitSlider(value: $volume, minValue: 0, maxValue: 100)
```

**Best for:** Continuous value adjustment — opacity, volume, zoom, timeline scrubbing.

---

### AppKitTextField (NSTextField)

**Replaces:** SwiftUI `TextField`

```swift
struct AppKitTextField: NSViewRepresentable {
    let placeholder: String
    @Binding var text: String
    var onCommit: (() -> Void)?

    func makeNSView(context: Context) -> NSTextField {
        let field = NSTextField()
        field.placeholderString = placeholder
        field.stringValue = text
        field.delegate = context.coordinator
        return field
    }

    func updateNSView(_ nsView: NSTextField, context: Context) {
        if nsView.stringValue != text { nsView.stringValue = text }
    }

    func makeCoordinator() -> Coordinator { Coordinator(parent: self) }

    class Coordinator: NSObject, NSTextFieldDelegate {
        let parent: AppKitTextField
        init(parent: AppKitTextField) { self.parent = parent }

        func controlTextDidChange(_ obj: Notification) {
            guard let field = obj.object as? NSTextField else { return }
            parent.text = field.stringValue
        }

        func control(_ control: NSControl, textShouldEndEditing fieldEditor: NSText) -> Bool {
            parent.onCommit?()
            return true
        }
    }
}

// Usage
AppKitTextField(placeholder: "Search...", text: $searchText)
AppKitTextField(placeholder: "File name", text: $fileName, onCommit: save)
```

**Best for:** Text input fields, search bars, inline editing.

---

### AppKitToolbarButtonStyle (SwiftUI .toolbar Exception)

**Source:** `Penumbra/Views/ToolbarButtonStyles.swift`

SwiftUI `.toolbar` is the **one exception** to the "no SwiftUI controls" rule. It handles placement (`.navigation`, `.principal`, `.primaryAction`) and `toolbarRole(.editor)` with minimal code. But toolbar buttons must use a custom `ButtonStyle` for native AppKit appearance instead of SwiftUI's default capsule styling.

```swift
/// Toolbar button with native AppKit appearance.
/// Flat background, 4pt corners, accent color when active.
struct AppKitToolbarButtonStyle: ButtonStyle {
    @Binding var isOn: Bool

    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .padding(.horizontal, 8)
            .padding(.vertical, 6)
            .foregroundColor(isOn ? .white : .primary)
            .background(
                ZStack {
                    if isOn {
                        Color.accentColor
                    } else {
                        Color(nsColor: .gray.withAlphaComponent(0.2))
                    }
                    if configuration.isPressed {
                        Color.black.opacity(0.2)
                    }
                }
            )
            .cornerRadius(4)
            .overlay(
                RoundedRectangle(cornerRadius: 4)
                    .stroke(Color.black.opacity(0.2), lineWidth: 1)
            )
            .scaleEffect(configuration.isPressed ? 0.95 : 1.0)
            .animation(.easeInOut(duration: 0.1), value: configuration.isPressed)
    }
}

// Usage in .toolbar
.toolbar {
    ToolbarItemGroup(placement: .navigation) {
        Button(action: importFile) {
            Image(systemName: "plus")
        }
        .buttonStyle(AppKitToolbarButtonStyle(isOn: .constant(false)))
    }

    ToolbarItemGroup(placement: .primaryAction) {
        Button(action: { showSidebar.toggle() }) {
            Image(systemName: "sidebar.right")
        }
        .buttonStyle(AppKitToolbarButtonStyle(isOn: $showSidebar))
    }
}
.toolbarRole(.editor)
```

**Why not NSToolbar?** NSToolbar gives user customization (drag items in/out) and overflow menus, but requires `NSToolbarDelegate` boilerplate (~80 lines) and bridging to SwiftUI state. SwiftUI `.toolbar` + custom style gets 90% of the native look with 10% of the code.

**Best for:** All toolbar buttons. Use `isOn: .constant(false)` for action buttons, `isOn: $binding` for toggle buttons.

---

## SwiftUI Performance

### The Core Principle: Diffing Checkpoints

**Source:** [SwiftUI Performance Article](https://www.swiftdifferently.com/blog/swiftui/swiftui-performance-article)

SwiftUI uses a "comparison engine" that diffs view output against previous renders. When state updates, the view body re-executes and SwiftUI compares the result.

**The Problem:** Large, monolithic view bodies force SwiftUI to compare many primitives (Text, Button, Image) on every state change.

**The Solution:** Extract subviews into separate structs. Each struct becomes a "diffing checkpoint" — SwiftUI skips re-evaluating subviews whose properties haven't changed.

```swift
// ❌ BAD: Monolithic view body
struct ContentView: View {
    @State private var counter = 0

    var body: some View {
        VStack {
            Text("Header")
            Image(systemName: "star")
            Text("Count: \(counter)")
            Button("Increment") { counter += 1 }
            // 50 more views here...
            // ALL re-evaluated when counter changes
        }
    }
}

// ✅ GOOD: Separate view structs
struct ContentView: View {
    @State private var counter = 0

    var body: some View {
        VStack {
            HeaderView()        // ← Diffing checkpoint (skipped if unchanged)
            CounterView(count: counter)
            IncrementButton { counter += 1 }
        }
    }
}

struct HeaderView: View {
    var body: some View {
        VStack {
            Text("Header")
            Image(systemName: "star")
        }
    }
}
```

---

### Anti-Pattern: @ViewBuilder Methods Don't Help

**Source:** [SwiftUI Performance Article](https://www.swiftdifferently.com/blog/swiftui/swiftui-performance-article)

Methods and computed properties using `@ViewBuilder` still trigger full re-execution because they're called at runtime. Only separate structs get the optimization.

```swift
// ❌ BAD: @ViewBuilder method (no performance benefit)
struct ContentView: View {
    @State private var counter = 0

    var body: some View {
        VStack {
            headerView   // Still re-executes every time!
            Text("Count: \(counter)")
        }
    }

    @ViewBuilder
    private var headerView: some View {
        Text("Header")
        Image(systemName: "star")
    }
}

// ✅ GOOD: Separate struct (actual optimization)
struct HeaderView: View {
    var body: some View {
        VStack {
            Text("Header")
            Image(systemName: "star")
        }
    }
}
```

---

### Equatable for Views with Closures

**Source:** [SwiftUI Performance Article](https://www.swiftdifferently.com/blog/swiftui/swiftui-performance-article)

SwiftUI can't compare closures, so views with closure properties always look "changed." Use `.equatable()` with custom equality.

```swift
struct ActionButton: View, Equatable {
    let title: String
    let action: () -> Void

    var body: some View {
        Button(title, action: action)
    }

    // Custom equality ignores the closure
    static func == (lhs: ActionButton, rhs: ActionButton) -> Bool {
        lhs.title == rhs.title
    }
}

// Usage:
ActionButton(title: "Save", action: save)
    .equatable()  // ← Enables custom equality check
```

---

### Debug Technique: Random Background Colors

**Source:** [SwiftUI Performance Article](https://www.swiftdifferently.com/blog/swiftui/swiftui-performance-article)

Visualize which views are re-rendering by adding random background colors:

```swift
extension View {
    func debugRender() -> some View {
        self.background(Color(
            red: .random(in: 0...1),
            green: .random(in: 0...1),
            blue: .random(in: 0...1)
        ))
    }
}

// Usage during debugging:
HeaderView()
    .debugRender()  // Color changes = view re-rendered
```

If a view's color changes when unrelated state updates, it needs extraction into a separate struct.

---

## Export & File Dialogs

### NSSavePanel with Progress

**Source:** `Phosphor/Views/Export/ExportSheet.swift`

```swift
private func startExport() {
    let panel = NSSavePanel()
    panel.title = "Export \(appState.exportSettings.format.rawValue)"
    panel.allowedContentTypes = [appState.exportSettings.format.utType]
    panel.nameFieldStringValue = "animation.\(appState.exportSettings.format.fileExtension)"
    panel.canCreateDirectories = true

    panel.begin { response in
        guard response == .OK, let url = panel.url else { return }

        Task { @MainActor in
            await executeExport(to: url)
        }
    }
}

private func executeExport(to url: URL) async {
    exportState = .exporting(progress: 0.0)

    do {
        try await appState.executeExportWithProgress(to: url, frames: appState.unmutedFrames) { progress in
            exportState = .exporting(progress: progress)
        }
        exportState = .completed(url: url)
    } catch {
        exportState = .failed(error: error.localizedDescription)
    }
}
```

---

### NSOpenPanel for Directory Selection

**Source:** `Directions/DirectionsFeature/Views/Settings/DirectoryPickerView.swift`

```swift
private func chooseFolder() {
    let panel = NSOpenPanel()
    panel.canChooseDirectories = true
    panel.canChooseFiles = false
    panel.allowsMultipleSelection = false
    panel.prompt = "Select"
    panel.message = message

    if panel.runModal() == .OK, let url = panel.url {
        selectedURL = url
    }
}
```

---

### Async NSOpenPanel (Non-Blocking)

**Source:** `CropBatch/Services/ExportCoordinator.swift`

```swift
func selectOutputFolderAndProcess(images: [ImageItem]) {
    let panel = NSOpenPanel()
    panel.title = "Choose Export Folder"
    panel.canChooseFiles = false
    panel.canChooseDirectories = true
    panel.allowsMultipleSelection = false
    panel.canCreateDirectories = true

    panel.begin { [weak self] response in
        guard response == .OK, let outputDirectory = panel.url else { return }
        Task { @MainActor [weak self] in
            await self?.processImagesWithConflictCheck(images, to: outputDirectory)
        }
    }
}
```

---

### Progress View with Time Tracking

**Source:** `QuickMotion/Views/Export/ExportProgressView.swift`

```swift
struct ExportProgressView: View {
    let fileName: String
    let progress: Double
    let elapsedTime: String
    let remainingTime: String?
    let isPreparing: Bool
    let onCancel: () -> Void

    var body: some View {
        VStack(spacing: 16) {
            Text(isPreparing ? "Preparing export..." : "Exporting \"\(fileName)\"...")
                .font(.headline)

            if isPreparing {
                ProgressView()
                    .progressViewStyle(.linear)
            } else {
                ProgressView(value: progress)
                    .progressViewStyle(.linear)
            }

            if !isPreparing {
                Text("\(Int(progress * 100))%")
                    .font(.system(.body, design: .monospaced))
                    .foregroundStyle(.secondary)
            }

            HStack {
                Text("Elapsed: \(elapsedTime)")
                    .font(.system(.body, design: .monospaced))
                Spacer()
                if let remaining = remainingTime {
                    Text("Remaining: ~\(remaining)")
                        .font(.system(.body, design: .monospaced))
                }
            }
            .foregroundStyle(.secondary)

            HStack {
                Spacer()
                Button("Cancel", action: onCancel)
            }
        }
        .padding()
        .frame(minWidth: 300)
    }
}
```

---

### Security-Scoped Bookmarks (Persistent Folder Access)

**Source:** `Directions/DirectionsFeature/Services/BookmarkManager.swift`

```swift
@Observable
@MainActor
public final class BookmarkManager {
    public private(set) var authorizedPaths: Set<URL> = []
    private var activeResources: [URL] = []

    /// Save a security-scoped bookmark for the given URL
    public func saveBookmark(for url: URL) throws {
        let bookmarkData = try url.bookmarkData(
            options: .withSecurityScope,
            includingResourceValuesForKeys: nil,
            relativeTo: nil
        )

        var bookmarks = loadBookmarks()
        bookmarks[url.path] = bookmarkData
        defaults.set(bookmarks, forKey: bookmarksKey)

        if url.startAccessingSecurityScopedResource() {
            authorizedPaths.insert(url)
            activeResources.append(url)
        }
    }

    /// Resolve all stored bookmarks on app launch
    public func resolveBookmarks() async {
        for (path, bookmarkData) in loadBookmarks() {
            do {
                var isStale = false
                let url = try URL(
                    resolvingBookmarkData: bookmarkData,
                    options: .withSecurityScope,
                    relativeTo: nil,
                    bookmarkDataIsStale: &isStale
                )

                if url.startAccessingSecurityScopedResource() {
                    authorizedPaths.insert(url)
                    activeResources.append(url)
                }
            } catch {
                // Handle stale bookmark
            }
        }
    }
}
```

**Critical:** Always call `stopAccessingSecurityScopedResource()` when done!

---

### SwiftUI .fileImporter with Drag & Drop

**Source:** `CropBatch/Views/ExportSettingsView.swift`

```swift
VStack(spacing: 6) {
    if let image = cachedImage {
        // Show preview with remove button
        Image(nsImage: image)
            .resizable()
            .aspectRatio(contentMode: .fit)
            .frame(height: 40)
    } else {
        // Drop zone
        VStack(spacing: 4) {
            Image(systemName: "photo.badge.plus")
                .foregroundStyle(.secondary)
            Text("Drop PNG or click to choose")
                .foregroundStyle(.secondary)
        }
        .onTapGesture {
            showingFilePicker = true
        }
        .onDrop(of: [.fileURL], isTargeted: $dragOver) { providers in
            handleDrop(providers)
        }
        .fileImporter(
            isPresented: $showingFilePicker,
            allowedContentTypes: [.png, .jpeg, .heic],
            allowsMultipleSelection: false
        ) { result in
            handleFileSelection(result)
        }
    }
}
```

---

## App Lifecycle & Initialization

### Standard App Entry Point

**Source:** `MusicServer/MusicServerApp.swift`

```swift
@main
struct MusicServerApp: App {
    // Services as @State (order matters for dependencies)
    @State private var folderManager = FolderManager()
    @State private var driveMonitor = DriveMonitor()
    @State private var bonjourAdvertiser = BonjourAdvertiser()

    @NSApplicationDelegateAdaptor(AppDelegate.self) private var appDelegate

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environment(folderManager)
                .environment(driveMonitor)
                .environment(bonjourAdvertiser)
                .onAppear {
                    restoreFolderAndSetupMonitoring()
                }
        }
        .commands {
            CommandGroup(replacing: .newItem) { }
        }
    }

    private func restoreFolderAndSetupMonitoring() {
        let restored = folderManager.restoreBookmark()
        if restored, let folderURL = folderManager.selectedFolderURL {
            _ = driveMonitor.startMonitoring(folderURL: folderURL)
        }
    }
}
```

---

### Service Initialization Order with .task

**Source:** `MusicClient/MusicClientApp.swift`

```swift
@main
struct MusicClientApp: App {
    @State private var serverDiscovery = ServerDiscovery()
    @State private var audioPlayer = AudioPlayer()
    @State private var nowPlayingInfoManager = NowPlayingInfoManager()
    @StateObject private var apiClient = MusicAPIClient()

    var body: some Scene {
        WindowGroup {
            RootView()
                .environment(serverDiscovery)
                .environment(audioPlayer)
                .environment(nowPlayingInfoManager)
                .environmentObject(apiClient)
                .task {
                    // ORDER OF INITIALIZATION:
                    // 1. Start server discovery
                    serverDiscovery.startDiscovery()

                    // 2. Configure dependent managers
                    nowPlayingInfoManager.configure(
                        audioPlayer: audioPlayer,
                        apiClient: apiClient
                    )
                }
                .onChange(of: serverDiscovery.selectedServer) { _, newServer in
                    // 3. React to changes
                    if let server = newServer, let url = server.baseURL {
                        apiClient.setBaseURL(url)
                    }
                }
        }
    }
}
```

---

### Scene Phase Handling (iOS)

**Source:** `Group Alarms/GroupAlarmsApp.swift`

```swift
@main
struct GroupAlarmsApp: App {
    @StateObject private var alarmKitManager = AlarmKitManager.shared
    @Environment(\.scenePhase) private var scenePhase

    var body: some Scene {
        WindowGroup {
            MainTabView()
                .task {
                    // Launch initialization
                    await cancelLegacyNotifications()
                    await requestAlarmPermissions()
                    await synchronizeAlarmsOnLaunch()
                }
                .onChange(of: scenePhase) { _, newPhase in
                    switch newPhase {
                    case .active:
                        // App came to foreground
                        Task { await synchronizeAlarmsOnLaunch() }
                    case .background:
                        // App went to background
                        Self.scheduleExpirationCheckTask()
                    case .inactive:
                        break
                    @unknown default:
                        break
                    }
                }
        }
    }
}
```

---

### Manager with Configure Pattern

**Source:** `MusicClient/Services/NowPlayingInfoManager.swift`

```swift
@MainActor
@Observable
final class NowPlayingInfoManager {
    private weak var audioPlayer: AudioPlayer?
    private weak var apiClient: MusicAPIClient?
    private var observationTask: Task<Void, Never>?

    init() {
        setupRouteChangeObserver()
    }

    /// Configure after managers are created
    func configure(audioPlayer: AudioPlayer, apiClient: MusicAPIClient) {
        self.audioPlayer = audioPlayer
        self.apiClient = apiClient
        setupRemoteCommands()
        startObservingAudioPlayer()
    }

    func cleanup() {
        observationTask?.cancel()
        clearNowPlayingInfo()
    }

    private func startObservingAudioPlayer() {
        observationTask?.cancel()
        observationTask = Task { [weak self] in
            while !Task.isCancelled {
                self?.checkForAudioPlayerChanges()
                try? await Task.sleep(for: .seconds(1))
            }
        }
    }
}
```

---

### FolderManager with Bookmark Restoration

**Source:** `MusicServer/Services/FolderManager.swift`

```swift
@MainActor
@Observable
public final class FolderManager {
    private enum Constants {
        static let bookmarkKey = "musicFolderBookmark"
    }

    public private(set) var selectedFolderURL: URL?
    public private(set) var isAccessingFolder: Bool = false

    /// Call on app launch to restore access
    @discardableResult
    public func restoreBookmark() -> Bool {
        guard let bookmarkData = userDefaults.data(forKey: Constants.bookmarkKey) else {
            return false
        }
        do {
            var isStale = false
            let url = try URL(resolvingBookmarkData: bookmarkData,
                            options: .withSecurityScope,
                            relativeTo: nil,
                            bookmarkDataIsStale: &isStale)
            selectedFolderURL = url
            startAccessingFolder()
            return true
        } catch {
            clearBookmark()
            return false
        }
    }

    public func startAccessingFolder() {
        guard let url = selectedFolderURL, !isAccessingFolder else { return }
        if url.startAccessingSecurityScopedResource() {
            isAccessingFolder = true
        }
    }

    public func stopAccessingFolder() {
        guard let url = selectedFolderURL, isAccessingFolder else { return }
        url.stopAccessingSecurityScopedResource()
        isAccessingFolder = false
    }
}
```

---

## MCP Memory Integration

Patterns for integrating LLM memory (Vestige MCP) with development workflows.

### Store Pattern for Automatic Recall

**Source:** This cookbook's creation session (2026-02-02)

When you solve a reusable problem, store it in Vestige so it surfaces automatically:

```javascript
// Using Vestige MCP tools from Claude

// 1. Store a code pattern
mcp__vestige__remember_pattern({
  name: "SwiftUI Window Layouts Cookbook",
  description: "Working patterns for macOS window layouts. Includes: NavigationSplitView, HSplitView variations, multi-window apps. Full cookbook at /path/to/PATTERNS-COOKBOOK.md",
  files: ["/path/to/PATTERNS-COOKBOOK.md"]
})

// 2. Store an architectural decision
mcp__vestige__remember_decision({
  decision: "Use HStack+Divider instead of HSplitView for complex layouts",
  rationale: "HSplitView has unpredictable vertical space filling on macOS",
  alternatives: ["HSplitView", "NSSplitView via NSViewRepresentable"],
  codebase: "all-macos-projects"
})

// 3. Search for relevant patterns (hybrid search)
mcp__vestige__search({
  query: "export dialog NSSavePanel video",
  limit: 5,
  min_similarity: 0.5
})
```

**Best for:** Building a "second brain" that surfaces relevant past solutions during coding.

---

### Dual-Trigger Pattern (CLAUDE.md + Vestige)

**Source:** This cookbook's creation session (2026-02-02)

Combine explicit triggers with semantic memory for reliable pattern recall:

**1. CLAUDE.md trigger (keyword-based):**
```markdown
## Pattern Cookbook

When implementing these UI patterns, **FIRST check** the cookbook:
- Window layouts (HSplitView, NavigationSplitView, 2-pane, 4-pane)
- Export dialogs (NSSavePanel, NSOpenPanel, progress indicators)
- File pickers, drag-and-drop, .fileImporter

**Location:** /path/to/PATTERNS-COOKBOOK.md
```

**2. Vestige memory (semantic-based):**
```javascript
// Stored patterns surface automatically when context matches
// e.g., "add an export dialog" triggers "Export Dialog & File Picker Patterns"
```

**Why both:**
- CLAUDE.md: Reliable keyword trigger, always in context
- Vestige: Semantic matching catches variations ("save panel" vs "export dialog")

**Best for:** Critical patterns that should never be forgotten.

---

### Session Log Integration

**Source:** `/log` command in Directions

Capture patterns at the moment of discovery, not later:

```markdown
## In /log command:

After syncing PROJECT_STATE.md, check for new patterns:

> "Did this session produce any reusable code patterns?"

**Trigger words to listen for:**
- "finally got X working"
- "figured out how to..."
- "this pattern works well"

If yes → run `/cookbook add` immediately
```

**Why:** Patterns captured immediately are more complete than extracted later.

---

### Memory Feedback Loop

**Source:** Vestige MCP documentation

Strengthen good memories, demote bad ones:

```javascript
// When user confirms a memory was helpful
mcp__vestige__promote_memory({ id: "memory-uuid" })

// When user says memory was wrong or unhelpful
mcp__vestige__demote_memory({ id: "memory-uuid" })
```

**Best for:** Self-improving memory that learns which patterns are actually useful.

---

## Agent Skills Integration

Patterns for extending Claude Code with reusable skills from skills.sh.

### Discover and Install Skills

**Source:** Session 2025-02-07

```bash
# Search for skills interactively
npx skills find

# Search by keyword
npx skills find "react"
npx skills find "swift"

# Install a skill repo globally (all skills in repo)
npx skills add <owner/repo> --yes --global --agent claude-code

# Examples:
npx skills add avdlee/swiftui-agent-skill --yes --global --agent claude-code
npx skills add obra/superpowers --yes --global --agent claude-code
npx skills add anthropics/skills --yes --global --agent claude-code
```

**Key flags:**
- `--yes` (`-y`): Skip confirmation prompts
- `--global` (`-g`): Install user-wide, not project-level
- `--agent claude-code`: Target Claude Code specifically

---

### Manage Installed Skills

**Source:** Session 2025-02-07

```bash
# List installed skills
npx skills list              # Project-level
npx skills list --global     # Global skills

# Check for updates
npx skills check

# Update all skills to latest
npx skills update

# Remove a skill
npx skills remove <skill-name> --global

# Remove all skills from a specific agent
npx skills remove --global --skill '*' --agent claude-code
```

---

### Recommended Skill Collections

**Source:** Session 2025-02-07

| Repo | Skills | Best For |
|------|--------|----------|
| `avdlee/swiftui-agent-skill` | 1 | SwiftUI patterns, state management, Liquid Glass |
| `avdlee/swift-concurrency-agent-skill` | 1 | async/await, actors, Swift 6 migration |
| `anthropics/skills` | 17 | PDF/DOCX/XLSX creation, frontend-design, MCP building |
| `obra/superpowers` | 14 | TDD, debugging, planning, verification, git worktrees |
| `wshobson/agents` | 146 | Architecture, testing, security, accessibility, marketing |
| `vercel-labs/agent-skills` | 4 | Web design, React best practices |
| `remotion-dev/skills` | 1 | Video processing with React |

---

### How Skills Activate

Skills load **automatically** based on context keywords in your prompts:

| You Say | Skills That Activate |
|---------|---------------------|
| "SwiftUI state management" | swiftui-expert-skill |
| "async/await actor isolation" | swift-concurrency |
| "design a dashboard" | ui-ux-pro-max, frontend-design |
| "debug this issue" | systematic-debugging |
| "write tests first" | test-driven-development |
| "create a PDF report" | pdf |

No manual invocation needed — skills enhance responses when relevant context is detected.

---

### Skills Location

```bash
# Global skills (available in all projects)
~/.claude/skills/
~/.agents/skills/  # Source, symlinked to above

# Project-level skills
./.claude/skills/
./.agents/skills/
```

**Best for:** Extending Claude Code with domain expertise that persists across sessions.

---

## Web Development Patterns

### Data Injection Pattern (Jinja2 → External JS)

**Source:** `PDF2Calendar/01_Project/templates/stats.html` + `static/js/stats.js`

When server-rendered templates have inline JavaScript with Jinja2 expressions, you can't simply move the JS to an external file. Use a data injection pattern:

**Template (stats.html):**
```html
<!-- Small inline script injects server-rendered data -->
<script>
    window.STATS_DATA = {
        dailyVisits: {{ daily_visits | tojson }},
        deviceData: {{ stats.page_visits.by_device | tojson }},
        exportDownload: {{ stats.export_download.by_parser | tojson }},
        // ... other server data
    };
</script>
<!-- Main logic in external file -->
<script src="/static/js/stats.js"></script>
```

**External JS (stats.js):**
```javascript
// Access server data via global object
const dailyData = window.STATS_DATA.dailyVisits;
const deviceData = window.STATS_DATA.deviceData;

// Use data in charts, etc.
new Chart(ctx, {
    data: { labels: dailyData.map(d => d[0]) }
});
```

**Benefits:**
- Separates data (server) from logic (client)
- External JS is cacheable
- ~90% of code moves to external file
- Only 10-20 lines of data assignment stays inline

**Best for:** Flask/Django/Jinja2 templates with significant inline JavaScript.

---

### Wave-Based Parallel Execution

**Source:** PDF2Calendar refactor session (2026-02-09)

Pattern for orchestrating multiple parallel tasks with fresh context per task:

**PLAN.md structure:**
```markdown
### Wave 1 (parallel - no dependencies)
- [ ] Task 1.1: Create file A
- [ ] Task 1.2: Create file B
- [ ] Task 1.3: Modify file C

### Wave 2 (depends on Wave 1)
- [ ] Task 2.1: Use files from Wave 1

### Wave 3 (verification)
- [ ] Task 3.1: Run tests
```

**Execution pattern (Claude Code):**
```javascript
// Wave 1: Spawn parallel tasks
Task(subagent_type="developer", prompt="Task 1.1: ...")
Task(subagent_type="developer", prompt="Task 1.2: ...")
Task(subagent_type="developer", prompt="Task 1.3: ...")

// Wait for all Wave 1 to complete
// Commit: git commit -m "feat(wave-1): description"
// Update PLAN.md checkboxes to [x]

// Wave 2: Sequential or parallel based on dependencies
Task(subagent_type="developer", prompt="Task 2.1: ...")
```

**Key principles:**
1. **Fresh context per task** - Each subagent starts clean, no conversation history
2. **Atomic commits** - One wave = one commit (easy rollback)
3. **State in files** - PLAN.md is source of truth, not conversation
4. **Orchestrator stays light** - Delegate heavy work to subagents

**Best for:** Multi-file refactors, feature implementations, any work that can be parallelized.

---

### ES Module Dependency Injection

**Source:** `PDF2Calendar/01_Project/static/js/modules/feedback.js`

When extracting JS code to ES modules, you often need access to objects from the main file (state machines, loggers, etc.). Passing direct references creates circular imports. Use callback injection:

**Module (feedback.js):**
```javascript
// Dependencies injected at init time (not imported)
let getWizardState = () => ({ currentStep: 1 });
let getSessionLog = () => ({ toArray: () => [], info: () => {} });

export const FeedbackModal = {
    init(options = {}) {
        // Accept getters instead of direct references
        if (options.getWizardState) getWizardState = options.getWizardState;
        if (options.getSessionLog) getSessionLog = options.getSessionLog;
        // ... rest of init
    },

    open() {
        const state = getWizardState();  // Call getter when needed
        const log = getSessionLog();
        log.info?.(`Feedback opened (Step ${state?.currentStep})`);
    }
};
```

**Main file (main.js):**
```javascript
import { FeedbackModal } from './modules/feedback.js';

// Inject dependencies with getters
FeedbackModal.init({
    getWizardState: () => Wizard.state,
    getSessionLog: () => SessionLog
});
```

**Benefits:**
- No circular imports (module doesn't import main)
- Module is testable (can mock dependencies)
- Lazy evaluation (gets current state, not stale reference)
- Default fallbacks for standalone usage

**Best for:** Extracting modals, widgets, or components that need access to main app state.

---

### Shared State Module Pattern

**Source:** `PDF2Calendar/01_Project/static/js/modules/state.js`

When a vanilla JS app has a state machine that multiple modules need to access, extract it to a shared module. This eliminates duplicate state and enables further modularization.

**State module (state.js):**
```javascript
// Shared state that other modules can import
export const state = {
    currentStep: 1,
    schedules: [],
    employees: [],
    dateRange: { start: null, end: null },
    selectedEmployee: null
};

// State manipulation functions
export function goToStep(step, skipAnimation = false) {
    if (step < 1 || step > 4) return false;
    if (step > state.maxUnlockedStep) return false;
    state.currentStep = step;
    updateUI();
    return true;
}

export function resetState() {
    Object.assign(state, {
        currentStep: 1,
        schedules: [],
        employees: [],
        // ... reset to defaults
    });
}

export function initWizard() {
    cacheElements();
    bindStepEvents();
    updateUI();
}
```

**Main file (main.js):**
```javascript
// Import state and functions (no duplicate definition needed)
import {
    state,
    goToStep,
    completeStep,
    setCardState,
    resetState,
    initWizard
} from './modules/state.js';

// Use directly
state.schedules = data.schedules;
completeStep(2);
goToStep(3);
```

**Other modules can now access state:**
```javascript
// calendar.js
import { state } from './state.js';

export function renderCalendar() {
    const schedules = state.schedules;  // Direct access!
    const dateRange = state.dateRange;
    // ... render logic
}
```

**Migration steps:**
1. Create state module with exported state object + functions
2. Add imports to main.js
3. Find/replace: `Wizard.state.` → `state.`, `Wizard.goToStep` → `goToStep`, etc.
4. Delete the original state machine object

**Benefits:**
- Eliminates duplicate state management code
- Enables further module extraction (views, utils can import state)
- Single source of truth for application state
- Cleaner main file (removed ~260 lines in PDF2Calendar)

**Best for:** Vanilla JS apps with state machines that have grown large (500+ lines).

---

## Timecode Display Typography

**Source:** `1-macOS/Penumbra/` (TimecodeView, ControlsRow, CurrentSelectionView)
**Use case:** Any video app displaying SMPTE timecode (HH:MM:SS:FF)

### The Problem

SF Mono (`.design(.monospaced)`) uses **slashed zeros** to distinguish `0` from `O`. This is correct for code editors but looks wrong in video timecode displays — professional NLEs like Final Cut Pro use clean round zeros.

### The Solution: SF Pro + `.monospacedDigit()`

```swift
// BAD — SF Mono, slashed zeros, too "code-like"
.font(.system(size: 32, weight: .light, design: .monospaced))

// GOOD — SF Pro with fixed-width digits, clean round zeros (FCP-style)
.font(.system(size: 32, weight: .thin).monospacedDigit())
```

### Weight Hierarchy for TC Displays

| Display | Weight | Rationale |
|---------|--------|-----------|
| Main TC (large, ~32pt) | `.thin` | Doesn't dominate the UI |
| Secondary TC (IN/OUT/DURATION, ~body) | `.light` | Readable at smaller size |
| Dimmed leading zeros | `.ultraLight` + `opacity(0.7)` | Subtle de-emphasis of `00:00:` prefix |

### NSFont Width Calculation (AppKit)

When using per-character layout with fixed-width frames, the `NSFont` for width measurement must match the rendered font:

```swift
// If rendering SF Pro .monospacedDigit(), measure with systemFont (NOT monospacedSystemFont)
let nsFont = NSFont.systemFont(ofSize: fontSize, weight: fontWeight.toNSFontWeight())
let digitWidth = NSAttributedString(string: "0", attributes: [.font: nsFont]).size().width
```

### Key Rule

**Timecode = `.monospacedDigit()`, Code = `.monospaced`**. Never use SF Mono for timecode in video apps.

---

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

## Context Menus

Right-click menus that change based on which pane the user clicked and what's selected. Four patterns from simple to advanced.

---

### Pattern 1: Basic `.contextMenu`

**Source:** `ClipSmart/Views/SnippetsView.swift`
**Use case:** Simple action list on a list item.

```swift
SnippetRow(snippet: snippet)
    .contextMenu {
        Button("Copy") {
            copySnippet(snippet)
        }

        Button("Edit") {
            selectedSnippet = snippet
            showingEditSheet = true
        }

        Divider()

        Button("Delete", role: .destructive) {
            snippetManager.deleteSnippet(snippet)
        }
    }
```

**Key rules:**
- `role: .destructive` renders the item in red and places it visually last
- `Divider()` separates action groups
- Attach to the row view, not the List

---

### Pattern 2: Conditional Items (State-Driven)

**Source:** `VAM/Views/Content/AssetGridView.swift`
**Use case:** Menu items that appear/disappear based on model state.

```swift
AssetGridItemView(asset: asset)
    .contextMenu {
        Button("Open in Finder") {
            NSWorkspace.shared.selectFile(asset.url.path, inFileViewerRootedAtPath: "")
        }

        Divider()

        if let proxy = asset.proxyFile {
            if proxy.status == .completed {
                Button("Delete Proxy", role: .destructive) {
                    proxyService.deleteProxy(for: asset)
                }
            }
            if proxy.status == .failed {
                Button("Retry Proxy") {
                    proxyQueue.enqueue([asset.id])
                }
            }
        } else {
            Button("Generate Proxy") {
                proxyQueue.enqueue([asset.id])
            }
            .disabled(!proxySettings.isConfigured)
        }
    }
```

**Key rule:** Use `if`/`else` inside the `@ViewBuilder` context menu closure. SwiftUI rebuilds the menu each time it's shown, so state is always current.

---

### Pattern 3: Extracted `@ViewBuilder` + Submenus

**Source:** `VideoWallpaper/UI/PlaylistLibraryView.swift`, `FileManagement/Views/FileContextMenu.swift`
**Use case:** Complex menus with nested options, checkmarks, toggle labels. Reusable across multiple views.

Extract the menu into a `@ViewBuilder` function:

```swift
@ViewBuilder
private func playlistContextMenu(for playlist: Playlist) -> some View {
    Button {
        playlistToRename = playlist
    } label: {
        Label("Rename…", systemImage: "pencil")
    }

    Button {
        library.duplicatePlaylist(playlist)
    } label: {
        Label("Duplicate", systemImage: "doc.on.doc")
    }

    Divider()

    // Nested submenu
    Menu {
        ForEach(SortOrder.allCases) { sortOrder in
            Button {
                var updated = playlist
                updated.sortOrder = sortOrder
                library.updatePlaylist(updated)
            } label: {
                HStack {
                    Text(sortOrder.displayName)
                    if playlist.sortOrder == sortOrder {
                        Spacer()
                        Image(systemName: "checkmark")
                    }
                }
            }
        }
    } label: {
        Label("Sort By", systemImage: "arrow.up.arrow.down")
    }

    // Toggle label that flips
    Button {
        var updated = playlist
        updated.shuffleEnabled.toggle()
        library.updatePlaylist(updated)
    } label: {
        Label(
            playlist.shuffleEnabled ? "Disable Shuffle" : "Enable Shuffle",
            systemImage: "shuffle"
        )
    }

    Divider()

    Button("Delete", role: .destructive) {
        library.deletePlaylist(id: playlist.id)
    }
}

// Apply:
PlaylistRow(playlist: playlist)
    .contextMenu { playlistContextMenu(for: playlist) }
```

**View extension pattern** for reusable context menus across files:

```swift
public struct FileContextMenu: View {
    let file: FileItem
    let onOpen: () -> Void
    let onQuickLook: () -> Void

    public var body: some View {
        Group {
            Button { onOpen() } label: {
                Label("Open", systemImage: "arrow.up.forward.app")
            }
            .keyboardShortcut(.return, modifiers: [])

            Button { onQuickLook() } label: {
                Label("Quick Look", systemImage: "eye")
            }
            .keyboardShortcut(.space, modifiers: [])

            Divider()

            Button { revealInFinder() } label: {
                Label("Reveal in Finder", systemImage: "folder")
            }

            // Dynamic "Open With" submenu
            Menu {
                let apps = NSWorkspace.shared.urlsForApplications(toOpen: file.url)
                ForEach(apps.prefix(10), id: \.self) { appURL in
                    Button {
                        NSWorkspace.shared.open([file.url], withApplicationAt: appURL,
                                                configuration: .init())
                    } label: {
                        Text(appURL.deletingPathExtension().lastPathComponent)
                    }
                }
                if apps.count > 10 {
                    Divider()
                    Button("Other…") { openWithOther() }
                }
            } label: {
                Label("Open With", systemImage: "arrow.up.forward.app.fill")
            }

            Divider()

            Button { copyPath() } label: {
                Label("Copy Path", systemImage: "doc.on.doc")
            }
        }
    }
}

// Reusable View extension:
extension View {
    func fileContextMenu(
        for file: FileItem?,
        onOpen: @escaping () -> Void,
        onQuickLook: @escaping () -> Void
    ) -> some View {
        Group {
            if let file {
                self.contextMenu {
                    FileContextMenu(file: file, onOpen: onOpen, onQuickLook: onQuickLook)
                }
            } else {
                self
            }
        }
    }
}
```

**Best for:** Complex menus shared across multiple views, menus with submenus or dynamic system data.

---

### Pattern 4: AppKit `NSMenuDelegate` (NSTableView / NSViewRepresentable)

**Source:** `VCR/Views/AppKit/FileTableView.swift`
**Use case:** Context menus on NSTableView rows inside an `NSViewRepresentable`. Menu built dynamically at display time.

```swift
// In makeNSView:
let menu = NSMenu()
menu.delegate = context.coordinator
tableView.menu = menu

// In Coordinator:
@MainActor
final class Coordinator: NSObject, NSTableViewDataSource, NSTableViewDelegate, NSMenuDelegate {
    var entries: [FileEntry] = []
    var onScan: (UUID) -> Void
    var onRemove: (UUID) -> Void

    // Called right before the menu appears
    func menuNeedsUpdate(_ menu: NSMenu) {
        menu.removeAllItems()

        guard let tableView,
              tableView.clickedRow >= 0,
              tableView.clickedRow < entries.count
        else { return }

        let entry = entries[tableView.clickedRow]

        let scanItem = NSMenuItem(
            title: "Scan",
            action: #selector(contextScan(_:)),
            keyEquivalent: ""
        )
        scanItem.target = self
        scanItem.representedObject = entry.id
        scanItem.isEnabled = !entry.isScanning && entry.scanResult == nil
        menu.addItem(scanItem)

        let removeItem = NSMenuItem(
            title: "Remove",
            action: #selector(contextRemove(_:)),
            keyEquivalent: ""
        )
        removeItem.target = self
        removeItem.representedObject = entry.id
        menu.addItem(removeItem)

        // Conditional items
        if entry.hasRepairableIssues {
            menu.addItem(.separator())
            let repairItem = NSMenuItem(
                title: "Queue Repair",
                action: #selector(contextQueueRepair(_:)),
                keyEquivalent: ""
            )
            repairItem.target = self
            repairItem.representedObject = entry.id
            menu.addItem(repairItem)
        }
    }

    @objc private func contextScan(_ sender: NSMenuItem) {
        guard let id = sender.representedObject as? UUID else { return }
        onScan(id)
    }

    @objc private func contextRemove(_ sender: NSMenuItem) {
        guard let id = sender.representedObject as? UUID else { return }
        onRemove(id)
    }
}
```

**Key rules:**
- `menuNeedsUpdate(_:)` fires right before display — always rebuild from scratch
- Use `representedObject` to pass data (row ID) from menu item to action handler
- `tableView.clickedRow` gives the row the user right-clicked (not the selection)
- Set `target = self` on every item — otherwise the responder chain may route incorrectly

**Best for:** NSTableView context menus where you need per-row, state-aware menus inside an `NSViewRepresentable`.

---

### Choosing a Pattern

| Need | Pattern | Example |
|---|---|---|
| Simple actions on a list item | **1: Basic** | Copy, Edit, Delete |
| Items that vary by item state | **2: Conditional** | Show "Retry" only on failures |
| Complex, reusable, with submenus | **3: Extracted** | File browser, playlist manager |
| NSTableView rows in AppKit wrapper | **4: NSMenuDelegate** | VCR file table |

**Anti-patterns:**
- Don't put 15+ items in a flat context menu — use submenus (`Menu { }`) to group
- Don't attach `.contextMenu` to the `List` itself — attach it to each row
- Don't use SwiftUI `.contextMenu` on an `NSViewRepresentable` — use `NSMenu` + delegate on the underlying `NSView`
- Don't duplicate menu items that already exist in the menu bar — users expect Cmd+C to work via the menu, not from a context menu

---

## Quick Reference Table

| Pattern | Source Project | Use Case |
|---------|---------------|----------|
| **App Shell Standard** | **Penumbra** | **MANDATORY — base for all macOS apps** |
| FCPToolbarButtonStyle | Penumbra | Flat 4px toolbar buttons, replaces round |
| PaneToggleButton | Penumbra | Toolbar toggle with FCPToolbarButtonStyle |
| Theme struct | Penumbra | Dark color palette (0.10/0.15 grays) |
| .hiddenTitleBar + .dark | Penumbra | No system chrome, forced dark mode |
| .toolbarRole(.editor) | Penumbra | Editor toolbar, no nav chrome |
| HSplitView + @AppStorage | Penumbra | Togglable panes with persisted visibility |
| InfoStripView | Penumbra | Contextual bar below toolbar |
| Separate view structs | swiftdifferently.com | Performance (diffing checkpoints) |
| .equatable() modifier | swiftdifferently.com | Views with closures |
| debugRender() extension | swiftdifferently.com | Visualize re-renders |
| NavigationSplitView | Directions | Sidebar navigation |
| HSplitView (simple) | TextScanner | 2-pane layouts |
| HSplitView (complex) | Phosphor | Preview + timeline |
| HSplitView (3-section) | AppUpdater | Sidebar with header/footer |
| Multi-window + Menu Bar | WindowMind | Background utilities |
| Autosave dividers | Penumbra, VCR | Remember pane sizes |
| NSTableView in SwiftUI | VCR | Column headers, cell reuse, native table |
| AppKitButton | Convention | Native NSButton, replaces SwiftUI Button |
| AppKitCheckbox | Convention | Native checkbox toggle |
| AppKitPopup | Convention | Native NSPopUpButton dropdown |
| AppKitSegmented | Convention | Native segmented control |
| AppKitSlider | Convention | Native NSSlider |
| AppKitTextField | Convention | Native NSTextField input |
| AppKitToolbarButtonStyle | Penumbra | Native look in SwiftUI .toolbar |
| NSSavePanel + progress | Phosphor | File export |
| NSOpenPanel (folder) | Directions | Folder selection |
| Security-scoped bookmarks | Directions | Persistent folder access |
| .fileImporter + drag/drop | CropBatch | Image picking |
| @main + .task init | MusicClient | Service initialization |
| Scene phase handling | Group Alarms | iOS lifecycle |
| Manager.configure() | MusicClient | Dependency injection |
| FolderManager | MusicServer | Bookmark restoration |
| **Layout Template A: Browser** | **FCP, Penumbra** | **Sidebar + grid + inspector** |
| **Layout Template B: Editor** | **FCP, Phosphor** | **Viewer + timeline + sidebar** |
| **Layout Template C: Organizer** | **AppUpdater** | **Source list + full detail** |
| **Layout Template D: Dual Viewer** | **FCP compare** | **Side-by-side / overlay / wipe** |
| **Layout Template E: Workspace** | **FCP tabs** | **Tab-switched distinct layouts** |
| KB Tier 1: SwiftUI Commands | VideoScout, Penumbra | Menu-bar shortcuts (Cmd+key) |
| KB Tier 2: .onKeyPress | QuickMotion, VideoScout | View-level JKL, arrows, space |
| KB Tier 3: NSEvent local monitor | Penumbra, VideoWallpaper | App-wide single-key, consume events |
| KB Tier 4: KeyboardShortcutManager | Penumbra | User-customizable, recordable |
| Context menu: basic | ClipSmart | Simple action list on rows |
| Context menu: conditional | VAM | State-driven items |
| Context menu: extracted + submenus | VideoWallpaper, FileManagement | Reusable, nested menus |
| Context menu: NSMenuDelegate | VCR | NSTableView row menus |
| Vestige pattern storage | This cookbook | Auto-recall past solutions |
| Dual-trigger (CLAUDE.md + Vestige) | This cookbook | Reliable pattern surfacing |
| Session log integration | Directions | Capture patterns when fresh |
| skills.sh global install | Session 2025-02-07 | Extend Claude Code with domain skills |
| Skills auto-activation | Session 2025-02-07 | Context-based skill loading |
| TC font: SF Pro .monospacedDigit() | Penumbra | Timecode without slashed zeros (FCP-style) |
| Jinja2 data injection | PDF2Calendar | Server→client data passing |
| Wave-based execution | Directions /execute | Parallel task orchestration |
| ES Module DI | PDF2Calendar | Avoid circular imports in JS modules |
| Shared State Module | PDF2Calendar | Centralized state for vanilla JS apps |

---

## Subprocess & URL Patterns

### URL Path for Subprocesses — Avoid `url.path()`

**Source:** `CutSnaps/Services/FFmpegService.swift`
**Problem:** Swift's `URL.path()` method (macOS 13+) defaults to `percentEncoded: true`, encoding spaces as `%20`. When passed to `Foundation.Process` or any subprocess, the path is garbled.

```swift
// BAD — spaces become %20, subprocess gets "No such file"
let args = ["-i", url.path()]

// GOOD — decoded path, spaces preserved
let args = ["-i", url.path(percentEncoded: false)]

// Also applies to embedded paths in filter strings:
let filter = "metadata=print:file=\(tempFile.path(percentEncoded: false))"
```

**Why it's subtle:** The deprecated `url.path` property (no parens) auto-decodes. The new `url.path()` method does not. Migrating from `.path` to `.path()` silently breaks paths with spaces.

---

### Security-Scoped Access Across Async Pipelines

**Source:** `CutSnaps/Models/VideoFile.swift`
**Problem:** File pickers and drag-and-drop grant security-scoped access, but calling `stopAccessingSecurityScopedResource()` before an async pipeline completes kills access for the entire chain.

```swift
// BAD — access revoked before async processing finishes
for url in urls {
    let accessing = url.startAccessingSecurityScopedResource()
    importVideo(url: url)  // enqueues async work
    if accessing { url.stopAccessingSecurityScopedResource() }  // too early!
}

// GOOD — manage access lifecycle on the model
@Observable
class VideoFile: Identifiable {
    let url: URL
    private var isAccessingSecurityScope = false

    func startAccess() {
        guard !isAccessingSecurityScope else { return }
        isAccessingSecurityScope = url.startAccessingSecurityScopedResource()
    }

    func stopAccess() {
        guard isAccessingSecurityScope else { return }
        url.stopAccessingSecurityScopedResource()
        isAccessingSecurityScope = false
    }

    deinit {
        if isAccessingSecurityScope {
            url.stopAccessingSecurityScopedResource()
        }
    }
}

// Call startAccess() on import, stopAccess() when processing completes or model removed
```

**Rule:** If `startAccessingSecurityScopedResource()` and the work using that resource are on different async boundaries, the access token must outlive the async chain.

---

## Anti-Patterns to Avoid

| Anti-Pattern | Problem | Solution |
|--------------|---------|----------|
| @ViewBuilder methods for subviews | No performance benefit — re-executes fully | Use separate view structs |
| Monolithic view bodies | Every state change re-evaluates all children | Extract subviews as structs |
| HSplitView layout bugs | Doesn't fill vertical space | Use HStack + Divider |
| SwiftUI controls on macOS | Capsule buttons, Catalyst look | AppKit wrappers via NSViewRepresentable |
| `try?` swallowing errors | Silent failures | Handle errors explicitly |
| Missing `stopAccessingSecurityScopedResource()` | Resource leaks | Always use `defer` or model lifecycle |
| `url.path()` for subprocesses | Percent-encodes spaces, breaks paths | Use `url.path(percentEncoded: false)` |
| Single AI review | Misses bugs | Multi-model validation |
| >500 line files | Unmaintainable | Extract managers/services |

---

*Generated from production code across Penumbra, Phosphor, Directions, MusicServer, AppUpdater, CropBatch, QuickMotion, WindowMind, and other projects.*
