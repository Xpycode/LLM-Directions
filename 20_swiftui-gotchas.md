<!--
TRIGGERS: UI not updating, @Observable, @State, SwiftUI bug, layout broken, view not refreshing, layout shift, conditional view, show hide
PHASE: implementation
LOAD: full
-->

# SwiftUI Gotchas Reference

*Common pitfalls that cause bugs in macOS/iOS development.*

---

## The Big Five (Most Common Issues)

### 1. @Observable Doesn't Detect Nested Mutations

**Problem:** UI doesn't update when you change a nested property.

```swift
// BROKEN: @Observable doesn't see this
video.activeSelection?.inPoint = newValue

// WORKS: Reassign the entire struct
var selection = video.activeSelection
selection?.inPoint = newValue
video.activeSelection = selection
```

**Why:** Swift's `@Observable` macro only detects when properties are *assigned*, not when nested values inside them mutate.

**Detection:** UI doesn't update. Add logging: `print("hasSelection: \(hasSelection), value: \(value)")` — if values are correct but UI is stale, this is likely the cause.

**Rule:** When modifying nested properties in `@Observable` objects, always reassign the parent property.

---

### 2. @State with Class References

**Problem:** Toggle buttons stuck, UI doesn't respond to state changes.

```swift
// BROKEN: @State doesn't observe a plain class's property changes
@State private var manager = SomeManager.shared

Button("Toggle") {
    manager.toggle()  // View never re-renders — SwiftUI can't see into an unobserved class
}
```

**Why:** `@State` is designed for value types (structs) or `@Observable` reference types. A plain
class's property mutations are invisible to SwiftUI's dependency tracking.

**Modern fix — mark the class `@Observable`:**
```swift
@Observable
final class SomeManager {
    var isEnabled = false

    func toggle() {
        isEnabled.toggle()
    }
}

// View
let manager = SomeManager.shared

Button("Toggle") {
    manager.toggle()  // @Observable tracks the read in body; view updates automatically
}
```

**Old workaround (pre-`@Observable`, avoid in new code):** force a refresh by bumping an unrelated
`@State` value whenever the class mutates:
```swift
@State private var isEnabled = false
@State private var refreshTrigger = UUID()

Button("Toggle") {
    manager.toggle()
    isEnabled = manager.isEnabled
    refreshTrigger = UUID()  // Force view refresh — unnecessary once manager is @Observable
}
```

**Rule:** For class-backed state, mark the class `@Observable` rather than working around observation with manual refresh triggers.

---

### 3. Split-Pane Choice: HSplitView vs. HStack + Divider

**Problem:** Picking the wrong split-pane primitive for the job — `HStack(spacing: 0)` with a
fixed `.frame(width:)` doesn't give the user a draggable divider; `HSplitView`/`VSplitView`
used for a genuinely fixed-width sidebar adds resize behavior nobody asked for.

**Rule — this is a decision tree, not a default:**
- **User-resizable panes** (draggable divider) → `HSplitView` (horizontal) or `VSplitView`
  (vertical). Reference: Penumbra (`HSplitView`), Conjoyn (`VSplitView`).
- **Fixed-width sidebar / non-resizable layout** → `HStack(spacing: 0)` with an explicit
  sidebar width and an optional `Divider()`. Reference: CropBatch.

```swift
// User-resizable: draggable divider
HSplitView {
    SidebarView()
    ContentView()
}

// Fixed-width: no draggable divider
HStack(spacing: 0) {
    SidebarView()
        .frame(width: sidebarWidth)   // fixed, not minWidth

    Divider()

    ContentView()
}
```

**Why it matters:** using `HStack` for a pane that should resize removes the drag handle users
expect; using `HSplitView` for a pane that should stay fixed adds unwanted resize affordance.
Pick the branch that matches the actual interaction, not habit. See `cookbook/00-app-shell.md`
§5 and `cookbook/01-window-layouts.md` for the full decision tree and code patterns.

---

### 4. PreferenceKey.reduce() Conditionals

**Problem:** Popover sizing breaks, initial layout wrong.

