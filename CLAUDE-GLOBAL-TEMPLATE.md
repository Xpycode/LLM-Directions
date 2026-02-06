# Global Claude Instructions (Template)

**Copy this to `~/.claude/CLAUDE.md` and customize paths.**

---

## Session Start: Auto-Detect and Resume

At the start of every session, **automatically run Project Detection (below)** to determine project state.

After detection:
- If Directions exists → show current status and ask what to work on
- If no Directions → offer to set it up, then show commands menu

**Available commands:**

| Command | What it does |
|---------|--------------|
| `/setup` | Re-run project detection, set up or migrate Directions |
| `/status` | Check current phase, focus, blockers, last session |
| `/log` | Create or update today's session log |
| `/decide` | Record an architectural/design decision |
| `/interview` | Run the full discovery interview |
| `/learned` | Add a term to your personal glossary |
| `/reorg` | Reorganize folder structure (numbered folders) |
| `/directions` | Show all available commands |
| `/phase` | Change project phase |
| `/context` | Show project context summary |
| `/handoff` | Generate handoff document for future sessions |
| `/blockers` | Log and track blockers |
| `/review` | Interactive production checklist |
| `/minimums` | Check baseline app features before shipping |
| `/new-feature` | Scaffold docs for new feature |
| `/execute` | Wave-based parallel execution with fresh contexts |
| `/update-directions` | Pull latest Directions from GitHub |
| `/code-review` | Quality checklist before commits |
| `/security-audit` | Comprehensive security audit (OWASP patterns) |
| `/tdd` | Test-driven development workflow |
| `/quality` | AI code quality audit (LOC, complexity, edge cases) |
| `/build-fix` | Xcode/Swift error resolution guide |
| `/cookbook` | Manage reusable code patterns cookbook |
| `/spec` | Create feature specification (mini-PRD) before implementation |
| `/plan` | Create implementation plan with task waves |
| `/checkpoint` | Create git tag checkpoints for safe rollback |
| `/next` | Get next steps based on current state |
| `/reflect` | Session reflection and lessons learned |
| `/example-map` | Example mapping for acceptance criteria |
| `/compound` | Extract reusable learnings from session |

---

## Pattern Cookbook (Auto-Trigger)

When implementing these UI patterns, **FIRST check** the cookbook at:
`[LOCAL_DIRECTIONS_PATH]/PATTERNS-COOKBOOK.md`

**Trigger keywords:**
- Window layouts (HSplitView, NavigationSplitView, 2-pane, 3-pane, sidebar)
- Export dialogs (NSSavePanel, NSOpenPanel, file picker)
- File import (drag-and-drop, .fileImporter, security-scoped bookmarks)
- App lifecycle (@main, AppDelegate, scenePhase, service initialization)

**Also search Vestige** for semantic matches - patterns are stored there too.

---

## Project Detection (Run automatically on session start)

Check the project state and act accordingly:

### Step 1: Check for Directions

```
Does docs/00_base.md exist?
```

**YES → Directions is set up.** Follow "Existing Projects with Directions" below.

**NO → Continue to Step 2.**

---

### Step 2: Check for Existing Docs

```
Is there a /docs folder OR scattered .md files in the project?
```

**YES → Existing documentation found.**

Offer two options:
> "Found existing documentation. How should I proceed?
> 1. **Migrate** (recommended) - Back up to /old-docs, set up Directions in /docs, extract useful info
> 2. **Skip** - Don't set up Directions, just work with what's here"

If they choose Migrate:
- Create git commit: "Pre-Directions backup"
- Move existing /docs (or scattered .md files except README.md) to `/old-docs`
- Set up Directions in `/docs`
- Read `/old-docs` to extract: project purpose, decisions, architecture hints
- Populate PROJECT_STATE.md and decisions.md from what was found
- Run gap interview for missing info

**NO → Continue to Step 3.**

---

### Step 3: New Project

No docs, no MDs, minimal files.

> "This looks like a new project. What are you building? (One sentence is fine - I'll ask follow-up questions.)"

