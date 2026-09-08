# Prepared intervention window

**Prepared:** 2026-09-07. **Status:** approved and completed; [both cases passed](intervention-live.md).
Task 1.3 remains open. This continues the completed [loss-timing tests](loss-timing-live.md).

## Preparation and scope (before approval)

- Read the current client, supervisor, native worker and disposable target. No source changes needed
  for the existing `escape` and `physical-key` cases.
- 32 offline tests passed in 10.414 seconds with
  `python3 -B -m unittest discover -s tools/mac-control/Spikes -p 'test_*.py' -v`.
  These exercise parsers, receipt/timing assertions and client pipes, not native intervention.
- `bash -n tools/mac-control/Spikes/build.sh` passed. The runtime directory/lock belong to this
  user, have modes 0700/0600, are not symlinks, and the marker reads `clean`.
  This read-only snapshot does not prove process absence; check owned processes before launch.
- No native build, permission query, desktop input, app launch or runtime-marker change performed.

## Proposed two-minute window

The only automated input target is the fresh **Directions Stop Spike** in-memory text view.
The user participates twice: press Escape in the first run, then lowercase `x` in the second,
each once after the sample visibly starts typing (ideally after about six characters).
Keep keyboard/mouse idle at other times and pause other foreground automation.

After agreement, the agent performs the commands and checks:

1. Compile with `bash tools/mac-control/Spikes/build.sh` into a fresh temporary directory.
   Compilation precedes the foreground timer, following the existing runbook.
2. Run that exact directory's `StopSpikeWorker --preflight`; require all three checks true.
   Check no previous spike target/worker/client/supervisor remains and the marker is clean.
   Resolve any outstanding instance before launch; never clear an unresolved marker to retry.
3. Announce the Escape case and start the maximum two-minute foreground window. Invoke
   `python3 -B tools/mac-control/Spikes/client.py --artifacts <fresh-directory> --case escape`.
   The fresh target activates, waits five seconds and starts typing. The user presses Escape once.
4. Keep the target open for the supervisor's two-second post-stop observation, then let its owned
   pipe close it gracefully. Check the final client verdict, trace, child exits and clean marker.
   A missing/wrong reason, incomplete drain or teardown failure ends the sequence without retry.
5. Only if at least 50 seconds remain, announce the physical-key case and run the same client with
   `--case physical-key`. On visible sample entry, the user presses unmodified lowercase `x` once.
   User input is deliberately not suppressed; it may appear in the disposable text view.
6. Verify both owned children exited, no spike processes remain and the marker is clean; announce
   screen control ended. Preserve and review evidence in the background. Do not extend the window
   or launch an extra case if either intervention was missed or the window expired.

Each client has a 40-second deadline plus a six-second supervisor teardown wait; the supervisor
has a 30-second experiment budget. If the user needs to abort, Stop/close remains available, but
closing the target makes receipt evidence inconclusive. No successful result authorizes a retry.

## Evidence and limits

- Preserve `events.jsonl`, `client-evidence.json`, source/artifact hashes, actual command and machine.
- Require worker and supervisor stop reasons `escape` or `unownedInput`, respectively; final
  `casePassed: true`, client/supervisor exit 0, both native children exit 0 and no teardown error.
- Require actual sample input before intervention, complete owned event identities and origins,
  correct sample prefixes before intervention, empty held-key state and input drain <=1 second.
  Inspect trace order for no later worker input except a reserved paired cleanup key-up.
- The physical `x` has no owned tag and must not count as automation. A physical character can
  affect a racing owned event's prefix check; preserve an inconclusive result, never weaken the
  assertion or clear a marker to obtain a pass. Assess the actual trace before designing a follow-up.
- Worker stop time measures detection/admission closure. The current monitor does not separately
  log physical-event origin time, so these runs cannot claim hardware-event-to-detection latency.
- These are narrow live samples for Escape and an unmodified key; clicks, scroll, all input-origin
  cases, focus loss, clipboard, crash/hung-call recovery and full Gate A remain unverified.

## Separate focus-loss experiment

The existing `wrong-focus` case expects `wrongFocus` or `readinessLost`. A click or Command-Tab
can first hit the worker's listen-only physical-input monitor (including modifier changes), which
stops with `unownedInput`. That demonstrates intervention, not the independent focus check.
Do not broaden accepted reasons or call this a focus-loss pass.

After these cases, prepare an owned disposable focus-change fixture that changes focus without
keyboard/mouse input. It needs a recorded transition time, an identified second disposable target
with event receipts, and evidence of no input to that second target or forced reactivation of the
first. A `readinessLost` result additionally needs a focus-specific cause, because permission and
monitor failures share that reason. This is still task 1.3, not production UI or a new backlog task.
Its source, checks and foreground window must be concrete before execution.
