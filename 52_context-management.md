<!--
TRIGGERS: context, token limit, context too big, CLAUDE.md bloated, large project,
          context rot, compacting, /compact, /clear, prompt engineering,
          information environment, progressive loading, router pattern
PHASE: any
LOAD: on-request
-->

# Context Management

*The complete guide to AI context: how to structure your docs, how to manage
context during sessions, and what information to actually put in it.*

This is the canonical context doc. It merges three earlier guides:
- Progressive Context Loading (was `50_progressive-context.md`)
- Context Management (was `52_context-management.md`)
- Context Engineering (was `58_context-engineering.md`)

The old paths now redirect here.

---

## The Three Layers

Context problems show up at three different levels. Each needs its own discipline:

| Layer | What it controls | Symptom when wrong |
|-------|------------------|---------------------|
| **Architecture** | How your project's docs are structured | CLAUDE.md is 400 lines, 90% irrelevant to current task |
| **Runtime** | How context behaves during a session | Quality degrades after 70%; Claude forgets earlier instructions |
| **Information design** | What you actually put in the context | "Fix the bug" without code, errors, or constraints — vague results |

Get all three right and you ship 2-3x faster with fewer corrections.

---

# Part 1 — Architecture: Progressive Context Loading

*From 150K to 2K tokens: the router pattern for large projects.*

## The Problem

As projects grow, monolithic CLAUDE.md files become problematic:

| Issue | Impact |
|-------|--------|
| **Token waste** | 400+ line CLAUDE.md consumes context even when 90%+ is irrelevant |
| **Attention dilution** | Claude tries to follow all rules simultaneously → confusion |
| **Maintenance overhead** | One giant file becomes unwieldy |

**Solution:** Progressive context loading — load only documentation relevant to the current task.

## The Router Pattern

Create a **lean main CLAUDE.md** (50-100 lines) that serves as a router, with detailed docs split into topic-specific files loaded only when needed.

### Directory Structure

```
project/
├── CLAUDE.md                    # Main router (lean, always loaded)
├── docs/
│   ├── frontend-guidelines.md   # Loaded only for frontend work
│   ├── backend-api-patterns.md  # Loaded only for backend work
│   ├── testing-standards.md     # Loaded only when writing tests
│   ├── deployment-guide.md      # Loaded only for deployment
│   └── security-guidelines.md   # Loaded only for auth/security
└── src/
    ├── frontend/
    │   └── CLAUDE.md            # Nested context for frontend/
    └── backend/
        └── CLAUDE.md            # Nested context for backend/
```

### Basic Router Example

**Main CLAUDE.md:**

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

Explain **why** and **when** to read files — dramatically improves Claude's loading decisions:

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

## Nested CLAUDE.md Pattern

Claude Code automatically discovers nested CLAUDE.md files in subdirectories.

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

Explicitly tell Claude **not** to load files immediately:

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

## Token Reduction Results

Real-world data from production implementations:

| Approach | Tokens | Reduction |
|----------|--------|-----------|
| Monolithic CLAUDE.md | 150,000 | Baseline |
| Basic modularization | 45,000 | 70% |
| Conditional router pattern | 8,000 | **95%** |
| Skills-based progressive loading | 2,000 | **98.7%** |

**Benefits:**
- 3-5x faster response times
- Lower costs (fewer input tokens)
- Better focus (Claude sees only relevant rules)

## Recommended by Project Size

| Project Size | Approach | Strategy |
|--------------|----------|----------|
| **Small** (<10K LOC) | Single CLAUDE.md | Monolithic (50-150 lines) |
| **Medium** (10-50K LOC) | Router + 3-5 domain docs | Conditional routing |
| **Large** (50-200K LOC) | Nested CLAUDE.md + router | Hierarchical |
| **Very Large** (200K+ LOC) | Claude Skills | Progressive loading |
| **Multi-repo** | Sub-agent orchestration | Specialized agents |

## Sub-Agent Orchestration

