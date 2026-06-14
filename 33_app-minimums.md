<!--
TRIGGERS: minimums, baseline features, must have, essential features, app features, ship requirements
PHASE: building, shipping
LOAD: full
-->

# App Minimums Reference

*Baseline features every app should have. Compiled from patterns across 15+ shipped macOS/iOS apps.*

> **Two-part release flow:**
> 1. First run `/minimums` → Feature baselines (this file)
> 2. Then run `/review` → Code quality ([30_production-checklist.md](30_production-checklist.md))

---

## Quick Reference

Before shipping, check that your app has these baseline features:

```
DEPLOYMENT
├── [ ] Auto-update mechanism (Sparkle/App Store)
├── [ ] Version visible in UI (About window or Settings)
├── [ ] Notarized and code-signed (macOS)
└── [ ] App icon at all required sizes

INFRASTRUCTURE
├── [ ] Diagnostic logging (to ~/Library/Application Support/)
├── [ ] Preferences system (@AppStorage)
├── [ ] Error handling with user feedback
└── [ ] Progress feedback for async operations

UI POLISH
├── [ ] Empty states with clear CTAs
├── [ ] Loading states (not blank screens)
├── [ ] Error states with retry option
├── [ ] Keyboard shortcuts (and document them)
└── [ ] About window

APP CITIZENSHIP  (use the shared packages — don't rebuild per app)
├── [ ] Send Feedback + Support/Donate + About  → AppCitizenshipKit (one line)
├── [ ] In-app Help (Help menu + content)        → HelpMenu (appHELP), vendored
├── [ ] Editable shortcuts (if app has hotkeys)  → ShortcutKit
└── [ ] App icon at all sizes                     → cookbook #76 generator

PLATFORM-SPECIFIC
├── macOS: Menu bar (About, Preferences, Quit)
├── macOS: Window state restoration
├── iOS: Review prompt (at the right moment)
├── iOS: What's New on update
└── Web: Favicon, meta tags, 404 page
```

---

## Deployment & Distribution

### Auto-Update Mechanism

**Why:** Users won't manually check for updates. You'll ship bugs. You need a way to push fixes.

**macOS (Non-App Store):**
- Use Sparkle framework with EdDSA signing
- Host appcast.xml with update info
- Check on launch + periodically