```swift
// BROKEN: Conditional blocks updates
struct ContentHeightKey: PreferenceKey {
    static func reduce(value: inout CGFloat, nextValue: () -> CGFloat) {
        let next = nextValue()
        if abs(next - value) > threshold {  // DON'T DO THIS
            value = next
        }
    }
}

// WORKS: Always take the value
struct ContentHeightKey: PreferenceKey {
    static func reduce(value: inout CGFloat, nextValue: () -> CGFloat) {
        value = max(value, nextValue())  // Always update
    }
}
```

**Why:** Adding thresholds or conditional updates breaks initial popover sizing. SwiftUI depends on consistent reduce behavior.

**Rule:** In `PreferenceKey.reduce()`, always use `value = max(value, nextValue())` or similar unconditional logic.

---

### 5. .clipped() vs .clipShape()

**Problem:** Overlays extend outside intended bounds.

```swift
// BROKEN: .clipped() only clips the view, not overlays
Rectangle()
    .frame(width: 100, height: 100)
    .clipped()
    .overlay {
        Text("Hello")  // NOT clipped!
    }

// WORKS: .clipShape() clips the entire composite
Color.clear
    .frame(width: 100, height: 100)
    .overlay {
        Text("Hello")  // IS clipped
    }
    .clipShape(Rectangle())
```

**Why:** `.clipped()` applies before overlays are added. `.clipShape()` applies to the final composite.

**Rule:** Use `.clipShape(Rectangle())` when you need to constrain overlays within bounds.

---

## Layout Issues

### Text Wrapping at Narrow Widths

**Problem:** Labels break into stacked individual characters.

```swift
// BROKEN: Multiple Labels wrap character-by-character
HStack {
    Label("Duration", systemImage: "clock")
    Label("Size", systemImage: "doc")
    Label("Format", systemImage: "film")
}

// WORKS: Single Text with inline separators
Text("Duration • Size • Format")
```

**Rule:** For narrow layouts, use single `Text` with separators instead of multiple `Label` views.

---

### State Mutation During View Updates

**Problem:** Infinite update loops, "Publishing changes from within view updates" warning.

```swift
// BROKEN: Modifying state in body computation
var body: some View {
    if condition {
        viewModel.updateSomething()  // NEVER do this
    }
    return SomeView()
}

// WORKS: Use onChange or task
var body: some View {
    SomeView()
        .onChange(of: condition) { _, newValue in
            if newValue {
                viewModel.updateSomething()
            }
        }
}
```

**Rule:** Never modify `@Published` properties during view body computation. Use `.onChange`, `.task`, or `.onAppear`.

---

### ForEach + ObservedObject Rebuilds

**Problem:** O(n) view rebuilds when any item changes.

```swift
// SLOW: Every item rebuilds when collection changes
ForEach(viewModel.items) { item in
    ItemRow(item: item)
}

// BETTER: Use identifiable items with stable IDs
ForEach(viewModel.items, id: \.stableId) { item in
    ItemRow(item: item)
}
```

**Why:** If IDs change, SwiftUI treats them as new items and rebuilds everything.

**Rule:** Use stable IDs that don't change when content changes (UUID assigned at creation, not content hash).

---

### Conditional Views Causing Layout Shifts

**Problem:** UI jumps/shifts when showing or hiding elements based on state.

```swift
// BROKEN: ZStack includes hidden view in size calculation
ZStack {
    MainContent()
        .padding(.bottom, 30)  // Reserve space

    if showIndicator {  // Structural change!
        IndicatorBar()
    }
}

// ALSO BROKEN: opacity still triggers layout recalc
ZStack {
    MainContent()
    IndicatorBar()
        .opacity(showIndicator ? 1 : 0)  // May still animate/recalc
}

// WORKS: Use .overlay - excluded from parent size calculation
MainContent()
    .padding(.bottom, 30)  // Reserve space
    .overlay(alignment: .bottom) {
        IndicatorBar()
            .opacity(showIndicator ? 1 : 0)
    }
```

**Why:** Two issues combine:
1. `if condition { View }` changes view structure, forcing SwiftUI to rebuild the hierarchy
2. `ZStack` calculates size from the union of all children's frames—even invisible ones can affect layout
3. `.overlay()` is explicitly excluded from parent size calculation

**Detection:** Layout shifts when toggling visibility. Add border to parent: `.border(.red)` — if size changes when child shows/hides, this is the cause.

**Fix Pattern:**

