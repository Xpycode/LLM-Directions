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

```markdown
# [Feature Name] Specification

**Status:** Draft | Review | Approved | Implementing | Complete
**Created:** YYYY-MM-DD
**Last Updated:** YYYY-MM-DD

---

## Problem Statement

### What problem does this solve?
[One paragraph describing the pain point or opportunity]

### Who has this problem?
[User persona or context]

### How do they solve it today?
[Current workaround or competing solution]

---

## Proposed Solution

### One-Liner
[Single sentence describing what we're building]

### Key Capabilities
1. [Capability 1]
2. [Capability 2]
3. [Capability 3]

### User Flow
1. User opens [X]
2. User does [Y]
3. System responds with [Z]
4. User sees [result]

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
1. /interview         → Gather requirements
2. Create spec        → Use this template
3. Review spec        → Check for gaps, contradictions
4. Get approval       → User confirms understanding
5. /plan             → Break into tasks
6. Reference during build → Spec is source of truth
```

---

## Spec Review Checklist

Before moving to `/plan`:

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

*Spec first, code second. The 20% upfront prevents the 80% rework.*
