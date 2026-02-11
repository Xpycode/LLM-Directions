# Context Management

How to prevent quality degradation during long sessions.

## The Problem: Context Rot

As Claude's context window fills up, quality degrades:
- Earlier instructions get "forgotten"
- Responses become less precise
- Code quality drops
- Repetition increases

This guide combines Directions' project memory with execution patterns from [Get Shit Done](https://github.com/glittercowboy/get-shit-done).

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
- `PROJECT_STATE.md` - source of truth for position
- `decisions.md` - architectural history
- `sessions/*.md` - daily logs
- `CLAUDE.md` - project instructions

**Temporary (execution artifacts):**
- `PLAN.md` - delete after execution completes
- `RESUME.md` - delete after resuming

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
| **Critical** | 95%+ | /clear immediately, create a handoff document first |

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

**Use CLAUDE.md for persistent instructions:** Instructions in conversation consume context every time. CLAUDE.md instructions consume context once and stay across sessions. Move repeated guidance there (coding style, conventions, terminology). Keep CLAUDE.md under 500 lines.

**Use skills instead of CLAUDE.md for workflow-specific instructions:** Skills load on-demand only when invoked, saving context until needed.

**Subagents for research:** Each subagent runs in its own context window. Verbose output stays there. Only the relevant summary returns to your session. One of the most effective context-saving techniques.

**Disable unused MCP servers:** MCP servers consume tokens just by existing (tool definitions always loaded). Disable via `/mcp` to reclaim context. CLI tools like `gh`, `aws`, `gcloud` don't have this overhead.

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
1. `/interview` - gather requirements
2. `/decide` - record decisions
3. `/log` - track sessions
4. `PROJECT_STATE.md` - maintain position

### For Implementation (GSD-style)
1. Create `PLAN.md` with waves and tasks
2. `/execute` - run wave-based execution
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

## Anti-Patterns

**Don't:**
- Keep PLAN.md or RESUME.md after they're used
- Put implementation details in PROJECT_STATE.md
- Let session logs grow beyond ~200 lines
- Do heavy implementation in the main context
- Accumulate "just in case" context

**The Kitchen Sink** — Start with one task, ask something unrelated, return to first task. Context fills with irrelevant information. Fix: `/clear` between unrelated tasks. A clean session with a good prompt outperforms a cluttered long session every time.

**The Correction Spiral** — Claude does something wrong, you correct, still wrong, correct again. Three rounds in, half your context is failed approaches. Fix: After two failed corrections, `/clear` and write a better initial prompt incorporating what you learned. Starting over with a good prompt is faster than correcting a bad one five times.

**Do:**
- Delete temporary files aggressively
- Summarize, don't duplicate
- Spawn subagents for implementation
- Keep orchestrator context light
- Trust the file system as memory

## Quick Reference

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

## Credits

Context management patterns adapted from [Get Shit Done](https://github.com/glittercowboy/get-shit-done) by glittercowboy. Integrated with Directions' project memory system.
