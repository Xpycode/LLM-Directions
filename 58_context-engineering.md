<!--
TRIGGERS: context, prompt engineering, LLM context, information environment, AI assistance
PHASE: any
LOAD: on-request
-->

# Context Engineering

**Treat AI interaction as constructing complete information environments.**

*Based on the "Context Engineering" concept from Beyond Vibe Coding.*

---

## The Shift

| Prompt Engineering | Context Engineering |
|--------------------|---------------------|
| "Write a good prompt" | "Build a complete information environment" |
| One-shot interaction | Assembled context + prompt |
| Hoping AI guesses right | AI has what it needs |
| Retry until it works | Structured for success |

Context engineering is about what information the AI has access to, not just what you ask.

---

## The Context Stack

Every AI interaction operates on a context stack:

```
┌─────────────────────────────────────┐
│  Your Prompt (current request)      │  ← What you're asking
├─────────────────────────────────────┤
│  Conversation History               │  ← Recent exchanges
├─────────────────────────────────────┤
│  Active Files (code, specs)         │  ← What's been read
├─────────────────────────────────────┤
│  System Instructions (CLAUDE.md)    │  ← Persistent context
├─────────────────────────────────────┤
│  Model Knowledge (training)         │  ← Built-in capabilities
└─────────────────────────────────────┘
```

You control the top 4 layers. Use them.

---

## What Makes Good Context

### 1. Relevant Code

Don't just reference files—show them:

| Weak | Strong |
|------|--------|
| "Fix the bug in auth.swift" | "Here's auth.swift: [code]. The bug is on line 42." |
| "Make it like the other one" | "Here's the pattern from user.swift: [code]. Apply to order.swift." |

### 2. Specific Constraints

State boundaries explicitly:

| Weak | Strong |
|------|--------|
| "Make it fast" | "Must handle 1000 items with <200ms render time" |
| "Keep it simple" | "No new dependencies. Under 50 lines." |
| "Make it secure" | "Sanitize inputs. No raw SQL. Use parameterized queries." |

### 3. Examples

Concrete examples beat abstract descriptions:

| Weak | Strong |
|------|--------|
| "Format like our other code" | "Follow this style: [example snippet]" |
| "Good error messages" | "Error format: 'Failed to [action]: [reason]. Try [suggestion].'" |

### 4. Error Messages

Full errors, not summaries:

| Weak | Strong |
|------|--------|
| "It crashed" | "Error: 'index out of range' at line 42 with input [x]" |
| "Didn't work" | "Expected: [x]. Got: [y]. Steps to reproduce: [steps]" |

---

## The Context Checklist

Before asking the AI to do something:

### For Bug Fixes
- [ ] The error message (full, not summarized)
- [ ] The code where the error occurs
- [ ] What input caused it
- [ ] What you expected vs what happened

### For New Features
- [ ] The specification or acceptance criteria
- [ ] Related existing code (patterns to follow)
- [ ] Constraints (performance, dependencies, style)
- [ ] Examples of desired behavior

### For Refactoring
- [ ] The current code
- [ ] Why it needs changing
- [ ] What patterns to apply
- [ ] What must NOT change (contracts, APIs)

### For Architecture Decisions
- [ ] The problem we're solving
- [ ] Constraints (scale, team, timeline)
- [ ] Options we're considering
- [ ] Trade-offs that matter to us

---

## Context Loading Patterns

### Progressive Loading

Start with summary, load details as needed:

```
1. "Here's the project overview" (CLAUDE.md)
2. "We're working on feature X" (spec)
3. "This is the relevant file" (code)
4. "This is the specific function" (focused)
```

### Just-In-Time Context

Load context right before it's needed:

```
"Before we implement caching, let me show you our current data flow:
[code snippet]

Now, add caching that works with this pattern."
```

### Explicit Boundaries

Tell the AI what context is NOT relevant:

```
"Ignore the UI code in this file—we're only changing the data layer.
Focus on the Repository class."
```

---

## Structured Context Formats

### For Code Changes

```markdown
## Current State
[code as it exists now]

## Problem
[what's wrong or missing]

## Desired State
[what it should do]

## Constraints
- [constraint 1]
- [constraint 2]
```

### For Bug Reports

```markdown
## Symptom
[what user sees]

## Expected
[what should happen]

## Actual
[what happens instead]

## Error
```
[full error message]
```

## Code
[relevant code]
```

### For Feature Requests

```markdown
## User Story
As a [user], I want [action] so that [benefit]

## Acceptance Criteria
- Given [X], when [Y], then [Z]

## Related Code
[existing patterns to follow]

## Constraints
[limits and requirements]
```

---

## Anti-Patterns

| Anti-Pattern | Problem | Fix |
|--------------|---------|-----|
| **Vague reference** | "Fix the thing" | Show the code, state the problem |
| **Missing error** | "It doesn't work" | Include full error message |
| **Assumed knowledge** | "Like we discussed" | Re-state key points |
| **Context dump** | [entire codebase] | Load only relevant parts |
| **No constraints** | "Make it better" | State specific requirements |
| **Stale context** | Old file in chat | Re-read files before referencing |

---

## Context for Directions

The Directions system is designed for context engineering:

| File | Provides Context For |
|------|---------------------|
| `CLAUDE.md` | Project-wide patterns and preferences |
| `PROJECT_STATE.md` | Current focus, phase, blockers |
| `specs/[feature].md` | Feature requirements and acceptance criteria |
| `decisions.md` | Why things are the way they are |
| `AGENTS.md` | Subagent patterns and constraints |

### Loading Order

```
1. 00_base.md        → How this system works
2. PROJECT_STATE.md  → Where we are now
3. specs/current.md  → What we're building
4. Relevant code     → What we're changing
```

---

## Claude Instructions

Add to CLAUDE.md:

```markdown
## Context Discipline

Before coding:
1. Read the relevant spec (if exists)
2. Read the code being modified
3. Note any patterns to follow
4. State constraints explicitly

When asking me to do something:
- Show me the code
- Tell me the constraints
- Give examples if style matters
- Include full error messages
```

---

*The AI is only as good as the context you give it.*
