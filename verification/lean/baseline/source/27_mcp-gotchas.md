<!--
TRIGGERS: codebase-memory-mcp, runaway CPU, MCP indexing, umbrella folder, $HOME, project root, index_repository, codebase-memory, mcp gotchas, mcp guard, PreToolUse hook
PHASE: any
LOAD: when MCP CPU/RAM looks wrong, or before installing a new cwd-sensitive MCP
-->

# MCP Gotchas

*Things that go wrong with MCP servers that aren't bugs — just MCPs faithfully doing what was asked from the wrong directory.*

---

## codebase-memory-mcp: umbrella-cwd CPU runaway

### Symptom

A single `codebase-memory-mcp` process at hundreds of % CPU, multi-GB resident memory, dozens of threads. Activity Monitor / `top` / `htop` shows it dwarfing every other process. The CPU graph stays pegged for tens of minutes.

### Evidence

Look in `~/.cache/codebase-memory-mcp/` (or wherever `CBM_CACHE_DIR` points). DB filenames mirror the directory you launched Claude Code from, with `/` rewritten to `-`:

| DB filename | Came from launching Claude Code in… | Typical size |
|---|---|---|
| `Users-you.db` | `$HOME` | 1–10 GB |
| `Users-you-Code.db` | a top-level code folder | 0.5–5 GB |
| `Users-you-Code-Group.db` | a single-level umbrella | 100 MB – 1 GB |
| `Users-you-Code-Group-Project.db` | a real project root | 1–50 MB |

If the largest file is one of the first three rows, you've hit the gotcha.

A `sample` of the live process will show the hot thread inside `pipeline.(*Pipeline).resolveFileCallsCBM` → `(*FunctionRegistry).resolveViaImportMap`, with `runtime.memmove`, `runtime.concatstring2`, and `maps.Iter.Next` near the top. That's the call-graph resolution pass scaling roughly as (call sites × import entries) — fine for a project, catastrophic for `$HOME`.

### Root cause

The four `codebase-memory-*` skills shipped with the MCP (`exploring`, `quality`, `tracing`, `reference`) each begin with a step that says, paraphrased:

> If the project isn't in `list_projects` yet, call `index_repository(repo_path=<cwd>)`.

The skill has no opinion about what counts as a project. When Claude Code is launched from `$HOME` or a folder containing many projects, that folder becomes the "project," and the indexer faithfully walks every file under it into a SQLite knowledge graph.

The MCP itself isn't broken — it's doing exactly what it was asked. The footgun is the **launch directory** combined with the skill's auto-index step.

### Why this is easy to trigger

- Starting a session from `~` to "look at something quickly."
- Working inside an Xcode/VSCode workspace whose root contains many projects.
- Using a monorepo-style folder that aggregates multiple service repos.
- Forgetting which directory the terminal is in.

### Fix: PreToolUse hook on `index_repository`

The cheapest safety rail is a Claude Code PreToolUse hook that gates the `mcp__codebase-memory-mcp__index_repository` tool. The hook auto-approves calls whose `repo_path` matches your real project layout, and forces an "ask" prompt with a warning for everything else.

A reusable, templated guard lives in this repo at `hooks/mcp-guards/codebase-memory-guard.sh`. See `hooks/mcp-guards/README.md` for the full install snippet; the short version:

1. Copy the guard to `~/.claude/hooks/`, `chmod +x` it.
2. Edit `APPROVED_RE` at the top to match your projects layout. The default rule is "at least two path segments deep under a single root," which excludes umbrella folders.
3. Add this block to `~/.claude/settings.json` under `hooks.PreToolUse` (merge with existing entries):

   ```json
   {
     "matcher": "mcp__codebase-memory-mcp__index_repository",
     "hooks": [
       { "type": "command", "command": "~/.claude/hooks/codebase-memory-guard.sh" }
     ]
   }
   ```

4. Restart Claude Code (or open `/hooks` once to reload).

After install, every `index_repository` call goes through the guard. Approved paths run silently; everything else surfaces a warning that names the requested path and explains why it's not auto-approved.

### Customizing what counts as "approved"

The guard reduces "where is it safe to index?" to a single regex at the top of the script:

```bash
APPROVED_RE='^/ABSOLUTE/PATH/TO/PROJECTS_ROOT/[^/]+/[^/]+(/|$)'
```

Examples for common layouts:

```bash
# One projects root, group/project subdirs
APPROVED_RE='^/Users/you/Code/[^/]+/[^/]+(/|$)'

# Two projects roots
APPROVED_RE='^(/Users/you/Code|/Users/you/Work)/[^/]+/[^/]+(/|$)'

# Flat — projects directly under ~/Code (no group level)
APPROVED_RE='^/Users/you/Code/[^/]+(/|$)'
```

Test changes with the pipe-test recipe in `hooks/mcp-guards/README.md` before relying on them.

### Cleaning up existing umbrella DBs

Use the MCP's own delete tool when possible — it knows the canonical filename and writes a clean shutdown:

```
mcp__codebase-memory-mcp__delete_project(project="<umbrella-name>")
```

If the MCP is already misbehaving (CPU pegged, refusing tool calls), a manual cleanup works:

1. Stop the runaway process: `kill <pid>` (use SIGTERM, not -9, so SQLite can flush its WALs).
2. Delete the umbrella DB and its sidecars:
   ```bash
   cd ~/.cache/codebase-memory-mcp
   rm Users-you.db Users-you.db-shm Users-you.db-wal     # repeat per umbrella
   ```
3. Claude Code will respawn the MCP on the next tool call. With the guard installed, it won't re-create the umbrella DB.

### Recommended version

Use codebase-memory-mcp ≥ **v0.4.10**. That release fixed an unrelated watcher OOM (the MCP used to scan every DB on startup; it now uses an explicit watch list). It does **not** address the umbrella-cwd footgun — the guard is still required.

### See also: Serena

[Serena MCP](https://github.com/oraios/serena) is invoked with `--project-from-cwd` in most reference configs, so it picks up the same launch-directory signal. We have not observed Serena producing umbrella indices in practice, but if its memory or CPU jump after launching from a non-project directory, the same guard pattern applies (`hooks/mcp-guards/`, new script, matcher = `mcp__serena__activate_project` or whichever entry tool is suspected).

### Upstream links

- Repo: [github.com/DeusData/codebase-memory-mcp](https://github.com/DeusData/codebase-memory-mcp)
- Docs: [deusdata.github.io/codebase-memory-mcp](https://deusdata.github.io/codebase-memory-mcp/)
- Releases: [github.com/DeusData/codebase-memory-mcp/releases](https://github.com/DeusData/codebase-memory-mcp/releases)

---

*Written after a real incident on Apple Silicon with codebase-memory-mcp v0.4.6 — 837% CPU, 21 GB resident, three umbrella DBs totalling 5.6 GB. Guard installed, problem resolved.*
