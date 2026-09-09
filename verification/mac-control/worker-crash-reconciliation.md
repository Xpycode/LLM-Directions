# Worker-crash reconciliation review

September 9, 2026 · offline review of the [retained native case](worker-crash-live.md),
[`Protocol.md`](../../tools/mac-control/Protocol.md) supervision/recovery contract,
`StopSpikeWorker.swift`, and the spike's lock and trace implementation.

**Decision for this evidence: retain the unresolved marker.** No native execution, marker write
or retry is part of this review. The trace remains useful fault-detection evidence, but does not
meet the existing recovery contract. Task 1.3 and Gate A remain incomplete.

## What the retained trace establishes

The live audit verified twelve distinct admitted, posted and received tags, correct source PIDs,
six valid prefixes, all event timestamps before the kill-call bracket, no later admission, target
observation acknowledgement, worker exit -9 and target exit 0. The client mirror exactly matches
all 114 journal rows. The observed loss-detection upper bound is 1.794583 ms. A post-run process
scan found no remaining named spike processes. These findings are not discarded by this review.

## Why it cannot release the current marker

1. **A posting acknowledgement is earlier than the worker's state update.** In `receive`, the
   key-up path calls `post`, which emits `posted`, and only after it returns sets `held = false`.
   The supervisor can observe that acknowledgement and the target receipt before this assignment
   runs. The current trace therefore cannot establish the worker's final internal held-key state.
   Balanced target receipts are valuable evidence, but are not a recorded cleanup checkpoint.
2. **The marker has no run identity.** Its only values are `clean` and `unresolved`. It records no
   boot/session identity, run ID, worker start identity, artifact identity or last admitted boundary.
   It cannot prove that an arbitrary retained report describes the uncertainty of the current
   marker. This session's known history is not a durable restart contract.
3. **The trace is not a pre-dispatch recovery ledger.** It is buffered in the supervisor and client,
   then saved after teardown. Worker-only death preserved it in this run. Supervisor/client loss
   could remove the evidence needed to reconcile an already-admitted event. The protocol requires
   uncertainty to be durable before dispatch and forbids incomplete state from proving idle.

Earlier focus-loss reconciliation is not a precedent for waiving these gaps: those retained cases
had a worker stop acknowledgement with empty held keys (or no admitted input), plus specifically
reviewed process-exit and trace evidence. This intentional worker death has no such acknowledgement.

The production protocol permits reconciliation when worker exit and all event/held-key uncertainty
are resolved; it does **not** require a dead worker to return an impossible late acknowledgement.
What is missing here is an independently verifiable replacement proof, not permission to ignore
the missing acknowledgement. Elapsed time, a matching PID lookup or a new broker generation cannot
provide that proof. A verified new boot is a separate protocol path and must be recorded as such;
this review neither requests a reboot nor assumes one occurred.

## Next bounded spike change

Add a **between-pairs recovery checkpoint** and a **versioned run record** in the isolated spike,
with offline tests before any native compile/run. Keep the production package and UI gated.

- Worker emits a distinct checkpoint only after a matching key-up post has returned and local
  `held` is false. Include run identity, last completed sequence/tag and held-key state; no text.
  Do not reinterpret existing `posted` rows as checkpoints or manufacture one for the old trace.
- Supervisor requires that checkpoint and matching target receipts before the controlled kill.
  A checkpoint is evidence about that boundary, not authority to skip normal dispatch checks.
  Any subsequent admitted event makes the previous checkpoint insufficient for recovery.
- Under the existing exclusive private lock, persist boot/session and run identity, owned process
  start/code identity and an explicit uncertain event boundary before enabling input. Persist the
  resolved checkpoint only after both worker state and target receipts agree. Crash/partial-write
  cases must leave the record unusable for automatic retry. Store no payload or capability.
- Design storage outside the timing-critical cancellation path. A bounded durable write may hold
  **new admission**; Stop and watchdog handling must remain serviceable. A synchronous per-event
  fsync in the current single-threaded supervisor loop does not meet that requirement.
- Build the record parser and transition tests with temporary files, fake identities and simulated
  receipts. No filesystem path from a report may become permission to signal a process. Runtime
  mutation requires the live lock and independently verified current identity.

This is a replacement proof to develop and verify, not a declaration that a checkpoint alone
establishes OS event quiescence. Native receipt/observation and process-exit evidence still apply.
The existing plain unresolved marker must stay blocked under the new parser; do not migrate it
to a clean record or attach a fabricated run identity.

## Required offline cases

| Evidence/state | Required decision |
|---|---|
| Current retained trace, no checkpoint or run-bound ledger | Preserve evidence; reconciliation blocked |
| Twelve matching receipts but last key-up post has not returned | No checkpoint; injection/recovery blocked |
| Checkpoint before latest admission, mismatched tag/run or duplicate receipt | Reject reconciliation |
| Truncated/corrupt/legacy marker, unknown boot/session or process-start identity | Block; never assume clean |
| Durable write fails or acknowledgement arrives after record changes | No new dispatch; close admission and retain uncertainty |
| Complete current-run checkpoint and receipts, but worker still live/identity ambiguous | Block reconciliation |
| Complete bound record, independently verified exit, resolved input/held state and observation | Candidate for native verification; never replay old input |

## Review result

Source and saved evidence were inspected; Markdown whitespace validation passed. No new runtime
tests were needed for this documentation-only review. The 61 offline tests and one native crash
observation remain the verification baseline. Next implement the versioned record parser and
transitions offline, then the worker checkpoint and nonblocking persistence integration.
