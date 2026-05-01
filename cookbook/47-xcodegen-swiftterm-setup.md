# #47 — xcodegen + SwiftTerm Setup Gotchas

**Extracted from:** MyOwnTerminal (2026-04-21)

Four non-obvious issues that surface together when setting up an Xcode project with xcodegen that includes SwiftTerm.

---

## 1. Binary resources (fonts, TTFs) not auto-included

xcodegen silently ignores `.ttf` files listed in the `resources` section — they never appear in Copy Bundle Resources regardless of whether you use `path:`, `glob:`, or plain string syntax.

**Fix:** Use a `postBuildScripts` phase to copy them at build time, and declare `ATSApplicationFontsPath` in Info.plist properties so macOS auto-registers them on launch (no code needed).

```yaml
# project.yml
targets:
  MyApp:
    info:
      path: MyApp/Resources/Info.plist
      properties:
        ATSApplicationFontsPath: Fonts          # ← auto-registers all fonts in Resources/Fonts/
        UIDesignRequiresCompatibility: true     # ← see gotcha #2

    postBuildScripts:
      - name: Copy Hack Fonts
        script: |
          FONTS_SRC="${PROJECT_DIR}/MyApp/Resources/Fonts"
          FONTS_DST="${TARGET_BUILD_DIR}/${CONTENTS_FOLDER_PATH}/Resources/Fonts"
          mkdir -p "$FONTS_DST"
          cp "$FONTS_SRC"/*.ttf "$FONTS_DST/"
```

`ATSApplicationFontsPath` takes a path **relative to `Contents/Resources/`** in the bundle. Use `NSFont(name: "Hack-Regular", size: 13)` directly — no `CTFontManagerRegisterFontURLs` call needed.

---

## 2. `UIDesignRequiresCompatibility` must live in `info.properties`, not as a real file

xcodegen **rewrites** the Info.plist file it's pointed at. If you put `UIDesignRequiresCompatibility` in a hand-edited plist and point `info.path` at it, xcodegen will overwrite it and the key is silently dropped.

**Fix:** Put it in `info.properties` — xcodegen merges these into the generated plist:

```yaml
info:
  path: MyApp/Resources/Info.plist
  properties:
    UIDesignRequiresCompatibility: true
    NSPrincipalClass: NSApplication
    NSMainStoryboardFile: ""
```

**Verify:**
```bash
/usr/libexec/PlistBuddy -c "Print :UIDesignRequiresCompatibility" MyApp/Resources/Info.plist
# → true
```

---

## 3. `SwiftUI.Color` vs `SwiftTerm.Color` ambiguity

When a file imports both `SwiftUI` and `SwiftTerm`, the unqualified name `Color` is ambiguous. An `extension Color { init(hex:) ... }` will fail to compile with:

```
error: 'Color' is ambiguous for type lookup in this context
```

**Fix:** Qualify the extension explicitly:

```swift
extension SwiftUI.Color {
    init(hex: String) {
        // parse #RRGGBB
        let hex = hex.hasPrefix("#") ? String(hex.dropFirst()) : hex
        let scanner = Scanner(string: hex)
        var value: UInt64 = 0
        scanner.scanHexInt64(&value)
        let r = Double((value >> 16) & 0xff) / 255.0
        let g = Double((value >> 8)  & 0xff) / 255.0
        let b = Double(value         & 0xff) / 255.0
        self.init(red: r, green: g, blue: b)
    }
}
```

Call sites in files that only import `SwiftUI` continue to work unqualified as `Color(hex: "#...")`. Files that also import `SwiftTerm` need no changes since the extension target is now unambiguous.

For the SwiftTerm ANSI color palette, return `[SwiftTerm.Color]` explicitly and use the `* 257` scale factor (maps 8-bit 0–255 to 16-bit 0–65535 exactly):

```swift
SwiftTerm.Color(red: UInt16(r) * 257, green: UInt16(g) * 257, blue: UInt16(b) * 257)
```

---

## 4. Re-run xcodegen after adding new `.swift` files outside Xcode

xcodegen doesn't watch the filesystem. Files created outside Xcode (by an editor, a script, a subagent) won't appear in the `.pbxproj` until you re-run:

```bash
xcodegen generate
```

Symptoms when you forget: `Cannot find 'TypeName' in scope` compiler errors that look cross-file, even though the file exists on disk and looks fine. Always re-run xcodegen before building after adding files.

---

## 5. SourceKit false positives before first Xcode open

After `xcodegen generate`, SourceKit shows several false errors until the project is indexed by Xcode:

- `No such module 'SwiftTerm'` — on any file that imports the SPM package
- `'main' attribute cannot be used in a module that contains top-level code` — on `@main`
- `Cannot find 'ContentView' in scope` — cross-file type resolution

**All disappear** on first open in Xcode once indexing completes. `xcodebuild build` succeeds regardless — these are IDE-only artifacts.

---

## SwiftTerm API quick reference

```swift
// Wrap in NSViewRepresentable
let tv = LocalProcessTerminalView(frame: .zero)

tv.font = NSFont(name: "Hack-Regular", size: 13) ?? NSFont.monospacedSystemFont(ofSize: 13, weight: .regular)
tv.nativeBackgroundColor = NSColor(Theme.background)
tv.nativeForegroundColor = NSColor(Theme.foreground)
tv.installColors(Theme.ansiColors())   // [SwiftTerm.Color] — 16 ANSI colors
tv.optionAsMetaKey = true

tv.processDelegate = coordinator       // LocalProcessTerminalViewDelegate

tv.startProcess(executable: "/bin/zsh", args: ["-l"], environment: nil, currentDirectory: session.cwd)
```

**Delegate methods** (all on `LocalProcessTerminalViewDelegate`):
```swift
func sizeChanged(source: LocalProcessTerminalView, newCols: Int, newRows: Int) {}
func setTerminalTitle(source: LocalProcessTerminalView, title: String) { ... }
func hostCurrentDirectoryUpdate(source: TerminalView, directory: String?) { ... }  // OSC 7
func processTerminated(source: TerminalView, exitCode: Int32?) { ... }
```

Note: `caretStyle = .blinkVerticalBar` does **not exist** in SwiftTerm 1.x — omit it.
