# Implementation Plan

> **Persists across sessions.** Execute using the shared `commands/execute.md` procedure.
> Repair scheduling errors while preserving task IDs, completed evidence and approved scope.

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

## Execution schedule and ownership

<!-- Group by explicit dependencies, not feature/layer headings. No task depends on another task
     in its wave. Independent tasks have exclusive source/test ownership; shared integration,
     project generation, tracking and Git belong to the coordinator. Name shared build resources.
     Record current user scope/limits; this template does not itself authorize execution. -->
- Execution scope/limits: [Current request or recorded authorization; otherwise awaiting execution]
- Coordinator-owned files/resources: [Shared wiring, project files, build/test directories]
- Interfaces to establish before dispatch: [Producer/consumer contracts]

## Tasks

### Wave 1 (parallel - no dependencies)
<!-- These can run simultaneously. Each task = one atomic commit. -->

- [ ] **1.1**: [Task description] -> `Model.swift`
  - Depends on / external gates: none
  - Owns: `Model.swift`, `ModelTests.swift`
  - Interface: [Contract provided to 2.1]
  - Success: [What "done" looks like]
  - Backpressure: [Test/lint/build that validates]

- [ ] **1.2**: [Independent task description] -> `Parser.swift`
  - Depends on / external gates: none
  - Owns: `Parser.swift`, `ParserTests.swift`
  - Interface: [Contract provided to 2.1; no dependency on 1.1]
  - Success: [What "done" looks like]
  - Backpressure: [Test/lint/build that validates]

### Wave 2 (serial integration — consumes 1.1 and 1.2)

- [ ] **2.1**: [Integrate model and parser] -> `Importer.swift`
  - Depends on: 1.1, 1.2
  - External gates: none
  - Owns: `Importer.swift`, `ImporterTests.swift`
  - Interface: [Integrated API required by verification]
  - Success: [What "done" looks like]
  - Backpressure: [Test/lint/build that validates]

### Wave 3 (verification)
<!-- Integration testing, manual verification -->

- [ ] **3.1**: Run integration suite
  - Depends on: 2.1
  - External gates: none
  - Owns: [Integration tests/evidence; coordinator serializes shared test resources]
  - Success: [Required integration behaviors verified]
  - Backpressure: [Exact command and expected result]
- [ ] **3.2**: Independent review where required
  - Depends on: 2.1
  - External gates: none
  - Owns: [Review report; findings return to implementation owner]
  - Success: [Applicable review findings resolved and affected checks passed]
  - Backpressure: [Review scope and evidence; no fixed number of speculative passes]

## External checks

- [ ] **E1**: Manual verification of user flows on target device
  - Depends on: 3.1, 3.2
  - Requires: [Device/user availability and any foreground authorization]
  - Owns: [Acceptance evidence]
  - Gates: [Named acceptance criteria and overall completion; not independent earlier tasks]
  - Success / verification: [Exact user flows, expected outcomes and retained evidence]
  - While unavailable: [Ready work that can continue; claims that must remain unverified]

---

## Operational Learnings
<!-- Add as you discover them. Route shared learnings to canonical docs; Codex-specific constraints may inform AGENTS.md. -->
- [Pattern discovered during implementation]
- [Gotcha to remember for next time]

## Blocked Tasks
<!-- Reference task IDs in place; do not duplicate completion boxes or lose dependencies.
     Record reason, evidence, affected dependents and required input. -->


---

## Execution Log
<!-- Updated by /execute as waves complete -->

| Wave / task IDs | Assignments or serial reason | Validation / evidence | Commits or exception | Remaining gates / next action or stop reason |
|---|---|---|---|---|
<!-- Add actual results during execution; do not prefill completions. Link long reports. -->

---
*Keep active while required work or acceptance is incomplete. On completion, archive with execution
evidence and update incoming links before retiring the active copy.*
