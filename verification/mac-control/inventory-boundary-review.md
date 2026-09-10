# Inventory-boundary review

September 10, 2026 · Wave 1, task 1.3 continuation on M1 Max.

**Later offline continuation:** [final-observation review and validated fixes](final-observation-review.md)
adds precise identity/observation diagnostics and append-only wrapper reporting. No native retry;
the historical results below remain unchanged.

## Finding and bounded change

The September 9 `inventoryAfterFirstScan` failure covers enumeration, validation and
comparison in one stage. The retained report cannot distinguish these causes. Three earlier
successful complete observations establish that the contract was satisfiable at those instants;
they do not establish process stability during the later failed acquisition.

Refine fixed failure stages to distinguish query failure, invalid inventory and observed
process-set change at each inventory boundary. Preserve strict buffer/PID checks, all-process
inspection, both scans, three agreeing enumerations, the helper deadline and output limits.
Keep historical stage names recognizable; do not reinterpret existing evidence.

The refined inventory stages use `Query`, `Malformed` and `Changed` suffixes.
`Query` means the enumeration call raised an exception. `Malformed` includes invalid
returned counts (zero, negative, partial or full-buffer), invalid/duplicate PIDs and
missing caller identity. It does not prove that the underlying kernel query succeeded.
`inventoryInitial` has no prior set to compare, so only query/malformed outcomes apply
there; a missing caller also fails validation. Both subsequent inventory boundaries can
report a valid but different PID set as `Changed`. No PID list, path, errno or native
exception text is added to diagnostic output.

## Quiet-window assessment

A quiet observation window can reduce incidental process starts/exits, but is not proof of
completeness. Success still requires every process to be readable and stable and all three
inventories to agree under the cooperating marker lock. Do not exclude transient processes,
terminate unrelated apps, change the process filter, relax equality, or retry until success.

One separately recorded read-only observation with the refined diagnostics can show the
current result. It is not acquisition or baseline retention, cannot identify the historical
cause, and cannot authorize recovery. If it fails, retain the exact fixed stage and stop.
If it succeeds, a fresh prospective capture and separate-process reload still need their own
transaction and scope before any boot-transition discussion.

The diagnostic invocation is
`python3 -B -I /private/tmp/directions-inventory-boundary-observation.py`.
It uses the original launcher's explicit local marker path, confirms the Darwin temporary
root, acquires `MarkerLock` with `create=False`, and checks marker bytes and namespace/file
fingerprints before release. It performs exactly one bounded observation, exclusively creates
its evidence report before observing, and emits only safe stages and verifier context.
No failed acquisition transaction is reused. No marker write, input, build, activation or
initialization is part of this observation.

The first wrapper invocation stopped at its preflight path comparison, before report creation,
marker acquisition or observation: Darwin returned `/var/folders/...`, while explicit trusted
configuration uses `/private/var/folders/...`. A read-only `resolve(strict=True)` check proved
the paths identical. The wrapper now canonicalizes that Darwin alias for comparison, as the
existing acquisition wrapper does. `MarkerLock` still opens the explicit canonical path with
its unchanged no-follow checks. This was not an inventory or acquisition attempt.

## Validation

- Environment: M1 Max, macOS 27.0 (26A5425a), Python 3.14.7.
- Acquisition regression was confirmed RED before implementation: the specific stage was
  reduced to `helperExit` instead of surviving in the failed acquisition report.
- Full suite: `python3 -B -m unittest discover -s tools/mac-control/Spikes -p 'test_*.py'`
  ran 370 tests in 42.938 seconds: **369 passed, one existing sandbox skip**.
- Independent Astra review found no production safety/correctness blocker. Its requests
  to clarify invalid-return semantics and test the actual adapter/helper path were addressed.
- Added one subprocess regression with two cases retaining actual `_Kernel.pids`,
  `capture_context`, `probe_main` and bounded parent validation. Partial-byte/duplicate-PID
  returns at post-first/post-second boundaries yield exact `Malformed` stages and exactly
  two/three enumeration calls. Only native calls are fixtures.
