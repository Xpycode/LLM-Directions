## Workspace Switching

Toolbar-driven mode or view switching that replaces the entire content area. Three patterns from lightweight pane toggles to full workspace systems.

---

### Pattern 1: View Mode Switching (Toolbar Buttons)

**Source:** `Penumbra/Views/ContentView.swift`
**Use case:** Switch between grid, list, and single-item views.

```swift
enum WorkspaceLayout: String, CaseIterable {
    case grid, list, single

    var icon: String {
        switch self {
        case .grid:   return "rectangle.grid.3x3"
        case .list:   return "rectangle.grid.1x3"
        case .single: return "rectangle.grid.1x2"
        }
    }
}

@State private var selectedWorkspace: WorkspaceLayout = .single

var body: some View {
    VStack(spacing: 0) {
        switch selectedWorkspace {
        case .grid:
            MediaGridView(library: library)
        case .list:
            MediaListView(library: library)
        case .single:
            SingleVideoView(library: library)
        }
    }
    .toolbar {
        ToolbarItemGroup(placement: .principal) {
            HStack {
                ForEach(WorkspaceLayout.allCases, id: \.self) { layout in
                    PaneToggleButton(
                        isOn: Binding(
                            get: { selectedWorkspace == layout },
                            set: { if $0 { selectedWorkspace = layout } }
                        ),
                        iconName: layout.icon,
                        help: layout.rawValue.capitalized
                    )
                }
            }
            .buttonStyle(.borderless)
        }
    }
    .toolbarRole(.editor)
}
```

**Key technique:** `PaneToggleButton` with a computed `Binding` that maps a boolean to an enum case. Only the active button shows as "on".

**Best for:** Same data, different presentation (grid vs list vs detail). The sidebar and inspector stay the same — only the center content changes.

---

### Pattern 2: Tool Mode Switching (Segmented Picker)

**Source:** `CropBatch/Models/AppState.swift`, `CropBatch/ContentView.swift`
**Use case:** Editor modes that change both the controls and the canvas overlay.

```swift
enum EditorTool: String, CaseIterable, Identifiable {
    case crop = "Crop"
    case blur = "Blur"

    var id: String { rawValue }

    var icon: String {
        switch self {
        case .crop: return "crop"
        case .blur: return "eye.slash"
        }
    }
}

// In an @Observable AppState:
var currentTool: EditorTool = .crop

// Segmented picker in sidebar:
Picker("Tool", selection: $appState.currentTool) {
    ForEach(EditorTool.allCases) { tool in
        Label(tool.rawValue, systemImage: tool.icon).tag(tool)
    }
}
.pickerStyle(.segmented)
.labelsHidden()

// Controls change per mode:
if appState.currentTool == .crop {
    CropControlsView()
} else {
    BlurToolSettingsPanel()
}

// Canvas overlay changes per mode:
if appState.currentTool == .crop {
    cropOverlay
    cropHandles
}
if appState.currentTool == .blur {
    BlurEditorView(/* ... */)
}
```

**Key technique:** `.pickerStyle(.segmented)` gives native macOS segmented control appearance. Mode enum lives in `@Observable` state so both the sidebar controls and the canvas respond to changes.

**Best for:** Editor modes where the tool/controls change but the canvas and data model stay the same.

---

### Pattern 3: Full Workspace Switching (Sidebar-Driven)

**Source:** `VOLTLAS/Sources/Views/Screens/MainView.swift`
**Use case:** Entirely different screens driven by sidebar navigation — dashboard, search, detail, comparison.

```swift
enum SidebarItem: Hashable {
    case dashboard
    case compare
    case search
    case volume(UUID)
}

@State private var selectedItem: SidebarItem? = .dashboard

var body: some View {
    HSplitView {
        // Sidebar with navigation items
        List(selection: $selectedItem) {
            Section("Overview") {
                Label("Dashboard", systemImage: "chart.bar")
                    .tag(SidebarItem.dashboard)
                Label("Compare", systemImage: "arrow.left.arrow.right")
                    .tag(SidebarItem.compare)
                Label("Search", systemImage: "magnifyingglass")
                    .tag(SidebarItem.search)
            }

            Section("Volumes") {
                ForEach(volumes) { volume in
                    Label(volume.name, systemImage: "externaldrive")
                        .tag(SidebarItem.volume(volume.id))
                }
            }
        }
        .frame(minWidth: 200, idealWidth: 240, maxWidth: 350)

        // Content switches entirely based on sidebar selection
        detailContent
            .frame(minWidth: 500)
    }
}

@ViewBuilder
private var detailContent: some View {
    switch selectedItem {
    case .dashboard, .none:
        DashboardView()
    case .compare:
        ComparisonView()
    case .search:
        SearchView()
    case .volume(let id):
        VolumeDetailView(volumeID: id)
    }
}
```

