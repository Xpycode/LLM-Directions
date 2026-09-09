# Fresh prospective acquisition and retained historical copy

September 9, 2026. `recovery_acquire.py` is a bounded capture/reload caller using the existing
provisioner, baseline capture, witness retention and flush APIs. No generic storage schema or
retention kind changes are needed. Native acquisition has not been run.

**Subsequent native attempt:** [capture failed before baseline retention](prospective-acquisition-live.md).
Partial transaction preserved; no reload or retry. Follow that checkpoint before another acquisition.

## Evidence contract

The new baseline records a fresh observation of the unresolved marker, boot, login session,
complete empty executor inventory and exact namespace fingerprints. The original acquisition
writer hashes those newly returned baseline bytes and immediately retains them in a newly
provisioned, independently configured baseline slot.

Its authenticated provenance string is canonical `prospectiveAcquisition/v1` JSON containing:
acquisition ID, archived history SHA-256 and byte count, operator acquisition record,
`historicalCopyAcquiredNow`, and `failedOrUnknownNonRetryable`. The history hash is explicitly
acquired now; it is never described as retained at the original crash. History is opaque archival
context, not a dispatch ledger, verified old boot or proof of the original report's authenticity.

The source is read once through a bounded no-symlink path walk with stable file/path checks.
Exact bytes are exclusively archived in a separate private directory. The file, archive directory
and its parent are flushed. The live marker is held with `create=False` throughout archive/capture/
retention; final checks require unchanged marker fingerprints, bytes and stable observed boot/session.
No clean write or input is possible through this entry point.

The baseline and archive are bound by the history digest inside the authenticated baseline.
On restart, load original slot identities from explicit independent anchor configuration, reload
the retained baseline, require exact equality of its internal and external provenance strings,
strictly parse the binding, and verify the explicitly supplied archive against that digest.
Neither an archive filename nor a hash printed in a diagnostic report establishes trust.

## Prepared native procedure

Use fresh transaction roots at the already validated local parents; do not use the disposable
`preflight-47cb6c9f33014610a3529148df308fde` slots. Select three explicit canonical private empty
roots: evidence slots, independent anchor, and a separate history archive. They must be disjoint
from each other and the original runtime namespace. Existing parents and newly created directory
names must be private where required and durably established as in the storage-location procedure.

Proposed layout, with one fresh `acquisition-<UUID>` chosen by the caller:

- Evidence: `~/Library/Application Support/Directions/MacControlEvidence/acquisition-<UUID>/slots`
- Archive: `~/Library/Application Support/Directions/MacControlEvidence/acquisition-<UUID>/archive`
- Anchor: `~/.config/directions/mac-control-anchors/acquisition-<UUID>`

Prepare and inspect those roots before the separately scoped native capture. The capture command
itself provisions the empty evidence and anchor roots; do not run storage-provision first.
Supply the original explicit marker namespace from acquisition configuration, the historical source
path, and an operator record explaining this is a new prospective acquisition after original pins
were not found. The selected roots are trusted caller configuration, never discovered from reports.

```bash
python3 -B tools/mac-control/Spikes/recovery_acquire.py capture \
  --marker-directory "$mac_original_marker_dir" \
  --history-source "$mac_history_source" \
  --evidence-directory "$mac_acquisition_slots" \
  --anchor-directory "$mac_acquisition_anchor" \
  --archive-directory "$mac_acquisition_archive" \
  --operator-record "$mac_acquisition_record"
```

Exit 0 and `prospectiveBaselineRetained` mean only the fresh acquisition and retention checks
completed with an unchanged marker. On failure retain all artifacts and stop; the same transaction
cannot be retried, repaired or overwritten. No reboot is part of this command.

Then a separate process can reload the exact acquired evidence:

```bash
python3 -B tools/mac-control/Spikes/recovery_acquire.py reload \
  --evidence-directory "$mac_acquisition_slots" \
  --anchor-directory "$mac_acquisition_anchor" \
  --archive-directory "$mac_acquisition_archive"
```

Reload flushes retained witness/configuration files through existing APIs and checks the archived
bytes. It does not access the runtime marker. `acquiredEvidenceReloaded` cannot prove a previous
capture caller completed: valid published evidence may survive its later failure. Both operations
always return false launch-eligibility and native-recovery flags.

Only after native capture and fresh-process reload succeed should a separately agreed boot
transition be considered. Later preflight still requires a different observed boot and unchanged
original namespace fingerprints. Same boot, missing/replaced temporary namespace or changed
marker stays blocked. Initialization/activation and a foreground experiment remain separate actions.

## Private verification

Tests enter the CLI parser with native clock/context substituted. They cover exact archived bytes,
unchanged marker, real fresh-process reload, replay rejection, archive corruption, replaced baseline
slot, source ancestor symlink/FIFO, overlapping namespaces, nonempty archive, archive flush failure,
marker change during retention, provenance mismatch and later-boot preflight integration.
The latter rejects same-boot and changed-namespace cases. No live marker or desktop input is used.

Independent design review required parent-name flushing, strict internal/external provenance
equality, non-authorizing interrupted acquisition behavior and full source path checks; these are
implemented. Native observation and power-loss durability remain unverified.

Final targeted suite: **9 passed in 0.525 seconds**. Full suite: **362 tests in 41.101 seconds,
361 passed and one existing sandbox boot-query skip**. Independent implementation review found
no concrete blocker; whitespace checks passed. No native acquisition, deployment or marker access
occurred. Task 1.3 and Gate A remain open.

```bash
python3 -B -m unittest discover -s tools/mac-control/Spikes -p test_recovery_acquire.py
python3 -B -m unittest discover -s tools/mac-control/Spikes -p 'test_*.py'
git diff --check
```
