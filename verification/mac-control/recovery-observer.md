# Independent recovery observer — offline result

September 9, 2026 · arm64 · macOS 27.0 (26A5425a) · Python 3.14.7.

The independent Python observer is implemented and tested with actual OS pipes and disposable
Python subprocesses. [Saved standalone evidence](recovery-observer-2026-09-09.json) records a
passing synthetic supervisor-crash case. Task 1.3 and Gate A remain open.

## Ownership and evidence

`recovery_observer.py` owns three fixed peers from `recovery_peer.py`; it accepts no arbitrary
executable, native artifact, target PID or input payload. All three are retained `Popen` children.
Only the synthetic supervisor retains the worker's command-pipe writer. The observer closes its
copy immediately after launch, so supervisor death produces actual worker EOF. A negative test
deliberately retains that copy and verifies that missing EOF fails the experiment.

The worker writes numbered synthetic receipts directly to a separate recorder pipe, and posting
and stop diagnostics directly to the observer. The recorder's control pipe belongs to the
observer, so it survives supervisor death and worker source EOF. Its final acknowledgement joins
the source reader first. The observer also consumes the worker output through EOF before asking
for the recorder fence. No desktop events or real held keys are involved.

After two matching receipts and posting records, the observer brackets the crash request through
observed supervisor exit using Python's shared monotonic clock. The supervisor exits with the
intentional code 17. Worker EOF, stop and terminal evidence remain available. The recorder is
confirmed alive before the final fence; it and the worker then exit 0. The standalone run needed
no forced termination. These timings do not establish native continuous-clock or macOS input limits.

The result separates `transportContained`, `syntheticDrainComplete`, `nativeDrainVerified` and
`restartEligible`. The latter two are always false for this offline tool. It neither reads nor
changes the live runtime marker. Restart rejection remains the separate isolated lock test.
Only a complete, persisted synthetic result returns CLI success. The output file is exclusively
created with private permissions; an existing report is never overwritten. Evidence-save errors
raise after child cleanup and cannot produce a successful CLI exit.

## Failures exercised

Eight new tests cover supervisor crash, hung worker, an accidentally retained pipe writer,
missing recorder fence, an unadmitted late receipt, recorder exit failure after a valid fence,
existing evidence and evidence-save failure. All use real subprocesses where relevant.

The hung-worker test initially exposed an ordering bug: waiting for the recorder first could
force-kill it while it waited for the worker's data pipe. Cleanup now waits for or terminates the
owned synthetic worker before waiting for its recorder. It closes command streams, uses bounded
waits, and records every child exit and forced termination. Forced cleanup never passes the case.
This fixture may kill only its retained disposable Python peers; it defines no native app policy.

## Validation

```bash
python3 -B -m unittest discover -s tools/mac-control/Spikes -p 'test_*.py' -v
python3 -B tools/mac-control/Spikes/recovery_observer.py --output verification/mac-control/recovery-observer-2026-09-09.json
git diff --check
```

57 tests passed. Standalone CLI exited 0 and saved the linked trace. Whitespace check passed.
For another run, use a new output filename. No native build, app launch, input or TCC change ran.

## Native adaptation boundary and next step

These peers are siblings under the observer. The actual native worker is currently a child of
the supervisor and validates process parent/start identity. This fixture therefore proves pipe
EOF and recorder independence, **not** native parent-loss detection or compatibility with that
identity contract. Do not replace native launch ownership with the sibling topology to get a pass.

Next implement the between-complete-pairs worker-crash case in the native harness source, with
offline sequencing tests and independent evidence transport. Preserve existing parent/target
identity checks, keep the recorder alive, and reject automatic restart after intentional worker
death. A live attempt needs an agreed foreground window after that preparation. Supervisor-death
and held-key cases still require native ownership/cleanup design; the new fixture alone does not
authorize or validate them.
