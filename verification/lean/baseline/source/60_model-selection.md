<!--
TRIGGERS: model, model selection, capability, reasoning effort, cheap, fast, slow, expensive,
          context problem, sub-agent, subagent, haiku, sonnet, opus, luna, terra, sol, astra
PHASE: any
LOAD: full
-->

# Model Selection Guide

Choose capability and reasoning deliberately. Provider model names, aliases, prices, context windows,
and availability change too quickly to serve as the framework's permanent vocabulary.

```text
Explore cheap.
Build balanced.
Reason deep.
Escalate deliberately.
```

Use the fastest and least resource-intensive available setting that can reliably finish the task.
Provider-specific mappings belong in `23_claude-code-cli.md` and `64_codex.md`, not here.

---

## Two Separate Controls

Treat model choice and reasoning effort as independent controls:

```text
effective capability = model capability × reasoning effort × relevant context
```

- **Model capability** controls the kind and difficulty of work the model can handle reliably.
- **Reasoning effort** controls how much time and token budget the selected model spends planning,
  analysing, and checking.
- **Context quality** controls whether the model has the right evidence and constraints in the first
  place.
- **Parallelism** controls whether independent work is delegated. It is an orchestration choice, not
  a synonym for maximum reasoning.

Exact effort names and supported ranges vary by provider, model, client, and release. Choose by role
rather than assuming every provider exposes the same ladder.

---

## Capability Tiers

| Tier | Role | Swift/macOS/iOS examples |
|---|---|---|
| **A — Mechanical** | Clear, repeatable, low-risk work | Find every use of a protocol; rename a symbol; extract a list from logs; apply a known formatting change |
| **B — Implementation** | Normal feature work and routine debugging | Add `Codable`; implement a SwiftUI settings pane; write tests; refactor a few related views |
| **C — Deep reasoning** | Ambiguous, cross-cutting, or correctness-sensitive work | Diagnose an `@Observable` state bug; resolve actor isolation; review a multi-file migration; reason about data integrity |
| **D — Frontier / end-to-end** | Large unfamiliar systems and sustained multi-step judgment | Plan a macOS architecture change; recover from repeated failed approaches; coordinate a high-risk migration or release audit |

These are workflow roles, not claims that models from different providers are technically equivalent.

---

## Reasoning-Effort Ladder

Use effort as a second dial after choosing an adequate capability tier.

| Task | Starting role |
|---|---|
| Search, inspect, classify | Mechanical capability + low effort |
| Tiny, fully specified edit | Mechanical capability + low effort |
| Normal feature or test work | Implementation capability + medium effort |
| Moderate refactor or ordinary debugging | Implementation capability + medium/high effort |
| Subtle state or concurrency problem | Deep capability + high/extra-high effort |
| Architecture or large unfamiliar system | Deep/frontier capability + high/extra-high effort |
| Repeated failed attempts or exceptional risk | Frontier capability + the highest justified effort |

Do not use maximum effort habitually. It is slower, consumes more usage, and cannot repair missing or
misleading context.

---

## Escalation Order

Before upgrading the model, ask whether the task is genuinely difficult or merely poorly framed.

```text
Clarify the task and success criteria
→ provide missing evidence and constraints
→ remove polluted context or compact/start fresh
→ increase reasoning effort
→ upgrade model capability
```

See `52_context-management.md` before treating repeated mistakes as proof that the model is too weak.

### Upgrade when

- architectural judgment or subtle trade-offs dominate the work;
- concurrency, state, security, destructive operations, or data integrity raise the cost of error;
- many interacting files or systems must remain consistent;
- the codebase is unfamiliar and the task is ambiguous;
- a well-contextualised approach has failed repeatedly.

### Downgrade when

- the plan and acceptance criteria are already clear;
- the work is repetitive or mechanically verifiable;
- a focused test or deterministic check supplies strong backpressure;
- exploration can be isolated from the judgment-heavy part of the task.

Avoid rigid triggers such as “more than five files always requires the strongest model.” File count is
only a weak proxy for coupling and risk.

## User-Facing Model-Fit Notice

Model advice must be visible without becoming a recurring nag. Show one concise notice when:

- a workflow transition changes the recommended capability or reasoning effort;
- new evidence materially raises the task's ambiguity, coupling, or cost of error;
- a well-contextualised approach has failed repeatedly; or
- a pre-clear or Mac-handoff log recommends the setting for the next session.

Do not repeat the notice while the recommendation is unchanged. Do not interrupt routine work merely
to advertise a cheaper model. For a consequential upgrade, explain the reason before continuing.

Use this shape:

```text
Model fit: this has become subtle state/concurrency work.
Recommended: deep capability + high reasoning.
Current setting: not reliably visible. Use the host's model control if you want to switch; otherwise I'll continue.
```

If the host reliably exposes the active model and effort, compare them directly. Otherwise say that
the current setting is not reliably visible—never guess. Use provider-neutral capability roles in
shared workflow files; a host-specific guide may add the exact current control or model name.

At a session boundary, base the recommendation on the recorded **next action**, not merely the phase
that just ended. Put it in the Resume/next-session block so a fresh session does not have to infer it.

---

## Delegation and Parallelism

Use subagents when the user or active instructions permit delegation and the work separates into
meaningfully independent tasks. Give each task its own evidence, boundaries, and success criteria.

Do not delegate merely to imitate a provider-specific model slogan. A capable main agent can implement
directly; delegation is valuable when it reduces context pollution, shortens independent research, or
adds a genuinely independent review perspective.

---

## Independent Validation

For concurrency, data integrity, destructive file operations, migrations, security-sensitive code, or
high-stakes architecture:

1. Complete the primary implementation or review.
2. Ask an independent reviewer—preferably another model family when available—to look for faults.
3. Compare disagreements and investigate the underlying evidence.
4. Verify with tests, builds, logs, or real user flows.

Cross-model agreement is not proof of correctness. Its value is independent fault-finding.

---

## Provider Mappings

- `64_codex.md` — current Codex models, reasoning controls, usage, permissions, and daily CLI workflow
- `23_claude-code-cli.md` — current Claude Code mapping and CLI controls

Date and source provider mappings when updating them. Never infer technical equivalence from a shared
workflow role.

---

## Related

- `52_context-management.md` — diagnose missing, oversized, or polluted context before escalating
- `01_quick-reference.md` — daily workflow and provider-specific controls
- `53_llm-failure-modes.md` — distinguish capability failures from process and verification failures
