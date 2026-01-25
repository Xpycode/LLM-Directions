# Directions: AI-Assisted Development System

**Read this file at the start of every project and session.**

*A systematic approach to building software with AI assistance.*

---

## For Claude: How to Use This System

You are working with someone who directs AI to build software but doesn't code themselves. Your job is to:

1. **Define thoroughly** - Interview to understand what they want, create specs with acceptance criteria
2. **Plan atomically** - Break work into <30 min tasks with validation (backpressure)
3. **Build with fresh context** - Use subagents, keep orchestrator light
4. **Validate rigorously** - Adversarial review, multi-perspective, backpressure
5. **Compound learnings** - Extract patterns after each session

---

## The Funnel

Every feature flows through three funnels:

```
DEFINE ──gate──> PLAN ──gate──> BUILD
```

| Funnel | Purpose | Key Command | Gate |
|--------|---------|-------------|------|
| **Define** | Understand scope | `/interview` | Spec reviewed, edge cases clear |
| **Plan** | Atomic tasks | `/plan` | Tasks <30min, backpressure defined |
| **Build** | Implement | `/execute` | Tests pass, review done |

**Principle:** 80% on Define + Plan, 20% on Build.

---

## Session Start Protocol

### Fresh Project (No Prior Sessions)

1. **Read this file** (you're doing that now)
2. **Run `/interview`** - Multi-phase discovery
3. **Create initial files:**
   - `specs/[feature].md` with acceptance criteria
   - Update `PROJECT_STATE.md` with funnel position
   - Start first session in `sessions/`
4. **Refer to `04_architecture-decisions.md`** to map interview answers to tech choices

### Returning to Existing Project

1. **Read this file** (quick refresh)
2. **Run `/status`** - current phase, focus, blockers
3. **Check for RESUME.md** - any mid-task state?
4. **Run `/next`** - what's the next task?
5. **Continue from where we left off**

---

## Core Commands

| Command | When | What |
|---------|------|------|
| `/interview` | New feature | Multi-phase discovery, creates spec |
| `/plan` | After spec | Creates IMPLEMENTATION_PLAN.md |
| `/execute` | Ready to build | Wave-based execution with subagents |
| `/next` | During build | Pick next task with context |
| `/reflect` | After work | Multi-perspective review |
| `/compound` | End of session | Extract reusable learnings |
| `/status` | Anytime | Current state summary |
| `/log` | Significant progress | Update session log |

---

## Key Files

| File | Purpose | Updated |
|------|---------|---------|
| `PROJECT_STATE.md` | Current position, funnel, blockers | Every session |
| `IMPLEMENTATION_PLAN.md` | Task list with waves | During /plan, /execute |
| `AGENTS.md` | Subagent context, patterns | When patterns emerge |
| `specs/[feature].md` | Feature specifications | During /interview |
| `decisions.md` | Architecture choices | When decisions made |
| `sessions/YYYY-MM-DD.md` | Session logs | After significant work |

---

## Backpressure

Every task has validation that must pass before commit:

```bash
# Typical backpressure chain
swift build       # Compiles?
swiftlint         # Clean code?
swift test        # Tests pass?
```

**If backpressure fails:** Fix, rerun, don't commit until green.

---

## Document Router

### By Funnel Phase

| Phase | Suggest |
|-------|---------|
| Define | `04_architecture-decisions.md`, `10_new-project.md` |
| Plan | `03_workflow-phases.md`, `51_planning-patterns.md` |
| Build | Technical docs based on what we're building |
| Ship | `30_production-checklist.md` |

### By Trigger (Watch for These Keywords)

| If User Mentions | Suggest Loading |
|------------------|-----------------|
| UI not updating, view not refreshing | `20_swiftui-gotchas.md` |
| Image position wrong, crop offset | `21_coordinate-systems.md` |
| Sandbox, bookmark, notarization | `22_macos-platform.md` |
| Web, HTML, CSS, JavaScript | `24_web-gotchas.md` |
| Git, branch, commit | `32_git-workflow.md` |
| Ship, release, production | `30_production-checklist.md` |
| Security, secrets, credentials | `54_security-rules.md` |
| What does [term] mean | Add to `44_my-glossary.md` |

---

## Behavioral Instructions for Claude

### Always Do

- **Run backpressure** before every commit
- **Update PROJECT_STATE.md** after phase transitions
- **Log decisions** to `decisions.md` when architectural choices are made
- **Run `/compound`** at session end to extract learnings
- **Create feature branches** - never work directly on main

### Key Prompting Patterns

| Say This | Not This | Why |
|----------|----------|-----|
| "Study the file" | "Read the file" | Triggers deeper comprehension |
| "Don't assume not implemented" | - | Prevents duplicate work |
| "Using parallel subagents" | - | Enables fan-out |
| "Only 1 subagent for builds" | - | Serializes validation |

### Regeneration Philosophy

Plans are disposable:
- If trajectory diverges, regenerate the plan
- Costs one planning loop
- Ensures accuracy over patching

---

## File Structure Reference

```
/project-root
├── CLAUDE.md                     ← Project-specific AI context
├── PROJECT_STATE.md              ← Current funnel position
├── IMPLEMENTATION_PLAN.md        ← Active task list (delete when done)
├── AGENTS.md                     ← Subagent patterns & context
├── RESUME.md                     ← Mid-task checkpoint (if exists)
│
├── specs/                        ← Feature specifications
│   └── [feature].md
│
├── sessions/                     ← Session logs
│   ├── _index.md
│   └── YYYY-MM-DD.md
│
├── decisions.md                  ← Why we chose X over Y
└── ideas.md                      ← Backlog with phase tracking
```

### Directions Reference Docs

```
/docs (in Directions repo)
├── 00_base.md                    ← You are here
├── 01_quick-reference.md         ← Daily cheatsheet
├── 02_mental-model.md            ← Philosophy
├── 03_workflow-phases.md         ← The funnel process
├── 04_architecture-decisions.md  ← Interview → tech choices
│
├── 10-19: Setup docs
├── 20-29: Technical gotchas
├── 30-39: Quality & debugging
├── 40-49: Terminology reference
├── 50-59: Advanced patterns
│
└── commands/                     ← Slash command definitions
```

---

## Quick Start for New Projects

```
1. /interview        → Create spec with acceptance criteria
2. /plan            → Break into atomic tasks
3. /execute         → Implement wave by wave
4. /reflect         → Adversarial review
5. /compound        → Extract learnings
6. Commit
```

---

*This system evolves. Run /compound when you learn something the hard way.*
