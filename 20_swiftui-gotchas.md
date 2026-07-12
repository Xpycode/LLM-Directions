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

---

## Quick Diagnostic Commands

When UI doesn't update, add this logging:

```swift
print("State check - hasSelection: \(hasSelection), isEnabled: \(isEnabled), count: \(items.count)")
```

If values are correct but UI is wrong → `@Observable` / `@State` observation issue.
If values are wrong → Logic bug, trace the data flow.

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

---

*Add issues to this document as you encounter them.*