**Key technique:** `@ViewBuilder` with `switch` on an enum — each case renders a completely different screen. The enum can have associated values (`.volume(UUID)`) for parameterized screens.

**Best for:** Apps with distinct functional areas (dashboard, analytics, settings, per-item detail). Each "workspace" is a fully independent view hierarchy.

---

### Pattern 4: Persistent Mode with `@AppStorage`

**Source:** `VideoScout/Views/ContentView.swift`
**Use case:** Workspace selection that survives app relaunch.

```swift
@AppStorage("activeWorkspace") private var workspace: String = "edit"

// Enum with RawRepresentable for @AppStorage:
enum Workspace: String, CaseIterable {
    case importMedia = "import"
    case edit = "edit"
    case export = "export"

    var icon: String {
        switch self {
        case .importMedia: return "square.and.arrow.down"
        case .edit:        return "slider.horizontal.3"
        case .export:      return "square.and.arrow.up"
        }
    }
}

private var activeWorkspace: Workspace {
    get { Workspace(rawValue: workspace) ?? .edit }
    set { workspace = newValue.rawValue }
}
```

**Key rule:** `@AppStorage` only stores `String`/`Int`/`Bool`/`Double`/`Data`/`URL`. For enums, use `rawValue: String` and a computed property to bridge.

---

### Pattern 5: Sub-Mode within a Workspace (Nested Switch)

**Source:** `VOLTLAS/Sources/Views/Screens/ComparisonView.swift`
**Use case:** A workspace that itself has modes — e.g., a comparison screen with "setup" and "results" phases.

```swift
enum ComparisonMode: String, CaseIterable, Identifiable {
    case specific = "Compare Selected"
    case oneVsAll = "One vs All"
    case global = "Global Dedup"

    var id: String { rawValue }
}

@Observable
class ComparisonViewModel {
    var selectedMode: ComparisonMode = .specific
    var showResults = false
}

var body: some View {
    VStack {
        if viewModel.showResults {
            ResultsView(viewModel: viewModel)
        } else {
            VStack {
                // Mode picker
                Picker("Mode", selection: $viewModel.selectedMode) {
                    ForEach(ComparisonMode.allCases) { mode in
                        Text(mode.rawValue).tag(mode)
                    }
                }
                .pickerStyle(.segmented)
                .labelsHidden()

                // Content varies by mode
                switch viewModel.selectedMode {
                case .specific:  MultiVolumeSelector(viewModel: viewModel)
                case .oneVsAll:  SingleVolumeSelector(viewModel: viewModel)
                case .global:    EmptyView()
                }

                Button("Compare") { viewModel.runComparison() }
            }
        }
    }
}
```

**Key technique:** Two-level switching — outer boolean (`showResults`) for phase, inner enum (`selectedMode`) for variant. Each level uses the lightest mechanism that works.

---

### Choosing a Pattern

| Need | Pattern | Key Trait |
|---|---|---|
| Same data, different layout (grid/list) | **1: View Mode** | `PaneToggleButton` + enum binding |
| Editor tool modes | **2: Tool Mode** | `.segmented` picker, controls + canvas change |
| Entirely different screens | **3: Sidebar-Driven** | `@ViewBuilder switch` on enum with associated values |
| Mode that persists across launches | **4: @AppStorage** | String raw value bridge |
| Workspace with sub-modes | **5: Nested** | Outer phase + inner variant |

**Anti-patterns:**
- Don't use `TabView` for workspace switching in pro apps — it creates iOS-style tabs at the top. Use `HSplitView` sidebar or toolbar buttons instead
- Don't animate workspace transitions with `.animation` on the switch — the content change is structural, not a value change. If you want transitions, use `.transition()` on each branch with `withAnimation`
- Don't put workspace state in a view-local `@State` if other views need to read it — use `@Observable` or `@AppStorage`

---

