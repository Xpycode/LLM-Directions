# Retained acquisition and prepared later-boot inspection

September 10, 2026 · Wave 1 / task 1.3 · Gate A remains open.

## Native acquisition result

The user requested continuation after status identified the prepared capture/reload as next.
The reviewed wrapper's `inspect` passed, then `run` executed once under tool approval.
Both capture and separate-process reload exited 0. The
[consumed journal](prospective-acquisition-c6448ce2f81c44f78af0752199fdae2b.jsonl)
records matching retained baseline/acquisition metadata, unchanged marker, and false
launch/recovery authority. Five earlier failed transactions and three observation journals
remain preserved. The successful acquisition wrapper must not be rerun, including its inspect mode.

## Preparation discovered by independent review

The previous inspection CLI required raw baseline files and lacked kernel inventory selection.
Its existing fixture test bypassed both issues with an exported fixture and injected observer.
The new `inspect-acquired` operation connects the retained acquisition loader to the existing
locked later-boot inspection, using the explicit reviewed inventory pin. It does not export
baseline bytes or derive trust from diagnostic journal hashes. Retained loading flushes existing
witness/configuration files; the runtime marker and evidence content remain unchanged.

The reviewed dylib was copied byte-for-byte, with tool approval, into a fresh private directory:

```text
/Users/sim/Library/Application Support/Directions/MacControlEvidence/inventory-b0d46b7fb180e1e04d29b538f18d19211fd90f6342106d917c7dcfa51c6eedfc/recovery_inventory.dylib
```

The source and destination hashes equal the suffix above. File creation was exclusive; file
fsync/F_FULLFSYNC and directory/parent fsync completed. Directory mode is 0700 and file mode 0500.
Read-only `otool -L` shows only libSystem as an imported dependency. The original temporary
install ID is the dylib's own identity, not a dependency; the explicit-path loader needs no
install-name rewrite. No native code was loaded or inventory queried during staging. This
location shares the previously inspected machine-local evidence parent, outside configured
Syncthing roots. Other synchronization services and power-loss durability are not established.

## Exact next operation

The [one-shot caller](acquired-preflight-kernel.py) binds the successful transaction's original
configuration and the persistent library path. Before arranging a restart, inspect preparation:

```sh
python3 -B verification/mac-control/acquired-preflight-kernel.py inspect
```

After a separately agreed restart of this same Mac, resume in this checkout and inspect again.
If all locations and the pinned library still exist, execute exactly once:

```sh
python3 -B verification/mac-control/acquired-preflight-kernel.py run
```

The native attempt consumes `acquired-preflight-c6448ce2f81c44f78af0752199fdae2b.jsonl`.
Failure after launch preserves the journal and never retries. Precheck failure launches nothing.
The command requires a different observed boot and exact original runtime namespace continuity.
It performs bounded observations under the existing marker lock; success is diagnostic only.

**Restart boundary:** no restart was performed or scheduled during preparation. A restart may
remove the original temporary marker directory. Missing/replaced namespace must stop this path;
do not recreate, migrate, copy back, or repair it. If that happens, preserve evidence and review
the design separately. Initialization/activation, repeatable recovery, compiled checkpoint
validation, clipboard and broader intervention experiments still remain before Gate A.

## Validation and assignments

Coordinator owns the native acquisition, artifact staging, one-shot wrapper/tests, integration,
records and Git. A fresh-context implementation agent owns the acquired inspection CLI/tests;
a separate fresh-context reviewer checks the integration and caller. Native capture/reload
success above is separate from offline fixture results. Final validation follows below.

Final validation: 52 focused preflight/acquisition/provisioning tests passed; three wrapper
tests passed, including timeout, malformed/oversized output, false authority and consumed-report
cases. The broad spike suite ran 479 tests in 50.882 seconds: **478 passed, one existing skip**.
Native boundaries in the new tests are substituted; no post-boot observation was performed.
Independent CLI and wrapper reviews found no blocking issue. The prepared caller's read-only
location/artifact `inspect` passed against the staged library; `run` remains unexecuted.

```sh
python3 -B -m unittest discover -s tools/mac-control/Spikes -p 'test_*.py' -q
```

Pre-clear: project state, task, plan and today's existing local log/index were refreshed.
The known archive-unaware index checker still reports 45 missing/zero orphan entries; combined
live/archive checking found zero missing targets and the same three previously recorded unindexed
logs. No repair or push. Local branch `fix/acquired-recovery-preflight` holds this continuation;
today's session log remains ignored/local under existing policy; the session index is tracked. Machine-local witness
storage and the staged dylib are outside Git. Task 1.3 and Gate A remain incomplete awaiting
an agreed same-Mac restart, namespace continuity inspection and remaining recovery experiments.
