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
# from the Directions master (or ~/.claude/commands/ on a deployed Mac)
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

Pull the latest master and refresh the **global** config. Under the read-on-demand model, universal
docs live only in the master and are read on demand via the Directions Index in `~/.claude/CLAUDE.md`
— so in a *consumer project* this **removes** stale copied docs, it doesn't add any.

1. **Find master** — the "Local master:" path in `~/.claude/CLAUDE.md`, else
   `/Users/sim/ProgrammingProjects/0-DIRECTIONS/__DIRECTIONS`.
2. **Pull** — `cd <master> && git pull origin main` (warn first if the master has uncommitted changes).
3. **Refresh global `~/.claude/`:**
   ```bash
   mkdir -p ~/.claude/commands
   cp <master>/commands/*.md ~/.claude/commands/                       # commands are global — keep current
   <master>/scripts/gen-directions-index.sh --write ~/.claude/CLAUDE.md # regenerate the Index (can't drift)
   diff -q <master>/CLAUDE-GLOBAL-TEMPLATE.md ~/.claude/CLAUDE.md        # compare — do NOT auto-overwrite
   ```
   If `CLAUDE.md` differs beyond Index/paths, ask before changing (it has machine-specific paths +
   personal sections): show the diff / merge specific sections / leave it (Index already refreshed).
4. **Clean the current project** (only if `docs/PROJECT_STATE.md` exists): ensure the tree is clean, then
   `git rm docs/[0-9][0-9]_*.md` and any copied command/skill/cookbook/template mirrors. **Never touch**
   `docs/PROJECT_STATE.md`, `docs/decisions.md`, `docs/sessions/*`, `docs/glossary.md`, or the project's
   root `CLAUDE.md`. Commit: `chore(directions): drop copied universal docs — read-on-demand via global Index`.
5. **Restart reminder** — if the pull changed `hooks/hooks.json`, `scripts/*.py`, or
   `.claude-plugin/plugin.json`, tell the user to restart Claude Code for it to take effect.

**Net effect:** one source of truth (the master) + a generated Index; consumer `docs/` folders hold
only project-specific state. See `sessions/2026-06-08.md` for why copies drift.
