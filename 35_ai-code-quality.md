<!--
TRIGGERS: vibe code, AI code, generated code, codebase size, LOC, complexity, edge case, review threshold, common mistakes, skipping the spec, giant feature, TODO accumulation
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

Use `34_testing.md` for proportional test selection, startup effects and evidence requirements.
Assess the changed behavior and its risks; the prompts below are review aids, not a requirement
to add a test for every listed possibility or rerun unrelated checks. Required acceptance remains open
until its evidence exists.

### 1. Edge Case Assessment

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

### 2. Error Path Assessment

AI code often has optimistic error handling. Require:

```
Show me every error path in this code.

For each path:
1. What triggers it?
2. Is it tested?
3. What does the user see?
4. Is it logged?

Add focused tests for relevant error paths where risk or complexity warrants them;
reuse valid existing coverage and record any remaining verification gap.
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

1. **Establish relevant current behavior**
   ```
   Before modifying [file/function]:
   1. Inspect affected code, callers and existing tests; batch independent reads
   2. Run relevant baseline checks when needed to distinguish pre-existing failures
   3. Record actual behavior, intended requirements and any relevant existing failures
   ```

2. **After modification, verify:**
   - Run checks for changed behavior and affected integrations; broaden for shared contracts or risk
   - Add or update tests when they protect meaningful behavior; trivial reversible edits may use inspection
   - Compare failures with baseline evidence; do not require unrelated repairs or hide new regressions
   - Repeat checks when changed code, failures or unresolved concerns justify it; preserve valid results
   - Keep unperformed required acceptance explicit; a focused pass does not establish release readiness

### The "Break It" Test

After AI "fixes" something:

```
This code was just modified. Try to break it:

1. What inputs would cause unexpected behavior?
2. What state combinations weren't considered?
3. What happens under load?
4. What happens with slow/failing dependencies?

Choose discriminating checks for plausible affected scenarios; automate when the risk warrants it.
```

---

## Quality Gates

### Before Commit

Apply checks appropriate to the changed files under `34_testing.md`; documentation-only edits do
not need an app build. Record pre-existing failures and blocked/not-run checks with their impact.

```
[ ] Applicable build/checks pass; failures and verification gaps are identified
[ ] Relevant tests pass; new or updated coverage added where warranted
[ ] Affected edge cases and error paths verified in proportion to risk
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

## Common AI-Assisted Development Mistakes

### Mistake 1: Skipping the Spec Interview

**Symptom:** Claude builds something, but it's not what you wanted.

**Fix:** Use `commands/spec.md` for new or uncertain scope; reuse known requirements and skip a new
interview for routine fixes or approved implementation.

### Mistake 2: One Giant Feature

**Symptom:** Working for days, nothing works yet.

**Fix:** Plan independently verifiable outcomes under `commands/make-plan.md`. Split by coupling,
risk and validation needs rather than a fixed duration.

### Mistake 3: Trusting Single AI Review

**Symptom:** "Claude said it looks good" → bug in production.

**Fix:** Adversarial review. Second model for critical code.

### Mistake 4: No Verification Loop

**Symptom:** "Build succeeded" but feature doesn't work.

**Fix:** Tell Claude how to verify. Watch it actually test.

### Mistake 5: Accumulating TODO Items

**Symptom:** 200-item wishlist, 0% completion.

**Fix:** NOW/NEXT/LATER. Maximum 5 items in NOW.

### Mistake 6: Not Documenting the WHY

**Symptom:** You fix a bug, then "improve" the code later, bug returns.

**Fix:** When you find a tricky bug, ask Claude:
```
Add a comment explaining WHY this code is written this way.
Include a reference to this conversation or a bug file.
```

Example:
```swift
// WARNING: DO NOT CHANGE
// originalSize must use cgImage dimensions (PIXELS), not nsImage.size (POINTS)
// On Retina displays, they differ by 2x
// This caused crop bugs that took 3 sessions to diagnose
// See: CropBatch-BUGFIX-retina-crop-position.md
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
