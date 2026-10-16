# Claude Code logging integration

Read only in Claude Code during pre-clear or Mac-handoff; Codex skips this file.
The shared model-fit reminder remains in the core.

<!-- CLAUDE-ONLY:START — Codex skips this model-marker integration -->

### Claude Code phase-marker integration

Switching models re-reads the whole context (a cache miss); doing it right after `/clear` at an empty
context is nearly free, mid-session at full context is the expensive moment. So the ritual is
**clear → switch → start**, and this reminder makes the next session begin on the right tier:

```bash
SID=$(ls -t "$HOME"/.claude/.current-model-* 2>/dev/null | head -1 | sed "s:.*/.current-model-::")
PHASE=$(cat "$HOME/.claude/.session-phase-$SID" 2>/dev/null)
echo "this session phase: ${PHASE:-unknown}"
rm -f "$HOME/.claude/.session-phase-$SID" 2>/dev/null   # consume it — fresh phase set next session
```

When it agrees with the actual next action, use the phase marker to add the exact Claude Code model
command to the shared reminder (do not emit a second notice):

| This session was | Show |
|---|---|
| `spec` | 🔴 **NEXT: PLANNING → `/model opus`** |
| `plan` | 🔴 **NEXT: EXECUTING → `/model sonnet`** |
| `execute` | 🔴 **More execution? STAY ON SONNET. Planning next? → `/model opus`** |
| unknown / empty | skip — no phase recorded |

Append: **"Clear FIRST, then `/model <X>`, then start."** This is a reminder, not an action.
<!-- CLAUDE-ONLY:END -->
