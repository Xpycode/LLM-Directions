#!/bin/bash
#
# install.sh — wire the Directions machine-local setup on THIS Mac.
#
# The hook *scripts* travel via git, but the wiring (symlinks into ~/.claude/hooks
# and the settings.json registrations) is per-machine and does NOT travel. Forgetting
# it on the second Mac is a recurring pain (see 37_multi-mac-discipline.md). Run this
# once per Mac after cloning/pulling the repo:
#
#     bash hooks/install.sh          # apply
#     bash hooks/install.sh --dry-run  # show what it would do, change nothing
#
# Idempotent: re-running is safe — symlinks are refreshed, settings entries are added
# only if absent. Existing non-Directions hooks (autoresearch, codebase-memory-guard,
# a custom statusLine) are preserved. settings.json is backed up before any edit.

set -euo pipefail

DRY_RUN=0
[ "${1:-}" = "--dry-run" ] && DRY_RUN=1

# Resolve the repo root from this script's location (works on any Mac, any clone path).
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO=$(cd "$SCRIPT_DIR/.." && pwd)
CLAUDE_DIR="$HOME/.claude"
HOOKS_DIR="$CLAUDE_DIR/hooks"
SETTINGS="$CLAUDE_DIR/settings.json"

say()  { printf '%s\n' "$*"; }
do_it() { if [ "$DRY_RUN" = 1 ]; then say "  [dry-run] $*"; else eval "$*"; fi; }

command -v jq >/dev/null 2>&1 || { say "✗ jq is required (brew install jq)."; exit 1; }
[ "$DRY_RUN" = 1 ] && say "— DRY RUN: no files will change —"
say "Repo:    $REPO"
say "Target:  $CLAUDE_DIR"
say

# --- 1. Symlinks ------------------------------------------------------------------
# repo path (relative to REPO)  ->  symlink to create under ~/.claude
LINKS=(
  "hooks/session-start.sh:$HOOKS_DIR/session-start.sh"
  "hooks/session-stop.sh:$HOOKS_DIR/session-stop.sh"
  "hooks/session-guard.sh:$HOOKS_DIR/session-guard.sh"
  "hooks/model-advisor.sh:$HOOKS_DIR/model-advisor.sh"
  "hooks/git-add-guard.sh:$HOOKS_DIR/git-add-guard.sh"
  "claude-statusline/statusline.sh:$CLAUDE_DIR/statusline.sh"
)

say "Symlinks:"
do_it "mkdir -p '$HOOKS_DIR'"
for pair in "${LINKS[@]}"; do
  src="$REPO/${pair%%:*}"
  dest="${pair#*:}"
  if [ ! -e "$src" ]; then
    say "  ⚠ skip (source missing): ${pair%%:*}"
    continue
  fi
  do_it "chmod +x '$src'"
  if [ -L "$dest" ] && [ "$(readlink "$dest")" = "$src" ]; then
    say "  ✓ already linked: $(basename "$dest")"
  else
    # If a real (non-symlink) file is in the way, back it up rather than clobber.
    if [ -e "$dest" ] && [ ! -L "$dest" ]; then
      do_it "mv '$dest' '$dest.pre-directions.bak'"
      say "  • backed up existing $(basename "$dest") → $(basename "$dest").pre-directions.bak"
    fi
    do_it "ln -sf '$src' '$dest'"
    say "  → linked $(basename "$dest")"
  fi
done
say

# --- 2. settings.json registrations ----------------------------------------------
say "settings.json hooks:"
if [ ! -f "$SETTINGS" ]; then
  say "  • no settings.json — creating one"
  do_it "printf '{}\n' > '$SETTINGS'"
fi

# Back up once before edits (only when actually applying).
if [ "$DRY_RUN" = 0 ] && [ -f "$SETTINGS" ]; then
  cp "$SETTINGS" "$SETTINGS.bak.$(date +%Y%m%d%H%M%S)"
fi

# ensure_hook EVENT COMMAND [MATCHER] — append a command-hook to EVENT if not already
# present anywhere in that event's groups. Preserves existing groups/hooks. A MATCHER
# (e.g. "Bash" for PreToolUse) scopes the group to that tool; omitted = all.
ensure_hook() {
  local event="$1" cmd="$2" matcher="${3:-}"
  local present
  present=$(jq -r --arg ev "$event" --arg cmd "$cmd" \
    '[(.hooks[$ev] // [])[].hooks[]?.command] | index($cmd) != null' "$SETTINGS")
  if [ "$present" = "true" ]; then
    say "  ✓ $event already has $(basename "$cmd")"
    return
  fi
  if [ "$DRY_RUN" = 1 ]; then
    say "  [dry-run] would register $event → $(basename "$cmd")${matcher:+ (matcher: $matcher)}"
    return
  fi
  local tmp
  tmp=$(mktemp)
  jq --arg ev "$event" --arg cmd "$cmd" --arg m "$matcher" '
    .hooks //= {} |
    .hooks[$ev] //= [] |
    .hooks[$ev] += [
      if $m == "" then { "hooks": [ { "type": "command", "command": $cmd } ] }
      else { "matcher": $m, "hooks": [ { "type": "command", "command": $cmd } ] }
      end
    ]
  ' "$SETTINGS" > "$tmp" && mv "$tmp" "$SETTINGS"
  say "  → registered $event → $(basename "$cmd")${matcher:+ (matcher: $matcher)}"
}

ensure_hook "SessionStart"     "~/.claude/hooks/session-start.sh"
ensure_hook "Stop"             "~/.claude/hooks/session-stop.sh"
ensure_hook "UserPromptSubmit" "~/.claude/hooks/model-advisor.sh"
ensure_hook "PreToolUse"       "~/.claude/hooks/git-add-guard.sh" "Bash"

# statusLine: point at the Directions statusline only if none is set.
if [ "$(jq -r '.statusLine.command // ""' "$SETTINGS")" = "" ]; then
  if [ "$DRY_RUN" = 1 ]; then
    say "  [dry-run] would set statusLine → ~/.claude/statusline.sh"
  else
    tmp=$(mktemp)
    jq '.statusLine = {"type":"command","command":"~/.claude/statusline.sh","padding":0}' \
      "$SETTINGS" > "$tmp" && mv "$tmp" "$SETTINGS"
    say "  → set statusLine → ~/.claude/statusline.sh"
  fi
else
  say "  ✓ statusLine already set (left as-is)"
fi
say

# --- 3. Validate ------------------------------------------------------------------
if [ "$DRY_RUN" = 0 ]; then
  if jq -e . "$SETTINGS" >/dev/null 2>&1; then
    say "✓ settings.json valid. Registered events: $(jq -r '.hooks | keys | join(", ")' "$SETTINGS")"
  else
    say "✗ settings.json is not valid JSON — restore from the .bak file next to it."
    exit 1
  fi
fi

say
say "Done. Restart Claude Code (or start a new session) for the hooks to take effect."
say "Note: the .stignore Syncthing boundary (37_multi-mac-discipline.md, Rule 1a) travels"
say "via Syncthing on its own — it is NOT set up by this script."
