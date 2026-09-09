# Directions Lean Efficiency — Implementation Plan

**Status:** Planned; execution not requested. **Date:** 2026-09-10.
**Spec:** [Directions lean efficiency](directions-lean-efficiency.md).
**Review:** [Planning review and sources](../verification/directions-lean-efficiency-planning.md).

## Goal and scope

Fix false index diagnostics and unsafe guidance discovery, then reduce instruction loading and
duplicated bookkeeping without losing authorized continuation, validation or recoverable evidence.
This is a separate maintenance plan. The root [Mac-control plan](../IMPLEMENTATION_PLAN.md), its task
IDs, runtime blocker and acceptance evidence remain intact. Select this plan explicitly when executing.
The older `OPTIMIZATION-PLAN.md` is historical input, not an additional execution queue.

Planning authorizes these documents only. Implementation, live installation, consumer migration and
pushes have not started. An execution request selects the approved scope under `commands/execute.md`.
Keep automatic pre-clear closeout at genuine run endings and continue authorized ready work between
waves. Never interpret an unavailable host, an unanswered question or a passed fixture as acceptance.

## Design decisions and defaults

| Topic | Planned disposition | Decision boundary |
|---|---|---|
| F01 | Union live/archive records; explicit log target takes precedence over the row's displayed date. `--fix` adds only truly unindexed files to the live table. | LE02 verifies current syntax and preservation; no automatic history cleanup. |
| F02 | Define eligible canonical numbered filenames; exclude conflict/backup artifacts without deleting them. Validate before any template/install write. | LE03 records the accepted filename grammar and failure behavior. |
| F03/F05 | Commands own lifecycle behavior. Keep `log.md` as the complete short dispatcher/core; move conditional procedures to linked canonical references. | Preserve closeout semantics. Moving sections must include all callers and installed-resource paths. |
| F04/F10 | Compare shortened inline routing with a compact domain router and detailed on-demand index. Keep safety and master discovery explicit. | LE07 selects only a candidate passing the routing matrix and byte comparison; otherwise repair, retain current routing and leave AC04 open. |
| F06 | Prefer plan task status/evidence; TASKS retains backlog/inbox and links; state retains an execution pointer. | LE06 must prove migration/progress rules in a disposable legacy fixture before LE10 removes mirrors. No live Mac-control migration. |
| F07 | Prefer independently verifiable tasks and coherent validated commits, allowing related small tasks together. | Proposed policy, applied only by LE11 after LE06; explicit no-commit restrictions prevail. |
| F08 | Evaluate proportional dispatch for small independent changes. Preserve fresh packets and exclusive ownership whenever delegated. | Recent explicit agent requirements remain active until a recorded policy decision accepts a concrete exception. No time threshold by assertion. |
| F09 | Prefer collision checks at arrival, branch/worktree mutations or known concurrency; preserve existing SessionStart guard. | LE06 checks all risky entry paths before LE12 can narrow status checks. Codex reports detector limitations accurately. |
| F11 | Retain the filename as a no-write retirement notice, with actionable supported commands and documented exit behavior. | A blind wrapper is rejected: `redeploy.sh` replaces existing Claude instructions. Reconsider only for evidenced compatibility needs. |

LE06 records decisions in `decisions.md`, with examples and alternatives. Routine choices within
this plan need no renewed permission. A proposed reversal of previously requested agent behavior
must be presented as a concrete decision; only that policy change and its dependents wait. Rejecting
a proposal is a valid evaluation result, but does not mark an unmet spec criterion complete.
For F08 specifically, absent an accepted exception, LE06 selects preservation of the existing
delegation policy and LE11 validates that default. Neither task waits for an optional policy answer.
LE13, LE14 and E1 can then validate the integrated default; AC08 stays open if proportionality has
not been demonstrated. A later policy change requires a scoped follow-up and affected revalidation.

## Acceptance and measurement contract

All implementation criteria remain unchecked in the spec. Task completion requires its stated
evidence; overall completion requires LE01–LE14 and E1, plus every AC or an explicit scoped deferral.

| Spec criterion | Implementation/evidence owners |
|---|---|
| AC01 | LE02, LE13 |
| AC02 | LE03, LE09, LE13 |
| AC03 | LE05, LE08, LE10 |
| AC04 | LE07, LE09, E1 |
| AC05 | LE08, LE13, E1 |
| AC06 | LE06, LE10, LE13, E1 |
| AC07–AC08 | LE06, LE11, E1 |
| AC09 | LE06, LE12, E1 |
| AC10 | LE04, LE13 |
| AC11 | LE01, LE13, LE14, E1 |

