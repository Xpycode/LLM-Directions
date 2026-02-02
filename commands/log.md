# Session Log

Create or update today's session log.

## Creating/Updating the Log

1. Check if `docs/sessions/` exists
2. Create today's log file: `docs/sessions/YYYY-MM-DD.md` (use actual date)
3. If continuing an existing session today, append to it

Log template:
```markdown
# Session: [DATE]

## Goal
[Ask user: "What are we working on this session?"]

## Progress
- [Track as we work]

## Decisions
- [Log any architectural/design decisions]

## Next
- [What to do next time]
```

Update `docs/sessions/_index.md` with this session.

## Sync PROJECT_STATE.md

After completing the session log, **always offer to sync PROJECT_STATE.md**:

> "Session logged. Should I sync PROJECT_STATE.md?"

If yes, review the session and update PROJECT_STATE.md with any changes to:

| Field | Update If... |
|-------|--------------|
| **Current Focus** | Focus shifted during session |
| **Last Session** | Always update to today's date |
| **Blockers** | New blockers found or existing ones resolved |
| **Next Actions** | Session identified new priorities |
| **Key Decisions** | Major decisions were made (add summary + link to decisions.md) |

Keep PROJECT_STATE.md as a **current snapshot** — it should reflect where the project stands *now*, not the history of how it got there (that's what session logs are for).

## Check for Cookbook Patterns

After syncing PROJECT_STATE.md, **check for new reusable patterns**:

> "Did this session produce any reusable code patterns worth adding to the cookbook?"

**Trigger words to listen for during session:**
- "finally got X working"
- "figured out how to..."
- "this pattern works well"
- "copied from [other project]"
- Window layouts, export dialogs, file pickers, app lifecycle

If yes, run `/cookbook add` to capture the pattern while it's fresh.

**Why:** Patterns captured immediately after solving a problem are more complete and accurate than trying to extract them later.
