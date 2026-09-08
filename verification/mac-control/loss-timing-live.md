# Live loss-timing recheck

**Date:** 2026-09-07 · **Result:** both narrowly scoped loss-detection and input-drain cases passed.
Task 1.3, AC12 restart behavior, and Gate A remain incomplete.

The user approved the [prepared two-minute window](prepared-live-window.md). The actual Codex
session compiled fresh standalone artifacts, checked the worker's nonprompting permissions outside
the sandbox (Accessibility, input monitoring, event posting all true), and verified a clean marker
and no old spike processes. Both cases ran sequentially outside the sandbox. Final process cleanup
was confirmed about 65 seconds after the foreground start was recorded; screen control then ended.

## Measurements

| Case | Actual loss-to-detection interval | Input drain after detection | Matching events | Correct prefixes |
|---|---|---|---|---|
| Disconnect (`clientEOF`) | 0.038042–0.054708 ms | 15.640375 ms | 12/12/12 | 6 |
| Heartbeat loss (`clientHeartbeatLost`) | 2680.614166–2680.620666 ms | 0.260625 ms | 36/36/36 | 18 |

Both conservative upper bounds met the three-second detection limit without tolerance. Both input
drains met the one-second limit. Heartbeat age at detection was **3011.003208 ms**, including
**11.003208 ms** beyond the three-second heartbeat-age threshold. This age is separate from the
actual suppression-to-detection interval: the fault was injected later than the last heartbeat.
The result does not establish zero scheduling overshoot or a universal real-time guarantee.

Both final client verdicts were `casePassed: true`; both clients and supervisors exited 0 with no
reported errors. A separate read-only trace replay checked unique admitted/posted/received tags,
event directions, owned worker source PIDs, expected text-prefix counts, and no admission after
Stop. No event was posted after worker closure. Disconnect posted one reserved cleanup key-up
after Stop; heartbeat loss posted none. Both workers reported empty held-key state.

Each target stayed observable for at least two seconds after detection. All four owned native
children exited 0; neither worker needed forced termination. The marker was clean after each run.
The final process-name scan outside the sandbox found no spike target, worker, client, or supervisor.
The supervisor launched the fresh artifact directly, and successful worker binding checked the
target's kernel executable path against that exact artifact.

## Evidence and reproduction

Portable reports embed the full supervisor trace and final client evidence, original private
temporary paths, SHA-256 hashes of both evidence files, artifact manifest, and source hashes:

- [Disconnect evidence](disconnect-2026-09-07.json)
- [Heartbeat-loss evidence](heartbeat-loss-2026-09-07.json)

Fresh artifact directory:
`/var/folders/ly/b2sk443n0hq1_z9mgf4q8f4w0000gn/T/directions-stop-build.bmNVuf`.
The disposable app is `StopSpikeTarget.app` within it; it was launched successfully for each case
and closed after observation. Older evidence and builds were preserved.

Exact commands, run from the repository root after approval:

```bash
bash tools/mac-control/Spikes/build.sh
/var/folders/ly/b2sk443n0hq1_z9mgf4q8f4w0000gn/T/directions-stop-build.bmNVuf/StopSpikeWorker --preflight
python3 -B tools/mac-control/Spikes/client.py --artifacts /var/folders/ly/b2sk443n0hq1_z9mgf4q8f4w0000gn/T/directions-stop-build.bmNVuf --case disconnect
python3 -B tools/mac-control/Spikes/client.py --artifacts /var/folders/ly/b2sk443n0hq1_z9mgf4q8f4w0000gn/T/directions-stop-build.bmNVuf --case heartbeat-loss
```

Rechecked environment: arm64, macOS 27.0 (26A5421a), Swift 6.3.3, Python 3.14.7.
The build passed in Swift 6 mode with complete concurrency checking and an explicit current-OS
target. Preparation had passed 32 offline tests plus shell syntax and whitespace checks; this run
changed no harness source. The replay reproduced both drain figures and timing verdicts.

## Remaining work

Prepare the next bounded intervention/focus-loss experiment and agree its foreground window.
Crash/hung-call recovery, full startup, permission/monitor loss, sleep/lock, clipboard handling,
broader text, and two-client handoff remain unverified. AC12 stays unchecked because restart is
not covered. No production package, installation, permission changes, deployment, or commit was
part of this run. This approved window is complete and grants no permission for further cases.
