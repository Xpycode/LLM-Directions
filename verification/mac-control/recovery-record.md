# Offline recovery record model

September 9, 2026 · arm64 Mac, macOS 27.0 (26A5425a), Python 3.14.7.

`Spikes/recovery_record.py` implements the bounded next step from the
[reconciliation review](worker-crash-reconciliation.md). The native supervisor and its live
marker are unchanged. This model does not establish recovery or close task 1.3/Gate A.

## Contract implemented

- Version 1 records bind boot, login session, run, worker and target PID/start/code identities.
  Exact schemas reject extra fields, duplicate JSON keys, unknown versions, legacy markers,
  incomplete identities, invalid types and oversized input. No paths, payloads or capabilities.
- Up to 256 ordered, uniquely tagged alternating down/up events retain the cumulative admitted
  boundary. Admission makes the record uncertain. Only an explicit checkpoint after an even
  boundary, empty held state and exact cumulative receipts can resolve that boundary.
- A later admission invalidates the preceding resolved boundary. Identity, sequence or tag
  mismatches, duplicated/missing receipts and posting-only evidence cannot resolve it.
- The write gate permits one outstanding revision. An exact durable acknowledgement models
  readiness for one dispatch; consuming it prevents replay. Loading a record restores no permit.
  Stop, failed writes, overlapping writes and stale acknowledgements close admission permanently.
  Failure during a new uncertain write retains the attempted boundary conservatively; failure
  during a resolving write retains the preceding uncertainty.
- A resolved record plus matching independently supplied worker/target exit and observation
  evidence yields only a recovery **candidate**. No function clears a marker or signals a process.

## Validation and limits

Tests use fake identities/checkpoints/receipts and isolated temporary files. The test file adapter
round-trips bytes; its acknowledgement is simulated. It does not implement or test crash durability,
atomic replacement, filesystem permissions, live locking, OS identity verification or native input.
Record fields describe validated evidence; parsing a report cannot authenticate that evidence.

The initial targeted test run failed because the module did not exist, then passed after
implementation. Full-suite command:

```bash
python3 -B -m unittest discover -s tools/mac-control/Spikes -p 'test_*.py' -v
git diff --check
```

Full suite: **74 tests passed in 16.455 seconds**, including 13 new record-model tests.

## Next integration boundary

Later continuation: [checkpoint transport and separate writer](checkpoint-storage.md) are now
implemented with 89 passing offline tests; verified OS identities and admission integration remain next.

Add the worker's explicit post-held-state-update checkpoint and bind its transport to the current
run. Require matching receipts/checkpoint before controlled crash injection. Implement a separately
serviced durable writer whose acknowledgement gates new admission while Stop/watchdogs remain
responsive. Verify current identities and the exclusive live lock outside this pure model.

The current plain unresolved marker remains blocked; do not fabricate an identity or checkpoint
for the old trace. No runtime path or native launch is part of these tests. A future foreground
experiment still needs its own agreed window under the existing implementation plan.
