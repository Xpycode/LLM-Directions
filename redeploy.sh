#!/bin/bash
#
# redeploy.sh — push THIS repo's Directions payload into ~/.claude on the current Mac.
#
# The repo travels via git; the *deployed* copy in ~/.claude does not. After a
# `git pull` on a second Mac, this script makes ~/.claude match the repo exactly:
#
#   1. Commands  — installs the canonical set AND prunes retired ones, while
#                  preserving independent (non-Directions) commands.
#   2. CLAUDE.md — overwrites ~/.claude/CLAUDE.md with the modernized template.
#   3. Hooks     — delegates to hooks/install.sh (per-Mac symlinks + settings.json).
#
# Everything is backed up before it is touched. Idempotent — safe to re-run.
#
#     bash redeploy.sh            # apply
#     bash redeploy.sh --dry-run  # show what it would do, change nothing
#     bash redeploy.sh --skip-claude-md   # commands + hooks only, leave CLAUDE.md
#
# WHY a dedicated script (not install-directions.sh): that installer *copies* commands
# but never prunes, and refuses to overwrite an existing CLAUDE.md — so a second Mac
# ends up with the new commands piled on top of the retired ones, and a stale CLAUDE.md.
# See 37_multi-mac-discipline.md.

set -euo pipefail

DRY_RUN=0
SKIP_CLAUDE_MD=0
for arg in "$@"; do
  case "$arg" in
    --dry-run)        DRY_RUN=1 ;;
    --skip-claude-md) SKIP_CLAUDE_MD=1 ;;
    *) echo "Unknown flag: $arg" >&2; exit 2 ;;
  esac
done

# Resolve repo root from this script's location — works on any Mac, any clone path.
REPO=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
CLAUDE_DIR="$HOME/.claude"
COMMANDS_DIR="$CLAUDE_DIR/commands"
CLAUDE_MD="$CLAUDE_DIR/CLAUDE.md"
TEMPLATE="$REPO/CLAUDE-GLOBAL-TEMPLATE.md"
STAMP=$(date +%Y%m%d-%H%M%S)

say()   { printf '%s\n' "$*"; }
do_it() { if [ "$DRY_RUN" = 1 ]; then say "  [dry-run] $*"; else eval "$*"; fi; }

[ "$DRY_RUN" = 1 ] && say "— DRY RUN: no files will change —"
say "Repo:   $REPO"
say "Target: $CLAUDE_DIR"
say

# Sanity: must be run from inside the git repo (provenance check needs history).
if ! git -C "$REPO" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  say "✗ $REPO is not a git work tree — provenance-based pruning needs history."
  say "  If .git was Syncthing-stripped, invoke the git-bootstrap skill first."
  exit 1
fi

# --- 1. Commands: install canonical, prune retired, keep independents -------------
say "Commands:"
do_it "mkdir -p '$COMMANDS_DIR'"
if [ -d "$COMMANDS_DIR" ]; then
  do_it "cp -R '$COMMANDS_DIR' '$COMMANDS_DIR.bak-$STAMP'"
  say "  • backed up existing commands → commands.bak-$STAMP"
fi

# Install the canonical set (the 13 that live in the repo).
do_it "cp '$REPO/commands/'*.md '$COMMANDS_DIR/'"
say "  → installed $(ls -1 "$REPO"/commands/*.md | wc -l | tr -d ' ') canonical commands"

# Prune: any *.md in ~/.claude/commands NOT in the repo's set is either a RETIRED
# Directions command (was tracked here, then deleted → remove) or an INDEPENDENT
# command that never lived in this repo (→ keep). git log --diff-filter=D decides.
say "  Pruning stragglers (retired Directions commands only):"
pruned=0; kept=0
if [ -d "$COMMANDS_DIR" ]; then
  for f in "$COMMANDS_DIR"/*.md; do
    [ -e "$f" ] || continue
    name=$(basename "$f")
    [ -e "$REPO/commands/$name" ] && continue   # part of canonical set — keep
    if git -C "$REPO" log --diff-filter=D --format= --name-only -- "commands/$name" \
         2>/dev/null | grep -q .; then
      do_it "rm '$f'"
      say "    ✗ removed retired: $name"
      pruned=$((pruned+1))
    else
      say "    ✓ kept independent: $name"
      kept=$((kept+1))
    fi
  done
fi
say "  ($pruned retired removed, $kept independent kept)"
say

# --- 2. CLAUDE.md: overwrite with the modernized template ------------------------
if [ "$SKIP_CLAUDE_MD" = 1 ]; then
  say "CLAUDE.md: skipped (--skip-claude-md)"
else
  say "CLAUDE.md:"
  if [ ! -f "$TEMPLATE" ]; then
    say "  ✗ template missing: $TEMPLATE"; exit 1
  fi
  if [ -f "$CLAUDE_MD" ]; then
    if cmp -s "$TEMPLATE" "$CLAUDE_MD"; then
      say "  ✓ already matches template — nothing to do"
    else
      do_it "cp '$CLAUDE_MD' '$CLAUDE_MD.bak-$STAMP'"
      do_it "cp '$TEMPLATE' '$CLAUDE_MD'"
      say "  → updated ~/.claude/CLAUDE.md (backup: CLAUDE.md.bak-$STAMP)"
    fi
  else
    do_it "cp '$TEMPLATE' '$CLAUDE_MD'"
    say "  → created ~/.claude/CLAUDE.md from template"
  fi
fi
say

# --- 3. Hooks: per-Mac wiring (idempotent) ---------------------------------------
say "Hooks (via hooks/install.sh):"
if [ "$DRY_RUN" = 1 ]; then
  bash "$REPO/hooks/install.sh" --dry-run | sed 's/^/  /'
else
  bash "$REPO/hooks/install.sh" | sed 's/^/  /'
fi
say

# --- 4. Verify -------------------------------------------------------------------
say "Verification:"
say "  commands live:      $(ls -1 "$COMMANDS_DIR"/*.md 2>/dev/null | wc -l | tr -d ' ') (expect 13 + independents)"
say "  CLAUDE.md lines:    $(wc -l < "$CLAUDE_MD" 2>/dev/null | tr -d ' ')"
say
say "Done. Restart Claude Code (or start a new session) for changes to take effect."
