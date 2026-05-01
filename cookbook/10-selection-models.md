## Selection Models

How selection works in pro apps: single item, multi-select, cross-pane propagation, and keyboard navigation. The core principle is **one source of truth** — selection lives in a shared `@Observable` model, not scattered across views.

---

### Pattern 1: Single Selection (List / Sidebar)

**Source:** `VideoScout/Views/Sidebar/VideoListView.swift`
**Use case:** Sidebar list where selecting an item drives a detail view.

```swift
@Binding var selectedVideo: VideoAsset?

var body: some View {
    List(selection: $selectedVideo) {
        ForEach(videos) { video in
            VideoRowView(video: video)
                .tag(video)
        }
    }
    .onDeleteCommand {
        guard let video = selectedVideo else { return }
        selectedVideo = nil
        modelContext.delete(video)
    }
}
```

**Key rules:**
- Bind to an optional model type: `@Binding var selectedVideo: VideoAsset?`
- Every row needs `.tag(video)` — without it, `List(selection:)` won't work
- `nil` means nothing selected

---

### Pattern 2: Multi-Selection with `Set<ID>`

**Source:** `Penumbra/Views/MediaListView.swift`
**Use case:** File list or table where the user selects multiple items for batch operations.

```swift
@State private var selection = Set<Video.ID>()

var body: some View {
    Table(filteredVideos, selection: $selection) {
        TableColumn("Name") { video in Text(video.name) }
        TableColumn("Duration") { video in Text(video.durationString) }
    }
    .onChange(of: selection) { _, newSelection in
        // Drive single-item detail from first selection
        library.selectedVideo = library.videos.first { newSelection.contains($0.id) }
    }

    // Footer with batch actions
    HStack {
        Text("\(selection.count) of \(filteredVideos.count) selected")
        Spacer()
        Button(action: deleteSelected) {
            Image(systemName: "trash")
        }
        .disabled(selection.isEmpty)
    }
}

private func deleteSelected() {
    let toDelete = library.videos.filter { selection.contains($0.id) }
    for video in toDelete {
        library.removeVideo(video)
    }
    selection.removeAll()
}
```

**Key rules:**
- `Set<Video.ID>` (not `Set<Video>`) — use the ID type for hashing efficiency
- `Table(selection:)` and `List(selection:)` both support `Set<>` for multi-select
- Filter the data source by the set: `library.videos.filter { selection.contains($0.id) }`

---

### Pattern 3: Grid Selection (LazyVGrid)

**Source:** `VideoScout/Views/Content/ShotGridView.swift`
**Use case:** Thumbnail grid with tap-to-select and keyboard arrow navigation.

```swift
@Binding var selectedShot: Shot?

private let columns = [GridItem(.adaptive(minimum: 150))]

var body: some View {
    ScrollView {
        LazyVGrid(columns: columns, spacing: 12) {
            ForEach(sortedShots) { shot in
                ShotThumbnailView(shot: shot, isSelected: selectedShot?.id == shot.id)
                    .onTapGesture { selectedShot = shot }
            }
        }
    }
    .onKeyPress(.leftArrow) {
        navigateShot(direction: -1)
        return .handled
    }
    .onKeyPress(.rightArrow) {
        navigateShot(direction: 1)
        return .handled
    }
}

private func navigateShot(direction: Int) {
    let sorted = sortedShots
    guard !sorted.isEmpty else { return }

    guard let current = selectedShot,
          let index = sorted.firstIndex(where: { $0.id == current.id }) else {
        selectedShot = sorted.first
        return
    }

    let newIndex = index + direction
    if sorted.indices.contains(newIndex) {
        selectedShot = sorted[newIndex]
    }
}
```

**Key rules:**
- `LazyVGrid` doesn't have built-in `selection:` — use `.onTapGesture` and manual highlighting
- Pass `isSelected` bool to each cell for visual state
- Arrow key navigation uses index math on the sorted array
- Fallback to first item when nothing is selected

---

### Pattern 4: NSTableView Selection (AppKit ↔ SwiftUI Sync)

**Source:** `VCR/Views/AppKit/FileTableView.swift`
**Use case:** `NSViewRepresentable` table with bidirectional selection sync.

