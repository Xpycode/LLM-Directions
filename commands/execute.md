# Wave-Based Execution

Run implementation tasks with fresh context per wave, preventing quality degradation. **`/execute`
absorbs `/next`** — use wave mode for parallel work, single-task mode (`/execute next`) to walk one
task at a time.

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

Check for `IMPLEMENTATION_PLAN.md` in the project root. If missing, ask what to implement and create it:

```markdown
# Execution Plan
## Goal
[one sentence]
## Tasks
### Wave 1 (parallel — no dependencies)
- [ ] **Task 1.1**: [description] -> `target-file`
### Wave 2 (depends on Wave 1)
- [ ] **Task 2.1**: [description] -> `target-file`
### Wave 3 (verification)
- [ ] **Task 3.1**: run tests, verify integration
```

Grouping: same wave = parallel (no inter-dependencies); next wave = depends on the previous; each task atomic.

## Step 2 — Execute waves

For each wave, use the active tool's parallel subagents when delegation is available and authorized.
Each task prompt MUST include:
- the specific task + target files + success criteria, and project context from `PROJECT_STATE.md`;
- **fresh context only — no conversation history.**

After each wave: review all subagent results · make atomic commits (`feat(wave-N): …`) · tick
`IMPLEMENTATION_PLAN.md` and matching `TASKS.md` Current Sprint boxes · update `PROJECT_STATE.md`.
If blocked: write a `RESUME.md` checkpoint, ask the user, spawn a `debugger` agent if needed.

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

Run build/tests, check integration points, update `PROJECT_STATE.md` with completion status, delete
`IMPLEMENTATION_PLAN.md` when done.

## Single-task mode  (`/execute next` — the old `/next`)

When you want one task at a time with full context instead of parallel waves:

1. Read `IMPLEMENTATION_PLAN.md` + `PROJECT_STATE.md` + `git status`.
2. Pick the next task by priority: **uncommitted work first** → next unchecked task in the active wave
   → next wave → verification wave.
3. Present it: description · target file · success criteria · backpressure command · dependencies ·
   context to read. Then start on confirmation.
4. On completion: run backpressure → pass = commit + tick the box + go again; fail = fix, rerun.
   Blocked = surface the blocker + options (resolve / skip to next unblocked / ask), don't guess.

## Key principles

1. **Orchestrator stays light** — never exceed ~40% context; delegate heavy work to subagents.
2. **Fresh context per task** — each subagent starts clean with only task-specific info.
3. **Atomic commits** — one task = one commit, easy to revert.
4. **State lives in files** — `IMPLEMENTATION_PLAN.md` + `PROJECT_STATE.md` are the source of truth.