- Final focused command, from `tools/mac-control/Spikes`:
  `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_recovery_context.py test_recovery_probe.py`
  passed **34 tests in 1.328 seconds**. No production source changed after the broad suite.
- One fresh-context Sol agent owned context implementation/tests; the coordinator owned
  the acquisition regression, broad suite, runbook/evidence, state and Git. Astra independently
  reviewed the final source and diagnostic wrapper. No parallel writers shared these files.

## Remaining boundary

The single native diagnostic **passed** in 260.090 ms:
[retained observation](inventory-boundary-observation-2026-09-10.json).
It returned complete empty inventory, with unchanged marker bytes and directory/file
fingerprints. Both authority flags are false. The reported boot matches the September 9
diagnostic boot; no later-boot proof has been established. This does not identify the prior
acquisition's failure cause.

### Prepared next action — fresh capture and separate-process reload

Read-only preparation passed:
`python3 -B -I /private/tmp/directions-prospective-acquisition-2026-09-10.py inspect`.
This is the existing reviewed acquisition wrapper with fresh transaction/report names and
an updated operator record. It checked canonical private parents, absent transaction/report
paths, and separation from all four configured Syncthing roots. Other sync services were not
assessed. It created no directories or acquisition evidence.

Concrete next invocation, requiring separate native-storage scope under the
[delivery boundary](delivery-review.md#next-bounded-work-packet):

```bash
python3 -B -I /private/tmp/directions-prospective-acquisition-2026-09-10.py run
```

Fresh transaction: `acquisition-390583674a3f43c88fd04375da922533`.

- Evidence/archive parent: `~/Library/Application Support/Directions/MacControlEvidence/acquisition-390583674a3f43c88fd04375da922533`
- Independent anchor: `~/.config/directions/mac-control-anchors/acquisition-390583674a3f43c88fd04375da922533`
- Output: `verification/mac-control/prospective-acquisition-2026-09-10.json`.

The wrapper makes one fresh capture, reloads in a separate process only after success, compares
the retained digest/acquisition metadata, and stops/preserves partial artifacts on failure.
It does not reuse either failed transaction, request a reboot, mutate the marker or launch apps.
The user subsequently authorized `run`; the result is recorded below. This transaction
must not be reused, and `inspect` now correctly rejects its existing paths.

### Authorized native result — failed after baseline retention

Read-only `inspect` passed again, then the exact `run` invocation above was executed once.
[Retained command/output](prospective-acquisition-2026-09-10.json) records capture exit 1,
`failure_stage: processIdentity`, `result: unresolved`, and both authority flags false.
The wrapper stopped immediately; no reload followed and no retry was made.

Read-only artifact verification found:

- The archive is 32,678 bytes and matches the selected historical source byte-for-byte.
- Baseline `witness.json` and `witness.tmp` each contain 3,005 bytes; the other four witness
  directories are empty. Independent `anchor.json`, `anchor.tmp` and `anchor.fence` remain.
- The current original marker bytes are `unresolved`.

Unlike the September 9 attempts, this attempt reached baseline retention. In `capture`, the
baseline is retained before the final `_observe_locked` recheck; a `processIdentity` failure
after those retained artifacts therefore localizes this run to that final observation phase.
The stage does not distinguish an unreadable/disappearing process from invalid identity data,
nor identify which of the two final observations failed. No native error text or PID details
were collected. Current marker bytes are not a substitute for a successful final continuity
check. Surviving witness files do not establish completed acquisition or authorize recovery.

All three failed transactions are preserved. Next: review the final process-identity failure
and its retained evidence before proposing another native action. No reboot, initialization,
activation, app build/launch or desktop input occurred. The stop-on-failure boundary is active.

Task 1.3 and Gate A stay open. The two failed September 9 transactions remain preserved.
The historical crash remains failed/unknown and the runtime marker unresolved. A successful
diagnostic cannot establish native recovery, clipboard handling or broader intervention proof.
Wave 2 task 2.1 remains blocked by Gate A; the separate efficiency plan is outside this run.
