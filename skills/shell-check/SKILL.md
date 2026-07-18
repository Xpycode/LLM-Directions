---
name: shell-check
description: Audit a macOS app against the App Shell Standard (Penumbra pattern). Checks for HSplitView, FCPToolbarButtonStyle, hidden title bar, dark-default appearance (user-switchable light), appearance-aware Theme struct, titlebar injection, and toolbarRole(.editor). Reports violations and offers to fix them. Run on any macOS Xcode project.
---

# App Shell Standard Audit

Checks the current macOS app project against the mandatory App Shell Standard
defined in `PATTERNS-COOKBOOK.md` section 0.

References:
- Pre-Tahoe SDK toolbar: `1-macOS/Penumbra/`
- macOS 26 SDK titlebar injection: `1-macOS/VAM/`
- Design tokens + appearance standard: `42_design-system.md`

## When to Use

- Starting work on an existing macOS app
- Before adding new features to an app that might not follow the standard
- After `/setup` on a macOS project
- Manually via `/shell-check`

## Audit Procedure

### Step 1: Find the App Entry Point

Search for `@main` in Swift files to locate the app struct.

```
Grep: pattern="@main" type="swift"
```

### Step 2: Run These Checks

For each check, search the project's Swift source files. Report as PASS or FAIL.

| # | Check | Search Pattern | Pass Condition |
|---|-------|---------------|----------------|
| 1 | **Hidden title bar** | `.windowStyle(.hiddenTitleBar)` | Found in App struct |
| 2 | **Appearance: dark default, user-switchable** | `NSApplication.shared.appearance` / `.preferredColorScheme` | Dark on first launch + Light/Dark/Match-System picker via `NSApplication.shared.appearance` (cookbook #113 — not `.preferredColorScheme`, whose `nil` can't revert). Hardcoded `.preferredColorScheme(.dark)` only = **pass with note**: legacy forced-dark, light rollout pending (`42_design-system.md` §0) |
| 3 | **Editor toolbar role** | `.toolbarRole(.editor)` | Found on main content view |
| 4 | **No NavigationSplitView** | `NavigationSplitView` | NOT found (use HSplitView instead) |
| 5 | **Uses HSplitView** | `HSplitView` | Found for pane layouts |
| 6 | **FCPToolbarButtonStyle** | `FCPToolbarButtonStyle` | Found and used on toolbar buttons |
| 7 | **Theme struct** | `struct Theme` | Found, **appearance-aware**: tokens backed by asset-catalog "Any, Dark" color sets or `NSColor(name:dynamicProvider:)`, hand-picked dark + light ramps (`42_design-system.md` §0/§2). Dark-only hardcoded palette = **pass with note**: light ramp pending |
| 8 | **Split view autosave** | `autosaveSplitView` | Found on HSplitView instances |
| 9 | **Pane toggles via @AppStorage** | `@AppStorage.*show` | Pane visibility persisted |
| 10 | **Titlebar injection** | `WindowToolbarConfigurator` | Found — toolbar buttons injected into NSTitlebarView via NSHostingView, bypassing NSToolbar chrome |

**Check 10 context:** Starting with Xcode 17 / macOS 26 SDK, Apple forces pill/capsule
system chrome on all `NSToolbarItem`s. Placing buttons inside SwiftUI `.toolbar {}`
results in system bezel regardless of custom `ButtonStyle`. The fix is to inject an
`NSHostingView` directly into the `NSTitlebarView` via `WindowToolbarConfigurator`.
If the app was built with an older SDK and buttons in `.toolbar {}` look correct,
check 10 can pass with a note that it will need migration on SDK upgrade.

### Step 3: Report Results

Present results as a checklist:

```
App Shell Standard Audit — [AppName]
═══════════════════════════════════════

[PASS] Hidden title bar (.hiddenTitleBar)
[NOTE] Appearance — hardcoded .preferredColorScheme(.dark); legacy forced-dark, add light + picker (42_ §0)
[FAIL] Editor toolbar role — using .automatic, should be .toolbarRole(.editor)
[FAIL] NavigationSplitView found — should migrate to HSplitView
[PASS] HSplitView used
[FAIL] FCPToolbarButtonStyle — not found, toolbar uses default button styles
[FAIL] Theme struct — not found, uses hardcoded colors
[PASS] Split view autosave
[PASS] Pane toggles via @AppStorage
[FAIL] Titlebar injection — buttons in .toolbar {} will show system chrome on macOS 26 SDK

Score: 4/10 — migration needed
```

### Step 4: Offer Migration

If any checks FAIL, offer to fix them:

> "[N] violations found. Want me to migrate this app to the App Shell Standard?
> I'll add the missing pieces one at a time so you can review each change."

Then fix in this order (each is independent, confirm after each):

1. Add `Theme` struct (foundation — other fixes depend on it; appearance-aware per `42_design-system.md`)
2. Add `FCPToolbarButtonStyle` + `PaneToggleButton`
3. Update App struct: `.windowStyle(.hiddenTitleBar)`; appearance = dark default + Light/Dark/Match-System picker via `NSApplication.shared.appearance` (#113), not hardcoded `.preferredColorScheme(.dark)`
4. Update main view: `.toolbarRole(.editor)`
5. Replace `NavigationSplitView` with `HSplitView` (if applicable — this is the biggest change)
6. Add `.autosaveSplitView(named:)` to HSplitViews
7. Convert pane visibility to `@AppStorage` bools
8. Add `WindowToolbarConfigurator` + `TitlebarToolbarContent` — move toolbar buttons out of `.toolbar {}` into titlebar injection

## Reference Files to Copy From

When adding missing pieces, copy from the reference implementations:

| File | Source |
|------|--------|
| `FCPToolbarButtonStyle` | `1-macOS/Penumbra/01_Project/Penumbra/Penumbra/Views/ToolbarButtonStyles.swift` |
| `Theme` / `ThemeManager` | `1-macOS/Penumbra/01_Project/Penumbra/Penumbra/Utils/ThemeManager.swift` |
| `SplitViewAutosaveHelper` | `1-macOS/Penumbra/01_Project/Penumbra/Penumbra/Utils/View+SplitViewAutosave.swift` |
| App struct pattern | `1-macOS/Penumbra/01_Project/Penumbra/Penumbra/App/PenumbraApp.swift` |
| `WindowToolbarConfigurator` | `1-macOS/VAM/01_Project/VAM/App/VAMApp.swift` |
| `TitlebarToolbarContent` | `1-macOS/VAM/01_Project/VAM/App/VAMApp.swift` |

## Notes

- **Appearance standard changed 2026-07-18:** dark default + user-selectable light
  (`42_design-system.md` §0). Forced-dark apps pass with a note and migrate gradually — an app may
  also *keep* forced dark as an explicit product decision (`00-app-shell.md` §2.1, e.g. Penumbra).
- The `NavigationSplitView → HSplitView` migration is the most involved change. It requires restructuring the view hierarchy. Confirm with the user before starting.
- Some apps may intentionally use `NavigationSplitView` for iOS cross-platform. Flag this but don't force the change on iOS targets.
- Per-app colors (accent, ramps) come from the app's `DESIGN.md` brief (`42_design-system.md` §1). The Theme *structure* must stay the same.
- **Titlebar injection** relies on `closeButton.superview.superview` to find `NSTitlebarView`. This is an internal view hierarchy that could change with macOS updates. It's a common pattern used by many pro apps but should be tested after major OS releases.
- Apps built with pre-macOS 26 SDK can use `.toolbar {}` with `FCPToolbarButtonStyle` and pass check 10 with a note. Migration to titlebar injection is required when upgrading to Xcode 17+ / macOS 26 SDK.
