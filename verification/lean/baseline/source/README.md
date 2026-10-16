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
They are **never copied into your projects** — copies drift and stop receiving updates. Codex and
Claude Code read them from your local clone through thin tool adapters and a generated Directions
Index.

### Install once (per machine)

```bash
git clone https://github.com/Xpycode/LLM-Directions.git
cd LLM-Directions

# Codex
bash deploy-codex.sh --dry-run
bash deploy-codex.sh

# Claude Code, only if you use it
bash redeploy.sh --dry-run
bash redeploy.sh
```

The Codex deployer links the Directions skill into `$CODEX_HOME/skills/` (default:
`~/.codex/skills/`) and merges a generated, marked block into `$CODEX_HOME/AGENTS.md` (default:
`~/.codex/AGENTS.md`); unrelated global guidance is preserved. Start a new Codex session after
deployment.

### For New Projects

1. Open your coding tool in the project and run `/setup`. In Codex, `setup` without the slash is
   an equivalent fallback if `/setup` is intercepted by the interface. It creates or preserves the
   appropriate `CLAUDE.md` and/or `AGENTS.md` entry point plus the project-specific Directions files:
   `docs/PROJECT_STATE.md` (the setup sentinel), `docs/sessions/`, `docs/decisions.md`, and
   `docs/glossary.md`, plus `docs/TASKS.md` for deferred work and observations. Universal guidance
   and command files are never copied.
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
    ├── glossary.md               ← Project-specific terms
    └── TASKS.md                  ← Deferred work + unconfirmed observations

LLM-Directions/ (this repo — read on demand, never copied)
├── 00_base.md                    ← System overview + document router
├── 01_quick-reference.md         ← Daily cheatsheet
├── 04_architecture-decisions.md  ← Interview → tech mapping
├── PATTERNS-COOKBOOK.md          ← Pattern index (patterns live in cookbook/)
├── 10-19: Setup docs
├── 20-29: Technical gotchas
├── 30-39: Quality & debugging
├── 40-49: Terminology reference
├── 50-63: Advanced patterns
└── 64_codex.md                    ← Codex integration, daily controls, and current model mapping
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

### Focus protection

When work exposes an unrelated issue, Directions acknowledges and records it before continuing:

```text
Captured → Backlog: export button alignment (should-fix, not blocking).
Continuing: persistence crash investigation.
```

Current blockers enter the active plan, confirmed non-blockers enter `TASKS.md` Backlog, and
unconfirmed one-off observations enter its Inbox. Model-fit advice appears once when the recommended
capability changes and again in a pre-clear or Mac-handoff summary for the next session.

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

### Codex (recommended for Codex users)

```bash
git clone https://github.com/Xpycode/LLM-Directions.git
cd LLM-Directions
bash deploy-codex.sh --dry-run
bash deploy-codex.sh
```

This uses the active Codex build's user skill directory and global `AGENTS.md`. The managed block is
replaced on future deploys without replacing personal instructions outside it.

### Claude Code

```bash
bash redeploy.sh --dry-run
bash redeploy.sh
```

`install-directions.sh` remains as the older Claude-only installer; `redeploy.sh` is the complete,
idempotent path because it also prunes retired commands and refreshes hooks and settings.

---

## Claude Code hooks (plugin only)

These hooks are not installed for Codex. See `64_codex.md` for the deliberate fallback and the
criteria for a later native Codex port.

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
