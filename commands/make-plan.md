# Planning Mode

Enter planning mode to create or update IMPLEMENTATION_PLAN.md.

Before starting, apply `60_model-selection.md` → **User-Facing Model-Fit Notice**. Planning normally
starts at deep capability with high reasoning. Show one provider-neutral notice only when that is a
change or a consequential recommendation. The Claude-specific block below fulfils this step for
Claude Code; do not emit both notices.

<!-- CLAUDE-ONLY:START — Codex skips this model-marker integration -->
## Step 0 — Model tier check (nudge)

Planning = decomposition + architecture = **Opus-tier** reasoning. Record the phase and read the model:

```bash
SID=$(ls -t "$HOME"/.claude/.current-model-* 2>/dev/null | head -1 | sed "s:.*/.current-model-::")
[ -n "$SID" ] && printf 'plan' > "$HOME/.claude/.session-phase-$SID"
MODEL=$(cat "$HOME/.claude/.current-model-$SID" 2>/dev/null)
echo "phase: plan · current model: ${MODEL:-unknown}"
```

If `MODEL` is Sonnet or Haiku (under-powered for architecture), **nudge once, then continue anyway**:

> 🔴 **You're on `<MODEL>` — planning is Opus-tier reasoning. Consider `/model opus`.**

If already Opus/Fable, say nothing and proceed.
<!-- CLAUDE-ONLY:END -->

## When to Use

- Starting a new feature
- IMPLEMENTATION_PLAN.md doesn't exist or is stale
- Trajectory has diverged significantly from plan

## Process

### Step 1: Scope (Define the Goal)

Infer the goal from the request and existing spec. Ask what to build only when that is missing.

If they have a spec already, read it. If not, run a quick interview:
- What's the core functionality?
- What are the acceptance criteria?
- What edge cases matter?

### Step 2: Gap Analysis

Compare the goal against existing code:

```
1. Read relevant existing files
2. Identify what exists vs. what's needed
3. List the delta as discrete tasks
```

**Key question:** "Don't assume not implemented" - check before creating new.

**If the feature involves UI:** Check `36_ui-changes-protocol.md` → UI Constraints Checklist. Ensure no planned tasks use forbidden elements (`NavigationSplitView` for the primary window; raw SwiftUI `Button`/`Picker`/`Slider`/etc.). Use AppKit wrappers (`47_project-ui-conventions.md`) for controls. For panes, follow the split-pane decision tree in `cookbook/00-app-shell.md` §5: `HSplitView`/`VSplitView` for user-resizable panes (the house standard for the main window split), `HStack(spacing: 0)` + `Divider()` only for fixed-width/non-resizable sidebars — `HSplitView` is not forbidden, it's the default for resizable layouts.

### Step 3: Create Task List

Break the delta into atomic tasks:

**Good tasks:**
- Completable in <30 minutes
- One logical change per task
- Has clear "done" criteria
- Has backpressure (test/lint/build that validates)

**Bad tasks:**
- "Build the feature" (too big)
- "Set up architecture" (no validation)
- "Various fixes" (not atomic)

### Step 4: Organize into Waves

Build the schedule from explicit task dependencies, not feature headings. Within a wave, tasks have
no mutual prerequisites and exclusive write ownership. Later waves start after their named
prerequisites have been integrated and validated; they need not depend on every earlier task.

- Name prerequisite task IDs and accepted interfaces. Check for cycles and missing prerequisites.
- Assign source/test files per task. Shared-file changes must be serialized, split at an interface,
  or owned by the coordinator during integration. Include shared project/build resources.
- Group dependency-ready, disjoint tasks for parallel agents. A single-task wave is valid for coupled
  integration work; give the reason. Use the execution command's delegation and authorization rules.
- Separate external checks (user fixtures, devices, credentials, provider delivery, manual acceptance)
  and name exactly which tasks/claims each gates. They must neither stop unrelated ready work nor be
  waived to advance dependent work. If provisional development is valid, specify its limits and the
  task that replaces/verifies the provisional assumption before acceptance.
- Include final integration and product acceptance. Distinguish implemented, validated and blocked
  work; a passing unit suite alone does not complete a manual acceptance task.

Before calling the plan ready, check every wave for dependency and ownership conflicts. If no safe
parallel work exists, say why. “Six waves” alone is not a validated execution schedule.

### Step 5: Write IMPLEMENTATION_PLAN.md

Read `IMPLEMENTATION_PLAN-template.md` from the Directions master. Write the project-specific plan
at the project's established path; do not copy the shared procedural library into the project.

Include for each task:
- Description
- Dependencies and external gates (explicitly `none` when absent)
- Target file(s)
- Exclusive ownership and interfaces needed by other tasks
- Success criteria
- Backpressure command

Include a compact execution log for actual assignments, validation evidence, commits/exceptions and
continuation or stop reasons. Do not prefill success evidence. Follow `commands/execute.md` at runtime.

### Step 6: Exit Planning

> "Plan created with [N] tasks across [M] waves.
> Ready to execute? Run `/execute` to start."

Update PROJECT_STATE.md:
- Funnel: `plan` -> validation gate passed
- Ready to move to `build`
- Now → Execution: link the plan and name the first wave/tasks with their prerequisite status;
  distinguish ready work from execution not yet requested. `/status` uses this for its reminder.

## Quick Start

If user just types `/make-plan`:

1. Check if IMPLEMENTATION_PLAN.md exists
   - **Yes**: "Found existing plan. Review and update, or start fresh?"
   - **No**: "No plan found. What are we building?"

2. Follow the process above

## Regeneration

If the schedule is wrong, repair dependencies and ownership while preserving task IDs, completed
evidence and approved requirements. Explain material scheduling changes. Regenerate the affected
plan when the goal or architecture has changed; obtain a decision for scope changes rather than
silently replacing approved work. Routine scheduling repairs do not need renewed permission.

---

## TASKS.md Integration

After creating IMPLEMENTATION_PLAN.md, sync with the task tracker (`docs/TASKS.md` in an installed
project; root `TASKS.md` in the Directions master):

1. **If tasks exist in Backlog:** Move relevant tasks to Current Sprint
2. **If new tasks:** Add them to Current Sprint (they weren't in Backlog)
3. Keep Current Sprint focused: 3-7 tasks max per sprint

```markdown
## Current Sprint
- [ ] Task 1.1: [from Wave 1]
- [ ] Task 1.2: [from Wave 1]
- [ ] Task 2.1: [from Wave 2]
```

**Mapping:** IMPLEMENTATION_PLAN.md tasks → TASKS.md Current Sprint
- Wave tasks become sprint tasks
- IMPLEMENTATION_PLAN.md has execution details (files, backpressure)
- TASKS.md has checkbox tracking for progress

> "Moved [N] tasks to Current Sprint. Run `/execute` to begin."

---
*80% of time on planning, 20% on execution. This is the 80%.*
