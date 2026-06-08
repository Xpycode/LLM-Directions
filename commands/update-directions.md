# Update Directions

Pull the latest Directions master and refresh the **global** config + commands. Under the
**read-on-demand model**, universal docs are NOT copied into projects — so this command's job in a
consumer project is to **remove** any stale copied docs, not add new ones.

> **Model reminder:** the universal guidance docs (`00`–`61`) live only in the master repo and are
> read on demand via the **Directions Index** in the global `~/.claude/CLAUDE.md`. Copies inside a
> project drift and are pure liability. See `sessions/2026-06-08.md`.

## Step 1: Find Directions Master

Check these locations in order:
1. The path in `~/.claude/CLAUDE.md` under "Local master:" / the Directions Index base path
2. Default: `/Users/sim/ProgrammingProjects/0-DIRECTIONS/__DIRECTIONS`

## Step 2: Pull Latest

```bash
cd <directions-master> && git pull origin main
```

If there are uncommitted local changes in the master, warn the user before pulling.

## Step 3: Refresh Global (~/.claude/)

```bash
mkdir -p ~/.claude/commands

# Command definitions are global — keep them current
cp <directions-master>/commands/*.md ~/.claude/commands/

# Regenerate the Directions Index from the docs' TRIGGERS headers (can't drift)
<directions-master>/scripts/gen-directions-index.sh --write ~/.claude/CLAUDE.md

# Compare global config against the template (do NOT auto-overwrite — it has machine-specific paths
# and personal sections like Performer Voices)
diff -q <directions-master>/CLAUDE-GLOBAL-TEMPLATE.md ~/.claude/CLAUDE.md
```

If `CLAUDE.md` differs in ways beyond the Index/paths, ask before changing anything:
> "Your ~/.claude/CLAUDE.md has customizations. Want me to: 1. Show the diff  2. Merge specific
> sections  3. Leave it (Index already refreshed)."

## Step 4: Clean the Current Project (remove copied universal docs)

Only if the current project has Directions (`docs/PROJECT_STATE.md` exists).

**The migration:** delete the redundant copied universal docs and any copied command/skill/template
mirrors. Keep only project-specific files. Everything removed is still in the master + git history.

```bash
# SAFETY: ensure the project's working tree is clean first, so the deletion is one reviewable commit
git -C . status --porcelain   # expect empty; if not, commit/stash before proceeding

# Remove copied universal reference docs (00–61) — now read on demand from the master
git rm -q docs/[0-9][0-9]_*.md 2>/dev/null || rm -f docs/[0-9][0-9]_*.md

# Remove copied system/meta docs and tooling mirrors that belong only in the master
for f in 00_base.md AGENTS.md CLAUDE-GLOBAL-TEMPLATE.md Directions-CURRICULUM.md \
         IMPLEMENTATION_PLAN-template.md PATTERNS-COOKBOOK.md README.md LICENSE \
         docs-browser.html docs.sh install-directions.sh; do
  git rm -q "docs/$f" 2>/dev/null || rm -f "docs/$f"
done
git rm -q -r docs/commands docs/skills docs/cookbook docs/mcp-templates docs/hooks docs/scripts 2>/dev/null || \
  rm -rf docs/commands docs/skills docs/cookbook docs/mcp-templates docs/hooks docs/scripts
```

**NEVER touch (project-specific — the only things that should remain in `docs/`):**
- `docs/PROJECT_STATE.md`   (project state + sentinel)
- `docs/decisions.md`       (project decision history)
- `docs/sessions/*`         (session logs + `_index.md`)
- `docs/glossary.md`        (project-specific terms, if present)
- `CLAUDE.md` in the project root (project-specific instructions)

If a project *also* uses a cookbook reference, it reads the master's `PATTERNS-COOKBOOK.md` on
demand (Pattern Cookbook block in global CLAUDE.md) — it is not copied either.

## Step 5: Commit the Cleanup (per project)

```bash
git add -A
git commit -m "chore(directions): drop copied universal docs — read-on-demand via global Index

Universal docs (00–61) now live only in the Directions master and are read
on demand via the Directions Index in ~/.claude/CLAUDE.md. Removing the stale
local copies; project-specific docs (PROJECT_STATE, decisions, sessions) kept."
```

Solo-dev workflow: commit to `main` locally (branch first if the project's convention requires it).
Do **not** open a PR.

## Step 6: Summary

```bash
git -C <directions-master> log --oneline -5     # what's new in master
echo "Remaining in docs/ (should be project-specific only):"
ls docs/
```

## Step 7: Remind About Restart

If global hooks/scripts/plugin changed in the pull, remind the user:
> "Hooks or scripts were updated. Restart Claude Code for changes to take effect."

Check whether these changed: `hooks/hooks.json`, `scripts/*.py`, `.claude-plugin/plugin.json`.

---

## Quick Reference (read-on-demand model)

| Item | Global (~/.claude/) | Project (./docs/) |
|------|---------------------|-------------------|
| `commands/*.md` | ✓ refresh | ✗ (removed if copied) |
| Directions Index | ✓ regenerate via script | ✗ |
| `[0-9][0-9]_*.md` universal docs | ✗ (master only) | ✗ **removed** (read on demand) |
| `skills/*`, cookbook, templates | ✗ (master only) | ✗ **removed** if copied |
| `PROJECT_STATE.md` | ✗ | ✓ keep (never touch) |
| `decisions.md` | ✗ | ✓ keep (never touch) |
| `sessions/*`, `glossary.md` | ✗ | ✓ keep (never touch) |

**Net effect:** one source of truth (the master) + a generated Index. Consumer `docs/` folders hold
only project-specific state.
