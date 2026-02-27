<!--
TRIGGERS: UI element, component name, what is this called, Apple UI, SwiftUI component, UIKit
PHASE: any
LOAD: on-request
-->

# macOS & iOS UI Design Elements

A reference for discussing Apple platform UI components with precision.

## Window & Container Types

### Window (macOS)
The fundamental container for app content. Has a title bar, traffic lights (close/minimize/zoom), and content area.

### Scene (iOS)
A single instance of your app's UI. An app can have multiple scenes (e.g., two Safari windows on iPad).

### Sheet
A modal view that slides down from the top (macOS) or up from the bottom (iOS). Blocks interaction with parent until dismissed.

Use: focused tasks, confirmations, settings that need immediate attention

### Popover
A floating container that points to its source element with an arrow. Dismisses when clicking outside.

Use: contextual controls, inspectors, secondary options

### Alert
A modal dialog demanding user attention. Contains a message and action buttons.

Types: informational, warning, critical/destructive

### Panel (macOS)
A floating auxiliary window. Stays above regular windows but doesn't block interaction.

Examples: Fonts panel, Colors panel, inspector panels

### Inspector
A panel or sidebar showing properties of the current selection.

Position: typically right sidebar (macOS) or popover/sheet (iOS)

## Navigation Structures

### Navigation Bar (iOS)
The bar at the top of a view containing back button, title, and trailing actions.

```
┌─────────────────────────────────┐
│  < Back      Title      Edit    │
└─────────────────────────────────┘
```

### Toolbar
A bar containing actions relevant to the current content.

Position: top of window (macOS), bottom of screen (iOS)

```
macOS toolbar:
┌─────────────────────────────────────┐
│ [◀ ▶] [+] [Share]     🔍 Search     │
└─────────────────────────────────────┘

iOS toolbar:
┌─────────────────────────────────────┐
│  [↩]    [📁]    [✏]    [📤]   [🗑]  │
└─────────────────────────────────────┘
```

### Tab Bar (iOS)
Bottom navigation showing app's main sections. Persists across the app.

```
┌─────────────────────────────────────┐
│   🏠      🔍      📚      ⚙️       │
│  Home   Search  Library  Settings   │
└─────────────────────────────────────┘
```

### Sidebar
A column (usually left) for navigation or filtering. Can collapse.

Standard widths: ~200–300pt (macOS), varies (iPad)

### Source List (macOS)
A sidebar variant with grouped, hierarchical navigation. Often has disclosure triangles.

Example: Finder sidebar, Mail mailboxes

### Outline View
Hierarchical list with expandable/collapsible rows (disclosure triangles).

### Split View
Two or more content panes side by side. Often sidebar + detail or list + detail.

Types: 
- Two-column (sidebar | content)
- Three-column (sidebar | list | detail)

### Tab View
Multiple content views switched via tabs. Only one visible at a time.

## Content Views

### List / Table View
Rows of content, often tappable. Can be plain, grouped, or inset grouped.

```
Plain:              Grouped:             Inset Grouped:
┌───────────┐      ┌───────────┐        ╭───────────╮
│ Item 1    │      │ SECTION A │        │ SECTION A │
├───────────┤      ├───────────┤        ├───────────┤
│ Item 2    │      │ Item 1    │        │ Item 1    │
├───────────┤      │ Item 2    │        │ Item 2    │
│ Item 3    │      └───────────┘        ╰───────────╯
└───────────┘      ┌───────────┐
                   │ SECTION B │
```

### Collection View
Grid or custom layout of items. More flexible than list view.

### Scroll View
A view whose content can be larger than its frame. Scrolls to reveal hidden content.

### Stack View
Arranges subviews in a horizontal or vertical line. Auto-handles spacing and alignment.

Axis: horizontal (HStack) or vertical (VStack)

### Grid
Two-dimensional arrangement of views in rows and columns.

## Controls

### Button
A tappable control that triggers an action.

Styles: 
- Bordered/filled (primary actions)
- Borderless/plain (secondary)
- Destructive (red, for dangerous actions)
- Gray (cancel/neutral)

### Toggle / Switch
A binary on/off control.

```
iOS:     ◯────●  (ON)     ●────◯  (OFF)
macOS:   [✓] Checkbox label
```

### Slider
Selects a value from a continuous range.

```
Min ├────────●──────────┤ Max
```

### Stepper
Increment/decrement a value with +/– buttons.

```
[ − ]  42  [ + ]
```

### Picker
Selects from a list of options.

Styles:
- Wheel (iOS classic)
- Segmented (inline options)
- Menu (dropdown)
- Inline (expanded list)

### Segmented Control
A horizontal set of mutually exclusive options.

```
┌─────┬─────┬─────┐
│ Day │ Week│Month│
└─────┴─────┴─────┘
```

