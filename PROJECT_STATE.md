# Project State

> **Size limit: <100 lines.** This is a digest, not an archive. Details go in session logs.

## Identity
- **Project:** Directions
- **One-liner:** LLM-assisted development framework with structured specs, plans, and verification
- **Tags:** meta, framework, documentation, workflow, Claude
- **Started:** 2024

## Current Position
- **Funnel:** build
- **Phase:** implementation
- **Focus:** Ecosystem tooling — XcodePreviews, cliclick, visual capture pipeline
- **Status:** ready
- **Last updated:** 2026-02-21

## Funnel Progress (Ralph-style)
<!-- The 3-phase funnel that ships software -->

| Funnel | Status | Gate |
|--------|--------|------|
| **Define** | done | Framework documented, patterns established |
| **Plan** | done | Slash commands, templates, workflows defined |
| **Build** | active | Iterating on improvements |

## Phase Progress
```
[################....] 80% - Mature framework
```

| Phase | Status | Tasks |
|-------|--------|-------|
| Discovery | done | ✓ |
| Planning | done | ✓ |
| Implementation | **active** | ongoing |
| Polish | ongoing | docs refinement |

## Readiness
<!-- Status per dimension: ⚪ not started | 🔶 WIP | ✅ done -->

| Dimension | Status | Notes |
|-----------|--------|-------|
| Features | ✅ done | Core framework complete |
| UI/Polish | 🔶 WIP | Slash commands, templates |
| Testing | ⚪ — | Manual verification |
| Docs | ✅ done | Full documentation suite |
| Distribution | ✅ done | GitHub repo, local master |

## Validation Gates
<!-- Backpressure checks before phase transitions -->
- [x] **Define → Plan**: Framework spec complete
- [x] **Plan → Build**: Commands and templates documented
- [ ] **Build → Ship**: Ongoing refinement

## Active Decisions
<!-- Last 3-5 decisions only. Full history in decisions.md -->
- 2026-02-18: Added XcodePreviews (Iron-Ham/XcodePreviews) to ecosystem — global `/preview` command, documented in 26_ecosystem.md and global CLAUDE.md
- 2025-02-07: Installed 261 agent skills globally via skills.sh for enhanced Claude Code capabilities

## Blockers
<!-- Empty = good. If blocked, include workaround attempts. -->


## Infrastructure
- **Global skills:** 261 installed at `~/.claude/skills/`
- **Key skill sets:** SwiftUI, Swift concurrency, UI/UX, workflow patterns, debugging, TDD
- **Update command:** `npx skills update`
- **XcodePreviews:** `/Users/sim/XcodeProjects/0-DIRECTIONS/XcodePreviews/` — `/preview` command for SwiftUI visual capture

## Resume
<!-- If RESUME.md exists, note it here. Otherwise blank. -->


---
*Updated by Claude. Source of truth for project position.*
