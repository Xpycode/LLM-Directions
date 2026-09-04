# Directions

Show the available commands, or update Directions. **`/directions` absorbs `/update-directions`.**

| `/directions <arg>` | Mode |
|---|---|
| (none), "list", "help" | **list** — show the command catalog |
| "update", "pull", "sync" | **update** — pull master + refresh global config |

## Mode: list  (generated — never hand-maintained)

Do **not** paste a hardcoded table (four hand-maintained catalogs drifted and all four went wrong —
that's why this is generated). Build the list live from the command files:

```bash
# from the Directions master (Claude may also use its deployed ~/.claude/commands copy)
for f in commands/*.md; do
  name=$(basename "$f" .md)
  # the one-line purpose is the file's first non-heading line
  desc=$(grep -m1 -vE '^\s*(#|$)' "$f")
  printf '/%s — %s\n' "$name" "$desc"
done
```

Present them grouped by theme, using the descriptions read from the files:
- **Workflow:** `/setup` · `/status` (+ `context`, `arrive` modes) · `/log` (end-of-session: close,
  depart, handoff, phase, compound, blockers) · `/decide` · `/learned`
- **Plan & build:** `/spec` (+ `deep`, `examples`) · `/make-plan` · `/execute` (+ `next`)
- **Quality:** `/check` (`code` | `ship` | `security`) · `/cookbook`
- **Isolation & testing:** `/worktree` · `/test-app`
- **Meta:** `/directions` (this, + `update`)

Because the list is read from `commands/` at run time, it always matches what actually exists.

## Mode: update  (the old `/update-directions`)

Pull the latest master and refresh the **active tool's** global adapter. Universal docs stay in the
master and are read on demand through the generated Directions Index; a consumer-project update
removes stale copies, it never adds them.

1. **Find master:**
   - Codex → resolve the active Directions skill symlink, then the `Local master:` value in
     `$CODEX_HOME/AGENTS.md` (default `~/.codex/AGENTS.md`).
   - Claude Code → read `Local master:` from `~/.claude/CLAUDE.md`.
   - Last fallback → `/Users/sim/ProgrammingProjects/0-DIRECTIONS/__DIRECTIONS` when it exists.
   Verify that the result contains `commands/` before continuing.
2. **Inspect before pulling** — show `git -C <master> status --short` and the current branch. If the
   tree is dirty, warn and stop for a decision; do not mix a pull with unexplained local changes.
3. **Pull** — after a clean-tree check, run `git -C <master> pull --ff-only origin main`.
4. **Refresh the active adapter:**
   - Codex → run `bash <master>/deploy-codex.sh --dry-run`, show the result, then ask before running
     `bash <master>/deploy-codex.sh` because it updates the active Codex home (`skills/` and
     `AGENTS.md`).
   - Claude Code → run `bash <master>/redeploy.sh --dry-run`, show the result, then ask before running
     `bash <master>/redeploy.sh` because it updates `~/.claude`.
   - If both tools are intentionally in use, offer both deployers; do not assume dual installation.
5. **Clean a consumer project only when stale copies actually exist.** Preserve
   `docs/PROJECT_STATE.md`, `docs/decisions.md`, `docs/sessions/*`, `docs/glossary.md`, root
   `AGENTS.md`, and root `CLAUDE.md`. Show the exact copied universal files first. Remove them only
   from a clean tree and with confirmation, then offer the commit
   `chore(directions): drop copied universal docs — read on demand`.
6. **Reload reminder** — if Codex global guidance, skills, or hooks changed, start a new Codex
   session. If Claude commands, hooks, or plugin files changed, restart Claude Code.

**Net effect:** one procedural source (the master) + thin tool adapters + a generated Index;
consumer `docs/` folders hold only project-specific state. See `sessions/2026-06-08.md` for why
copies drift.
