# Implementation Plan

> **Persists across sessions.** This is the task list that Ralph executes against.
> Regenerate when wrong rather than patching. Costs one planning loop.

## Goal
[One sentence describing what we're building]

## Acceptance Criteria
<!-- Derived during Define phase. Tests must satisfy these. -->
- [ ] [User can do X]
- [ ] [System handles Y edge case]
- [ ] [Performance meets Z threshold]

## Specs
<!-- One file per JTBD topic, created during Define phase -->
- `specs/auth-flow.md` - Authentication requirements
- `specs/data-model.md` - Entity relationships

---

## Tasks

### Wave 1 (parallel - no dependencies)
<!-- These can run simultaneously. Each task = one atomic commit. -->

- [ ] **1.1**: [Task description] -> `target-file.swift`
  - Success: [What "done" looks like]
  - Backpressure: [Test/lint/build that validates]

- [ ] **1.2**: [Task description] -> `target-file.swift`
  - Success: [What "done" looks like]
  - Backpressure: [Test/lint/build that validates]

### Wave 2 (depends on Wave 1)
<!-- Only start after Wave 1 completes. -->

- [ ] **2.1**: [Task description] -> `target-file.swift`
  - Depends on: 1.1, 1.2
  - Success: [What "done" looks like]
  - Backpressure: [Test/lint/build that validates]

### Wave 3 (verification)
<!-- Integration testing, manual verification -->

- [ ] **3.1**: Run full test suite
- [ ] **3.2**: Manual verification of user flows
- [ ] **3.3**: Adversarial review (2-3 passes)

---

## Operational Learnings
<!-- Add as you discover them. These inform AGENTS.md. -->
- [Pattern discovered during implementation]
- [Gotcha to remember for next time]

## Blocked Tasks
<!-- Move tasks here if blocked. Include reason and workaround attempts. -->


---

## Execution Log
<!-- Updated by /execute as waves complete -->

| Wave | Started | Completed | Commits |
|------|---------|-----------|---------|
| 1 | 2026-01-26 10:00 | 2026-01-26 10:45 | abc123, def456 |
| 2 | | | |
| 3 | | | |

---
*Delete this file when all tasks complete. Archive to sessions/ if needed for reference.*
