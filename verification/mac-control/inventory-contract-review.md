# Inventory disappearance contract

September 10, 2026 · Wave 1 / task 1.3 · inventory implementation validated; recovery incomplete.

## Scope

The [native missing-process observation](identity-read-review.md#native-outcome)
requires an absence proof, not a retry policy. The revised observation permits only
a noncaller process that is missing on its first identity read and absent from both
later inventories. A process still listed but unreadable remains unresolved.
All four failed acquisitions and the consumed observation journal remain preserved.

## Algorithm

1. Validate the initial UID PID list and require caller membership as before.
2. Attempt the first identity read of every listed PID. Only the exact native
   `Missing` category for a noncaller may provisionally omit a row. Do not retry it.
   Other failures, malformed identities, path failures and immediate identity
   recheck failures still reject the entire observation.
3. Let S be the successful first-scan rows. Require the middle enumeration to equal
   exactly the sorted keys of S. An omitted PID that remains listed, an added PID,
   or a vanished successfully read PID rejects.
4. Scan S again with all existing identity/path checks and require exact row equality.
   No second-scan missing process is tolerated.
5. Require the final enumeration to equal S and retain the existing context/caller
   checks and external deadline. Only then return the unchanged context schema.

Every candidate already observed remains represented or causes failure. A disappearing
candidate cannot be silently removed after its path was read. No configurable name
exclusion, stable-missing placeholder, process signalling or automatic retry is added.

## Completeness argument

Apple's [enumeration implementation](https://github.com/apple-oss-distributions/xnu/blob/main/bsd/kern/proc_info.c#L337-L457)
sizes an internal buffer from `nprocs + 20` before taking the process-list lock.
A return smaller than the caller buffer alone does not establish completeness.
However, K surviving incarnations read before and after the middle enumeration
provide a lifetime lower bound: if all are continuously counted, `nprocs >= K`.
Both the internal sizing limit and caller capacity then exceed K, so a middle
enumeration returning exactly K entries cannot have filled either buffer.
That middle observation supplies the completeness proof retrospectively.

The independent source review confirms the count across exec transitions:
[forkproc](https://github.com/apple-oss-distributions/xnu/blob/main/bsd/kern/kern_fork.c)
increments `nprocs` for ordinary creation and exec shadow allocation. Exec carries
the logical PID/start identity into the replacement;
[exec handover](https://github.com/apple-oss-distributions/xnu/blob/main/bsd/kern/kern_exec.c)
switches the hash/shadow state under the process-list lock.
[Final removal](https://github.com/apple-oss-distributions/xnu/blob/main/bsd/kern/kern_exit.c)
decrements the count. Shadow overlap can overcount, rather than leave a lifetime gap.
The same PID/start tuple must still identify a continuing incarnation; this is the
existing identity model, not a new claim that timestamps are globally unique.
Conforming workers must keep their effective UID and fixed
executable identity. Cooperating launch exclusion must cover the scanned UID sessions
and fork-to-exec/admission interval. Samples do not enforce those preconditions.

The [native lookup path](https://github.com/apple-oss-distributions/xnu/blob/main/bsd/kern/proc_info.c#L2046-L2090)
does not request zombie lookup with the adapter's zero argument. Therefore ESRCH
must not be relabelled “unrelated process” or “recovery complete.” This algorithm
uses subsequent inventory omission rather than ESRCH alone as absence evidence.
Public source is supporting evidence, not exact-build verification of the beta host.

## Validation and next boundary

Coordinator owns helper integration tests, this review, records and Git. Fresh-context
Sol owns context source and its unit tests. Fresh-context Astra independently reviews
the proof and final implementation. The helper integration regression failed before
implementation: a confirmed disappearance still ended at the first identity read.
It enters through the actual ctypes identity/enumeration adapters, capture, helper
subprocess and parent parser. Libproc calls and the other native context reads
(boot, session and path) are mocked.

Full suite: `python3 -B -m unittest discover -s tools/mac-control/Spikes -p 'test_*.py'`
ran **407 tests in 45.719 seconds: 406 passed, one existing skip**. A final candidate
second-scan failure regression was added during that run; afterward the complete current
context suite ran **29 tests in 0.038 seconds, all passed**. That final delta changed
only a comment and a test, not runtime behavior. The probe suite's 19 tests also passed
in independent review. `git diff --check` and observation-caller AST checks passed.
Environment: macOS 27.0 (26A5425a), Python 3.14.7, same M1 Max runtime namespace.
Fresh-context Astra reviewed the source proof, implementation and observation caller
with no blocking finding. Tests use private fixtures and mocked OS boundaries; they
do not establish native recovery.

Inventory observation does not resolve old admitted events or prove recovery,
clipboard cleanup or broader intervention.
Task 1.3 and Gate A remain open; Wave 2 task 2.1 remains blocked.

The [fresh one-shot caller](inventory-contract-observation.py) reuses the reviewed
identity observation implementation and exclusively creates a different journal.
After review it performed one bounded read under the existing marker lock, checking
marker bytes/fingerprints unchanged, with both authority flags false. It cannot
capture/reload witnesses, clear the marker, initialize, activate or send desktop input.

## Native observation

`python3 -B -I verification/mac-control/inventory-contract-observation.py` ran once
outside the sandbox and exited 0. The [three-record journal](inventory-contract-observation-2026-09-10.jsonl)
retains prepared, started and observed records. The observation took **227.361375 ms**
including marker rechecks, returned a complete empty executor inventory, and preserved
marker bytes/fingerprints. Both authority flags remained false. This shows the revised
probe works in this one native observation; the unchanged schema does not say whether
the successful scan actually encountered a disappearing process.

## Fresh prospective capture

Prepared [prospective-acquisition-inventory.py](prospective-acquisition-inventory.py)
with transaction `acquisition-cd911942b7cb40adb20dc1753668b3ae`, a new report and operator
record. Historical callers and all four transactions remain unchanged. Read-only `inspect`
passed: existing private canonical parents, unused destinations and disjointness from
the runtime parent and four configured Syncthing roots. Other sync services are unassessed.
Capture/reload uses the existing reviewed runner, checks and timeout behavior; there is
no marker repair, initialization, activation, reboot, app launch or input in that operation.
The capture must succeed before separate-process reload, and any failure preserves
partial artifacts and ends the sequence without retry. Fresh-context Astra reviewed
the configuration-only delta and cleared the one capture/conditional reload sequence.

## Capture outcome and handoff

`python3 -B verification/mac-control/prospective-acquisition-inventory.py run` ran once
outside the sandbox, exiting 1. The [retained journal](prospective-acquisition-cd911942b7cb40adb20dc1753668b3ae.jsonl)
records capture failure at **observation 3 / final / inventoryAfterFirstScanChanged**.
The middle inventory did not equal the first scan's successful rows. The fixed stage
does not distinguish an added PID, a successfully read PID disappearing, or a
provisionally missing PID remaining listed. No specific cause or process is inferred.
The runner stopped before reload; there was no retry.

Read-only post-failure checks found matching 3,329-byte baseline witness.json/witness.tmp
and a 32,678-byte history archive identical to the source. The archive digest remains
`15b48185b7164aae443d56ab8741453719d0d6cbdfafb64bd00ec0bab9a44076`;
the retained baseline digest is
`1e6a4ac5f207c69b50469514033fb1e23c3d657c08a2c51e880d56c19f4e53a6`.
A separate create=False locked read confirmed the current marker is still unresolved.
These files prove retention, not completion of the failed capture or recovery.

The caller is consumed. Preserve all **five** failed transactions and both native
observation journals. No reboot, initialization, activation, foreground window or
additional capture is arranged. Next review a bounded contract for inventory changes
during observation: this narrower disappearance rule passed one native probe but did
not establish reliable four-observation acquisition. Another blind retry is not the
next action. Task 1.3/Gate A and Wave 2 task 2.1 remain blocked/incomplete.

Independent follow-up recommends reviewing a kernel-backed inventory snapshot adapter
before another native attempt, rather than adding another diagnostic category or
requiring a globally quiet process list. A broader libproc proof could use K persistent
witnesses and a returned count M strictly below K+20, but would couple more behavior to
an internal allocation constant. An alternative is `KERN_PROC_UID`:
[sysctl's output check](https://github.com/apple-oss-distributions/xnu/blob/main/bsd/kern/kern_sysctl.c#L761-L889)
reports ENOMEM on insufficient output space, and
[proc_iterate](https://github.com/apple-oss-distributions/xnu/blob/main/bsd/kern/kern_proc.c#L3827-L3946)
rechecks allocation against the process count under its lock before collecting PIDs.
Neither alternative is approved as a replacement by this review. The next proof must
cover vanished callbacks, SIDL/shadow omissions, PID reuse, UID filtering, executor-name
classification and bounded execution. Simply swapping APIs while retaining global
set equality would reproduce the compatibility obstacle.