Freeze before/after scenarios in LE01: plain status, a small standalone fix, plain log, selected-task
pre-clear, whole-plan multi-wave continuation, one blocked dependency with unrelated ready work,
explicit no-agent/no-commit limits, Mac handoff, and launched-app cleanup with an explicit keep-running
exception. Include root-master and `docs/` consumer layouts, no active plan and a legacy partial plan.
Run routing cases in both hosts: every domain represented in the current eligible index, slashless
commands, natural-language plan continuation, incidental keyword mentions, installed globals and a
repository without globals. Explicitly cover secrets, dirty work, multi-Mac recovery and UI constraints.

Record source hashes, host/version/model/effort, scenario input, loaded files/bytes, tool calls,
files changed, unnecessary questions and outcome. Count initial instructions and subsequently read
files separately; include the extra index lookup in two-stage totals. Use the same host/model/effort
for each paired comparison. Three fresh runs per representative workflow per host support descriptive
medians/ranges; no statistical or latency claim from a walkthrough or byte count. Record unavailable
metrics as unavailable. Acceptance requires zero lost safety/continuity checks, all required routes
found, smaller entry-point bytes per host and lower ordinary-path loaded bytes. Report other metric
regressions; resolve them or obtain an explicit tradeoff decision before recommending rollout.

## Execution schedule and ownership

The coordinator alone owns this plan, spec acceptance boxes, `PROJECT_STATE.md`, `TASKS.md`, Git,
integration and the frozen baseline. Named task owners exclusively edit the files below while
assigned; even coordinator-owned policy files are serialized by task. New `verification/lean/`
scripts/reports below are planned artifacts, not checks that already exist or have passed.
Each task writes its own fixture/output directory. Shared commands/templates are never concurrently
written. With four slots, Wave 2's four ready tasks run in batches or use coordinator capacity.

| Wave | Tasks | Scheduling reason |
|---|---|---|
| 1 | LE01 | Freeze source and workflow baseline before mutations. |
| 2 | LE02, LE03, LE04, LE05 | Independent scripts, installer and context guide; disjoint files. |
| 3 | LE06, LE07 | Independent policy/migration analysis and routing experiment. |
| 4 | LE08, LE09 | Logging core and routing integration have separate write ownership. |
| 5 | LE10 | Serial lifecycle migration spans shared commands. |
| 6 | LE11, LE12 | Commit/delegation policy and collision boundaries own separate files. |
| 7 | LE13 | Coordinator integrates the final source and runs acceptance fixtures. |
| 8 | LE14 | Independent review of integrated behavior; E1 remains a separate host gate. |

Wave numbers are scheduling guidance, not global barriers: use the named prerequisites below.
LE04, for example, can continue while an LE03 failure is repaired. External E1 never blocks local
implementation. Current next task is LE01, prerequisite-ready, awaiting an execution request.

## Tasks

- [ ] **LE01 — Freeze baseline and scenario oracles.** Depends on: none. External gates: none.
  Owns: `verification/lean/baseline.md`, `verification/lean/scenarios.md`,
  `verification/lean/measure.py` and immutable fixture inputs under `verification/lean/baseline/`.
  Interface: hashed pre-change inputs, expected routing/continuation/safety outcomes and measurement
  format used by every later comparison. Preserve locally dirty source in the snapshot; label it.
  Success: reproduce spec byte measurements or explain differences; record static baselines and
  replayable inputs. Host observations unavailable now are reserved for E1 using the frozen source.
  Backpressure: `python3 verification/lean/measure.py --check-baseline` verifies hashes and byte totals;
  coordinator checks each scenario has an observable expected outcome, not just required keywords.

- [ ] **LE02 — Make session checking archive-aware and row-aware (F01).** Depends on: LE01.
  External gates: none. Owns: `scripts/sync-session-index.sh`, `verification/lean/test-session-index.sh`.
  Interface: preserve command arguments and documented 0/1/2 outcomes; document any existing fix-error
  exit separately. Read `_index.md` plus optional `_index-archive.md`; links win over display dates.
  Success: clean union, no archive, empty indexes, `./` links, suffixed links with unsuffixed display
  dates, bare dates, paths with spaces, duplicates across indexes, true missing and orphan records
  all classify correctly. `--fix` is idempotent and preserves archive/file bytes; unindexed conflict
  logs remain visible for human reconciliation, not silently hidden or deleted. Missing cross-Mac
  files are reported as unavailable targets, without claiming their history should be removed.
  Backpressure: `bash -n scripts/sync-session-index.sh` and
  `bash verification/lean/test-session-index.sh`; fixtures assert exit codes, diagnostics and hashes.

