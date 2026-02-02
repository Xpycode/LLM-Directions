# Project Status

Quick status check. Read and summarize:

**File Detection (dual-mode):**
- If `docs/PROJECT_STATE.md` exists → use `docs/` paths (installed project)
- If `./PROJECT_STATE.md` exists at root → use root paths (master repo)

1. `PROJECT_STATE.md` - current phase, focus, blockers
2. `TASKS.md` - backlog, current sprint, progress (if exists)
3. `tasks-archive.md` - archived count (if exists)
4. `sessions/_index.md` - last session date and outcome
5. Latest session log if exists

Report:
- What phase we're in
- **Task progress** (if TASKS.md exists):
  - Backlog: N tasks
  - Current Sprint: N/M complete
  - Archived: N tasks
  - Overall: X%
- Readiness snapshot (Features/UI/Testing/Docs/Distribution status)
- What we're working on
- Any blockers
- What happened last time
- Suggested next action

## Phase-Specific Reminders

If phase is **polish** or **shipping**, add:

> **Reminder:** Run `/minimums` to check baseline features (updates, logging, UI polish) before release.
