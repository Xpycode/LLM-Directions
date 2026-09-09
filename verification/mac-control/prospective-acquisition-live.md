# Native prospective acquisition — failed before baseline retention

**Subsequent execution:** [safe diagnostics and a fresh failed attempt](context-probe-diagnostics.md)
now localize failure to the inventory boundary. Use that report's current resume.

September 9, 2026. Resumed the prepared execution handoff. Nine focused acquisition tests
passed in 0.391 seconds. Native capture returned exit 1 (`unresolved`, `ValueError`);
fresh-process reload was not run. No recovery or launch authority was produced.

## Exact attempt and retained artifacts

The reviewed one-shot wrapper was `/private/tmp/directions-prospective-acquisition.py`:
`python3 -B /private/tmp/directions-prospective-acquisition.py inspect`, then separately
approved outside-sandbox `python3 -B /private/tmp/directions-prospective-acquisition.py run`.
[Machine-readable report](prospective-acquisition-2026-09-09.json) retains explicit paths,
capture argv, exit status and both output streams.

Transaction: `acquisition-501142a1d74c47b086c42c75b32b7e9d`. Preserve all of:

- `~/Library/Application Support/Directions/MacControlEvidence/acquisition-501142a1d74c47b086c42c75b32b7e9d/slots`
- `~/Library/Application Support/Directions/MacControlEvidence/acquisition-501142a1d74c47b086c42c75b32b7e9d/archive`
- `~/.config/directions/mac-control-anchors/acquisition-501142a1d74c47b086c42c75b32b7e9d`

Canonical parent directories have UID 501/mode 700. Newly created directories and their
parent names were flushed. All selected roots are outside the four currently configured
Syncthing folders and the entire original runtime temp parent. Other sync services were
not assessed. Marker configuration came from the supervisor's Darwin temp-root rule,
not from an evidence report; its canonical directory is
`/private/var/folders/ly/b2sk443n0hq1_z9mgf4q8f4w0000gn/T/directions-stop-spike`.

Read-only inspection after failure found the 32,678-byte historical archive, five empty
witness directories, and the provisioned anchor manifest/fence. In particular, no baseline
witness exists. Do not reuse, repair, overwrite or interpret this transaction as completed.

## Bounded diagnosis

An independent direct native context read returned complete empty inventory, boot
`306b3572-d45a-4158-90a8-27e89bbd5f3d`, session `100024`.
A read-only `_observe_locked` diagnostic then reproduced `bounded context unresolved`
at its first sample through `capture_bounded_context`. Marker bytes before and after
were exactly `b'unresolved'`. No new baseline was retained by diagnostics.

The exact isolated helper subsequently exited 0 with complete empty inventory. A traced
bounded probe passed, and one traced probe under the existing marker lock also passed.
The last locked diagnostic still read `b'unresolved'`. These later successes do not make
the original failed capture successful and do not prove a specific cause. The current
exception sanitization suppresses the lower-level reason; process inventory churn is
only a hypothesis, not an established diagnosis.

## Resume boundary

The prepared procedure requires: “On failure retain all artifacts and stop.” Honored:
no capture retry, reload, reboot, initialization, marker clear, app build/launch or input.
Task 1.3/Gate A remain open; progress stays 2/25. Earlier dirty changes remain preserved.

Next bounded work is diagnostic preparation for the reproduced intermittent native probe
failure: retain a safe stage/error classification so the next observation explains why
it is unresolved, without relaxing inventory completeness or adding retries. Review and
test that diagnostic change before arranging a fresh acquisition with a new transaction.
Do not request a boot transition until capture and separate-process reload both succeed.
Model fit remains deep capability with high reasoning for native evidence integrity.
