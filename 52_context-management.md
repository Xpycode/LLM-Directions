<!--
TRIGGERS: context, token limit, context too big, AGENTS.md bloated, CLAUDE.md bloated, large project,
          context rot, compacting, /compact, /clear, prompt engineering,
          information environment, progressive loading, router pattern
PHASE: any
LOAD: on-request
-->

# Context Management

Keep the current task, relevant evidence and constraints easy to find. This guide covers context
diagnosis and document design. [Execution](commands/execute.md) owns continuation and plan
completion; [logging](commands/log.md) owns session close and the session-log Resume block.
Follow those commands for lifecycle actions rather than treating this guide as another procedure.

The former `50_progressive-context.md` and `58_context-engineering.md` paths redirect here.
For worked router templates and prompt examples, optionally read
[Context examples](reference/context-examples.md). Routine diagnosis needs only this guide;
do not load the examples by default.

## Diagnose before adding context

| Symptom | Check | Useful response |
|---|---|---|
| Wrong task or lost constraint | Current request, selected plan and current handoff | Restate scope and re-read specific evidence |
| Wrong answer about code | Actual file version and full error | Inspect relevant code and reproduction |
| Entry point mostly irrelevant | Which rules apply to every task | Route domain detail to conditional docs |
| Repeated corrections or confused history | Failed approaches mixed with accepted decisions | Summarize accepted facts; compact or start fresh when appropriate |
| Slow or crowded session | Host-reported usage, loaded files and output | Reduce unnecessary reads; do not infer a percentage |

These are clues, not a guaranteed sequence of degradation. A terse answer alone does not prove
a full context window. Before increasing model capability, use the diagnosis order in
[model selection](60_model-selection.md): clarify, improve context, compact or start fresh, then
adjust effort or capability.

## Route documentation by need

- Keep durable project facts and safety constraints in the host entry point (`AGENTS.md` or
  `CLAUDE.md`); changing state belongs in the plan, project state, decisions and logs.
- Give each reference a concrete **when to read** trigger and a short explanation of what it
  resolves. Load only references needed for the current task.
- Keep universal Directions guides in the master; consumer projects retain their own facts and
  links. Copied universal guides drift.
- Use nested instructions only for intentionally narrower scope and the host's documented loading
  behavior. See [Codex guidance](64_codex.md) or [Claude guidance](23_claude-code-cli.md).
- Summarize evidence where consumed and link the detailed record; avoid duplicating histories.

## Give the agent usable evidence

For a bug, supply expected and actual behavior, reproduction input, the full relevant error and
current code. For a feature, supply acceptance criteria, existing patterns and constraints.
For a refactor, name the contracts that must remain stable. For an architecture decision, identify
options, constraints and the trade-offs that matter.

Prefer a precise file/function or small excerpt to a whole-codebase dump. With file access, inspect
the actual file rather than trust stale pasted code. State exclusions when adjacent work is out of
scope. Record failed attempts and their results in the task's evidence; this is not an instruction
to run a second session-close log.

## Preserve working headroom

Use the host's real context display if available; report unknown usage as unknown. There is no
universal percentage, message count or elapsed-time threshold at which every task must stop.
Leave room for the next code read, tool output and verification, especially for complex work.
Status-line color bands are display heuristics, not permission to discard context or end work.

Compact when continuing related work and the conversation has become noisy. Start fresh for
unrelated work or when reconstruction from saved evidence is clearer. Before a context reset,
preserve task IDs, modified files, validation results, accepted decisions, remaining gates and
the exact next action through the authoritative logging workflow. Never clear or exit the user's
session automatically.

Host controls differ; consult [Codex guidance](64_codex.md) or
[Claude guidance](23_claude-code-cli.md) when operating that host. A host's session-resume feature
does not replace the project's durable handoff.

## Keep one lifecycle

| Situation | Authoritative route and expected state |
|---|---|
| Pause mid-task or prepare to clear | `/log clear` saves the session-log Resume block, state and index under `commands/log.md`; incomplete work stays active |
| End an execution run | `commands/execute.md` invokes the pre-clear log automatically; do not log twice |
| Continue authorized ready waves | Continue under `commands/execute.md`; a wave boundary alone is not a session close |
| Resume work | Use current project state, its selected active plan and current session-log handoff; verify evidence before continuing |
| Blocked task | Keep unchecked with its gate and required input; independent authorized ready work can continue |
| Selected task/wave finished | Record selected scope complete and next pickup; the unfinished overall plan stays active |
| Whole plan verified | Archive plan and execution evidence, update incoming links, then retire the active copy under `commands/execute.md` |

Do not create a separate `RESUME.md` or delete execution evidence. Historical logs remain evidence,
not competing instructions to resume old work. If current pointers conflict, resolve selection
through the status/execution workflow rather than guessing. Logging does not expand Git, deployment
or desktop-control authorization; preserve explicit limits and unresolved recovery.

| File | Context role | Retention |
|---|---|---|
| `PROJECT_STATE.md` | Lean current digest and active-plan pointer | Refresh present state; link history |
| Active plan | Tasks, dependencies, gates and execution evidence | Keep active while incomplete; archive after verified completion |
| Session log and Resume block | Chronological evidence and current pickup | Preserve evidence; refresh current handoff through `/log` |
| `decisions.md` | Rationale for accepted choices | Retain and link |
| Host entry point | Durable project instructions | Maintain stable guidance, not session state |

## Bounded work and context

Keep the main conversation focused. Delegate independent bounded work when authorized and useful;
serialize coupled work. A fresh task context receives the task description, prerequisites, relevant
files, constraints, success criteria and validation. The coordinator collects results and maintains
shared state. Execution's ownership and delegation rules remain in `commands/execute.md`.

Update task evidence at meaningful milestones rather than every fixed number of tool calls.
Do not turn each milestone into `/log`; that command closes the session. Existing task-size planning
examples remain in the optional reference pending the separate policy review.
