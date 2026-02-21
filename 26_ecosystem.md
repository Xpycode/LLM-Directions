<!--
TRIGGERS: plugin, add-on, superpowers, beads, beans, ralph, gsd, mcp server, marketplace, ecosystem, framework
PHASE: any
LOAD: when exploring tools
-->

# Claude Code Ecosystem & Add-Ons

*Tools, frameworks, and plugins that extend Claude Code — curated for non-coders.*

---

## Extension Types

| Type | What It Is | Example |
|------|-----------|---------|
| **Skills** | Reusable instruction files (SKILL.md) | Commit workflows, code review |
| **Plugins** | Bundles of capabilities | Complete dev workflows |
| **Subagents** | Specialized AI agents | Security auditing, documentation |
| **MCP Servers** | External connections | APIs, databases, cloud services |
| **Hooks** | Event-triggered automation | Quality enforcement, security scanning |

---

## Development Frameworks

### Superpowers (Recommended Starting Point)

**By:** Jesse Vincent (`github.com/obra/superpowers`)
**Purpose:** Enforces brainstorm → plan → build workflow. Prevents Claude from skipping to code.

| Command | Purpose |
|---------|---------|
| `/superpowers:brainstorm` | Interactive design refinement via Socratic questioning |
| `/superpowers:write-plan` | Detailed implementation plan (2-5 min tasks with file paths) |
| `/superpowers:execute-plan` | Execute plan in batches with subagents |

**Key features:**
- Socratic questioning (asks about your idea, pokes at assumptions)
- Bite-sized tasks (2-5 min each) with verification steps
- Fresh subagents per task with embedded code reviews
- Enforces TDD (red-green-refactor)
- Token-light: core pulls in <2k tokens

**Install:**
```
/plugin marketplace add obra/superpowers-marketplace
/plugin install superpowers@superpowers-marketplace
```

**Best for:** Anything that takes more than an hour. Overkill for quick fixes.

---

### Beads

**By:** Steve Yegge
**Purpose:** Persistent, git-backed task memory that survives context compaction.

**Key insight:** Store task state in files, not conversation memory. When context compacts, state survives because it lives in `.beads/` files.

| Command | Purpose |
|---------|---------|
| `bd ready` | Display tasks without blockers |
| `bd create "Title" -p 0` | Add a priority task |
| `bd update <id> --claim` | Claim a task |
| `bd close <id>` | Mark complete |
| `bd comments add <id> "notes"` | Add context |
| `bd dep add <child> <parent>` | Set dependencies |

**Install:**
```bash
npm install -g @beads/bd
```

**Best for:** Multi-day work with task dependencies. Complements Superpowers.

---

### GSD (Get Shit Done)

**By:** TACHES/kogumauk
**Purpose:** Structure without ceremony for solo developers and small teams.

**Persistent state files:**
| File | Purpose |
|------|---------|
| `PROJECT.md` | Project vision and constraints |
| `ROADMAP.md` | Phases and milestones |
| `STATE.md` | Current progress |
| `PLAN.md` | Structured tasks |
| `SUMMARY.md` | Committed outcomes |
| `ISSUES.md` | Deferred work |

| Command | Purpose |
|---------|---------|
| `/gsd:new-project` | Capture requirements |
| `/gsd:create-roadmap` | Generate phases |
| `/gsd:plan-phase [N]` | Create atomic task plans |
| `/gsd:execute-plan` | Run subagent implementation |
| `/gsd:map-codebase` | Generate 7 analysis documents |

**Install:**
```bash
npx get-shit-done-cc
```

**Best for:** Solo developers. `/gsd:map-codebase` alone is worth installing.

---

### Ralph Loops

**By:** Geoffrey Huntley
**Purpose:** Autonomous AI agent loop — give Claude a PRD, it works through every requirement.

**Three phases:**
1. Generate detailed PRD using `/prd` skill
2. Convert to structured JSON using `/ralph` skill
3. Run the loop with `./scripts/ralph/ralph.sh`

**Loop behavior:** Select highest-priority incomplete story → implement → run quality checks → commit if pass → update status → move on.

**Quality gates (non-negotiable):** Type checking, automated testing, CI validation. If any gate fails, story stays incomplete.

**Best for:** Batch work, large projects. Critical dependency: only as good as your PRD.

---

### BEANS (Because Every Agent Needs Support)

**Purpose:** All-in-one development toolkit (methodology + memory + code intelligence).

**Components:** Beads (issue tracker) + Smart-Ralph (spec-driven dev) + Valyu (knowledge retrieval) + Code Intelligence (AST analysis).

