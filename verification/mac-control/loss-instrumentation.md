# Loss-timing instrumentation — offline follow-up

**Date:** 2026-09-06 · **Status:** implemented and reviewed; 32 offline tests passed. No new native
build or live foreground experiment in this follow-up. Task 1.3, AC12 and Gate A remain incomplete.

**Subsequent live verification, 2026-09-07:** [both instrumented loss cases passed](loss-timing-live.md).
The offline history below is unchanged; restart and broader Gate A proof remain pending.

## Result

The [earlier live cases](loss-cases.md) measured input drain but lacked the actual client fault
timestamp. The minimal client now brackets its real pipe close or heartbeat-suppression mutation
with the same continuous boot clock used by the supervisor/worker. It also brackets the final
heartbeat write. These timestamps are local evidence; no new protocol message conveys them or
refreshes liveness. The control request and fault route remain the same.

The supervisor's first `stopping` report now includes `detectionNs` from its captured `stop_at` and
`lastClientLivenessNs` from the last accepted request/heartbeat. It snapshots them before later
message processing can update liveness. The client adds `clientReceivedNs` when it reads that report.
The existing `originNs`/drain oracle remains separate.

The new [timing oracle](../../tools/mac-control/Spikes/loss_timing.py) checks:

- A matching loss case and stop reason, complete timestamps, valid ordering and no future detection
  relative to the client's report receipt. Missing or malformed evidence fails.
- A conservative interval: `detection - beforeInjection` is the upper bound;
  `max(0, detection - afterInjection)` is the lower bound. Detection inside the `close()` bracket
  is valid. Heartbeat receive may occur during a write or before the latest queued write is processed.
- The upper bound must be **<=3,000,000,000 ns**, compared as integers with no tolerance. One
  nanosecond late fails even if the lower bound fits. Heartbeat loss also requires received-heartbeat
  age to have reached the existing three-second threshold.
- Heartbeat age and threshold overshoot are separate telemetry, not the actual loss duration.
  A measured case establishes only this injection-to-detection bound and its separate drain result;
  it does not complete AC12's restart requirement.

The client saves `client-evidence.json` in a fresh private `directions-stop-client-*` temporary
directory after teardown. Its bounded evidence includes the case, clock, fault/heartbeat brackets,
first stop report and receipt time, supervisor result/exit code, supervisor trace directory, errors,
timing evaluation and `casePassed`. Directory mode is 0700 and file mode 0600. It records no typed
content, screenshot or clipboard data. No evidence-file I/O occurs on the active fault/Stop path.
Crash before persistence can still lose this client evidence; this is not a recovery ledger.

`caseResult` reports the evidence path and the combined verdict. Exit 0 requires the requested
reason, measured drain, passing timing for loss cases, supervisor exit 0 and no captured errors.
Duplicate/truncated results, impossible timestamps, missed deadlines, teardown timeout, native-child
failure reports and evidence-save failure prevent success. Native-child nonzero exits now retain
the supervisor's unresolved marker. The supervisor's earlier generic `result` still describes
drain only; use the final client verdict and both evidence files for case review.

## Scheduling review

The supervisor retains its 10 ms selector poll and the existing heartbeat-age threshold of
3,000 ms. A poll or OS scheduling delay can process threshold crossing later, as the earlier
3003.094042 ms reading showed. Shortening sleep cannot guarantee zero overshoot; no threshold was
silently reduced or acceptance tolerance added. This change measures actual loss duration and
rejects a late result. Hung-call resilience and admission behavior under load remain separate
task 1.3 work, not proven by these tests.

## Validation

Environment: M1 Max, macOS 27.0 (26A5421a), Python 3.14.7 (rechecked earlier this session).

```bash
python3 -B -m unittest discover -s tools/mac-control/Spikes -p 'test_*.py' -v
git diff --check
```

**32 tests passed in 10.179 s.** The suite contains the original 16 parser/drain tests, nine timing
tests and seven client transport tests (some with several subcases). Timing tests cover just below,
exactly at and one nanosecond past the deadline, overlapping clock brackets, heartbeat-age versus
loss duration, absent/reversed/future timestamps and the wrong stop reason.

The transport tests run the actual `run_case` client with real inherited OS pipes and a synthetic
Python supervisor peer. They prove that disconnect closes the pipe, heartbeat loss keeps it open
without further heartbeat messages, reports persist, invalid detection cannot hide behind a drain
success, and teardown/save errors fail. They replace the native supervisor launch and use a shared
`time.monotonic_ns` test clock; they do not execute the actual supervisor loop, call permission APIs,
launch AppKit, create taps, or post input. Native timing and actual supervisor integration therefore
still require a live recheck.

All five Python files parsed with `ast.parse`; whitespace checks passed. Independent source review
identified future timestamps and incomplete target teardown as possible false passes; both were
fixed and covered by tests. Final scoped review found no further issues. No Swift source changed,
so no native rebuild was used as an offline validation claim.

## Next live window

Schedule the same two disposable cases for a fresh two-minute foreground window with other
foreground automation paused. Build and run the documented client commands in the spike runbook;
the client now prints both the supervisor trace and final client-evidence path. Review both files,
the exact loss-duration bounds, heartbeat age, every post/receipt, and successful owned-child exits.
Preserve the earlier live artifacts/reports rather than relabeling them with the new assertions.
The new instrumentation has no live result yet. No production package or installation starts here.
