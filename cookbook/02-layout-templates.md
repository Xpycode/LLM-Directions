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

