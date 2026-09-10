# Shared runtime root and opt-in kernel inventory

September 10, 2026 · Wave 1 / task 1.3 · implementation and offline validation.

## Shared-root correction

The [counterexample](kernel-inventory-review.md#shared-root-counterexample) is addressed
by one independent source pin in `Spikes/runtime_root.py`, matching the already configured
native capture callers. The OS temporary-directory lookup is a consistency check, never
authority to select another namespace. Its canonical form may account for Darwin's `/var`
alias, but the actual marker open always uses the fixed canonical pin and the existing
no-follow descriptor walker. A lookup that resolves elsewhere rejects before launch.

The supervisor now requires the directory and lock to exist (`create=False`). It never
creates an alternate directory/marker, repairs missing state or migrates the unresolved
marker. Existing mode, owner, lock contention, marker/fence and retained activation checks
remain. This is explicitly a current-host spike; another Mac or lost temporary state fails
closed until a separately reviewed provisioning/configuration procedure exists.

Supported native boundaries are supervisor startup, acquisition CLI capture, preflight CLI
legacy inspection, retained activation and the tracked observation/acquisition wrappers.
They share the pin check. Fully injected clock/observation APIs and generic storage functions
remain internal offline seams; they do not establish native launch exclusion on arbitrary
roots. Old launchers, separately edited source pins, hostile same-UID code and deletion or
replacement of the namespace during use are outside the cooperative supported contract.
Pinning a path is not a historical inode/provenance proof: the existing retained-evidence
checks still establish continuity for recovery.

## Opt-in integration

`recovery_kernel_context.py` adapts one validated C inventory result to the existing context
schema only under the [conditional absence contract](kernel-inventory-review.md#preconditions-and-proof).
`inventory_complete=True` here means coverage of surviving conforming fixed-name executors
under uninterrupted shared launch exclusion, not an atomic historical process snapshot.
Candidates, all C errors, unknown statuses, changed UID/boot/session and artifact validation
failures reject; there is no query retry or fallback to the previous adapter.

`recovery_probe.capture_bounded_context(..., inventory_library=(path, sha256))` explicitly
selects the new adapter. The isolated helper receives the trusted artifact pin and the same
continuous clock as the supervisor. Existing output limits, two-second default deadline,
50 ms scheduled checks and bounded owned-helper cleanup remain. A blocked kernel call can
still exceed cleanup timing; timeout/reap failure rejects and never authorizes recovery.
No library configuration keeps the existing adapter; default native callers are unchanged.

`build-inventory.sh` compiles only a dylib, prints its canonical path/digest and never calls
the native query. The prepared [one-shot observation](kernel-inventory-observation.py) pins
the resulting artifact, reuses the original locked append-only observation caller, and
uses a new exclusive report. Existing consumed journals and all five failed transactions
remain untouched. Source/library changes require a new reviewed pin, not an automatic rebuild.

## Native observation — passed once

```sh
python3 -B verification/mac-control/kernel-inventory-observation.py
```

The caller pins `/private/tmp/directions-inventory.1aT0KH/recovery_inventory.dylib`
with SHA-256 `b0d46b7fb180e1e04d29b538f18d19211fd90f6342106d917c7dcfa51c6eedfc`.
It holds the existing marker lock read-only, requires `unresolved`, performs one bounded
inventory/context observation, verifies unchanged marker bytes/fingerprints and appends
`kernel-inventory-observation-2026-09-10.jsonl`. It never acquires a new baseline, initializes,
activates, clears the marker, launches an app or sends input. A failure consumes its report;
no retry follows. Successful observation alone does not close recovery or Gate A.

After implementation, independent review and tool approval, this exact observation ran once
outside the sandbox and exited 0 in **337.630 ms**. The
[append-only journal](kernel-inventory-observation-2026-09-10.jsonl) records one observation,
empty conforming-executor inventory, unchanged marker bytes/fingerprints, and both authority
flags false. No retry, native acquisition, marker mutation or foreground action occurred.
The journal is consumed; do not rerun this caller.

## Fresh acquisition — capture and reload passed

```sh
python3 -B verification/mac-control/prospective-acquisition-kernel.py inspect
python3 -B verification/mac-control/prospective-acquisition-kernel.py run
```

`inspect` passed read-only location checks, the shared root check and library hash verification.
The new transaction is `acquisition-c6448ce2f81c44f78af0752199fdae2b`. `run` exclusively
creates its evidence/slot/archive subtree under
`/Users/sim/Library/Application Support/Directions/MacControlEvidence` and independent anchor
subtree under `/Users/sim/.config/directions/mac-control-anchors`, plus a new repository journal.
Both parents are private and the selected transaction paths are disjoint from all four
configured Syncthing folders and the runtime namespace. Other sync services are not assessed.

The capture CLI explicitly passes the same library pin through all four bounded observations,
retains the prospective baseline and acquired-now historical copy, then reloads in a separate
process only if capture succeeds. Any failure stops and preserves the new partial transaction;
none of the five previous attempts or three observation journals is reused. The marker remains
read-only; no initialization, activation, reboot, app launch or input is included.

After the user's September 10 continuation and tool approval, `inspect` passed again and
`run` executed exactly once outside the sandbox, exiting 0. The
[consumed journal](prospective-acquisition-c6448ce2f81c44f78af0752199fdae2b.jsonl)
records successful capture and separate-process reload, matching baseline/acquisition bindings,
unchanged marker and both authority flags false. All five failed transactions and three earlier
observation journals remain preserved. Do not rerun this caller or reuse its transaction.

Task 1.3/Gate A remains incomplete; later-boot continuity,
explicit initialization/activation and actual recovery/clipboard/intervention proof remain.

## Assignments and validation

Coordinator owns shared runtime-root source, native entry guards, helper integration,
build-only script, prepared caller, new regressions, documentation and Git. A fresh-context
agent audited entry points and adapted eight existing fixture suites; a second independent
agent approved the shared-root implementation and ran its eight regressions. A fresh-context
implementation agent owns only the new kernel-context adapter and tests. Integration review
and final validation are recorded below when complete.

Shared-root checkpoint: 55 adapted lock/activation/storage tests passed; eight new root
regressions passed. Broad suite ran 435 tests in 48.651 seconds: **434 passed, one existing
skip**. Existing suite includes limited native self-identity/session smoke checks; the new
tests use private roots and mocked OS boundaries, with no live runtime-marker access.
Compilation-only `bash Spikes/build-inventory.sh` succeeded without running the library.

Opt-in integration: broad suite ran **457 tests in 47.170 seconds: 456 passed, one existing
skip**. The final compiled-C/real-loader/helper/parent-wire regression then passed with all
20 C fixture tests in 0.449 seconds; only `sysctl` and boot/session/clock are substituted,
and the fixture dylib has no native `_sysctl` reference. Eighteen new adapter tests passed.
Independent integration and prepared-observation review found no blockers, confirmed the
actual artifact hash/export/dependencies read-only, and ran those 18 tests. The adapter's
unit tests do not load the production artifact. The single native result above is separate.

Fresh capture preparation: 19 acquisition tests and independent caller/CLI review passed.
Final affected-suite check ran **66 tests in 4.746 seconds, all passed**:
`python3 -B -m unittest test_recovery_acquire test_recovery_acquire_run test_runtime_root test_recovery_probe test_identity_observation -q`
from `tools/mac-control/Spikes`. Read-only wrapper inspection passed; `run` has not executed.
Independent review also confirmed the final compiled-parser/helper regression. All current
source and callers are reviewed; remaining native storage authorization is the next boundary.

Pre-clear audit: whitespace and touched-shell syntax checks passed. The index script's known
45-missing/zero-orphan warning persists because it omits archived rows; combined live/archive
audit has no missing targets and the same three already recorded unindexed logs. No index
repair or push. Scoped local execution checkpoint; today's session log remains ignored/local.
