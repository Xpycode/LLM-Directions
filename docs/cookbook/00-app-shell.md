## App Shell Standard

**Source:** `1-macOS/Penumbra/` (reference implementation)

The standard app shell for all macOS apps. Avoids macOS Tahoe's round capsule buttons, frosted sidebars, and default system chrome. Every new app starts with this. Every existing app migrates to this.

---

### 1. App Entry Point

```swift
@main
struct MyApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
                .frame(minWidth: 900, minHeight: 600)
                .preferredColorScheme(.dark)
        }
        .windowStyle(.hiddenTitleBar)     // no system title bar
        .commands {
            SidebarCommands()             // keep ⌘⇧S for sidebar toggle
        }

        Settings {
            SettingsView()
        }
    }
}
```

**Key decisions:**
- `.windowStyle(.hiddenTitleBar)` — removes the standard title bar chrome
- `.preferredColorScheme(.dark)` — forced dark mode, consistent across system settings
- No `.navigationTitle()` — title bar is hidden, so titles go in custom info strips or toolbars

---

### 2. Theme Struct

Centralized dark color palette. Use `Theme.xxx` everywhere instead of hardcoded colors.

```swift
import SwiftUI

@Observable
class ThemeManager {
    static let shared = ThemeManager()

    var accentColor: Color {
        didSet { saveColor(accentColor, forKey: "accentColor") }
    }

    private init() {
        self.accentColor = Self.loadColor(forKey: "accentColor")
            ?? Color(red: 0.9, green: 0.5, blue: 0.2)  // brand orange
    }

    private func saveColor(_ color: Color, forKey key: String) {
        let nsColor = NSColor(color)
        if let data = try? NSKeyedArchiver.archivedData(
            withRootObject: nsColor, requiringSecureCoding: false
        ) {
            UserDefaults.standard.set(data, forKey: key)
        }
    }

    private static func loadColor(forKey key: String) -> Color? {
        guard let data = UserDefaults.standard.data(forKey: key),
              let nsColor = try? NSKeyedUnarchiver.unarchivedObject(
                  ofClass: NSColor.self, from: data
              ) else { return nil }
        return Color(nsColor: nsColor)
    }
}

struct Theme {
    static var primaryBackground: Color { Color(white: 0.10) }
    static var secondaryBackground: Color { Color(white: 0.15) }
    static var accent: Color { ThemeManager.shared.accentColor }
    static var primaryText: Color { .white }
    static var secondaryText: Color { .white.opacity(0.65) }
}
```

**Usage:** `Theme.primaryBackground`, `Theme.accent`, `Theme.secondaryText` — never `Color.gray` or `.secondary` for backgrounds.

---

### 3. FCPToolbarButtonStyle (Flat Toolbar Buttons)

Replaces macOS default round/capsule toolbar buttons with flat, 4px-corner-radius buttons inspired by Final Cut Pro.

```swift
struct FCPToolbarButtonStyle: ButtonStyle {
    @Binding var isOn: Bool

    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .padding(.horizontal, 8)
            .padding(.vertical, 6)
            .foregroundColor(isOn ? .white : .primary)
            .background(
                ZStack {
                    if isOn {
                        Theme.accent
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
            .animation(.spring(response: 0.3, dampingFraction: 0.5), value: isOn)
    }
}
```

For toolbar toggle buttons, wrap in a reusable view:

```swift
struct PaneToggleButton: View {
    @Binding var isOn: Bool
    let iconName: String
    let help: String

    var body: some View {
        Button(action: { withAnimation { isOn.toggle() } }) {
            Image(systemName: iconName)
                .resizable()
                .aspectRatio(contentMode: .fit)
                .frame(width: 16, height: 16)
        }
        .help(help)
        .buttonStyle(FCPToolbarButtonStyle(isOn: $isOn))
    }
}
```

**For non-toggle toolbar buttons**, pass `.constant(false)`:
```swift
Button(action: importFiles) {
    Image(systemName: "plus")
        .resizable().aspectRatio(contentMode: .fit)
        .frame(width: 16, height: 16)
}
.buttonStyle(FCPToolbarButtonStyle(isOn: .constant(false)))
```

---

### 4. Toolbar Configuration — Titlebar Injection (macOS 26 SDK)

