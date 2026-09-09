# Single-reader supervisor recovery integration

September 9, 2026 · offline Python fixtures; no native input or runtime marker access.

The worker-crash supervisor now creates `OwnedEvidence` after verified launch-identity setup and
before bind/dispatch. The supervisor remains the only reader of native stdout. Exact bytes and EOF
feed the collector before its existing safety parser; the collector independently frames and
validates them and obtains exit observations from retained child handles. External-reader mode
never registers or reads a second pipe. Existing normalized/native standalone readers still work.

The final resolved writer acknowledgement is bound only after complete receipt/post/checkpoint
collection and observed child liveness. Controlled crash injection requires this binding. Dispatch
and the writer close before the crash signal. The collector waits two seconds after both observed
worker exit and EOF before requesting the target fence; it closes target stdin after acknowledgement
and continues reading to target EOF and owned exit. Five seconds bounds incomplete recovery
observation after Stop. Target teardown retains the existing graceful timeout; targets are not killed.

Collected evidence, including actual waits/EOFs, is retained in the trace and mirrored to the client.
`recoveryEvidenceComplete` means collection finished, not that reconciliation passed: late or
duplicate rows remain present and can still fail the verifier. Worker-crash results remain failed
experiments with `restartEligible=false` and an unresolved marker. Native clocks use the supervisor's
existing continuous clock. `capture_context(clock=...)` can now use that same transaction domain.

## Validation and review

Synthetic peers now emit the exact native schemas and expose EOF after process exit. Existing
crash tests therefore observe EOF before the end-of-loop wait in one fault case; its expected
reason was updated. Malformed receipt kinds reject at the new strict parser before admission.

Supervisor integration tests cover a real temporary writer, final acknowledgement binding before
fault injection, complete stream/wait collection passed to the real verifier with synthetic context,
missing/wrong/post-exit acknowledgements, partial EOF, oversized frames, late extra receipts,
write failures, setup timeouts, and Stop/heartbeats during a stalled write. A synthetic successful
candidate never enables restart. Extra late receipts survive collection and fail verification.

Independent review reproduced an asynchronous-kill race: delaying the final acknowledgement until
the next-dispatch time and delaying `poll()`'s exit observation allowed a new uncertain reservation
after the fault signal. Closing admission and the writer before kill prevents that overwrite.
The reviewer added `test_supervisor_crash_race.py` and confirmed the correction. Final full suite:
**203 tests in 26.835 seconds — 202 passed, one existing sandbox boot-query skip**.
Whitespace validation passed. The review found no remaining concrete correctness issue.

```bash
python3 -B -m unittest discover -s tools/mac-control/Spikes -p test_recovery_integration.py -v
python3 -B -m unittest discover -s tools/mac-control/Spikes -p 'test_*.py'
git diff --check
```

## Next bounded task

**Completed in the [held-lock continuation](recovery-reconciliation.md).** The following was its
original scope; the continuation records validation and the next pickup.

Connect the retained collector to read-only locked reconciliation in the supervisor after teardown,
without releasing/reacquiring ownership between evidence and the decision. The snapshot adapter
currently acquires its own marker lock, while the supervisor already holds it: design an explicit
trusted held-lock interface and test ownership/descriptor lifetime, pending writer lock, changing
files/context and failure paths. Wait for writer resource release with a bounded post-input deadline.
Use `capture_context(clock=now)` and the same continuous clock for the whole transaction. Keep the
verdict non-authorizing, preserve the marker and never replay a persisted report as owned evidence.

Native inventory visibility and Swift compilation remain unverified. A future native experiment
requires its separately agreed window and must address the historical unresolved marker first.
The in-process collector does not survive supervisor death, so broker-crash recovery remains
separate. Task 1.3/Gate A, clipboard and broader intervention proof remain open. No commit, push,
native launch, marker clear or installation occurred; earlier dirty work remains preserved.
