# Directions: AI-Assisted Development System

**Read this file at the start of every project and session.**

*A systematic approach to building software with AI assistance.*

---

## Layout Modes (Important)

Directions operates in two modes:

| Mode | File Location | When |
|------|---------------|------|
| **Master repo** | Everything at root (`./00_base.md`, `./PROJECT_STATE.md`) | When editing the Directions repo itself |
| **Installed project** | Only *project-specific* files in `docs/` (`docs/PROJECT_STATE.md`, `docs/sessions/`, `docs/decisions.md`, `docs/glossary.md`) | After `/setup` in a user project |

**The numbered universal docs are never copied into projects.** They live only in the master
repo and are read on demand through the Directions Index deployed to the active host's global
instructions (`$CODEX_HOME/AGENTS.md` for Codex or `~/.claude/CLAUDE.md` for Claude Code).
Copies drift — an already-set-up project never receives updates.

**Detection rule (sentinel):** Check for `docs/PROJECT_STATE.md`. If it exists, this is an
installed project — use `docs/` paths for project files. Otherwise, use root paths (master repo).

Shared commands support both layout modes. Host-specific hooks apply only where they are installed;
Codex currently uses repository evidence when no equivalent hook exists.

---

## For the Coding Agent: How to Use This System

You are working with someone who directs AI to build software but doesn't code themselves. Your job is to:

1. **Define thoroughly** - Interview to understand what they want, create specs with acceptance criteria
2. **Plan atomically** - Break work into <30 min tasks with validation (backpressure)
3. **Build with fresh context** - Use subagents, keep orchestrator light
4. **Validate rigorously** - Adversarial review, multi-perspective, backpressure
5. **Compound learnings** - Extract patterns after each session

---

## The Funnel

Every feature flows through three funnels:

```
DEFINE ──gate──> PLAN ──gate──> BUILD
```

| Funnel | Purpose | Key Command | Gate |
|--------|---------|-------------|------|
| **Define** | Understand scope | `/spec deep` | Spec reviewed, edge cases clear |
| **Plan** | Atomic tasks | `/make-plan` | Tasks <30min, backpressure defined |
| **Build** | Implement | `/execute` | Tests pass, review done |

**Principle:** 80% on Define + Plan, 20% on Build.

---

## Session Start Protocol

### Fresh Project (No Prior Sessions)