For very large projects, use orchestration with specialized Claude instances.

**Root CLAUDE.md (orchestrator):**
```markdown
# Orchestrator Agent

## Your Role
You are a coordinator, NOT an implementer.
You DO NOT modify code files directly.

## How to Accomplish Tasks
1. Identify which module is affected
2. Spawn a headless Claude instance in that subdirectory:
   ```bash
   cd src/frontend && claude --headless "implement feature"
   ```
3. The subdirectory Claude loads its own specialized CLAUDE.md
4. Monitor progress and coordinate between modules
5. Report back to user with summary
```

**Benefits:**
- Each domain Claude has focused context
- Root orchestrator maintains coordination
- Total context never exceeds single-domain scope

## Migration Strategy

### Week 1: Audit and Categorize

Categorize every CLAUDE.md section:
- Core (always needed)
- Frontend (conditional)
- Backend (conditional)
- Testing (conditional)
- Domain-specific (conditional)

### Week 2: Extract Domain Files

```bash
mkdir -p docs/{frontend,backend,testing,deployment,security}

# Move frontend rules to docs/frontend-guidelines.md
# Move backend rules to docs/backend-api-patterns.md
# etc.
```

### Week 3: Create Router CLAUDE.md

```markdown
# New lean CLAUDE.md (50-100 lines max)

## Core Rules (10-20 lines)
[Only universal rules for EVERY task]

## Conditional Documentation (30-60 lines)
[Routing table with "when to read" conditions]
```

### Week 4: Test and Iterate

- Verify Claude loads correct docs automatically
- Verify Claude doesn't over-load docs
- Use `/context` to check what's loaded
- Adjust trigger language if needed

## Router Template

Copy this as a starting point:

```markdown
# [Project Name]

## Core Stack
- [Language/Framework]
- [Key libraries]

## Essential Rules (Always Apply)
- [Rule 1 - applies to everything]
- [Rule 2 - applies to everything]
- [Rule 3 - applies to everything]

## Conditional Documentation

### [Domain 1] Work
- **When:** [Trigger conditions]
- **Read:** @docs/[domain1]-guidelines.md
- **Contains:** [What's in the file]
- **DO NOT load unless working on [domain1]**

### [Domain 2] Work
- **When:** [Trigger conditions]
- **Read:** @docs/[domain2]-patterns.md
- **Contains:** [What's in the file]
- **DO NOT load unless working on [domain2]**

## How to Use This Documentation
1. Read this main file first (you're doing it now)
2. Based on your current task, identify which conditional docs apply
3. Read ONLY the relevant conditional docs before starting work
4. Do NOT load all docs simultaneously — focus on what's needed
```

---

# Part 2 — Runtime: Managing Context During Sessions

*Preventing context rot in long sessions.*

## The Problem: Context Rot

As Claude's context window fills up, quality degrades:
- Earlier instructions get "forgotten"
- Responses become less precise
- Code quality drops
- Repetition increases

