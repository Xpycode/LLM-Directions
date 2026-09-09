# Prepared independent focus-loss window

**Prepared:** 2026-09-09. **Status:** approved window completed; [startup failed before input](focus-loss-startup.md).
The singleton fix recompiles but has not run. Marker reconciliation and a new window remain pending.
Task 1.3 and Gate A remain open. The preparation and original procedure below are retained for context.

## Scope and implementation

`client.py --case focus-loss` starts the owned supervisor with `--focus-loss`. After the worker's
existing nonprompting preflight, a separate `StopSpikeFocusSink.app` starts hidden and inactive.
Its ready PID must match the spawned child before the supervisor launches the original text target.
The worker still binds exclusively to that original target; the sink receives no worker capability.

After five seconds and six completely posted/received character pairs, the supervisor sends the
sink its one-shot `activate` command. The sink requests foreground focus using AppKit, without
generating keyboard or mouse events. All worker safeguards remain enabled and dispatch is not
paused. Missing activation or a competing stop reason fails this experiment.

The sink records local keyboard/mouse/scroll events without text content, activation transitions,
and foreground PID/active state every 100 ms. The original target records activation transitions.
After the two-second post-stop interval the supervisor requests an evidence-stream fence from
both apps and consumes both acknowledgements before evaluating. A missing fence fails after
500 ms. Both apps keep recording until their owned stdin pipes close during graceful teardown.
These fences cover emitted application records through each acknowledgement, not hypothetical
events indefinitely delayed inside macOS.

The worker's final pre-post foreground check now records `wrongFocus`/`frontmost` explicitly.
The focus oracle requires that cause, a successful independent activation, six pre-fault characters,
zero sink input, no original-target reactivation, initial/periodic/final sink focus observations
with gaps <=200 ms, both fences, and no posts after worker closure or admissions after Stop.
The request-to-detection conservative bound must be <=1 second; generic drain must independently
meet its existing <=1 second bound. A reserved cleanup key-up remains allowed before closure.
The client additionally rejects missing focus evidence and failed sink teardown. Supervisor exit
status is now decided after teardown, including failed target/sink exits.

## Offline verification

September 9 result: **45 tests passed in 12.527 seconds**; build-script syntax and
`git diff --check` passed. Machine reports `M1-Max`, macOS 27.0 (26A5425a), Apple Swift 6.3.3,
Python 3.14.7. The compiler version query emitted sandbox cache/FSEvents warnings but succeeded;
this was not a native compilation. Its default target is macOS 28; the build script explicitly
targets the running OS as before.

Run from the Directions master:

```bash
python3 -B -m unittest discover -s tools/mac-control/Spikes -p 'test_*.py'
bash -n tools/mac-control/Spikes/build.sh
git diff --check
```

Coverage includes synthetic focus traces and false-pass rejection, the actual supervisor loop with
deterministic synthetic child/selector/clock substitutes, and the real client over pipes to a
synthetic Python peer. None of these launches native apps or proves actual AppKit activation,
permission availability, scheduling latency, event delivery, or second-Mac compatibility.
Independent review identified the unread-output gap and sparse-sampling false pass; fences and
bounded sample-gap checks address those findings. Native Swift compilation remains pending under
the existing task 1.3 scheduled-window procedure.

## Proposed next window: one case, at most two minutes

After the user agrees to this specific window:

1. Run `bash tools/mac-control/Spikes/build.sh` to create three fresh artifacts and their manifest.
   Build time precedes the foreground timer. A build failure ends preparation without launching.
2. Recheck actual Mac/toolchain, owned spike processes and private runtime lock/marker. Preserve
   unresolved markers; do not clear one to retry. Run the exact fresh worker's `--preflight` in
   the permitted execution context. False permissions end the run without TCC changes.
3. Announce the start of the two-minute window. Run exactly:
   `python3 -B tools/mac-control/Spikes/client.py --artifacts <fresh-directory> --case focus-loss`.
   The user leaves keyboard/mouse idle and pauses other foreground automation. Only the two
   disposable apps activate. No real editor, clipboard or user store is a target.
4. Allow automatic focus transfer and Stop, evidence fences, then graceful teardown. The client
   deadline is 40 seconds plus at most eight seconds waiting for supervisor teardown; the supervisor
   experiment budget is 30 seconds followed by bounded observation/teardown. No automatic retry.
5. Require `casePassed: true`, supervisor/client exit 0, all three owned native children exit 0,
   complete event identities/prefixes/drain, focus evidence and a clean marker. Verify executable
   paths in the trace against the fresh artifacts and confirm no owned spike processes remain.
   Announce screen control ended before background evidence preservation/review.

Escape or other physical intervention can abort. Closing the original target aborts and makes
receipt evidence inconclusive. Any missed transfer, competing stop, failed teardown, unavailable
permission or expired window ends the case; retain evidence and do not extend or retry silently.
Recovery, clipboard, broader intervention and all other Gate A work remain pending afterwards.
