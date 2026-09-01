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

**Read-on-demand model:** the universal docs in this repo are the single source of truth.
They are **never copied into your projects** — copies drift and stop receiving updates.
Claude reads them on demand from your local clone of this repo, routed by the Directions
Index in your global `~/.claude/CLAUDE.md`.

### Install once (per machine)

```bash
git clone https://github.com/Xpycode/LLM-Directions.git
cd LLM-Directions
./install-directions.sh
```

Then open `~/.claude/CLAUDE.md` and replace every `[LOCAL_DIRECTIONS_PATH]` placeholder
with the path to your local clone (the install script prints it).

### For New Projects

1. Open your coding tool in the project and run `/setup`. In Codex, `setup` without the slash is
   an equivalent fallback if `/setup` is intercepted by the interface. It creates or preserves the
   appropriate `CLAUDE.md` and/or `AGENTS.md` entry point plus the project-specific Directions files:
   `docs/PROJECT_STATE.md` (the setup sentinel), `docs/sessions/`, `docs/decisions.md`, and
   `docs/glossary.md`. Universal guidance and command files are never copied.
2. Run `/spec deep` to create your first spec
3. Run `/make-plan` to break into tasks, `/execute` to build

Codex recognizes the same short workflow vocabulary: `/status arrive`, `/spec`, `/make-plan`,
`/execute`, `/check`, and `/log`. The slashless forms (`status arrive`, `log clear`) are also
supported and avoid collisions with Codex built-ins. `$directions` remains compatible but is not
required.

### For Existing Projects (older copied-docs layout)

If a project still contains copied universal docs (`docs/00_base.md`, `docs/20_*.md`, …),
run `/directions update` — it removes the stale copies and switches the project to
read-on-demand. Your project-specific files (state, sessions, decisions) are untouched.

### Core Workflow

```
/spec  →  /make-plan  →  /execute  →  /check  →  /log
   │           │            │           │          │
 Spec        Tasks        Build      Review      Learn
```

---

## File Structure

```
your-project/
├── CLAUDE.md                     ← Claude Code project instructions
├── IMPLEMENTATION_PLAN.md        ← Active task list (waves, delete when done)
├── AGENTS.md                     ← Codex project instructions
├── specs/                        ← Feature specifications
│   └── [feature].md
└── docs/                         ← Scaffolded by /setup — project files ONLY
    ├── PROJECT_STATE.md          ← Current funnel position (the sentinel)
    ├── sessions/                 ← Session logs
    ├── decisions.md              ← Why we chose X over Y
    └── glossary.md               ← Project-specific terms

LLM-Directions/ (this repo — read on demand, never copied)
├── 00_base.md                    ← System overview + document router
├── 01_quick-reference.md         ← Daily cheatsheet
├── 04_architecture-decisions.md  ← Interview → tech mapping
├── PATTERNS-COOKBOOK.md          ← Pattern index (patterns live in cookbook/)
├── 10-19: Setup docs
├── 20-29: Technical gotchas
├── 30-39: Quality & debugging
├── 40-49: Terminology reference
└── 50-62: Advanced patterns
```

---

## Key Commands

| Command | Phase | Purpose |
|---------|-------|---------|
| `/spec` (`deep`, `examples`) | Define | Multi-phase discovery, example mapping, creates spec |
| `/make-plan` | Plan | Creates IMPLEMENTATION_PLAN.md with waves |
| `/execute` (`next`) | Build | Wave-based execution with subagents; pick next task |
| `/check` (`code`, `ship`, `security`) | Review | Code quality, production checklist, security audit |
| `/log` | Learn | Update session log; also covers end-of-session close, handoff, blockers, phase changes |
| `/status` (`full`, `arrive`) | Any | Current state summary; full dump; sit-down handover check |

### Other Commands

| Command | Purpose |
|---------|---------|
| `/setup` | Detect project state, offer setup/migration |
| `/decide` | Record an architectural decision |
| `/learned` | Add term to personal glossary |
| `/cookbook` | Manage reusable code patterns |
| `/directions` (`update`) | Show all available commands; pull latest Directions from GitHub |
| `/worktree` | Parallel session isolation via git worktrees |
| `/test-app` | AppProbe UI automation testing |

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
- Reusable patterns → cookbook or the relevant shared guidance doc
- Codex-specific operating constraints → `AGENTS.md`
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

`PATTERNS-COOKBOOK.md` is the index; the full code snippets live as individual files in `cookbook/`.

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

**Then replace every `[LOCAL_DIRECTIONS_PATH]` placeholder in `~/.claude/CLAUDE.md`** with
the path to your local clone — a raw copy of the template is not functional without this.

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
