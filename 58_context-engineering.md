<!--
TRIGGERS: context engineering, prompt engineering, information environment,
          context stack
PHASE: any
LOAD: redirect
-->

# Context Engineering → moved

This file has been consolidated into the canonical context doc:

**→ [`52_context-management.md`](./52_context-management.md)**

Specifically, see **Part 3 — Information Design: Context Engineering**, which
covers:
- The shift from prompt engineering to context engineering
- The context stack model
- What makes good context (relevant code, constraints, examples, errors)
- The context checklist (per task type: bugs, features, refactors, decisions)
- Loading patterns (progressive, just-in-time, explicit boundaries)
- Structured context formats (code changes, bug reports, feature requests)
- Directions-specific context loading order

`52_context-management.md` is the canonical entry point for all context-related
guidance — architecture, runtime, and information design.

---

*Consolidated 2026-05-14. Merged with `50_progressive-context.md` and
`52_context-management.md` to eliminate ~1042 lines of overlapping coverage.*