**Fix 1: `.overlay()` instead of `ZStack`**
- Move the toggled element into an `.overlay()` modifier
- Overlays are completely excluded from parent layout sizing
- The main content determines its own size; the overlay floats on top

**Fix 2: Always render, control with `opacity`**
- Remove `if condition { View }` conditionals
- View is always in the tree with `opacity` controlling visibility
- Prevents SwiftUI structural identity changes that trigger layout passes

**Rule:** For show/hide elements that shouldn't affect layout:
1. Use `.overlay()` instead of `ZStack` siblings
2. Always render the view (no `if`), control visibility with `.opacity()`
3. Reserve space with fixed padding on the parent

---

### Conditional Inside a LazyVStack Breaks scrollTo

**Problem:** `ScrollViewReader.scrollTo` silently no-ops for EVERY row — correct id, correct
anchor, no error, nothing moves. (Aloft s75–s77: cost three debugging sessions because two
plausible decoys — an anchor change and an `AnyHashable`-boxed id — sat in the same commit.)

```swift
// BROKEN: if/else INSIDE the lazy container — _ConditionalContent wraps the rows
// and breaks scrollTo's row-anchor resolution
LazyVStack {
    if sectioned {
        sectionedRows
    } else {
        ForEach(items) { row($0) }
    }
}

// WORKS: hoist the branch — one LazyVStack per arm, shared modifiers on a Group
Group {
    if sectioned {
        LazyVStack { sectionedRows }
    } else {
        LazyVStack { ForEach(items) { row($0) } }
    }
}
```

**Rule:** Never branch view content inside a `LazyVStack` whose rows are `scrollTo` targets.
To machine-verify a scrollTo without eyeballs: watch whether the stack's measured height (a
GeometryReader preference) churns after the call — a real scroll realizes rows and moves the
estimate; silence = no-op.

---

### Scroll-Varying Measurements Stored in @State Live-Lock Layout

**Problem:** App pins the main thread at 100% ("Not Responding") during scrolling; `sample`
shows `LazySubviewPlacements.placeSubviews` hot with app symbols nearly absent.

```swift
// BROKEN: a LazyVStack's measured height SHIFTS as rows realize/de-realize while
// scrolling; each change → @State write → body invalidation → re-placement → new
// measurement… flushed synchronously inside ONE run-loop observer callback
.onPreferenceChange(HeightKey.self) { measuredHeight = $0 }   // @State

// WORKS: record into a reference type — mutation doesn't invalidate the view;
// read imperatively where needed
.onPreferenceChange(HeightKey.self) { [holder] in holder.height = $0 }
```

**Rule:** A measurement that varies with scroll position (lazy-container heights,
realized-row preferences) must never re-enter the view graph via `@State` — sink it into a
plain reference holder (or a notification) and read it imperatively. Unit tests and
summon/typing CPU traces will NOT catch this class; only live scrolling closes the cycle.

---

## Threading Issues

### Publishing from Background Threads

**Problem:** Purple runtime warning, potential crashes.

```swift
// BROKEN: Combine sink runs on background thread
cancellable = publisher
    .sink { value in
        viewModel.value = value  // Wrong thread!
    }

// WORKS: Receive on main thread
cancellable = publisher
    .receive(on: DispatchQueue.main)
    .sink { value in
        viewModel.value = value
    }
```

**Rule:** Always `.receive(on: DispatchQueue.main)` before updating `@Published` properties.

---

### Deferred @Published Updates

**Problem:** Removing `DispatchQueue.main.async` breaks updates.

```swift
// Sometimes needed to defer @Published changes
DispatchQueue.main.async {
    self.viewModel.isLoading = false
}
```

**Why:** Sometimes updates need to be deferred to the next run loop to avoid "Publishing changes from within view updates."

**Rule:** If removing `DispatchQueue.main.async` breaks things, it's probably needed for timing. Document why.

---

## NSCursor Issues

### Cursor Stack Imbalance

**Problem:** Cursor gets stuck in wrong state (spinning, crosshair, etc.)

```swift
// BROKEN: Push without guaranteed pop
func startOperation() {
    NSCursor.pointingHand.push()
    // If this throws, pop never happens
    try riskyOperation()
    NSCursor.pop()
}

// WORKS: Use defer
func startOperation() {
    NSCursor.pointingHand.push()
    defer { NSCursor.pop() }
    try riskyOperation()
}
```

