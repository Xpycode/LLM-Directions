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
  September 8 M4-Pro check also found prior ignored session logs absent locally; distinguish
  cross-Mac log availability from index drift before repairing entries.
  September 9 combined live/archive audit: no broken links; the existing February18 variant and
  `sessions/2026-09-08.sync-conflict-20260908-223811-OLVB77F.md` are unindexed. Preserve the conflict
  log (it contains the earlier full handoff) pending comparison with the canonical September8 log.
  Lean review independently reproduced the archive false positive; see
  [F01 / AC01](specs/directions-lean-efficiency.md) and LE02 in the linked lean-efficiency plan.
  September 10 close: combined live/archive links still have no missing targets; also preserve
  the unindexed `sessions/2026-09-09.sync-conflict-20260910-012344-OLVB77F.md` pending comparison.
- [ ] Implement the queued [Directions lean-efficiency plan](specs/directions-lean-efficiency-plan.md):
  review/planning completed with Sol, Luna and web sources on September 10; 14 tasks/eight waves plus
  host acceptance. LE01 freezes the baseline; LE03–LE14 cover F02–F11; F01 uses the maintenance item
  above via LE02. Awaiting explicit execution, with policy/migration gates in the plan. Keep the
  Mac-control Current Sprint intact; no implementation or deployment performed by planning.

## Current Sprint
<!-- Active work. Populated by /make-plan or /execute. Keep focused (3-7 tasks). -->
<!-- When done: /log moves to tasks-archive.md -->

