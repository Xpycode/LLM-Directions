# Live intervention tests

**Date:** 2026-09-07 · **Result:** Escape and one physical keypress passed their narrow stop cases.
Task 1.3, full intervention coverage and Gate A remain incomplete.

The user approved the [prepared two-minute window](prepared-intervention-window.md). This actual
Codex session built fresh standalone artifacts, checked the worker's nonprompting permissions
outside the sandbox (all three true), and confirmed no old spike processes and a clean marker.
Both cases ran sequentially outside the sandbox. Final process cleanup was confirmed about
58 seconds after recording the window start; screen control then ended.

## Measurements

| Case | Stop reason | Input drain from worker stop detection | Matching admitted/posted/received events | Correct prefixes |
|---|---|---|---|---|
| Escape | `escape` | 8.233833 ms | 12/12/12 | 6 |
| Physical keypress (requested lowercase `x`) | `unownedInput` | 1.490500 ms | 12/12/12 | 6 |

Both clients reported `casePassed: true` and exited 0. Both supervisors and all four owned native
children exited 0, with no teardown errors or forced worker termination. The marker was clean after
each case; process scans outside the sandbox found no spike target, worker, client or supervisor.

A separate read-only replay of the saved traces verified unique event identities, event directions,
worker source PIDs, text-prefix counts, empty held-key state and each drain figure. Neither case
admitted another pair after worker Stop. Each posted exactly one already-reserved cleanup key-up
after Stop and no event after worker closure. Each target stayed observable for over two seconds
after supervisor detection. Both drains met the one-second requirement for these runs.

Physical-event origin time is not separately recorded, so these figures start at worker stop
detection and do not measure hardware-event-to-detection latency. The physical-key reason records
unowned input, not its character or a universal proof of physical versus synthetic origin.
The known sample and user participation establish only these two supervised scenarios.

## Evidence and reproduction

Portable evidence embeds each full supervisor trace, client evidence, original temporary paths,
evidence/source/artifact SHA-256 hashes and the replay results:

- [Escape evidence](escape-2026-09-07.json)
- [Physical-key evidence](physical-key-2026-09-07.json)

Fresh artifact directory:
`/var/folders/ly/b2sk443n0hq1_z9mgf4q8f4w0000gn/T/directions-stop-build.mYp0GY`.
Its `StopSpikeTarget.app` launched successfully for both cases and closed after observation.
The worker's successful binding checked the running target's kernel executable path against that
exact fresh artifact. No previous test instance remained before either launch.

Exact commands from the repository root after approval:

```bash
bash tools/mac-control/Spikes/build.sh
/var/folders/ly/b2sk443n0hq1_z9mgf4q8f4w0000gn/T/directions-stop-build.mYp0GY/StopSpikeWorker --preflight
python3 -B tools/mac-control/Spikes/client.py --artifacts /var/folders/ly/b2sk443n0hq1_z9mgf4q8f4w0000gn/T/directions-stop-build.mYp0GY --case escape
python3 -B tools/mac-control/Spikes/client.py --artifacts /var/folders/ly/b2sk443n0hq1_z9mgf4q8f4w0000gn/T/directions-stop-build.mYp0GY --case physical-key
```

Environment rechecked: arm64, macOS 27.0 (26A5421a), Swift 6.3.3, Python 3.14.7. Build passed
in Swift 6 mode with complete concurrency checking and an explicit current-OS target. Preparation
passed 32 offline tests and shell syntax checks; this live run changed no harness source.

## Next

Prepare the separate disposable focus-loss fixture described in the prepared runbook. A manual
app switch can stop on physical input first, so it cannot independently verify focus handling.
Clicks/scroll, broader input-origin handling, crash/hung-call recovery, startup, permission/monitor
loss, sleep/lock, clipboard and broader text remain pending. The approved window is complete;
no extra foreground case, installation, permission change, deployment or commit was performed.