**Rule:** Always use `defer { NSCursor.pop() }` immediately after pushing a cursor.

---

## Window and Popover Issues

### Window Style Causing Layout Problems

**Problem:** Extra space between title bar and content.

```swift
// PROBLEMATIC: Can cause spacing issues
.windowStyle(.hiddenTitleBar)

// SAFER: Standard window style
// (remove .windowStyle modifier entirely)
```

**Rule:** Only use `.windowStyle(.hiddenTitleBar)` if you've tested all layout scenarios.

### Full-Window NSViewRepresentable Overlay Makes the Whole App Mouse-Dead

**Problem:** Every SwiftUI control stops responding to the mouse — while drawing, keyboard,
menu bar, drag-drop, and accessibility (AXPress) all keep working. Maddening to diagnose because
everything *except* real clicks behaves normally, so it masquerades as a hit-testing or popover bug.

**Cause:** A helper `NSViewRepresentable` (the classic "reach the NSWindow" probe) attached with
`.overlay(...)`. You think it's zero-size (`NSView(frame: .zero)`), but SwiftUI sizes an overlay
representable to the **full overlay area** — and AppKit routes mouse events to the topmost NSView.
SwiftUI controls aren't NSViews; they never see the click. (PlayPlayPlay, 2026-07-12: two days of
popover-bug hunting; the tell was a plain *welcome window* being equally dead.)

```swift
// PROBLEMATIC: plain NSView in .overlay swallows every click in the window
struct WindowAccessor: NSViewRepresentable {
    func makeNSView(context: Context) -> NSView { NSView(frame: .zero) } // NOT zero-size in .overlay!
}

// FIX: click-transparent by construction — the mouse must never see the probe
private final class ClickThroughView: NSView {
    override func hitTest(_ point: NSPoint) -> NSView? { nil }
}
```

**Rule:** Any full-window helper representable must override `hitTest → nil`. Don't rely on
`.background` placement instead — a z-order change silently re-breaks it.
**Diagnostic:** if AXPress fires actions but real clicks don't, hunt for a hosted AppKit view lying
over the content; test a second, simpler window (it discriminates instantly).

### Popover Anchored via an `.offset` Proxy Opens at the Window's Top-Left