**13 subagents** covering: research, requirements, design, task execution, code review, testing, documentation, optimization.

| Command | Purpose |
|---------|---------|
| `/beans` | List ready issues |
| `/beans "Add dark mode"` | Full autonomous flow |
| `/beans:research` | Research phase only |

**Install:**
```bash
npm install -g @morebeans/cli
beans init
```

**Best for:** Comprehensive autonomous development. High barrier to entry — evaluate whether you'll use most of its 13 agents.

---

## Comparison Matrix

| Framework | Focus | Complexity | Autonomy | Best For |
|-----------|-------|-----------|----------|----------|
| **Superpowers** | TDD + Systematic Dev | Medium | High | Teams wanting enforced quality |
| **Beads** | Persistent Task Memory | Low | N/A (supports others) | Multi-session complex projects |
| **GSD** | Spec-Driven Solo Dev | Medium | High | Solo developers, small teams |
| **Ralph Loops** | PRD-Driven Autonomous | Low-Medium | Very High | Batch work, large projects |
| **BEANS** | All-in-One Toolkit | High | Very High | Comprehensive autonomous dev |

### Picking Recommendation

1. **Start with Superpowers** — most accessible, teaches transferable habits
2. **Add Beads** if you need persistent task memory
3. **GSD** for solo developers wanting opinionated workflows
4. **Ralph** for set-and-forget batch work
5. **BEANS** for the full suite (be honest about whether you'll use it all)

---

## Installed MCP Servers

These are the MCP servers currently configured and active on this machine.

### Zen (Multi-Model Orchestration)
Orchestrates multiple AI models (Gemini, GPT, O3, etc.) in a single conversation with context continuity. Send work to other models for second opinions, code reviews, or consensus.

**Key tools:** `chat`, `codereview`, `debug`, `precommit`, `planner`, `consensus`, `challenge`

**Config:** `~/.mcp.json` → Python venv at `~/zen-mcp-server/`

**Best for:** Multi-model code reviews, architecture debates, pre-commit validation.

### Apple Doc MCP (Apple Developer Documentation)
Instant access to current Apple Developer Documentation (SwiftUI, UIKit, Foundation) with wildcard symbol search. Avoids stale training-data answers for Apple APIs.

**Key tools:** `search_symbols`, `get_documentation`, `list_technologies`

**Config:** `~/.mcp.json` → `~/apple-doc-mcp/`

**Best for:** iOS/macOS development — looking up current API signatures, finding framework symbols.

### Sosumi (Apple Documentation Search)
Remote Apple documentation search and fetch. Complementary to Apple Doc MCP with broader coverage.

**Key tools:** `searchAppleDocumentation`, `fetchAppleDocumentation`, `fetchExternalDocumentation`

**Config:** `~/.mcp.json` → remote at `https://sosumi.ai/mcp`

**Best for:** Quick Apple doc lookups without local installation overhead.

### XcodeBuildMCP (Xcode Build Automation)
Automates Xcode builds, simulator management, Swift package development, LLDB debugging, screenshots, and UI automation.

**Key tools:** `build_macos`, `build_run_macos`, `screenshot`, `scaffold_macos_project`

**Config:** `~/.mcp.json` → `npx xcodebuildmcp@latest`

**Best for:** Build-test-screenshot cycles without leaving Claude Code.

### Serena (Semantic Code Navigation & Editing)
IDE-like symbol-level code navigation and editing across 30+ languages. Reads specific functions/classes instead of entire files — saves tokens on large codebases.

**Key tools:** `find_symbol`, `get_symbols_overview`, `replace_symbol_body`, `find_referencing_symbols`

**Config:** `~/.mcp.json` → `uvx` from `github.com/oraios/serena`

**Best for:** Large codebase navigation, precise symbol-level edits, finding all references.

### Vestige (Long-Term Memory)
Persistent cognitive memory system using FSRS-6 spaced repetition. Remembers patterns, decisions, and context across sessions with human-like decay.

**Key tools:** `memory`, `recall`, `remember_pattern`, `remember_decision`, `set_intention`

**Config:** `.claude.json` (project-level) → `~/.local/bin/vestige-mcp`

**Best for:** Cross-session learning, remembering architectural decisions, tracking intentions.

### Context7 (Live Documentation)
Injects up-to-date, version-specific documentation into prompts. Include "use context7" in any prompt to get current docs instead of training-data answers.

**Config:** `.claude.json` (user-level) → `npx -y @upstash/context7-mcp`

**Note:** No API key configured — runs at 60 req/hour free tier. Get a key at `context7.com/dashboard` for higher limits.

**Best for:** Getting current library docs (React, Next.js, etc.) instead of outdated training data.

### Playwright (Browser Automation)
Microsoft's official browser automation MCP. Uses accessibility tree for reliable navigation. Enables end-to-end testing, web scraping, form automation.

**Config:** `.claude.json` (user-level) → `npx -y @playwright/mcp@latest`

**Tip:** Have Claude show a login page, log in yourself, then tell Claude what to do next.

**Best for:** E2E testing, web scraping, form filling, visual verification.

### Not Installed (Documented for Reference)

**Firecrawl** — Web scraping producing clean markdown optimized for LLMs. Requires API key (free tier: 500 credits). Install when needed:
```bash
claude mcp add --scope user firecrawl -e FIRECRAWL_API_KEY=your-key -- npx -y firecrawl-mcp
```

---

## CLI Tools (Not MCP)

### XcodePreviews (PreviewBuild)
Programmatic SwiftUI preview capture — builds and screenshots UI components without running the full app.

**By:** Iron-Ham (`github.com/Iron-Ham/XcodePreviews`)

| Approach | Build Time | Use Case |
|----------|-----------|----------|
| Dynamic injection | ~3-4 sec | Xcode projects with `#Preview` |
| Minimal host | ~5 sec | Standalone Swift files |
| SPM temp project | ~20 sec | Swift packages |

**Installed at:** `~/XcodePreviews`
**Claude command:** `/preview path/to/MyView.swift`

```bash
~/XcodePreviews/scripts/preview MyView.swift --output /tmp/preview.png
```

**Best for:** Visual verification of SwiftUI views during AI-assisted development.

---

## Evaluating Add-Ons

### Trust Hierarchy

| Level | Source | Recommended Use |
|-------|--------|----------------|
| Highest | Anthropic-developed | Production use |
| High | Anthropic Verified badge | Production use |
| Medium | Official marketplace (no badge) | Review before use |
| Lower | Community marketplaces | Careful evaluation |
| Lowest | Direct GitHub installs | Expert evaluation |

Start with the official marketplace. Stay there until you have a specific reason to look elsewhere.

### Health Check Before Installing

| Indicator | Good Sign | Warning Sign |
|-----------|-----------|-------------|
| Last commit | Within 3 months | Over 6 months ago |
| Issue response | Days | Weeks or months |
| Security issues | None or addressed | Unaddressed |
| Documentation | Clear README | Missing or vague |
| Stars | 50+ for smaller projects | Very few |

### Pre-Installation Checklist

- [ ] From official Anthropic marketplace?
- [ ] Has "Anthropic Verified" badge?
- [ ] Can find it on GitHub and see the code?
- [ ] Updated in last 6 months?
- [ ] Clear documentation?
- [ ] Functionality matches what I need?
- [ ] No red flags in README or issues?

### Anti-Patterns

- **Plugin rot** — maintainer moves on, plugin breaks after Claude Code update
- **Configuration conflicts** — two plugins that individually work but together produce bizarre behavior
- **Over-extending** — installing too many add-ons; aim for smallest number that solve actual problems
- **Scope confusion** — project scope (`.claude/plugins/`) vs local scope (`~/.claude/plugins/`) mixups

---

## Discovery Sources

### Official
- `/plugin` in Claude Code → navigate to "Discover"
- `github.com/anthropics/skills` (official skills)

### Community Lists
- `hesreallyhim/awesome-claude-code` (21,600+ stars)
- `travisvn/awesome-claude-skills` (foundational curated list)
- `VoltAgent/awesome-agent-skills` (200+ skills from official dev teams)

### MCP Directories
- `github.com/modelcontextprotocol/servers` (official)
- `mcp-awesome.com` (1,200+ servers)
- `mcpindex.net`

### Skill Marketplaces
- **SkillsMP** (`skillsmp.com`) — large directory with smart search
- **SkillHub** (`skillhub.club`) — AI-evaluated skills with quality scoring

---

## What Directions Already Provides

Directions solves the same core problems as these frameworks:
- **Phase-based workflow** → Ralph Funnel (Define → Plan → Build)
- **Quality gates** → Backpressure system
- **Persistent state** → PROJECT_STATE.md, RESUME.md
- **Wave execution** → /execute with subagents
- **Adversarial review** → Multi-perspective code review

These ecosystem tools can complement Directions, not replace it. Pick tools that fill specific gaps in your workflow.

---

*Based on "Claude Code for the Rest of Us" by Harry Munro (2026). Frameworks evolve rapidly — verify current versions before installing.*