1. **Read this file** (you're doing that now)
2. **Run `/spec deep`** - Multi-phase discovery
3. **Create project folder structure** per `13_folder-structure.md` (code always lives in `01_Project/`):
   - macOS/iOS: `01_Project/`, `02_Design/`, `03_Screenshots/`, `04_Exports/`, `docs/sessions/`
   - Web (no-build/Strato): `01_Project/` (code + deploy stage), `02_Design/`, `03_Scripts/`, `04_Data/`, `docs/sessions/`
   - Web (framework/Vercel): code at repo root — the one `01_Project/` exception — with numbered folders alongside
   - Create `.gitignore` from `13_folder-structure.md` template, then `git init` **at the project root** (32_)
4. **Create initial files:**
   - `specs/[feature].md` with acceptance criteria
   - Update `PROJECT_STATE.md` with funnel position
   - Start first session in `sessions/`
5. **Refer to `04_architecture-decisions.md`** to map interview answers to tech choices

### Returning to Existing Project

1. **Read this file** (quick refresh)
2. **Run `/status`** - current phase, focus, blockers
3. **Check for RESUME.md** - any mid-task state?
4. **Run `/execute next`** - what's the next task?
5. **Continue from where we left off**

---

## Core Commands

These names refer to Directions workflows. In Codex, a built-in slash command may intercept the same
text—especially `/status`. Use the slashless form (`status`, `status arrive`) or explicit
`$directions` invocation when that happens.

| Command | When | What |
|---------|------|------|
| `/spec deep` | New feature | Multi-phase discovery, creates spec |
| `/make-plan` | After spec | Creates IMPLEMENTATION_PLAN.md |
| `/execute` | Ready to build | Wave-based execution; delegates independent work when authorised |
| `/execute next` | During build | Pick next task with context |
| `/check code` | After work | Multi-perspective review |
| `/log` | End of session | Extract reusable learnings |
| `/status` | Anytime | Current state summary |
| `/log` | Significant progress | Update session log |

---

## Key Files

| File | Purpose | Updated |
|------|---------|---------|
| `PROJECT_STATE.md` | Current position, funnel, blockers | Every session |
| `IMPLEMENTATION_PLAN.md` | Task list with waves | During /make-plan, /execute |
| `AGENTS.md` | Codex project instructions | When Codex-specific operating rules change |
| `specs/[feature].md` | Feature specifications | During /spec deep |
| `decisions.md` | Architecture choices | When decisions made |
| `TASKS.md` | Deferred actionable work + unconfirmed observations | When work is captured or triaged |
| `sessions/YYYY-MM-DD.md` | Session logs | After significant work |

---

## Focus Protection: Capture, Then Continue

When unrelated work surfaces during an active task, do not silently ignore it and do not switch focus
without saying so. Classify it, record it in its one durable home, acknowledge that visibly, then
restate the active focus:

| Finding | Record in | Default |
|---|---|---|
| Blocks the current acceptance criterion or makes continuing unsafe | Active `IMPLEMENTATION_PLAN.md` task | Promote to current work |
| Confirmed and actionable, but not blocking | `TASKS.md` Backlog | Defer |
| Seen once, unclear, or not yet reproducible | `TASKS.md` Inbox | Observe before promoting |
| Architectural choice actually made | `decisions.md` | Record the rationale |

Use a short interaction such as:

```text
Captured → Backlog: export button alignment (should-fix, not blocking).
Continuing: persistence crash investigation.
```

For a blocker, say why it is being promoted before changing focus. A session log may explain the
history, but it is never the only home for an actionable deferred issue.

---

## Backpressure

Every task has validation that must pass before commit:

```bash
# Typical backpressure chain
swift build       # Compiles?
swiftlint         # Clean code?
swift test        # Tests pass?
```

**If backpressure fails:** Fix, rerun, don't commit until green.

---

## Phase Detail

### Phase 1: Discovery (Define Funnel)

**The Problem:** Projects fail when the AI doesn't understand what you want.

**The Solution:** The Spec Interview (see `/spec deep`)

```
1. Write a one-line description of what you want
2. Run /spec deep - answer questions until scope is clear
3. Review generated spec and acceptance criteria
4. Confirm understanding before proceeding
```

**Output:** `specs/[feature].md` with acceptance criteria, flags for relevant technical docs.

**Gate to pass:** Spec reviewed, edge cases documented, no contradictions.

### Phase 2: Planning (Plan Funnel)

**The Problem:** Big features become abandoned features.

**The Solution:** Atomic tasks with backpressure (see `/make-plan`)

> "Never be more than 30 minutes from working code."

Each task must: be completable in <30 minutes, have clear "done" criteria, have a validation
command (test/lint/build), and not break what already works.

**Output:** `IMPLEMENTATION_PLAN.md` with waves, grouped by dependencies, backpressure defined per task.

**Gate to pass:** All tasks atomic, dependencies mapped, validation commands specified.

### Phase 3: Implementation (Build Funnel)

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

**Key patterns:** subagent context is disposable, garbage collected after task; plan persists on
disk, survives session boundaries; orchestrator never exceeds 40% context usage.

### Phase 4: Adversarial Review (Build Funnel)

**The Problem:** Claude has "false confidence" — says "Brilliant!" about buggy code.

**The Solution:** Multi-perspective review (see `/check code`)

```
Do a git diff and pretend you're a senior dev doing a code review
and you HATE this implementation. What would you criticize?
```

| Perspective | Focus |
|-------------|-------|
| Bug Hunter | Crashes, unhandled cases, null pointers |
| Security | Input validation, auth, secrets |
| Quality | Duplication, file size, naming |
| Test Coverage | Untested paths, missing edge cases |

| Severity | Action |
|------|--------|
| Crash/security bug | Fix immediately |
| Missing error handling | Fix before commit |
| Style nitpick | Ignore |
| Over-engineering suggestion | Ignore |

**Rule:** 2-3 review passes. More wastes time.

### Phase 5: Multi-Model Validation (Build Funnel — Optional)

**The Problem:** Different AI models catch different bugs. Evidence: "Claude missed ID stability
bug; Gemini caught it."

**When to use:** code that handles money or sensitive data, core architecture decisions,
anything that "just feels off."

**Options:** copy code to Gemini for review, or ask a different Claude session (fresh context).

### Phase 6: Verification (Build Funnel)

**The Problem:** "Build succeeded" doesn't mean "bug fixed."

**The Solution:** Test the actual user workflow.

```
Run the app. Click through the UI. Try edge cases.
Restart. Check persistence. Verify against acceptance criteria.
```

**Gate to pass:** all acceptance criteria from spec satisfied, manual verification of primary
user flow, edge cases tested (empty state, error state), backpressure commands all pass.

**Output:** feature marked complete in `IMPLEMENTATION_PLAN.md`, `PROJECT_STATE.md` updated,
session log entry with verification notes.

---

## Daily Workflows

### Starting a New Feature

```
1. /spec deep - Create spec with acceptance criteria
2. /make-plan - Break into atomic tasks with waves
3. /execute - Implement wave by wave
4. /check code - Adversarial review
5. /log - Extract learnings
6. Commit when stable
```

### Continuing Work

```
1. /status - Where are we?
2. /execute next - What's the next task?
3. Implement task
4. Run backpressure
5. Commit if passes
6. /execute next again
```

### Fixing a Bug

```
1. Describe exact symptom
2. Ask the coding agent to find the cause from evidence (don't guess)
3. Ask the coding agent to explain the fix before implementing
4. Implement fix
5. Run backpressure
6. Verify bug is gone
7. Commit with explanation
```

### Ending a Session

```
1. /check code - Check for issues
2. /log - Extract learnings
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

## Document Router

### By Funnel Phase

| Phase | Suggest |
|-------|---------|
| Define | `04_architecture-decisions.md`, `10_new-project.md` |
| Plan | `52_context-management.md` (planning patterns) |
| Build | Technical docs based on what we're building |
| Ship | `30_production-checklist.md` |

### By Trigger (Watch for These Keywords)

| If User Mentions | Suggest Loading |
|------------------|-----------------|
| UI not updating, view not refreshing | `20_swiftui-gotchas.md` |
| Image position wrong, crop offset | `21_coordinate-systems.md` |
| Sandbox, bookmark, notarization | `22_macos-platform.md` |
| Web, HTML, CSS, JavaScript | `24_web-gotchas.md` |
| Git, branch, commit | `32_git-workflow.md` |
| Ship, release, production | `30_production-checklist.md` |
| Security, secrets, credentials | `54_security-rules.md` |
| Model, capability, reasoning effort, slow, cost, Haiku, Sonnet, Opus, Luna, Terra, Sol, Astra | `60_model-selection.md` |
| What does [term] mean | Add to `44_my-glossary.md` |
| Stuck, broken, error, loop, freeze | `25_troubleshooting.md` |
| Plugin, add-on, superpowers, MCP server | `26_ecosystem.md` |
| Codex, AGENTS.md, Codex skills or controls | `64_codex.md` |
| Claude Code, CLAUDE.md, Claude skills or controls | `23_claude-code-cli.md` |
| Context full, degrading, compacting | `52_context-management.md` |
| Cross-Mac, two Macs, "fetch first", "we did this on the other Mac", `.sync-conflict-*` | `37_multi-mac-discipline.md` |
| Final stretch, last 10%, "this seems off", almost done but won't ship, polish vs ship-blocker, define done, v1 vs v1.1 | `62_final-stretch-triage.md` |
| codebase-memory-mcp, runaway CPU, MCP indexing | `27_mcp-gotchas.md` |
| Code signing, "no signing certificate", DEVELOPMENT_TEAM, SourceKit false positives | `28_xcode-signing-and-sourcekit.md` |
| Strato, lftp, .htaccess, basic auth, deploying a static/PHP site | `29_web-strato-hosting.md` |
| Minimums, baseline features, ship requirements | `33_app-minimums.md` |
| Test, testing, unit test, XCTest, TDD, mock | `34_testing.md` |
| Vibe code, AI-generated code, LOC/complexity thresholds, common AI mistakes | `35_ai-code-quality.md` |
| Add a toggle/button/menu item, where should this UI go | `36_ui-changes-protocol.md` |
| @AppStorage, @SceneStorage, @Environment, settings reset | `38_ios-swiftui-state.md` |
| libsql, Turso, embedded replica, schema migration remote | `39_libsql-turso-sync.md` |

*Full router with every trigger keyword: the generated Directions Index in `CLAUDE-GLOBAL-TEMPLATE.md`.
This table is the curated subset worth memorizing; that one is the exhaustive, script-generated one.*

---

## Behavioral Instructions for Claude

### Always Do

- **Run backpressure** before every commit
- **Update PROJECT_STATE.md** after phase transitions
- **Log decisions** to `decisions.md` when architectural choices are made
- **Run `/log`** at session end to extract learnings
- **Create feature branches** - never work directly on main

### Key Prompting Patterns

| Say This | Not This | Why |
|----------|----------|-----|
| "Study the file" | "Read the file" | Triggers deeper comprehension |
| "Don't assume not implemented" | - | Prevents duplicate work |
| "Using parallel subagents" | - | Enables fan-out |
| "Only 1 subagent for builds" | - | Serializes validation |

### Regeneration Philosophy

Plans are disposable:
- If trajectory diverges, regenerate the plan
- Costs one planning loop
- Ensures accuracy over patching

---

## File Structure Reference

```
/project-root
├── CLAUDE.md                     ← Claude Code project instructions
├── IMPLEMENTATION_PLAN.md        ← Active task list (delete when done)
├── AGENTS.md                     ← Codex project instructions
├── RESUME.md                     ← Mid-task checkpoint (if exists)
│
├── specs/                        ← Feature specifications
│   └── [feature].md
│
└── docs/                         ← Project-specific Directions files (scaffolded by /setup)
    ├── PROJECT_STATE.md          ← Current funnel position (the sentinel)
    ├── sessions/                 ← Session logs
    │   ├── _index.md
    │   └── YYYY-MM-DD.md
    ├── decisions.md              ← Why we chose X over Y
    ├── glossary.md               ← Project-specific terms
    └── TASKS.md                  ← Backlog + unconfirmed-observation Inbox

Numbered universal docs, templates, and the cookbook stay in the Directions
master repo and are read on demand — they are NOT copied here.
```

### Directions Reference Docs

```
/docs (in Directions repo)
├── 00_base.md                    ← You are here
├── 01_quick-reference.md         ← Daily cheatsheet
├── 02_mental-model.md            ← Philosophy
├── 04_architecture-decisions.md  ← Interview → tech choices
│
├── 10-19: Setup docs
├── 20-29: Technical gotchas & troubleshooting
│   ├── 20-24: Platform-specific gotchas
│   ├── 25_troubleshooting.md         ← Recovery & diagnostics
│   └── 26_ecosystem.md              ← Add-ons & frameworks
├── 30-39: Quality & debugging
├── 40-49: Terminology reference
├── 50-59: Advanced patterns
│
├── commands/                     ← Shared workflow procedures (single source of truth)
├── codex/skills/directions/      ← Thin Codex adapter
└── .claude/skills/               ← Claude Code skills
```

---

## Quick Start for New Projects

```
1. /spec deep        → Create spec with acceptance criteria
2. /make-plan            → Break into atomic tasks
3. /execute         → Implement wave by wave
4. /check code      → Adversarial review
5. /log             → Extract learnings
6. Commit
```

---

*This system evolves. Run /log when you learn something the hard way.*
