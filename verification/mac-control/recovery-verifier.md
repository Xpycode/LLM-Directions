# Offline restart/reconciliation verifier

September 9, 2026.

Follow-up: the [snapshot/evidence adapter](recovery-adapter.md) is implemented and tested offline;
that report supersedes the next-task pickup below. Native probe/transport integration remains pending.

`Spikes/recovery_verifier.py` checks supplied recovery evidence without reading runtime paths,
looking up or signalling processes, writing markers, or restoring admission. Its public `verify`
function returns `blocked`, `sameBootCandidate`, or `newBootCandidate`; every result explicitly
keeps restart eligibility and native recovery verification false. Task 1.3/Gate A remain open.

## Evidence checked

- Strict existing record parser, exact unresolved run marker and complete empty executor inventory.
- Same boot/session, full run/process identity and SHA-256 binding to the exact record bytes.
  Same-boot candidates require the latest boundary to be durably resolved.
- Exact cumulative posting and receipt sequences, kinds, tags, receipt origins and multiplicity.
  Receipt timestamps can precede post acknowledgements because the acknowledgement is emitted
  after the posting call returns. Duplicates, missing events and receipts after worker exit reject.
- Explicit empty-held checkpoints after each pair's final post return; no checkpoint inferred from
  balanced receipts. The next pair must follow the previous checkpoint and receipts.
- Independently retained owned-wait exits with PID/start/code binding, complete worker/target
  streams, successful target exit, and a run/target-bound observation fence requested at least
  two seconds after both worker exit and stream EOF. Future and reversed timestamps reject.
- A separate new-boot path accepts an unresolved event boundary only with a valid old run-bound
  record, independently obtained different current boot and complete empty executor inventory.
  Old monotonic timestamps are not compared with the new boot clock. Legacy/missing records remain
  blocked; generic first-run/bootstrap recovery requires separate proof.

## Trust boundary and remaining work

These are normalized offline inputs, not authenticated reports. The caller contract requires a
future trusted adapter to obtain the latest marker/record under runtime and storage locks, stable
OS context and complete executor inventory, and independent owned-process/stream evidence.
The adapter must preserve all events, including duplicates and late rows, and reject partial data.
A hash binds bytes to evidence; it does not prove origin, freshness, lock ownership or durability.
No native adapter or startup integration is implemented by this change. Finite observation is
evidence for this bounded experiment, not a general proof against indefinitely late OS delivery.

Next bounded task: implement and test that snapshot/evidence adapter using isolated temporary
namespaces and synthetic owned peers. Include lock contention, concurrent/pending writes, stale
snapshots, incomplete inventory and truncated streams before any native integration. Do not
convert candidate results into automatic marker clearing or retry. The historical legacy marker
was not accessed and remains unresolved; Swift checkpoint source remains uncompiled.

## Validation

The verifier tests enter through its public API with synthetic evidence. A regression feeds the
retained native crash report to the record parser and confirms it cannot retroactively supply a
run-bound durable record; the report bytes stay unchanged. No desktop input or live marker access.

```bash
python3 -B -m unittest discover -s tools/mac-control/Spikes -p test_recovery_verifier.py -v
python3 -B -m unittest discover -s tools/mac-control/Spikes -p 'test_*.py'
git diff --check
```

Final full suite: **140 tests in 22.374 seconds — 139 passed, 1 sandbox boot-query skip**.
All **19 verifier tests passed** in the separate review run. Independent review found that a
later pair's receipt could precede the prior checkpoint despite valid post-return ordering.
The fix checks both next-post and next-receipt timestamps; the new regression and the valid
receipt-before-own-acknowledgement case pass. Review confirmed the fix. Whitespace check passed.
No native build/launch, runtime marker access, commit or push occurred; earlier local edits remain.
