# Supervisor reconciliation under retained ownership

September 9, 2026 · macOS 27.0 (26A5425a), arm64 · offline fixtures only.

The supervisor now retains an explicit `MarkerLock` owner from experiment acquisition through
teardown, evidence verification and trace persistence. Snapshot reconciliation borrows that owner;
it never releases, reacquires, duplicates or closes the marker descriptor. The owner validates its
private descriptor and namespace, while snapshots additionally pin file bytes and metadata.
Raw descriptors and persisted evidence reports cannot supply this ownership or owned-process proof.

After input handling and native-child teardown, the supervisor cancels setup and waits up to two
seconds for setup completion and writer resource release. This includes cancellation during writer
construction, before the collector exists. Pending resources produce a blocked verdict. The snapshot
also independently acquires the storage lock, rejecting contention, pending files and changed state.

Two fresh OS-context samples bracket the retained in-process evidence under both locks. Each sample
runs in a fixed owned Python helper with inherited descriptors closed, bounded output, and a two-second
deadline using the supervisor's continuous clock. The helper calls `capture_context(clock=mac_clock())`.
Only that helper can be killed on timeout; cleanup has a further half-second reap allowance.
Process creation itself cannot be interrupted by Python, and synchronous filesystem calls are not
hard real-time operations. An observed launch overrun rejects the sample rather than yielding success.

`recoveryReconciliation` is recorded after teardown and mirrored to the client. A synthetic successful
result is `sameBootCandidate`, with `restartEligible=false` and `nativeRecoveryVerified=false`.
It does not change the failed crash-experiment exit, unresolved marker, or task 1.3/Gate A.
Owner cleanup also covers setup and trace-write exceptions; it never clears a crash marker.

## Validation

Full suite: **244 tests in 28.602 seconds — 243 passed, one existing sandbox boot-query skip**.
Whitespace validation passed.

Tests use private temporary files, real locks/writers and owned Python peers, with synthetic native
transport, identities and OS context. They cover original-lock retention, owner closure/reuse,
namespace/byte changes, pending writer locks, resource deadlines, setup cancellation before writer
publication, context drift, probe failure, output pressure, EOF/exit deadlines and non-authorizing
supervisor integration. Independent review found the missing-collector early-return gap; it was fixed
and regression-tested. No native inventory query, Swift build, desktop input or runtime marker access.

```bash
python3 -B -m unittest discover -s tools/mac-control/Spikes -p 'test_*.py'
git diff --check
```

## Next bounded task

Validate native context/inventory visibility in a read-only preflight and review the historical
unresolved marker's recovery path. The historical crash predates the durable run record and cannot
be accepted by replaying its report into this verifier. Prepare any needed native compilation and
new crash experiment concretely before requesting the separately agreed foreground window.
The changed Swift checkpoint transport remains uncompiled. Broker-death recovery, clipboard and
broader intervention proof remain pending; the production package and UI stay behind Gate A.

No commit, push, install, marker clear or native launch occurred. Prior dirty work remains preserved.
