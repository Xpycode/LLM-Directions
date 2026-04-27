# MCP Guards

Drop-in PreToolUse hooks that gate specific MCP tool calls based on their arguments. Each guard handles ONE tool and answers ONE question: should this call be auto-approved, or should it stop and ask the user first?

## Why

Some MCP tools happily do something expensive when called with the "wrong" arguments. The auto-skill that called them often has no idea what those arguments will be. A small PreToolUse hook is the cheapest place to enforce "only run this tool when it's pointing at something I expect."

See `27_mcp-gotchas.md` in the Directions root for the canonical example (codebase-memory-mcp accidentally indexing `$HOME`).

## Available guards

| Guard | Tool it gates | Default policy |
|---|---|---|
| `codebase-memory-guard.sh` | `mcp__codebase-memory-mcp__index_repository` | Approve only paths matching `APPROVED_RE` (edit at top of script). Everything else → "ask". |

## Install

1. Copy the script and make it executable:
   ```bash
   mkdir -p ~/.claude/hooks
   cp codebase-memory-guard.sh ~/.claude/hooks/
   chmod +x ~/.claude/hooks/codebase-memory-guard.sh
   ```

2. Edit `APPROVED_RE` near the top of the script to match your real project layout.

3. Wire it into `~/.claude/settings.json` (merge with existing `hooks` block; don't replace):
   ```json
   {
     "hooks": {
       "PreToolUse": [
         {
           "matcher": "mcp__codebase-memory-mcp__index_repository",
           "hooks": [
             { "type": "command", "command": "~/.claude/hooks/codebase-memory-guard.sh" }
           ]
         }
       ]
     }
   }
   ```

4. Restart Claude Code or open `/hooks` once to reload.

## Pipe-test before installing

Each guard reads PreToolUse JSON on stdin and writes a decision to stdout — easy to verify by hand:

```bash
# Should allow
echo '{"tool_input":{"repo_path":"/your/projects/group/project"}}' \
  | ./codebase-memory-guard.sh

# Should ask (with warning)
echo '{"tool_input":{"repo_path":"/Users/you"}}' \
  | ./codebase-memory-guard.sh
```

Look for `"permissionDecision": "allow"` vs `"permissionDecision": "ask"` in the output.

## Writing your own guard

The contract is simple:

- **Input:** PreToolUse JSON on stdin: `{ "tool_name": ..., "tool_input": {...} }`
- **Output:** a JSON object on stdout with `hookSpecificOutput.permissionDecision` set to `"allow"`, `"ask"`, or `"deny"`, plus an optional `permissionDecisionReason` string

`codebase-memory-guard.sh` is a complete worked example — copy it as a starting point.
