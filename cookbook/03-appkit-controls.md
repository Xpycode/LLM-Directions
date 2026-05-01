## AppKit Controls

All interactive controls use AppKit wrappers via `NSViewRepresentable` instead of SwiftUI controls. SwiftUI's `.bordered` button style renders as rounded capsules; AppKit's `.rounded` bezel gives the classic ~4pt corner radius. This applies to every control — buttons, toggles, pickers, sliders, etc. See `41_apple-ui.md` → Project UI Conventions for the full mapping table.

**Convention:** Keep all wrappers in `Views/AppKit/` and reuse across the project.

### AppKitButton (NSButton)

**Replaces:** SwiftUI `Button`

```swift
struct AppKitButton: NSViewRepresentable {
    let title: String
    var bezelStyle: NSButton.BezelStyle = .rounded
    var keyEquivalent: String = ""
    let action: () -> Void

    func makeNSView(context: Context) -> NSButton {
        let button = NSButton(title: title, target: context.coordinator,
                              action: #selector(Coordinator.clicked))
        button.bezelStyle = bezelStyle
        button.keyEquivalent = keyEquivalent
        return button
    }

    func updateNSView(_ nsView: NSButton, context: Context) {
        nsView.title = title
        nsView.bezelStyle = bezelStyle
        nsView.keyEquivalent = keyEquivalent
    }

    func makeCoordinator() -> Coordinator { Coordinator(action: action) }

    class Coordinator: NSObject {
        let action: () -> Void
        init(action: @escaping () -> Void) { self.action = action }
        @objc func clicked() { action() }
    }
}

// Usage
AppKitButton(title: "Export", action: handleExport)
AppKitButton(title: "OK", bezelStyle: .rounded, keyEquivalent: "\r", action: confirm)
AppKitButton(title: "Delete", bezelStyle: .texturedSquare, action: delete)
```

**Bezel styles:** `.rounded` (standard), `.texturedSquare` (toolbar), `.regularSquare` (flat), `.recessed` (subtle)

**Best for:** Any tappable action — primary, secondary, destructive, toolbar buttons.

---

### AppKitCheckbox (NSButton, checkbox type)

**Replaces:** SwiftUI `Toggle`

```swift
struct AppKitCheckbox: NSViewRepresentable {
    let title: String
    @Binding var isOn: Bool

    func makeNSView(context: Context) -> NSButton {
        let checkbox = NSButton(checkboxWithTitle: title, target: context.coordinator,
                                action: #selector(Coordinator.toggled))
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

// Usage
AppKitCheckbox(title: "Show grid", isOn: $showGrid)
AppKitCheckbox(title: "Auto-save", isOn: $autoSave)
```

**Best for:** Boolean settings, preferences, feature toggles.

---

### AppKitPopup (NSPopUpButton)

**Replaces:** SwiftUI `Picker` with `.menu` style

```swift
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

// Usage
AppKitPopup(items: ExportFormat.allCases, titleForItem: \.rawValue, selection: $format)
```

**Best for:** Enum selection, format pickers, any dropdown menu.

---

### AppKitSegmented (NSSegmentedControl)

**Replaces:** SwiftUI `Picker` with `.segmented` style

```swift
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

// Usage
AppKitSegmented(items: [("List", ViewMode.list), ("Grid", ViewMode.grid)], selection: $viewMode)
```

**Best for:** View mode switching, tab-like selection, mutually exclusive options.

---

### AppKitSlider (NSSlider)

**Replaces:** SwiftUI `Slider`

```swift
struct AppKitSlider: NSViewRepresentable {
    @Binding var value: Double
    var minValue: Double = 0
    var maxValue: Double = 1

    func makeNSView(context: Context) -> NSSlider {
        let slider = NSSlider(value: value, minValue: minValue, maxValue: maxValue,
                              target: context.coordinator, action: #selector(Coordinator.changed))
        slider.isContinuous = true
        return slider
    }

    func updateNSView(_ nsView: NSSlider, context: Context) {
        nsView.doubleValue = value
        nsView.minValue = minValue
        nsView.maxValue = maxValue
    }

    func makeCoordinator() -> Coordinator { Coordinator(value: $value) }

    class Coordinator: NSObject {
        let value: Binding<Double>
        init(value: Binding<Double>) { self.value = value }
        @objc func changed(_ sender: NSSlider) { value.wrappedValue = sender.doubleValue }
    }
}

// Usage
AppKitSlider(value: $opacity, minValue: 0, maxValue: 1)
AppKitSlider(value: $volume, minValue: 0, maxValue: 100)
```

**Best for:** Continuous value adjustment — opacity, volume, zoom, timeline scrubbing.

---

### AppKitTextField (NSTextField)

**Replaces:** SwiftUI `TextField`

```swift
struct AppKitTextField: NSViewRepresentable {
    let placeholder: String
    @Binding var text: String
    var onCommit: (() -> Void)?

    func makeNSView(context: Context) -> NSTextField {
        let field = NSTextField()
        field.placeholderString = placeholder
        field.stringValue = text
        field.delegate = context.coordinator
        return field
    }

    func updateNSView(_ nsView: NSTextField, context: Context) {
        if nsView.stringValue != text { nsView.stringValue = text }
    }

    func makeCoordinator() -> Coordinator { Coordinator(parent: self) }

    class Coordinator: NSObject, NSTextFieldDelegate {
        let parent: AppKitTextField
        init(parent: AppKitTextField) { self.parent = parent }

        func controlTextDidChange(_ obj: Notification) {
            guard let field = obj.object as? NSTextField else { return }
            parent.text = field.stringValue
        }

        func control(_ control: NSControl, textShouldEndEditing fieldEditor: NSText) -> Bool {
            parent.onCommit?()
            return true
        }
    }
}

// Usage
AppKitTextField(placeholder: "Search...", text: $searchText)
AppKitTextField(placeholder: "File name", text: $fileName, onCommit: save)
```

**Best for:** Text input fields, search bars, inline editing.

---

### AppKitToolbarButtonStyle (SwiftUI .toolbar Exception)

**Source:** `Penumbra/Views/ToolbarButtonStyles.swift`

SwiftUI `.toolbar` is the **one exception** to the "no SwiftUI controls" rule. It handles placement (`.navigation`, `.principal`, `.primaryAction`) and `toolbarRole(.editor)` with minimal code. But toolbar buttons must use a custom `ButtonStyle` for native AppKit appearance instead of SwiftUI's default capsule styling.

```swift
/// Toolbar button with native AppKit appearance.
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

// Usage in .toolbar
.toolbar {
    ToolbarItemGroup(placement: .navigation) {
        Button(action: importFile) {
            Image(systemName: "plus")
        }
        .buttonStyle(AppKitToolbarButtonStyle(isOn: .constant(false)))
    }

    ToolbarItemGroup(placement: .primaryAction) {
        Button(action: { showSidebar.toggle() }) {
            Image(systemName: "sidebar.right")
        }
        .buttonStyle(AppKitToolbarButtonStyle(isOn: $showSidebar))
    }
}
.toolbarRole(.editor)
```

**Why not NSToolbar?** NSToolbar gives user customization (drag items in/out) and overflow menus, but requires `NSToolbarDelegate` boilerplate (~80 lines) and bridging to SwiftUI state. SwiftUI `.toolbar` + custom style gets 90% of the native look with 10% of the code.

**Best for:** All toolbar buttons. Use `isOn: .constant(false)` for action buttons, `isOn: $binding` for toggle buttons.

---

