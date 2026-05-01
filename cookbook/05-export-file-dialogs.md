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

