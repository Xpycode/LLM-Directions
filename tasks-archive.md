# Tasks Archive

> **Completed tasks archive.** Used for progress calculation.

## Stats
- **Total archived:** 9
- **Last updated:** 2026-10-28

## Completed

<!-- Newest at top. Added by /log when tasks complete. -->
<!-- Format: - [x] Task description (YYYY-MM-DD) -->

- [x] Reconcile confirmed guidance contradictions from the October 27 Reddit review (2026-10-28).
  Removed retired context-zone/drift thresholds in `53_llm-failure-modes.md`, fixed compaction
  percentage in `CLAUDE-GLOBAL-TEMPLATE.md`, blanket baseline/new-test wording in
  `35_ai-code-quality.md`, and consumer-local cookbook routing in `commands/cookbook.md`.
  Existing `52_context-management.md`, `34_testing.md` and master ownership are authoritative.
  Also clarified legitimate user instructions versus injection in retrieved content.
  [Source review and checks](sessions/2026-10-28.md#guidance-contradiction-cleanup).
  Source-only completion; no deployment/runtime acceptance, E1 or recovery gate closure.

- [x] Mac Control 1.1: Inventory actual clients and backends (2026-09-05)
  - [Environment evidence](verification/mac-control/environment.md): local versions, identity hints,
    permissions and user-reported cross-project UI tests. Live compatibility remains unverified.
- [x] Mac Control 1.2: Freeze the protocol and lifecycle fixtures (2026-09-05)
  - [Static verification](verification/mac-control/protocol.md): revision 1, six JSON files,
    86 declarative scenarios and independent review fixes. No runtime stop test yet.

- [x] Task 1.1: Define the Claude/Codex/shared instruction ownership boundary (2026-09-01)
- [x] Task 1.2: Inventory instruction-file references and scaffolding surfaces (2026-09-01)
- [x] Task 2.1: Replace the root placeholder AGENTS.md with Directions-specific Codex guidance (2026-09-01)
- [x] Task 2.2: Add the Codex template and update project setup guidance (2026-09-01)
- [x] Task 2.3: Update overview and folder-structure documentation (2026-09-01)
- [x] Task 3.1: Run consistency, placeholder, and final diff verification (2026-09-01)

---
*Auto-updated by /log. Count used for progress calculation.*
