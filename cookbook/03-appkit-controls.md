## Controls on macOS 26 — Custom SwiftUI styles, not AppKit wrappers

> **Rewritten 2026-05-26.** Earlier versions of this entry recommended `NSViewRepresentable`-wrapped AppKit controls to escape SwiftUI's default Tahoe chrome. **That advice was wrong.** Apple redesigned `NSButtonCell` drawing at the cell level on macOS 26, so AppKit wrappers do NOT escape Liquid Glass either. The correct escape is **custom SwiftUI styles**.

### The rule

Two surfaces draw control chrome on macOS 26:

|  | System paints (→ Tahoe pills) | You paint (→ your shape) |
|---|---|---|
| **SwiftUI** | `Button` / `Toggle` / etc. with a **built-in** style (`.automatic`, `.bordered`, `.borderedProminent`, `.plain`, `.link`, default segmented, default slider) | `Button` + custom `ButtonStyle.makeBody(...)`; `Toggle` + custom `ToggleStyle`; `Menu` + custom button label; `TextField(.plain)` + view modifiers; replace `Picker(.segmented)` with `HStack` of styled `Button`s |
| **AppKit** | `NSButton` / `NSSegmentedControl` / etc. with any built-in `bezelStyle`, **even when wrapped via `NSViewRepresentable`** | Custom `NSButtonCell` subclass overriding `draw(withFrame:in:)` |

Both technologies have an escape — SwiftUI's is one short struct (~20 lines), AppKit's is a Cell subclass + manual drawing (~100 lines per bezel). **Default to SwiftUI + custom styles.**

`UIDesignRequiresCompatibility = true` in `Info.plist` opts the *SwiftUI built-in styles* out of Liquid Glass on some bezels (notably `.helpButton`), but it does NOT roll back the `.push` / default-action capsule shape and does NOT affect AppKit cells at all. Keep the flag in `Info.plist` as belt-and-suspenders — it's free — but it's not the load-bearing piece.

### Per-control verdicts (macOS 26 spike, 2026-05-26)

| Control | Recommended path | Why |
|---|---|---|
| **Button** | SwiftUI `Button` + custom `ButtonStyle` | Default SwiftUI = wide pill capsule. AppKit wrapper = same wide capsule. Custom `ButtonStyle.makeBody` = your shape, full control. |
| **Toggle (checkbox)** | SwiftUI `.toggleStyle(.checkbox)` | macOS 26 default `.checkbox` style still renders as a classic small square. No custom needed. |
| **Toggle (switch)** | SwiftUI `.toggleStyle(.switch)` (acceptable Tahoe pill) — or custom `ToggleStyle` if classic chrome wanted | Default switch is Tahoe-redesigned but the new chrome is acceptable. |
| **Segmented** | `HStack` of styled `Button`s | Both SwiftUI `Picker.segmented` and `NSSegmentedControl` are Tahoe-redesigned. Compose from styled buttons instead. |
| **Slider** | SwiftUI `Slider` (default) | macOS 26 default slider is slim, accent-fill, classic-modern. Both SwiftUI and `NSSlider` render identically and acceptably. |
| **Popup / Menu** | SwiftUI `Menu` with styled-`Button` label | SwiftUI `Picker.menu` and AppKit `NSPopUpButton` both render Tahoe. `Menu` + custom button label gives full control. |
| **TextField** | SwiftUI `TextField(.plain)` + view modifiers | Default `TextField` chrome is acceptable on macOS 26; `.plain` + explicit background/stroke gives full control. |
| **`.helpButton`** | `NSButton(bezelStyle: .helpButton)` via `NSViewRepresentable` | The one bezel Apple kept classic in the Tahoe redesign. Niche escape. |

**Net: 0 of 8 controls require general-purpose `NSViewRepresentable` wrappers.** Only `.helpButton` and edge cases (NSSlider with tick marks etc.) reach for an AppKit bridge.

---

### `FCPButtonStyle` — the primary style; replaces every `Button`

**Source:** Penumbra's `ToolbarButtonStyles.swift` (App Shell Standard).

```swift
struct FCPButtonStyle: ButtonStyle {
    var isOn: Bool = false
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .padding(.horizontal, 10).padding(.vertical, 4)
            .foregroundColor(isOn ? .white : .primary)
            .background(isOn ? Color.accentColor
                              : Color(nsColor: .gray.withAlphaComponent(0.25)))
            .cornerRadius(4)
            .overlay(RoundedRectangle(cornerRadius: 4)
                       .stroke(Color.black.opacity(0.25), lineWidth: 1))
            .opacity(configuration.isPressed ? 0.6 : 1.0)
            .animation(.easeInOut(duration: 0.1), value: configuration.isPressed)
    }
}

// Usage
Button("Export") { handleExport() }.buttonStyle(FCPButtonStyle())
Button("OK")     { confirm() }
    .buttonStyle(FCPButtonStyle(isOn: true))
    .keyboardShortcut(.defaultAction)
```

The `isOn` parameter doubles for "this is the default/active button" — pass `true` and the button takes the accent color.

---

### Segmented from styled Buttons

