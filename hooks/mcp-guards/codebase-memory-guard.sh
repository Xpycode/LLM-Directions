#!/usr/bin/env bash
# codebase-memory-guard.sh
#
# PreToolUse hook for codebase-memory-mcp's `index_repository` tool.
# Stops accidental indexing of $HOME or umbrella directories — the kind of
# call that creates a multi-GB SQLite DB and burns hundreds of % CPU on the
# call-graph resolution pass.
#
# Wire it up in ~/.claude/settings.json:
#
#   "hooks": {
#     "PreToolUse": [
#       {
#         "matcher": "mcp__codebase-memory-mcp__index_repository",
#         "hooks": [
#           { "type": "command", "command": "~/.claude/hooks/codebase-memory-guard.sh" }
#         ]
#       }
#     ]
#   }
#
# Contract:
#   stdin  — PreToolUse JSON: { "tool_input": { "repo_path": "..." } }
#   stdout — JSON with hookSpecificOutput.permissionDecision = "allow" | "ask"
#
# Pipe-test:
#   echo '{"tool_input":{"repo_path":"/abs/path"}}' | ./codebase-memory-guard.sh

set -euo pipefail

# ============================================================================
# EDIT THIS — anchored regex matching repo_paths you want to auto-approve.
#
# Default below requires at least two path segments under a single projects
# root, e.g. /home/you/code/<group>/<project>/... — single-level umbrellas
# like /home/you/code/<group> are deliberately excluded.
# ============================================================================
APPROVED_RE='^/ABSOLUTE/PATH/TO/PROJECTS_ROOT/[^/]+/[^/]+(/|$)'
# ============================================================================

input=$(cat)
repo_path=$(printf '%s' "$input" | jq -r '.tool_input.repo_path // ""')

if [[ -n "$repo_path" && "$repo_path" =~ $APPROVED_RE ]]; then
  jq -n --arg path "$repo_path" '{
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "allow",
      permissionDecisionReason: ("Approved project path: " + $path)
    }
  }'
else
  shown_path=$repo_path
  [[ -z "$shown_path" ]] && shown_path="<empty / not provided>"
  jq -n --arg path "$shown_path" --arg re "$APPROVED_RE" '{
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "ask",
      permissionDecisionReason: (
        "WARNING: codebase-memory-mcp wants to index a NON-APPROVED folder.\n\n" +
        "Requested repo_path: " + $path + "\n" +
        "Approved pattern  : " + $re + "\n\n" +
        "Paths outside this pattern (your home dir, an umbrella folder, etc.) can\n" +
        "produce multi-GB SQLite databases and spike CPU on the call-graph pass.\n\n" +
        "Approve only if you genuinely want a new project DB at this path. To make\n" +
        "this path auto-approved, edit APPROVED_RE at the top of the guard script."
      )
    }
  }'
fi
