---
name: shell-check
description: Audit a macOS app against the App Shell Standard (Penumbra pattern). Checks for UIDesignRequiresCompatibility, HSplitView, flat toolbar buttons, hidden title bar, dark-default appearance (user-switchable light), a Theme struct, split-view autosave, and toolbarRole(.editor). Reports violations and offers to fix them — preferring adoption of the AppShellKit package over copied code. Run on any macOS Xcode project.
---

# App Shell Standard Audit

Checks the current macOS app project against the mandatory App Shell Standard
defined in `PATTERNS-COOKBOOK.md` section 0 / `cookbook/00-app-shell.md`.

References:
- **Canonical shell chrome: the `AppShellKit` package** — `1-macOS/zPackages/Sources/AppShellKit/`
- Reference app (Approach A toolbar): `1-macOS/Penumbra/`
- Design tokens + appearance standard: `42_design-system.md`
- Full pattern + decision trees: `cookbook/00-app-shell.md`

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

Also locate the app's `Info.plist` (or the `INFOPLIST_KEY_*` build settings in
`project.pbxproj` / `project.yml`) — check 1 needs it.

### Step 2: Run These Checks

For each check, search the project's Swift source files. Report as PASS or FAIL.

| # | Check | Search Pattern | Pass Condition |
|---|-------|---------------|----------------|
| 1 | **`UIDesignRequiresCompatibility`** | `UIDesignRequiresCompatibility` in Info.plist | Present and `true`. **Nothing else in this standard works without it** — see context below |
| 2 | **Hidden title bar** | `.windowStyle(.hiddenTitleBar)` | Found in App struct |
| 3 | **Appearance: dark default, user-switchable** | `NSApplication.shared.appearance` / `.preferredColorScheme` | Dark on first launch + Light/Dark/Match-System picker via `NSApplication.shared.appearance` (cookbook #113 — not `.preferredColorScheme`, whose `nil` can't revert). Hardcoded `.preferredColorScheme(.dark)` only = **pass with note**: legacy forced-dark, light rollout pending (`42_design-system.md` §0). Forced dark as an explicit product decision also passes (`00-app-shell.md` §2.1, e.g. Penumbra) |
| 4 | **Editor toolbar role** | `.toolbarRole(.editor)` | Found on main content view |
| 5 | **No NavigationSplitView** | `NavigationSplitView` | NOT found on macOS targets |
| 6 | **Correct split-pane container** | `HSplitView` / `VSplitView` / `HStack(spacing: 0)` | Resizable panes → `HSplitView`/`VSplitView`; fixed sidebar → `HStack(spacing: 0)`. Per the decision tree in `00-app-shell.md` §5 — **either is a pass** |
| 7 | **Flat toolbar button style** | `FlatToolbarButtonStyle` / `FCPToolbarButtonStyle` | Found and used on toolbar buttons. Prefer the `AppShellKit` type over a local copy |
| 8 | **Theme struct** | `struct Theme` / `import AppShellKit` | Found. `AppShellKit.Theme` (five-token dark floor) = pass. A local **appearance-aware** Theme (asset-catalog "Any, Dark" sets or `NSColor(name:dynamicProvider:)`, hand-picked dark + light ramps) = pass. Dark-only hardcoded palette = **pass with note**: light ramp pending |
| 9 | **Split view autosave** | `autosaveSplitView` | Found on split-view instances |
| 10 | **Pane toggles via @AppStorage** | `@AppStorage.*show` | Pane visibility persisted |

Additionally report, as an **informational line rather than a check**: whether the app
imports `AppShellKit` or carries forked local copies of the shell types. Forks are the
drift this standard exists to kill — see Step 4.

**Check 1 context — the load-bearing flag.** Starting with Xcode 17 / macOS 26 SDK, Apple
forces pill/capsule system chrome on `NSToolbarItem`s. `UIDesignRequiresCompatibility = true`
in Info.plist opts the app out and lets a custom `ButtonStyle` render flat. Without it, no
amount of styling produces the house look. It is a **per-app Info.plist key — a package
cannot supply it**, so it must be verified per app.

> ⚠️ **Time-boxed.** Apple ignores `UIDesignRequiresCompatibility` at the **macOS 27 SDK**
> build, and there is no sanctioned flat-toolbar API under Liquid Glass (the HIG discourages
> custom bezels). The flat look is on a countdown; flag this when auditing an app that is
> about to move to SDK 27. *(Verified 2026-07-14 fleet audit.)*

**On titlebar injection.** Injecting an `NSHostingView` into `NSTitlebarView` via a
`WindowToolbarConfigurator` is **not** the house standard — `00-app-shell.md` lists it as
Approach B, "for edge cases only", and the migration checklist says explicitly *do NOT use
titlebar injection*. Removing real `.toolbar {}` items breaks content-area safe-area
calculation and blanks `GeometryReader` canvases. **Do not fail an app for lacking it**, and
treat its presence as a finding to review, not a pass. (Only AutoRedact uses it fleet-wide.)

### Step 3: Report Results

Present results as a checklist:

```
App Shell Standard Audit — [AppName]
═══════════════════════════════════════

[FAIL] UIDesignRequiresCompatibility — missing from Info.plist; toolbar will show system chrome
[PASS] Hidden title bar (.hiddenTitleBar)
[NOTE] Appearance — hardcoded .preferredColorScheme(.dark); legacy forced-dark, add light + picker (42_ §0)
[FAIL] Editor toolbar role — using .automatic, should be .toolbarRole(.editor)
[FAIL] NavigationSplitView found — should migrate per the §5 decision tree
[PASS] Split-pane container (HSplitView)
[FAIL] Flat toolbar button style — not found, toolbar uses default button styles
[FAIL] Theme struct — not found, uses hardcoded colors
[PASS] Split view autosave
[PASS] Pane toggles via @AppStorage

Shell source: local forks (3 files) — AppShellKit not adopted
Score: 4/10 — migration needed
```

### Step 4: Offer Migration

If any checks FAIL, offer to fix them:

> "[N] violations found. Want me to migrate this app to the App Shell Standard?
> I'll add the missing pieces one at a time so you can review each change."

Then fix in this order (each is independent, confirm after each):

1. **Add `UIDesignRequiresCompatibility = true` to Info.plist** — nothing else renders
   correctly without it, so this goes first.
2. **Add the `AppShellKit` package dependency** (`.package(path: "../zPackages")`, product
   `AppShellKit`) and `import AppShellKit`. This supplies `Theme`, `ThemeManager`,
   `FlatToolbarButtonStyle` (+ `FCPToolbarButtonStyle` alias), `PaneToggleButton`, and
   `autosaveSplitView` in one step — **prefer this over copying code**. If the app already
   has local forks of these types, delete them as part of this step.
3. Update App struct: `.windowStyle(.hiddenTitleBar)`; appearance = dark default +
   Light/Dark/Match-System picker via `NSApplication.shared.appearance` (#113), not hardcoded
   `.preferredColorScheme(.dark)`
4. Update main view: `.toolbarRole(.editor)`
5. Replace `NavigationSplitView` per the §5 decision tree — `HSplitView`/`VSplitView` for
   resizable panes, `HStack(spacing: 0)` for a fixed sidebar (this is the biggest change)
6. Add `.autosaveSplitView(named:)` to split views
7. Convert pane visibility to `@AppStorage` bools
8. Replace hardcoded colors with `Theme` tokens

**Do not** migrate toolbar buttons out of `.toolbar {}` into titlebar injection — that is
Approach B, reserved for edge cases where Approach A fails on the target SDK.

## Where the Shell Types Come From

`AppShellKit` is the canonical source. Add the package rather than copying files:

| Type | Provided by |
|------|-------------|
| `FlatToolbarButtonStyle` (+ `FCPToolbarButtonStyle` alias) | `AppShellKit` |
| `PaneToggleButton` | `AppShellKit` |
| `Theme` (5-token floor: primary/secondaryBackground, accent, primary/secondaryText) | `AppShellKit` |
| `ThemeManager` (persisted brand accent) | `AppShellKit` |
| `.autosaveSplitView(named:)` | `AppShellKit` |
| App struct pattern (reference only) | `1-macOS/Penumbra/01_Project/Penumbra/Penumbra/App/PenumbraApp.swift` |

Proven adopters to copy wiring from: **QuickScreenShot**, **Contour** (both wired 2026-07-14).

## Notes

- **AppShellKit shipped 2026-07-14** and replaces the old "copy these files from Penumbra"
  workflow. An app carrying local forks of the shell types should adopt the package instead
  of having its copies patched — the fork drift is what the package exists to kill.
- **`AppShellKit.Theme` is a dark-only five-token floor**, deliberately minimal. An app
  adopting it passes check 8 with the standing "light ramp pending" note. Apps needing more
  tokens extend it additively in the app target (`extension Theme`); apps needing a runtime
  token editor keep that app-side (see Penumbra's own `ThemeManager`).
- **Appearance standard changed 2026-07-18:** dark default + user-selectable light
  (`42_design-system.md` §0). Forced-dark apps pass with a note and migrate gradually — an app
  may also *keep* forced dark as an explicit product decision (`00-app-shell.md` §2.1).
- The split-pane migration is the most involved change. It requires restructuring the view
  hierarchy. Confirm with the user before starting.
- Some apps may intentionally use `NavigationSplitView` for iOS cross-platform, or because a
  native sidebar is genuinely the better control (Aloft's Settings). Flag it, don't force it —
  and never force it on iOS targets.
- Per-app colors (accent, ramps) come from the app's `DESIGN.md` brief (`42_design-system.md`
  §1). The Theme *structure* must stay the same.
- **Never remove real `.toolbar {}` items.** SwiftUI uses them for content-area safe-area
  calculation; removing them makes `GeometryReader` report wrong sizes and canvases render
  blank. *(Learned from CropBatch, 2026-04-05.)*