- [ ] 1.3 Prove bounded input and stop in a disposable target —
  Current [kernel-inventory review/prototype](verification/mac-control/kernel-inventory-review.md)
  passed 19 focused tests and independent review; it stays isolated because shared runtime-root
  selection must be enforced before integration.
  Directory-helper fallback can split the lock namespace; reproduced with private locks and
  mocked directory selection. Next trusted existing root contract, preserving the unresolved
  marker and all five failed transactions. No live probe replacement; task/Gate A remain open.
  Latest [inventory disappearance contract](verification/mac-control/inventory-contract-review.md)
  implemented/reviewed: 406 broad passes/one skip, 29 final focused passes. Native probe passed;
  fresh capture failed at observation 3/final/inventoryAfterFirstScanChanged after retention.
  Preserve five transactions, no reload/retry. Next bounded inventory-change contract review;
  task 1.3/Gate A still incomplete.
  Latest [identity-read review](verification/mac-control/identity-read-review.md): fixed native
  failure categories, 397 tests passed/one skip, independent review passed. Single diagnostic
  failed with ESRCH during first identity scan; marker unchanged, no capture/retry. Next review
  all-process inventory stability/completeness; task 1.3 and Gate A remain incomplete.
  Latest [authorized capture failed](verification/mac-control/fresh-caller-review.md#authorized-native-outcome)
  at observation 3/final/processIdentityFirstScanRead after retention. No reload/retry; all four
  failed transactions preserved. Next review native identity-read handling offline; Gate A open.
  [Fresh caller prepared/reviewed](verification/mac-control/fresh-caller-review.md): location
  inspection, 23 focused tests and independent review passed. Next agree exact native capture/reload
  scope; no capture performed, task 1.3 and Gate A remain incomplete.
  [Final-observation offline fixes](verification/mac-control/final-observation-review.md) complete:
  precise identity/observation diagnostics, append-only wrapper outcomes and late-failure tests.
  386 full-suite passes/one skip; independent review passed. No native retry or Gate A closure.
  Next prepare/review fresh caller configuration before separately scoped native work.
  [September 10 inventory review](verification/mac-control/inventory-boundary-review.md) refines
  query/malformed/process-change diagnostics; full suite 369 passed/one skip, 34 final focused
  passes. One native observation passed with unchanged marker; authorized acquisition then failed
  at final `processIdentity` observation after baseline retention. No reload/retry; review the
  late failure next. Preserve all three failed transactions and Gate A.
  [Fresh acquisition/reload caller](verification/mac-control/prospective-acquisition.md) is implemented
  and privately tested; [native attempt failed](verification/mac-control/prospective-acquisition-live.md)
  before baseline retention. [Safe diagnostics now implemented](verification/mac-control/context-probe-diagnostics.md);
  fresh attempt failed at inventory boundary. Review that boundary next; preserve both transactions.
  Historical report classified acquired-now failed/unknown,
  never original crash-authenticated evidence. Marker/recovery and Gate A remain unresolved.
  [Native storage/provenance check](verification/mac-control/storage-and-provenance-review.md) passed
  disposable provision/reload. Original whole-report pins not found; prospective acquisition and
  retention review is next, preserving the historical failed/unknown outcome and unresolved marker.
  [Runnable native preflight](verification/mac-control/native-preflight.md) provides disposable
  provision/reload and read-only legacy inspection; 13 focused tests pass. Establish original
  external pins/provenance and review local storage locations before native use. Gate A stays open.
  [Persistent slot/anchor provisioning](verification/mac-control/persistent-witness-provisioning.md)
  passes 10 new tests; deployment-location validation and read-only native preflight next.
  [Native caller/witness retention](verification/mac-control/native-caller-retention.md) implemented
  with 12 new offline tests; persistent provisioning and external trust-anchor retention next.
  Stop, disconnect and heartbeat-loss
  input drains passed; [live loss timing passed](verification/mac-control/loss-timing-live.md)
  after 32 offline tests. [Escape/key intervention passed](verification/mac-control/intervention-live.md)
  at 8.233833/1.490500 ms; window ended. [Independent focus-loss fixture prepared](verification/mac-control/prepared-focus-window.md)
  September 9; [live startup failed before input](verification/mac-control/focus-loss-startup.md).
  Singleton fix confirmed on [retry](verification/mac-control/focus-loss-retry.md); marker reconciled.
  Final [focus-loss retest passed](verification/mac-control/focus-loss-live.md) after shutdown fix:
  11.248584 ms detection, 0.04275 ms drain, all processes exited0; marker clean.
  [Offline recovery preparation](verification/mac-control/recovery-preparation.md): 49 tests passed;
  [independent subprocess observer now passed](verification/mac-control/recovery-observer.md), 57 tests.
  [Native worker-crash case prepared](verification/mac-control/prepared-worker-crash-window.md): 61 tests;
  [One approved native run completed](verification/mac-control/worker-crash-live.md): 1.794583 ms loss
  detection upper bound, 12 matching events and target fence; all processes exited. Marker unresolved.
  [Reconciliation review complete](verification/mac-control/worker-crash-reconciliation.md): missing
  post-state-update checkpoint and run-bound durable record. [Record model implemented offline](verification/mac-control/recovery-record.md);
  [Checkpoint transport and separate writer added](verification/mac-control/checkpoint-storage.md), 89 tests passed.
  [Identity and durable admission integrated](verification/mac-control/recovery-admission.md).
  [Read-only verifier implemented offline](verification/mac-control/recovery-verifier.md).
  [Snapshot/evidence adapter implemented offline](verification/mac-control/recovery-adapter.md).
  [Darwin context/inventory probe implemented offline](verification/mac-control/recovery-context.md),
  with 15 tests. [Native wire/ack adapter](verification/mac-control/recovery-native.md) adds 12 tests.
  [Single-reader supervisor integration](verification/mac-control/recovery-supervisor.md) connects
  acknowledgements, fault gating and EOF/waits. [Held-lock reconciliation](verification/mac-control/recovery-reconciliation.md)
  now checks retained evidence after teardown with bounded setup/writer and context waits.
  [Native inventory visibility passed](verification/mac-control/native-context-live.md) outside sandbox;
  legacy marker/boot baseline retained unchanged. [Fenced bootstrap initialization](verification/mac-control/legacy-bootstrap-implementation.md)
  now has offline provenance/continuity and process-death tests; launcher rejects its retained artifacts.
  [Activation contract/native handoff reviewed](verification/mac-control/legacy-activation-preparation.md);
  v2 audit binds post-clean marker metadata and rejects six tested rewrite boundaries.
  [Completion seal/read-only preflight](verification/mac-control/legacy-completion-seal.md) now implemented
  offline, including external persistence and process-death checks.
  [Activation/one-shot admission](verification/mac-control/legacy-activation.md) now reaches the actual
  supervisor entry, with explicit checkpoint reconciliation and crash/replay tests. Next native
  caller/independent pin retention; boot freshness and native recovery remain unverified.
  Keep the marker unresolved and Gate A open.
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
