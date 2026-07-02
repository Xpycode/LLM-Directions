#!/bin/bash

# Stop hook — nudge to commit + push before walking away from a multi-Mac repo.
#
# WHY a Stop hook: SessionEnd output is invisible (the session is already gone) and
# SessionStart only fires at the start. Stop is the only event that fires while the
# user is still looking at the transcript. But it fires after EVERY assistant turn,
# so this script must be quiet:
#   1. It speaks only when there is real uncommitted OR unpushed work.
#   2. It DEBOUNCES — at most once per ~20 min per session (timestamp file).
#   3. It NEVER blocks (no decision:block) — it's a reminder, not a gate.
#
# Surfaces via the `systemMessage` JSON field (the one Stop-hook channel the user sees).
# Pairs with hooks/session-start.sh (start-of-session detection) and /log
# (the confirmed commit+push action). See 37_multi-mac-discipline.md.

input=$(cat)
session_id=$(printf '%s' "$input" | jq -r '.session_id // "default"' 2>/dev/null)
cwd=$(printf '%s' "$input" | jq -r '.cwd // ""' 2>/dev/null)
[ -n "$cwd" ] && cd "$cwd" 2>/dev/null

# Only act inside a git work tree with a remote.
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || exit 0

dirty=$(git status --porcelain 2>/dev/null | head -1)
unpushed=0
upstream=$(git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null)
[ -n "$upstream" ] && unpushed=$(git rev-list --count '@{u}..HEAD' 2>/dev/null || echo 0)

# Nothing to nag about → silent.
[ -z "$dirty" ] && [ "${unpushed:-0}" -eq 0 ] && exit 0

# Debounce: at most once per 20 min per session.
stamp="$HOME/.claude/.git-nudge-$session_id"
now=$(date +%s 2>/dev/null || echo 0)
if [ -f "$stamp" ]; then
  last=$(cat "$stamp" 2>/dev/null || echo 0)
  [ "$now" -ne 0 ] && [ $(( now - last )) -lt 1200 ] && exit 0
fi
[ "$now" -ne 0 ] && echo "$now" > "$stamp" 2>/dev/null

# Build the reminder.
repo=$(basename "$(git rev-parse --show-toplevel 2>/dev/null || echo "$PWD")")
parts=""
[ -n "$dirty" ] && parts="uncommitted changes"
if [ "${unpushed:-0}" -gt 0 ]; then
  [ -n "$parts" ] && parts="$parts + "
  parts="${parts}${unpushed} unpushed commit(s)"
fi
msg="⚠ $repo has $parts. Before switching Macs, run /log (or git commit + push) — the other Mac can't see uncommitted/unpushed work, which is how duplicate work happens."

printf '{"systemMessage": %s, "suppressOutput": true}\n' "$(printf '%s' "$msg" | jq -Rs .)"
exit 0
