# Native storage validation and original provenance search

September 9, 2026. Native disposable storage passed; the historical preflight lacks original
independently retained report hashes. No marker was opened or modified in this continuation.

## Native storage result

Parsed `/Users/sim/Library/Application Support/Syncthing/config.xml` folder paths only. Neither
proposed parent overlaps any of its four configured synchronization roots. This checks that local
configuration, not every possible sync service or future configuration change. Existing ancestors
are local directory paths without symlink components, on device 16777232.

Both proposed Directions parents were absent. The explicitly scoped native check created four
private directories with mode 700, preserved all existing ancestor modes, and flushed new directories
and their parent names:

- `/Users/sim/Library/Application Support/Directions`
- `/Users/sim/Library/Application Support/Directions/MacControlEvidence`
- `/Users/sim/.config/directions`
- `/Users/sim/.config/directions/mac-control-anchors`

Created matching disposable children named `preflight-47cb6c9f33014610a3529148df308fde` in the two
leaf parents. Ran `recovery_preflight.py storage-provision`, then `storage-reload` in a separate
process, with both explicit paths and the location-review record. Both returned exit 0; root
identities and original slot identities matched. Native file and directory flush calls completed.

[Machine-readable results](storage-location-2026-09-09.json) retain both full reports, paths,
ownership/modes, fingerprints, slot identities, and the synchronization review limitation.
The execution wrapper was `/private/tmp/directions-storage-location-check.py`; the reusable
operations and preparation procedure are in [the preflight runbook](native-preflight.md).

The disposable directories remain for review. They contain no live baseline, seal or activation
authority. No app/helper installation, startup registration, permission change, native app build,
desktop input, reboot, initialization or recovery operation occurred. Successful flush calls and
process reload do not prove power-loss persistence.

## Original hash search result

Before this check, the expected local Directions configuration/evidence directories and
`~/Library/Application Support/com.lucesumbrarum.MacControl` did not exist. Repository acquisition
reports and session logs describe preserving evidence but supply no independent whole-report pins.

Independent review traced the original writer calls in machine-local Codex records:

| Artifact | Original acquisition record | Finding |
|---|---|---|
| `worker-crash-2026-09-09.json` | `~/.codex/sessions/2026/09/09/rollout-2026-09-09T12-47-43-01a085c7-dd22-7f71-8ea8-d514797cad78.jsonl`, line 262; 11:07:22.570 UTC | Exclusive JSON creation; calculated a raw trace hash, but no complete-report pin |
| `native-context-2026-09-09.json` | `~/.codex/sessions/2026/09/09/rollout-2026-09-09T18-04-36-01a086e9-fc0a-7210-b3ae-97588530cf93.jsonl`, lines 361 and 389; 16:19:20.891 and 16:20:58.347 UTC | Created baseline and added metadata; no report hash retained |

The baseline acquisition's recorded hash belongs to the ten-byte `unresolved` marker. The history's
trace hash belongs to its raw journal. Neither authenticates the exact complete report required by
`inspect-legacy`. Filename-bearing tool records from September 9 before 20:00 were checked, excluding
this ongoing session's echoes. This is a bounded search, not proof that no external copy exists anywhere.

No new report hashes were calculated and presented as old pins. No authority was inferred from
the surviving transcript, report contents or newly provisioned directories.

## Next bounded action

The existing historical-preflight route cannot run with the located inputs. Review a fresh
prospective acquisition using the existing `capture_baseline` and durable retention APIs. Specify
how the original caller will preserve its newly acquired baseline and separately record the old
crash report as historical failed/unknown evidence acquired now. Do not label a new history hash
as one retained at the original crash. Resolve that contract before live acquisition.

This should be a concrete acquisition/retention procedure using existing code, not another general
recovery subsystem. Preserve the historical files and unresolved marker. Do not request a reboot
until the prospective evidence and its independent retention are ready. The later-boot namespace
survival and repeatable-startup gaps in the delivery review remain unchanged.

## Validation

Native provision and separate-process reload passed; retained JSON parsed and asserted matching
identities, completed flushes and false launch/recovery flags. `git diff --check` passed.
No source changed, so the prior 352-passed/one-skip suite was not rerun. Task 1.3/Gate A and progress
counts remain unchanged.