```swift
struct FileTableView: NSViewRepresentable {
    let entries: [FileEntry]
    @Binding var selectedFileID: UUID?

    func updateNSView(_ scrollView: NSScrollView, context: Context) {
        let coordinator = context.coordinator

        // SwiftUI → AppKit sync (guard against loops)
        if !coordinator.isUpdatingSelection {
            let desiredRow: Int
            if let id = selectedFileID,
               let index = entries.firstIndex(where: { $0.id == id }) {
                desiredRow = index
            } else {
                desiredRow = -1
            }

            if tableView.selectedRow != desiredRow {
                coordinator.isUpdatingSelection = true
                if desiredRow >= 0 {
                    tableView.selectRowIndexes(IndexSet(integer: desiredRow),
                                               byExtendingSelection: false)
                } else {
                    tableView.deselectAll(nil)
                }
                DispatchQueue.main.async {
                    coordinator.isUpdatingSelection = false
                }
            }
        }
    }

    @MainActor
    final class Coordinator: NSObject, NSTableViewDelegate {
        var isUpdatingSelection = false

        func tableViewSelectionDidChange(_ notification: Notification) {
            guard !isUpdatingSelection else { return }
            isUpdatingSelection = true
            defer { isUpdatingSelection = false }

            guard let tableView else { return }
            let row = tableView.selectedRow
            let newID = row >= 0 && row < entries.count ? entries[row].id : nil

            if parent.selectedFileID != newID {
                parent.selectedFileID = newID
            }
        }
    }
}
```

**Critical:** The `isUpdatingSelection` flag prevents infinite loops. Without it: SwiftUI sets selection → `updateNSView` → `selectRowIndexes` → `tableViewSelectionDidChange` → sets binding → `updateNSView` → forever.

---

### Pattern 5: Cross-Pane Propagation (Shared Observable)

**Source:** `Penumbra/Views/ContentView.swift`, `Penumbra/Models/VideoLibrary.swift`
**Use case:** Selection in one pane drives content in other panes.

```swift
// Shared model — single source of truth
@Observable
class VideoLibrary {
    var videos: [Video] = []
    var selectedVideo: Video? = nil

    func removeVideo(_ video: Video) {
        videos.removeAll { $0.id == video.id }
        if selectedVideo?.id == video.id {
            // Smart fallback: pick adjacent item, not just nil
            if let index = videos.firstIndex(where: { $0.id == video.id }) {
                selectedVideo = videos.indices.contains(index) ? videos[index] : videos.last
            } else {
                selectedVideo = videos.first
            }
        }
    }
}

// Root view passes to all panes
struct ContentView: View {
    @State private var library = VideoLibrary()

    var body: some View {
        HSplitView {
            if showSidebar {
                MediaListView(library: library)          // writes library.selectedVideo
            }
            VideoPlayerView(video: library.selectedVideo) // reads
            if showInspector {
                InspectorView(video: library.selectedVideo) // reads
            }
        }
    }
}
```

**The pattern:**
- `@Observable` model holds both data and selection state
- List pane **writes** `library.selectedVideo`
- Detail and inspector panes **read** `library.selectedVideo`
- Deletion logic auto-selects adjacent item (never leaves user with blank screen)

---

### Pattern 6: Two-Level Selection (Sidebar + Content)

**Source:** `VAM/Views/ContentView.swift`
**Use case:** Sidebar selects a category/collection, content area selects an item within it.

```swift
@State private var selectedSidebarItem: SidebarItem? = .allVideos
@State private var selectedAsset: VideoAsset?

var body: some View {
    HSplitView {
        if showSidebar {
            SidebarView(selection: $selectedSidebarItem)
        }

        AssetGridView(
            sidebarSelection: selectedSidebarItem,   // read-only: filters content
            selectedAsset: $selectedAsset             // read-write: item selection
        )

        if showInspector {
            AssetDetailView(asset: selectedAsset)     // reads item selection
        }
    }
}
```

**The pattern:**
- Level 1: `selectedSidebarItem` (category) — passed as read-only to filter the grid
- Level 2: `selectedAsset` (item) — passed as binding, drives the inspector
- Changing sidebar selection should clear or update the item selection

---

### Choosing a Pattern

| Need | Pattern | Key Trait |
|---|---|---|
| One item from a list | **1: Single** | `@Binding var selected: Item?` + `.tag()` |
| Batch operations (delete, export) | **2: Multi-select** | `Set<Item.ID>` + filter by set |
| Thumbnail grid with keyboard nav | **3: Grid** | `.onTapGesture` + arrow key index math |
| AppKit table in SwiftUI | **4: NSTableView** | `isUpdatingSelection` loop guard |
| Selection drives multiple panes | **5: Cross-pane** | `@Observable` with shared selection |
| Category → item drill-down | **6: Two-level** | Sidebar binds category, grid binds item |

**Deletion rule:** When removing the selected item, auto-select the adjacent item (next, or last if at end). Never leave the user staring at an empty detail pane.

---

