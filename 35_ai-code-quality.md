<!--
TRIGGERS: vibe code, AI code, generated code, codebase size, LOC, complexity, edge case, review threshold
PHASE: implementation, shipping
LOAD: full
-->

# AI Code Quality Discipline

*Guardrails for AI-assisted development. Based on observed failure patterns.*

---

## The Core Problem

AI-generated code has predictable failure patterns:

| Pattern | Why It Happens | Impact |
|---------|----------------|--------|
| **Happy-path bias** | Training data skews toward working examples | Error paths untested |
| **Verbose solutions** | Models optimize for completeness, not elegance | Bloated codebases |
| **Shallow edge cases** | Models miss domain-specific boundaries | Bugs in production |
| **Confident wrongness** | No uncertainty signals | Silent failures |

Estimated defect rate for AI code: **1.5-2x higher** than experienced human code.

---

## Complexity Thresholds

### Codebase Size Alerts

| LOC | Risk Level | Action |
|-----|------------|--------|
| < 5,000 | Low | Standard testing |
| 5,000 - 20,000 | Medium | Review architecture, consolidate |
| 20,000 - 50,000 | High | External review recommended |
| > 50,000 | Critical | Audit before shipping |

**Check your codebase:**
```bash
# Count lines of code (excluding blanks and comments)
find . -name "*.swift" -not -path "./.build/*" | xargs wc -l | tail -1

# Or use cloc if available
cloc --include-lang=Swift .
```

### Feature Interaction Formula

Feature interactions grow as: `2^n - 1 - n`

| Features | Possible Interactions |
|----------|----------------------|
| 5 | 26 |
| 7 | 120 |
| 10 | 1,013 |
| 15 | 32,752 |

**Mitigation:** Modular architecture. Clear interfaces. Explicit feature boundaries.

---

## AI-Specific Testing Requirements

### 1. Edge Case Generation (Mandatory)

After any AI implementation, explicitly ask:

```
What edge cases exist for this code?

Check:
1. Empty/nil inputs
2. Maximum values (Int.max, huge strings)
3. Unicode edge cases (emoji, RTL text)
4. Concurrent access
5. Resource exhaustion (memory, disk)
6. Network failures (timeout, no connection)
7. Permission denied scenarios
8. Corrupt/malformed data
9. State machine transitions (unexpected order)
10. Boundary conditions (0, 1, max-1, max)

For each edge case, do we:
- Handle it explicitly?
- Test it?
- Document the expected behavior?
```

### 2. Error Path Testing (Mandatory)

AI code often has optimistic error handling. Require:

```
Show me every error path in this code.

For each path:
1. What triggers it?
2. Is it tested?
3. What does the user see?
4. Is it logged?

Generate tests for each error path.
```

### 3. The "What If It's Wrong" Audit

After AI generates code, ask:

```
Assume this implementation has bugs. Where are the most likely places?

Consider:
- Off-by-one errors
- Race conditions
- Missing null checks
- Resource leaks
- Silent failures
```

---

## Anti-Bloat Discipline

### Weekly Consolidation Prompt

```
Analyze this codebase for consolidation opportunities:

1. Duplicate or near-duplicate code
2. Functions that could be combined
3. Unused imports/dependencies
4. Dead code paths
5. Overly abstract patterns (used only once)
6. Files that could be merged

For each finding:
- Quote the specific code
- Explain why it's redundant
- Suggest consolidation
```

### Before Adding New Code

Ask: *"Does this need to be new code, or does existing code already do this?"*

```
Before implementing [feature], search the codebase for:
- Similar functionality
- Patterns I should follow
- Code I can extend instead of duplicate
```

### LOC Budget

Set a target and track it:

```
This project should stay under [X] LOC.
Current: [Y] LOC

If we're over budget:
1. What can be simplified?
2. What's unused?
3. What's over-engineered?
```

---

## Human Review Triggers

### When AI Review Is Insufficient

Request human code review when:

| Trigger | Why |
|---------|-----|
| Security-sensitive code | Auth, crypto, user data |
| Financial calculations | Money, billing, accounting |
| Complex algorithms | AI may miss subtle bugs |
| > 500 LOC change | Too much for self-review |
| Third integration | External dependencies |
| Shipping to paying users | Liability |

### Human Review Checklist

```markdown
## Human Review Request

**What changed:** [summary]
**LOC added/modified:** [count]
**Risk areas:** [security/data/money/other]

**Specific questions:**
1. Is the error handling complete?
2. Are there race conditions I missed?
3. Is the architecture reasonable?
4. What would you do differently?
```

---

## Regression Testing Discipline

### Before AI Modifies Existing Code

1. **Snapshot current behavior**
   ```
   Before modifying [file/function]:
   1. List all current test cases
   2. Run tests, confirm passing
   3. Document expected behavior
   ```

2. **After modification, verify:**
   - All existing tests still pass
   - New tests cover the change
   - No unintended behavior changes

### The "Break It" Test

After AI "fixes" something:

```
This code was just modified. Try to break it:

1. What inputs would cause unexpected behavior?
2. What state combinations weren't considered?
3. What happens under load?
4. What happens with slow/failing dependencies?

Generate tests for each scenario.
```

---

## Quality Gates

### Before Commit

```
[ ] Build succeeds
[ ] Tests pass (including new tests)
[ ] Edge cases tested (see list above)
[ ] Error paths tested
[ ] No debug code left
[ ] LOC check (not over budget)
```

### Before Shipping

```
[ ] All commit gates pass
[ ] Full test suite green
[ ] Human review completed (if triggered)
[ ] Manual testing of user flows
[ ] Edge case scenarios manually verified
[ ] Error states manually verified
```

---

## Asking Claude for Quality

### After Any Implementation

```
Review this code for AI-typical issues:

1. Happy-path bias - are error cases handled?
2. Edge cases - what inputs weren't considered?
3. Verbosity - can this be simpler?
4. Confidence mismatch - are you sure this works?

For each issue, suggest a specific fix and test.
```

### Weekly Codebase Health Check

```
Analyze this codebase for health:

1. Total LOC (target: under [X])
2. Largest files (flag > 400 lines)
3. Test coverage gaps
4. Unused code
5. Complexity hotspots

Provide specific recommendations.
```

---

## Quick Reference

```
AI code review mantra:
├── "What edge cases exist?"
├── "What error paths exist?"
├── "What if this is wrong?"
├── "Can this be simpler?"
└── "Is this tested?"

Thresholds:
├── > 20k LOC → Get external review
├── > 500 LOC change → Careful self-review
├── Security/money → Human review required
└── > 7 features → Map interactions
```

---

*AI lowers the barrier to writing code. It doesn't lower the bar for shipping quality.*
