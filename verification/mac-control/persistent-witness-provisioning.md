# Persistent witness provisioning and restart identity

September 9, 2026 · isolated native-filesystem and Python process tests.

`recovery_provision.py` creates five private evidence slots once and durably retains their original
device/inode identities in a separate explicitly configured local anchor. A fresh process can reload
those identities and pass the resulting `WitnessSlot` values into the existing native caller.
The original runtime marker is never opened by this module.

## Root of trust

The independently configured anchor directory is the trust root. Its path is selected by the
installer/trusted caller, outside evidence, runtime, seal, temporary and synchronized directories.
It is not read from a report or discovered by scanning for a plausible manifest. The evidence root
is also supplied explicitly at restart; a manifest cannot redirect the loader to another location.
Both roots must already exist with mode 700, owned by the current UID, and cannot overlap. All path
components are opened without following symlinks. Provisioning requires both roots to be empty.

This closes the previous in-memory identity dependency by retaining the original identities in an
independent configuration namespace. It does not claim a self-reported hash authenticates arbitrary
JSON. The original writer and installer-selected configuration remain trusted under the existing
cooperating same-UID model. Hostile same-UID modification, forged configuration and inode reuse
after deletion remain outside that model. There is no automatic relocation or recovery of a missing
anchor. Copying a manifest into a replacement root fails its recorded root identity check.

## Provisioning and interruption

The fixed slots are `baseline`, `seal`, `transition`, `activation` and `reconciliation`. No dynamic
slot names or overwrite operation are accepted. Historical bytes remain separately pinned inputs;
the provisioner neither imports historical reports nor assigns them authority.

Provisioning flushes the existing roots' parent directories, exclusively creates and fully flushes
permanent `anchor.fence`, and flushes the anchor directory before creating any slot. Each new private
slot is flushed, then the evidence root naming all five slots is flushed. The manifest binds the
configured paths, original root identities, original slot identities and a fresh transaction ID.
It is fully written/flushed as `anchor.tmp`, published exclusively as hard-linked `anchor.json`, and
followed by directory flush and final exact byte, topology, path and metadata checks.

An incomplete attempt retains all artifacts. A second provision call rejects; the module never
repairs, overwrites or removes partial evidence. Death before manifest publication cannot return
authenticated slots on reload. Once complete publication survives, explicit reload can validate and
flush the manifest, fence, slots, roots and their parent names anew. That establishes durability now;
it does not assert that the interrupted provision call completed.

Reload checks exact fixed names, private owned files, two-link manifest topology, original root and
slot identities, and continuity across flushes. Slot contents may have grown through normal witness
retention; their original directory identities remain pinned. `recovery_retention.load` separately
validates witness contents before use. Corrupt, missing or replaced slots are not recreated. A
reloaded slot is storage configuration, not an activation acknowledgement or a foreground grant.

## Integration and next native boundary

The supported API takes explicit configured roots:

```python
# One original, explicitly requested provisioning action; both roots already exist.
slots = recovery_provision.provision(evidence_root, trusted_anchor_directory=configured_anchor)

# Explicit restart path, using the same trusted configuration; no in-memory inode pins needed.
slots = recovery_provision.load(evidence_root, trusted_anchor_directory=configured_anchor)
# Pass slots["transition"] and slots["activation"] to activate_retained only in the
# separately authorized native activation action. Retain/reload other witnesses separately.
```

Next prepare a deployment-location validation action using disposable evidence only, before live
initialization. Suggested machine-local layout to make that action concrete:

- Evidence parent: `~/Library/Application Support/Directions/MacControlEvidence/`.
- Independent configured anchor parent: `~/.config/directions/mac-control-anchors/`.
- Use one fresh, matching transaction subdirectory in each parent, with the exact canonical paths
  supplied explicitly. Establish private durable parents before calling the provisioner. Exclude
  both from synchronization. Do not reuse a previous transaction's names after failure.

These are proposed deployment locations, not created or installed paths. The API intentionally
supports temporary fixtures for testing; it cannot infer a directory's actual synchronization or
retention policy. Deployment must validate those properties and native flush/metadata behavior at
the selected location. A boot transition, original-namespace read-only preflight, live bootstrap and
new foreground recovery case remain separate steps in the [native handoff](native-caller-retention.md).

## Verification

Ten behavioral tests pass, including nine actual subprocess-death boundaries, a fresh-process reload
with no in-memory identity pins, replacement during publication/reload, corruption and missing slots,
every provisioner directory-flush failure, and reload file/directory-flush failure. The integration
test passes restored slots through the actual native caller, activation, retention and one-shot
admission gate; only native context/clock and the downstream foreground experiment are absent.
An independent review found no blocking defect within the stated trust model. Its additional root
replacement probes rejected; the requested replacement and provisioning-flush regressions were added.

The test module initially failed because the implementation was absent. Targeted suite after
implementation and review: **10 passed in 1.616 seconds**. Final full suite: **340 tests, 339 passed,
one existing sandbox boot-query skip, in 41.990 seconds**. Whitespace checks passed. No persistent
installation, live marker access, Swift build, boot transition or desktop
input occurred. Local flush calls do not establish power-loss durability. Task 1.3/Gate A stays open.

```bash
python3 -B -m unittest discover -s tools/mac-control/Spikes -p test_recovery_provision.py
python3 -B -m unittest discover -s tools/mac-control/Spikes -p 'test_*.py'
git diff --check
```