This part combines Directions' project memory with execution patterns from
[Get Shit Done](https://github.com/glittercowboy/get-shit-done).

## Core Principles

### 1. File Size Limits

Every file has a purpose and a size constraint:

| File | Purpose | Limit |
|------|---------|-------|
| `PROJECT_STATE.md` | Current position | <80 lines |
| `PLAN.md` | Active execution | Delete when done |
| `RESUME.md` | Session bridge | Delete after use |
| Session logs | Daily record | ~200 lines |
| `decisions.md` | Decision history | Grows (but summarize in PROJECT_STATE) |

**Why?** Small, focused files = fast context loading = better quality.

### 2. Temporary vs Permanent Files

**Permanent (project memory):**
- `PROJECT_STATE.md` — source of truth for position
- `decisions.md` — architectural history
- `sessions/*.md` — daily logs
- `CLAUDE.md` — project instructions

**Temporary (execution artifacts):**
- `PLAN.md` — delete after execution completes
- `RESUME.md` — delete after resuming

Temporary files prevent stale context from accumulating.

### 3. Orchestrator Pattern

The main conversation should never exceed 40% context.

```
Main Context (orchestrator)
├── Reads PROJECT_STATE.md, PLAN.md
├── Spawns subagents for heavy work
├── Collects results
├── Updates state files
└── Never does implementation directly

Subagent (fresh context)
├── Receives only: task description, target files, success criteria
├── No session history
├── Does one atomic task
├── Returns result
└── Context discarded
```

### 4. Wave-Based Execution

Group tasks by dependency, execute in waves:

```
Wave 1: [A] [B] [C]  ← parallel, independent
         ↓ complete
Wave 2: [D] [E]      ← depend on Wave 1
         ↓ complete
Wave 3: [F]          ← verification
```

Each task in a wave runs in a fresh subagent context.

### 5. The 70% Rule

Community-derived guideline: treat ~70% context usage as your practical ceiling.

| Zone | Usage | Action |
|------|-------|--------|
| **Green** | 0-50% | Carry on |
| **Yellow** | 50-70% | Start thinking about compacting |
| **Orange** | 70-85% | Don't read more files than needed. Prepare to compact |
| **Red** | 85-95% | Stop new work. Compact now |
| **Critical** | 95%+ | `/clear` immediately, create a handoff document first |

Response quality starts dipping before auto-compact triggers at ~95%. Keep headroom for complex tasks.

### 6. Checking Context Usage

**The `/context` command** shows token breakdown:
```
claude-sonnet-4-20250514 * 17k/200k tokens (8%)
Breakdown:
- System prompt: 3,200 tokens (1.6%)
- System tools: 11,600 tokens (5.8%)
- Custom agents: 69 tokens (0.0%)
- Memory files: 743 tokens (0.4%)
- Messages: 1,200 tokens (0.6%)
- Free space: 183,300 tokens (91.6%)
```

**Typical context breakdown:**

| Category | Percentage |
|----------|-----------|
| System instructions | 5-10% (always present) |
| Tool definitions (MCP, skills) | 5-15% (even if not used!) |
| CLAUDE.md files | 1-5% |
| Conversation history | 40-70% (the big one) |
| Response buffer | 10-20% |

**Status bar shortcut:** `Ctx(u): 56.0%` — this percentage is the one to watch. Configure via `/terminal-setup`.

**When to check:**
- Start of each session (know your baseline)
- When responses feel slower or less precise
- After installing new MCP servers or skills
- Before starting something complex

### 7. What Degradation Looks Like

Signs appear in this order:
1. **Terse answers** where Claude used to give detailed ones
2. **Context bleeding** — confusing current task with something discussed earlier
3. **Lost instruction following** — style preferences and rules from earlier get ignored
4. **Confident mistakes** — contradicts things it said earlier without awareness
5. **Inconsistent responses** — verbose then terse, cautious then reckless

By the time you notice symptoms, quality has already been degrading for a while.

### 8. Compaction Guidance

**When to compact:**
- After finishing a feature (natural breakpoint)
- Before switching to a different area of the codebase
- Proactively at 65-70%, before symptoms appear
- Every 60-90 minutes or every 25-30 messages

**Compact with focus instructions (recommended):**
```
/compact Focus on the API changes
/compact Prioritise test output and code changes
/compact Preserve the full list of modified files
```

**Add to your CLAUDE.md:**
```markdown
# Compact instructions
When compacting, always preserve:
- Full list of modified files
- Test commands used
- Key architectural decisions
```

**`/clear` vs `/compact`:**
- `/clear` — switching to unrelated work, context over 80%, starting fresh would be faster
- `/compact` — need to preserve task context, continuing related work, hit a milestone in same domain

### 9. Context-Saving Strategies

**Use CLAUDE.md for persistent instructions:** Instructions in conversation consume
context every time. CLAUDE.md instructions consume context once and stay across
sessions. Move repeated guidance there (coding style, conventions, terminology).
Keep CLAUDE.md under 500 lines.

**Use skills instead of CLAUDE.md for workflow-specific instructions:** Skills load
on-demand only when invoked, saving context until needed.

**Subagents for research:** Each subagent runs in its own context window. Verbose
output stays there. Only the relevant summary returns to your session. One of the
most effective context-saving techniques.

**Disable unused MCP servers:** MCP servers consume tokens just by existing (tool
definitions always loaded). Disable via `/mcp` to reclaim context. CLI tools like
`gh`, `aws`, `gcloud` don't have this overhead.

**Write specific prompts:**
- Vague: `Improve this codebase` (triggers broad scanning, eats context)
- Specific: `Add input validation to the login function in auth.ts` (minimal file reads)

**Name and save sessions:**
```
/rename oauth-migration
/clear
# Later:
/resume oauth-migration
```

## The Hybrid Workflow

### For Discovery/Planning (Directions-style)
1. `/interview` — gather requirements
2. `/decide` — record decisions
3. `/log` — track sessions
4. `PROJECT_STATE.md` — maintain position

### For Implementation (GSD-style)
1. Create `PLAN.md` with waves and tasks
2. `/execute` — run wave-based execution
3. Subagents do heavy lifting with fresh contexts
4. Atomic commits per task
5. Delete `PLAN.md` when done

### For Session Handoff
1. Create `RESUME.md` with exact next step
2. Update `PROJECT_STATE.md`
3. New session reads `RESUME.md` first
4. Delete `RESUME.md` after resuming

## Practical Commands

### Starting a Session
```
1. Read PROJECT_STATE.md (current position)
2. Check for RESUME.md (if exists, that's your starting point)
3. Read latest session log (recent context)
```

### Ending a Session Mid-Task
```
1. Create RESUME.md with exact next action
2. Update PROJECT_STATE.md status
3. Commit any work in progress
```

### Implementing a Feature
```
1. Create PLAN.md with tasks grouped into waves
2. Run /execute
3. Subagents execute each task with fresh context
4. Each task = one atomic commit
5. Delete PLAN.md when complete
6. Update PROJECT_STATE.md
```

### Context Getting Full
```
1. Create RESUME.md with current state
2. Complete current task if possible
3. Commit work
4. Tell user: "Context is full. Run /execute to continue with fresh agents."
```

---

# Part 3 — Information Design: Context Engineering

*Treat AI interaction as constructing complete information environments.*

Based on the "Context Engineering" concept from *Beyond Vibe Coding*.

## The Shift

| Prompt Engineering | Context Engineering |
|--------------------|---------------------|
| "Write a good prompt" | "Build a complete information environment" |
| One-shot interaction | Assembled context + prompt |
| Hoping AI guesses right | AI has what it needs |
| Retry until it works | Structured for success |

Context engineering is about *what information the AI has access to*, not just what you ask.

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

# Part 4 — Anti-Patterns (Consolidated)

### Architecture anti-patterns

| Anti-Pattern | Problem | Fix |
|--------------|---------|-----|
| **Monolithic CLAUDE.md** | 400+ lines always loaded; 90% irrelevant | Router pattern + conditional docs |
| **Claude ignores conditionals** | All @-referenced files load immediately | Use "**DO NOT load**" directives; separate references from instructions |
| **Nested CLAUDE.md not loading** | Subdirectory rules ignored | Claude loads nested CLAUDE.md only when reading/writing files in that dir — instruct it explicitly |
| **Weak trigger language** | "See docs/testing.md" — gets ignored | Use IMPORTANT/MUST + explicit "before X you MUST read Y" |

### Runtime anti-patterns

| Anti-Pattern | Problem | Fix |
|--------------|---------|-----|
| **The Kitchen Sink** | Mixing unrelated tasks fills context with noise | `/clear` between unrelated tasks |
| **The Correction Spiral** | Three rounds of corrections = half the context is failed approaches | After 2 failed corrections, `/clear` + rewrite the prompt |
| **Heavy work in main context** | Orchestrator does implementation directly | Spawn subagents; orchestrator stays light |
| **Stale temp files** | `PLAN.md`/`RESUME.md` linger after use | Delete aggressively when done |
| **Bloated session logs** | Logs grow past 200 lines | Summarize, archive old details to decisions.md |
| **Just-in-case context** | Reading files "in case we need them" | Load only what the current task requires |

### Information design anti-patterns

| Anti-Pattern | Problem | Fix |
|--------------|---------|-----|
| **Vague reference** | "Fix the thing" | Show the code, state the problem |
| **Missing error** | "It doesn't work" | Include full error message |
| **Assumed knowledge** | "Like we discussed" | Re-state key points |
| **Context dump** | Pasting entire codebase | Load only relevant parts |
| **No constraints** | "Make it better" | State specific requirements |
| **Stale context** | Old file version in chat | Re-read files before referencing |

### Do
- Delete temporary files aggressively
- Summarize, don't duplicate
- Spawn subagents for implementation
- Keep orchestrator context light
- Trust the file system as memory

---

# Part 5 — Quick References

## When context is full

```
Context Full?
├── Mid-task → RESUME.md → fresh session
├── Between tasks → commit, update PROJECT_STATE.md
└── During /execute → wave completes, next wave in fresh agent

Starting Session?
├── RESUME.md exists → read it, delete it, continue
├── No RESUME.md → read PROJECT_STATE.md, latest session log
└── /execute in progress → continue from PLAN.md state

Ending Session?
├── Clean stop → update PROJECT_STATE.md, /log
├── Mid-task → create RESUME.md with exact next step
└── Emergency → at minimum update PROJECT_STATE.md
```

## Verification commands

| Command | Purpose |
|---------|---------|
| `/context` | View currently loaded context |
| `/memory` | View all CLAUDE.md files discovered |
| `/compact` | Compress current context |
| `/clear` | Wipe context, start fresh |
| `claude doctor` | Health check for configuration |

## File lifecycle

| File | Created | Read | Deleted |
|------|---------|------|---------|
| `PROJECT_STATE.md` | Project setup | Every session start | Never (lives forever) |
| `PLAN.md` | Before `/execute` | During waves | Right after completion |
| `RESUME.md` | Mid-task pause | Next session start | After resuming |
| `sessions/YYYY-MM-DD.md` | Each session | Optional | Never (archived) |
| `decisions.md` | When architectural choice made | When reviewing rationale | Never |

## Key principles

1. **Main CLAUDE.md as index** (50-100 lines, always loaded)
2. **Domain-specific docs** split into separate files
3. **Explicit "when to read" conditions** using natural language
4. **"Pitch" pattern** explaining why and when docs matter
5. **Nested CLAUDE.md** for directory-specific context
6. **Progressive loading** only what's needed for current task
7. **Stay under 70%** context usage during sessions
8. **Orchestrator + subagents** for heavy work
9. **Show, don't reference** — paste the code, the error, the constraint

---

## Sources

- [Progressive Context Loading Guide](https://www.remio.ai/post/mastering-claude-skills-progressive-context-loading-for-efficient-ai-workflows)
- [From 150K to 2K Tokens](https://williamzujkowski.github.io/posts/from-150k-to-2k-tokens-how-progressive-context-loading-revolutionizes-llm-development-workflows/)
- [Claude Code Best Practices](https://www.anthropic.com/engineering/claude-code-best-practices)
- [How I Use Every Claude Code Feature](https://blog.sshh.io/p/how-i-use-every-claude-code-feature)
- Context-management patterns adapted from [Get Shit Done](https://github.com/glittercowboy/get-shit-done) by glittercowboy
- "Context Engineering" concept from *Beyond Vibe Coding*

---

*Architecture controls what gets loaded. Runtime controls how it behaves.
Information design controls what's in it. All three matter — but the AI is
only as good as the context you give it.*
