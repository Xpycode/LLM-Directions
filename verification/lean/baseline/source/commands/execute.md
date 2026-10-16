# Wave-Based Execution

Run implementation tasks with fresh context per wave, preventing quality degradation. **`/execute`
absorbs `/next`** — use wave mode for parallel work, single-task mode (`/execute next`) to walk one
task at a time.

## Scope and continuation

In a Directions project, requests to execute or resume an approved plan (including “continue
implementation” and “next wave”) use this procedure even without a slash command. A status question
does not start execution, and a small standalone fix does not require a new wave plan.

Execution of the approved plan includes fresh-context task delegation when the host permits it.
Preserve explicit user limits: “only Wave 2”, “one task”, “no agents”, “no commits” and foreground
test windows retain their scope. Without broader authorization, “next wave” selects one wave;
“execute the plan” or “continue implementation” continues through ready waves. A follow-up naming
the next wave does not revoke existing whole-plan authorization unless the user limits it.
Do not ask again at ordinary task/wave boundaries.
Planning approval alone is not an instruction to start implementation. Deployment, publication,
pushes and production-data operations retain their own authorization boundaries.

Before starting, apply `60_model-selection.md` → **User-Facing Model-Fit Notice**. Clear execution
normally uses implementation capability with medium reasoning; keep deep capability when the plan
contains subtle state, concurrency, security, destructive operations, or data-integrity work. Show
one notice only when the recommendation changes. The Claude-specific block below fulfils this step
for Claude Code; do not emit both notices.

<!-- CLAUDE-ONLY:START — Codex skips this model-marker integration -->
## Step 0 — Model tier check (NUDGE, not a gate)

Executing a clear plan is the canonical **Sonnet-tier** job; Opus/Fable burns premium tokens on bulk
edits. Record the phase (cheap — `/log` reads it for the next-session reminder) and read the model:

```bash
SID=$(ls -t "$HOME"/.claude/.current-model-* 2>/dev/null | head -1 | sed "s:.*/.current-model-::")
[ -n "$SID" ] && printf 'execute' > "$HOME/.claude/.session-phase-$SID"
MODEL=$(cat "$HOME/.claude/.current-model-$SID" 2>/dev/null)
echo "phase: execute · current model: ${MODEL:-unknown}"
```

