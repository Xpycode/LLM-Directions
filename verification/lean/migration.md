# LE10 task-state integration

The canonical procedure is `reference/task-state.md`, added as a coordinator-owned integration
resource. make-plan, execute, log, status, setup and the plan/project-entry templates now consume
one authority contract. Discovery also found a stale Current Sprint sentence in commands/spec.md;
LE11 owns that file next and must replace it before final integration.

The migration recipe preserves exact originals before writing canonical records, validates evidence,
then publishes state/tracker pointers before retiring reconciled mirrors. It selects one current
handoff, retains older log bytes and does not mark manual gates complete. Read-only status never
initiates migration. New project scaffolding no longer copies the master's live task history.

`python3 verification/lean/test-task-state.py` exercises disposable root/docs records: selected-plan
counts and duplicate IDs, absent/ambiguous plans, false completion with a gate, standalone fallback,
interruption before pointer publication, repeat idempotence, immutable backups/mismatch, preserved
historical handoff and archival bytes/links. It is a contract rehearsal, not a production migrator
and not evidence of instruction-following by a fresh host.

Static transition review:

| Transition | Expected / source result |
|---|---|
| make-plan → execute | Plan owns boxes; tracker links it; request or state selects exact path; readiness requires prerequisites. |
| execute → log | Task evidence saved once in plan; run-ending close still automatic; open external gates remain. |
| log → status | Progress is selected-plan complete/total plus gates; no combined backlog percentage. |
| status → resume | Current handoff pointer selects one anchor; legacy ambiguity reported without changing records. |
| completed plan | Archive with evidence and repoint links before retiring active copy; open manual gate prevents completion. |

All five transitions were traced in root and docs layouts. Existing Mac-control plan/evidence is
not migrated. Consumer rollout remains separately authorized. The record fixtures prove data
invariants; E1 must still observe host behavior.
