# Initialization completion seal and activation preflight

September 9, 2026 · isolated offline implementation of the
[reviewed preparation contract](legacy-activation-preparation.md).
Validation host: arm64, macOS 27.0 (26A5425a), Python 3.14.7.

`recovery_seal.py` now retains completion evidence during fresh fenced initialization and checks
that evidence later without changing the runtime. `activationCandidate` always has
`launch_eligible: false` and `native_recovery_verified: false`. The existing launcher is unchanged:
every bootstrap artifact still blocks startup. No live runtime files were accessed or new native
baseline acquired; existing suite parser tests read retained repository evidence only.

## Acquisition and retention

`initialize_sealed` requires an already held `MarkerLock`, a trusted baseline/history and an explicit
existing empty private seal directory disjoint from the marker directory. It calls the real v2
initializer itself under uninterrupted ownership. It cannot accept a previous initialization result
or retrospectively seal existing artifacts. Errors preserve evidence and fences; there is no cleanup,
retry, activation or input API.

After initialization's final flushes and rechecks, it snapshots the exact pending/committed bytes,
digests and fingerprints, post-clean marker fingerprint, namespace identity/metadata and topology.
The seal binds these to a new transaction ID and acquisition provenance. Baseline/history pins and
initialization context are retained through the exact original audit bytes. Generated seals/audits
are canonical JSON; externally pinned baseline/history retain their original formatting and bytes.

The seal is written exclusively to `seal.tmp`, fully flushed, then published exclusively as
`seal.json` by hard link. After directory flush, both names, bytes, link count, external directory
identity/metadata and the entire marker snapshot are rechecked. Only then does the call return a
`TrustedSeal` containing the acquired bytes, digest and provenance. The caller must independently
retain that acquired pin/provenance. Loading a surviving file and hashing it does not recover a
missing completion acknowledgement. Acquisition provenance must match the embedded seal label;
that equality is a consistency check, not authentication. The external pin remains a trusted input.

The source does not install a native pin store. Durable retention of the returned pin, already
durably established external directory/ancestors, and validated native flush behavior remain live
integration requirements. Process-death tests do not prove power-loss persistence.

## Read-only preflight

`load_seal` checks the caller's independent pin, provenance, exact schema/types, bounded canonical
encoding, fields, fingerprints and artifact digests. `preflight` revalidates those checks even for
a manually constructed object, then verifies the complete audit against the separately pinned
baseline/history. Unknown/v1 audits, numeric substitutes for booleans, extra/missing fields,
duplicate keys and inconsistent pending/committed evidence cannot produce a candidate.

The caller selects the namespace and holds its original lock; no path from the report is opened.
Snapshots require exactly the marker and three initialization names, private owned regular files,
one pending link, and exactly two committed names for one inode. Evidence/marker inodes are distinct.
They compare exact bytes, path/descriptor identities and fingerprints to the sealed snapshot.

Fresh injected context samples must report complete empty executor inventory and the initialization
boot/session, different from the old baseline boot. Samples are locally bracketed within the two-second
window and cannot predate initialization on that same boot. No cross-boot timestamp comparison occurs.
Exact snapshot checks bracket observations and follow the final clock callback. Independent review
reproduced a mutation at that final callback escaping an identity-only check; the exact final check
and regression close that gap. No failure repairs or rewrites evidence.

Fingerprints detect observable metadata changes under trusted ownership. They do not prove arbitrary
write history on every filesystem; native timestamp resolution and filesystem behavior remain to be
validated. The observer/clock and in-process caller are trusted dependencies, not hostile-code boundaries.
The bounded native context adapter exists separately; this module has no native default or CLI.

## Verification

- Behavioral fixtures cover successful read-only preflight, later lock reacquisition, exact opaque
  evidence, incorrect pins/provenance, malformed audits/seals, context drift/staleness, incomplete
  inventory, marker/namespace replacement, altered files/modes/link topology and final-callback mutation.
- Storage tests exercise zero/short writes, file and directory flush failure, changed external
  namespace, deletion, corruption and extra hard links. Exceptions retain marker ownership and fences.
- Seventeen actual subprocess cases cover death at all eleven initialization and five seal boundaries,
  plus success. No interrupted child returns a pin, including after publication. Every case enters
  the actual `experiment_lock` launcher and is rejected without changing retained marker/audit bytes.

The initial behavioral run caught two provenance failures; those were fixed. Independent final review
found no remaining blocker within this isolated, fenced scope. Final full suite: **293 tests in
33.947 seconds — 292 passed, one existing sandbox boot-query skip**. Whitespace checks passed.
Commands:

```bash
python3 -B -m unittest discover -s tools/mac-control/Spikes -p 'test_*.py'
git diff --check
```

## Next boundary

The [activation/one-shot admission implementation](legacy-activation.md) now covers allowed namespace
transitions, explicit interrupted-publication reconciliation and actual-launcher/process-death tests.
Prepare native caller/pin retention next. A completion candidate alone cannot bypass the launch
fence; explicit independently retained activation evidence is required. No native bootstrap, recovery pass, foreground window,
build, installation or deployment occurred. Task 1.3/Gate A and all tracked task counts stay open.
