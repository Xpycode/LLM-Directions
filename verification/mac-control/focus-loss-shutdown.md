# Focus-loss measurement with failed worker shutdown — September 9

User requested another test after the interrupted attempt. One fresh two-minute window ran with
`client.py --case focus-loss --artifacts /var/folders/ly/b2sk443n0hq1_z9mgf4q8f4w0000gn/T/directions-stop-build.IdAV2D`.
Preflight all true, no old spike processes, initial marker clean.

**Overall result: failed.** Six correct characters, all 12 posted/received/origin-verified events,
`wrongFocus` with `frontmost` cause, 16.80225 ms activation-request-to-detection upper bound,
0.045292 ms measured input drain, zero sink input, and both observation fences passed.
Observation lasted 2007.34275 ms. These are narrow measurements, not a successful complete case.

Worker PID 69281 then had exit -5 (SIGTRAP); target 69283 and sink 69282 exited0.
Client/supervisor exited2, `casePassed:false`. Final process scan empty, screen control ended.
Marker remains unresolved. [Portable evidence](focus-loss-shutdown-2026-09-09.json) preserves the
trace, client outcome and tested artifact hashes. Runtime trace: `directions-stop-spike-hmc70v96`;
client: `directions-stop-client-wk6shtqp`.

Crash report `~/Library/Logs/DiagnosticReports/StopSpikeWorker-2026-09-09-123759.ips` identifies
SIGTRAP in `Worker.tick()`. Code inspection found `now - stopAt` on UInt64 after a focus check can
call stop() and record a timestamp later than tick's cached `now`. This underflow is consistent
with the crash location/registers. The shutdown check now resamples the monotonic clock before
subtraction. Standalone Swift6/complete-concurrency compilation passed into fresh temporary
directory `directions-stop-build.hgLdR5`; this corrected artifact was not launched.

Next: review reconciliation against the full retained input receipt/closure/fence and process-exit
evidence (the earlier **no-input** reconciliation does not apply), then run in a newly agreed window.
Do not clear the marker based on process absence or treat the generic measurement as a complete pass.
No TCC/install/deployment/commit changes. Task 1.3/Gate A and broader recovery/clipboard work stay open.
