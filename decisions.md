# Decisions Log

This file tracks the WHY behind technical and design decisions.

---

## Template

### [Date] - [Decision Title]
**Context:** [What situation prompted this decision?]
**Options Considered:**
1. [Option A] - [pros/cons]
2. [Option B] - [pros/cons]

**Decision:** [What we chose]
**Rationale:** [Why we chose it]
**Consequences:** [What this means going forward]

---

## Decisions

### 2026-01-25 - Integrate everything-claude-code Features

**Context:** Discovered affaan-m/everything-claude-code repository - a battle-tested Claude Code configuration with agents, commands, and workflows. Evaluated for complementary features to add to Directions.

**Options Considered:**
1. **Full adoption** - Replace Directions with everything-claude-code
   - Pros: More comprehensive command set, hooks system
   - Cons: Different philosophy (TypeScript/web-focused), loses Directions' strengths

2. **Selective integration** - Cherry-pick complementary features
   - Pros: Best of both worlds, no breaking changes
   - Cons: Maintenance of adapted code

3. **No integration** - Keep systems separate
   - Pros: Simpler, no merge work
   - Cons: Miss valuable workflow improvements

**Decision:** Selective integration (Option 2)

**Rationale:**
- Directions is stronger at: discovery interviews, architecture mapping, Swift/macOS gotchas, progressive context
- everything-claude-code is stronger at: code review automation, TDD workflow, build error handling
- The features complement rather than compete

**What was integrated:**
- `/code-review` command - Automated quality checklist before commits
- `/tdd` command - Test-driven development workflow
- `/build-fix` command - Xcode/Swift error resolution
- `54_security-rules.md` - Security checklist reference

**What was NOT integrated:**
- Hooks system (Directions uses session logs instead)
- Memory persistence (Directions uses PROJECT_STATE.md)
- MCP configs (too specific to their web stack)
- Package manager setup (Directions is Swift-focused)

**Consequences:**
- Three new commands available for quality workflows
- Attribution to source repo in adapted files
- May adopt more features in future if valuable

---
*Add decisions as they are made. Future-you will thank present-you.*