> **⚠ Sandbox gotcha:** If App Sandbox is enabled (`ENABLE_APP_SANDBOX = YES` in build settings), you **must** add the `com.apple.security.network.client` entitlement — otherwise Sparkle silently fails because all outgoing HTTP is blocked. Xcode may enable sandbox by default even if your `.entitlements` file is empty. If unsandboxed, no entitlement needed. See [22_macos-platform.md](22_macos-platform.md#sandbox-considerations).

> **⚠ Versioning gotcha:** Sparkle compares `sparkle:version` (= `CFBundleVersion` / `CURRENT_PROJECT_VERSION`) **not** the marketing version. The marketing version (`sparkle:shortVersionString`) is display-only. Build numbers must be **monotonically increasing** across all releases — if v1.2 has build 3 and v1.3 has build 2, Sparkle thinks v1.2 is newer and offers a downgrade loop.

**Build number scheme** (encode version in digits: `major` `minor` `patch` `iteration`):

| Marketing version | Build range | Meaning |
|---|---|---|
| v1.0 | 1000–1009 | 1.0.0, up to 10 builds |
| v1.1 | 1100–1109 | 1.1.0 |
| v1.3 | 1300–1309 | 1.3.0 |
| v1.3.1 | 1310–1319 | patch release |
| v1.3.4 | 1340–1349 | patch release |
| v2.0 | 2000–2009 | major version bump |

Rules:
- `CURRENT_PROJECT_VERSION` = first number in the range (e.g. 1300 for v1.3)
- `sparkle:version` in appcast **must match** `CURRENT_PROJECT_VERSION` exactly
- Subsequent builds increment the last digit (1301, 1302…)
- Never reuse a build number across releases
- Capacity: 10 builds per patch, 10 patches per minor, 10 minors per major

**macOS (App Store):**
- System handles updates, but show "What's New" on first launch after update

**iOS:**
- System handles updates via App Store
- Show "What's New" screen on first launch after update
- Consider in-app prompt for critical updates

### Version Visibility

**Why:** Users need to tell you what version they're running when reporting bugs.

- Show in About window: `v1.2.3 (build 45)`
- Consider: Settings footer, menu bar tooltip
- Format: Marketing version + build number

### Code Signing & Notarization (macOS)

**Why:** Gatekeeper blocks unsigned apps. Users get scary warnings.

```bash
# Sign
codesign --force --sign "Developer ID Application: ..." --options runtime MyApp.app

# Notarize
xcrun notarytool submit MyApp.zip --apple-id ... --wait

# Staple
xcrun stapler staple MyApp.app
```

---

## Infrastructure

### Diagnostic Logging

**Why:** When users report issues, you need to see what happened. Crash logs aren't enough.

**Pattern:**
```swift
final class DiagnosticLogger {
    static let shared = DiagnosticLogger()
    private let logURL: URL

    init() {
        let appSupport = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask).first!
        let appFolder = appSupport.appendingPathComponent("YourApp")
        try? FileManager.default.createDirectory(at: appFolder, withIntermediateDirectories: true)
        logURL = appFolder.appendingPathComponent("diagnostic.log")
    }

    func log(_ message: String, state: [String: Any] = [:]) {
        let timestamp = ISO8601DateFormatter().string(from: Date())
        let stateStr = state.isEmpty ? "" : " | \(state)"
        let entry = "[\(timestamp)] \(message)\(stateStr)\n"
        // Append to file...
    }
}
```

**Key principle:** Log **state**, not just flow. Include `hasSelection: true, isEnabled: false` — not just "button tapped."

**Location:** `~/Library/Application Support/YourApp/diagnostic.log`

### Preferences System

**Why:** Users expect their settings to persist. Use @AppStorage backed by UserDefaults.

**Pattern:**
```swift
// Simple preferences
@AppStorage("showInDock") var showInDock = true
@AppStorage("checkUpdatesAutomatically") var checkUpdates = true

// Feature flags for migrations
@AppStorage("useNewWorkspace") var useNewWorkspace = false
```

**Advanced:** For per-entity settings (e.g., per-monitor, per-project), use JSON in App Support.

### Error Handling with User Feedback

**Why:** Silent failures frustrate users. They don't know if it worked or not.

**Pattern:**
```swift
do {
    try await performOperation()
    // Show success feedback
} catch is CancellationError {
    // Don't show anything — user cancelled
} catch {
    // Generic message for security
    showError("Operation failed. Please try again.")
    // Log full error for debugging
    DiagnosticLogger.shared.log("Operation failed", state: ["error": error.localizedDescription])
}
```

**Never expose:** File paths, internal state, stack traces to users.

### Progress Feedback

**Why:** Long operations need visual feedback or users think the app is frozen.

**Pattern:**
```swift
@MainActor
class ViewModel: ObservableObject {
    @Published var isProcessing = false
    @Published var progress: Double = 0
    @Published var statusMessage = ""

    func processFiles(_ files: [URL]) async {
        isProcessing = true
        defer { isProcessing = false }

        for (index, file) in files.enumerated() {
            progress = Double(index) / Double(files.count)
            statusMessage = "Processing \(file.lastPathComponent)..."
            await processFile(file)
        }
    }
}
```

---

## UI Polish

### Empty States

**Why:** Blank screens confuse users. Tell them what to do.

**Pattern:**
```
┌─────────────────────────────────────┐
│                                     │
│         📁 No files yet             │
│                                     │
│    Drag files here or click         │
│    [Import] to get started          │
│                                     │
└─────────────────────────────────────┘
```

**Include:** Icon/illustration, explanation, clear action button.

### Loading States

**Why:** Users need to know something is happening.

**Options:**
- Progress bar (determinate) — for known duration
- Spinner (indeterminate) — for unknown duration
- Skeleton UI — for content that will load
- Status text — "Loading 3 of 10..."

### Error States

**Why:** Users need to know what went wrong and what to do about it.

**Pattern:**
```
┌─────────────────────────────────────┐
│                                     │
│         ⚠️ Connection failed        │
│                                     │
│    Couldn't reach the server.       │
│    Check your internet and          │
│    [Try Again]                      │
│                                     │
└─────────────────────────────────────┘
```

**Include:** What happened, why (if known), action to resolve.

### Keyboard Shortcuts

**Why:** Power users expect them. macOS apps especially.

**Must-have for macOS:**
- ⌘Q — Quit
- ⌘, — Preferences
- ⌘W — Close window
- ⌘N — New (if applicable)
- ⌘O — Open (if applicable)
- ⌘S — Save (if applicable)

**Document them:**
- In Help menu → Keyboard Shortcuts
- In onboarding or tips
- In README

### About Window

**Why:** Standard expectation. Shows version, links to support.

**Include:**
- App icon
- App name
- Version (marketing + build)
- Copyright
- Links: Website, Support, Privacy Policy
- Acknowledgments/Credits (if applicable)

---

## App Citizenship (Shared Packages — Don't Rebuild)

**Why:** Feedback, Donate, About, and Help are identical across apps — they have nothing to do with
what an app *does*. A 2026-06-14 portfolio audit (30 macOS apps) found them wired ad-hoc or missing:
**Donate 0/30, Feedback 2/30, a custom About 1/30, real Help 3/30.** These all have drop-in packages.
Adopt the package; never hand-roll them again.

### Feedback + Donate + About → `AppCitizenshipKit`

One package, one line. Adds Help › Send Feedback, Help › Support <App>, and a link-rich About.

```swift
// Package: https://github.com/Xpycode/AppCitizenshipKit  (private, from: "0.1.0")
import AppCitizenshipKit

private let citizenship = CitizenshipConfig(
    appID: "myapp",              // lowercase slug — feedback allow-list AND donate ?app=
    appName: "MyApp",
    accent: .blue,
    websiteURL: URL(string: "https://apps.lucesumbrarum.com/myapp"),
    privacyURL: URL(string: "https://apps.lucesumbrarum.com/privacy"),
    logProvider: { DiagnosticLogger.shared.recentTail(maxLines: 80) }  // optional
)

var body: some Scene {
    WindowGroup { ContentView() }
        .commands { CitizenshipCommands(citizenship) }   // ← all three menu items
}
```

**Non-code steps (once per app):**
1. Pick a lowercase `appID` slug; use it for *both* feedback and donate.
2. **Feedback:** add the slug to `ALLOWED_APPS` in `feedback-submit.php` (server). Cookbook #49.
3. **Donate:** register the slug in `donate.html` so the page self-personalizes. Cookbook #100.

`AppCitizenshipKit` re-exports **FeedbackKit** (`Xpycode/FeedbackKit`, the underlying feedback engine),
so you don't add it separately. It does **not** wrap Help or shortcuts — those stay below.

### In-app Help → `HelpMenu` (appHELP)

Help is *not* in AppCitizenshipKit because it needs per-app content (`.md` files) and is **vendored**
(copied) into each app, not fetched. Engine lives at `1-macOS/appHELP`.

```swift
// project.yml:  packages: { HelpMenu: { path: HelpMenu } }   (vendor the source in)
import HelpMenu

private let helpContent = (try? HelpContent(manifest: "help-manifest", in: .main))
    ?? HelpContent(topics: [], windowTitle: "MyApp Help")
// in .commands:
HelpMenuCommands(content: helpContent, appName: "MyApp")
```
Ship a `help-manifest.json` + `help-*.md` in the app target. Reference apps: Conjoyn, Penumbra.

### Editable shortcuts → `ShortcutKit` (only if the app has hotkeys)

Local package at `1-macOS/zPackages` (local-path dep, no remote). `ShortcutRecorder(shortcut:title:)`
+ `ShortcutStore<Action>`. Reference app: ClipSmart. Hardcoded `.keyboardShortcut(...)` does **not**
count as user-editable.

### Updates → Sparkle (directly)

**Not** the `AppUpdater` app (that's a standalone MacUpdater-clone that scans *other* apps — not a
library). Self-update = Sparkle + EdDSA appcast. See [Auto-Update Mechanism](#auto-update-mechanism)
above. 6/30 apps had it wired; one (AvidMXFPeek) links Sparkle but never calls it — verify it's live.

> **Paid licensing ≠ donate.** `PaymentOptions` (`4-Other/`) is unbuilt *paid-licensing* design
> (Paddle, signed entitlements), a separate large project. Donations are just the `donate.html` link.

---

## Platform-Specific

### macOS Menu Bar

**Required menus:**
- **App menu:** About, Preferences (⌘,), Quit (⌘Q)
- **File menu:** (if file-based) New, Open, Save, Close
- **Edit menu:** Undo, Redo, Cut, Copy, Paste, Select All
- **Window menu:** Minimize, Zoom, standard window commands
- **Help menu:** Search, link to documentation

### macOS Window State Restoration

**Why:** Users expect windows to reopen where they left them.

```swift
// In your WindowGroup or NSWindow setup
.handlesExternalEvents(matching: Set(arrayLiteral: "*"))
// Or implement NSWindowRestoration
```

### macOS Dock Icon Behavior

**For menu bar apps:** Option to show/hide dock icon.

```swift
// Hide dock icon
NSApp.setActivationPolicy(.accessory)

// Show dock icon
NSApp.setActivationPolicy(.regular)
```

### iOS App Store Review Prompt

**Why:** Reviews help discovery. But timing matters — don't annoy users.

**When to prompt:**
- After a positive action (completed task, saved file)
- After N successful uses (not on first launch)
- Not during onboarding
- Not after an error

```swift
import StoreKit

// After positive moment
if let scene = UIApplication.shared.connectedScenes.first as? UIWindowScene {
    SKStoreReviewController.requestReview(in: scene)
}
```

### iOS What's New Screen

**Why:** Users don't read App Store changelogs. Show them in-app.

**Pattern:**
- Check stored version vs current version on launch
- If different, show What's New sheet
- Store new version after dismissal

### Website Essentials

- **Favicon:** favicon.ico + apple-touch-icon
- **Meta tags:** title, description, og:image
- **404 page:** Helpful, branded, links to home
- **Mobile responsive:** Test on actual phones
- **SSL/HTTPS:** Always

---

## Architecture Patterns (Your Defaults)

Based on your codebase patterns:

| Layer | Your Default | Why |
|-------|--------------|-----|
| **UI** | SwiftUI + occasional AppKit | AppKit for Canvas, NSWorkspace |
| **Concurrency** | async/await + actors | Not raw GCD |
| **State** | @Published + ObservableObject | @EnvironmentObject for sharing |
| **Persistence** | JSON + UserDefaults | No Core Data |
| **ViewModels** | @MainActor | Thread safety by design |
| **Services** | Actors | Thread safety by design |
| **Distribution** | Notarized DMG | Non-App Store for entitlements |
| **Updates** | Sparkle | EdDSA signed |

---

## Pre-Ship Minimums Checklist

Run through this before every release:

### Deployment
- [ ] Auto-update works (test the flow)
- [ ] Version shows correctly in About
- [ ] App is signed and notarized
- [ ] DMG/installer works on clean system

### Infrastructure
- [ ] Diagnostic log writes to correct location
- [ ] Preferences save and restore correctly
- [ ] Errors show user-friendly messages
- [ ] Progress shows for long operations

### UI Polish
- [ ] Empty states have clear CTAs
- [ ] Loading states show (not blank)
- [ ] Error states have retry option
- [ ] Keyboard shortcuts work
- [ ] About window has current version

### App Citizenship
- [ ] `AppCitizenshipKit` added → Send Feedback + Support/Donate + About all present
- [ ] Feedback slug allow-listed in `feedback-submit.php`; donate slug registered in `donate.html`
- [ ] Help menu has real content (HelpMenu + manifest), not the empty default
- [ ] App icon populated at all sizes (not a blank/generic icon)

### Platform
- [ ] macOS: Menu bar items work
- [ ] macOS: Window state restores
- [ ] iOS: Review prompt triggers appropriately
- [ ] iOS: What's New shows after update
- [ ] Web: Favicon, meta, 404 all present

---

## Common Oversights

Things you've forgotten before:

| Oversight | Consequence | Prevention |
|-----------|-------------|------------|
| No update mechanism | Users stuck on buggy versions | Sparkle from day 1 |
| No version in UI | Can't debug user reports | About window required |
| No diagnostic logging | Blind when users report issues | Add logger early |
| Silent errors | Users confused, retry blindly | Always show feedback |
| No empty states | Users think app is broken | Design from empty first |
| Hardcoded debug URLs | Ships with wrong endpoints | Use build config |
| Missing keyboard shortcuts | Power users frustrated | Standard shortcuts + docs |
| No Feedback / Donate / About | No user channel, no support income, looks unfinished | `AppCitizenshipKit` (one line) |
| Hand-rolled Help/feedback per app | Drift, wasted effort | Use the shared packages, not bespoke |
| Blank/generic app icon | Screams "unfinished" | Generate all sizes (cookbook #76) |

---

*Add items here as you discover new minimums. This list grows with experience.*
