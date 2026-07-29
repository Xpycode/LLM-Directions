#!/bin/bash
#
# git-add-guard.sh — PreToolUse hook (matcher: Bash): block sweep-staging.
#
# `git add -A`, `git add --all`, and `git add .` stage EVERYTHING in the tree — and on
# these Syncthing-shared checkouts the tree routinely holds uncommitted work the current
# session did not create (carried over from the other Mac, or left by a prior session).
# One such sweep staged 133 lines of the user's pre-existing work into a Claude commit
# (2026-07-29 usage report). `Bash(git add:*)` is on the permissions allowlist, so the
# permission layer can't catch this — a PreToolUse hook runs regardless of allow rules.
#
# Contract: hook input is JSON on stdin; exit 2 + stderr blocks the tool call and feeds
# the message back to Claude, which then stages explicit paths instead. Any other exit
# lets the call proceed. Fail OPEN on missing jq / unparsable input — a broken guard
# must never block ordinary git work.

command -v jq >/dev/null 2>&1 || exit 0
input=$(cat 2>/dev/null) || exit 0
cmd=$(printf '%s' "$input" | jq -r '.tool_input.command // empty' 2>/dev/null) || exit 0
[ -z "$cmd" ] && exit 0

# Exception: a repo created in this same command has no pre-existing work to sweep —
# the /setup initial commit (`git init … git add -A … git commit`) is the one legitimate sweep.
if printf '%s' "$cmd" | grep -qE '(^|[;&|[:space:]])git[[:space:]]+init([[:space:]]|$|[;&|])'; then
  exit 0
fi

# -A in any single-dash cluster (-A, -Av, -nA), or --all, allowing flags in between.
sweep_flags='git[[:space:]]+add([[:space:]]+-[^[:space:]]+)*[[:space:]]+(-[a-z]*A[a-z]*|--all)([[:space:]]|$|[;&|])'
# Bare `.`, `./`, or `..` as the pathspec. `./src/file.c` and `.gitignore` do NOT match —
# the boundary after the optional slash is required, so explicit paths stay allowed.
sweep_dot='git[[:space:]]+add([[:space:]]+-[^[:space:]]+)*[[:space:]]+\.{1,2}/?([[:space:]]|$|[;&|])'

if printf '%s' "$cmd" | grep -qE "$sweep_flags|$sweep_dot"; then
  cat >&2 <<'MSG'
BLOCKED (git-add-guard): stage explicit paths only — never `git add -A`, `--all`, or `.`.
On this Syncthing-shared setup the working tree can hold the user's own uncommitted
work from another Mac or a prior session; a sweep has previously staged 133 lines of it
into a Claude commit. Do this instead:
  1. git status --porcelain   — see what is actually in the tree
  2. git add <only the files this session changed>
MSG
  exit 2
fi
exit 0