If `MODEL` looks like Opus/Fable/Haiku, **nudge once and CONTINUE** (don't stop):
> 🔴 **You're on `<MODEL>` — execution is Sonnet-tier. `/model sonnet` saves cost; or continue if the plan is subtle.**

Then proceed. (The model read is best-effort — under two concurrent sessions the newest `.current-model-*`
may be the *other* session's, so this is a nudge, never a hard gate. Chat can't render red — use **bold + 🔴**.)
<!-- CLAUDE-ONLY:END -->

## Step 1 — Find or create the plan

Read project state, its linked active plan, task tracker and Git status. Prefer the linked plan;
otherwise check root and `docs/IMPLEMENTATION_PLAN.md`. Preserve overlapping uncommitted work;
use `37_multi-mac-discipline.md` when cross-Mac reconciliation is needed. Do not commit unrelated
work merely because it is dirty.

If no usable plan exists, use `commands/make-plan.md` and the shared plan template. Infer the goal
from the request and existing spec; ask only for missing requirements that affect the work.

Before dispatch, check task dependencies, success criteria, validation and exclusive file ownership.
“Storage”, “UI” and “tests” are feature groups, not evidence that their tasks can run concurrently.
If the schedule is wrong, repair it while preserving task IDs, completed evidence and approved scope;
explain the correction. Ask only if the repair needs a product decision or changes authorized scope.

## Step 2 — Execute waves

Repeat within the authorized scope:

1. **Select ready tasks.** A task is ready only when its named prerequisites and gates have evidence
   of completion. Group independent tasks into the next execution wave; reconcile an outdated schedule
   first. A failed external check blocks its named dependents, not the entire project. Keep blocked
   tasks unchecked. Provisional interfaces or injected fixtures are valid only where the plan permits
   them; they do not satisfy the missing gate.
2. **Assign ownership.** Announce the task IDs and parallel/serial arrangement briefly. Use parallel
   task agents for independent work, within available slots. Each gets **fresh context only — no
   conversation history**: task body, prerequisite evidence, accepted interfaces, relevant project
   facts, owned source/test files, success criteria and validation command. Serialize coupled work or
   split it at an interface first. If delegation is unavailable, prohibited or offers no independent
   work, state why and proceed serially; do not claim fresh-agent execution.
3. **Keep integration under one owner.** The coordinator owns shared project generation, integration
   adapters, plan/state/tracker updates and Git operations. Agents return out-of-scope edits for
   reassignment; they do not edit each other's files or commit the shared checkout. Shared build/test
   directories have one writer; independent checks use isolated scratch/output directories.
4. **Integrate and verify.** Review returned diffs against task criteria, integrate interfaces, then
   run relevant task and integration checks. Obtain independent review where required by
   `60_model-selection.md`. Fix concrete findings and rerun affected checks. Repeat a passed broader
   suite only when changes or unresolved risks justify it. Test results do not establish unperformed
   manual acceptance, real-provider behavior or device checks.
5. **Record the outcome.** Mark a task complete only when all its required criteria pass. Record
   implemented-but-unverified work separately and leave its completion box unchecked. Make scoped
   atomic commits for validated work under `32_git-workflow.md`, unless the user restricted commits
   or Git is unavailable; record the exception. Update the plan, matching tracker items and concise
   project state. Record task IDs, actual assignments/serial reason, validation evidence, commit or
   exception, remaining gates and next action in the plan's execution log; link longer evidence.
   Keep one `Now → Execution` line in project state: active plan link, current wave/task IDs and
   ready/blocked/awaiting-acceptance status with its reason. Replace the line as work advances;
   completed wave history stays in the execution log.
6. **Continue or explain the stop.** Continue to the next ready wave without renewed permission when
   the request covers it. At a user-imposed boundary, report what is ready next. If no authorized task
   is ready, checkpoint the exact blocker, affected task IDs, evidence and required input; ask only
   when user input is needed. Do not turn an unanswered optional question into a project-wide stop,
   or a timeout into approval. A user pause, end-of-session request or genuine tool limit also warrants
   a checkpoint; a wave boundary alone does not. When ending the execution run, apply Step 4 below.

### Interruptions discovered during execution

Protect the active focus using `00_base.md` → **Focus Protection**:

1. Current blocker/safety issue → add or promote it in the active plan and say why focus is changing.
2. Confirmed but non-blocking issue → add it to `TASKS.md` Backlog.
3. Unconfirmed or one-off observation → add it to `TASKS.md` Inbox with the date and available evidence.
4. Acknowledge the capture and restate the task being resumed. Do not ask whether to switch unless
   the classification is genuinely ambiguous or the user must choose a priority.

```text
Captured → Backlog: export button alignment (should-fix, not blocking).
Continuing: persistence crash investigation.
```

## Step 3 — Verify

Run the plan's final integration and acceptance checks, reusing still-valid evidence. Update project
state honestly. The overall plan remains open while required tasks or acceptance gates are incomplete,
even if all code is implemented. On completion, archive the plan and its execution evidence under the
project's documentation, update incoming links, then retire the active copy.

## Step 4 — Automatically prepare for clear

At the end of an execution run, read the master `commands/log.md` completely and run its **pre-clear**
workflow automatically, without asking the user to invoke `/log clear`. This applies when the whole
plan completes, a user-selected wave/task finishes, or execution ends at a genuine blocker/pause.
Do not run session-close logging between waves while authorized ready work remains; continue instead.
Respect an explicit request not to log or to stop immediately.

Record the exact outcome: **plan complete**, **selected scope complete; plan continues**, or
**blocked/incomplete**. Keep any incomplete plan active. Save the log, state, index and Resume with
remaining gates, uncommitted/unpushed work and the next action. The logging command owns those steps;
do not create a duplicate close procedure here. Honor explicit app-handoff instructions when retiring
test builds, and preserve commit/push restrictions. Local execution-commit authorization alone does
not authorize a push.

After saving and checking the handoff, end with `Logged and ready to clear — <outcome>; next: <action>.`
If a required write/check failed, report the failure and do not claim the handoff is ready. A known
index-maintenance warning may be recorded with its impact without erasing existing history. Ready to
clear means conversation context is saved; it does not mean release-ready or safe to switch Macs.
Never clear or exit the user's session automatically.

## Single-task mode  (`/execute next` — the old `/next`)

When you want one task at a time with full context instead of parallel waves:

1. Locate and read the active plan, project state and Git status as in Step 1.
2. Reconcile relevant uncommitted work, then select one dependency-ready task under Step 2.
3. Present its description, target files, success criteria, validation and prerequisites; start under
   the existing execution request. Ask only for a missing decision or authorization.
4. Apply Step 2's ownership, verification and recording rules. Report the next task after completion;
   stop after this task unless the user requested continued single-task execution. If blocked, report
   the dependency and an available alternative without silently substituting unrelated work.
   At the end of the run, apply Step 4's automatic pre-clear log.

## Key principles

1. **Orchestrator stays light** — keep task detail in files and fresh task contexts; do not invent
   context percentages when the host does not expose them.
2. **Fresh context per task** — each subagent starts clean with only task-specific info.
3. **Atomic commits** — one task = one commit, easy to revert.
4. **State lives in files** — `IMPLEMENTATION_PLAN.md` + `PROJECT_STATE.md` are the source of truth.
