# Swift/SwiftUI Patterns Cookbook

**Extracted from working production code across 15+ projects.**
**Last updated: 2026-04-29 (added #59 decodable-only-codingkeys; #60 closure-bridged-appkit; #61 probe-classify-not-catch-all)**

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

Each pattern lives in `cookbook/`. Read the relevant file when a pattern is needed.

| # | File | What's Inside |
|---|------|---------------|
| 0 | [00-app-shell.md](cookbook/00-app-shell.md) | **MANDATORY** — Entry point, Theme, FCPToolbarButtonStyle, HSplitView panes, migration checklist |
| 1 | [01-window-layouts.md](cookbook/01-window-layouts.md) | NavigationSplitView, HSplitView variants, multi-window, autosave dividers, NSTableView |
| 2 | [02-layout-templates.md](cookbook/02-layout-templates.md) | 5 archetypes: Browser, Editor, Organizer, Dual Viewer, Workspace |
| 3 | [03-appkit-controls.md](cookbook/03-appkit-controls.md) | NSButton, NSCheckbox, NSPopUpButton, NSSegmentedControl, NSSlider, NSTextField wrappers |
| 4 | [04-swiftui-performance.md](cookbook/04-swiftui-performance.md) | Diffing checkpoints, @ViewBuilder anti-pattern, .equatable(), image cache flash fix |
| 5 | [05-export-file-dialogs.md](cookbook/05-export-file-dialogs.md) | NSSavePanel, NSOpenPanel, async panels, progress tracking, security-scoped bookmarks, .fileImporter |
| 6 | [06-app-lifecycle.md](cookbook/06-app-lifecycle.md) | @main entry, .task init order, scenePhase, Manager.configure(), FolderManager |
| 7 | [07-timecode-typography.md](cookbook/07-timecode-typography.md) | SF Pro .monospacedDigit() for timecode displays, weight hierarchy |
| 8 | [08-keyboard-shortcuts.md](cookbook/08-keyboard-shortcuts.md) | 4 tiers: SwiftUI Commands → .onKeyPress → NSEvent monitor → custom manager |
| 9 | [09-context-menus.md](cookbook/09-context-menus.md) | Basic, conditional, extracted @ViewBuilder, NSMenuDelegate for NSTableView |
| 10 | [10-selection-models.md](cookbook/10-selection-models.md) | Single, multi Set\<ID\>, grid, NSTableView sync, cross-pane, two-level |
| 11 | [11-drag-drop.md](cookbook/11-drag-drop.md) | .onDrop, typed handler, concurrent TaskGroup, internal reorder, NSTableView, NSView |
| 12 | [12-activity-progress.md](cookbook/12-activity-progress.md) | Status bar, inline progress, determinate+cancel, multi-level, metrics panel, floating, phases |
| 13 | [13-workspace-switching.md](cookbook/13-workspace-switching.md) | View mode toggle, tool picker, sidebar-driven, @AppStorage persist, nested sub-modes |
| 14 | [14-subprocess-url.md](cookbook/14-subprocess-url.md) | URL.path() pitfall, security-scoped access across async pipelines |
| 15 | [15-native-video-analysis.md](cookbook/15-native-video-analysis.md) | Shot/scene detection (Y-plane histogram), motion scoring (frame differencing) |
| 16 | [16-sparkle-auto-updates.md](cookbook/16-sparkle-auto-updates.md) | Integration checklist, INFOPLIST_KEY_ gotcha, empty appcast fix, minimal updater |
| 17 | [17-thread-safe-rendering.md](cookbook/17-thread-safe-rendering.md) | NSBitmapImageRep for TaskGroup offscreen rendering |
| 18 | [18-pipeline-extraction.md](cookbook/18-pipeline-extraction.md) | Shared processing logic, caller-owned I/O |
| 19 | [19-swift6-concurrency.md](cookbook/19-swift6-concurrency.md) | @MainActor + @Observable — enforce main-thread mutation at class level |
| 20 | [20-actor-reentrancy.md](cookbook/20-actor-reentrancy.md) | When TOCTOU is NOT possible — synchronous sequences can't race |
| 21 | [21-anti-patterns.md](cookbook/21-anti-patterns.md) | Common mistakes to avoid |
| 22 | [22-debounced-cifilter.md](cookbook/22-debounced-cifilter.md) | Live filter preview with SwiftUI fallback cache |
| 23 | [23-z-order-overlay.md](cookbook/23-z-order-overlay.md) | Out-of-bounds visual feedback without badges |
| 24 | [24-web-dev-patterns.md](cookbook/24-web-dev-patterns.md) | Jinja2 data injection, ES module DI, shared state module |
| 25 | [25-extension-file-splitting.md](cookbook/25-extension-file-splitting.md) | Split large files via extensions, access level fixes, strategy by file type |
| 26 | [26-launchd-node-service.md](cookbook/26-launchd-node-service.md) | KeepAlive server, scheduled tasks, install/uninstall, Apple Silicon PATH gotcha |
| 27 | [27-timelineview-elapsed.md](cookbook/27-timelineview-elapsed.md) | TimelineView(.periodic) for elapsed/remaining readouts, replaces Timer + objectWillChange |
| 28 | [28-commandgroup-observation.md](cookbook/28-commandgroup-observation.md) | Commands struct with @ObservedObject — makes menu items update from @Published state |
| 29 | [29-disk-space-preflight.md](cookbook/29-disk-space-preflight.md) | URLResourceKey volume APIs, preflight check, same-volume detection, named-volume errors |
| 30 | [30-volume-custom-icons.md](cookbook/30-volume-custom-icons.md) | **Two-step write** (`.VolumeIcon.icns` + `com.apple.FinderInfo` xattr + `utimes`) because `NSWorkspace.setIcon` is broken on volume roots since macOS 13.1 |
| 31 | [31-volume-enumeration.md](cookbook/31-volume-enumeration.md) | "External drive" heuristic — why `volumeIsRemovableKey` is misleading; correct filter is `!isInternal && !isRootFileSystem && !isLikelyDiskImage` |
| 32 | [32-nsworkspace-asyncstream.md](cookbook/32-nsworkspace-asyncstream.md) | Bridge `NSWorkspace` mount/unmount notifications to `AsyncStream<MountEvent>` inside an actor; observer ownership + termination cleanup |
| 33 | [33-managed-developer-id.md](cookbook/33-managed-developer-id.md) | Xcode Archive → Direct Distribution with a server-side managed Developer ID cert; CLI `notarytool` pipeline as an appendix |
| 34 | [34-xcodeproj-clone-rename.md](cookbook/34-xcodeproj-clone-rename.md) | Clone an existing `.xcodeproj` when a new app needs the same toolchain bundling / entitlements / build phases — `cp -R` + sed recipe with macOS sed, display-name-with-spaces, and xcuserdata gotchas |
| 35 | [35-asyncstream-bounded-fanout.md](cookbook/35-asyncstream-bounded-fanout.md) | `withTaskGroup` drain-and-refill pattern for streaming results from thousands of async operations with a bounded concurrency cap; why the naive `for url in files { group.addTask }` version is wrong |
| 36 | [36-fast-preview-heavy-commit.md](cookbook/36-fast-preview-heavy-commit.md) | Split render API into `preview(…) throws -> NSImage` (in-memory, sync, ~15 ms) vs `render(…) async throws -> Data` (full pipeline with subprocess, ~300 ms). Synchronous `.onChange` wiring for live slider feedback; no Task/cancel gymnastics. |
| 37 | [37-effective-source-fallback.md](cookbook/37-effective-source-fallback.md) | `pending ?? cached` editor binding so settings can be tweaked on a previously-saved asset without re-importing. Includes dirty-detection for the commit gate and self-healing for disappeared cache files. |
| 38 | [38-destructive-copy-guard.md](cookbook/38-destructive-copy-guard.md) | `sourceURL.standardizedFileURL == destURL.standardizedFileURL` early-return before `removeItem → copyItem` — avoids deleting the file you're about to read when `src == dest`. |
| 39 | [39-design-tokens.md](cookbook/39-design-tokens.md) | **App-wide visual tokens** — typography scale (semantic, modular ratio), 8pt spacing grid with internal≤external rule, SF Symbol weight/scale conventions, corner radii, CSS `clamp()` fluid translation for web projects |
| 40 | [40-spaces-plist-backend.md](cookbook/40-spaces-plist-backend.md) | **Public Spaces backend via `com.apple.spaces`** — parse the documented-format-undocumented-semantics plist to get real Space UUIDs + current-Space per monitor without private CGS SPI. Handles `spans-displays=0`/`1` modes correctly. Includes Swift 6 reader, AsyncStream wiring with 120ms settle delay, v1→v2 migration strategy, and known limits |
| 41 | [41-web-hero-floating-icons.md](cookbook/41-web-hero-floating-icons.md) | **Web landing-hero composition** — fill empty hero space with the product's own app icons scattered at gentle angles around the centered headline. `.hero-stage` wrapper + 3× `.float-icon` (absolute, rotated, drop-shadow stacks, staggered drift animations 7s/8s/9s, hidden under 820px). Why `filter: drop-shadow` not `box-shadow`; why coprime animation periods; accessibility (`alt=""` + `aria-hidden`). |
| 42 | [42-web-native-dialog-lightbox.md](cookbook/42-web-native-dialog-lightbox.md) | **Web image lightbox via native `<dialog>`** — click any thumbnail to enlarge it in a fullscreen overlay (GitHub-style). Single shared `<dialog>` per page, JS swaps `img.src`. Free focus trap + ESC-close + `::backdrop` pseudo-element; backdrop-filter blur; click-anywhere-to-close. `.shot` a11y attrs (`tabindex`/`role`/`aria-label`/keydown) added at runtime, not in HTML. Variations for next/prev nav, captions inside dialog, pinch-zoom alternatives. |
| 43 | [43-subprocess-fire-and-collect.md](cookbook/43-subprocess-fire-and-collect.md) | **Short-lived subprocess → single stdout blob** — `waitUntilExit() + readDataToEndOfFile()` inside `Task.detached` instead of `readabilityHandler`. Avoids the tail-byte race at child-termination, kills 30 lines of handler-cleanup boilerplate, same performance for bounded outputs. Right for `ffprobe`/`exiftool`/`shasum`/`git rev-parse`; wrong for long-running processes with streamed progress (use `readabilityHandler` there). Covers stderr always-drain rule, `Task.detached` rationale, per-call cancellation trade-off. |
| 44 | [44-inherited-project-dead-code-sweep.md](cookbook/44-inherited-project-dead-code-sweep.md) | **Bulk-remove dead Swift code from forked Xcode project** — `sed -i '' "/filename.swift/d" project.pbxproj` per dead file removes all 4 pbxproj references at once (works because Xcode-generated pbxproj puts filename in every `/* comment */`). Combine with disk `rm`, in-place trim for partially-dead files via `sed -n "${N},\$p"`, safety-net unit tests. AvidMXFPeek sweep: 30 files deleted, 5 files trimmed, ~4500 → 1507 LOC in ~20 min. Gotchas: escape regex metachars in filenames, close Xcode first, watch for prefix-name collisions, PBXFileSystemSynchronizedRootGroup exempts contents from pbxproj file refs. |
| 45 | [45-macos-firmlink-canonical-path.md](cookbook/45-macos-firmlink-canonical-path.md) | **macOS firmlink / `/var` vs `/private/var` URL-equality gotcha** — `URL.resolvingSymlinksInPath()` is a **no-op on APFS firmlinks** (Catalina+), but `FileManager`'s enumerator returns firmlink-resolved URLs. Result: hand-built `/var/folders/...` URLs fail `==` against enumerator-returned `/private/var/folders/...` URLs. Fix: `URLResourceValues.canonicalPath` (requires path to exist — canonicalize the parent, then `appendingPathComponent` the leaf). Covers when this bites (test fixtures, Sets of URLs, path-based dedup), what doesn't work (resolvingSymlinksInPath/standardized/NSString variants), diagnostic approach via xcresult assertion diffs. |
| 47 | [47-xcodegen-swiftterm-setup.md](cookbook/47-xcodegen-swiftterm-setup.md) | **xcodegen + SwiftTerm setup gotchas** — binary resources (TTF fonts) not auto-included → postBuildScripts + ATSApplicationFontsPath; UIDesignRequiresCompatibility must be in info.properties not real plist; SwiftUI.Color vs SwiftTerm.Color ambiguity → extension SwiftUI.Color; re-run xcodegen after adding files; SourceKit false positives before first Xcode open |
| 48 | [48-swiftterm-output-monitor.md](cookbook/48-swiftterm-output-monitor.md) | **SwiftTerm output monitoring + PTY input bridge** — override `dataReceived(slice:)` in a `LocalProcessTerminalView` subclass (safe intercept point; delegate interception breaks internals); closure bridge pattern for PTY writes from model layer (`session.sendInput?("y\n")`); rolling 512-char buffer for split-pattern matching across chunks; threading gotchas (dispatch to main before @Observable mutation) |
| 46 | [46-web-php-download-counter.md](cookbook/46-web-php-download-counter.md) | **Web download counter — PHP + flat-file JSON, no backend** — `/dl.php?app=<name>` validates against a regex (path traversal blocked), finds first matching `{dmg,zip,saver,pkg}`, increments `counts.json` under `flock(LOCK_EX)`, then 302s to the real file (Apache serves bytes — Range requests work natively). GET-only counting (HEAD doesn't increment, defeats browser speculative-prefetch and `curl -I`), bot UA filter, counter failure non-fatal. Companion `download-stats.js` reads `counts.json` and prepends "N downloads · " to a static "latest vX.Y · NN MB" line baked into HTML — graceful degradation if JS fails. ~50 lines PHP + 20 lines JS, no DB, no third-party analytics. |
| 49 | [49-web-php-feedback-form-with-admin.md](cookbook/49-web-php-feedback-form-with-admin.md) | **Web feedback form with admin — PHP + flat-file JSON, public/private split, Basic-Auth admin** — in-app "Report a bug / Feature request" form that persists to `feedback/public.json` (web-readable, no PII) + `feedback/private/submissions.log` (`.htaccess` denied, append-only, with email + salted-IP-hash + UA). Join-at-read rather than at-write so operator cat of public.json still shows no email. XSS-safe via `textContent` / `createElement` discipline (no `innerHTML`, no escape function needed). Honeypot + `sha256($ip.$salt)` rate limit (3/h, 10/d). Admin UI at `/admin/` gated by `.htaccess` Basic-Auth + `.htpasswd` — **critical pairing**: Basic-Auth's auto-attached credentials mean CSRF is a real threat, so admin `update.php` enforces same-origin via Origin/Referer check. One-time `_whereami.php` helper discovers the server's absolute path for `AuthUserFile` (delete after use). `deploy.sh` must `--exclude` server-managed files or mirror becomes destructive on second deploy. Composes with #46. |
| 50 | [50-detachable-windows.md](cookbook/50-detachable-windows.md) | **Detachable windows — `WindowGroup(for: UUID.self)` + `WindowManager`** — each detached window gets its own manager looked up by UUID. `WindowManager` maps `[UUID: YourManager]`; `detachSession` moves item out of source manager, creates new manager, stores it, returns the UUID; `openWindow(value: uuid)` opens the typed scene. Includes cross-window drag via `Transferable` + custom UTType + `.dropDestination`. Gotchas: `import CoreTransferable` in non-SwiftUI files; use `removeSession` (not `closeSession`) for moves; typed scene body receives `Binding<UUID?>` — nil-check before lookup. |
| 51 | [51-swiftui-recursive-split-pane.md](cookbook/51-swiftui-recursive-split-pane.md) | **SwiftUI recursive split pane — `indirect enum` tree + recursive View** — `SplitNode` with `leaf` and `split(direction:ratio:)` cases; `inserting/removing` operations return new trees (value semantics). `SplitPaneView` recurses via `HSplitView`/`VSplitView` (AppKit-backed drag-to-resize, free). Critical: `switch` in SwiftUI `body` breaks the result builder — delegate to `@ViewBuilder private func content()`. Active pane gets 1px accent border via `ZStack` overlay with `allowsHitTesting(false)`. Keyboard shortcuts via `Commands` struct + `.commands{}` on `WindowGroup`. |
| 52 | [52-appendingpathcomponent-fs-probe.md](cookbook/52-appendingpathcomponent-fs-probe.md) | **`URL.appendingPathComponent(_:)` fs-probe URL-equality gotcha** — the single-argument overload performs a filesystem probe to set `hasDirectoryPath`. If the same path is resolved twice (once before the directory exists, once after) the two URLs compare **unequal** because `URL ==` walks `hasDirectoryPath`. Bites caches, `prepareOutputDir`-style APIs, `Set<URL>`/`[URL:T]` keyed by computed paths, and diff algorithms. Fix: always pass `isDirectory: true` when appending a directory component (or `.appending(path:, directoryHint: .isDirectory)` on macOS 13+). Standardizing, string-comparing, and firmlink-normalization don't help — only the explicit `isDirectory:` parameter stabilises it. Composes with #45 (firmlink canonical-path); apply both when mixing `FileManager` output with hand-built URLs. |
| 53 | [53-web-grid-masonry-jsspan.md](cookbook/53-web-grid-masonry-jsspan.md) | **Web masonry — CSS Grid + JS-computed `grid-row-end: span N`** — row-first reading order preserved (photos 1→3 along row 1, 4→6 along row 2), unlike CSS `column-count` which fills column 1 entirely before column 2. Technique: `grid-auto-rows: 8px` small unit + per-item JS sets `grid-row-end: span ceil((natH/natW * clientWidth + gap) / (8 + gap))` on img `load`. Resize debounced at 150ms. ~15 lines JS. Pairs with `<dialog>` lightbox (#42). Non-Firefox-gated (native `grid-template-rows: masonry` is still Firefox-only). |
| 54 | [54-web-portrait-aware-uniform-grid.md](cookbook/54-web-portrait-aware-uniform-grid.md) | **Web portrait-aware uniform grid** — mostly-landscape gallery with occasional portraits that shouldn't get cropped or break row flow. `.gallery-link` has `aspect-ratio: 3/2`; JS adds `.portrait` class when `img.naturalHeight > naturalWidth`; `.portrait` gets `grid-row: span 2` + `aspect-ratio: 2/3`; `grid-auto-flow: dense` auto-fills gaps with landscapes stacking beside. Aspect-ratio MUST live on the link (not on `<picture>` — transparent element ignores CSS). Visual outcome: portrait in col 2 spanning rows 2+3, landscapes in cols 1+3 stack above/below. Extensible to panoramics via `.panoramic { grid-column: span 2 }`. |
| 55 | [55-web-preview-suffix-deploy.md](cookbook/55-web-preview-suffix-deploy.md) | **Web preview-via-suffix deploy — staging without staging** — for multi-day rewrites of static sites on shared hosting (Strato, Dreamhost, etc.). Every new page deploys as `*-new.html` alongside the live original; internal hrefs on preview pages use `-new.html` so reviewers stay in preview. Same origin = shared images/fonts/CSS, no duplication. Ship = rename `*-new.html` → `*.html` + sitewide sed to strip `-new` from hrefs. SFTP `put <local> <remote-with-suffix>` keeps local filenames clean. Alternative: `/preview/` subfolder for longer migrations. Pre-deploy grep to catch preview pages accidentally linking to production. |
| 57 | [57-commandgroup-saveitem-cmdw-override.md](cookbook/57-commandgroup-saveitem-cmdw-override.md) | **`⌘W` override in SwiftUI macOS — `CommandGroup(replacing: .saveItem)`** — multi-tab/multi-pane apps need ⌘W to close active pane→tab→spawn-fresh, not the system default close-window. The trap: `CommandMenu` with `.disabled(panes <= 1)` falls through to the system close-window when greyed-out, so ⌘W behaves differently with one vs many panes. Fix: use `CommandGroup(replacing: .saveItem)` (the only placement that wins over `File > Close Window`) with a button that's **never** `.disabled`, and a `closeActive()` that handles every state (close pane → close tab → auto-spawn fresh tab to keep window non-empty). Confirmation via `@Binding<Bool>` + `.confirmationDialog` (not `NSAlert.runModal` — transaction-unsafe). Not for `DocumentGroup` apps (system handling is correct there). Composes with #28, #50. |
| 58 | [58-xcodegen-postbuildscripts-sandbox.md](cookbook/58-xcodegen-postbuildscripts-sandbox.md) | **`xcodegen` postBuildScripts: sandbox-safe + dep-analysis-friendly** — copying resources via a script phase fails two ways out of the box: (1) Xcode warns "will be run during every build because it does not specify any outputs"; (2) sandbox denies `file-read-data` against source paths outside `$TARGET_BUILD_DIR`. Both fixed by **both** `inputFiles:` (sandbox grant) AND `outputFiles:` (mtime-based skip on incremental builds) — one alone is insufficient. Use `$(VAR)` not `${VAR}` in xcodegen path entries (pbxproj syntax, not shell). Globs don't work for sandbox grants — list concrete paths. For >10 files, switch to `inputFileLists` / `outputFileLists` referencing `.xcfilelist` text files. Always `xcodegen generate` after editing `project.yml`. Extends #47. |
| 56 | [56-web-static-admin-template-roundtrip.md](cookbook/56-web-static-admin-template-roundtrip.md) | **Template round-trip invariant as admin-write safety net** — when a static site grows an admin that regenerates public HTML on every mutation, prove `parse(committed_leaf) → render(manifest) == committed_leaf` byte-for-byte *before* writing any mutation endpoint. Anatomy: parametrise one representative page into `{{PLACEHOLDER}}` template; pure-function renderer with `strtr` (one-pass, no recursion footgun) + literal-string concatenation for repeating blocks (heredocs are a whitespace trap); regex parser for reverse direction (brittleness to shape is a feature); CLI-only (`PHP_SAPI !== 'cli'`) harness that parses committed HTML and diffs against render output. Widen coverage across every structural variant you have (masonry+uniform, each parent section, 1-photo and 500-photo galleries). Test becomes permanent regression guard for all future template edits. Validated across 4 leaves × 436 figures zero-diff. Composes with #49 (Basic-Auth scaffold) and #55 (preview-suffix deploy for rolling out admin mutations shadow-first). |
| 59 | [59-decodable-only-codingkeys.md](cookbook/59-decodable-only-codingkeys.md) | **`Decodable`-only types with custom `init(from:)` need explicit `CodingKeys`** — Swift's Codable synthesis (SE-0166) only generates `CodingKeys` when it's also synthesizing one of `init(from:)` / `encode(to:)`. A type that's *only* `Decodable` *and* has a hand-rolled `init(from:)` has nothing left to synthesize, so `decoder.container(keyedBy: CodingKeys.self)` fails with "cannot find 'CodingKeys' in scope". The same shape compiles fine on full `Codable` because the still-synthesized `encode(to:)` carries the keys. Fix: declare `private enum CodingKeys: String, CodingKey { case … }` explicitly. Don't reach for fake `Encodable` — the synthesized `encode(to:)` may bypass your decode-time normalisation. |
| 60 | [60-closure-bridged-appkit.md](cookbook/60-closure-bridged-appkit.md) | **Closure-bridged AppKit from a model-layer `@MainActor` ObservableObject** — when a SwiftUI controller in a non-UI file (`Client.swift`, networking layer) needs to trigger AppKit behaviour (window close, NSWorkspace deep-link, NSAlert), don't hold `weak var window: NSWindow?` — that forces `import AppKit` into your model file and makes every consumer transitively AppKit-dependent. Inject closures (`var dismissAction: (() -> Void)?`, `var openSettingsAction: (() -> Void)?`) from the window controller after `super.init` (weak-capture the window inside to avoid retain cycles). Compile-time enforcement of layer boundaries; trivially stubbable in tests; cross-platform-friendly. Composes with #19, #28. |
| 61 | [61-probe-classify-not-catch-all.md](cookbook/61-probe-classify-not-catch-all.md) | **TCC / FDA pre-flight without false positives — probe-and-classify, not catch-all** — `catch { return false } → fdaBlocked = true` is a false-positive generator: any error (file-not-found, ENOTDIR, ENOENT, transient I/O) gets misread as a permission denial. Real fix: `enum AccessProbeResult { case granted / notFound / notADirectory / permissionDenied / other }` driven by `fileExists(atPath:isDirectory:)` first, then typed `CocoaError where .code == .fileReadNoPermission`, then a catch-all that **logs** the actual NSError domain+code+desc to OSLog. Only `.permissionDenied` triggers the destructive FDA gate; other failures populate `lastError` with a contextual message. Note that arbitrary `~/...` paths are NOT TCC-protected — apps that don't access `~/Documents`/`~/Desktop`/iCloud/etc. **never appear in the FDA list automatically** (gate copy must explain the "+ button" workflow). Companion: #29, #52. |

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
| **Volume custom icons (two-step write)** | **Sigil** | **`.VolumeIcon.icns` + FinderInfo xattr** |
| **VolumeEnumerator + external heuristic** | **Sigil** | **`!isInternal && !DMG` filter** |
| **NSWorkspace → AsyncStream bridge** | **Sigil** | **Mount/unmount events via structured concurrency** |
| **Managed Developer ID GUI workflow** | **Sigil** | **Archive → Direct Distribution, no local cert** |
