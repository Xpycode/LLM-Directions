# Disconnect and heartbeat-loss experiments — task 1.3

**Date:** 2026-09-06 · **Status:** both input-drain measurements passed; detection timing needs
stronger instrumentation. Task 1.3 and Gate A remain incomplete.

**Later offline follow-up:** [timestamp instrumentation and deadline assertions](loss-instrumentation.md)
are implemented with 32 passing tests. The historical live measurements below are unchanged;
the new assertions need a fresh live recheck.

The user approved the next two-minute foreground window for these two disposable cases with other
foreground automation paused. The actual Codex session compiled a fresh build, checked that no old
spike process was running, and ran each case sequentially outside the shell sandbox. Worker
Accessibility, input-monitoring and event-posting preflights were true; no permission settings changed.

## Results

| Case | Stop reason | Matching admitted/posted/received events | Correct text prefixes | Input drain after detection |
|---|---|---|---|---|
| Disconnect | `clientEOF` | 12/12/12 | 6 | 11.109334 ms |
| Heartbeat loss | `clientHeartbeatLost` | 36/36/36 | 18 | 10.571042 ms |

Portable evidence: [disconnect](disconnect-2026-09-06.json) and
[heartbeat loss](heartbeat-loss-2026-09-06.json), including artifact/source/trace hashes.

Every target receipt has the owned worker's PID and expected unique tag. No pair was admitted after
Stop and no event was posted after worker admission closure. Disconnect posted only its reserved
cleanup key-up after Stop; heartbeat loss posted nothing after Stop. Both workers acknowledged empty
held-key state. Targets stayed observable for at least two seconds after Stop, then all four owned
child instances exited with code 0. Neither case needed forced worker termination. The clients exited
0. The experiment marker was clean after each run, and the final executable-name scan found no spike
worker or target running. The fresh app was launched and its exact path checked by the harness for
each case, then closed after observation.

Independent read-only trace review confirmed event direction, uniqueness, source identity, text,
cleanup boundaries and exits. A separate local replay reproduced both drain figures. Drain is measured
from supervisor detection to final input receipt/admission closure, not process-exit latency.

## Detection timing limitation

Heartbeat age at detection was **3003.094042 ms**, 3.094042 ms beyond the protocol's 3000 ms loss
threshold. The supervisor polls every 10 ms and the generic `measured` result checks drain only;
neither it nor the client's reason check establishes the liveness deadline.

This does **not** establish an AC12 failure from actual connection loss: heartbeat suppression starts
after the sixth receipt, later than the last heartbeat. Detection followed that receipt by
2685.149292 ms. For disconnect, detection followed receipt six by 0.196458 ms. These contextual
intervals are not directly measured injection-to-detection latencies: the client records neither
the EOF/suppression instant nor the final heartbeat send time in the trace. AC12 also requires restart
behavior, which these cases did not test. Keep AC12 unchecked and preserve the exact measurements.

Next, add timestamped client fault injection and explicit detection-deadline assertions, with offline
boundary tests. Review watchdog scheduling and the distinction between heartbeat age and actual loss
before another approved live run. Do not silently relax the acceptance criterion or count generic
`measured` as liveness success.

## Reproduction and artifacts

Environment rechecked: M1 Max (legacy machine-label file), arm64, macOS 27.0 (26A5421a), Swift 6.3.3,
Python 3.14.7. Compiler default target is macOS 28.0; the build script explicitly targets this Mac.

```bash
bash tools/mac-control/Spikes/build.sh
/var/folders/ly/b2sk443n0hq1_z9mgf4q8f4w0000gn/T/directions-stop-build.Vryec8/StopSpikeWorker --preflight
python3 -B tools/mac-control/Spikes/client.py --artifacts /var/folders/ly/b2sk443n0hq1_z9mgf4q8f4w0000gn/T/directions-stop-build.Vryec8 --case disconnect
python3 -B tools/mac-control/Spikes/client.py --artifacts /var/folders/ly/b2sk443n0hq1_z9mgf4q8f4w0000gn/T/directions-stop-build.Vryec8 --case heartbeat-loss
```

- Fresh app: `/var/folders/ly/b2sk443n0hq1_z9mgf4q8f4w0000gn/T/directions-stop-build.Vryec8/StopSpikeTarget.app`.
- Disconnect trace: `/var/folders/ly/b2sk443n0hq1_z9mgf4q8f4w0000gn/T/directions-stop-spike-fmgudf1u/events.jsonl`.
- Heartbeat trace: `/var/folders/ly/b2sk443n0hq1_z9mgf4q8f4w0000gn/T/directions-stop-spike-s6fffz2f/events.jsonl`.

Before the live window, 16 offline parser/oracle tests, `bash -n tools/mac-control/Spikes/build.sh`,
and `git diff --check` passed. Both Swift sources compiled in Swift 6 language mode with complete
concurrency checking. Process inspection required shell escalation; the sandboxed `ps` was denied.
No target self-check was rerun; these live cases verified actual text insertion.

No global own-event tap receipts were observed. Physical intervention/focus loss, crash/hung-call
recovery, startup, clipboard, broader text and two-client handoff remain unverified. This window
covered only these two cases; it grants no standing foreground permission for later experiments.
No production package, installation, deployment or commit was made.