### Text Field
Single-line text input.

### Text Editor / Text View
Multi-line text input.

### Search Field
Text field with search icon, clear button, and optional scope bar.

```
┌─🔍─────────────────────────╳─┐
│   Search...                  │
└──────────────────────────────┘
```

### Menu
A list of actions or options, shown on click/tap.

Types:
- Pull-down menu (toolbar actions)
- Pop-up menu (selection from options)
- Context menu (right-click / long-press)

### Date Picker
Selects date and/or time.

Styles: compact, inline, wheel, graphical (calendar)

### Color Picker
Selects a color.

### Progress Indicator
Shows task progress.

Types:
- Determinate (progress bar with percentage)
- Indeterminate (spinner, no known endpoint)

```
Determinate:   [████████░░░░░░░] 55%
Indeterminate: ⏳ or spinning wheel
```

## Feedback & Status

### Label
Static text displaying information.

### Badge
A small indicator (usually a number) overlaid on an icon.

```
  📬
   3   ← badge
```

### Banner
A temporary message appearing at the top of a view.

### Toast (not Apple-native, but common)
A brief message that appears and auto-dismisses.

### Activity Indicator
A spinner showing ongoing activity.

### Pull to Refresh
Gesture to reload content by pulling down on a scroll view.

## Gestures

| Gesture | Action |
|---------|--------|
| Tap | Primary action |
| Double-tap | Secondary action, zoom |
| Long press | Context menu, drag initiation |
| Swipe | Delete, actions, navigation |
| Pinch | Zoom in/out |
| Rotate | Rotation (maps, images) |
| Pan / Drag | Move content or objects |
| Edge swipe | Back navigation (iOS) |

## Layout Concepts

### Safe Area
The portion of the screen not obscured by system UI (notch, home indicator, status bar).

### Margins
Padding from the edge of the container. System provides "readable content" margins for text.

### Spacing
Distance between elements. Apple uses an 8pt grid system as a baseline.

### Alignment
How items line up: leading, center, trailing, top, bottom, baseline.

### Adaptive Layout
UI that responds to size class, device, or orientation.

Size classes:
- Compact width (iPhone portrait)
- Regular width (iPad, iPhone landscape)
- Compact height (iPhone landscape)
- Regular height (most configurations)

## Visual Styling

### Materials (Blur Effects)
Translucent backgrounds that blur content behind them.

Types: ultra-thin, thin, regular, thick, chrome

### Vibrancy
Text/icons that blend with the blurred material behind them for better readability.

### SF Symbols
Apple's icon system. Vector icons that scale with text and support weights/variants.

### Accent Color / Tint Color
The app's primary interactive color. Applied to buttons, links, selections.

### Semantic Colors
Colors that adapt to light/dark mode and accessibility settings.

Examples: label, secondaryLabel, tertiaryLabel, systemBackground, systemGroupedBackground

### Corner Radius
Rounded corners on containers. Apple uses continuous (squircle) curves, not simple arcs.

Common values: 10pt (buttons), 12pt (cards), 20pt+ (sheets)

## Quick Reference Table

| Element | macOS | iOS | Purpose |
|---------|-------|-----|---------|
| Sheet | Slides from top | Slides from bottom | Modal task |
| Popover | Points to source | Points to source | Contextual UI |
| Sidebar | Left column | iPad only | Navigation |
| Toolbar | Top of window | Bottom of screen | Actions |
| Tab Bar | Less common | Bottom persistent | App sections |
| Navigation Bar | N/A | Top of view | View title + nav |
| Inspector | Right panel/popover | Sheet/popover | Properties |

## Project UI Conventions

These preferences apply to all projects unless explicitly overridden in project CLAUDE.md.

### 1. No Tahoe Sidebar

Do **not** use `NavigationSplitView` or the macOS Tahoe liquid glass sidebar style. These create opinionated navigation that's hard to customize and introduces platform-version coupling.

```swift
// ❌ AVOID
NavigationSplitView {
    SidebarContent()
} detail: {
    DetailContent()
}

// ❌ AVOID — Tahoe glass sidebar styling
.navigationSplitViewStyle(.prominentDetail)
```

### 2. HStack + Divider Panes

