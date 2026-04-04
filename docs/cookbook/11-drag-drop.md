## Drag & Drop

Two categories: **external drops** (files from Finder into your app) and **internal drag** (reordering items within or between panes). Most apps need external drops; internal drag is for editors and organizers.

---

### Pattern 1: Basic File Drop (SwiftUI `.onDrop`)

**Source:** `CropBatch/Views/DropZoneView.swift`, `VideoCorruptor/Views/ContentView.swift`
**Use case:** Drop zone that accepts files from Finder.

```swift
@State private var isDropTargeted = false

var body: some View {
    ContentArea()
        .overlay {
            if isDropTargeted {
                RoundedRectangle(cornerRadius: 8)
                    .stroke(Theme.accent, lineWidth: 2)
                    .background(Theme.accent.opacity(0.1))
            }
        }
        .onDrop(of: [.fileURL], isTargeted: $isDropTargeted) { providers in
            handleDrop(providers: providers)
        }
}

private func handleDrop(providers: [NSItemProvider]) -> Bool {
    var handled = false

    for provider in providers {
        if provider.canLoadObject(ofClass: URL.self) {
            _ = provider.loadObject(ofClass: URL.self) { url, _ in
                if let url {
                    Task { @MainActor in
                        appState.addFiles(from: [url])
                    }
                }
            }
            handled = true
        }
    }

    return handled
}
```

**Key rules:**
- `isTargeted` drives visual feedback (border highlight)
- Always dispatch UI updates to `@MainActor`
- Return `true` from the handler to accept the drop
- Use `.fileURL` as the UTType for general file drops

---

### Pattern 2: Typed Drop Handler (Reusable Utility)

**Source:** `QuickMotion/Utilities/VideoDropHandler.swift`
**Use case:** Centralized drop logic for a specific file type, reused across views.

```swift
enum VideoDropHandler {
    static let supportedTypes: [UTType] = [
        .movie, .video, .mpeg4Movie, .quickTimeMovie
    ]

    static func loadURL(from providers: [NSItemProvider]) async -> URL? {
        guard let provider = providers.first else { return nil }

        for type in supportedTypes {
            if provider.hasItemConformingToTypeIdentifier(type.identifier) {
                if let url = try? await loadURL(from: provider,
                                                 typeIdentifier: type.identifier) {
                    return url
                }
            }
        }
        return nil
    }

    private static func loadURL(
        from provider: NSItemProvider,
        typeIdentifier: String
    ) async throws -> URL? {
        try await withCheckedThrowingContinuation { continuation in
            provider.loadItem(forTypeIdentifier: typeIdentifier, options: nil) { item, error in
                if let error { continuation.resume(throwing: error); return }

                if let url = item as? URL {
                    continuation.resume(returning: url)
                } else if let data = item as? Data,
                          let url = URL(dataRepresentation: data, relativeTo: nil) {
                    continuation.resume(returning: url)
                } else {
                    continuation.resume(returning: nil)
                }
            }
        }
    }
}

// Usage:
.onDrop(of: VideoDropHandler.supportedTypes, isTargeted: $isTargeted) { providers in
    Task {
        if let url = await VideoDropHandler.loadURL(from: providers) {
            await MainActor.run { onDrop(url) }
        }
    }
    return true
}
```

**Best for:** When multiple views in your app accept the same file type. Extract once, reuse everywhere.

---

### Pattern 3: Concurrent Multi-File Drop (async TaskGroup)

**Source:** `Penumbra/Views/ContentView.swift`
**Use case:** User drops 20 video files at once — load them all in parallel.

```swift
.onDrop(of: [.movie], isTargeted: $isDropTargeted) { [library] providers in
    Task {
        let urls = await withTaskGroup(of: URL?.self, returning: [URL].self) { group in
            for provider in providers {
                group.addTask {
                    do {
                        let data = try await withCheckedThrowingContinuation {
                            (cont: CheckedContinuation<Data?, Error>) in
                            _ = provider.loadDataRepresentation(for: .fileURL) { data, error in
                                if let error { cont.resume(throwing: error) }
                                else { cont.resume(returning: data) }
                            }
                        }
                        guard let data,
                              let url = URL(dataRepresentation: data, relativeTo: nil)
                        else { return nil }
                        return url
                    } catch {
                        return nil
                    }
                }
            }

            var results: [URL] = []
            for await url in group {
                if let url { results.append(url) }
            }
            return results
        }

        if !urls.isEmpty {
            await library.addVideos(urls: urls)
        }
    }
    return true
}
```

**Best for:** Bulk import where each file resolution is independent. `TaskGroup` parallelizes the `NSItemProvider` loads.

---

### Pattern 4: Internal Reordering (`.draggable` + `.dropDestination`)

**Source:** `Phosphor/Views/TimelinePane.swift`, `CropBatch/Views/ThumbnailStripView.swift`
**Use case:** Drag thumbnails to reorder them in a timeline or strip.