> **Why not `.toolbar {}`?** Starting with Xcode 17 / macOS 26 SDK, Apple forces
> pill/capsule system chrome on ALL `NSToolbarItem`s — regardless of custom `ButtonStyle`,
> `.borderless`, or any SwiftUI modifier. The old `.toolbar {}` approach (still shown in
> older Penumbra builds) only works when linked against the macOS 15 SDK or earlier.
>
> **The fix:** Bypass `NSToolbar` entirely. Inject an `NSHostingView` directly into the
> titlebar's NSView hierarchy. Buttons render as regular SwiftUI views — no
> `NSToolbarItem` wrapping, no system bezel.

#### Step 1: WindowToolbarConfigurator (NSViewRepresentable)

Finds the titlebar view via the traffic light buttons and injects our custom toolbar content.

```swift
struct WindowToolbarConfigurator: NSViewRepresentable {
    static let viewID = NSUserInterfaceItemIdentifier("AppToolbarContent")

    func makeNSView(context: Context) -> NSView {
        let view = NSView(frame: .zero)
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.2) {
            Self.injectToolbar(from: view)
        }
        return view
    }

    func updateNSView(_ nsView: NSView, context: Context) {}

    private static func injectToolbar(from view: NSView) {
        guard let window = view.window else { return }

        // closeButton → NSWindowButtonsView → NSTitlebarView
        guard let closeButton = window.standardWindowButton(.closeButton),
              let titlebarView = closeButton.superview?.superview else { return }

        // Don't inject twice
        if titlebarView.subviews.contains(where: { $0.identifier == viewID }) { return }

        let content = TitlebarToolbarContent()    // your SwiftUI toolbar view
            .preferredColorScheme(.dark)
        let hostingView = NSHostingView(rootView: content)
        hostingView.translatesAutoresizingMaskIntoConstraints = false
        hostingView.identifier = viewID

        titlebarView.addSubview(hostingView)

        NSLayoutConstraint.activate([
            hostingView.leadingAnchor.constraint(
                equalTo: titlebarView.leadingAnchor, constant: 78),  // clear traffic lights
            hostingView.trailingAnchor.constraint(
                equalTo: titlebarView.trailingAnchor, constant: -8),
            hostingView.centerYAnchor.constraint(
                equalTo: titlebarView.centerYAnchor),
            hostingView.heightAnchor.constraint(equalToConstant: 30)
        ])
    }
}
```

#### Step 2: TitlebarToolbarContent (SwiftUI view)

A regular SwiftUI view — uses `FCPToolbarButtonStyle`, `@AppStorage` for toggle state.
Because it lives in an `NSHostingView` (not an `NSToolbarItem`), no system chrome is applied.

```swift
struct TitlebarToolbarContent: View {
    @AppStorage("showSidebarView") private var showSidebar = true
    @AppStorage("showInspectorView") private var showInspector = true

    var body: some View {
        HStack(spacing: 8) {
            // Left — primary actions
            Button(action: importFiles) {
                Image(systemName: "plus")
                    .resizable().aspectRatio(contentMode: .fit)
                    .frame(width: 14, height: 14)
            }
            .buttonStyle(FCPToolbarButtonStyle(isOn: .constant(false)))

            Spacer()

            // Right — pane toggles
            HStack(spacing: 4) {
                PaneToggleButton(isOn: $showSidebar, iconName: "sidebar.leading", help: "Sidebar")
                PaneToggleButton(isOn: $showInspector, iconName: "sidebar.trailing", help: "Inspector")
            }
        }
        .padding(.horizontal, 4)
    }
}
```

#### Step 3: Wire it up

```swift
// In your content view:
HSplitView { /* ... panes ... */ }
    .background(WindowToolbarConfigurator())   // inject custom toolbar
    .toolbar {}                                // empty — keeps titlebar height
    .toolbarRole(.editor)                      // editor-style layout

// In your App struct (unchanged):
WindowGroup { ContentView() /* ... */ }
    .windowStyle(.hiddenTitleBar)
```

#### How it works

| Layer | What | Chrome? |
|-------|-------|---------|
| `NSToolbar` (SwiftUI `.toolbar {}`) | Empty — exists only for titlebar height | N/A (no items) |
| `NSTitlebarView` | macOS titlebar container with traffic lights | System-managed |
| Our `NSHostingView` | Injected as subview of `NSTitlebarView` | **None** — regular SwiftUI |
| `FCPToolbarButtonStyle` | Renders flat 4px buttons | Exactly as designed |

