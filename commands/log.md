# Session Log

Wrap up the current session: write the session log + sync state, ready to clear or switch Macs.

> **In practice `/log` is the last action of a session** (measured: 69/69 invocations across the
> active projects were session-enders, and the "what are we working on?" question was inferred —
> never asked — every time). Treat it as a session-close, not a mid-session note.

## Wrap-up mode — read the command argument FIRST

The argument is almost never a goal; it's the **wrap-up mode**, and it changes what the log must
contain. Detect it and adjust — do **not** ask which mode when the arg already says:

| Arg contains… | Mode | The log MUST… |
|---------------|------|---------------|
| "clear", "next session", "for next time" | **pre-clear** | end with a **Resume block**: uncommitted work, exact next pickup point, any half-done edit. The next session starts cold. |
| "switch Macs", "handoff", "other Mac", "depart" | **Mac-handoff** | include a **Sync block**: commit + push state, unpushed commits, current branch, "what the other Mac needs to pull". **Verify the tree is clean / pushed** before declaring done. (Overlaps `/depart`.) |
| (no arg, or "log it", "just log") | **plain** | a normal log, no resume/sync ceremony. |

If no arg is given, default to **plain** — do not ask.

## Write the log

1. Detect path mode: `docs/sessions/` exists → use `docs/` paths; else `./sessions/` (master repo).
2. Create today's file `sessions/YYYY-MM-DD.md` (actual date). If today's log exists, **append** /
   refresh it rather than duplicating — and if it's already comprehensive, say so instead of redoing it.
3. Use this template:

```markdown
# Session: [DATE]

## Goal
[INFER from the work just completed — the log is written after the fact, so the goal is already
visible in context. Do NOT ask the user. Ask a single clarifying question ONLY if the session had
no coherent thread (several unrelated tasks) AND the arg gives no framing — e.g.
"Frame the log around X, or list them separately?"]

## Progress
- [What actually happened, plain language]

## Decisions
- [Any architectural/design decisions — also log to decisions.md if significant]

## Next
- [What to do next time]
## Resume        ← pre-clear mode only
- [Uncommitted work + exact pickup point]
## Sync          ← Mac-handoff mode only
- [Push state, unpushed commits, branch, what the other Mac pulls]
```

4. Update `sessions/_index.md` with a row for this session.

## Then — silent defaults, not questions

Run these automatically and **report** the result; do not ask permission for each:

- **Sync PROJECT_STATE.md** — always do it (a stale snapshot is the failure case, especially when
  clearing/switching). Update only what changed: Current Focus (if it shifted), Last Session (always),
  Blockers (new/resolved), Next Actions, Key Decisions (summary + link to `decisions.md`). Keep it a
  **current snapshot**, not history. Report "Synced PROJECT_STATE." — don't ask "Should I sync?".

- **Cookbook check** — only surface it if a pattern actually emerged this session (trigger phrases:
  "finally got X working", "figured out how to…", "this pattern works well", "copied from [project]",
  or a reusable window/export/picker/lifecycle pattern). If one did, offer `/cookbook add`. If not,
  **skip silently** — don't ask the open-ended "did this produce a pattern?" question.

- **Archive completed tasks** (skip if no `TASKS.md` or nothing checked):
  1. Read `TASKS.md` Current Sprint; find `- [x]` items.
  2. Move them to `tasks-archive.md` Completed (top), dated `(YYYY-MM-DD)`; bump "Total archived";
     update "Last updated".
  3. Remove them from TASKS.md Current Sprint.
  4. Update the PROJECT_STATE progress bar: `Progress = (archived + current_checked) / (backlog +
     current + archived) × 100`, format `[##########..........] 50%`.
  Report "Archived [N] tasks. Progress: [X]%" only if something was archived.

## Note on the CLEAR/EXIT ambiguity

`/log` writes a log; it does **not** clear or exit the session itself. When the user pairs it with
"clear"/"switch Macs", that's the *wrap-up mode* above — prepare the log for that, but leave the
actual `/clear` or Mac switch to the user.
