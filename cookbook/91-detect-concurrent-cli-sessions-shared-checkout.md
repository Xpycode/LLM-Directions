## Git / Tooling — Detect concurrent CLI sessions sharing one git checkout (warn before the shared-HEAD collision)

**Source:** Directions master, 2026-06-11. Two Claude Code sessions were open in the same project folder; one ran `git checkout feature/theme-editor`, which moved HEAD for **both** sessions, so the other session's commit landed on the wrong branch. Built a warn-only guard that fires at session start and on `/status`.

**Use case:** Any time more than one long-lived CLI agent/session (Claude Code, an editor terminal, a TUI) can be open in the **same git working directory**. They share **one HEAD** — git keeps a single checked-out branch per working tree — so a `git checkout`/`switch`/`rebase` in one silently changes the branch under all the others, and a commit can land where you didn't intend. You want to *detect* the dangerous configuration and nudge toward the fix (a `git worktree`), without blocking anything or touching git.

**When to reach for it:** you run two agent sessions in one repo and occasionally find commits on a branch you didn't expect, with *no other machine involved* (this is the same-machine cousin of the cross-Mac duplicate-commit class). Also useful as a generic "is someone else already working here?" probe before an automated branch operation.

---

### Why git can't answer this — but the OS can

Git has **no concept of a session.** "Are two sessions in this folder?" is invisible to `git status`, hooks, or any git query. The naive trigger people reach for — *"is there a checkout?"* — is **useless**: every repo always has a HEAD, so that fires 100% of the time and becomes noise.

The real signal is **"is a second live session's working directory inside this same git working tree right now?"** That's an **operating-system** question — about running processes and their `cwd` — not a git question. So you answer it by inspecting processes:

```
pgrep the agent binary  →  each PID's cwd (lsof)  →  resolve to git worktree toplevel  →  group; warn if 2+ share one
```

---

### The detector (POSIX/macOS shell, warn-only, ~20 lines)

```bash
#!/bin/bash
# Warn when 2+ `claude` CLI sessions share ONE git working tree. Exits 0 always.
target="${1:-$PWD}"
here=$(git -C "$target" rev-parse --show-toplevel 2>/dev/null) || exit 0   # worktree toplevel
command -v pgrep >/dev/null 2>&1 && command -v lsof >/dev/null 2>&1 || exit 0

count=0
for pid in $(pgrep -x claude 2>/dev/null); do                  # -x = exact process name
  cwd=$(lsof -a -d cwd -p "$pid" -Fn 2>/dev/null | sed -n 's/^n//p' | head -1)
  [ -n "$cwd" ] || continue
  [ "$(git -C "$cwd" rev-parse --show-toplevel 2>/dev/null)" = "$here" ] && count=$((count+1))
done

[ "$count" -ge 2 ] || exit 0
echo "⚠️  $count sessions share '$(basename "$here")' — they share one HEAD."
echo "    A 'git checkout' in either switches the branch for BOTH. Isolate with:"
echo "        git worktree add ../$(basename "$here")-<name> -b <branch>"
```

Three load-bearing choices:

1. **`pgrep -x <name>`, not `pgrep -f`.** Match the **exact process name** (`claude`), not a substring of the command line. `-f` matches `claude` anywhere in argv — it would catch the GUI desktop app's `Claude Helper` renderer/utility procs, your own `grep claude`, any path containing "claude". Exact-name match isolates the actual CLI sessions. (Verify on your platform: `pgrep -fl <name>` once to see what the binary is actually called.)
2. **Resolve `cwd → git worktree toplevel` and group by that — this is what makes it worktree-aware.** `git rev-parse --show-toplevel` returns the **worktree's** path, so two sessions in *different worktrees of the same repo* resolve to *different* toplevels and **don't** trip the guard. That's exactly right: separate worktrees have separate HEADs and are the *safe* configuration you're steering people toward. Grouping by the repo's common `.git` dir instead would false-positive on the cure.
3. **Count ≥ 2, no self-exclusion needed.** At `SessionStart` your own process is already in the `pgrep` list, so "the second session opening" sees count 2 and warns; a lone session sees count 1 and stays silent.

---

### Why process-inspection beats a lock file

The obvious alternative — write a PID lockfile on start, delete on exit — **goes stale**: a crash/`kill -9` leaves a lock that blocks or false-warns forever, and in a Syncthing/multi-Mac setup a lockfile *inside the repo* syncs to the other machine and lies about which host it's on. Process inspection is **stateless and self-correcting**: it reads ground truth (who's actually running, where) every time, there's nothing to clean up, nothing to go stale, and it never touches the repo or git. Cost: one `pgrep` + a handful of `lsof` calls (<1s for a few PIDs) — cheap enough for a `SessionStart` hook.

---

### Wiring it in

- **Fire at `SessionStart`** so the second session is flagged the instant it opens, *before* anyone runs a checkout. If your start script is itself a **symlink** (e.g. `~/.claude/hooks/session-start.sh` → repo), resolve the symlink chain to find the sibling detector script — `dirname "$0"` points at the symlink's dir, not the repo:
  ```bash
  src="${BASH_SOURCE[0]}"; while [ -L "$src" ]; do
    l=$(readlink "$src"); case "$l" in /*) src="$l";; *) src="$(cd "$(dirname "$src")"&&pwd)/$l";; esac; done
  "$(cd "$(dirname "$src")"&&pwd)/session-guard.sh"
  ```
- **Also expose it on demand** (a `/status`-type command) with a stable path (`~/.claude/hooks/session-guard.sh`) plus a repo-path fallback for a machine that hasn't run the per-machine install yet.
- **Warn-only, never block.** Match the host's "remind, don't mutate" hook style — this is advice, not a gate. Pair it with a one-command **`git worktree add`** helper so the recommended fix is one step (the warning is wasted if the cure is firiction).

---

### Pitfalls

- **`pgrep -f` over-matches** (see above) — desktop-app helpers, your own grep, incidental path substrings. Use `-x`.
- **`lsof` cwd field parsing:** `lsof -a -d cwd -p PID -Fn` emits machine-readable fields; the `cwd` path is the line starting with `n` (strip the `n`). Don't scrape the human table format.
- **A session whose `cwd` is a *subdirectory*** of the repo still resolves correctly — `git -C "$subdir" rev-parse --show-toplevel` walks up to the same toplevel. Group by toplevel, not raw `cwd`.
- **Worktrees are single-machine / short-lived.** A worktree's internal `.git` is a **file** containing an **absolute** `gitdir:` path valid only on the machine that created it — a worktree dir that rides a file-sync tool (Syncthing) to another machine is a broken reference there. Create/use/remove in one sitting; let the *commits* (which travel via git) carry the work across machines. Don't conflate this with cross-machine sync discipline.
- **Generalizes beyond Claude.** Swap `pgrep -x claude` for any agent/REPL/TUI binary name to guard any tool where two instances can share a checkout.

---

### Composes with

- `37_multi-mac-discipline.md` **Rule 5** (the same-folder, same-Mac collision — this detector is its enforcement; Rules 1–4 are the orthogonal cross-Mac axis).
- A `/worktree` helper command (the one-step fix the warning points at).
- **#85** (phase-aware watchdog) and **#88** (fail2ban-vs-auth) — sibling "diagnose the *configuration*, don't just retry" shell-ops patterns.
