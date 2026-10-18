# Local runner validation — October 16, 2026

**Selected local scope complete; E1 remains open.** No model pilot, provider request, live
deployment, consumer migration, desktop control or push occurred. Independent fresh-context
implementation owners handled runner and preparation; the coordinator integrated them and a
separate reviewer checked confinement, evidence integrity and failure handling.

## Evidence

- 19 runner tests pass: executed SHA-256, missing-file errors, discovery and UTF-8 accounting,
  exact response boundaries, oversized response withholding, parallel requested/dispatched counts,
  serial 56-call batch, forbidden tools, path/link escapes, root initialization failure,
  host failure, incomplete protocol, blocked-pipe timeout, TERM grace and KILL/reaping.
- Nine preparation tests pass: pinned archive/hash/CRC, all 91 historical source and 91 rendered
  files, original S17 evidence/request, S19 seven originals/copies and two false recorded hashes,
  exclusive output, exact rendering/sizes and manifest alteration/missing/link rejection.
- Three integration regressions pass: symlink aliases into the freeze and live-master output are
  rejected before writes; a copied frozen runner executes without writing bytecode into its inputs,
  even when the caller normally permits bytecode.
- The 28-test run passed; affected preparation tests and the three added integration regressions
  passed after final integration corrections. No unrelated application suite was run.
- Actual frozen-runner replay: S19 16 calls / 4,510 bytes; S17 4 / 1,335; routing 4 / 12,573.
  Total 24 / 18,418. All three owned fake processes exited zero. Fourteen tool checksum receipts
  match independent computation from actual file bytes; all seven original/copy pairs match.
  Full inventory and manifest identity match before/after.

These fake-host results establish local enforcement and tool behavior. They do not score model
answers, adherence, runtime efficiency or the manual rules in `scoring.json`.

Independent review found and resolved blocking response writes, premature delivery audit,
mixed final/call messages, limit validation, master ancestor access, linked inventory entries,
output aliases, disposable entry rendering, manifest identity checks and frozen-import bytecode.
No blocking defect remained within the reviewed local scope. The runner retains this machine's
absolute master denial path when copied; it is not a portable installation design.

## Exact configured bytes

UTF-8 file bytes, excluding hidden host context, wire envelopes and provider settings. Fixture
metadata and evidence are separate; S17's nine original fixture files and original request remain
byte-identical. S19 explicitly narrows coverage to seven original/copy pairs plus historical inventory.

| Session | Entries | Prompt | Fixture metadata | Fixture evidence | Physically present files | Body-readable files |
|---|---:|---:|---:|---:|---:|---:|
| S19 | 11,325 | 597 | 1,181 | 3,278 | 1,001,803 | 1,001,803 |
| S17 | 11,325 | 308 | 2,692 | 1,254 | 1,001,001 | 1,001,001 |
| routing | 11,337 | 354 | 298 | 0 | 993,338 | 24,309 |

The complete master is physically present for routing; the broker permits body reads only from
its entry/fixture allowlist. File-byte inventory is distinct from measured response bytes and the
maximum response budget. Entries differ from the earlier checkout-render totals because these
paths are longer. All per-file sizes/hashes are in the frozen `manifest.json` and `sizes.json`.

## Retained artifacts and reproduction

Source/tools/report folder for Finder Go to Folder:
`/Users/sim/ProgrammingProjects/0-DIRECTIONS/__DIRECTIONS/verification/lean/pilot`
Open `README.md` or `validation-receipts.json` there. The receipt records all current tool hashes,
configured sizes, real fake-host exits/timing, historical preservation checks and archive identity.

Final frozen folder:
`/private/tmp/directions-pilot-local-2026-10-16-hl50v46l/frozen-v3`

Raw local validation folder:
`/private/tmp/directions-pilot-local-2026-10-16-hl50v46l/validation-v3`

Machine-local ignored archive folder:
`/Users/sim/ProgrammingProjects/0-DIRECTIONS/__DIRECTIONS/.archive/pilot-local-2026-10-16`
Open `frozen-v3-and-local-validation.zip` there. ZIP CRC passes; SHA-256 is
`e5c1746c9cc6fa96bc6522f6bc806ac0f4855894c08ed1f2f0ecfaa9ca623ba8`.
Temporary paths and ignored archives are not cross-Mac availability guarantees. Earlier local
snapshots remain retained: v1 was unlaunched; v2's local smoke was superseded to distinguish
physical inventory from body-readable byte totals explicitly. No historical replay was overwritten.

The commands used were:

```bash
python3 -B -m unittest discover -s /Users/sim/ProgrammingProjects/0-DIRECTIONS/__DIRECTIONS/verification/lean/pilot -p 'test_*.py' -v
python3 -B /Users/sim/ProgrammingProjects/0-DIRECTIONS/__DIRECTIONS/verification/lean/pilot/prepare.py --output /private/tmp/directions-pilot-local-2026-10-16-hl50v46l/frozen-v3
python3 /Users/sim/ProgrammingProjects/0-DIRECTIONS/__DIRECTIONS/verification/lean/pilot/validate.py --frozen /private/tmp/directions-pilot-local-2026-10-16-hl50v46l/frozen-v3 --output /private/tmp/directions-pilot-local-2026-10-16-hl50v46l/validation-v3
```

The test command also ran focused preparation/integration patterns as described above. Preparation
and validation refuse existing output directories; a reproduction needs fresh absolute output paths.
Archive-dependent tests explicitly skip when the pinned historical archive is unavailable.

## Remaining gates

The [October 17 actual-CLI probe](transport-validation.md) found a tool-surface/configuration
blocker. It does not close any live-provider or adapter acceptance gate.

The [supported broker-only policy](host-policy.md) now defines exact registry/schema and dispatch
requirements. The diagnostic enforces its advertisement subset; no live host is admitted and the
remaining gates below are unchanged.

**October 17 user direction: live transport validation before any pilot.** Keep this gate open
until the actual adapter has retained passing evidence for every item below. Protocol/schema
inspection and inert-host replay are preparation, not live-transport acceptance. Passing this
gate permits a pilot proposal; it does not authorize a pilot or provider/model requests.

- Actual host discovery and response envelopes enter the broker's call/UTF-8 byte accounting,
  including errors, repeated reads and separately counted parallel invocations.
- Native shell, write, app, web and delegation paths are disabled in the actual host; the confined
  broker is the only tool execution path. A prompt asking the model to avoid tools is insufficient.
- Cap, timeout, disconnect and provider failures stop the batch without retry/fallback, retain
  partial evidence and verify owned-process teardown.
- Exact executable/version and effective model/effort/settings are recorded; any mismatch with
  the reviewed proposal is disclosed before launch.
- Actual launch verifies the frozen input/tool/schema/scoring manifest and rejects tampering
  before any provider request. Historical manifests and evidence remain unchanged.

There is no live Codex adapter. Actual host discovery/envelope accounting, disablement of native
tools, provider failure mapping, settings/version checks and manifest enforcement at actual launch
must be integrated and checked before requesting a pilot. The inert transport cannot establish
those properties. The proposed three-session budget remains unchanged, with no retries or fallback.
The 1,200-token final-output target is not a token or subscription-cost cap.

Corrected host behavior, historical consumer/routing findings, full migration/idempotence, thirty
deferred Claude observations and entry/runtime byte tradeoffs remain unverified or unresolved.
No pilot is authorized or scheduled, and no rollout recommendation follows.
