# Disposable stop spike — task 1.3 preparation

**2026-09-05: built; first mid-entry Stop case passed with six correct characters and 11.716291 ms
input drain.** [Evidence and runtime fixes](../../../verification/mac-control/stop-spike.md).
This is a supervised, disposable experiment for the [protocol](../Protocol.md), not the production
coordinator. Task 1.3 and Gate A remain open. Do not use it to control another application.

**2026-09-06:** disconnect and heartbeat-loss input drains also passed (11.109334/10.571042 ms).
[Latest evidence](../../../verification/mac-control/loss-cases.md) records clean exits and the
detection-timing gap: heartbeat age reached 3003.094042 ms; exact client loss origin is unlogged.
Generic supervisor `measured` does not check the detection deadline.

**Offline follow-up:** [loss instrumentation](../../../verification/mac-control/loss-instrumentation.md)
now records client fault/heartbeat brackets and supervisor detection/receive timestamps. The final
client `caseResult` requires a passing loss-duration bound as well as measured drain. 32 offline
tests passed; the updated instrumentation still needs an agreed live recheck.

**2026-09-07 live recheck:** [both instrumented cases passed](../../../verification/mac-control/loss-timing-live.md).
Loss-detection upper bounds were 0.054708/2680.620666 ms; drains 15.640375/0.260625 ms. Both cases
closed cleanly. The approved window is finished; intervention, clipboard and recovery remain pending.

