<!--
TRIGGERS: token limit, context too big, CLAUDE.md bloated, large project,
          router pattern, progressive loading
PHASE: any
LOAD: redirect
-->

# Progressive Context Loading → moved

This file has been consolidated into the canonical context doc:

**→ [`52_context-management.md`](./52_context-management.md)**

Specifically, see **Part 1 — Architecture: Progressive Context Loading**, which
covers:
- The router pattern (lean CLAUDE.md as index)
- Nested CLAUDE.md for directory-specific context
- The "Pitch" pattern (when/why explanations)
- "DO NOT load" directives
- Custom loading commands
- Token reduction results (95-98% reduction)
- Recommendations by project size
- Sub-agent orchestration
- Migration strategy and router template

`52_context-management.md` is the canonical entry point for all context-related
guidance — architecture, runtime, and information design.

---

*Consolidated 2026-05-14. Merged with `52_context-management.md` and
`58_context-engineering.md` to eliminate ~1042 lines of overlapping coverage.*
