# Local instruction cleanup review — October 17, 2026

Selected scope: six source files, reviewed as one local corrective checkpoint. The earlier
lean implementation remains 16/16 with E1 open. No deployment or live-host acceptance follows.

| Source | Reviewed result |
|---|---|
| `02_mental-model.md` | Code-validation/red-flag wording survives the compact three-trigger router. Other triggers remain available in the full header. |
| `scripts/gen-directions-index.sh` | Build/test requests load the effects guide; path-only requests preserve their read limit. Discovery, validation and atomic write behavior are unchanged. |
| `CODEX-GLOBAL-TEMPLATE.md` | Generated body matches the generator exactly, including both corrective rules. |
| `CLAUDE-GLOBAL-TEMPLATE.md` | Same generated body; consolidated detection supports master/root state and existing user requests. Unconditional kill/clean/launch recipe is replaced by shared testing and handoff rules. |
| `34_testing.md` | Acceptance steps require inspected support; missing capabilities become blocked proposed requirements. No new live test is authorized. |
| `reference/task-state.md` | Preservation hashes require executed computation/trusted receipts and per-file verification. Unavailable verification leaves reconciliation blocked. |

The October 16 source receipts remain historical. Five corrective-source hashes still match;
Claude's template changed during cleanup. Both complete generated template bodies match current
generator output. Rendered global + repository totals are 11,238 Codex bytes and 18,686 Claude
bytes, versus frozen baselines of 12,120 and 19,748. These are UTF-8 source sizes, not runtime costs.

## Validation

- 50 disposable generator invocations: pass.
- 47-route integration/reference and unchanged out-of-scope baseline-byte checks: pass.
- Eight disposable task-state contract tests: pass. These rehearse records, not host adherence.
- Three headless test-safety demonstrations: pass (producer status, identity selection, owned wait).
- 85 frozen baseline files: hashes/byte counts pass.
- Generator shell syntax and diff whitespace: pass.
- 40 deployment invocations in disposable homes: pass, including both hosts, preservation,
  repeat installs, pre-write rejection, dry runs and unchanged outside sentinels. No live deploy.

Review was serial because the generator and its two rendered template bodies are coupled.
No independent-review or corrected-host behavior claim. Historical replay, byte tradeoffs, deferred
Claude observations and transport admission remain open.

## Checkpoint boundary

Only the six source files above plus this review belong in the checkpoint. Other modified guides,
machine notes, state/history, replay evidence and parked transport/pilot files are retained outside
it. Their presence does not make them reviewed or accepted by this source checkpoint.

Repository identity was verified and origin fetched before checkpoint preparation. The current
branch has 23 commits ahead of its upstream and 35 ahead of origin/main, zero behind either;
it is not already merged into origin/main. No checkout, merge, pull or push is part of this work.
Directions has no supported Codex collision detector; no concurrent writer is known in this session.
