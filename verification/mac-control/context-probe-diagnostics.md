# Context failure diagnostics and fresh native attempt

September 9, 2026. Continued execution after the first acquisition failure. Added safe failure
stages across `recovery_context.py`, the isolated helper in `recovery_probe.py`, and the
`recovery_acquire.py` report. This changes diagnostics only: inventory checks, deadlines,
output limits, teardown and non-authorizing outcomes remain enforced. No retry loop added.

Native exceptions are reduced to fixed stage names. The parent accepts a diagnostic only
from nonzero helper exit with the exact error schema and an allowlisted stage. Unknown,
extra-field, duplicate-field or malformed output cannot become success or leak native error
text. Successful output still passes the unchanged strict context verifier.

## Validation and native diagnosis

New regressions first failed because errors lacked stage attributes. Tests now cover safe
stage propagation, inventory-change rejection without retry, actual helper entry in a
subprocess with the native boundary substituted, malformed diagnostic suppression, timeout,
output-limit and launch stages, and acquisition failure preserving the empty baseline slot.
Independent read-only review found no concrete blocker; its helper-entry and stage-assertion
coverage recommendations were addressed.

- Full suite: 368 tests in 41.876 seconds, **367 passed and one existing sandbox skip**.
- After additional stage assertions and an output-limit test: **14 probe tests passed** in
  0.894 seconds. No implementation changed after the full suite.
- `git diff --check` passed.
- Three fixed native read-only observations under the existing marker lock passed, with
  complete empty inventories and unchanged marker bytes/fingerprints. All samples remain
  individually retained in [diagnostic evidence](context-diagnostics-2026-09-09.json).

Then one fresh acquisition was attempted using newly inspected private roots. It failed
before retaining a baseline, reporting **`failure_stage: inventoryAfterFirstScan`**.
This localizes the new failure to the inventory re-enumeration/validation/equality check
after the first scan. It does not distinguish a query/validation failure from an observed
PID-set change, and cannot retroactively identify the first attempt's hidden cause.

## Preserved transaction

[Exact configuration, argv and failure output](prospective-acquisition-fresh-2026-09-09.json).
Wrapper: `/private/tmp/directions-prospective-acquisition-fresh.py`, run once in `inspect`
mode and then once in `run` mode with outside-sandbox approval. No transaction was reused.

Fresh failed transaction: `acquisition-35953f406b1d4ca991db2a29ac4d0ffe`:

- Evidence/archive parent: `~/Library/Application Support/Directions/MacControlEvidence/acquisition-35953f406b1d4ca991db2a29ac4d0ffe`
- Independent anchor: `~/.config/directions/mac-control-anchors/acquisition-35953f406b1d4ca991db2a29ac4d0ffe`

The archive contains 32,678 bytes; all five witness directories are empty. The independent
anchor manifest/fence exists. Preserve these, the original failed transaction
`acquisition-501142a1d74c47b086c42c75b32b7e9d`, and the earlier disposable storage preflight.
The capture path does not write the marker. No reload followed this failure.

## Current resume

The acquisition procedure's stop-on-failure boundary is active again. No automatic retry,
reboot, initialization, activation, app build/launch, desktop input or commit occurred.
Task 1.3/Gate A remains open and progress stays 2/25. Previous dirty edits were preserved.

Next bounded action: review the inventory-boundary failure in isolation. Distinguish native
enumeration failure from actual process-set churn in safe diagnostics, then assess whether
a quiet observation window can satisfy the existing completeness contract. Do not silently
ignore processes, weaken the two-scan checks, or add retries to get a passing acquisition.
A fresh acquisition/reload must succeed before separately arranging a boot transition.
Model fit: deep capability and high reasoning for the inventory/recovery contract.
