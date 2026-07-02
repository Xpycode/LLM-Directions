<!--
TRIGGERS: NavigationSplitView, HSplitView, AppKit controls, NSViewRepresentable, no SwiftUI controls, Tahoe sidebar, liquid glass sidebar, AppKitToolbarButtonStyle, toolbar buttons, project UI conventions
PHASE: implementation, UI review
LOAD: full
-->

# Project UI Conventions

**These preferences apply to all projects unless explicitly overridden in project CLAUDE.md.**

*For general UI terminology (what's a Sheet, a Popover, a Toast), see `41_ui-vocabulary.md`.
This doc is project-specific rules, not vocabulary.*

---

## 1. No Tahoe Sidebar in the Primary Window

Do **not** use `NavigationSplitView` or the macOS Tahoe liquid glass sidebar style **for the
primary app window**. These create opinionated navigation that's hard to customize and
introduces platform-version coupling.

```swift
// ❌ AVOID in the primary app window
NavigationSplitView {
    SidebarContent()
} detail: {
    DetailContent()
}

// ❌ AVOID — Tahoe glass sidebar styling
.navigationSplitViewStyle(.prominentDetail)
```

**Exception:** `NavigationSplitView` is acceptable in a **secondary utility window** (e.g. a
Help window), where the stock navigation chrome is fine and the platform-version coupling
doesn't affect the app's primary identity. See `cookbook/01-window-layouts.md`.

For the primary window, use the split-pane decision tree instead (see `cookbook/00-app-shell.md`
§5 and `cookbook/01-window-layouts.md`): `HSplitView`/`VSplitView` for user-resizable panes,
`HStack` + `Divider()` for a fixed-width sidebar.

## 2. HStack + Divider Panes — the Fixed-Width Branch

`HStack(spacing: 0)` with `Divider()` is the **fixed-width / non-resizable** branch of the
split-pane decision tree — use it when the sidebar has no draggable divider. It gives full
control over widths and collapse behavior. For a **resizable** pane (draggable divider), use
`HSplitView`/`VSplitView` instead — see `cookbook/00-app-shell.md` §5.

```swift
// ✅ Fixed-width sidebar (no draggable divider)
HStack(spacing: 0) {
    SidebarContent()
        .frame(width: sidebarWidth)

    Divider()

    DetailContent()
        .frame(maxWidth: .infinity)
}
```

For three-column fixed layouts:

```swift
// ✅ Fixed-width three-column layout
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

## 3. AppKit Controls (All Interactive Elements via NSViewRepresentable)

Do **not** use SwiftUI interactive controls (`Button`, `Toggle`, `Picker`, `Stepper`, `Slider`, `DatePicker`, `ColorPicker`, segmented `Picker`). Wrap their AppKit equivalents via `NSViewRepresentable` for consistent native macOS appearance.

**Why:** SwiftUI controls on macOS use `.bordered` / Catalyst-like styling (rounded capsules, padded toggles) that look like an iPad port. AppKit controls give the classic pro-Mac look — rectangular buttons with subtle ~4pt corner radius, compact toggles, native popup menus.

### Mapping Table

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

### Button Wrapper

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

### Toggle (Checkbox) Wrapper

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

### Popup (Picker) Wrapper

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

### Segmented Control Wrapper

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

## 4. Toolbars: SwiftUI .toolbar + AppKit-Style ButtonStyle

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

## Related

- `41_ui-vocabulary.md` — UI terminology reference (Apple + Web)
- `36_ui-changes-protocol.md` — process for proposing UI changes, checks against these constraints
- `cookbook/00-app-shell.md`, `cookbook/01-window-layouts.md` — the split-pane decision tree these rules feed into
