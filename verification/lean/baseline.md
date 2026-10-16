# LE01 implementation-start baseline

Captured 2026-10-16 before workflow/script changes: 85 source files in `baseline/source/`, with
SHA-256 and byte counts in `baseline/manifest.json`. The manifest retains HEAD and initial dirty
status. Existing platform-guide and planning edits are part of this working-tree baseline, not
changes attributable to this execution. Copies are immutable evaluation fixtures, not routed guides.

| Source | September bytes | Execution-start bytes |
|---|---:|---:|
| CODEX-GLOBAL-TEMPLATE.md | 8,406 | 8,406 |
| CLAUDE-GLOBAL-TEMPLATE.md | 19,385 | 19,385 |
| AGENTS.md | 3,615 | 3,615 |
| 52_context-management.md | 33,813 | 33,813 |
| commands/log.md | 16,803 | 17,024 |
| commands/execute.md | 11,104 | 11,104 |

The logging difference is the already-recorded October growth, not this implementation.
`scenarios.md` freezes 23 inputs/oracles and routing coverage. The baseline includes the deferred
Mac-control plan for preservation checks. Do not execute historical app-control prescriptions.

Environment: current Codex API session on macOS; exact host build/model effort not reliably exposed.
Actual fresh-host runtime, calls, questions and latency metrics are unavailable here and reserved
for E1. Static source bytes are neither token counts nor measured speed/cost. Three matched fresh
runs per host/scenario remain a host-acceptance requirement.

Validation: `python3 verification/lean/measure.py --check-baseline` checks every preserved file;
`--compare` reports current source bytes without changing the frozen data. The coordinator reviewed
all S01–S23 for observable outcomes including forbidden-action negatives and positive scoped control.
