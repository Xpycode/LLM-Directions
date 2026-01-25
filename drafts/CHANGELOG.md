# Directions v2 Changelog

## What Changed

This update integrates patterns from:
- [Ralph Playbook](https://github.com/ClaytonFarr/ralph-playbook) - Autonomous execution methodology
- [Compound Engineering](https://github.com/EveryInc/compound-engineering-plugin) - Learning extraction
- [Context Engineering Kit](https://github.com/NeoLabHQ/context-engineering-kit) - Reflexion patterns
- [miniPM](https://github.com/chyzhang/minipm) - Task phase progression
- [Deep Research Skill](https://github.com/199-biotechnologies/claude-deep-research-skill) - Multi-phase discovery

---

## New Concepts

### The Funnel (from Ralph)
Three-phase funnel replaces linear phases:
- **DEFINE** → Spec with acceptance criteria
- **PLAN** → Atomic tasks with backpressure
- **BUILD** → Wave-based execution

### Backpressure (from Ralph)
Every task has validation that must pass:
- Tests, lints, builds
- Gates between phases
- No commit until green

### Compounding (from Compound Engineering)
Extract learnings after every session:
- Patterns → AGENTS.md or relevant docs
- Terms → glossary
- Decisions → decisions.md

### Wave Execution (from Ralph)
Tasks grouped by dependencies:
- Wave 1: Parallel (no dependencies)
- Wave 2: Depends on Wave 1
- Final: Verification

### Reflexion (from Context Engineering Kit)
Multi-perspective review:
- Bug Hunter, Security, Quality, Tests
- 2-3 passes, then stop
- Ignore nitpicks

---

## New Files

| File | Purpose |
|------|---------|
| `IMPLEMENTATION_PLAN.md` | Persistent task list (delete when done) |
| `AGENTS.md` | Subagent context, code patterns |
| `specs/[feature].md` | Feature specifications |

---

## New Commands

| Command | Purpose |
|---------|---------|
| `/plan` | Enter planning mode, create IMPLEMENTATION_PLAN.md |
| `/next` | Pick next task with full context |
| `/reflect` | Multi-perspective review |
| `/compound` | Extract learnings to permanent homes |

---

## Updated Commands

| Command | Change |
|---------|--------|
| `/interview` | Now multi-phase: Scope → Explore → Triangulate → Synthesize |
| `/execute` | Now references IMPLEMENTATION_PLAN.md, wave-based |
| `/status` | Now shows funnel position |

---

## Updated Files

| File | Change |
|------|--------|
| `PROJECT_STATE.md` | Added funnel tracking, validation gates, compound learnings |
| `03_workflow-phases.md` | Rewritten around funnel model |
| `00_base.md` | Simplified, integrated new patterns |
| `ideas.md` | Now has phase progression (ideas → specs → doing → done) |

---

## Key Principles Added

1. **80/20 Rule**: 80% planning/review, 20% execution
2. **Plans are disposable**: Regenerate when wrong, don't patch
3. **Backpressure > Prescription**: Let tests guide correctness
4. **Fresh context per task**: Subagents start clean
5. **Compound everything**: Never solve the same problem twice

---

## Migration

To adopt v2:

1. Copy files from `drafts/` to replace originals
2. Create `specs/` folder in projects
3. Create `AGENTS.md` in projects (or use template)
4. Update `CLAUDE.md` to reference new commands
5. Next session, use `/plan` instead of jumping to `/execute`

---

## Sources

- [awesome-claude-code](https://github.com/hesreallyhim/awesome-claude-code) - Curated resource list
- [Ralph Playbook](https://github.com/ClaytonFarr/ralph-playbook) - Funnel methodology
- [Compound Engineering](https://github.com/EveryInc/compound-engineering-plugin) - Learning loops
- [Context Engineering Kit](https://github.com/NeoLabHQ/context-engineering-kit) - Reflexion patterns
- [miniPM](https://github.com/chyzhang/minipm) - Task progression
- [Deep Research Skill](https://github.com/199-biotechnologies/claude-deep-research-skill) - Discovery pipeline
- [CCPM](https://github.com/automazeio/ccpm) - GitHub Issues integration patterns
- [Simone](https://github.com/Helmi/claude-simone) - Project management framework
