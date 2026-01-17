# Execution Plan

> Delete this file after execution completes. It's a working document, not history.

## Goal
<!-- One sentence. What are we building/fixing? -->


## Context Files
<!-- Files the executor needs to read. Keep minimal. -->
- `PROJECT_STATE.md` - current position
- `src/models/User.swift` - existing user model
- `docs/decisions.md` - relevant decisions

## Success Criteria
<!-- How do we know we're done? Be specific. -->
- [ ] All tests pass
- [ ] Feature works end-to-end
- [ ] No type errors

---

## Wave 1: [Name]
<!-- Tasks that can run in parallel -->

### Task 1.1: [Short name]
- **Do:** [Specific implementation instruction]
- **Files:** `path/to/file.swift`
- **Verify:** [How to check it worked]
- **Commit:** `feat(auth): add user model`

### Task 1.2: [Short name]
- **Do:** [Specific implementation instruction]
- **Files:** `path/to/other.swift`
- **Verify:** [How to check it worked]
- **Commit:** `feat(auth): add login route`

---

## Wave 2: [Name]
<!-- Depends on Wave 1 completing -->

### Task 2.1: [Short name]
- **Do:** [Specific implementation instruction]
- **Files:** `path/to/file.swift`
- **Depends on:** Task 1.1, Task 1.2
- **Verify:** [How to check it worked]
- **Commit:** `feat(auth): wire up middleware`

---

## Wave 3: Verification
<!-- Always end with verification wave -->

### Task 3.1: Integration test
- **Do:** Run full test suite, check integration points
- **Verify:** All tests pass, no regressions
- **Commit:** `test(auth): add integration tests`

### Task 3.2: Manual check
- **Do:** Test the actual user flow
- **Verify:** [Specific steps to verify manually]
- **Type:** checkpoint (requires human)

---

## Execution Log
<!-- Updated by /execute as waves complete -->

| Wave | Status | Commits | Notes |
|------|--------|---------|-------|
| 1 | | | |
| 2 | | | |
| 3 | | | |

---

## Template Usage

**Task types:**
- Default: auto-execute, auto-commit
- `checkpoint`: Stop and ask user (for decisions, manual verification)
- `tdd`: Write test first, then implementation

**Grouping rules:**
- Same wave = no dependencies between tasks = parallel execution
- Each wave must complete before next starts
- Keep tasks atomic (one logical change = one commit)

**After execution:**
1. All tasks checked off
2. Execution log filled in
3. PROJECT_STATE.md updated
4. **Delete this file** - it served its purpose
