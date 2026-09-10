# Fresh acquisition caller preparation

September 10, 2026 · Wave 1 / task 1.3 · native run pending.

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

Task 1.3 and Gate A remain open. Next is this exact capture/reload operation within
separately agreed native scope. Preserved historical artifacts do not prove recovery;
later-boot continuity, recovery, clipboard and remaining intervention checks still apply.