- [ ] **LE03 — Filter and validate generated guidance (F02).** Depends on: LE01. External gates: none.
  Owns: `scripts/gen-directions-index.sh`, `verification/lean/test-guidance-index.sh`.
  Interface: existing preview, `--base` and `--write` behavior; `--base` changes rendered paths, not the
  source directory. Tests therefore place a generator copy in a disposable master with fixture docs.
  Success: canonical docs occur once; Syncthing, backup and editor copies and redirect stubs are
  excluded and unchanged. Empty eligible sets, malformed marker pairs and bad arguments fail before
  replacing a destination; repeat generation is identical and preserves text outside managed markers.
  Backpressure: `bash -n scripts/gen-directions-index.sh` and
  `bash verification/lean/test-guidance-index.sh`, including contaminated-input negative cases.

- [ ] **LE04 — Retire unsafe legacy installation (F11).** Depends on: LE01. External gates: none.
  Owns: `install-directions.sh`, `README.md`, `verification/lean/test-legacy-install.sh`.
  Interface: retained entry filename; help names `deploy-codex.sh` and Claude's `redeploy.sh` separately,
  explains the latter's overwrite behavior, and directs users to dry-run/skip options.
  Success: inventory repository callers and the current argument behavior first; no-argument invocation
  reports retirement and a documented nonzero exit; help succeeds; unsupported arguments fail clearly.
  No commands, symlinks, settings or personal instructions are written, even on repeated invocation.
  Backpressure: `bash -n install-directions.sh` and `bash verification/lean/test-legacy-install.sh`;
  use a disposable-home child process and compare complete before/after file inventories and bytes.

- [ ] **LE05 — Remove competing lifecycle instructions (F03).** Depends on: LE01. External gates: none.
  Owns: `52_context-management.md`, optional `reference/context-examples.md`,
  `verification/lean/context-review.md`.
  Interface: session-log Resume and archived plans/evidence remain the canonical lifecycle.
  Success: replace all contradictory prose, diagrams, checklists and tables, not just lines 673–714.
  Retain useful context diagnosis/tutorials behind optional links; remove or qualify unsupported
  speedups and invented context percentages. No new full-load route to extracted material.
  Backpressure: `rg -n 'RESUME|[Dd]elete|[Aa]rchiv|[0-9]+%' 52_context-management.md reference/context-examples.md`
  (omit the optional path if unused), classify every remaining match in the review, and walk pause,
  resume, completion and blocked-plan scenarios against current execute/log commands.

- [ ] **LE06 — Resolve bookkeeping and proportionality contracts (F06–F09).** Depends on: LE01.
  External gates: none; preserve existing delegation if its proposed exception is not accepted.
  Owns: `decisions.md`, `verification/lean/policy-and-migration.md` and its disposable example records.
  Interface: accepted status/progress schema, legacy selection rules, commit examples, delegation
  decision table and collision trigger matrix for LE10–LE12. No workflow policy changes in this task.
  Success: demonstrate plan/task ID identity, pending/implemented-unverified/complete/blocked states,
  evidence links and gates; calculate plan progress independently from backlog/archive totals.
  Define no-plan fallback, multiple-plan selection, legacy checkbox/evidence reconciliation, partial
  migration recovery, completed-plan archival, retained history and repeat-migration idempotence.
  Compare dispatch overhead for small independent versus substantial independent work; do not weaken
  fresh-context/ownership requirements. Record adopted, rejected and unresolved choices separately.
  Backpressure: replay the LE01 transition cases on legacy and proposed records and record expected
  versus actual status/count/link results; review decision examples against `commands/execute.md`,
  `32_git-workflow.md`, `37_multi-mac-discipline.md` and the recent wave-workflow review.

- [ ] **LE07 — Compare routing candidates (F04/F10).** Depends on: LE01, LE03. External gates: none.
  Owns: `verification/lean/routing.md`, `verification/lean/routing-cases.json`,
  candidate fixtures under `verification/lean/routing/`.
  Interface: selected format, canonical detailed-index location if used, complete domain coverage,
  missing-global fallback and exact generator/deployer changes for LE09.
  Success: compare both candidates with the frozen baseline; measure global-plus-repository initial
  bytes and per-scenario retrieval bytes/calls. Check relevant-task matching and incidental keywords.
  Static walkthroughs are labelled provisional pending E1, never reported as observed host behavior.
  Backpressure: `python3 verification/lean/measure.py --routing` (add this mode within LE07 only after
  LE01 has relinquished the file); validate all expected paths and record every matrix disposition.

