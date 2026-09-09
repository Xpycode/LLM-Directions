# Checkpoint transport and asynchronous record storage

September 9, 2026 · arm64 Mac, macOS 27.0 (26A5425a), Python 3.14.7.

**89 offline tests passed in 16.689 seconds.** Checkpoint transport is wired into the supervisor's
worker-crash case. The dedicated record writer is implemented and tested separately; it is not
yet connected to live admission. The current unresolved runtime marker was not read or changed.
Task 1.3/Gate A remain open.

## Worker and supervisor

- Binding now includes a fresh 32-character hexadecimal run ID. The worker saves it on the
  existing main run loop and emits a distinct checkpoint only after normal key-up posting returns
  and `held` becomes false. Stop cleanup retains its separate stopped acknowledgement.
- The checkpoint carries run, completed sequence/tag and empty-held-state evidence. The crash
  case waits for the explicit checkpoint plus posting and target receipt before advancing past
  each key-up. Its existing receipt timeout bounds a missing checkpoint.
- The supervisor rejects stale/duplicate boundaries, changed run/tag, held state, extra fields
  and ambiguous types. Controlled crash injection still requires six complete pairs, correct
  target origins and text prefixes. No old posting row is upgraded into a checkpoint.
- Synthetic transport deliberately delivers receipts before posting/checkpoint. Missing and
  malformed final checkpoints prevent controlled crash injection and prevent a thirteenth event.

The Swift edit was source-reviewed but **not compiled or launched**. The Python tests substitute
the native children and do not establish that the real worker emits the new frame correctly.
Old worker artifacts reject the changed binding schema; rebuild both sides together during the
next agreed native window. No new native window is needed for the remaining offline integration.

## Storage component

`recovery_storage.py` owns a dedicated disk thread and a fixed-name lock in a fresh private
directory. Construction performs pre-input filesystem setup; submit/poll/close do not wait for
disk or join the writer. One revision may be outstanding, and identity/revision transitions are
validated against the preceding acknowledged record. A prepared record must be saved first.

Writes use an exclusive temporary file, complete short writes, fsync plus Darwin F_FULLFSYNC,
atomic replacement and directory fsync before returning the exact bytes as acknowledgement.
The writer retains its lock/directory descriptors until I/O finishes. Closing suppresses even
queued acknowledgements; a stuck writer cannot make close wait. Its finished event means resource
release only, never input quiescence. The future broker's live lock must outlive worker cleanup
independently of this storage lock.

Tests use only fresh temporary namespaces, real files, a real lock and a writer thread. They cover
stalled file/directory flush, short/zero writes, flush/replace failures, changed identity, overlapping
requests, symlinks, permissions and abrupt Python-process death before flush. Existing or partial
namespaces are refused, including after lock release. This fresh-only API is not a runtime
bootstrap/reconciliation implementation and must never be pointed at the live namespace.

Stall tests keep the flush blocked while polling and closing the writer and stopping the record
gate. They verify cancellation remains callable and the lock remains held until completion.
This is component-level cancellation evidence, not a supervisor/watchdog latency measurement.
Filesystem tests exercise the available flush APIs, not simulated power loss or storage hardware.

## Validation

Initial checkpoint tests failed against the old supervisor behavior; storage tests initially
failed for the absent module. Following implementation, the complete suite passed:

```bash
python3 -B -m unittest discover -s tools/mac-control/Spikes -p 'test_*.py' -v
bash -n tools/mac-control/Spikes/build.sh
git diff --check
```

Shell syntax and whitespace checks passed. No native build, desktop input, permission change,
marker reconciliation, commit or push occurred.

## Next bounded step

Implement verified boot/login and owned-process start/code identity acquisition, then connect
the writer/record gate to supervisor admission using injected identities and transport tests first.
Define a bounded write deadline serviced in the normal loop, route failures into Stop, reject
late acknowledgements, and test heartbeats/Stop while the real writer is stalled. Preserve the
reserved cleanup-up uncertainty when adapting the event ledger. No dispatch may precede its
uncertain durable record, and no next admission may use a stale checkpoint.

The current legacy marker remains unresolved. A future native recovery candidate still needs
independent receipt/observation/exit evidence and an agreed experiment window.
