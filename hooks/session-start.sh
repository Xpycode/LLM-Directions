#!/bin/bash

# --- Multi-Mac pre-flight (37_multi-mac-discipline.md, Rule 1) -----------------
# This codebase is edited from more than one Mac. Fetch read-only on every
# session start and report sync state BEFORE any work, so we never redo what
# another Mac already pushed (the 2026-06-08 duplicate-commit incident).
# Read-only: this never merges, pulls, or touches the working tree.
if git rev-parse --is-inside-work-tree >/dev/null 2>&1 && git remote | grep -q .; then
  # Cap the fetch so a slow/offline network can't hang session start.
  if command -v timeout >/dev/null 2>&1; then
    timeout 10 git fetch --quiet >/dev/null 2>&1
  elif command -v gtimeout >/dev/null 2>&1; then
    gtimeout 10 git fetch --quiet >/dev/null 2>&1
  else
    git fetch --quiet >/dev/null 2>&1
  fi

  upstream=$(git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null)
  if [ -n "$upstream" ]; then
    branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)
    # left = commits on upstream not local (behind); right = local not on upstream (ahead)
    counts=$(git rev-list --left-right --count "@{u}...HEAD" 2>/dev/null)
    behind=$(printf '%s' "$counts" | awk '{print $1+0}')
    ahead=$(printf '%s' "$counts" | awk '{print $2+0}')
    echo "— Multi-Mac pre-flight —"
    if [ "${behind:-0}" -gt 0 ] && [ "${ahead:-0}" -gt 0 ]; then
      echo "⚠️  '$branch' has DIVERGED from $upstream: $ahead local / $behind remote."
      echo "    Do NOT push. Reconcile first (git fetch already done; see 37_multi-mac-discipline.md)."
    elif [ "${behind:-0}" -gt 0 ]; then
      echo "⚠️  origin has $behind commit(s) you don't have on '$branch'."
      echo "    PULL before editing — another Mac may have already done this work."
    elif [ "${ahead:-0}" -gt 0 ]; then
      echo "ℹ️  '$branch' is ahead of $upstream by $ahead unpushed commit(s)."
    else
      echo "✓ '$branch' in sync with $upstream."
    fi
    echo
  fi
fi
# -----------------------------------------------------------------------------

cat << 'EOF'

What would you like to do?

| Command     | What it does                                      |
|-------------|---------------------------------------------------|
| /setup      | Detect project state, set up or migrate Directions|
| /status     | Check current phase, focus, blockers, last session|
| /log        | Create or update today's session log              |
| /decide     | Record an architectural/design decision           |
| /interview  | Run the full discovery interview                  |
| /learned    | Add a term to your personal glossary              |
| /reorg      | Reorganize folder structure (numbered folders)    |
| /execute    | Wave-based parallel execution (fresh contexts)    |
| /update-directions | Pull latest and sync to project             |

**More:** /phase, /context, /handoff, /blockers, /review, /minimums, /new-feature

**Context tip:** Use /execute for implementation (spawns fresh subagents).
Create RESUME.md if ending mid-task. Keep PROJECT_STATE.md under 80 lines.

Or just tell me what you're working on.

EOF

exit 0
