# Native wire and durable acknowledgement adapter

September 9, 2026 · offline preparation · Python 3.14.7.

`recovery_native.NativeFrames` translates the existing Swift worker/target wire format within
`OwnedEvidence`, which remains the sole reader of its retained child pipes. It preserves actual
post/receipt kinds, event order, origin PIDs and checkpoints. Launch identity and tag base must
come from trusted pre-input setup, never a report. The tag establishes sequence; it does not
manufacture an event kind. Unknown messages, wrong source/run, malformed timestamps, nonempty
held state, invalid target PID and nonadvancing text receipts reject.

Native mode requires an explicit clock because Swift uses `mach_continuous_time`. The caller must
use that domain for context probes, verifier transaction boundaries and wait/EOF observations too.
Every raw frame, including allowed diagnostics, counts against the existing 1024-row bound.
No unlimited heartbeat stream can evade that bound; exhausting it blocks verification.

`Admission.poll` now returns the exact successfully validated writer acknowledgement bytes once.
The final resolved bytes can be bound to already collected independent evidence while both owned
children are still alive. Reading a restart snapshot cannot substitute for this acknowledgement.
Existing dispatch/Stop behavior is unchanged; current supervisor callers ignore the new return.

`OwnedEvidence.finish_target` closes only the retained target stdin after an acknowledged fence.
The Swift target intentionally keeps recording after observeEnd. Continued reads through actual
EOF and an owned wait remain mandatory; neither the fence nor stdin close is exit proof.

## Validation and review

Twelve new tests use Python subprocesses emitting the native Swift schemas, real pipes, a real
private RecordWriter and the actual admission acknowledgement return. They cover successful
translation/fence/EOF/wait, wrong kinds/origins, duplicate and late receipts, failed target exit,
early target close, post-exit receipt binding, malformed/forged frames, diagnostic limits and
native clock selection. Synthetic peers substitute monotonic time for the native continuous clock.
The observation interval is shortened in these transport fixtures; the existing normalized
integration retains its real two-second check. These are not native compatibility measurements.

The writer test replays admission/storage transitions against collected receipts; it does not
exercise native dispatch admission timing. That remains covered only by existing synthetic
supervisor integration until a new native test window is agreed.

Independent review found that a matching prefix alone could admit empty/unchanged text. The
adapter now requires cumulative keyDown text progress, and regression tests reject both cases.
The reviewer confirmed the correction and reran all 12 native transport tests successfully.
Final full suite: **198 tests in 26.788 seconds — 197 passed, one existing sandbox boot-query
skip**. Whitespace validation passed; no native execution was performed.

```bash
python3 -B -m unittest discover -s tools/mac-control/Spikes -p test_recovery_native.py
python3 -B -m unittest discover -s tools/mac-control/Spikes -p 'test_*.py'
git diff --check
```

## Exact next integration boundary

The live supervisor still reads native stdout itself. Do not attach a second reader to those
pipes: readers would split evidence. Next bounded work is a single-reader supervisor integration
that delivers native frames to its existing safety state machine and the owned evidence collector,
with explicit ownership of stream framing, EOF and waits. Route the exact final `Admission.poll`
bytes to binding before `maybe_crash`, and gate that fault on successful independent binding.
Retain parent identities, Stop/watchdogs and nonblocking I/O. Align the context probe and transaction
with the existing `mac_clock()` domain. Add synthetic supervisor integration tests for success,
late/absent acknowledgements, stream pressure, early exits and Stop while a write is pending.

This collector lives in its owning process; it does not yet survive supervisor death. Do not
replace parent supervision with the earlier sibling-process observer topology or claim broker
crash recovery. Native inventory visibility, builds/launches and live recovery need their own
agreed validation window. Historical marker remains unresolved and untouched. No Swift edits,
native launches, commits or pushes occurred in this continuation. Task 1.3/Gate A remains open.