#### Alternatives considered

| Approach | Result |
|----------|--------|
| `.toolbar {}` + `FCPToolbarButtonStyle` | System forces pill/capsule bezel on macOS 26 SDK |
| `.buttonStyle(.borderless)` wrapper | Suppressed chrome for `.primaryAction` only, not `.navigation` |
| `ToolbarChromeStripper` (walk NSView tree, set `isBordered = false`) | SwiftUI uses hosting views, not raw NSButtons — didn't reach the right layer |
| `NSTitlebarAccessoryViewController` with `.bottom` | Works but adds a **separate row** below traffic lights |
| **Direct titlebar injection** (this pattern) | Buttons on **same row** as traffic lights, zero chrome |

**Key:** `.toolbarRole(.editor)` on the content view still matters — it prevents back/forward navigation chrome and sets the correct titlebar height.

---

### 5. Pane Layout with HSplitView

```swift
var body: some View {
    VStack(spacing: 0) {
        // Optional: Info strip at top
        InfoStripView()
            .frame(height: 25)

        // Main content area
        HSplitView {
            if showSidebar {
                SidebarView()
                    .frame(minWidth: 220, idealWidth: 300, maxWidth: 500)
            }
            MainContentView()
                .frame(minWidth: 500)
            if showInspector {
                InspectorView()
                    .frame(minWidth: 220, idealWidth: 300, maxWidth: 500)
            }
        }
        .layoutPriority(1)
        .autosaveSplitView(named: "MainSplitView")

        // Optional: Bottom bar
        BottomBarView()
            .frame(height: 40)
    }
    .toolbar { /* ... */ }
    .toolbarRole(.editor)
}
```

**Pane visibility** is driven by `@AppStorage` bools toggled from the toolbar:
```swift
@AppStorage("showSidebar") private var showSidebar: Bool = true
@AppStorage("showInspector") private var showInspector: Bool = true
```

---

### 6. Button Style Guide (Non-Toolbar)

| Context | Style | Example |
|---------|-------|---------|
| Transport controls (play, pause, step) | `.buttonStyle(.plain)` | Icon-only, no background |
| Inline text actions (skip, dismiss) | `.buttonStyle(.borderless)` | Text link appearance |
| Secondary actions (Mark IN, Mark OUT) | `.buttonStyle(.bordered)` | Subtle bordered in dark mode |
| Primary CTA (Export, Submit) | `.borderedProminent` + `.tint(Theme.accent)` | Accent-colored, prominent |

---

### 7. Info Strip (Optional Top Bar)

Thin bar below the toolbar showing contextual info (file name, metadata, progress).

```swift
struct InfoStripView: View {
    var body: some View {
        HStack {
            Text("Current file info")
                .font(.caption)
            Spacer()
            Text("metadata")
                .font(.caption)
                .foregroundColor(.secondary)
        }
        .padding(.horizontal)
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .leading)
        .background(Color(nsColor: .windowBackgroundColor))
        .overlay(
            Rectangle().frame(height: 1)
                .foregroundColor(Color(nsColor: .separatorColor)),
            alignment: .bottom
        )
    }
}
```

---

### Migration Checklist

When migrating an existing app to the App Shell Standard:

- [ ] Replace `NavigationSplitView` with `HSplitView`
- [ ] Add `.windowStyle(.hiddenTitleBar)` to the `WindowGroup` scene
- [ ] Add `.preferredColorScheme(.dark)`
- [ ] Add `.toolbarRole(.editor)` to the main view
- [ ] Replace `.toolbar {}` buttons with titlebar injection (`WindowToolbarConfigurator` + `TitlebarToolbarContent`)
- [ ] Keep empty `.toolbar {}` + `.toolbarRole(.editor)` for titlebar height
- [ ] Add `Theme` struct, replace hardcoded colors
- [ ] Add `.autosaveSplitView(named:)` to split views
- [ ] Convert pane visibility to `@AppStorage` bools toggled from toolbar
- [ ] Remove any `NavigationTitle` calls (title bar is hidden)
- [ ] Verify: no round/capsule buttons remain in the toolbar

---

