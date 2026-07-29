# 173 — Crash-tolerant parallel agent fan-out (file contract + supervisor sweep)

**Tags:** subagents, parallel agents, Agent tool, fan-out, 529 overloaded, API error, retry, supervisor, research pipeline, plan docs, batch, self-contained brief, durable orchestration

**Extracted from:** 2026-07-29 usage-report analysis of the 13-agent roadmap-planning bursts (23 plan docs), where individual agents died to 529 overloads and connection drops and had to be babysat with manual "continue"

## What this is for

Running N parallel subagents (research sweeps, per-feature plan docs, per-repo audits) so that
**one agent dying does not cost the whole wave** — and recovery means relaunching exactly the
failures, not re-running everything or hand-feeding "continue".

## Why the naive burst is fragile

A subagent that hits a terminal API error (529 overload, dropped connection) loses everything it
held in its context — its findings existed nowhere else. With 13 agents in flight the probability
that *at least one* dies is high, and the failure surfaces as a half-missing result set you notice
only while merging. Worse, the natural fix — re-running the whole burst — is 13× the cost of the
one lost agent.

## The pattern: three rules

**1. File contract — findings hit disk before the agent returns.**
Every agent's brief ends with: *"BEFORE returning, write your findings to `<dir>/<unit>.md`"*
(one file per unit, fixed schema: Summary / Findings with evidence / Confidence). The file, not
the agent's return message, is the deliverable. An agent that dies after writing cost nothing;
an agent that dies before writing is *detectable* — the file is missing.

**2. Supervisor sweep — diff expected vs. landed, relaunch only the gaps.**
The expected unit list is written down *first* (`<dir>/UNITS.md`), so "done" is checkable by
machine: `ls <dir>` vs. the list. After each batch, relaunch only units with no file — up to 2
retries, then record the unit as **UNRESOLVED in the merge output** rather than blocking the
pipeline. Never mark a unit done because the agent *returned*; only because the file *exists*.

**3. Self-contained briefs, modest batches.**
Each brief must carry everything the agent needs (it cannot see the conversation): the question,
the output path, the schema, the evidence bar. That is also what makes a retry cheap — relaunching
is resending the same brief. Batch 4–5 at a time rather than all N at once: a systemic failure
(overload window, quota) burns one batch, and the sweep between batches catches it early.

## Shape of a run

```
Phase 1  Plan      — enumerate units → write UNITS.md (the ground truth for "complete")
Phase 2  Fan out   — batches of ≤5 agents; each writes findings/<unit>.md before returning
Phase 3  Supervise — diff UNITS.md vs findings/; relaunch gaps (≤2 retries → UNRESOLVED)
Phase 4  Merge     — one agent reads every findings file → single deduplicated artifact,
                     with an explicit UNRESOLVED section (silent gaps read as "covered")
```

## Gotchas

- **The return message is a trap.** It feels like the result, but it dies with the harness's
  bookkeeping if anything goes wrong in flight. Files on disk survive everything.
- **Don't dedupe against the merged output when looping** — track a separate "seen" list. If a
  finding was judged and rejected, deduping against the *accepted* set makes it reappear every
  round and the loop never converges.
- **Log what was dropped.** If a unit ends UNRESOLVED after retries, it must be named in the
  final artifact. A merge that only lists what landed is indistinguishable from full coverage.
- **The Workflow tool subsumes phases 2–3** when available (it retries, journals each agent's
  return, and supports resume-from-run) — but the file contract still pays for itself: outputs
  are inspectable mid-run and survive even a killed orchestrator.
