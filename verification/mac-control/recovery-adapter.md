# Locked snapshot and independent evidence adapter

September 9, 2026 · arm64 Mac · macOS 27.0 (26A5425a) · Python 3.14.7.

The offline adapter now connects actual locked file snapshots and owned process streams to the
recovery verifier. `recovery_snapshot.py` handles filesystem snapshots; `recovery_evidence.py`
collects independent pipe/wait evidence and exposes `check_recovery`. Every result remains a
candidate or blocked: no restart permission, native recovery claim, marker clearing or replay.

## Implemented

- Two explicitly configured directories match the actual spike layout: the persistent marker
  directory contains `lock`; the separate run directory contains `recovery/record.lock` and
  `record.json`. Both locks are acquired exclusively and without waiting, marker first, and held
  through evidence verification and final rechecks. No path is extracted from a report.
- Opens follow no symlinks, including path ancestors. Private directory/file permissions, UID,
  regular-file type, link count, size limits and run identity are checked. Missing, partial,
  unknown or pending storage entries reject. Names, bytes and metadata are rechecked before
  release; a cancelled writer that still has pending I/O retains its lock and blocks the snapshot.
- An observer attaches before dispatch to retained child handles and trusted launch identities.
  Source identity comes from the pipe, exits from owned waits, and stream completion from actual
  EOF. Framing is bounded and rejects malformed, duplicated-key, partial and forged lifecycle
  messages. Actual event order, kinds, origins, duplicates and extra rows are preserved.
- Final durable acknowledgement is bound once, independently of the restart snapshot. All
  matching receipts/posts/checkpoints must already be collected, then both children must still
  be observed alive. The record digest cannot be supplied by reading the snapshot under test.
- The observer requests a fixed input-free target fence only after the required interval following
  worker exit/EOF observations. Target acknowledgement, successful target exit and both stream
  EOFs are required. Verification uses two fresh, consistent context/inventory probes under locks.

## Review finding and correction

Delayed polling originally stamped worker exit after an already-late receipt, allowing a false
candidate. An owned wait timestamp is an upper bound on exit, not the exact exit instant.
The correction validates the complete boundary and observes the worker still alive before binding
the durable acknowledgement. Thus collected receipts precede proven liveness; subsequent extra
rows still reject. A real-pipe regression delays the final receipt until after independently waited
worker exit and confirms binding fails. Early binding also fails.

## Validation

Tests use private temporary directories and fixed Python peers, with no input APIs or native apps.
One successful integration exercises the actual two-second observation interval. Other rejection
fixtures shorten only that interval. A real RecordWriter test binds actual durable acknowledgement
bytes to collected receipts/checkpoints; its synthetic storage replay does not test dispatch
admission order (the existing admission integration suite owns that contract).

```bash
python3 -B -m unittest discover -s tools/mac-control/Spikes -p test_recovery_evidence.py -v
python3 -B -m unittest discover -s tools/mac-control/Spikes -p 'test_*.py'
git diff --check
```

Final full suite: **171 tests in 24.574 seconds — 170 passed, 1 sandbox boot-query skip**.
The additions comprise 17 snapshot and 14 evidence tests. Independent review confirmed the
delayed-exit correction and reran all 14 evidence plus 19 verifier tests successfully, with no
additional actionable findings. Whitespace check passed. No native build/launch, live marker
access, commit or push occurred. Earlier local edits remain preserved.

## Limits and next work

The OS context/inventory probe and launch identity remain trusted injected dependencies, using
synthetic values in these tests. There is deliberately no native default that could misrepresent
an incomplete process scan as complete. Advisory locks protect cooperating writers; private paths
and hashes do not authenticate a hostile same-UID process. Filesystem/OS reads may block, so the
adapter must remain outside active input/Stop handling. Verdicts carry no authority after unlock.

Next bounded task: implement the read-only Darwin boot/session and complete managed-executor
inventory probe, first with mocked kernel enumeration tests for errors, truncation, process races,
unreadable candidates and identity drift. Then wire the actual native observer/acknowledgement
transport without weakening parent identity or worker supervision. A process name or report PID
must never become signalling authority. Native build/foreground testing needs a separately agreed
window. Current historical marker remains unresolved and was not accessed; Swift checkpoint source
remains uncompiled. Task 1.3/Gate A, clipboard and broader intervention proof remain open.
