# Project State

> **Lean digest — target <50 lines.** Current state + a short changelog, then pointers to detail
> files. History lives in `decisions.md` and `sessions/_index.md`, not here.

## Identity
- **Project:** Directions — LLM-assisted development framework (specs, plans, verification)
- **Tags:** meta, framework, documentation, workflow, Codex, Claude Code · **Started:** 2024

## Now
- **Phase:** planning complete — lean-efficiency plan ready for an execution request.
  <!-- Phase changed: 2026-10-16 -->
- **Focus:** make Directions leaner while preserving useful planning, evidence and work-preservation rules.
  [October review](verification/directions-review-2026-10-16.md): 156 logs and two plans screened across
  21 projects; findings and proposed wording are recorded, not implemented.
- **Next:** execute the revised [lean-efficiency plan](specs/directions-lean-efficiency-plan.md)
  when requested: LE01 is prerequisite-ready; then LE15/LE16/LE03 lead the independent fixes.
- **Execution:** planning selected this maintenance plan; execution has not been requested.
  LE01 freezes the baseline. Policy choices and host acceptance retain their named gates.
- **Deferred Mac-control:** [plan](IMPLEMENTATION_PLAN.md) Wave 1 / task 1.3 and Gate A remain incomplete.
  User set restart aside on October 16; do not resume restart/recovery work as the next-session default.
  Preserve the unresolved marker, successful acquisition, failed transactions and observation journals.
- **Continuing backlog:** exercise shared Codex workflows in consumer projects and refine the ten
  new entry points from real use; broader lifecycle-hook migration remains evidence-gated.
- **Plan:** 16 tasks/eight waves plus host acceptance; two fresh-context agents reviewed the revision
  and primary web sources informed it. Archive-aware source exists; LE02 acceptance remains pending.
  No deployment, consumer migration or desktop control authorized.

## Recent
<!-- Last ~5 changes, one line each, plain language. Full detail → sessions/_index.md -->
- **2026-10-16** — Revised the efficiency plan using two agents and primary web sources; added authority/test-effect tasks and synchronized the first sprint.
- **2026-09-17** — Kept the existing model setup after reviewing MultiVibe; integrated three unindexed logs, preserving original conflict snapshots.
- **2026-09-10** — Native evidence capture and fresh-process reload passed; preserved the inventory library for restart and prepared retained-evidence inspection.
- **2026-09-10** — Fixed shared runtime selection and reviewed opt-in kernel inventory; native read-only check passed with marker unchanged. Fresh acquisition prepared.
- **2026-09-10** — Kernel-inventory prototype passed 19 tests and independent review; reproduced a shared-lock directory gap that blocks live integration.
## Progress
- **Funnel:** Define ✅ · Plan ✅ · Build ⚪ — plan validated; ready for requested execution.
- **Readiness:** Features ✅ · UI/Polish 🔶 · Testing ⚪ · Docs ✅ · Distribution ✅ (existing framework).
- **Tracked progress:** lean-efficiency 0/16 plus E1 pending; deferred Mac-control plan 2/25 = 8%.

## Detail (read only if needed)
- **Why** → `decisions.md` · **history** → `sessions/_index.md` · **backlog** → `TASKS.md` (+ archive)
- **Global config mirrors** → `CODEX-GLOBAL-TEMPLATE.md` + `deploy-codex.sh`; Claude Code remains in
  `CLAUDE-GLOBAL-TEMPLATE.md`, `CLAUDE-SETTINGS-TEMPLATE.json` / `.md`, and `redeploy.sh`.

## Infrastructure
- Codex Directions skill source: `codex/skills/directions/`; deploy to `CODEX_HOME/skills/directions`.
- XcodePreviews `/preview` at `/Users/sim/ProgrammingProjects/0-DIRECTIONS/XcodePreviews/`
- **Mac restore:** `git pull --ff-only`, then `bash deploy-codex.sh --dry-run && bash deploy-codex.sh`.
  If Claude Code is also used, run its separate `redeploy.sh` flow.

