# /execute - Wave-Based Task Execution

Run implementation tasks with fresh context per wave, preventing quality degradation.

## When to Use

- Implementing a feature with multiple tasks
- Any work that might fill your context window
- When you want atomic commits per task

## Workflow

### Step 1: Check or Create Plan

Look for `PLAN.md` in project root. If missing, create one:

```markdown
# Execution Plan

## Goal
[One sentence: what are we building?]

## Tasks

### Wave 1 (parallel)
- [ ] **Task 1.1**: [description] → `file1.swift`
- [ ] **Task 1.2**: [description] → `file2.swift`

### Wave 2 (depends on Wave 1)
- [ ] **Task 2.1**: [description] → `file3.swift`

### Wave 3 (verification)
- [ ] **Task 3.1**: Run tests, verify integration
```

**Rules for grouping:**
- Same wave = can run in parallel (no dependencies)
- Next wave = depends on previous wave completing
- Keep each task atomic (one logical change)

### Step 2: Execute Waves

For each wave:

1. **Spawn parallel subagents** using Task tool:
   ```
   Task(subagent_type="developer", prompt="Execute Task 1.1: [full context]...")
   Task(subagent_type="developer", prompt="Execute Task 1.2: [full context]...")
   ```

2. **Each subagent prompt must include:**
   - The specific task description
   - Target files
   - Success criteria
   - Current project state (from PROJECT_STATE.md)
   - NO session history (fresh context)

3. **After wave completes:**
   - Collect results
   - Make atomic commits: `feat(wave-1): task 1.1 description`
   - Update PLAN.md checkboxes
   - Update PROJECT_STATE.md progress

4. **If blocked:**
   - Create checkpoint in RESUME.md
   - Ask user for decision
   - Continue or spawn debugger agent

### Step 3: Verify

After all waves:
- Run full test suite
- Check integration points
- Update PROJECT_STATE.md with completion

## Deviation Rules

Subagents should auto-handle:
1. **Bug fixes** - Fix broken behavior inline
2. **Critical additions** - Add missing error handling, validation
3. **Blockers** - Resolve issues preventing task completion

Subagents should checkpoint for:
- Architectural decisions
- Scope changes
- Unclear requirements

## Example Session

```
User: /execute

Claude: I found PLAN.md with 3 waves, 7 tasks total.

**Wave 1** (3 parallel tasks):
- Task 1.1: Create UserAuth model → src/models/
- Task 1.2: Add auth routes → src/routes/
- Task 1.3: Create login view → src/views/

Spawning 3 developer agents with fresh contexts...

[Wave 1 complete - 3 commits made]

**Wave 2** (2 parallel tasks):
- Task 2.1: Wire up auth middleware
- Task 2.2: Add session storage

Spawning 2 developer agents...

[Wave 2 complete - 2 commits made]

**Wave 3** (verification):
Running tests... All pass.
Integration check... Working.

Execution complete. 5 atomic commits made.
Updated PROJECT_STATE.md.
```

## Key Principles

1. **Orchestrator stays light** - Never exceed 40% context. Delegate heavy work.
2. **Fresh context per task** - Each subagent starts clean with only what it needs.
3. **Atomic commits** - One task = one commit. Easy to revert or bisect.
4. **State in files** - PROJECT_STATE.md and PLAN.md are source of truth, not conversation history.

## Related Commands

- `/status` - Check current state before executing
- `/log` - Record session after execution
- `/review` - Production checklist after shipping