**Problem:** A `.popover` presented from an invisible proxy view (the standard trick for anchoring
a popover somewhere the presenting view can't live — e.g. outside an animated subtree) ignores
where the proxy is drawn and presents from the container's top-leading corner.

**Cause:** `.offset` is a `GeometryEffect` — a **render-time transform**. It moves the pixels and
the hit-test region, but the view's **layout frame** never moves, and NSPopover anchoring reads
the layout frame. A `GeometryReader` child sits at top-leading by default, so that's where the
popover appears. (PlayPlayPlay, 2026-07-12: caught in a user visual pass; the popover host proxy
was `.offset(x: rect.minX, y: rect.minY)`.)

```swift
// PROBLEMATIC: drawn over the target, but its LAYOUT frame is still at (0,0)
Color.clear.frame(width: rect.width, height: rect.height)
    .offset(x: rect.minX, y: rect.minY)
    .popover(...)            // presents from the top-left corner

// FIX: place by LAYOUT (.position), and attach .popover INSIDE it so the
// attachment anchor rect stays in the proxy's own (small) coordinate space
Color.clear.frame(width: rect.width, height: rect.height)
    .popover(...)            // anchor space = the small proxy — correct
    .position(x: rect.midX, y: rect.midY)
```

**Rule:** anchors, popovers, and anything that reads a view's *frame* need **layout** placement
(`.position`, `.padding`, alignment) — `.offset` is only for visuals. Modifier order matters:
`.popover` before `.position`, or the anchor space becomes the full-size positioning wrapper and
you're back at the corner.

---

## Quick Diagnostic Commands

When UI doesn't update, add this logging:

```swift
print("State check - hasSelection: \(hasSelection), isEnabled: \(isEnabled), count: \(items.count)")
```

If values are correct but UI is wrong → `@Observable` / `@State` observation issue.
If values are wrong → Logic bug, trace the data flow.

---

## SF Symbols renames — new-style names don't back-deploy

**Symptom:** `Image(systemName:)` renders blank on older macOS even though the name is right there in the SF Symbols app.

**Cause:** Apple renames symbols across SF Symbols releases (SF 7 / macOS 26 renamed the whole cursor family: `cursorarrow.click` → `pointer.arrow.click`, etc.). The SF Symbols app shows **only the new names**, but a new name exists only in the OS it shipped with — it is NOT aliased backward. Legacy names keep working forever (they alias forward to the current design).

**Fix:** when the deployment target predates the current OS, use the **legacy** name in code. Verify locally — the system catalog maps every name (including legacy) to its minimum OS:

```bash
# /System/Library/CoreServices/CoreGlyphs.bundle/Contents/Resources/name_availability.plist
# symbols dict: name → year token; year_to_release: token → {macOS: version}
```

(Caught 2026-07-12 in Aloft: `pointer.arrow.motionlines.click` = macOS 26-only; the identical glyph is `cursorarrow.motionlines.click` = macOS 11+.)

---

## Summary Table

| Issue | Symptom | Fix |
|-------|---------|-----|
| Nested mutation | UI doesn't update | Reassign parent property |
| @State + class | Buttons stuck | Mark the class `@Observable` |
| Split-pane choice | Wrong resize affordance | HSplitView/VSplitView if resizable, HStack + Divider if fixed |
| PreferenceKey conditional | Sizing breaks | Always use max(value, nextValue()) |
| .clipped() | Overlay escapes | Use .clipShape(Rectangle()) |
| Conditional view | Layout shifts | Use .overlay() + opacity, not if/ZStack |
| Background publish | Purple warning | .receive(on: .main) |
| Cursor imbalance | Cursor stuck | defer { NSCursor.pop() } |
| SF Symbols rename | Blank icon on older macOS | Use the legacy name (`pointer.arrow.*` → `cursorarrow.*`); check CoreGlyphs name_availability.plist |
| Popover proxy via .offset | Popover opens at window top-left | `.offset` is render-only; place the proxy with `.position` (layout), `.popover` attached inside |

---

*Add issues to this document as you encounter them.*

## macOS 26 (Tahoe): List `.onMove` silently dead when rows are 100% control

**Symptom:** drag-to-reorder in a `List { ForEach(...) { Toggle(...) } .onMove {...} }`
stops committing — no error, the model array just never changes. Code that user-verified
fine on pre-Tahoe macOS breaks with zero diffs.

**Cause:** `.onMove` on macOS adds a per-row drag recognizer that only starts on *inert*
row area. A row whose entire content is an interactive control (a full-row `Toggle` —
checkbox + label are ONE control; same class of issue as FB7367473's tap-gesture
conflict) leaves nothing to grab; under Tahoe's rebuilt List the control wins the
mouse-down outright.

**Fix:** separate the control from an inert, draggable region:

```swift
HStack(spacing: 8) {
    Toggle("", isOn: binding).labelsHidden()   // checkbox only
    Label(title, systemImage: symbol)          // inert → initiates the row drag
    Spacer(minLength: 0)
}
.contentShape(Rectangle())
```

Trade-off: clicking the row text now drags instead of toggling. Diagnosis shortcut for
"reorder not sticking": check the *persisted* order first — if it's still the migration
default, the write path (drag) never fired; don't chase the display path.
(Found in QuickStatsPanel, 2026-07-12; reorder had been silently broken since the Tahoe update.)

## @Observable can't see through non-observable objects (dead Edit ▸ Undo)

**Symptom:** a menu item or view bound to state like `undoManager.canUndo` never
updates — Edit ▸ Undo (and ⌘Z) stays greyed out forever even though undo
registrations happen. No error; the value is *correct* when read, the UI just
never re-reads it.

**Cause:** `@Observable` only tracks its **own stored properties**. A computed
property that reaches into a plain Foundation object (`UndoManager`,
`NotificationCenter`-backed state, any non-`@Observable` reference type held in a
`let`) produces no observation events — SwiftUI captures the value once at launch
and is never invalidated.

**Fix:** mirror the foreign object's state into stored properties on the
`@Observable` class, refreshed on every mutation path:

```swift
@Observable final class SelectionUndoManager {
    private let undoManager = UndoManager()   // invisible to observation
    private(set) var canUndo = false          // stored mirror — observable
    private(set) var canRedo = false

    private func refreshMirrors() {           // call after EVERY register/undo/redo/clear
        canUndo = undoManager.canUndo
        canRedo = undoManager.canRedo
    }
}
```

Diagnosis shortcut: if a SwiftUI-bound value is "right when you print it but the UI
never changes", ask *what observable stored property changed* — if the answer is
none, you've found it. (Penumbra ⌘Z fix, 2026-07-12; broken since the class was
introduced, caught only by a live smoke because unit tests read the value directly.)

