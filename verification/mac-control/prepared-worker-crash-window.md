# Prepared worker-crash window

September 9, 2026. Source and offline sequencing preparation.
Follow-up: [one approved native run completed](worker-crash-live.md); marker remains unresolved.
Task 1.3 and Gate A remain open.

## Implemented case

`client.py --case worker-crash` routes to the supervisor's mutually exclusive `--worker-crash`
mode. Native artifacts, launch parents and target identity checks are unchanged. No Swift source
change or sibling-process substitution is needed for this worker-only fault.

The supervisor injects exactly once, only after six complete down/up pairs: twelve distinct tags
must match admitted events, worker posts and target receipts, including source PID and six valid
text prefixes. No outstanding event, prior stop, duplicate receipt or output-pressure interruption
may remain. It calls `kill()` only on its retained live worker child and brackets the signal call
with the existing continuous clock. Normal worker EOF/exit/write-loss detection must close admission;
the injector does not send Stop first or manufacture a worker closure acknowledgement.

The supervisor stays alive with the target recorder. After two seconds of observation it requests
the target's existing `observeEnd` acknowledgement, with a 500 ms fence deadline, then tears down
the target gracefully. Missing fence, incomplete evidence or unexpected teardown remains failure.

Every sanitized trace row is also emitted nonblockingly to the client, which retains an independent
copy and saves it after teardown. Output pressure interrupts control; active paths do not wait on
disk. `recoveryTraceSaved` follows supervisor journal flush/fsync and includes the row count. The
client checks that count against its copy. `recoveryTraceComplete` means this transport/persistence
check succeeded; it does not validate crash containment or prove event quiescence.

This intentional worker death always leaves `casePassed:false`, `drainVerified:false`,
`restartEligible:false` and the runtime marker unresolved. Worker exit -9, `workerExitFailed`, and
CLI exit 2 are expected diagnostic outcomes, not a successful stop test. No automatic marker
reconciliation or second run follows. Before any later retry, review all retained receipts,
admission boundaries, fence, process exits and remaining uncertainty.

## Offline verification

```bash
python3 -B -m unittest discover -s tools/mac-control/Spikes -p 'test_*.py' -v
python3 -B tools/mac-control/Spikes/client.py --help
python3 -B tools/mac-control/Spikes/supervisor.py --help
git diff --check
```

61 tests passed. CLI help and whitespace checks passed. Three new supervisor tests verify kill
ordering after all twelve posts/receipts, matching client mirror through teardown, no injection
when the final posting acknowledgement is absent, and missing-fence rejection. One real-pipe client
test covers valid/truncated/mismatched mirrors and rejects even a misleading generic drain-success
reply. The synthetic child fixture now preserves its existing exit code when stdin closes, so a
simulated crash cannot be accidentally rewritten as a normal exit.

No native build, process kill, app launch, desktop input, permission change or live marker mutation
was performed by this preparation; subprocess tests use only disposable Python peers.

## Concrete foreground window

With the user present and other foreground automation paused, request approval for compilation
followed by one supervised live case: about 30 seconds of foreground budget (40-second client
deadline plus bounded teardown; compilation is additional). It opens only Directions Stop Spike,
waits five seconds, types six fixed characters, kills its owned worker between completed pairs,
keeps the target recording, then closes the target. Escape or the Stop button can interrupt the
experiment; interruption prevents the intended fault if it arrives before injection.

After explicit agreement:

```bash
bash tools/mac-control/Spikes/build.sh
python3 -B tools/mac-control/Spikes/client.py --artifacts <exact-printed-directory> --case worker-crash
```

Preserve the client audit and supervisor journal in verification storage and report actual stop
reason, signal-to-detection interval, any admission after injection, twelve matching receipts,
target fence, all exit codes and unresolved marker state. A denied preflight or existing unresolved
marker ends the attempt without fallback or forced retry. Supervisor-death and held-key crash cases
remain outside this window, as do installation and TCC changes.
