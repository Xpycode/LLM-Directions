# Final-observation diagnostics and acquisition reporting

September 10, 2026 · Wave 1, task 1.3 · selected offline scope complete.

## Review and reproduced failure

The [September 10 failed capture](inventory-boundary-review.md#authorized-native-result--failed-after-baseline-retention)
retained a baseline before one of the final two observations failed at `processIdentity`.
Read-only archive/witness checks confirmed the recorded byte counts, matching history copy,
matching raw baseline digest and equal internal/external provenance. The two retained baseline
samples were 178.690709 ms apart and reported complete empty executor inventories. These checks
do not authenticate the original crash or establish completed acquisition.

Private fixtures reproduced failure at observation three and four. Both preserved witnesses,
left the marker unchanged and produced the same coarse failure report. Evidence-only reload
could succeed afterward with both authority flags false. The exact native cause remains unknown.

The historical temporary wrapper also lost operation diagnostics on `TimeoutExpired`: its
report remained `prepared` because saving followed `subprocess.run`. This was reproduced using
the actual operation loop with a substituted subprocess; no native invocation was performed.

## Bounded implementation

- `recovery_context.py` adds `processIdentityFirstScanRead`,
  `processIdentityFirstScanMalformed`, `processIdentitySecondScanRead` and
  `processIdentitySecondScanMalformed`. `Read` means the process adapter did not return a usable
  row, including a rejected short native return. It does not identify errno or prove a process
  disappeared. `Malformed` means a returned row failed the existing identity checks.
- `recovery_acquire.py` reports `failure_observation` (1–4) and `failure_phase` (`baseline` for
  1–2, `final` for 3–4) when a bounded probe fails. The scan position is supplied by the fixed stage.
  Historical stages remain accepted; no old report is relabeled. No PID, path or raw native error
  enters the new context diagnostics. The helper wire shape and success context remain unchanged.
- `recovery_acquire_run.py` replaces the wrapper's in-place report rewriting with an append-only
  JSON-lines journal. It flushes `started` before launch and `finished` before validation/reload.
  Timeout and launch errors are recorded and stop the operation sequence. Timeout stdout/stderr
  are retained up to 16 KiB each with truncation flags. Capture must report success, unchanged
  marker and false authority flags before reload; digest/metadata equality is required afterward.
  A consumed journal or partial tail cannot be reused. Earlier records survive an interrupted append.
- The [tracked wrapper](prospective-acquisition-wrapper.py) is the revised concrete native caller,
  replacing reliance on a temporary-only script. Its historical transaction/report configuration
  is deliberately retained, so existing paths prevent execution. Before any new native attempt,
  prepare a separate caller copy with fresh transaction and `.jsonl` report names and an updated
  operator record; inspect that exact copy and establish native scope separately. The original
  `/private/tmp/directions-prospective-acquisition-2026-09-10.py` is historical and superseded.
- The README now labels the worker-crash preparation paragraph as historical.

All strict identity, inventory, marker, retention, equality and deadline checks remain. No filter
exclusion, retry, marker repair, initialization or activation was added. Retention order is unchanged.

## Validation and ownership

- Initial review baseline: 371 tests, 370 passed/one existing sandbox skip in 44.453 seconds.
- Sol owned context diagnostics and context/probe tests in a fresh context: 37 focused tests
  passed in 1.624 seconds. Native calls were substituted while retaining the inherited process
  adapter, actual capture/helper entry, subprocess transport and strict parent parser.
- Coordinator owned acquisition observation reporting/regressions, journal runner/tests,
  wrapper, README, integration, project records and Git. Initial acquisition/runner focused suite:
  22 passed in 1.527 seconds. A further real subprocess capture-to-journal integration test then
  covered both final failures with fixture observations and no native state.
- Final full suite: `python3 -B -m unittest discover -s tools/mac-control/Spikes -p 'test_*.py'`:
  **387 tests in 46.041 seconds; 386 passed, one existing sandbox skip.**
- Tests cover real synthetic-child timeout/reaping, partial output, launch/nonzero failure,
  invalid capture reports, reload mismatch, interrupted appends, failed flushes and replay
  rejection. Late capture failures retain witnesses and survive a separate-process evidence-only
  reload without authority. Exact native caller syntax checked without importing or executing it.
- Fresh-context Astra independent review found no blocking correctness, safety or coverage issue.
  `git diff --check` passed. No Swift compilation or actual native acquisition was performed.

## Remaining boundary and next pickup

Task 1.3 and Gate A remain open. Preserve all three failed transactions and the unresolved runtime
marker. No new diagnostic observation, acquisition/reload, reboot, marker mutation, native build,
app launch or desktop input occurred in this continuation. The review does not grant those actions.

Next: prepare and review one fresh caller configuration using the tracked wrapper and the improved
diagnostics before a separately scoped native attempt. Stop and retain its result on any failure.
The underlying native cause remains unknown; success still needs four complete observations, eight
process scans and twelve PID enumerations. Repeated attempts are not a reliability measurement.

Known limits: subprocess output is buffered before retention truncation; its timeout does not bound
process creation or filesystem flushing. Journal exclusivity relies on the trusted wrapper, not a
new runner lock. Interrupted final writes can leave an incomplete tail; retain it as unresolved.
Native power-loss durability is unverified. The later-boot/original-temporary-namespace condition,
one-shot activation/repeat-run gap, recovery, clipboard and other intervention cases remain pending.
