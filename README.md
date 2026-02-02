# Directions

[![GitHub stars](https://img.shields.io/github/stars/Xpycode/LLM-Directions)](https://github.com/Xpycode/LLM-Directions/stargazers)
[![GitHub last commit](https://img.shields.io/github/last-commit/Xpycode/LLM-Directions)](https://github.com/Xpycode/LLM-Directions/commits/main)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

**A systematic approach to AI-assisted software development.**

For people who direct AI to build software but don't code themselves.

---

## What This Is

Directions is a documentation and workflow system that helps you:

1. **Define clearly** - Multi-phase discovery creates specs with acceptance criteria
2. **Plan atomically** - Break work into <30 min tasks with validation
3. **Build with fresh context** - Wave-based execution prevents context degradation
4. **Validate rigorously** - Backpressure and multi-perspective review
5. **Compound learnings** - Extract patterns so you never solve the same problem twice

---

## The Funnel

Every feature flows through three phases:

```
DEFINE ──gate──> PLAN ──gate──> BUILD
   │                │              │
   ▼                ▼              ▼
  Spec        Task List      Working Code
```

**Principle:** 80% on Define + Plan, 20% on Build.

---

## Quick Start

### For New Projects

1. Copy this folder to your project as `/docs`
2. Add to your `CLAUDE.md`:
   ```markdown
   ## Context
   Read docs/00_base.md at the start of every session.
   Check docs/PROJECT_STATE.md for current focus.
   ```
3. Start a Claude session - run `/interview` to create your first spec
4. Run `/plan` to break into tasks, `/execute` to build

### Core Workflow

```
/interview  →  /plan  →  /execute  →  /reflect  →  /compound
    │            │           │            │            │
  Spec       Tasks       Build        Review      Learn
```

---

## File Structure

```
project/
├── CLAUDE.md                     ← Project-specific AI context
├── PROJECT_STATE.md              ← Current funnel position
├── IMPLEMENTATION_PLAN.md        ← Active task list (waves)
├── AGENTS.md                     ← Subagent patterns & context
│
├── specs/                        ← Feature specifications
│   └── [feature].md
├── sessions/                     ← Session logs
├── decisions.md                  ← Why we chose X over Y
└── ideas.md                      ← Backlog with phase tracking

docs/ (Directions reference)
├── 00_base.md                    ← Start here every session
├── 01_quick-reference.md         ← Daily cheatsheet
├── 03_workflow-phases.md         ← The funnel process
├── 04_architecture-decisions.md  ← Interview → tech mapping
├── PATTERNS-COOKBOOK.md          ← Reusable code patterns
├── 10-19: Setup docs
├── 20-29: Technical gotchas
├── 30-39: Quality & debugging
├── 40-49: Terminology reference
└── 50-59: Advanced patterns
```

---

## Key Commands

| Command | Phase | Purpose |
|---------|-------|---------|
| `/interview` | Define | Multi-phase discovery, creates spec |
| `/plan` | Plan | Creates IMPLEMENTATION_PLAN.md with waves |
| `/execute` | Build | Wave-based execution with subagents |
| `/next` | Build | Pick next task with full context |
| `/reflect` | Review | Multi-perspective code review |
| `/compound` | Learn | Extract reusable patterns |
| `/status` | Any | Current state summary |
| `/log` | Any | Update session log |

### Other Commands

| Command | Purpose |
|---------|---------|
| `/setup` | Detect project state, offer setup/migration |
| `/decide` | Record an architectural decision |
| `/learned` | Add term to personal glossary |
| `/cookbook` | Manage reusable code patterns |
| `/phase` | Change project phase |
| `/review` | Production checklist |
| `/new-feature` | Scaffold docs for new feature |
| `/directions` | Show all available commands |

---

## Key Concepts

### Backpressure
Every task has validation that must pass before commit:
```bash
swift build   # Compiles?
swiftlint     # Clean?
swift test    # Tests pass?
```
No commit until green.

### Waves
Tasks grouped by dependencies:
- **Wave 1**: Parallel (no dependencies)
- **Wave 2**: Depends on Wave 1
- **Final**: Verification

### Compounding
After each session, extract learnings:
- Patterns → `AGENTS.md`
- Terms → `44_my-glossary.md`
- Decisions → `decisions.md`

### Patterns Cookbook
Reusable code patterns extracted from production apps. Copy-first beats building new.

```
/cookbook         # Update cookbook (rescan for patterns)
/cookbook add     # Quick-add a pattern you just built
/cookbook search  # Search existing patterns
```

**Included patterns:**
- Window layouts (NavigationSplitView, HSplitView, multi-window)
- Export dialogs (NSSavePanel, NSOpenPanel, progress indicators)
- App lifecycle (initialization order, scene phase handling)
- MCP memory integration (Vestige patterns)

See `PATTERNS-COOKBOOK.md` for full code snippets.

---

## Installation

### Option 1: Plugin Install (Recommended)

```bash
git clone https://github.com/Xpycode/LLM-Directions.git
cd LLM-Directions
./install-directions.sh
```

Or manually:
```bash
mkdir -p ~/.claude/plugins/local
ln -sf /path/to/LLM-Directions ~/.claude/plugins/local/directions
cp commands/* ~/.claude/commands/
cp CLAUDE-GLOBAL-TEMPLATE.md ~/.claude/CLAUDE.md
```

### Option 2: Commands Only

```bash
cp -r commands/* ~/.claude/commands/
```

---

## Hooks (Plugin Only)

| Hook | Trigger | Behavior |
|------|---------|----------|
| **SessionStart** | New session | Auto-loads project state |
| **Stop** | Ending session | Reminds to run `/log` |
| **UserPromptSubmit** | Every prompt | Suggests relevant docs |
| **PostToolUse** | After commits | Suggests `/decide` for architecture |

---

## Patterns Adopted From

- [Ralph Playbook](https://github.com/ClaytonFarr/ralph-playbook) - Funnel methodology, backpressure
- [Compound Engineering](https://github.com/EveryInc/compound-engineering-plugin) - Learning extraction
- [Context Engineering Kit](https://github.com/NeoLabHQ/context-engineering-kit) - Reflexion patterns
- [miniPM](https://github.com/chyzhang/minipm) - Task phase progression
- [Deep Research Skill](https://github.com/199-biotechnologies/claude-deep-research-skill) - Multi-phase discovery
- [Simone](https://github.com/Helmi/claude-simone) - Project management framework

---

## Origin

Synthesized from 229 documentation files across 15+ shipped macOS/iOS projects, enhanced with community patterns from the Claude Code ecosystem.

---

## License

MIT - Use freely, modify as needed.