```swift
@State private var draggedFrameID: UUID?
@State private var dropTargetIndex: Int?

var body: some View {
    ScrollView(.horizontal) {
        HStack(spacing: 8) {
            ForEach(Array(frames.enumerated()), id: \.element.id) { index, frame in
                thumbnailView(frame: frame, index: index)
            }
        }
    }
}

private func thumbnailView(frame: ImageItem, index: Int) -> some View {
    HStack(spacing: 0) {
        // Drop indicator bar
        Rectangle()
            .fill(Color.accentColor)
            .frame(width: 3, height: thumbnailHeight)
            .opacity(dropTargetIndex == index ? 1.0 : 0.0)

        FrameThumbnailView(frame: frame, isSelected: selectedIndex == index)
            .opacity(draggedFrameID == frame.id ? 0.5 : 1.0)
            .draggable(frame.id.uuidString) {
                // Drag preview
                FrameThumbnailView(frame: frame, isSelected: true)
                    .frame(width: 80, height: 60)
                    .onAppear { draggedFrameID = frame.id }
            }
            .dropDestination(for: String.self) { items, _ in
                handleReorder(destinationIndex: index)
            } isTargeted: { targeted in
                dropTargetIndex = targeted ? index : (dropTargetIndex == index ? nil : dropTargetIndex)
            }
    }
}

private func handleReorder(destinationIndex: Int) -> Bool {
    guard let draggedID = draggedFrameID,
          let sourceIndex = frames.firstIndex(where: { $0.id == draggedID }),
          sourceIndex != destinationIndex
    else {
        draggedFrameID = nil
        dropTargetIndex = nil
        return false
    }

    appState.reorderFrames(from: IndexSet(integer: sourceIndex), to: destinationIndex)
    draggedFrameID = nil
    dropTargetIndex = nil
    return true
}
```

**Visual feedback:**
- Dragged item: `opacity(0.5)` to ghost it
- Drop target: 3px accent-colored bar appears at insertion point
- Cleanup: always reset `draggedFrameID` and `dropTargetIndex` on drop or cancel

---

### Pattern 5: AppKit NSTableView Drop (NSViewRepresentable)

**Source:** `VCR/Views/AppKit/FileTableView.swift`
**Use case:** File drop onto an NSTableView wrapped in SwiftUI.

```swift
// In makeNSView:
tableView.registerForDraggedTypes([.fileURL])

// In Coordinator:
func tableView(
    _ tableView: NSTableView,
    validateDrop info: any NSDraggingInfo,
    proposedRow row: Int,
    proposedDropOperation: NSTableView.DropOperation
) -> NSDragOperation {
    guard info.draggingPasteboard.canReadObject(
        forClasses: [NSURL.self], options: nil
    ) else { return [] }

    // Drop onto table as a whole, not between rows
    tableView.setDropRow(-1, dropOperation: .on)
    return .copy
}

func tableView(
    _ tableView: NSTableView,
    acceptDrop info: any NSDraggingInfo,
    row: Int,
    dropOperation: NSTableView.DropOperation
) -> Bool {
    guard let urls = info.draggingPasteboard.readObjects(
        forClasses: [NSURL.self],
        options: [.urlReadingFileURLsOnly: true]
    ) as? [URL], !urls.isEmpty
    else { return false }

    onDropFiles(urls)
    return true
}
```

**Key rules:**
- `registerForDraggedTypes([.fileURL])` in `makeNSView` — without it, nothing happens
- `setDropRow(-1, dropOperation: .on)` retargets to "whole table" (not between rows)
- Use `.urlReadingFileURLsOnly: true` to filter out non-file URLs
- Call back to SwiftUI via closure (`onDropFiles`)

---

### Pattern 6: AppKit NSView Drop (Custom View Subclass)

**Source:** `TimeCodeEditor/Views/DropTargetView.swift`
**Use case:** Custom drop zone as an `NSView` subclass with file type validation.

```swift
class DropTargetView: NSView {
    weak var delegate: DropTargetViewDelegate?
    private let supportedExtensions = ["mov", "mp4", "m4v", "mxf", "mts"]

    override init(frame: NSRect) {
        super.init(frame: frame)
        registerForDraggedTypes([.fileURL])
    }

    override func draggingEntered(_ sender: NSDraggingInfo) -> NSDragOperation {
        hasValidFiles(in: sender) ? .copy : []
    }

    override func draggingUpdated(_ sender: NSDraggingInfo) -> NSDragOperation {
        hasValidFiles(in: sender) ? .copy : []
    }

    override func performDragOperation(_ sender: NSDraggingInfo) -> Bool {
        guard let urls = sender.draggingPasteboard.readObjects(
            forClasses: [NSURL.self]
        ) as? [URL] else { return false }

        let valid = urls.filter { supportedExtensions.contains($0.pathExtension.lowercased()) }
        guard !valid.isEmpty else { return false }

        delegate?.dropTargetView(self, didReceiveFiles: valid)
        return true
    }

    private func hasValidFiles(in info: NSDraggingInfo) -> Bool {
        guard let urls = info.draggingPasteboard.readObjects(
            forClasses: [NSURL.self]
        ) as? [URL] else { return false }
        return urls.contains { supportedExtensions.contains($0.pathExtension.lowercased()) }
    }
}
```

**Best for:** Pure AppKit apps or when you need full control over drag feedback (custom highlight drawing, per-extension validation).

---

### Choosing a Pattern

| Need | Pattern | Key Trait |
|---|---|---|
| Simple file drop zone | **1: Basic** | `.onDrop` + visual highlight |
| Same file type in many views | **2: Typed Handler** | Extracted utility enum |
| Bulk drop (10+ files) | **3: Concurrent** | `TaskGroup` parallel loading |
| Reorder items in a list/strip | **4: Internal** | `.draggable` + `.dropDestination` |
| NSTableView file drop | **5: AppKit Table** | `registerForDraggedTypes` + delegate |
| Custom AppKit drop view | **6: AppKit NSView** | `NSDraggingDestination` override |

**Anti-patterns:**
- Don't use `.onDrop` on an `NSViewRepresentable` — use `registerForDraggedTypes` on the underlying `NSView`
- Don't forget `@MainActor` when dispatching from `NSItemProvider` callbacks to UI
- Don't skip `isTargeted` visual feedback — without it the user can't tell where they're dropping
- Don't use `.onDrop(of: [.data])` as a catch-all — be specific about UTTypes you accept

---