Use `HStack(spacing: 0)` with `Divider()` for split layouts. This gives full control over widths, collapse behavior, and avoids `HSplitView` layout bugs (see `20_swiftui-gotchas.md` gotcha #3).

```swift
// ✅ PREFERRED
HStack(spacing: 0) {
    SidebarContent()
        .frame(width: sidebarWidth)

    Divider()

    DetailContent()
        .frame(maxWidth: .infinity)
}
```

For three-column layouts:

```swift
// ✅ PREFERRED
HStack(spacing: 0) {
    NavigationPane()
        .frame(width: navWidth)

    Divider()

    ListPane()
        .frame(width: listWidth)

    Divider()

    DetailPane()
        .frame(maxWidth: .infinity)
}
```

### 3. AppKit Controls (All Interactive Elements via NSViewRepresentable)

Do **not** use SwiftUI interactive controls (`Button`, `Toggle`, `Picker`, `Stepper`, `Slider`, `DatePicker`, `ColorPicker`, segmented `Picker`). Wrap their AppKit equivalents via `NSViewRepresentable` for consistent native macOS appearance.

**Why:** SwiftUI controls on macOS use `.bordered` / Catalyst-like styling (rounded capsules, padded toggles) that look like an iPad port. AppKit controls give the classic pro-Mac look — rectangular buttons with subtle ~4pt corner radius, compact toggles, native popup menus.

#### Mapping Table

| SwiftUI Control | AppKit Replacement | Notes |
|----------------|-------------------|-------|
| `Button` | `NSButton` | `.rounded` bezel for standard, `.texturedSquare` for toolbar |
| `Toggle` | `NSButton` (checkbox) | `.switch` type, or `NSSwitch` for switch style |
| `Picker` (menu) | `NSPopUpButton` | Native dropdown menu |
| `Picker` (segmented) | `NSSegmentedControl` | Native segmented control |
| `Slider` | `NSSlider` | Linear or circular |
| `Stepper` | `NSStepper` | Paired with `NSTextField` for value display |
| `DatePicker` | `NSDatePicker` | `.textFieldAndStepper` or `.clockAndCalendar` style |
| `ColorPicker` | `NSColorWell` | Standard or `.minimal` style |
| `TextField` | `NSTextField` | Native text input |
| `TextEditor` | `NSTextView` | Multi-line editing, scrollable |

#### Button Wrapper

```swift
// ❌ AVOID
Button("Export") { handleExport() }

// ✅ PREFERRED
struct AppKitButton: NSViewRepresentable {
    let title: String
    var bezelStyle: NSButton.BezelStyle = .rounded
    let action: () -> Void

    func makeNSView(context: Context) -> NSButton {
        let button = NSButton(title: title, target: context.coordinator, action: #selector(Coordinator.clicked))
        button.bezelStyle = bezelStyle
        return button
    }

    func updateNSView(_ nsView: NSButton, context: Context) {
        nsView.title = title
        nsView.bezelStyle = bezelStyle
    }

    func makeCoordinator() -> Coordinator { Coordinator(action: action) }

    class Coordinator: NSObject {
        let action: () -> Void
        init(action: @escaping () -> Void) { self.action = action }
        @objc func clicked() { action() }
    }
}
```

#### Toggle (Checkbox) Wrapper

```swift
// ❌ AVOID
Toggle("Show grid", isOn: $showGrid)

// ✅ PREFERRED
struct AppKitCheckbox: NSViewRepresentable {
    let title: String
    @Binding var isOn: Bool

    func makeNSView(context: Context) -> NSButton {
        let checkbox = NSButton(checkboxWithTitle: title, target: context.coordinator, action: #selector(Coordinator.toggled))
        checkbox.state = isOn ? .on : .off
        return checkbox
    }

    func updateNSView(_ nsView: NSButton, context: Context) {
        nsView.title = title
        nsView.state = isOn ? .on : .off
    }

    func makeCoordinator() -> Coordinator { Coordinator(isOn: $isOn) }

    class Coordinator: NSObject {
        let isOn: Binding<Bool>
        init(isOn: Binding<Bool>) { self.isOn = isOn }
        @objc func toggled(_ sender: NSButton) { isOn.wrappedValue = sender.state == .on }
    }
}
```

#### Popup (Picker) Wrapper

```swift
// ❌ AVOID
Picker("Format", selection: $format) {
    ForEach(formats) { Text($0.name).tag($0) }
}

// ✅ PREFERRED
struct AppKitPopup<T: Hashable>: NSViewRepresentable {
    let items: [T]
    let titleForItem: (T) -> String
    @Binding var selection: T

    func makeNSView(context: Context) -> NSPopUpButton {
        let popup = NSPopUpButton(frame: .zero, pullsDown: false)
        popup.target = context.coordinator
        popup.action = #selector(Coordinator.selected)
        return popup
    }

    func updateNSView(_ nsView: NSPopUpButton, context: Context) {
        nsView.removeAllItems()
        for item in items { nsView.addItem(withTitle: titleForItem(item)) }
        if let idx = items.firstIndex(of: selection) { nsView.selectItem(at: idx) }
    }

    func makeCoordinator() -> Coordinator { Coordinator(parent: self) }

    class Coordinator: NSObject {
        let parent: AppKitPopup
        init(parent: AppKitPopup) { self.parent = parent }
        @objc func selected(_ sender: NSPopUpButton) {
            let idx = sender.indexOfSelectedItem
            if idx >= 0 && idx < parent.items.count { parent.selection = parent.items[idx] }
        }
    }
}
```

#### Segmented Control Wrapper

```swift
// ❌ AVOID
Picker("View", selection: $viewMode) { ... }.pickerStyle(.segmented)

// ✅ PREFERRED
struct AppKitSegmented<T: Hashable>: NSViewRepresentable {
    let items: [(title: String, value: T)]
    @Binding var selection: T

    func makeNSView(context: Context) -> NSSegmentedControl {
        let control = NSSegmentedControl(labels: items.map(\.title),
                                          trackingMode: .selectOne,
                                          target: context.coordinator,
                                          action: #selector(Coordinator.changed))
        if let idx = items.firstIndex(where: { $0.value == selection }) {
            control.selectedSegment = idx
        }
        return control
    }

    func updateNSView(_ nsView: NSSegmentedControl, context: Context) {
        if let idx = items.firstIndex(where: { $0.value == selection }) {
            nsView.selectedSegment = idx
        }
    }

    func makeCoordinator() -> Coordinator { Coordinator(parent: self) }

    class Coordinator: NSObject {
        let parent: AppKitSegmented
        init(parent: AppKitSegmented) { self.parent = parent }
        @objc func changed(_ sender: NSSegmentedControl) {
            let idx = sender.selectedSegment
            if idx >= 0 && idx < parent.items.count { parent.selection = parent.items[idx].value }
        }
    }
}
```

> **Tip:** Keep all AppKit wrappers in a shared `AppKit/` folder (e.g., `Views/AppKit/`). Each project should build this wrapper set once and reuse across all views.

### 4. Toolbars: SwiftUI .toolbar + AppKit-Style ButtonStyle

**Exception to the "no SwiftUI controls" rule.** Keep SwiftUI `.toolbar` for structure and placement — it handles `.navigation`, `.principal`, `.primaryAction` grouping and `toolbarRole(.editor)` integration with minimal code. But use a custom `ButtonStyle` inside the toolbar that renders with AppKit appearance (~4pt corner radius, flat background, subtle border).

```swift
// ✅ PREFERRED — SwiftUI .toolbar with AppKit-styled buttons
.toolbar {
    ToolbarItemGroup(placement: .navigation) {
        Button(action: importFile) {
            Image(systemName: "plus")
        }
        .buttonStyle(AppKitToolbarButtonStyle(isOn: .constant(false)))
    }

    ToolbarItemGroup(placement: .principal) {
        // View mode toggles
    }

    ToolbarItemGroup(placement: .primaryAction) {
        Button(action: toggleSidebar) {
            Image(systemName: "sidebar.right")
        }
        .buttonStyle(AppKitToolbarButtonStyle(isOn: $showSidebar))
    }
}
.toolbarRole(.editor)
```

```swift
/// Toolbar button style with native AppKit appearance.
/// Flat background, 4pt corners, accent color when active.
struct AppKitToolbarButtonStyle: ButtonStyle {
    @Binding var isOn: Bool

    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .padding(.horizontal, 8)
            .padding(.vertical, 6)
            .foregroundColor(isOn ? .white : .primary)
            .background(
                ZStack {
                    if isOn {
                        Color.accentColor
                    } else {
                        Color(nsColor: .gray.withAlphaComponent(0.2))
                    }
                    if configuration.isPressed {
                        Color.black.opacity(0.2)
                    }
                }
            )
            .cornerRadius(4)
            .overlay(
                RoundedRectangle(cornerRadius: 4)
                    .stroke(Color.black.opacity(0.2), lineWidth: 1)
            )
            .scaleEffect(configuration.isPressed ? 0.95 : 1.0)
            .animation(.easeInOut(duration: 0.1), value: configuration.isPressed)
    }
}
```

> **Why not NSToolbar?** NSToolbar gives user customization (drag items in/out) and overflow menus, but requires `NSToolbarDelegate` boilerplate (~80 lines) and bridging to SwiftUI state. For most apps, SwiftUI `.toolbar` + custom style gets 90% of the native look with 10% of the code. Use NSToolbar only if you specifically need user-customizable toolbars.

---

## Related Terms

- **HIG**: Human Interface Guidelines (Apple's design documentation)
- **UIKit**: iOS/iPadOS UI framework (imperative)
- **AppKit**: macOS UI framework (imperative)
- **SwiftUI**: Declarative UI framework (cross-platform)
- **Catalyst**: Run iPad apps on macOS
- **Size Class**: Categorization of available space (compact/regular)
- **Trait Collection**: Environment info (size class, appearance, accessibility)
