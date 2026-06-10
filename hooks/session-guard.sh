#!/bin/bash
#
# session-guard.sh — warn when 2+ Claude CLI sessions share ONE working directory.
#
# THE HAZARD: two `claude` sessions open in the same folder share a single git
# checkout — git keeps one HEAD per working directory. If either session runs
# `git checkout`, it switches the branch for BOTH, and a commit from one session
# can land on the branch the other just switched to (the theme-editor cross-commit
# incident). git worktrees are the fix: each worktree directory has its OWN HEAD,
# so two sessions in DIFFERENT worktrees of the same repo are SAFE and do not trip
# this guard — they resolve to different toplevels.
#
# This is warn-only: it never blocks and never touches git. Detection is purely
# local process inspection (pgrep + lsof), so there is nothing to go stale and no
# interaction with Syncthing / the multi-Mac flow. See 37_multi-mac-discipline.md.
#
# Usage:  session-guard.sh [dir]      # dir defaults to $PWD
# Output: prints a warning block to stdout IFF a same-folder collision is found.
#         Exits 0 always (so it's safe to chain in a SessionStart hook).

target="${1:-$PWD}"

# Resolve to the worktree toplevel. Worktree-aware on purpose: two worktrees of the
# same repo resolve to DIFFERENT toplevels, so parallel work across worktrees (the
# thing we're recommending) never false-positives.
here=$(git -C "$target" rev-parse --show-toplevel 2>/dev/null) || exit 0
[ -n "$here" ] || exit 0

# Need both tools; degrade silently if either is missing.
command -v pgrep >/dev/null 2>&1 || exit 0
command -v lsof  >/dev/null 2>&1 || exit 0

# Count claude CLI sessions whose current directory sits in this same worktree.
count=0
others=""
for pid in $(pgrep -x claude 2>/dev/null); do
  cwd=$(lsof -a -d cwd -p "$pid" -Fn 2>/dev/null | sed -n 's/^n//p' | head -1)
  [ -n "$cwd" ] || continue
  top=$(git -C "$cwd" rev-parse --show-toplevel 2>/dev/null)
  if [ "$top" = "$here" ]; then
    count=$((count + 1))
    others="$others $pid"
  fi
done

# 0 or 1 session here → nothing to warn about.
[ "$count" -ge 2 ] || exit 0

repo=$(basename "$here")
branch=$(git -C "$here" rev-parse --abbrev-ref HEAD 2>/dev/null)

cat <<EOF
⚠️  Session collision — $count Claude sessions are working in '$repo'
    ($here, currently on '${branch:-?}').
    They share ONE git checkout: if either runs 'git checkout', the branch
    switches for BOTH — that's how a commit lands on the wrong branch.

    Safe options:
      • Keep all git actions in ONE of the sessions, OR
      • Isolate this session in its own worktree (separate HEAD):
            /worktree                      (helper — sets it up for you)
        or manually:
            git worktree add ../$repo-<name> -b <branch-name>
            cd ../$repo-<name>             (then point the 2nd session here)

    Two sessions in DIFFERENT worktrees are safe — they don't share a HEAD.
EOF
exit 0
