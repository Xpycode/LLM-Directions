# Independent focus-loss case — passed September 9

User requested a retest after the worker shutdown fix. One fresh two-minute window ran.
**Complete case passed**, including successful shutdown. Task 1.3/Gate A remain incomplete for
other recovery, clipboard and intervention requirements.

## Preparation and exact run

Reconciled the prior unresolved marker under the exclusive private lock after checking the raw
trace hash/rows, reconstructing all12 event receipts/origins/prefixes and input closure, rechecking
focus/observation fences, confirming all recorded child exits, and scanning for remaining processes.
Preserved the reconciliation audit before syncing the clean marker. This is evidence-specific
reconciliation of the retained crash, not general crash recovery or a successful prior test.

Fresh corrected artifact directory: `directions-stop-build.hgLdR5`; built with Swift6 complete
concurrency checking. Permission preflight all true; no old spike processes. Ran:

```bash
python3 -B tools/mac-control/Spikes/client.py --artifacts /var/folders/ly/b2sk443n0hq1_z9mgf4q8f4w0000gn/T/directions-stop-build.hgLdR5 --case focus-loss
```

Actual session used approved outside-sandbox execution. Machine M1-Max, macOS27.0 (26A5425a),
Apple Swift6.3.3, Python3.14.7. The supervisor verified all three executable hashes before launching
the exact artifacts. The original text target bound successfully and the separate sink activated.

## Measurements and cleanup

- Six correct sample characters; 12 admitted, posted, received and origin-verified events.
- Independent stop reason `wrongFocus`, cause `frontmost`.
- Activation request to detection upper bound **11.248584 ms**.
- Input drain **0.04275 ms**; no held keys or duplicate receipts.
- Zero input events received by sink; no original-target reactivation; focus sampling and both
  observation fences passed. Post-stop observation **2050.909833 ms**.
- Worker72370, sink72371, target72372 all exited0. Client/supervisor exited0; `casePassed:true`.
- Final process scan empty, marker clean; screen control ended. No further case ran.

[Portable trace, client evidence, artifact hashes and reconciliation audit](focus-loss-2026-09-09.json).
Runtime trace `directions-stop-spike-7zk1iueq`; client `directions-stop-client-95eenml3`.
No source changes in this retest, no TCC/install/deployment/commit changes. Finite observed focus
and delivery measurements do not establish all OS conditions, generic recovery or provider integration.

Next: prepare the remaining crash/hung-call recovery experiments offline, maintaining the same
supervised-window requirement for live input. Clipboard and broader intervention proof also remain.
