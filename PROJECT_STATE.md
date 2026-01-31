# Project State

> **Size limit: <100 lines.** This is a digest, not an archive. Details go in session logs.

## Identity
- **Project:** [Name]
- **One-liner:** [What it does in one sentence]
- **Started:** [Date]

## Current Position
- **Funnel:** define | plan | build
- **Phase:** discovery | planning | implementation | polish | shipping
- **Focus:** [Current task/feature in 1 line]
- **Status:** ready | in-progress | blocked | verifying
- **Last updated:** [Date]

## Funnel Progress (Ralph-style)
<!-- The 3-phase funnel that ships software -->

| Funnel | Status | Gate |
|--------|--------|------|
| **Define** | done | Spec exists, acceptance criteria clear |
| **Plan** | active | IMPLEMENTATION_PLAN.md complete, tasks atomic |
| **Build** | pending | Tests pass, backpressure satisfied |

## Phase Progress
```
[##########..........] 50% - Phase 3 of 6
```

| Phase | Status | Tasks |
|-------|--------|-------|
| Discovery | done | 5/5 |
| Planning | done | 3/3 |
| Implementation | **active** | 4/12 |
| Polish | pending | 0/5 |

## Readiness
<!-- Status per dimension: ⚪ not started | 🔶 WIP | ✅ done -->

| Dimension | Status | Notes |
|-----------|--------|-------|
| Features | 🔶 WIP | [what's done/remaining] |
| UI/Polish | ⚪ — | [current state] |
| Testing | ⚪ — | [coverage notes] |
| Docs | ⚪ — | [README, API docs, etc.] |
| Distribution | ⚪ — | [build, signing, release] |

## Validation Gates
<!-- Backpressure checks before phase transitions -->
- [ ] **Define → Plan**: Spec reviewed, edge cases documented
- [ ] **Plan → Build**: Tasks are atomic (<30 min each), dependencies mapped
- [ ] **Build → Ship**: Tests pass, adversarial review done, manual verification complete

## Active Decisions
<!-- Last 3-5 decisions only. Full history in decisions.md -->
- [Date]: [Decision summary]

## Blockers
<!-- Empty = good. If blocked, include workaround attempts. -->


## Execution State
<!-- Only present during /execute. Delete when done. -->
- **Plan:** IMPLEMENTATION_PLAN.md
- **Current wave:** 2 of 3
- **Tasks complete:** 5/12
- **Last commit:** `abc123` feat(wave-2): add auth middleware

## Compound Learnings
<!-- Patterns extracted from recent sessions. Move to glossary/decisions when stable. -->


## Resume
<!-- If RESUME.md exists, note it here. Otherwise blank. -->


---
*Updated by Claude. Source of truth for project position.*