- [ ] **LE08 — Extract conditional logging procedures (F05).** Depends on: LE02, LE05.
  External gates: none. Owns: `commands/log.md`, `commands/execute.md`,
  canonical subprocedures under `reference/log/`, `verification/lean/logging.md`.
  Interface: read `log.md` completely as the short core; it dispatches optional app cleanup, Mac/Git
  handoff and host-specific integration by actual trigger, with master-absolute resolution from an
  installed command. Thus existing full-command readers remain correct and need no blanket exception.
  Success: ordinary logging loads no irrelevant branches; state/index/evidence remain saved;
  execution endings log automatically, ongoing waves do not. Preserve explicit keep-app-running,
  no-log/no-commit/no-push boundaries, exact outcome and next-session model-fit reminder.
  Backpressure: run the frozen log/continuation/blocked scenarios as documented walkthroughs in
  `verification/lean/logging.md`; compare required outputs and loaded paths/bytes with LE01.

- [ ] **LE09 — Integrate selected lean routing (F02/F04/F10).** Depends on: LE03, LE07.
  External gates: none; host proof remains E1. Owns: `CODEX-GLOBAL-TEMPLATE.md`,
  `CLAUDE-GLOBAL-TEMPLATE.md`, `AGENTS.md`, `CLAUDE.md` if present,
  `scripts/gen-directions-index.sh`, `deploy-codex.sh`, `redeploy.sh`,
  `codex/skills/directions/SKILL.md`, optional `DIRECTIONS-INDEX.md`,
  `verification/lean/test-deployment.sh`.
  Interface: validated candidate and reliable master/command/reference discovery for both hosts.
  Success: preserve local repository facts, safeguards and standalone fallback; render both hosts
  through the same eligibility source, not independently edited tables. Preview validation catches
  contamination before installation. Temporary installs are repeatable; Codex personal text is
  preserved; Claude's established whole-file replacement is explicit and backed up in fixtures.
  Do not broaden that behavior through the retired installer. Establish master-relative reference
  resolution using an independent fixture; LE13 verifies LE08's actual references after integration.
  Backpressure: `bash verification/lean/test-guidance-index.sh`,
  `bash verification/lean/test-deployment.sh`, and LE07 routing comparison. Deployment tests use
  disposable master/home paths only, with outside-path write assertions; no live deployment.

- [ ] **LE10 — Apply canonical task-state ownership (F06).** Depends on: LE06, LE08, LE09.
  External gates: unresolved LE06 status schema only. Coordinator task; owns `commands/make-plan.md`,
  `commands/execute.md`, `commands/log.md`, `commands/status.md`, `commands/setup.md`,
  `IMPLEMENTATION_PLAN-template.md`, relevant embedded state/task templates in `commands/setup.md`
  and `12_documentation-templates.md`,
  `verification/lean/test-task-state.py`, and `verification/lean/migration.md`.
  Interface: all lifecycle commands read the same accepted authority and legacy fallback; backlog
  discovery and incomplete acceptance survive transitions. Inventory additional consumers before
  editing and serialize any newly discovered shared file through the coordinator.
  Success: complete-plan archival preserves links/evidence; status derives counts correctly without
  mirrored boxes. Prove migration on disposable legacy copies, including conflicting mirrors and
  interrupted migration; no bulk consumer or active Mac-control migration. Use the new format for
  new plans and provide an explicit migration recipe for existing plans.
  Backpressure: `python3 verification/lean/test-task-state.py` plus transition walkthroughs for
  make-plan → execute → log → status → resume in both root and `docs/` layouts. Python validates
  records/links/counts; walkthrough and E1 validate instruction-following behavior.

