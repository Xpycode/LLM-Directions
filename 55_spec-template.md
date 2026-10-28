<!--
TRIGGERS: spec, specification, requirements, PRD, mini-PRD, feature doc, before coding
PHASE: define
LOAD: on-request
-->

# Spec Template (Mini-PRD)

**Write the spec before writing the code.**

*Based on the "plan before coding" principle from Beyond Vibe Coding.*

---

## Why Specs Matter

The "70% Problem": Vibe coding gets you 70% there fast, but the last 30% becomes extremely challenging without proper specifications.

| Without Spec | With Spec |
|--------------|-----------|
| "Just start coding" | Clear scope before code |
| Scope creep mid-build | Boundaries documented |
| "What was I building again?" | Reference during implementation |
| Endless iteration | Defined done criteria |

---

## The SPEC.md Template

Create `specs/[feature-name].md` with this structure:

For a new project or substantial uncommitted expansion, use `commands/spec.md` → **New-project
assessment** first. Keep its conclusion in the fields below; omit conditional fields for routine
work and link an existing decision rather than copying it. Use-existing/park outcomes need no spec.

```markdown
# [Feature Name] Specification

**Status:** Draft | Review | Approved | Implementing | Complete
**Created:** YYYY-MM-DD
**Last Updated:** YYYY-MM-DD

---

## Problem Statement

### What problem does this solve?
[Intended benefit: personal utility, release, learning, enjoyment or craft; smallest worthwhile outcome]

### Who has this problem?
[User persona or context]

### How do they solve it today?
[Current workaround/alternatives; a recent concrete shortcoming, frequency and cost where relevant]

For a new commitment only (omit for routine work):

- Choice and why now: [Selected approach and reason, or link to the existing decision]
- Investment and trade-off: [Time/attention and maintenance worth spending; what gets less attention]
- Reconsider when: [Critical assumption fails, investment limit reached or scope materially expands]

---

## Proposed Solution

### One-Liner
[Single sentence describing what we're building]

### Key Capabilities
1. [Capability 1]
2. [Capability 2]
3. [Capability 3]

### User Flow
1. Source/input: [Concrete starting data and location]
2. User action: [What the user does]
3. Destination/output: [Where the result goes]
4. Observable outcome: [What proves success to the user]

### Usefulness or Feasibility Check (when needed)
- Uncertainty: [Critical benefit assumption or technical feasibility question; distinguish the two]
- Smallest check: [Representative task/data or demonstration of learning]
- Observable result: [Expected observation and contrary result that would change the decision]
- Agreed limit: [Scope/resources authorized for this experiment]
- Stop/replan: [Failure, limit or expansion condition; decide continue, simplify, replace or park]
- New subsystems: [Require a scoped decision before expansion]
- Result: [Observation and decision, or not run; inconclusive evidence leaves the assumption unresolved]

---

## Acceptance Criteria

> Use Given/When/Then format for testability.
> See 56_acceptance-criteria.md for guidance.

### Core Functionality
- [ ] Given [precondition], when [action], then [result]
- [ ] Given [precondition], when [action], then [result]

### Edge Cases
- [ ] Given [edge case], when [action], then [graceful handling]

### Error States
- [ ] Given [failure condition], when [action], then [error message/recovery]

---

## Technical Considerations

### Dependencies
- [Library/framework needed]
- [API/service required]

### Architecture Notes
- [Pattern to follow]
- [Integration point]

### Performance
- [Latency requirement]
- [Data size consideration]

### Security
- [Authentication need]
- [Data sensitivity]

---

## Out of Scope

Explicitly excluded from this spec:
- [Feature we're NOT building]
- [Edge case we're deferring]
- [Platform we're not supporting yet]

---

## Open Questions

| Question | Status | Answer |
|----------|--------|--------|
| [Unresolved question] | Open | - |
| [Answered question] | Resolved | [Answer] |

---

## Related

- Decisions: [link to decisions.md entry]
- Previous specs: [link if iterating]
- Sessions: [link to discovery session]
```

---

## Spec Types by Scope

| Scope | Spec Depth | Example |
|-------|-----------|---------|
| Quick fix | No spec needed | Typo fix, config change |
| Minor feature | Light spec (Problem + Acceptance) | Add a button, new field |
| Major feature | Full spec | New screen, workflow |
| Architecture change | Full spec + ADR | Database change, new service |

---

## Spec Workflow

```
1. /spec deep         → Gather requirements
2. Create spec        → Use this template
3. Review spec        → Check for gaps, contradictions
4. Get approval       → User confirms understanding
5. /make-plan             → Break into tasks
6. Reference during build → Spec is source of truth
```

---

## Spec Review Checklist

Before moving to `/make-plan`:

- [ ] Problem statement is clear (not solution-focused)
- [ ] Acceptance criteria are testable (Given/When/Then)
- [ ] Edge cases are documented
- [ ] Out of scope is explicit
- [ ] Open questions are resolved or noted as blockers
- [ ] Technical considerations cover dependencies
- [ ] Security implications considered

---

## Anti-Patterns

| Anti-Pattern | Problem | Fix |
|--------------|---------|-----|
| Solution-first spec | Biases toward one approach | Focus on problem, explore options |
| Vague acceptance | "It should work well" | Use Given/When/Then |
| Missing edge cases | Discovered during build | Ask "What if [unusual input]?" |
| Scope creep in spec | Everything becomes v1 | Use Out of Scope aggressively |
| No spec at all | 70% problem | Write spec before code |

---

*Resolve uncertainty and define observable success before substantial implementation.*
