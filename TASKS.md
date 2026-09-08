# Tasks

> **Persistent task tracker.** Root path in the Directions master. Progress syncs to PROJECT_STATE.md.
> Active plan: [Mac Control Coordinator](IMPLEMENTATION_PLAN.md). IDs match the plan.

## Backlog
<!-- Ideas and future work. Added by /spec deep, user input, or discovered during development. -->
<!-- Priority: top = highest, bottom = lowest -->

- [ ] 2.2 Implement private IPC and client identity.
- [ ] 2.3 Implement request queue and human decision transitions.
- [ ] 2.4 Implement countdown, deadlines, and liveness.
- [ ] 3.1 Implement typed action admission and target checks.
- [ ] 3.2 Implement the bounded AX worker.
- [ ] 3.3 Implement revoke, drain, and failed-stop handling.
- [ ] 3.4 Verify two-client exclusivity at the executor boundary.
- [ ] 3.5 Implement fresh-build handoff and interrupted-launch recovery.
- [ ] 4.1 Add menu-bar queue and safe request panel.
- [ ] 4.2 Add countdown and running overlay.
- [ ] 4.3 Wire emergency stop and environment loss.
- [ ] 4.4 Verify placement and accessibility.
- [ ] 5.1 Implement CLI request/status/progress/action lifecycle.
- [ ] 5.2 Verify Codex client integration.
- [ ] 5.3 Verify Claude client integration.
- [ ] 5.4 Add shared Directions control procedure and routing.
- [ ] 6.1 Add reproducible app packaging and diagnostics.
- [ ] 6.2 Add opt-in install/update/removal with a temporary-home dry run.
- [ ] 7.1 Run the full acceptance matrix.
- [ ] 7.2 Independent lifecycle and integration review.
- [ ] 7.3 Pilot launch and Directions handoff.
- [ ] Maintenance: make `scripts/sync-session-index.sh` archive-aware and handle suffixed dates;
  review the unindexed `sessions/2026-02-18-vic-variant.md`. Confirmed by the 2026-09-05 log audit;
  combined live/archive links have no missing targets. Outside the 25-task feature plan.

## Current Sprint
<!-- Active work. Populated by /make-plan or /execute. Keep focused (3-7 tasks). -->
<!-- When done: /log moves to tasks-archive.md -->

- [ ] 1.3 Prove bounded input and stop in a disposable target — Stop, disconnect and heartbeat-loss
  input drains passed; [live loss timing passed](verification/mac-control/loss-timing-live.md)
  after 32 offline tests. [Escape/key intervention passed](verification/mac-control/intervention-live.md)
  at 8.233833/1.490500 ms; window ended. Next: prepare an independent disposable focus-loss fixture.
  Broader intervention, clipboard and recovery evidence remain pending.
- [ ] 2.1 Scaffold the isolated Swift package and test harness — depends on Gate A.

---

## Inbox
<!-- Untriaged ideas and observations. For a possible bug, include date + evidence/repro status. -->
<!-- Promote confirmed actionable work to Backlog; dismiss observations that do not recur. -->

<!-- No untriaged observations. Compatibility questions are explicit gates in the plan. -->

---

## Progress Calculation

```
Sprint Progress = checked in Current Sprint / total in Current Sprint
Overall Progress = (archived count + checked) / (backlog + current + archived)
```

Archived task count is read from `tasks-archive.md` header.

## Workflow Integration

| Command | Action |
|---------|--------|
| `/spec deep` | Adds tasks to Backlog |
| `/make-plan` | Moves Backlog → Current Sprint |
| `/execute` | Checks off tasks as waves complete |
| `/log` | Archives checked tasks, updates PROJECT_STATE.md progress bar |
| `/status` | Reports progress from checkbox counts |
| Any active workflow | Captures non-blocking issues in Backlog and unconfirmed observations in Inbox |

---
*Location: root `TASKS.md` in this master; `docs/TASKS.md` in consumer projects.*
