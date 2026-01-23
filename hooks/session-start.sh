#!/bin/bash

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
