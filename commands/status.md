# Project Status

Fast, plain-language status. **`/status` also absorbs `/context` and `/arrive`** via modes:

| `/status <arg>` | Mode | Does |
|---|---|---|
| (none) | **status** | the lean digest below — read-only, ≤8 lines |
| "full", "context" | **full** | status + last 3 sessions + last 3 decisions |
| "arrive", "sit down", "switch", "behind?" | **arrive** | the cross-Mac git handover (§Arrive) — fetch + verdict + where-I-left-off |

**No commit SHAs, no codenames or jargon** — say what something *means*, not what it's called.
Detect mode: `docs/PROJECT_STATE.md` exists → `docs/` paths; else `./PROJECT_STATE.md` (master repo).

## Mode: status  (default)

**Read only what you need (stop early):**
1. `PROJECT_STATE.md` — the digest; almost always all you need.
2. The **first data row** of `sessions/_index.md` (most recent). **Never** the whole file.
3. `TASKS.md` top section — only if it exists.

Don't read full session logs or `tasks-archive.md` unless asked.

**Report — aim for ≤8 lines, plain English. Skip any line with nothing to say.**
- **Phase / focus** — one sentence: where we are + what's active.
- **Tasks** — `N/M sprint · X% overall`, only if `TASKS.md` exists.
- **Blockers** — name them, or `none`.
- **Last session** — one sentence, translated out of jargon (no SHAs).
- **Next** — one concrete suggested action.

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

Run when you **sit down at a Mac**, especially after switching from the other one and letting
Syncthing settle. The per-project, human-readable version of the session-start git pre-flight.
**Read-only** — it fetches and reports; never pulls/commits/switches without asking. Pairs with
`/log` Mac-handoff mode (which stamps each commit with the Mac that pushed it).

1. **Who am I?**
   ```bash
   MAC=$(cat ~/.claude/this-mac 2>/dev/null || scutil --get LocalHostName 2>/dev/null || hostname -s)
   ```
   `~/.claude/this-mac` is a one-line per-machine label (e.g. `M1 Max`), kept **outside** Syncthing so
   it never travels — same path, different content per Mac. Missing → the Mac's own name is used.
2. **git + remote?** `git rev-parse --is-inside-work-tree` and `git remote get-url origin`.
   - No git → "files travel by Syncthing only; nothing to compare." Skip to 4.
   - git but no remote → "history has no GitHub remote, so I can't see the other Mac's work — add one?" Skip to 4.
3. **Fetch and read the other Mac's last work (read-only):**
   ```bash
   git fetch --quiet 2>/dev/null; git status -sb | head -1
   git log -1 @{u} --format='%cr%n%an%n%s' 2>/dev/null
   git log -1 @{u} --format='%(trailers:key=Handoff-from,valueonly)' 2>/dev/null
   ```
   `Handoff-from:` is the Mac `/log` stamped in (immutable, conflict-free). Empty → predates it; report author/date.
   **Plain verdict (no SHAs):**
   - **up to date** → "✓ Up to date. Last: <Mac>, <when> — \"<subject>\". Good to start."
   - **behind N** → "⚠ <Mac> pushed <when> — you're N behind. Pull first?" Offer `git pull --ff-only`; pull only on **yes**.
   - **ahead M** → "M commits here not pushed (prior session on this Mac). Fine to keep working — `/log` before you leave."
   - **diverged (ahead+behind)** → "⚠ Both Macs have unpushed work — diverged. Don't pull blindly." → `37_multi-mac-discipline.md` Rule 1. No auto-pull/reset.
4. **Where did I leave off?** Read `PROJECT_STATE.md`; show just **Now → Focus** and **Now → Next** (one line each).
5. **Collision check** (light) — see §Same-folder below.

## Same-folder session collision check  (all modes)

Two Claude sessions in the **same folder** share one git checkout (one HEAD) — if either runs
`git checkout`, it switches the branch for **both**. Run the detector and surface the result:

```bash
bash ~/.claude/hooks/session-guard.sh 2>/dev/null \
  || bash /Users/sim/ProgrammingProjects/0-DIRECTIONS/__DIRECTIONS/hooks/session-guard.sh 2>/dev/null
```

- **No output** → no collision; say nothing (don't pad the report).
- **A warning block** → show it plainly: *another Claude session shares this checkout; coordinate git
  in one session, or split off with `/worktree`.* Two sessions in **different worktrees** are safe.

Read-only — it inspects running processes, never touches git.

Source: `37_multi-mac-discipline.md`, `hooks/session-start.sh` (same fetch logic), `hooks/session-guard.sh`.
