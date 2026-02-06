<!--
TRIGGERS: model, haiku, sonnet, opus, which model, slow, expensive, cost, fast, sub-agent, subagent
PHASE: any
LOAD: full
-->

# Model Selection Guide

Which Claude model to use for which task. Optimize for the right balance of speed, cost, and reasoning depth.

---

## Quick Selector

```
Simple / fast / read-only  →  Haiku
Daily coding work          →  Sonnet
Hard problems / high-stakes →  Opus
```

---

## Model Comparison

| Dimension | Haiku 4.5 | Sonnet 4.5 | Opus 4.6 |
|-----------|-----------|------------|----------|
| **Cost (input/output per MTok)** | $1 / $5 | $3 / $15 | $5 / $25 |
| **Relative cost** | 1x | 3x | 5x |
| **Speed** | Fastest (~100 tok/s) | Fast | Moderate |
| **SWE-bench** | 73.3% | 77.2% | 80.8% |
| **Context window** | 200K | 200K (1M beta) | 200K (1M beta) |
| **Max output** | 64K | 64K | 128K |
| **Long-context recall (MRCR v2)** | — | 18.5% | 76% |
| **Extended thinking** | Yes | Yes | Yes |
| **Adaptive thinking** | No | No | Yes (exclusive) |

**Key insight:** Opus is dramatically better at finding specific details in large contexts (76% vs 18.5% MRCR). For large codebase comprehension, the model upgrade pays for itself.

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

**Watch out:** Quality degrades past ~150 lines of generated code. Don't use for complex multi-file changes.

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
| Architecture decisions | Deepest reasoning, weighs trade-offs, asks right questions. |
| Complex multi-file refactoring | Maintains consistency across large restructuring. Self-corrects. |
| Subtle / hard-to-reproduce bugs | Superior root cause analysis for timing, state, race conditions. |
| Security audits | Catches vulnerabilities shallower models miss. |
| Performance optimization | Reasons about algorithmic complexity and systemic bottlenecks. |
| Large codebase comprehension | 76% MRCR recall vs Sonnet's 18.5%. Dramatically better. |
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

| Strategy | Savings |
|----------|---------|
| **Use Haiku for exploration** | 5x cheaper than Opus for search tasks |
| **Sonnet for implementation** | 40% cheaper than Opus, 77% SWE-bench is sufficient |
| **Opus only for decisions** | Reserve the expensive model for high-value reasoning |
| **Prompt caching** | Cache hits cost 0.1x base price — big savings for repeated context |
| **Keep files small** | Smaller context = fewer tokens = lower cost (see `52_context-management.md`) |

**Rule of thumb:** If the task is "find" or "write boilerplate," use the cheapest model. If the task is "decide" or "debug something subtle," use the best model.

---

## Multi-Model Validation

For critical code (security, data integrity, core algorithms):

1. Write/review with Opus
2. Copy to a different model family (Gemini, GPT) for independent review
3. Compare findings — disagreements reveal blind spots

Already in `01_quick-reference.md` as "Multi-Model Validation" technique.

---

## Related

- `52_context-management.md` — Context window management (model choice affects context efficiency)
- `50_progressive-context.md` — Loading context efficiently
- `AGENTS.md` — Sub-agent patterns
- `01_quick-reference.md` — Multi-model validation technique
