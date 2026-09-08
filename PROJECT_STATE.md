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
- **Next:** prepare a separate disposable focus-loss fixture to avoid input-monitor ambiguity.
  Recovery, clipboard and broader intervention proof remain pending before task 1.3 can close.
  Scope is occasional UI-test interruption across projects; Conjoyn provides a shell/AppleScript example.
- **Continuing backlog:** exercise shared Codex workflows in consumer projects and refine the ten
  new entry points from real use; broader lifecycle-hook migration remains evidence-gated.

## Recent
<!-- Last ~5 changes, one line each, plain language. Full detail → sessions/_index.md -->
- **2026-09-08** — Logged the intervention results and prepared the focus-loss handoff; cleanup rechecked and no test app remained running.
- **2026-09-07** — Escape/key intervention stopped input in 8.23/1.49 ms; loss-detection cases also
  passed. All test processes closed; portable evidence saved. Focus-loss and recovery remain pending.
- **2026-09-06** — Disconnect and heartbeat-loss input drains passed (11.11/10.57 ms); all test
  processes closed. Added timestamp/deadline checks and rejected teardown false passes; 32 offline
  tests passed. Updated instrumentation still needs live evidence.
- **2026-09-05** — Built the disposable harness and passed the first live Stop test: six correct
  characters, 12 matching events, 11.72 ms input drain; both processes closed. Broader proof pending.
- **2026-09-04** — Made model/context guidance provider-neutral, documented current Codex controls
  and provider mappings, refreshed global routing, and added tailored `AGENTS.md` files to the ten
  recently active projects after their logs and existing instructions were audited.
## Progress
- **Funnel:** Define ✅ · Plan ✅ · Build ⚪ — active feature; compatibility Gate A precedes implementation.
- **Readiness:** Features ✅ · UI/Polish 🔶 · Testing ⚪ · Docs ✅ · Distribution ✅ (existing framework).
- **Tracked progress:** 8/32 = 25% overall; active Mac-control plan 2/25 = 8% (inventory/protocol only).

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
- [Checkpoint](RESUME.md): task 1.3 partly verified; loss timing and Escape/key cases passed.
  [Latest verification](verification/mac-control/intervention-live.md) records the intervention window.
  [Pre-clear session resume](sessions/2026-09-08.md#resume) records the exact focus-loss pickup.
  Both approved windows are finished; Mac-control work is included in this checkpoint commit.
  Unrelated OtherSpaces guidance edits remain local; logs/checkpoint follow existing ignore rules.
  Focus-loss/recovery/clipboard and broader intervention proof are still pending.
- 22 Backlog items (21 feature + one index-maintenance); 0 Inbox; Current Sprint 0/2 after archiving.

---
*Lean digest. Source of truth for current position; history lives in the linked files.*
*Last updated: 2026-09-08.*
