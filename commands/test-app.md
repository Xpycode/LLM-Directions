# Test App — AppProbe UI Automation

Generate and run an automated UI test plan for a macOS app using AppProbe.

## Step 1: Identify the App

Ask: "Which app do you want to test?" if not provided as argument: $ARGUMENTS

Determine:
- **App name** (display name)
- **Bundle identifier** (from Info.plist or project settings)
- **Project path** (source code location)
- **Xcode scheme** (for building if needed)

If the user gives a project name, search `/Users/sim/XcodeProjects/1-macOS/` for it.

## Step 2: Build the App (if needed)

Check if the app is already running:
```bash
swift run --package-path /Users/sim/XcodeProjects/9-TESTING/AppProbe appprobe check
```

If the app isn't running, offer to build and launch it:
```bash
xcodebuild -scheme "SchemeName" -destination "platform=macOS" build
open /path/to/Build/Products/Debug/AppName.app
```

Wait for it to launch, then proceed.

## Step 3: Discover the UI

Run discovery to inspect the running app's accessibility tree:
```bash
swift run --package-path /Users/sim/XcodeProjects/9-TESTING/AppProbe appprobe discover <bundle-id> --output /tmp/appprobe-discovery.json
```

Read the discovery JSON to understand what UI elements exist: windows, buttons, menus, text fields, etc.

## Step 4: Read the Source Code

Read the app's key source files to understand:
- What the app does (purpose, features)
- All user-facing views and their interactions
- Menu items and keyboard shortcuts
- User workflows (what sequences of actions a user would perform)
- State changes (what should happen after each action)

Use Serena's symbolic tools or file reads to efficiently scan the codebase. Focus on:
- `*App.swift` — entry point, menu bar setup
- `*View.swift`, `*ContentView.swift` — UI views
- `*ViewModel.swift` — business logic
- `Commands.swift` or menu setup files — keyboard shortcuts
- Any `Settings`/`Preferences` views

## Step 5: Generate the Test Plan

Combine the discovery report + source code understanding to create a comprehensive YAML test plan.

**Test plan structure:**

```yaml
app: "AppName"
bundle_id: "com.example.appname"
settings:
  screenshot_on_every_step: false
  screenshot_on_failure: true
  default_timeout: 5.0
  delay_between_steps: 0.5
  output_dir: "./appprobe-results/AppName"
tests:
  # ... generated tests
```

**Test categories to cover (in this order):**

### 1. Smoke Tests (tag: smoke)
- App launches successfully
- Main window appears with expected title
- Menu bar is accessible
- Window can be resized

### 2. Menu Navigation (tag: menus)
- Each top-level menu can be opened
- Key menu items work (File > New, File > Open, Edit > Select All, etc.)
- Keyboard shortcuts trigger the right actions

### 3. Core Functionality (tag: core)
- Primary user workflow end-to-end
- Each interactive element (buttons, text fields, toggles) responds
- Data entry and modification
- State changes are visible (labels update, views change)

### 4. Window Management (tag: windows)
- Multiple windows (if supported)
- Window close and reopen
- Preferences/Settings window

### 5. Edge Cases (tag: edge)
- Empty states (no data loaded)
- Rapid clicking / repeated actions
- Keyboard navigation (Tab through elements)

### 6. Cleanup (tag: cleanup)
- Close all windows
- Terminate app

**Element query guidelines:**
- Prefer `identifier` if available (most stable)
- Use `role` + `title` for buttons and menu items
- Use `role` + `label` for elements with accessibility labels
- Use `titleContains` for dynamic titles
- Add `description` to each step explaining what it verifies

Save the test plan to: `/Users/sim/XcodeProjects/9-TESTING/AppProbe/plans/<app-name>.yaml`

## Step 6: Ask Before Running

Show the user:
- Number of tests and steps generated
- Summary of what will be tested
- The command that will run

Ask: "Ready to run? Options:"
1. **Run with overlay** (recommended): `--slow --overlay --verbose`
2. **Run fast**: `--verbose`
3. **Run specific tag**: `--tag smoke`
4. **Edit first**: Let me review/modify the plan

## Step 7: Execute

Run the chosen command:
```bash
swift run --package-path /Users/sim/XcodeProjects/9-TESTING/AppProbe appprobe run plans/<app-name>.yaml --slow --overlay --verbose --output ./appprobe-results/<app-name>
```

## Step 8: Review Results

After execution:

1. Read `appprobe-results/<app-name>/results.json`
2. Read any failure screenshots
3. Present a summary:
   - Total pass/fail/skip
   - Each failed test with the error and screenshot
   - Suggestions for what might be wrong (code bug vs. test plan issue)

If failures look like test plan issues (wrong element queries, timing), offer to fix the plan and re-run.
If failures look like app bugs, describe the bug and suggest a fix.

## Quick Usage

```
/test-app PointerActions
/test-app "Menu Bar Overflow Manager"
/test-app   (will ask which app)
```
