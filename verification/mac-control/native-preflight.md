# Runnable native recovery preflight

September 9, 2026. `tools/mac-control/Spikes/recovery_preflight.py` provides three explicit
operations: `storage-provision`, `storage-reload`, and `inspect-legacy`. It reuses the existing
provisioner, locked baseline checks and bounded native probe. It has no initialize, activate,
clear, retry, reboot or launch operation.

**Latest native continuation:** [storage validation and provenance search](storage-and-provenance-review.md)
passed disposable provision/reload at the proposed parents. Original acquisition records do not
contain whole-report pins; the historical inspection below remains blocked on trusted inputs.
Review prospective acquisition/retention next; do not synthesize historical pins.

## Storage-location procedure

The proposed parent locations remain:

- Evidence: `~/Library/Application Support/Directions/MacControlEvidence/`.
- Independently configured anchor: `~/.config/directions/mac-control-anchors/`.

Before using these paths, inspect the actual machine's synchronization configuration and establish
that both are local, persistent and excluded. Check their canonical paths, ownership and mode 700.
Their ancestors must exist without symlink components. Missing parents need an explicit local setup
action; the CLI does not create or change them. Record who checked the policy and which configuration
was inspected. `--location-review` records that assertion; it never makes software verification of
Syncthing, retention or power-loss durability claims.

After that location review, the following uses fresh disposable children only. Run from the repository
root, with reviewed parent directories already present. Do not reuse a transaction name after failure.
These commands are prepared for the separately scoped native location check; they were not executed
against the proposed persistent parents during this implementation.

```bash
mac_preflight_txn="preflight-$(uuidgen)"
mac_evidence_parent="$HOME/Library/Application Support/Directions/MacControlEvidence"
mac_anchor_parent="$HOME/.config/directions/mac-control-anchors"
mac_evidence_dir="$mac_evidence_parent/$mac_preflight_txn"
mac_anchor_dir="$mac_anchor_parent/$mac_preflight_txn"
mkdir -m 700 "$mac_evidence_dir" "$mac_anchor_dir"
```

Stop if directory creation fails. Supply the actual location-review record as the final argument:

```bash
python3 -B tools/mac-control/Spikes/recovery_preflight.py storage-provision \
  --evidence-directory "$mac_evidence_dir" --anchor-directory "$mac_anchor_dir" \
  --location-review "$mac_location_review"
```

Only after exit 0 and `disposableStorageProvisioned`, run the separate process:

```bash
python3 -B tools/mac-control/Spikes/recovery_preflight.py storage-reload \
  --evidence-directory "$mac_evidence_dir" --anchor-directory "$mac_anchor_dir" \
  --location-review "$mac_location_review"
```

Retain both JSON outputs outside the two transaction roots. Compare `slots` and root identities;
the expected result is `disposableStorageReloaded` with identical original slot identities.
Both operations flush files/directories. Neither is read-only. Reports include canonical configured
paths, root fingerprints (device/inode, mode, UID/GID, links, size, mtime/ctime), validated ownership/
mode, slot identities and successful flush-call status. They do not prove persistence across power
loss. A nonzero exit ends the action; retain partial roots and output for review. Do not repair,
overwrite, transplant, activate from, or install these disposable slots.

## Historical inspection procedure

Required caller inputs, obtained independently of the JSON reports being loaded:

- Explicit original marker namespace from the original acquisition configuration.
- Exact original baseline/history files, their separately retained SHA-256 pins, and acquisition
  provenance covering both pins. No pin may be calculated from the current report to fill a gap.

The repository contains the historical baseline and crash report, but this continuation did not
establish an independent surviving pin store. The command is ready; those trusted inputs and the
deployment-location review remain prerequisites for a live handoff. If original pins are unavailable,
report that failure and review a prospective baseline acquisition/design separately. Do not invent
provenance or ask for a reboot to compensate for missing trust inputs.

After the caller has supplied these values, the exact invocation is:

```bash
python3 -B tools/mac-control/Spikes/recovery_preflight.py inspect-legacy \
  --marker-directory "$mac_original_marker_dir" \
  --baseline "$mac_original_baseline_file" --baseline-sha256 "$mac_retained_baseline_pin" \
  --history "$mac_original_history_file" --history-sha256 "$mac_retained_history_pin" \
  --provenance "$mac_original_acquisition_record"
```

The command authenticates input bytes before opening the existing marker with `create=False`.
Under the lock it compares the original fingerprints, gathers two bounded native context samples
with complete empty inventory, and requires a boot different from the baseline. It rechecks marker
bytes/metadata before releasing ownership. The report contains observations, never activation
authority, and a later initialization must repeat its own checks.

| Outcome | Meaning and next action |
|---|---|
| Exit 0, `legacyPreflightObserved` | Later-boot observation with unchanged legacy namespace; retain proof for separate initialization review |
| `sameBoot` | Required boot transition has not been proved; arrange it only after trust inputs and procedure are ready |
| Missing/replaced namespace or `baselineContinuityLost` | Current legacy path cannot proceed; preserve evidence and review a separate design |
| Missing provenance, wrong pin or malformed baseline | No trusted input chain; supply original acquisition evidence, never recompute authority |
| Busy marker, incomplete inventory, timeout or other nonzero result | Inspection unresolved; no mutation/retry follows automatically |

The required reboot may remove the temporary namespace. This procedure deliberately cannot recreate
it. Even a later successful initialization/activation allows only one admission; repeatable normal
startup remains a separate recovery requirement. Neither this report nor disposable storage success
closes Gate A. Native checkpoint compilation and foreground experiments still require an agreed window.

## Validation

Focused CLI tests first failed because the entry point did not exist, then passed. Thirteen tests
cover actual command parsing, real subprocess provisioning/reload, replay and missing-slot rejection,
partial storage/flush failure, symlink rejection, absent location review, malformed pinned evidence,
wrong pin before runtime access, missing/replaced/busy marker, same boot, stale/unavailable inventory,
intervening marker mutation and successful non-authorizing inspection. Native clock/context are
substituted in inspection tests; no live marker or GUI app is accessed.

Independent review reproduced a malformed pinned baseline escaping the JSON error report; the
entry point now reports that failure and has a regression. Review also requested root metadata in
storage output; the report now includes it. The command deliberately does not read witness contents:
these are disposable empty-slot checks. Live witnesses remain handled by `recovery_retention` under
the separate caller contract.

Final focused suite: **13 passed in 0.443 seconds**. Full suite: **353 tests in 42.401 seconds,
352 passed and one existing sandbox boot-query skip**. Independent final review found no remaining
blockers within the private-fixture scope. No native marker inspection, persistent deployment,
Swift build, app launch, desktop input, reboot, initialization or activation occurred.

```bash
python3 -B -m unittest discover -s tools/mac-control/Spikes -p test_recovery_preflight.py
python3 -B -m unittest discover -s tools/mac-control/Spikes -p 'test_*.py'
git diff --check
```
