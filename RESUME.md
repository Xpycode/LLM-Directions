# Resume Point

> **This file is a temporary bridge.** Delete after resuming work.

## Quick Context
<!-- 2-3 sentences max. What's the situation? -->
Work in **zPackages** (2026-06-07) spilled into Directions. A new house-style doc is drafted but
**uncommitted**, and a **framework decision is parked** about fixing how Directions reaches
projects. You have many sessions in flight — this is the Directions-side to-do.

## Last Completed
<!-- Specific items done. Not "worked on X" but "finished X, Y, Z" -->
- Drafted **`46_main-menu.md`** — house-style: *the main menu is the complete command inventory*
  (every UI action also a menu command). Sibling to `41_apple-ui.md`; full doc + audit checklist.

## Still In Progress
<!-- What's partially done? Include enough detail to continue. -->
- `46_main-menu.md` is written but **not committed** in the Directions repo.

## Decisions Made
<!-- Key choices so the next session doesn't re-debate -->
- Menu conventions belong in **Directions**, not a zPackages package (menu content too app-specific).
- **Diagnosis — Directions has a copy-vs-drift flaw:** universal docs are copied into each project
  at setup, so new/updated house-style docs never reach already-set-up projects (N copies drift).
  Same tension packages solved with path-deps (single source of truth).

## Blockers
<!-- What's stuck? Include any workarounds tried. -->
- None. The items below are decisions awaiting your go-ahead, not technical blocks.

## Start Here
<!-- THE MOST IMPORTANT SECTION. Exact next action. -->
**Immediate next step — decide + execute these two, then commit `46_main-menu.md`:**

1. **Wire a "Directions Index" into global `~/.claude/CLAUDE.md`** — a topic→master-doc trigger
   table (sibling to the existing Pattern Cookbook block) so a running project, which only reliably
   reads global+local CLAUDE.md, knows *which* master doc to read on demand instead of a stale local
   copy. The docs already carry `TRIGGERS:` headers to aggregate.
   - **Option A (recommended):** hand-write the table now (~15 lines, immediate value).
   - **Option B:** generate it from the docs' `TRIGGERS:` headers via a small script (can't drift).
2. **Change `/setup`** to stop cloning the universal `20–61` docs into each project — scaffold only
   the project-specific ones (PROJECT_STATE, sessions/, decisions, glossary). The other half of
   killing the drift.
3. **Commit `46_main-menu.md`** (+ the index/setup changes once made).

Full reasoning: `sessions/2026-06-07.md` (here) and the zPackages session log of the same date.


---

## Usage

**Create this file when:**
- Session ends mid-task
- Context is getting full and you need fresh start
- Handing off to a different session

**On resume:**
1. Read this file first
2. Execute the "Start Here" action
3. **Delete this file** (it's served its purpose)

**Why delete?** Stale resume points pollute future sessions. PROJECT_STATE.md is the permanent record; this is just a cognitive bridge.
