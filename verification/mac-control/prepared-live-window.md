# Prepared loss-timing recheck

**Prepared:** 2026-09-06. **Status:** approved and completed 2026-09-07; [both cases passed](loss-timing-live.md).
Scope: task 1.3, disconnect followed by heartbeat loss in the disposable Directions Stop Spike.
This preparation is not live evidence or completion of AC12/Gate A.

## Preparation results

- 32 offline tests passed in 10.146 seconds using
  `python3 -B -m unittest discover -s tools/mac-control/Spikes -p 'test_*.py' -v`.
- `bash -n tools/mac-control/Spikes/build.sh` and `git diff --check` passed.
- Exact spike process-name scan outside the sandbox found no target, worker, or spike client/supervisor.
- Runtime directory and lock belong to this user, with modes 0700/0600; marker reads `clean`.
  This is a preparation snapshot; repeat before launch and between cases. The marker was not changed.
- No native compilation, permission query, app launch, or desktop input was performed.

## Proposed window

After approval, compile fresh temporary artifacts and check the worker's nonprompting preflight.
The [runbook](../../tools/mac-control/Spikes/README.md) reserves compilation for after agreement.
Then announce the start of a maximum two-minute foreground window. Other foreground automation
must be paused, and the user should leave keyboard/mouse idle while the samples run.
Compilation is additional background preparation time; do not silently extend foreground time.

1. Run `bash tools/mac-control/Spikes/build.sh`; retain its exact printed artifact directory.
2. Run `<fresh-directory>/StopSpikeWorker --preflight`; require all three checks to pass.
   Recheck the marker and absence of old spike processes. Failed checks stop the sequence.
3. Announce the foreground start and record its deadline. Run
   `python3 -B tools/mac-control/Spikes/client.py --artifacts <fresh-directory> --case disconnect`.
   The owned target activates, waits five seconds, then receives fixed sample text. The client
   disconnects after the sixth key-down receipt.
4. Inspect the final client verdict, trace, owned-child exits, and clean marker before continuing.
   Any failure or unresolved teardown stops the sequence. Start the next case only if at least
   50 seconds remain for its 40-second client deadline, six-second teardown wait, and margin.
5. Run the same client command with `--case heartbeat-loss`. It suppresses heartbeats after
   the sixth key-down receipt while keeping the pipe open; the supervisor detects liveness loss.
6. Verify owned target/worker exits and marker, and announce when screen control has ended.
   Review and preserve evidence in the background. No automatic retries or extra cases.

The target's Stop button, Escape, physical intervention, and closing the target are available
candidate interruption routes, but remain unverified. Closing the target ends input and makes
late-delivery evidence inconclusive. On an interruption, cancel the sequence and inspect teardown;
never clear an unresolved marker merely to retry.

## Evidence required for each case

- Preserve both printed paths: supervisor `events.jsonl` and client `client-evidence.json`.
  Preserve fresh artifact/source hashes with the new report; keep earlier evidence unchanged.
- Correct reason (`clientEOF` or `clientHeartbeatLost`), final `casePassed: true`, client exit 0,
  supervisor exit 0, successful owned-child exits, and no teardown errors.
- Conservative actual fault-injection-to-detection upper bound <=3,000,000,000 ns; report both
  bracket bounds. Heartbeat age and threshold overshoot are separate measurements.
- Input drain <=1 second, complete matching admitted/posted/received event identities and text-prefix
  checks, closed admission, empty held-key state, and no unexplained events after stopping.
- A failed timing result is recorded as failed even if the generic supervisor drain result passed.
  Recovery, intervention, clipboard, and broader compatibility remain pending after these cases.
