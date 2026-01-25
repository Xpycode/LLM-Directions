<!--
TRIGGERS: workflow, phases, process, how to build, spec interview, planning, implementation, review
PHASE: any
LOAD: full
-->

# The Development Workflow

**The funnel that ships working software.**

*Three funnels. Six phases. Backpressure at every gate.*

---

## The Ralph Funnel

Every feature flows through three funnels:

```
DEFINE ──gate──> PLAN ──gate──> BUILD
```

| Funnel | Purpose | Output | Gate |
|--------|---------|--------|------|
| **Define** | Understand what we're building | Spec with acceptance criteria | Spec reviewed, edge cases clear |
| **Plan** | Break into atomic tasks | IMPLEMENTATION_PLAN.md | Tasks atomic, dependencies mapped |
| **Build** | Implement with backpressure | Working code | Tests pass, review done |

**Key principle:** 80% of time on Define + Plan, 20% on Build.

---

## Phase 1: Discovery (Define Funnel)

**The Problem:** Projects fail when the AI doesn't understand what you want.

**The Solution:** The Spec Interview (see `/interview`)

```
1. Write a one-line description of what you want
2. Run /interview - answer questions until scope is clear
3. Review generated spec and acceptance criteria
4. Confirm understanding before proceeding
```

**Output:**
- `specs/[feature].md` - Full specification
- Acceptance criteria (testable)
- Flags for relevant technical docs

**Gate to pass:** Spec reviewed, edge cases documented, no contradictions.

---

## Phase 2: Planning (Plan Funnel)

**The Problem:** Big features become abandoned features.

**The Solution:** Atomic tasks with backpressure (see `/plan`)

> "Never be more than 30 minutes from working code."

Each task must:
1. Be completable in <30 minutes
2. Have clear "done" criteria
3. Have a validation command (test/lint/build)
4. Not break what already works

**Output:**
- `IMPLEMENTATION_PLAN.md` with waves
- Each wave grouped by dependencies
- Backpressure defined for each task

**Gate to pass:** All tasks atomic, dependencies mapped, validation commands specified.

---

## Phase 3: Implementation (Build Funnel)

**The Problem:** Context degrades over long sessions.

**The Solution:** Wave-based execution with fresh context (see `/execute`)

```
For each wave:
1. Spawn parallel subagents for independent tasks
2. Each subagent gets fresh context + task-specific info
3. Validate with backpressure after each task
4. Commit atomically: one task = one commit
5. Main agent stays light (orchestrator only)
```

**Key patterns:**
- Subagent context is disposable, garbage collected after task
- Plan persists on disk, survives session boundaries
- Orchestrator never exceeds 40% context usage

**Output:**
- Code changes committed per-task
- IMPLEMENTATION_PLAN.md checkboxes updated
- Operational learnings noted

---

## Phase 4: Adversarial Review (Build Funnel)

**The Problem:** Claude has "false confidence" - says "Brilliant!" about buggy code.

**The Solution:** Multi-perspective review (see `/reflect`)

```
Do a git diff and pretend you're a senior dev doing a code review
and you HATE this implementation. What would you criticize?
```

**Perspectives to apply:**

| Perspective | Focus |
|-------------|-------|
| Bug Hunter | Crashes, unhandled cases, null pointers |
| Security | Input validation, auth, secrets |
| Quality | Duplication, file size, naming |
| Test Coverage | Untested paths, missing edge cases |

**Severity guide:**

| Type | Action |
|------|--------|
| Crash/security bug | Fix immediately |
| Missing error handling | Fix before commit |
| Style nitpick | Ignore |
| Over-engineering suggestion | Ignore |

**Rule:** 2-3 review passes. More wastes time.

---

## Phase 5: Multi-Model Validation (Build Funnel - Optional)

**The Problem:** Different AI models catch different bugs.

**Evidence:** "Claude missed ID stability bug; Gemini caught it."

**When to use:**
- Code that handles money or sensitive data
- Core architecture decisions
- Anything that "just feels off"

**Options:**
- Copy code to Gemini for review
- Use `/zen` tools to consult other models
- Ask a different Claude session (fresh context)

---

## Phase 6: Verification (Build Funnel)

**The Problem:** "Build succeeded" doesn't mean "bug fixed."

**The Solution:** Test the actual user workflow

```
Run the app. Click through the UI. Try edge cases.
Restart. Check persistence. Verify against acceptance criteria.
```

**Gate to pass:**
- All acceptance criteria from spec satisfied
- Manual verification of primary user flow
- Edge cases tested (empty state, error state)
- Backpressure commands all pass

**Output:**
- Feature marked complete in IMPLEMENTATION_PLAN.md
- PROJECT_STATE.md updated
- Session log entry with verification notes

---

## Daily Workflows

### Starting a New Feature

```
1. /interview - Create spec with acceptance criteria
2. /plan - Break into atomic tasks with waves
3. /execute - Implement wave by wave
4. /reflect - Adversarial review
5. /compound - Extract learnings
6. Commit when stable
```

### Continuing Work

```
1. /status - Where are we?
2. /next - What's the next task?
3. Implement task
4. Run backpressure
5. Commit if passes
6. /next again
```

### Fixing a Bug

```
1. Describe exact symptom
2. Ask Claude to find cause (don't guess)
3. Ask Claude to explain fix before implementing
4. Implement fix
5. Run backpressure
6. Verify bug is gone
7. Commit with explanation
```

### Ending a Session

```
1. /reflect - Check for issues
2. /compound - Extract learnings
3. /log - Update session log
4. Commit any uncommitted work
5. Note resume point in RESUME.md if mid-task
```

---

## The Checklists

### Before Starting Any Feature

- [ ] Spec exists with acceptance criteria
- [ ] Edge cases documented
- [ ] IMPLEMENTATION_PLAN.md created
- [ ] First wave tasks are clear and atomic

### Before Each Commit

- [ ] Backpressure passes (build, lint, test)
- [ ] Task is atomic (one logical change)
- [ ] No debug print statements
- [ ] No force unwraps without nil checks

### Before Shipping

- [ ] All acceptance criteria verified
- [ ] Adversarial review done (2-3 passes)
- [ ] Manual user flow tested
- [ ] CHANGELOG updated
- [ ] README current

---

## Regeneration Philosophy

Plans are disposable. If a plan is wrong:

1. Don't patch it
2. Regenerate from current state
3. Costs one planning loop
4. Ensures accuracy

> "The plan is not the territory. When reality diverges, update the plan."

---

*This workflow evolves. When you learn something the hard way, run /compound.*