```swift
struct FCPSegmented<T: Hashable>: View {
    let items: [(label: String, value: T)]
    @Binding var selection: T
    var body: some View {
        HStack(spacing: 0) {
            ForEach(items, id: \.value) { item in
                Button(item.label) { selection = item.value }
                    .buttonStyle(FCPButtonStyle(isOn: selection == item.value))
            }
        }
    }
}

// Usage
FCPSegmented(items: [("List", ViewMode.list), ("Grid", ViewMode.grid)],
             selection: $viewMode)
```

---

### `FCPCheckboxToggleStyle` — only if classic `.checkbox` isn't enough

```swift
struct FCPCheckboxToggleStyle: ToggleStyle {
    func makeBody(configuration: Configuration) -> some View {
        HStack(spacing: 6) {
            ZStack {
                RoundedRectangle(cornerRadius: 3)
                    .fill(configuration.isOn ? Color.accentColor
                                              : Color(nsColor: .gray.withAlphaComponent(0.25)))
                    .frame(width: 14, height: 14)
                    .overlay(RoundedRectangle(cornerRadius: 3)
                               .stroke(Color.black.opacity(0.3), lineWidth: 1))
                if configuration.isOn {
                    Image(systemName: "checkmark")
                        .font(.system(size: 9, weight: .bold))
                        .foregroundColor(.white)
                }
            }
            configuration.label
            Spacer(minLength: 0)
        }
        .contentShape(Rectangle())
        .onTapGesture { configuration.isOn.toggle() }
    }
}

// Default `.checkbox` style usually suffices on macOS 26:
Toggle("Show grid", isOn: $showGrid).toggleStyle(.checkbox)
```

---

### Popup / Menu

```swift
Menu {
    ForEach(formats, id: \.self) { f in Button(f) { selected = f } }
} label: {
    HStack {
        Text(selected); Spacer()
        Image(systemName: "chevron.up.chevron.down").font(.caption)
    }
    .frame(minWidth: 120)
}
.menuStyle(.borderlessButton)
.buttonStyle(FCPButtonStyle())
```

Explicit `HStack { Text; Spacer; Image }` in the label avoids `Menu`'s default chevron-on-left layout.

---

### TextField

```swift
TextField("Search…", text: $query)
    .textFieldStyle(.plain)
    .padding(.horizontal, 6).padding(.vertical, 4)
    .background(Color(nsColor: .textBackgroundColor))
    .cornerRadius(4)
    .overlay(RoundedRectangle(cornerRadius: 4)
               .stroke(Color.gray.opacity(0.4), lineWidth: 1))
```

---

### Slider

```swift
Slider(value: $opacity, in: 0...1)
```

macOS 26's default slider is acceptable — slim track, small accent-fill, classic thumb. No style override needed. Reach for `NSViewRepresentable<NSSlider>` only when you need a specific AppKit interaction (tick marks, custom hit-testing) that the SwiftUI Slider doesn't expose.

---

### `.helpButton` (niche AppKit escape)

The one bezel Apple kept classic in the Tahoe redesign. Used for the small circular "?" button in dialogs.

```swift
struct AppKitHelpButton: NSViewRepresentable {
    let action: () -> Void
    func makeNSView(context: Context) -> NSButton {
        let b = NSButton(title: "", target: context.coordinator,
                         action: #selector(Coordinator.clicked))
        b.bezelStyle = .helpButton
        return b
    }
    func updateNSView(_ nsView: NSButton, context: Context) {
        context.coordinator.action = action
    }
    func makeCoordinator() -> Coordinator { Coordinator(action: action) }
    @MainActor final class Coordinator: NSObject {
        var action: () -> Void
        init(action: @escaping () -> Void) { self.action = action }
        @objc func clicked() { action() }
    }
}
```

---

### Code organization

- Styles live in `Views/Styles/` — one file per style or per logical group. Reuse across the app.
- Don't inline custom styles per call site — that loses the single-source-of-truth benefit.
- The toolbar exception from earlier versions of this cookbook is gone — `FCPButtonStyle` IS the toolbar style; toolbar `Button`s just apply `.buttonStyle(FCPButtonStyle())`.

### What changed (historical context)

- **macOS 15 (Sonoma) and earlier:** AppKit `.rounded` / `.push` bezel = classic 4pt-corner rectangle. SwiftUI `.bordered` Button = same classic look. `NSViewRepresentable` wrappers were unnecessary but harmless.
- **macOS 26 (Tahoe / Liquid Glass):** both SwiftUI built-in styles AND AppKit `NSButtonCell` were redesigned to capsule/pill shapes. The earlier cookbook claim "AppKit `.push` gives ~4pt corners" became false. Custom drawing on either side is the only escape.
- **Per-view "compatibility" knobs that DO NOT roll back chrome on macOS 26** (don't bother): `UIDesignRequiresCompatibility = true` (helps some SwiftUI bezels but not `.push` or default-action), `NSView.prefersCompactControlSizeMetrics = true` (metrics only), `NSView.appearance = NSAppearance(named: .aqua)` (colors only, shape unchanged).

### Deprecated AppKit bezel cases on macOS 26

Only relevant if you DO reach for `NSViewRepresentable` (rare per above): `.rounded` → `.push`; `.regularSquare` → `.smallSquare`; `.recessed` → `.accessoryBar`; `.texturedSquare` → `.toolbar`; `.texturedRounded` → `.toolbar` or `.push`. New opt-IN case is `.glass` — don't pick by accident.
