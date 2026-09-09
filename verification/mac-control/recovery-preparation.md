# Offline crash and hung-call recovery preparation

September 9, 2026 · arm64 · macOS 27.0 (26A5425a) · Python 3.14.7.
Task 1.3 remains open. This report adds offline evidence, not a live recovery pass.

Follow-up: the [independent subprocess observer](recovery-observer.md) is now implemented;
57 offline tests pass. The design below records the preceding preparation and remaining native scope.

## Checked behavior

`test_recovery.py` runs the actual supervisor loop through the existing synthetic transport.
It reserves the first input pair, then substitutes either a worker crash or an event call that
never returns posting/receipt evidence and ignores Stop. The clock and child processes in these
two scenarios are simulated; the test does not call AppKit, AX or CGEvent.

Both cases must close admission with exactly one event command, return failure, retain the
unresolved marker, and report no verified drain. The hung-event case detects the missing receipt
within 410 ms in the simulated schedule and kills only its owned worker 500–510 ms after Stop.
These bounds test policy with 10 ms ticks; they are not observed native latencies. The synthetic
transport still delivers heartbeats, isolating the receipt watchdog from the liveness watchdog.
The target closes through EOF and is never force-killed. Killing a worker cannot turn missing
input evidence into success.

Separate tests exercise the real `experiment_lock`, filesystem permissions, `flock` and `fsync`
inside a disposable test directory. A Python child exits abruptly with `os._exit(17)` while holding
the lock; the next acquisition fails on the retained unresolved marker even after that child is
reaped. A concurrent acquisition and unknown marker also reject without changing marker contents.
This child owns no native worker. The test substitutes only the runtime-directory lookup and
never accesses or reconciles the real spike marker. These checks do not prove stale worker identity
reconciliation, production bootstrap or grant invalidation.

## Remaining live experiment design

The current CLI has no crash or hung-call case. Do not pass invented case names or kill a live
supervisor with its current recorder: its trace is buffered in memory and its target closes on
parent EOF, which would destroy the observation needed to assess late events.

| Case | Controlled fault | Required evidence and expected outcome |
|---|---|---|
| Worker crash between complete pairs | Retained owned-child handle, after six matched pairs | Bracket fault and detection on the shared continuous clock; admission closes, recorder stays open through an observation fence, child exit is recorded. Missing closure keeps recovery blocked even if all prior receipts match. |
| Worker stalls before posting | One-shot test-only stall after admission, before posting | Record the fault boundary independently; watchdog closes admission and terminates only its owned worker. Reserved but unaccounted tags keep the marker unresolved. This synthetic stall establishes watchdog behavior, not an actual AX timeout. |
| Worker crash with a held key | After a down receipt, before its paired up | Explicitly account for the pending up; process death alone cannot prove held-key cleanup. Do not run until a bounded cleanup and evidence strategy exists. |
| Supervisor crash | Owned supervisor dies while worker and recorder survive under an independent observer | Capture worker parent-loss/EOF detection, held-key cleanup, receipts, fences and exits despite supervisor death. Retry must refuse the unresolved marker; no auto-resume. |
| Restart after uncertainty | New process attempts normal lock acquisition | Reject before any native child launches. Preserve the marker and the old evidence. Never signal a PID loaded from a file. |

Before a foreground window, build an independent observer fixture offline. It must preserve the
recorder lifetime and sanitized evidence across supervisor death without retaining an extra worker
stdin writer (which would conceal EOF). It needs bounded cleanup of retained owned children,
fault timestamp brackets, final stream fences, and separate outcomes for fault containment,
input drain and restart eligibility. Test it first with real pipes and disposable Python children.
Do not add synchronous per-event disk writes to the active supervisor to obtain crash evidence.

Start with the between-pairs worker fault. Leave the held-key and supervisor-death cases blocked
until that observer and cleanup contract are tested. Do not add production recovery or broaden
the accepted `measured` verdict merely to make intentional crash cases pass.

## Validation

```bash
python3 -B -m unittest discover -s tools/mac-control/Spikes -p 'test_*.py' -v
git diff --check
```

Result: 49 offline tests passed, including four new recovery tests; whitespace check passed.
No native build, app launch, input, TCC change or live marker mutation was performed.
The next step at this checkpoint was the independent subprocess observer, now completed in the
linked follow-up. A later native compile/run still requires the scheduled foreground window.