- [ ] **LE11 — Apply accepted task/commit/delegation policy (F07/F08).** Depends on: LE06, LE10.
  External gates: none; validate the LE06 preservation default if no delegation exception is accepted.
  Owns: `commands/make-plan.md`, `commands/execute.md`, `IMPLEMENTATION_PLAN-template.md`,
  `32_git-workflow.md`, `60_model-selection.md`, `verification/lean/granularity.md`.
  Interface: one consistent outcome/commit/dispatch policy across instructions and examples.
  Preserving and testing current delegation completes that implementation disposition, not an
  unproven AC08 efficiency claim; retain that criterion separately until demonstrated or deferred.
  Success: remove the arbitrary under-30-minute split and conflicting one-task-per-commit mandates
  only as accepted; scoped coherent commits retain task-to-commit evidence and validation. Honor
  no-agent/no-commit and selected-scope requests. Keep independent review where correctness needs it.
  Backpressure: `rg -n '30 minutes|one task|one commit|atomic commit|parallel|delegat' commands/make-plan.md commands/execute.md IMPLEMENTATION_PLAN-template.md 32_git-workflow.md 60_model-selection.md`;
  classify matches and replay the LE06 examples, including a substantial parallel wave and a coupled fix.

- [ ] **LE12 — Narrow status collision checks at verified boundaries (F09).** Depends on: LE06, LE10.
  External gates: unresolved LE06 collision policy only. Owns: `commands/status.md`,
  `commands/worktree.md`, `37_multi-mac-discipline.md`, `verification/lean/collision.md`.
  Interface: explicit trigger table; existing `hooks/session-guard.sh` and SessionStart wiring retained.
  Success: plain read-only status avoids unnecessary detector calls; arrival/known concurrency and
  every branch-changing entry point preserve warnings. No invented Codex process detector.
  Backpressure: `rg -n 'session-guard|collision|concurr|checkout|branch' commands/status.md commands/worktree.md 37_multi-mac-discipline.md`;
  trace the LE06 boundary matrix including absent detector and separate-worktree cases.

- [ ] **LE13 — Integrate and compare final behavior (all findings).** Depends on: LE02–LE12.
  External gates: none; integrate accepted choices/defaults and retain any unmet AC separately.
  Owns: `verification/lean/integration.md`, `verification/lean/run-checks.sh`, coordinator cross-links.
  Success: run all targeted fixtures against final sources, validate installed reference resolution,
  source links, routing and whole lifecycle consistency. Compare bytes/calls/writes/questions/outcomes
  with LE01 without inferred token or speed claims. Retain original Mac-control plan hash and blocker.
  Backpressure: `bash verification/lean/run-checks.sh` invokes the named fixture checks and `bash -n`
  for touched shell scripts; `git diff --check`; review complete frozen scenario matrix with evidence.
  Static checks do not close E1. Only rerun affected checks after a concrete later correction.

- [ ] **LE14 — Independently review integrated changes.** Depends on: LE13. External gates: none.
  Owns: `verification/lean/final-review.md`; implementation fixes return to their owners.
  Success: fresh-context reviewer inspects record preservation, migration, routing recall, deployment
  boundaries and workflow contradictions. Resolve material findings and revalidate affected behavior.
  Prefer Sol for cross-command migration and Luna for shell/routing fixture checks when available and
  permitted. State a serial review fallback if independent agents are unavailable; do not invent one.
  Backpressure: every finding has a file/evidence reference, disposition and affected rerun result.

## External acceptance and rollout

- [ ] **E1 — Observe fresh Codex and Claude Code sessions.** Depends on: LE13 and LE14.
  Requires: both hosts available in isolated test projects/profiles; model/effort recorded. Foreground
  app tests, real Mac handoff, global installation and consumer migration require their own actual
  authorization; ordinary fixtures do not grant it. Use isolated repositories/remotes for handoff tests.
  Owns: `verification/lean/host-acceptance.md`.
  Gates: observed-host claims in AC04–AC09 and AC11, overall completion and rollout recommendation.
  Success: replay frozen before/after sources with matched settings, record the required routing and
  workflow observations and comparative metrics, including preservation of every safety/continuity
  check. Explicitly distinguish simulated handoff/cleanup from any actual product behavior tested.
  While unavailable: complete all local work; keep this box and affected ACs open with exact missing
  scenarios. A final report may say locally validated, host acceptance pending.

After E1, report the concrete deploy commands, rendered diffs and compatibility notes for a separately
authorized rollout. Preserve backups and the baseline; revert only this plan's scoped changes if a
regression occurs. Never restore a whole dirty checkout or remove conflicts/history to meet a target.

## Execution log

| Task IDs | Assignment / serial reason | Validation / evidence | Commit / exception | Remaining gates / next action |
|---|---|---|---|---|

No implementation assignments or passing results recorded yet. Planning evidence lives in the linked
review. On completion archive this plan with its evidence and update incoming links; while any
required gate is open, retain the plan and its unchecked tasks.
