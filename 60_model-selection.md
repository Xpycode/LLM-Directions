<!--
TRIGGERS: model, haiku, sonnet, opus, which model, slow, expensive, cost, fast, sub-agent, subagent
PHASE: any
LOAD: full
-->

# Model Selection Guide

Which Claude model tier to use for which task. Optimize for the right balance of speed, cost, and reasoning depth.

**A note on durability:** model versions and benchmark numbers change often — this guide is written to survive those changes by describing *tiers* (Haiku / Sonnet / Opus) rather than pinning it to a specific model version. As of this writing the current families are the Claude 5 family (Fable 5, Sonnet 5, Haiku 4.5) and Opus 4.8, but always check `claude-code-guide` or the `claude-api` skill for the current model IDs rather than trusting a hardcoded string here.

---

## Quick Selector

```
Simple / fast / read-only   →  Haiku
Daily coding work           →  Sonnet
Hard problems / high-stakes →  Opus
```

---

## Model Comparison

| Dimension | Haiku | Sonnet | Opus |
|-----------|-------|--------|------|
| **Relative cost** | Lowest | Mid | Highest |
| **Relative speed** | Fastest | Fast | Slower — trades speed for depth |
| **Context window** | 200K | 1M | 1M |
| **Reasoning depth** | Shallow — good for pattern-matching, not judgment calls | Strong, everyday-capable | Deepest — best for ambiguity and high-stakes judgment |

**Key insight:** the gap that matters most isn't raw benchmark scores (which shift every release) — it's how well each tier handles *ambiguity* and *large context*. Opus is the tier to reach for when a task requires holding a lot of context in mind and reasoning carefully about trade-offs; Haiku is the tier for narrow, well-specified, high-volume work.

**Thinking depth is adaptive on current models** — Claude decides when and how much to think per request. There's no separate "thinking" tier to pick, and no manual thinking-budget keyword ladder to invoke (see `01_quick-reference.md`).

---

## Task-to-Model Map

### Haiku: fast, simple, high-volume

| Task | Why |
|------|-----|
| File exploration / search / grep | Read-only, speed matters. Built-in Explore agent already uses Haiku. |
| Simple edits (typos, renames) | Trivial changes, no deep reasoning needed. |
| Boilerplate / scaffolding | Templates and repetitive patterns. |
| Code navigation / find usages | Pattern matching, not reasoning. |
| Quick syntax questions | "How do I write X in Swift?" |
| Documentation lookups | Searching and summarizing existing docs. |

**Watch out:** quality can degrade on large or complex code generation. Don't use Haiku for complex multi-file changes — step up to Sonnet or Opus.

### Sonnet: daily workhorse

| Task | Why |
|------|-----|
| New feature implementation | Good code quality at reasonable speed. |
| Standard bug fixing | Strong enough reasoning for most bugs. |
| Test writing | Understands patterns, generates comprehensive cases. |
| Code review (standard) | Good thoroughness-to-speed ratio. |
| Single-file refactoring | Handles restructuring within a module well. |
| Documentation writing | Clear, well-structured output. |
| Moderate multi-file changes | Coordinates across several related files. |
| CI/CD and build scripts | Config files, pipeline definitions. |

**Default choice.** When unsure, start with Sonnet.

### Opus: hard problems, high stakes

| Task | Why |
|------|-----|
| Architecture decisions | Deepest reasoning, weighs trade-offs, asks the right questions. |
| Complex multi-file refactoring | Maintains consistency across large restructuring. Self-corrects. |
| Subtle / hard-to-reproduce bugs | Superior root cause analysis for timing, state, race conditions. |
| Security audits | Catches vulnerabilities shallower tiers miss. |
| Performance optimization | Reasons about algorithmic complexity and systemic bottlenecks. |
| Large codebase comprehension | Best at retaining and reasoning over large amounts of context. |
| Planning and orchestration | Plans the work, delegates to Sonnet/Haiku sub-agents. |
| Critical code review | Self-correction catches issues others overlook. |
| Migration projects | Framework migrations, API upgrades spanning many files. |

**Use when the cost of getting it wrong is high.**

---

## The Orchestration Pattern

**Opus plans, Sonnet builds, Haiku explores.**

```
┌─────────────────────────────────────┐
│  Opus (orchestrator)                │
│  - Architecture decisions           │
│  - Planning                         │
│  - Reviewing critical output        │
│                                     │
│  Delegates to:                      │
│  ├── Haiku sub-agents (explore)     │
│  │   - File search                  │
│  │   - Codebase navigation          │
│  │   - Quick lookups                │
│  └── Sonnet sub-agents (implement)  │
│      - Feature implementation       │
│      - Test writing                 │
│      - Standard refactoring         │
└─────────────────────────────────────┘
```

In Claude Code CLI, the Task tool supports a `model` parameter:
```
model: "haiku"   → fast exploration
model: "sonnet"  → implementation work
model: "opus"    → deep reasoning
```

The built-in Explore agent already uses Haiku automatically.

---

## When to Upgrade Models

Switch from Sonnet to Opus when:
- Bug fix attempt #2 fails (deeper reasoning needed)
- Multi-file refactor touches >5 files
- You need to understand a large unfamiliar codebase
- Security or correctness is critical
- The AI keeps making the same mistake (self-correction needed)

Switch from Opus to Sonnet when:
- Implementation plan is clear, just needs execution
- Writing tests from a well-defined spec
- Straightforward feature work
- Cost is a concern and reasoning depth isn't needed

---

## Cost Optimization

| Strategy | Why |
|----------|-----|
| **Use Haiku for exploration** | Cheapest tier — fine for search/read-only tasks where speed matters more than judgment. |
| **Sonnet for implementation** | Meaningfully cheaper than Opus, and sufficient quality for most day-to-day work. |
| **Opus only for decisions** | Reserve the priciest tier for high-value reasoning — architecture, hard bugs, security. |
| **Prompt caching** | Cache hits cost a fraction of base price — big savings for repeated context. |
| **Keep files small** | Smaller context = fewer tokens = lower cost (see `52_context-management.md`). |

**Rule of thumb:** If the task is "find" or "write boilerplate," use the cheapest tier. If the task is "decide" or "debug something subtle," use the best tier.

---

## Multi-Model Validation

For critical code (security, data integrity, core algorithms):

1. Write/review with Opus
2. Copy to a different model family (Gemini, GPT) for independent review
3. Compare findings — disagreements reveal blind spots

Already in `01_quick-reference.md` as "Multi-Model Validation" technique.

---

## Related

- `52_context-management.md` — Canonical context guide (architecture, runtime, information design)
- `AGENTS.md` — Codex project instructions
- `01_quick-reference.md` — Multi-model validation technique
