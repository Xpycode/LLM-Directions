# Swift/SwiftUI Patterns Cookbook

**Extracted from working production code across 15+ projects.**
**Last updated: 2026-02-09**

---

## Table of Contents

1. [Window Layouts](#window-layouts)
2. [SwiftUI Performance](#swiftui-performance)
3. [Export & File Dialogs](#export--file-dialogs)
4. [App Lifecycle & Initialization](#app-lifecycle--initialization)
5. [MCP Memory Integration](#mcp-memory-integration)
6. [Agent Skills Integration](#agent-skills-integration)
7. [Web Development Patterns](#web-development-patterns)
8. [Quick Reference Table](#quick-reference-table)

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

**Source:** `Penumbra/Utils/View+SplitViewAutosave.swift`

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

## Quick Reference Table

| Pattern | Source Project | Use Case |
|---------|---------------|----------|
| Separate view structs | swiftdifferently.com | Performance (diffing checkpoints) |
| .equatable() modifier | swiftdifferently.com | Views with closures |
| debugRender() extension | swiftdifferently.com | Visualize re-renders |
| NavigationSplitView | Directions | Sidebar navigation |
| HSplitView (simple) | TextScanner | 2-pane layouts |
| HSplitView (complex) | Phosphor | Preview + timeline |
| HSplitView (3-section) | AppUpdater | Sidebar with header/footer |
| Multi-window + Menu Bar | WindowMind | Background utilities |
| Autosave dividers | Penumbra | Remember pane sizes |
| NSSavePanel + progress | Phosphor | File export |
| NSOpenPanel (folder) | Directions | Folder selection |
| Security-scoped bookmarks | Directions | Persistent folder access |
| .fileImporter + drag/drop | CropBatch | Image picking |
| @main + .task init | MusicClient | Service initialization |
| Scene phase handling | Group Alarms | iOS lifecycle |
| Manager.configure() | MusicClient | Dependency injection |
| FolderManager | MusicServer | Bookmark restoration |
| Vestige pattern storage | This cookbook | Auto-recall past solutions |
| Dual-trigger (CLAUDE.md + Vestige) | This cookbook | Reliable pattern surfacing |
| Session log integration | Directions | Capture patterns when fresh |
| skills.sh global install | Session 2025-02-07 | Extend Claude Code with domain skills |
| Skills auto-activation | Session 2025-02-07 | Context-based skill loading |
| Jinja2 data injection | PDF2Calendar | Server→client data passing |
| Wave-based execution | Directions /execute | Parallel task orchestration |
| ES Module DI | PDF2Calendar | Avoid circular imports in JS modules |
| Shared State Module | PDF2Calendar | Centralized state for vanilla JS apps |

---

## Anti-Patterns to Avoid

| Anti-Pattern | Problem | Solution |
|--------------|---------|----------|
| @ViewBuilder methods for subviews | No performance benefit — re-executes fully | Use separate view structs |
| Monolithic view bodies | Every state change re-evaluates all children | Extract subviews as structs |
| HSplitView layout bugs | Doesn't fill vertical space | Use HStack + Divider |
| `try?` swallowing errors | Silent failures | Handle errors explicitly |
| Missing `stopAccessingSecurityScopedResource()` | Resource leaks | Always use `defer` |
| Single AI review | Misses bugs | Multi-model validation |
| >500 line files | Unmaintainable | Extract managers/services |

---

*Generated from production code across Penumbra, Phosphor, Directions, MusicServer, AppUpdater, CropBatch, QuickMotion, WindowMind, and other projects.*