**2026-09-07 intervention:** [Escape and physical-key cases passed](../../../verification/mac-control/intervention-live.md)
with 8.233833/1.490500 ms drains and clean process exits. That window is also finished. These two
routes now have narrow live evidence; other intervention routes, independent focus-loss, clipboard
and recovery remain pending. See the [next-fixture rationale](../../../verification/mac-control/prepared-intervention-window.md#separate-focus-loss-experiment).

## Foreground test procedure

Agree the window with the user before compiling or running, as required by
[the plan](../../../IMPLEMENTATION_PLAN.md). The first approved case was **`stop-mid-entry`**:

1. Compile the two standalone Swift files into a fresh private temporary directory.
2. Invoke the minimal client from this actual agent session. It starts the owned supervisor;
   the worker checks its own Accessibility, input-monitoring and event-posting permissions.
   A failed preflight ends the experiment without launching the target or requesting permissions.
3. If preflight succeeds, open **Directions Stop Spike**, containing an in-memory text view and
   a Stop button. This activating launch is the reason for scheduling foreground time.
4. Wait five seconds, then type a fixed printable sample at about five characters per second.
   The client sends Stop after receipt of the sixth key-down. No user text or real app store is used.
5. Observe target receipts for two seconds after Stop, then close the disposable target gracefully.
   Report measured timestamps, missing evidence, and the exact artifact/trace locations.

The live portion has a 30-second supervisor budget and a 40-second client deadline, plus bounded
teardown; compilation time is additional. Escape, a physical key/click/scroll, the target's Stop
button, closing the target, client EOF, and Ctrl-C are candidate stop routes. They are **unverified**;
the completed run measured automatic client Stop only. Keep the target visible and do not type during
this first experiment. Closing it ends input but makes late-delivery evidence inconclusive.

After explicit agreement, the agent runs these commands; the user need not run them manually:

```bash
bash tools/mac-control/Spikes/build.sh
```

The build prints the fresh artifact directory. Pass that exact directory to:

```bash
python3 -B tools/mac-control/Spikes/client.py --artifacts <printed-directory> --case stop-mid-entry
```

These are reusable instructions; the linked verification report records the actual approved run.
No installation, permission changes, global deployment, signing-identity changes or real-app
replacement is part of this experiment. Fresh artifacts remain in machine-local temporary storage.

## Components and boundaries

| File | Responsibility |
|---|---|
| `client.py` | Fixed typed JSON request over a persistent inherited pipe; 500 ms heartbeats; selected stop case; bounded wait |
| `supervisor.py` | Owned child processes, one event at a time, admission closure, watchdog, receipt oracle, temporary trace |
| `StopSpikeWorker.swift` | Own permission checks, main-run-loop state, kernel process-start/UID/parent/executable and AX focus checks, tagged PID-directed events, paired key-up cleanup |
| `StopSpikeTarget.swift` | Owned AppKit window/text view, event timestamps/PID/tag and sample-prefix checks, Stop request, graceful EOF close |
| `build.sh` | Swift 6 language mode and complete concurrency checking; isolated temporary app/worker artifacts with SHA-256 manifest |
| `test_supervisor.py` | Offline parser and evidence-oracle regression tests; never starts the live harness |
| `loss_timing.py` | Offline conservative loss-duration oracle; heartbeat age and drain stay separate |
| `test_client.py` | Actual client over real pipes to a synthetic Python peer; no native supervisor or apps |

The worker owns all mutable state on the main actor because AppKit identity/focus queries and its
event-tap source are serviced by that run loop. It has no unstructured input tasks. Synchronous AX
queries use a 50 ms process-wide messaging timeout. An external process supervises hung calls;
the first live drain is recorded above, while hung-call behavior remains unmeasured. Neither actors
nor a configured timeout prove bounded input. Initial launch has a one-use two-second wait for
focus/AX publication; no event is admitted until it passes, and later focus loss stops immediately
when detected. Executable equality uses kernel `proc_pidpath` and POSIX `realpath` consistently.

Before dispatching a down event, the supervisor reserves both its down and possible cleanup-up
tags. It waits for both worker posting and target receipt before admitting the next event. Stop
closes admission first; the worker may send only a paired key-up for an already-held synthetic key.
Only the owned worker may be force-terminated. Target EOF is graceful experiment teardown **after**
the observation interval; target exit does not stand in for quiescence.

The monitor listens without suppressing user input. PID-directed events may bypass the global
session tap, so target receipts must carry the expected worker PID and unique event tag. Global
own-event observations are optional telemetry; physical intervention still requires a separate
live test. Apple's [event source metadata](https://developer.apple.com/documentation/coregraphics/cgeventsource/userdata)
and [Unicode event API](https://developer.apple.com/documentation/coregraphics/cgevent/keyboardsetunicodestring%28stringlength%3Aunicodestring%3A%29)
describe these facilities; they do not guarantee that a target accepts the text. The recorder
therefore checks each owned down event's resulting count and expected sample prefix.

The Swift build is standalone: default nonisolated declarations, explicit `@MainActor` for UI and
run-loop state, `-swift-version 6 -strict-concurrency=complete`, no package or upcoming-feature flags.
The build explicitly targets the current Mac's architecture and OS version because inventory found
the compiler's default target newer than the running OS. Record the first build's actual versions;
this local experiment does not establish the production app's supported OS baseline.

## Evidence and fail-closed behavior

`measured` requires all admitted tags to have worker posting and exactly one target receipt, source
PID verification, correct text prefix/count per down, empty held-key state, worker exit, and final
receipt/admission closure within one second of Stop. The recorder stays open an additional second
to catch late events. No input, missing key-up, wrong prefix, duplicate receipt, target loss, or
missing closure reports `inconclusiveOrFailed`. The client also checks the requested stop reason.
For loss cases its final `caseResult` additionally requires a conservative injection-to-detection
bound of at most three seconds. It saves timestamp brackets and the evaluation in a private
`directions-stop-client-*/client-evidence.json` after teardown; preserve it with the supervisor trace.
Heartbeat age/threshold overshoot stay separate from actual loss duration. Missing evidence,
teardown failures or failure to save the evidence prevent client success.
This finite observation is a measurement, not a proof against every possible OS delivery delay.
`drainVerified` separately records complete event quiescence; a wrong text prefix still fails the
experiment but need not leave an unresolved input marker after both processes exit. No-input or
incomplete-delivery failures report `drainMs:null`. Worker-exit latency is not the drain figure.

A failed permission preflight or missing AX attribute has no fallback to another app, arbitrary
AppleScript, coordinate input or permission-dialog automation. The worker binds only the target
spawned by its supervisor. Its input format is an experimental subset, not the production protocol
parser, ownership/capability implementation or public endpoint.

One verified private lock under the OS per-user temporary directory excludes **other spike runs**.
The lock file is marked unresolved and synced before any child starts. Active trace data stays in
bounded memory so disk writes cannot delay Stop. Trace data is flushed after teardown. A crash can
lose this trace and leaves the marker unresolved, blocking automatic retry. Do not clear the marker
to force another run; inspect the outstanding worker/event uncertainty and design recovery first.
An empty first-run marker is **not** the protocol's clean-bootstrap proof. A fully preserved known
trace may support a narrowly reviewed reconciliation; never substitute PID absence or a failed
text assertion alone for complete receipt/closure and owned-process-exit evidence.

The runtime lock does not exclude legacy automation, native provider control or arbitrary tools.
Run only in the supervised window with other foreground automation paused. Traces contain timings,
event types, PIDs, tags, counts and booleans, never typed content, clipboard data or screenshots.
The target disables copy/cut/paste and does not intentionally access the general pasteboard.

## Later cases and remaining Gate A work

The successful run required approved execution outside the shell sandbox: the worker's own
`--preflight` reported all three checks false inside and true outside, without permission changes.
This mode only reports checks and cannot open a tap, bind a target or post events. Target
`--self-check` verifies its in-memory text system without opening a window or sending input.

CLI cases are `disconnect`, `heartbeat-loss`, `escape`, `wrong-focus`, `physical-key`, and
`stop-button`. The first two now have the narrow drain evidence linked above; the others remain
unverified. Schedule further runs explicitly. For manual cases, intervene
only once sample entry begins. `heartbeat-loss` leaves the pipe open and stops heartbeats; its trace
records detection age separately from drain. A passing generic event-drain result does not prove
the three-second disconnect requirement or any unexercised stop route.

Task 1.3 still needs worker/broker crash and hung-call fault injection, full startup/recovery
evidence, permission/monitor loss, sleep/lock, clipboard ownership/conflict cleanup, target replacement
and broader text boundaries. This first path uses only printable ASCII, no clipboard and no
activation/AX press steps after initial launch. Those omissions cannot be counted as passed criteria.
No production package, menu-bar coordinator, provider integration or installation starts before Gate A.

The user's reiterated multi-session requirement remains in the spec and protocol: one shared FIFO
ready queue per Mac/login, project/session/target/time/steps shown, fresh Yes for each turn, explicit
Review after Wait, one countdown/active owner, and no next owner until input drains. Task 2.3 builds
that queue; task 3.4 proves exclusion with two real clients. This spike lock implements no queue.

## Offline validation

Safe preparation checks, requiring no foreground window:

```bash
python3 -B -m unittest discover -s tools/mac-control/Spikes -p 'test_*.py' -v
bash -n tools/mac-control/Spikes/build.sh
git diff --check
```

The parser/oracle tests use synthetic rows. Client transport tests use real OS pipes to an owned
synthetic Python peer. They do not run the native supervisor/Swift harness, create an event tap,
query permissions, post input or establish live compatibility.
