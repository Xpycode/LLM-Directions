# Wave execution workflow review — 2026-09-09

## Problem and evidence

SoftwareLicensesManager's September 9 session records the owner's correction of six sequential
feature groups labelled as waves. The amended plan preserved 40 task IDs, separated external checks,
and scheduled the remaining work into dependency waves with exclusive ownership. Its subsequent
Wave 1–3 entries document fresh task agents and integrated validation. The original session also
recorded narrower delegation authorization; those historical limits must not be retroactively ignored.

ChargeMap's September 8–9 records show useful distinctions to preserve: catalog validation can finish
with an empty production catalog while G3 real-pricing evidence remains missing; implemented controls
with automated tests remain unchecked where manual acceptance is required. Its current plan explicitly
keeps dependent Wave 6 work behind those checks. These logs support targeted workflow corrections,
not a claim that every recent app failed to use agents or that logs prove every tool invocation.

Read-only sources in the local app workspaces:

- `SoftwareLicensesManager/docs/sessions/2026-09-09.md`, “dependency-wave rearrangement” and Waves 1–3.
- `SoftwareLicensesManager/IMPLEMENTATION_PLAN.md`, execution schedule and external checks.
- `ChargeMap/docs/sessions/2026-09-08.md` and `2026-09-09.md`.
- `ChargeMap/IMPLEMENTATION_PLAN.md`, gates, Tasks 4.4 and 4.6/5.1–5.6, execution log.
- `MacroPorn/docs/sessions/2026-09-09-pages.md` also documents disjoint agent ownership and integration.

## Changes

- Global entry points route natural-language execution requests to the live shared command.
- Planning requires dependencies, external gates, interfaces and exclusive file ownership.
- Execution selects ready tasks, dispatches fresh contexts, integrates under one owner, validates,
  records evidence and continues within the user's requested scope.
- Missing external evidence blocks named dependents; it neither stops unrelated work nor counts as a pass.
- The plan template records assignments, validation, commits/exceptions and continuation/stop reasons.
- Completed plans retain their execution evidence in an archive. Existing consumer plans are not rewritten.

## Scenario review

This is a manual walkthrough of the revised instructions against recorded and counterexample cases,
not a live app execution or proof of future model compliance.

| Input / state | Required behavior under the revised rules | Review |
|---|---|---|
| License collection sizing unavailable; independent model/import work ready | Keep sizing open, enforce final bounds gate, continue independent tasks | Covered by planning dependency review and execute Step 2.1 |
| “Execute the plan”; independent tasks with disjoint ownership | Fresh-context agents, coordinator integration, relevant validation, then next ready wave | Covered by scope and Steps 2.2–2.6 |
| Two nominally parallel tasks both edit the model | Repair ownership/schedule or serialize; no concurrent shared-file writes | Covered by planning and Steps 1/2.3 |
| ChargeMap G3 missing | Allow permitted empty-catalog/synthetic work; real activation and acceptance remain blocked | Covered by explicit gates and provisional-work limits |
| Controls implemented, automated tests pass, required manual checks unavailable | Keep completion unchecked; do not advance dependent acceptance/integration | Covered by Steps 2.1, 2.4–2.5 and final verification |
| “Only Wave 2”, “next wave” without broader authorization, or `/execute next` | Finish the selected wave/task, report next; no renewed permission within selected scope | Covered by scope and single-task mode |
| Whole-plan execution authorized; follow-up names the next wave | Preserve broader authorization unless the user explicitly narrows it | Covered by scope |
| “Continue implementation”; wave complete, another ready | Continue without another permission prompt | Covered by Step 2.6 |
| User prohibits agents, commits or foreground operations | Preserve each restriction; record serial/commit exception; continue unaffected work | Covered by scope, Steps 2.2/2.5 and tool authorization boundaries |
| Status question, planning approval, small standalone fix | Do not start plan execution from discussion or require wave scaffolding for a small fix | Covered by scope and adapter routing |

## Limits and follow-up

### Status reminders and automatic close

Follow-up request: make project status remind the user about wave execution and automatically save
a pre-clear log when execution ends. Status/full/arrive now use the Next line for the ready wave or
specific blocker, reading the relevant plan entries if the state digest lacks an Execution line.
Planning, execution and logging maintain that concise state line. Status remains read-only.

Execution invokes the existing log command in pre-clear mode at its terminal boundary. It does not
close between authorized ready waves, grant push permission, clear the session or call blocked work
complete. A selected wave/task can be complete while the overall plan remains active.

Manual rule walkthrough:

| Case | Expected result |
|---|---|
| Status with ready wave | One Next reminder with `/execute`, wave and work; no execution/logging |
| Arrive with missing Execution field | Read relevant linked plan/dependencies; report ready work or blocker without migrating files |
| Status with missing/ambiguous plan evidence | Report readiness unknown; do not invent a runnable wave |
| Whole-plan execution, next wave ready | Continue; no pre-clear log at the intermediate boundary |
| Selected wave/task complete | Pre-clear log, keep remaining plan active, identify next task |
| All required implementation and acceptance complete | Archive plan, pre-clear log, report plan complete and ready to clear |
| Required acceptance blocked | Pre-clear log on ending the run, preserve open gates, report incomplete |
| Log write fails | Report failure; no “ready to clear” claim |
| User requested no log or immediate stop | Respect restriction; automatic close does not override it |

These checks review instruction behavior; they are not end-to-end agent execution tests.

These are procedural instructions, not an enforced scheduler. The execution log makes deviations
reviewable. Check the next real consumer execution for actual assignments, gate handling and
continuation; do not report this walkthrough as a behavioral trial. Existing broader consumer-workflow
follow-up remains in Project State; no product acceptance gate changed.

## Validation and installation

- `git diff --check` passed.
- Temporary-home deployment passed: unrelated personal guidance preserved, one managed block,
  correct skill symlink and byte-identical global output on a second deployment.
- Live Codex deployment passed on M4-Pro; the previous global AGENTS.md was backed up. The skill
  already links to the live master. Start a new Codex session to reload global guidance/discovery.
- Skill YAML parsed successfully with Ruby's YAML parser; name, description type and length passed.
  The bundled Python skill validator could not run because its PyYAML dependency is absent; no
  dependency was installed solely for this Markdown change.
- Claude's source template is aligned; its live configuration was not redeployed. No consumer
  application files were edited, and no app tests or live behavioral trial were run.
