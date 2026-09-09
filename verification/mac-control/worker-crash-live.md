# Native worker-crash observation — September 9

One explicitly approved compile/foreground window completed. The intended between-pairs worker
crash was observed with complete retained receipts and clean target teardown. This is **not a
verified input drain or completed recovery case**: worker closure is absent by design and the
runtime marker remains unresolved. Task 1.3 and Gate A stay open.

## Build and run

Fresh standalone build succeeded with Swift 6 complete concurrency checking at:
`/var/folders/ly/b2sk443n0hq1_z9mgf4q8f4w0000gn/T/directions-stop-build.F6Iv6A`.
No old spike processes were present. The worker's own Accessibility, event-posting and input-monitoring
checks all passed. Artifact hashes were verified before launch; native parent and target identity
checks were preserved and the fresh target bound successfully.

```bash
bash tools/mac-control/Spikes/build.sh
python3 -B tools/mac-control/Spikes/client.py --artifacts /var/folders/ly/b2sk443n0hq1_z9mgf4q8f4w0000gn/T/directions-stop-build.F6Iv6A --case worker-crash
```

The client ran from this actual Codex session with approved outside-sandbox execution. Machine:
arm64, macOS 27.0, Python 3.14.7. No TCC, installation or global configuration changes occurred.

## Retained observations

- Six correct sample prefixes; all 12 admitted tags match exactly 12 worker posts and 12 target
  receipts, with the expected worker source PID. All precede the fault bracket.
- Owned worker 90651 received the intentional kill; supervisor detected `workerEOF`.
- Signal-call bracket to detection: **1.7355–1.794583 ms**. This measures fault-to-detection,
  not drain or actual OS process-death timing.
- No admission after injection. Target 90652 stayed active through its terminal acknowledgement,
  **2032.261375 ms** after detection.
- Worker exited -9 as intended; target exited 0. Client and supervisor exited 2 as specified for
  this diagnostic case. `workerExitFailed` is the expected recorded error.
- All 114 supervisor journal rows exactly equal the independently retained client mirror.
  Artifact hashes, raw journal hash, both traces, audit and measurements are preserved in
  [portable evidence](worker-crash-2026-09-09.json).
- Final outside-sandbox process scan found no StopSpike worker, target or focus-sink processes.
  The runtime marker was read as `unresolved` and was not modified.

Verification assertions checked exact tag sets/counts, source PIDs, prefix counts, timestamps
before injection, no worker closure, target fence duration, exit codes, mirror equality and marker.
The prior 61 offline tests remain the source-validation baseline; this run changed no source code.

## Limits and next step

`casePassed:false`, `drainVerified:false`, `drainMs:null`, `restartEligible:false` are expected.
Complete receipts and process death do not replace the absent worker closure acknowledgement.
This finite target observation does not establish every possible late OS delivery behavior.
No second test or marker reconciliation was attempted; the approved foreground window ended.

Next review a narrowly scoped reconciliation contract against this retained evidence, offline.
Do not clear the marker from PID absence alone. Hung native calls, supervisor death, held-key
cleanup, clipboard and broader intervention requirements remain unverified.

Follow-up: [reconciliation review completed](worker-crash-reconciliation.md). Current evidence lacks
a post-state-update checkpoint and run-bound durable record; the unresolved marker is retained.