## Resume
- **Exact pickup:** [revised plan](specs/directions-lean-efficiency-plan.md), Wave 1 / LE01;
  [planning review](verification/directions-lean-efficiency-planning.md#october-16-revision).
- **Boundary:** execution not requested; no restart, Mac-control continuation or deployment follows
  automatically. Preserve incomplete safety gates and all earlier evidence.
- **Sprint:** LE01, LE15, LE16, LE03 (0/4); Mac-control tasks retained separately as deferred.
- **Model fit:** deep capability + high reasoning for cross-command policy and migration planning;
  current host setting not reliably visible.

## Deferred Mac-control evidence
These are historical checkpoint notes. Their restart/next-action suggestions are superseded by the
October 16 planning direction above; retain them as evidence, not current execution instructions.

- [Successful acquisition and later-boot preparation](verification/mac-control/acquired-preflight-review.md):
  kernel capture/reload passed once, marker unchanged. Successful transaction and all prior evidence
  preserved. Persistent byte-identical library staged; CLI/caller independently reviewed.
  Broad suite: 478 passed/one skip; 52 focused tests and three wrapper tests passed.
  Continuation branch: `fix/acquired-recovery-preflight`; includes the validated implementation and restart handoff.
  User explicitly deferred restart until a new session. Coordinate timing then; no automatic
  restart on session entry. No reboot, initialization, activation or foreground test has occurred.
  Handoff includes the final restart deferral; today's session log is ignored/local.
- [Shared-root and kernel integration](verification/mac-control/shared-root-and-kernel-integration.md):
  source pin now shared by native boundaries, startup never creates a missing root/marker.
  Opt-in kernel adapter and prepared caller independently reviewed; 456 broad passes/one skip,
  20 final compiled-parser tests passed. Native observation passed once in 337.630 ms,
  marker unchanged. Preserve its consumed journal with both earlier journals/five transactions.
  Fresh transaction c6448ce2f81c44f78af0752199fdae2b capture/reload caller is prepared;
  read-only inspect passed, run not executed. Native storage scope remains pending.
- [Kernel inventory contract/prototype](verification/mac-control/kernel-inventory-review.md):
  conditional absence proof reviewed; source-only current worker naming is supported.
  Directory-helper fallback can select different runtime roots; reproduced using mocked
  directory selection and real private locks. Define one trusted existing root and reject
  disagreement before launch. Preserve the current marker; no namespace migration or retry.
  Prototype passed 19 focused tests, warning-clean C compilation and independent review.
  Disconnected from recovery; task 1.3/Gate A remain open. Scoped local checkpoint, no push.
- Latest [inventory contract and capture outcome](verification/mac-control/inventory-contract-review.md):
  reviewed narrow disappearance rule passed one native observation; acquisition failed at
  observation 3/final/inventoryAfterFirstScanChanged after retention. No reload/retry.
  Preserve all five transactions and both consumed observation journals. Marker still unresolved;
  review the inventory snapshot replacement contract next. No new native or foreground scope arranged.
  Current code/handoff committed locally under execution authorization; no push.
- Latest [identity-read review and native result](verification/mac-control/identity-read-review.md):
  diagnostic fix validated; single native observation failed with ESRCH, marker unchanged.
  Review the all-process stability/completeness contract next; no further capture is arranged.
- [September 10 Wave 1 checkpoint](sessions/2026-09-10.md#resume): task 1.3 incomplete.
  Earlier [capture failure](verification/mac-control/fresh-caller-review.md#authorized-native-outcome)
  and [final-observation fixes](verification/mac-control/final-observation-review.md) remain recorded.
  No further native action is arranged.
  Preserve all four transactions; surviving baseline witness files do not prove completion.
  M1 Max arrival recovery stash retained; continuation committed locally, not pushed.
- Workflow changes are recorded in [the review](verification/wave-execution-workflow.md). Start a new
  Codex session to reload global routing; observe the next consumer execution for actual wave
  assignments, gate handling, status reminders and automatic logging. Claude's template is aligned
  but its live configuration has not been redeployed. This does not close the Mac-control gates below.
- [September 9 detailed recovery handoff](sessions/2026-09-09.md#resume--after-native-acquisition-failures)
  retains the prior failures; the September 10 checkpoint above is the current pickup point.
  [Latest continuation](verification/mac-control/legacy-activation.md): activation/reconciliation and
  one-shot admission implemented through the actual supervisor entry, with crash/replay tests.
  [Native caller and witness storage](verification/mac-control/native-caller-retention.md) now tested
  offline; [persistent provisioning](verification/mac-control/persistent-witness-provisioning.md) now
  retains original identities across processes. [Delivery review](verification/mac-control/delivery-review.md)
  is complete; [native-preflight CLI/runbook](verification/mac-control/native-preflight.md) is ready.
  [Native storage/provenance review](verification/mac-control/storage-and-provenance-review.md) passed
  disposable location checks; no original whole-report pins found. The [prospective acquisition caller](verification/mac-control/prospective-acquisition.md)
  is implemented and privately tested; its native attempt failed before baseline retention.
  Ordinary startup remains fenced; no safety gate was waived.
  Worker-crash marker unresolved. Candidate evidence never restores admission.
  Swift checkpoint edit uncompiled. No automatic retry or foreground authorization.
  [Latest evidence](verification/mac-control/worker-crash-2026-09-09.json) retains measurements and both traces.
  M4-Pro reconciled the Mac-control checkpoint; this documentation handoff includes the remaining
  iOS gesture and private credential-entry guidance. The arrival recovery stash remains on M4-Pro.
  Logs/checkpoint retain ignore rules. Native witness storage is machine-local and is not in Git.
  All approved windows ended. Recovery/clipboard and broader intervention proof remain pending.
- Model fit: deep capability + high reasoning for recovery state/durability; active host setting not reliably visible.
- 23 Backlog items (21 feature, one index-maintenance, one lean-efficiency review); 0 Inbox; Current Sprint 0/2 after archiving.

---
*Lean digest. Source of truth for current position; history lives in the linked files.*
*Last updated: 2026-10-16.*
