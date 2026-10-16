# Context Examples (Optional)

Worked examples for [Context Management](../52_context-management.md). Load only when designing
project documentation or shaping a concrete request. These are illustrative project conventions,
not universal Swift rules or a second workflow. Execution and lifecycle actions belong to
[execute](../commands/execute.md) and [log](../commands/log.md).

## The Router Pattern

Create a lean project entry point that serves as a router, with detailed docs split into topic-specific
files loaded only when needed. Use `AGENTS.md` for Codex and `CLAUDE.md` for Claude Code.

### Directory Structure

```
project/
├── AGENTS.md                    # Codex entry point (when used)
├── CLAUDE.md                    # Claude Code entry point (when used)
├── docs/
│   ├── frontend-guidelines.md   # Loaded only for frontend work
│   ├── backend-api-patterns.md  # Loaded only for backend work
│   ├── testing-standards.md     # Loaded only when writing tests
│   ├── deployment-guide.md      # Loaded only for deployment
│   └── security-guidelines.md   # Loaded only for auth/security
└── src/
    ├── frontend/                # Optional nested host entry point
    └── backend/                 # Optional nested host entry point
```

### Basic Router Example

**Main entry point (`AGENTS.md` or `CLAUDE.md`):**

```markdown
# Project: My App

## Core Stack
- Frontend: SwiftUI
- Backend: Swift actors
- Persistence: JSON files

## Essential Rules (Always Apply)
- Use async/await, never completion handlers
- ViewModels must be @MainActor
- Services must be actors

## Conditional Documentation
**Read these files ONLY when working on specific tasks:**

### UI Work
- **When:** Modifying Views or ViewModels
- **Read:** @docs/swiftui-patterns.md
- **Contains:** Component patterns, state management

### Data Layer
- **When:** Working on Services or persistence
- **Read:** @docs/data-architecture.md
- **Contains:** Actor patterns, JSON persistence

### Testing
- **When:** Writing or fixing tests
- **Read:** @docs/testing-standards.md
- **Contains:** Test structure, mocking patterns

## How to Use This Documentation
1. Read this main file first
2. Identify which conditional docs apply to your task
3. Read ONLY the relevant conditional docs
4. Do NOT load all docs simultaneously
```

## The "Pitch" Pattern

Explain **why** and **when** to read files—this improves an agent's loading decisions:

```markdown
## Extended Documentation (Load Conditionally)

### Coordinate Systems Documentation
**File:** @docs/coordinate-systems.md
**When to read:**
- If working with image cropping or positioning
- When debugging "off by 2x" visual bugs
- If mixing NSImage and CGImage operations
**Why it matters:**
Contains Retina scaling rules and origin system documentation
that prevents the #1 category of image processing bugs.
**DO NOT load immediately — only access for image/video work.**

### Thread Safety Patterns
**File:** @docs/concurrency-patterns.md
**When to read:**
- If creating new Services or Managers
- When debugging race conditions or crashes
- If seeing @MainActor or Sendable errors
**Why it matters:**
Our actor patterns differ from basic examples — specific
isolation rules that must be followed.
**For simple View work, you do NOT need this file.**
```

## Nested Entry-Point Pattern

Codex composes root and nested `AGENTS.md` instructions, with closer files applying to their subtree.
Claude Code has its own nested `CLAUDE.md` discovery rules. Do not assume the two hosts use identical
loading mechanics; see `64_codex.md` and `23_claude-code-cli.md`.

The example below uses Claude Code naming:

**How it works:**
- **Root CLAUDE.md**: Always loaded at session start
- **Subdirectory CLAUDE.md**: Loaded only when Claude reads/edits files in that directory

### Example Structure

**Root CLAUDE.md:**
```markdown
# My App

## Global Standards
- Swift 5.9+
- SwiftUI for all UI
- async/await for concurrency

## Directory-Specific Context
Each module has its own CLAUDE.md with specialized rules.
These load automatically when you work in that directory.
```

**Sources/Views/CLAUDE.md:**
```markdown
# Views Module Context

## Patterns
- All Views are structs
- Use @Observable ViewModels
- Co-locate View and ViewModel

## State Management
- @State for view-local only
- @Environment for shared state
- Never mutate state during body computation
```

**Sources/Services/CLAUDE.md:**
```markdown
# Services Module Context

## Requirements
- ALL services must be actors
- Use async/await exclusively
- Cache results where appropriate

## Error Handling
- Never use try? silently
- Log errors with context
- Propagate to UI layer
```

## Explicit Trigger Language

### Weak (Often Ignored)

```markdown
See docs/testing.md for testing information.
```

### Strong (Reliably Followed)

```markdown
**IMPORTANT: Before writing ANY tests, you MUST read @docs/testing-standards.md**

This file contains:
- Required test structure patterns
- Mocking strategies for our architecture
- Coverage requirements that fail CI if not met

DO NOT attempt to write tests without reading this file first.
```

## "DO NOT Load" Directives

Explicitly tell the active agent **not** to load files immediately:

```markdown
## API Documentation Reference

**File:** @docs/api/openapi-spec.md

**DO NOT load this file at session start.**

**Only read when:**
- Implementing new API endpoints
- User asks about API contract
- Debugging API integration issues

**Why wait:** This file is 15,000 tokens. Loading it for
non-API work wastes context.
```

## Custom Loading Commands

Create slash commands to explicitly load context:

**File: `.claude/commands/study.md`**
```markdown
# /study Command

When user types `/project:study authentication`:
1. Read @docs/auth/authentication-flow.md
2. Read @docs/auth/security-patterns.md
3. Summarize key points
4. Say "Auth context loaded. Ready to work."

When user types `/project:study frontend`:
1. Read @docs/swiftui-patterns.md
2. Read Sources/Views/CLAUDE.md
3. Summarize component patterns
4. Say "Frontend context loaded."
```

**Usage:**
```
> /project:study authentication
[Claude loads all auth docs]
> Now implement token refresh logic
[Claude applies loaded context]
```


## Planning Level by Task Size

Choose depth by uncertainty, coupling and verification needs, not elapsed-time estimates. Follow
current commands and explicit limits, including no commits or no delegation.

| Task Type | Planning Level |
|-----------|---------------|
| Clear isolated fix | Inspect, change and validate directly; commit only within authorization |
| Bounded feature with known behavior | Record acceptance and dependencies at matching depth |
| Coupled feature with unresolved requirements | Spec and dependency-aware plan before broad implementation |
| Architecture changes | Full planning + decisions.md |
| New project | Full setup of all files |

---


## Information Design Examples

## What Makes Good Context

### 1. Relevant Code

Don't just reference files — show them:

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
"Ignore the UI code in this file — we're only changing the data layer.
Focus on the Repository class."
```

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

````markdown
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
````

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
