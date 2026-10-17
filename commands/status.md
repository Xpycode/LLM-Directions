# Project Status

Fast, plain-language status. **`/status` also absorbs `/context` and `/arrive`** via modes:

| `/status <arg>` | Mode | Does |
|---|---|---|
| (none) | **status** | the lean digest below — read-only, ≤8 lines |
| "full", "context" | **full** | status + last 3 sessions + last 3 decisions |
| "arrive", "sit down", "switch", "behind?" | **arrive** | the cross-Mac git handover (§Arrive) — fetch + verdict + where-I-left-off |

**No commit SHAs, no codenames or jargon** — say what something *means*, not what it's called.
Detect mode: `docs/PROJECT_STATE.md` exists → `docs/` paths; else `./PROJECT_STATE.md` (master repo).

## Resolve canonical procedures

`<master>` means the **absolute Directions master directory**, never the project or installed
command directory. Use the invoking Directions adapter's resolved master, otherwise the `Local
master:` value in the host's managed global instructions. For a repository-only invocation, the
real command source's repository root (the parent of `commands/`) is a candidate only if it contains
`commands/status.md` and `reference/status/`. Validate the chosen root contains both. If unresolved,
ask for the master location; do not guess relative to an installed `~/.claude/commands/status.md`
or copy references into projects. Expand every `<master>/…` path to that absolute root before
reading. Load conditional references only at their actual trigger below, not during initial core loading.
Resolve other shared guide/reference paths from that same master.

## Mode: status  (default)

**Read only what you need (stop early):**
1. `PROJECT_STATE.md` — the digest; almost always all you need.
2. The **first data row** of `sessions/_index.md` (most recent). **Never** the whole file.
3. `TASKS.md` top section — only if it exists.
4. For an active implementation plan, apply the execution reminder below; read only the relevant
   plan section and prerequisite/gate entries if the digest lacks enough evidence.

Don't read full session logs or `tasks-archive.md` unless asked.

**Report — aim for ≤8 lines, plain English. Skip any line with nothing to say.**
- **Phase / focus** — one sentence: where we are + what's active.
- **Tasks** — completed/total in the selected plan plus open external gates. Without a plan, report
  standalone TASKS status; do not combine backlog/archive totals into plan progress.
- **Deferred** — `N confirmed · M awaiting reproduction`, only when Backlog or Inbox is non-empty.
- **Blockers** — name them, or `none`.
- **Last session** — one sentence, translated out of jargon (no SHAs).
- **Next** — one concrete suggested action.

### Execution reminder (all modes, including full and arrive)

When a plan is active, use the **Next** line to remind the user of wave execution and its current
boundary. Prefer `Now → Execution` when present; otherwise use the linked plan (then root or
`docs/IMPLEMENTATION_PLAN.md`) and inspect the next task's prerequisites. Do not require consumers
to migrate their state format just to receive this reminder.

- Ready: `Next: /execute — continue Wave N: <plain-language work>.`
- Blocked, with independent work ready: `Next: /execute — <ready work>; <check> still blocks <dependent work>.`
- No ready work: `Next: Wave N blocked by <specific check>; resolve <input/action> before continuing.`
- Plan not yet approved for execution: `Next: review the plan, then /execute when ready.`
- Required acceptance remains after implementation: `Next: finish <acceptance check>; execution is not complete.`
- Plan complete: suggest its recorded next action; do not advertise another implementation wave.

If readiness cannot be established from available records, say so and suggest reviewing the plan;
do not invent a wave number or imply that a missing gate passed. Keep the lean report within its
normal budget by replacing the generic Next line, not appending a second checklist. This is read-only:
showing `/execute` never starts work, grants authorization or runs `/log`.
If counts, plan selection or legacy mirrors disagree, read the master's `reference/task-state.md`;
report uncertainty without migrating during read-only status. Follow the Current handoff pointer
instead of treating all historical Resume headings as current.

**Style:** translate technobabble ("moved the sentinel" → "changed which file marks a project as set
up"). No hashes / path-soup / codenames unless the user used them first. Empty field → two words
(`Blockers: none`), don't pad.

**Old-shape check (offer, don't force):** if `PROJECT_STATE.md` has a `## Active Decisions` section,
or is **missing either `## Now` or `## Recent`**, or its **`## Now` exceeds ~30 lines**, or the whole
file exceeds **~250 lines** (a loose backstop for bloat outside those sections), add one line:
*"`Now` has grown to N lines (retired waves are probably still in it) — migrate to the lean digest?"*
If yes → `<directions-master>/MIGRATE-PROJECT-STATE.md`. Never migrate without asking — `/status` is
read-only by default.

**Measure `Now`, not the whole file.** `Infrastructure`, `Backlog`, `Risks` and `Detail` are
legitimately long and are not rot; a correctly-migrated digest can exceed 100 lines and still be
healthy. Raw file length fires on correct output, so it gets ignored — see `/log` step 2 for the
regrowth this replaced. A `Recent` over ~5 entries is a **prune** (`/log` step 2 owns it), never a
reason to offer a migration.

**Phase reminder:** if phase is **polish** or **shipping**, add: *"Run `/check ship` before release."*

## Mode: full  (adds the old `/context`)

After the status lines, append (one line each, "Not found" if a file is absent):
- **Recent sessions** — last 3 from `sessions/_index.md`.
- **Recent decisions** — last 3 titles from `decisions.md`.

## Mode: arrive  (adds the old `/arrive` — cross-Mac handover)

Only in **arrive** mode (including its aliases), read `<master>/reference/status/arrive.md`
completely. It verifies repository identity before remote/fetch claims, fetches and reports; never
pulls/commits/switches without asking. Any authorized mutation also requires
`<master>/37_multi-mac-discipline.md` Rule 5.

## Same-folder session collision check  (triggered)

Ordinary read-only **status/full with no known concurrency** skips detection and omits collision
status. For **arrive**, **known concurrent sessions in any mode**, or **before a branch, checkout
or worktree mutation**, read `<master>/reference/status/collision.md` completely. Preserve known
risk even if detection is silent. Before any mutation, apply `<master>/37_multi-mac-discipline.md`
Rule 5 (including merge/rebase/pull and recovery). Status never authorizes a mutation.
The existing **SessionStart hook is unchanged**; narrowing status does not disable startup checks.

Source: `37_multi-mac-discipline.md`, `hooks/session-start.sh` (same fetch logic), `hooks/session-guard.sh`.
