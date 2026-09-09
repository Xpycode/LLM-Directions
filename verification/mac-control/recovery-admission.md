# Durable admission and identity integration

September 9, 2026 · arm64 Mac, macOS 27.0 (26A5425a), Python 3.14.7.

The worker-crash case now connects verified identity setup, the versioned record and the dedicated
writer to the real supervisor loop. Offline tests substitute the native peers and clock while
exercising actual storage. No native executable was compiled/launched, and the current unresolved
marker was not accessed or changed. Task 1.3/Gate A remain open.

## Implemented contract

- `recovery_identity.py` obtains boot UUID, caller security session, owned child PID/parent/UID/start
  and canonical executable path from Darwin APIs. Hashing checks stable file metadata before and
  after bounded reads, then repeats both child/context snapshots. The setup layer compares captured
  digests with the already verified build artifact digests before creating its private writer.
- Identity acquisition and writer setup run on a dedicated thread. The normal supervisor loop
  enforces a three-second setup deadline, services heartbeats/Stop, and waits for the prepared record
  to be durable before binding the worker. An early worker bound message cannot bypass this gate.
- Each down and its possible normal/emergency cleanup up are reserved together in one uncertain
  durable revision. The admission controller consumes exact sequence/tag permissions once only.
  No down can precede the pair's acknowledgement, and no new pair can precede a resolved checkpoint.
- Checkpoint resolution matches actual target receipt and worker post kinds as well as tags,
  origins, prefixes and the explicit empty-held-state checkpoint. Duplicate postings/receipts and
  wrong kinds fail. The controlled kill requires the sixth pair's checkpoint to be durable.
- Every write has a 400 ms deadline. Timeout, failure, mismatched acknowledgement and Stop close
  admission, cancel result delivery and send the existing worker Stop. The controller never joins
  the writer in the input loop. A late durable completion cannot reopen input.
- For future worker-crash runs only, the existing exclusive lock is marked `unresolved:<run ID>`
  and synced before children launch. The same run ID appears in the record and worker checkpoint.
  Legacy unresolved markers remain blocked; no migration or retroactive identity is performed.

Other native cases retain their earlier admission path. This is still an isolated spike, not a
production bootstrap or general broker. No record is accepted as authority to signal a PID.

## Verification

Test-first transport regressions exposed two review findings: an early bound message could bypass
setup, and tag-only receipts could treat two keyDowns as a completed pair. Both were fixed and
independently rereviewed. The tests now reject those cases and duplicate posting acknowledgements.

Real-writer transport tests verify pair durability at each synthetic dispatch, checkpoint durability
before kill, Stop and heartbeat service during stalled writes, write failure/deadline closure and
setup timeout. Separate tests cancel blocked identity setup and reject artifact changes before
writer creation. An isolated real-lock test verifies new run binding and unchanged unresolved bytes
on restart. All storage/runtime namespaces in these tests are temporary test-owned directories.

Commands:

```bash
python3 -B -m unittest discover -s tools/mac-control/Spikes -p 'test_*.py'
python3 -B -m unittest discover -s tools/mac-control/Spikes -p test_recovery_identity.py -v
bash -n tools/mac-control/Spikes/build.sh
git diff --check
```

The sandbox denies `kern.bootsessionuuid`; its availability smoke test skips there, while capture
fails closed. The identity-only command also ran outside the sandbox: **all 19 tests passed**,
including real self-process/path, boot UUID and security-session API checks. No identities were
printed and no native app or live marker was involved.

Final full suite: **121 tests in 21.805 seconds — 120 passed, 1 sandbox availability skip**.
That skipped boot check passed in the separate outside-sandbox identity run above. Shell syntax
and whitespace checks passed. No native build, marker mutation, commit or push occurred.

## Limits and next work

The security-session identity describes the caller session inherited by the owned children; this
does not attest a child deliberately changing sessions. Digests describe verified disk artifacts,
not signatures or mapped-memory integrity. Identity probing can block in OS I/O, so the external
setup deadline remains necessary. Synthetic clock/transport tests do not establish native input
timings, actual checkpoint emission or power-loss durability.

Next implement a read-only restart/reconciliation verifier that binds retained records to the
marker, boot/session and independent worker/target exit/receipt/observation evidence. Cover legacy,
incomplete and mismatched records plus the verified-new-boot path offline. A complete record is
still only candidate evidence: the current legacy marker remains unresolved, no automatic retry
is permitted, and native compilation/foreground testing needs a separately agreed window.