## PreferenceKey from a GeometryReader background never updates (macOS)

**Symptom:** the classic size-measuring pattern —
`.background(GeometryReader { Color.clear.preference(key:, value: geo.size.height) })`
plus `.onPreferenceChange` — delivers **only the initial `defaultValue` (0)** and
then goes silent. Anything driven by it (window auto-resize, layout math) acts on 0
once and never corrects.

**Cause:** preference updates set during a *layout-time* GeometryReader background
are not reliably propagated by NSHostingView on macOS. The value genuinely changes;
the `onPreferenceChange` callback is just never re-invoked.

**Fix:** skip the preference channel entirely — use state-driven callbacks inside
the same GeometryReader:

```swift
.background(
    GeometryReader { geo in
        Color.clear
            .onAppear { heightChanged(geo.size.height) }
            .onChange(of: geo.size.height) { heightChanged($0) }
    }
)
.frame(minWidth: 480, maxWidth: .infinity, minHeight: 75)  // AFTER the background
```

Two placement traps in the same pattern: (1) put the measuring `.background`
**before** `.frame` — after it you measure the flexible wrapper, which inflates to
the window's proposal, so the loop reads back its own output and reports "nothing
to fix"; (2) if the measured stack contains a both-ways-flexible child (e.g.
`.aspectRatio(16/9, contentMode: .fit)` tiles), that child silently absorbs any
squeeze and the measured height never changes — give it a rigid width-derived
`.frame(height:)` so the container is the only flexible element per axis.
(VideoWallpaper window auto-resize, 2026-07-12; NSLog instrumentation showed a
single `measured=0.0` and the main window collapsed to a bare 32pt title bar.)

---

## macOS 26+: popover presented right after NSOpenPanel dismissal crashes the app

**Problem:** Hard crash (`EXC_BREAKPOINT` via `+[NSApplication _crashOnException:]`)
when a `.popover` presents immediately after `NSOpenPanel.runModal()` returns. On
macOS 26+ open/save panels are **ViewBridge-hosted for ALL apps** (the panel content
is an out-of-process `NSRemoteView`), not just sandboxed ones. `runModal()` returning
does **not** mean the panel is gone — its XPC teardown completes asynchronously over
the next runloop turns. Flip a `@Published`/`@State` presentation flag synchronously
in that window and SwiftUI presents the popover on the very next layout pass; the
popover's window ordering posts a notification the dying panel's **stale
`NSRemoteView` observer** (`containingWindowWillOrderOnScreen:`) still receives — it
throws, AppKit's crash-on-exceptions traps.

```swift
// BROKEN: presentation flag flipped in the same runloop turn as panel dismissal
guard panel.runModal() == .OK, let url = panel.url else { return }
showConfirmPopover = true   // races the panel's ViewBridge teardown → crash

// WORKS: defer past the async XPC teardown (@MainActor class → Task inherits actor)
guard panel.runModal() == .OK, let url = panel.url else { return }
Task {
    try? await Task.sleep(for: .milliseconds(400))
    showConfirmPopover = true
}
```

**Rule:** Never present a popover/sheet from the same runloop turn in which an
open/save panel was dismissed. A bare `DispatchQueue.main.async` is NOT enough —
the teardown spans XPC round-trips; use a short (~400 ms, humanly imperceptible)
deferral. Migrating to `panel.begin(completionHandler:)` does not fix it — the
completion fires in the same race window. Leave a why-comment on the delay or a
future cleanup will remove it. (Conjoyn 1.0.3 output-folder crash, 2026-07-18,
macOS 27.0 beta; fix `ConversionViewModel.swift:293`, commit `dcf44b8`.)
