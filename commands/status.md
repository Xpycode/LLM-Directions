# Project Status

Fast, plain-language status. Keep it short. **No commit SHAs, no internal codenames or jargon** —
say what something *means*, not what it's called.

**Detect mode:**
- `docs/PROJECT_STATE.md` exists → use `docs/` paths (installed project)
- else `./PROJECT_STATE.md` exists → use root paths (master repo)

**Read only what you need (stop early):**
1. `PROJECT_STATE.md` — this is the digest; it's almost always all you need.
2. The **first data row** of `sessions/_index.md` (most recent session). Do **not** read the whole file.
3. `TASKS.md` top section — only if it exists.

Do **not** read full session logs or `tasks-archive.md` unless the user asks to dig deeper.

**Old-shape check (offer, don't force):** if `PROJECT_STATE.md` is old-shape — has a
`## Active Decisions` section, or lacks both `## Now` and `## Recent`, or exceeds ~70 lines — add
one line after the status: *"This PROJECT_STATE is the old verbose shape (N lines). Want me to
migrate it to the lean digest?"* If yes, follow `<directions-master>/MIGRATE-PROJECT-STATE.md`.
Never migrate without asking — `/status` is read-only by default.

**Report — aim for ≤8 lines, plain English. Skip any line with nothing to say.**
- **Phase / focus** — one sentence: where we are + what's active.
- **Tasks** — one line `N/M sprint · X% overall`, only if `TASKS.md` exists.
- **Blockers** — name them, or `none`.
- **Last session** — one sentence on what got done, translated out of jargon (no SHAs).
- **Next** — one concrete suggested action.

**Style rules:**
- Translate technobabble. "Moved the sentinel" → "changed which file marks a project as set up."
- No commit hashes, file-path soup, or codenames unless the user used them first.
- Empty/clean field → two words (`Blockers: none`). Don't pad.

## Phase-Specific Reminder

If phase is **polish** or **shipping**, add one line:

> Run `/minimums` to check baseline features before release.

## Same-Folder Session Collision Check

Two Claude sessions open in the **same folder** share one git checkout (one HEAD) — if either
runs `git checkout`, it switches the branch for **both**, which is how a commit lands on the wrong
branch. Run the detector and surface the result:

```bash
bash ~/.claude/hooks/session-guard.sh 2>/dev/null \
  || bash /Users/sim/ProgrammingProjects/0-DIRECTIONS/__DIRECTIONS/hooks/session-guard.sh 2>/dev/null
```

(The first path is the per-Mac symlink from `hooks/install.sh`; the fallback is the master repo,
for when this Mac hasn't re-run install yet.)

- **No output** → no collision; say nothing (don't pad the report with "no collision").
- **A warning block** → show it. In plain language: *another Claude session is in this folder; you
  share one checkout. Coordinate git in one session, or split off with `/worktree`.* Worktrees are
  the clean fix — each gets its own branch. Two sessions in **different worktrees** are safe.

This is read-only — it inspects running processes, never touches git.
