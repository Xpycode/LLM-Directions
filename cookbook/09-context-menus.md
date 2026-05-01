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