Then:
> "Want me to set up the Directions documentation system?"

If yes, set up Directions by **executing this command** (do not create files manually):

```bash
# Primary: Copy from local master (includes all reference guides)
mkdir -p docs && cp -r /path/to/LLM-Directions/* ./docs/

# Fallback if local not available: Clone from GitHub
# git clone https://github.com/Xpycode/LLM-Directions.git docs
```

**Important:** Always copy ALL files from the source. Do not manually create a subset of files.

Then read `docs/00_base.md` and run the full discovery interview.

After the interview, create a `CLAUDE.md` in the project root with:
- Project name and description
- Tech stack decided
- Key architecture decisions
- Pointer to `docs/00_base.md`

Then show the **Setup Complete** message:
> "✓ **Setup complete!** Your project is ready.
>
> **Quick start:**
> - `/status` - See current focus
> - `/log` - Start your first session log
> - Or just tell me what you want to build!"

---

## Existing Projects with Directions

If `docs/00_base.md` exists:

1. Read `docs/PROJECT_STATE.md` for current phase/focus/blockers
2. Show: "Phase: [X] | Focus: [Y] | Last session: [date]"
3. Ask: "Continue with [current focus], or work on something else?"

Only read additional files (session logs, decisions.md) if specifically needed for the task.

---

## Migration: Reading Existing Docs

When migrating from existing docs, look for:

| Look For | Extract To |
|----------|------------|
| Project description, goals | PROJECT_STATE.md |
| Technical decisions, "we chose X" | decisions.md |
| Architecture notes, patterns | CLAUDE.md tech stack section |
| TODOs, plans, phases | PROJECT_STATE.md current focus |
| Bug notes, issues found | Session log or debugging notes |
| API docs, specs | Keep in /old-docs for reference |

After extraction, run a **gap interview**:
> "I've read your existing docs. Here's what I found: [summary].
> I still need to understand: [list gaps].
> Can we fill these in?"

---

## General Preferences

### Git Discipline
- Never commit directly to main
- Create feature branches: `feature/`, `fix/`, `experiment/`
- Commit messages: what + why
- Remind me about branching before implementation

### Communication Style
- Be direct, skip unnecessary preamble
- Ask clarifying questions when unsure
- Offer relevant docs from Directions when keywords match triggers
- Remind me about terminology references when I'm searching for words

### Quality
- Test the actual user flow, not just "build succeeded"
- Log decisions to `docs/decisions.md` when architectural choices are made
- Update session logs after significant progress

### UI Changes
When adding UI elements (views, controls, toggles, buttons, menus):
1. **Find similar first** — Locate an existing comparable control
2. **Trace wiring** — Show where it's defined, how state flows
3. **Propose location** — State exact file/line for new element
4. **Wait for confirmation** — Do not implement until approved

See `docs/55_ui-changes-protocol.md` for full protocol and examples.

### Xcode Build Behavior
Before building any app, ALWAYS do a clean build cycle:

1. **Kill the running app** (if any)
   ```bash
   # macOS app
   killall "AppName" 2>/dev/null || true

   # iOS Simulator
   xcrun simctl terminate booted <bundle-id> 2>/dev/null || true
   ```

2. **Clean the build folder**
   ```bash
   xcodebuild clean -scheme "SchemeName" -destination "..."
   # Or: rm -rf ~/Library/Developer/Xcode/DerivedData/ProjectName-*
   ```

3. **Build the app**
   ```bash
   xcodebuild -scheme "SchemeName" -destination "..." build
   ```

4. **Launch the app**
   ```bash
   # macOS
   open /path/to/Build/Products/Debug/AppName.app

   # iOS Simulator
   xcrun simctl install booted /path/to/app
   xcrun simctl launch booted <bundle-id>
   ```

This ensures a fresh state every time - no stale caches or zombie processes.

---

## Directions Location

Customize these paths for your setup:

- **GitHub:** https://github.com/Xpycode/LLM-Directions
- **Local master:** /path/to/your/LLM-Directions

---

*Copy to ~/.claude/CLAUDE.md and customize paths.*
