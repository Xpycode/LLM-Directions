# Swift/SwiftUI Patterns Cookbook

**Extracted from working production code across 15+ projects.**
**Last updated: 2026-04-15**

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
> Reference implementation: `1-macOS/Penumbra/` (pre-Tahoe SDK toolbar)
> Titlebar injection reference: `1-macOS/VAM/` (macOS 26 SDK — no system chrome)

---

## Patterns Index

Each pattern lives in `docs/cookbook/`. Read the relevant file when a pattern is needed.

| # | File | What's Inside |
|---|------|---------------|
| 0 | [00-app-shell.md](docs/cookbook/00-app-shell.md) | **MANDATORY** — Entry point, Theme, FCPToolbarButtonStyle, HSplitView panes, migration checklist |
| 1 | [01-window-layouts.md](docs/cookbook/01-window-layouts.md) | NavigationSplitView, HSplitView variants, multi-window, autosave dividers, NSTableView |
| 2 | [02-layout-templates.md](docs/cookbook/02-layout-templates.md) | 5 archetypes: Browser, Editor, Organizer, Dual Viewer, Workspace |
| 3 | [03-appkit-controls.md](docs/cookbook/03-appkit-controls.md) | NSButton, NSCheckbox, NSPopUpButton, NSSegmentedControl, NSSlider, NSTextField wrappers |
| 4 | [04-swiftui-performance.md](docs/cookbook/04-swiftui-performance.md) | Diffing checkpoints, @ViewBuilder anti-pattern, .equatable(), image cache flash fix |
| 5 | [05-export-file-dialogs.md](docs/cookbook/05-export-file-dialogs.md) | NSSavePanel, NSOpenPanel, async panels, progress tracking, security-scoped bookmarks, .fileImporter |
| 6 | [06-app-lifecycle.md](docs/cookbook/06-app-lifecycle.md) | @main entry, .task init order, scenePhase, Manager.configure(), FolderManager |
| 7 | [07-timecode-typography.md](docs/cookbook/07-timecode-typography.md) | SF Pro .monospacedDigit() for timecode displays, weight hierarchy |
| 8 | [08-keyboard-shortcuts.md](docs/cookbook/08-keyboard-shortcuts.md) | 4 tiers: SwiftUI Commands → .onKeyPress → NSEvent monitor → custom manager |
| 9 | [09-context-menus.md](docs/cookbook/09-context-menus.md) | Basic, conditional, extracted @ViewBuilder, NSMenuDelegate for NSTableView |
| 10 | [10-selection-models.md](docs/cookbook/10-selection-models.md) | Single, multi Set\<ID\>, grid, NSTableView sync, cross-pane, two-level |
| 11 | [11-drag-drop.md](docs/cookbook/11-drag-drop.md) | .onDrop, typed handler, concurrent TaskGroup, internal reorder, NSTableView, NSView |
| 12 | [12-activity-progress.md](docs/cookbook/12-activity-progress.md) | Status bar, inline progress, determinate+cancel, multi-level, metrics panel, floating, phases |
| 13 | [13-workspace-switching.md](docs/cookbook/13-workspace-switching.md) | View mode toggle, tool picker, sidebar-driven, @AppStorage persist, nested sub-modes |
| 14 | [14-subprocess-url.md](docs/cookbook/14-subprocess-url.md) | URL.path() pitfall, security-scoped access across async pipelines |
| 15 | [15-native-video-analysis.md](docs/cookbook/15-native-video-analysis.md) | Shot/scene detection (Y-plane histogram), motion scoring (frame differencing) |
| 16 | [16-sparkle-auto-updates.md](docs/cookbook/16-sparkle-auto-updates.md) | Integration checklist, INFOPLIST_KEY_ gotcha, empty appcast fix, minimal updater |
| 17 | [17-thread-safe-rendering.md](docs/cookbook/17-thread-safe-rendering.md) | NSBitmapImageRep for TaskGroup offscreen rendering |
| 18 | [18-pipeline-extraction.md](docs/cookbook/18-pipeline-extraction.md) | Shared processing logic, caller-owned I/O |
| 19 | [19-swift6-concurrency.md](docs/cookbook/19-swift6-concurrency.md) | @MainActor + @Observable — enforce main-thread mutation at class level |
| 20 | [20-actor-reentrancy.md](docs/cookbook/20-actor-reentrancy.md) | When TOCTOU is NOT possible — synchronous sequences can't race |
| 21 | [21-anti-patterns.md](docs/cookbook/21-anti-patterns.md) | Common mistakes to avoid |
| 22 | [22-debounced-cifilter.md](docs/cookbook/22-debounced-cifilter.md) | Live filter preview with SwiftUI fallback cache |
| 23 | [23-z-order-overlay.md](docs/cookbook/23-z-order-overlay.md) | Out-of-bounds visual feedback without badges |
| 24 | [24-web-dev-patterns.md](docs/cookbook/24-web-dev-patterns.md) | Jinja2 data injection, ES module DI, shared state module |
| 25 | [25-extension-file-splitting.md](docs/cookbook/25-extension-file-splitting.md) | Split large files via extensions, access level fixes, strategy by file type |
| 26 | [26-launchd-node-service.md](docs/cookbook/26-launchd-node-service.md) | KeepAlive server, scheduled tasks, install/uninstall, Apple Silicon PATH gotcha |
| 27 | [27-timelineview-elapsed.md](docs/cookbook/27-timelineview-elapsed.md) | TimelineView(.periodic) for elapsed/remaining readouts, replaces Timer + objectWillChange |
| 28 | [28-commandgroup-observation.md](docs/cookbook/28-commandgroup-observation.md) | Commands struct with @ObservedObject — makes menu items update from @Published state |
| 29 | [29-disk-space-preflight.md](docs/cookbook/29-disk-space-preflight.md) | URLResourceKey volume APIs, preflight check, same-volume detection, named-volume errors |

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
| Selection: single `@Binding` | VideoScout | `List(selection:)` + `.tag()` |
| Selection: multi `Set<ID>` | Penumbra | `Table(selection:)`, batch ops |
| Selection: grid + keyboard nav | VideoScout | `LazyVGrid` + arrow keys |
| Selection: NSTableView sync | VCR | `isUpdatingSelection` loop guard |
| Selection: cross-pane observable | Penumbra | `@Observable` shared model |
| Selection: two-level | VAM | Sidebar category + item binding |
| Drop: basic `.onDrop` | CropBatch | File drop zone + highlight |
| Drop: typed handler utility | QuickMotion | Reusable `VideoDropHandler` |
| Drop: concurrent TaskGroup | Penumbra | Bulk multi-file import |
| Drop: internal reordering | Phosphor | `.draggable` + `.dropDestination` |
| Drop: NSTableView | VCR | `registerForDraggedTypes` + delegate |
| Drop: AppKit NSView subclass | TimeCodeEditor | `NSDraggingDestination` override |
| Progress: status bar | VCR | `.safeAreaInset` bottom bar |
| Progress: inline in bar | Penumbra, VAM | Spinner + text when busy |
| Progress: determinate + cancel | Phosphor, CutSnaps | Export bar + % + cancel |
| Progress: multi-level | VideoScout | Overall + per-item bars |
| Progress: metrics panel | P2toMXF | Elapsed / ETA / speed chips |
| Progress: floating overlay | VideoScout | Slide-up `.bottomTrailing` |
| Progress: phase indicator | VOLTLAS, VCR | Color-coded stage icons |
| Progress: footer swap | P2toMXF | Normal actions → progress+stop |
| Workspace: view mode toggle | Penumbra | Grid/list/single via toolbar |
| Workspace: tool mode picker | CropBatch | `.segmented` picker, controls swap |
| Workspace: sidebar-driven | VOLTLAS | `@ViewBuilder switch` on enum |
| Workspace: @AppStorage persist | VideoScout | Mode survives relaunch |
| Workspace: nested sub-modes | VOLTLAS | Outer phase + inner variant |
| TC font: SF Pro .monospacedDigit() | Penumbra | Timecode without slashed zeros (FCP-style) |
| Jinja2 data injection | PDF2Calendar | Server→client data passing |
| ES Module DI | PDF2Calendar | Avoid circular imports in JS modules |
| Shared State Module | PDF2Calendar | Centralized state for vanilla JS apps |
| launchd KeepAlive server | X-STATUS | Node.js server auto-start + auto-restart |
| launchd scheduled task | X-STATUS | Daily data collection (cron replacement) |
| Install/uninstall scripts | X-STATUS | Idempotent launchd agent management |
