# Project State

> **Lean digest — target <50 lines.** Current state + a short changelog, then pointers to detail
> files. History lives in `decisions.md` and `sessions/_index.md`, not here.

## Identity
- **Project:** Directions — LLM-assisted development framework (specs, plans, verification)
- **Tags:** meta, framework, documentation, workflow, Codex, Claude Code · **Started:** 2024

## Now
- **Phase:** compatibility spike — establish loss detection, input intervention and recovery behavior.
- **Focus:** shared FIFO Mac-control queue with Yes/No/Wait, countdown, progress, and enforced stop.
  [Spec](specs/mac-control-coordinator.md) · [plan](IMPLEMENTATION_PLAN.md) ·
  [research](specs/mac-control-research.md). Runtime compatibility is the current focus.
- **Gates:** task 1.3 must prove bounded input, stop and recovery from an actual session before the full UI.
- **Execution:** [Mac-control plan](IMPLEMENTATION_PLAN.md), Wave 1 / task 1.3 fresh caller reviewed; awaiting separate native scope, recovery blocked and Gate A open.
- **Next:** agree one capture/reload attempt using the [reviewed fresh caller](verification/mac-control/fresh-caller-review.md).
  Location inspection and 23 focused tests passed; exact native failure cause remains unknown.
  Preserve all three failed transactions, including the retained baseline witness.
  **Blocker:** runtime marker unresolved after the worker-crash experiment; no verified recovery or retry.
  Recovery, clipboard and broader intervention proof remain pending before task 1.3 can close.
  Scope is occasional UI-test interruption across projects; Conjoyn provides a shell/AppleScript example.
- **Continuing backlog:** exercise shared Codex workflows in consumer projects and refine the ten
  new entry points from real use; broader lifecycle-hook migration remains evidence-gated.
- **Queued plan:** [Directions lean efficiency](specs/directions-lean-efficiency-plan.md), 14 tasks in
  eight waves plus host acceptance; LE01 is prerequisite-ready, execution not requested. Define/plan
  gate passed for staged work; policy/migration choices have named gates. Mac-control remains active.

## Recent
<!-- Last ~5 changes, one line each, plain language. Full detail → sessions/_index.md -->
- **2026-09-10** — Prepared fresh acquisition caller; location inspection, 23 focused tests and independent review passed. Native capture/reload awaits separate scope; recovery remains unverified.
- **2026-09-10** — Added precise final-observation diagnostics and durable timeout reporting; 386 tests passed/one skip, independent review passed. No native retry; recovery gate remains open.
- **2026-09-10** — Refined diagnostics and one native observation passed. Authorized capture then failed during final process-identity observation after baseline retention; evidence preserved, no reload/retry.
- **2026-09-10** — Reviewed lean efficiency with Sol, Luna and official web sources; wrote the separate dependency/ownership/validation plan, preserving Mac-control work.
- **2026-09-09** — Strengthened wave planning/execution, added status reminders and automatic pre-clear logging; Codex guidance installed on M4-Pro. [Review and checks](verification/wave-execution-workflow.md).
## Progress
- **Funnel:** Define ✅ · Plan ✅ · Build ⚪ — active feature; compatibility Gate A precedes implementation.
- **Readiness:** Features ✅ · UI/Polish 🔶 · Testing ⚪ · Docs ✅ · Distribution ✅ (existing framework).
- **Tracked progress:** 8/33 ≈ 24% overall; active Mac-control plan 2/25 = 8% (inventory/protocol only).

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
- [September 10 Wave 1 checkpoint](sessions/2026-09-10.md#resume): task 1.3 incomplete.
  [Offline review/fixes complete](verification/mac-control/final-observation-review.md): precise
  scan/observation diagnostics, append-only outcome reporting and late-failure regressions validated.
  [Fresh caller now reviewed](verification/mac-control/fresh-caller-review.md); agree its exact
  capture/reload scope next. No further native action is arranged.
  Preserve all three transactions; surviving baseline witness files do not prove completion.
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
*Last updated: 2026-09-10.*
