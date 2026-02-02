# Pattern Cookbook

Manage the reusable code patterns cookbook.

**Location:** `/Users/sim/XcodeProjects/0-DIRECTIONS/__DIRECTIONS/PATTERNS-COOKBOOK.md`

## Commands

### `/cookbook` or `/cookbook update`

Full rescan of XcodeProjects to find new patterns.

**Process:**
1. Scan `/Users/sim/XcodeProjects` for Swift files containing:
   - Window layouts (HSplitView, NavigationSplitView, WindowGroup)
   - Export dialogs (NSSavePanel, NSOpenPanel)
   - File pickers (.fileImporter, drag-and-drop)
   - App lifecycle (@main, AppDelegate, scenePhase)
   - Service patterns (Manager, Coordinator, @Observable)

2. Compare against existing cookbook entries

3. For new patterns found, ask:
   > "Found new pattern in [Project]: [Description]. Add to cookbook?"

4. If yes, append to PATTERNS-COOKBOOK.md with:
   - Pattern name
   - Source file path
   - Code snippet (20-50 lines)
   - "Best for" description

5. Update Vestige memory with new patterns

---

### `/cookbook add`

Quick-add a pattern you just built.

**Process:**
1. Ask: "What pattern did you just build? (e.g., 'custom progress indicator', 'multi-window state sync')"

2. Ask: "Which file contains the working code?"

3. Read the file and extract the relevant code

4. Ask: "What's it best for? (one line)"

5. Append to PATTERNS-COOKBOOK.md under appropriate section:
   - Window Layouts
   - Export & File Dialogs
   - App Lifecycle & Initialization
   - **Other Patterns** (new section if needed)

6. Store in Vestige for automatic recall

7. Confirm: "Added [pattern name] to cookbook and Vestige."

---

### `/cookbook search <query>`

Search existing patterns.

**Process:**
1. Search Vestige for matching patterns
2. Read relevant sections from PATTERNS-COOKBOOK.md
3. Present matches with code snippets

---

## Pattern Categories

| Category | Keywords to Detect |
|----------|-------------------|
| Window Layouts | HSplitView, VSplitView, NavigationSplitView, WindowGroup, NSSplitView |
| Export & File Dialogs | NSSavePanel, NSOpenPanel, .fileImporter, .fileExporter |
| App Lifecycle | @main, AppDelegate, scenePhase, .task, .onAppear |
| State Management | @Observable, @StateObject, @EnvironmentObject, Manager |
| Concurrency | actor, async/await, Task, MainActor |
| Persistence | UserDefaults, bookmarkData, securityScoped |

---

## When to Add Patterns

Add a pattern when:
- You built something that took >30 min to figure out
- You copied code from another project
- You solved a SwiftUI/AppKit quirk
- You want to remember "how we did X in Project Y"

**Don't add:**
- One-off hacks
- Project-specific logic
- Obvious/trivial code
