# Fresh acquisition caller preparation

September 10, 2026 · Wave 1 / task 1.3 · authorized native capture failed; no reload.

Prepared [prospective-acquisition-next.py](prospective-acquisition-next.py) from the
historical tracked wrapper. Only the module description, transaction ID, report name
and operator record changed. The historical caller and all three failed transactions
remain untouched. Production source is unchanged.

## Concrete proposed operation

Transaction: `acquisition-586afa02a34e4ea9b0ff8290f847bd4d`.
Report: `verification/mac-control/prospective-acquisition-586afa02a34e4ea9b0ff8290f847bd4d.jsonl`.
Evidence/archive use that transaction under the existing private MacControlEvidence
parent; the independent anchor uses the same transaction under mac-control-anchors.
The exact absolute paths are fixed in the caller, including the original runtime namespace.

After separately agreed native scope, repeat the read-only inspection and run once:

```bash
python3 -B verification/mac-control/prospective-acquisition-next.py inspect
python3 -B verification/mac-control/prospective-acquisition-next.py run
```

`run` creates only the fresh private transaction directories and append-only report,
archives the historical failed/unknown report, observes and retains a new prospective
baseline while holding the existing marker lock, and conditionally reloads it in a
separate process. Capture must pass all checks before reload. Each subprocess has a
45-second timeout; process creation and filesystem flushes are not thereby bounded.
Any failure stops the sequence and retains partial artifacts; no automatic retry.
No marker repair, initialization, activation, reboot, app launch or desktop input is
included. Neither success flag grants launch authority or verifies native recovery.

## Validation

- Python AST syntax check passed without importing the caller.
- `python3 -B verification/mac-control/prospective-acquisition-next.py inspect` passed:
  canonical private existing parents and marker directory, unused destination paths,
  separation from the runtime parent and all four configured Syncthing folders.
  This mode performs filesystem/configuration inspection only, with no native context
  observation, marker-content read or transaction/report creation. Other sync services
  were not assessed. Location facts are point-in-time and rechecked by `run`.
- `python3 -B -m unittest discover -s tools/mac-control/Spikes -p 'test_recovery_acquire*.py'`:
  23 tests passed in 1.724 seconds. Tests use private fixtures, not native acquisition.
- Fresh-context Astra independent review found no blocking issue. It confirmed the
  four configuration-only changes, failure preservation, provenance and unchanged
  capture/reload checks. Use ordinary nonoptimized Python: existing preflight checks
  use assertions. Existing timeout, flush, journal-lock and durability limits remain.

Coordinator owns preparation, validation, records and Git; independent reviewer owns
read-only fault finding. Configuration preparation is serial because there is one
caller; review runs independently alongside coordinator validation.

Task 1.3 and Gate A remain open. The configuration is now consumed; do not rerun it.
Preserved historical artifacts do not prove recovery;
later-boot continuity, recovery, clipboard and remaining intervention checks still apply.

## Authorized native outcome

The user explicitly authorized the proposed run. Repeated `inspect` passed, then
`python3 -B verification/mac-control/prospective-acquisition-next.py run` ran once
outside the shell sandbox with approved access to the private storage parents.
Capture exited 1 in 0.616 seconds total wrapper time; no reload or retry followed.

The [append-only journal](prospective-acquisition-586afa02a34e4ea9b0ff8290f847bd4d.jsonl)
contains prepared, capture-started and capture-finished records. Child output reports
`ProbeFailure`, observation **3**, phase **final**, stage
`processIdentityFirstScanRead`; result unresolved and both authority flags false.
No stderr or truncation was reported. The process adapter did not return a usable row;
this does not prove a disappearing process or identify the native error.

Read-only retained-file checks found a 32,678-byte history archive and matching
3,254-byte baseline witness.json/witness.tmp, plus retained anchor files. Baseline
SHA-256: `a27938a084a06ab0e0649b826b48343d56f77072ef1d99b4beeccbfd820cd57a`.
Archive SHA-256: `15b48185b7164aae443d56ab8741453719d0d6cbdfafb64bd00ec0bab9a44076`.
These files show retention, not successful final continuity or recovery. No independent
post-failure marker-content verification was performed. All four failed transactions
remain preserved. No native build, app launch, input, marker repair or reboot occurred.

Next: review the native process-identity adapter's rejected read/short-return handling
offline using this exact stage evidence. No additional native attempt is arranged.
