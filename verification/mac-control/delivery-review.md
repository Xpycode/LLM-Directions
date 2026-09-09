# Delivery review — shortest path to a usable pilot

September 9, 2026. Repository review only; no new runtime evidence.

## Finding

The next deliverable is a runnable, reviewable native recovery procedure. The existing recovery
modules have substantial offline coverage, but their deployment locations and native caller are
not yet validated together. Resolving the historical marker permits a new experiment; it does not
prove crash recovery or complete task 1.3. The recorded 339 passing tests measure supporting
behavior, while the production queue, approval UI and client workflow remain unbuilt.

The shortest path supported by the current plan retains one controlled CLI executor route on the
first Mac. That route must still cover the specified actions and cancellation behavior. Printable
ASCII into the disposable target alone is insufficient for the requested cross-project UI tests.
Wait/Review, clipboard cleanup, fresh-build handoff and two-client exclusion remain requirements.
No task, acceptance criterion or gate is removed by this review.

## Delivery sequence and observable exits

| Step | Work | Exit evidence |
|---|---|---|
| 1. Finish native preparation | One explicit caller procedure using existing provisioning, observation and activation APIs; validate disposable storage at the selected local locations | Exact invocations, trusted inputs, location/flush results and failure outcomes are reviewable; no authority inferred from surviving reports |
| 2. Resolve the legacy startup block | Verify a separately agreed later boot and original namespace continuity; review read-only proof, then separately authorized initialization/activation | Retained completion witnesses and one-shot admission; historical crash remains failed/unknown |
| 3. Prove recovery with current binaries | Prepared compile/foreground window; fresh worker-crash experiment with durable checkpoints, then broker-death, hung-action and held-key cases | Actual-session stop/recovery evidence, no late input, owned exits and blocked stale retries |
| 4. Close the remaining compatibility cases | Permission/monitor loss, sleep/lock, target replacement, broader text and clipboard ownership/conflict; verify the required action path | Each remaining task 1.3 requirement has measured evidence; Gate A can be reviewed |
| 5. Build the usable workflow | Existing Waves 2–5: ownership/queue/time, enforced actions and fresh-build handoff, native Yes/No/Wait/countdown/Stop, then real CLI clients | Gate B enforcement and Gate C actual-client workflow; two clients cannot overlap |
| 6. Package and pilot | Existing Waves 6–7: packaging, install/update/removal checks, acceptance and independent review | Exact first-Mac artifact and recorded user workflow; unsupported providers/environments explicit |

Recovery must also prove a second legitimate run after successful cleanup. Legacy activation is
permanently one-shot; the current supervisor's ordinary startup rejects retained bootstrap/
activation artifacts even with a clean marker. A resolved-ledger startup path is therefore an
explicit recovery delivery gap. Demonstrate it before claiming repeatable pilot readiness; do not
remove artifacts or reuse the activation receipt to obtain that result.

These are delivery checkpoints within the existing 25-task plan, not additional backlog tasks.
The full pilot still depends on the planned gates. There is no evidence-based delivery date yet;
the first useful scheduling measurement is completion or a concrete failure of steps 1–2.

## Next bounded work packet

Prepare one native-preflight entry point and its invocation/report before adding another recovery
subsystem. Reuse `recovery_provision`, `recovery_probe`, `recovery_retention` and the existing locked
snapshot APIs. Keep disposable storage validation separate from read-only historical inspection.

Required inputs and outputs:

1. Explicit evidence and independent anchor roots, following the proposed locations in
   [persistent provisioning](persistent-witness-provisioning.md). Establish whether those exact
   locations are machine-local and excluded from synchronization; the API cannot infer this.
2. Disposable transaction directories only for the storage action. Record canonical paths,
   ownership, modes, identities, native flush results and fresh-process reload. Preserve failures;
   do not retry by repairing or reusing a partially created transaction.
3. Explicit historical namespace and original baseline/history acquisition provenance for the
   read-only action. Check that independently retained trust inputs actually remain available.
   A hash newly computed from a repository report is not a substitute.
4. Under `MarkerLock.acquire(..., create=False)`, collect bounded native context and complete
   inventory, compare the required boot/namespace continuity, and report unchanged marker bytes
   and fingerprints. Same boot, missing/replaced namespace, unreadable inventory or missing
   provenance is a named failure, with no initialization or launch.
5. Exercise rejection paths in private fixtures and a successful disposable provision/reload.
   Stop preparation when the command and report are usable. Only a reproduced failure of this
   concrete path justifies additional supporting implementation.

The read-only report must make the next native operation reviewable before requesting it. Do not
request a reboot until provenance and the exact procedure are ready. The current design requires
the original temporary namespace to survive that transition; if it does not, this path fails and
requires a separate explicit design decision. Recreating the marker elsewhere is not a shortcut.

Native storage writes outside the workspace, a boot transition, marker mutation, and compilation/
foreground experiments retain their existing separate authorization boundaries. This review
performs none of them. The plan explicitly requires an agreed window for spike compilation/run.

## Validation and limits

Reviewed the active plan, specification, latest pre-clear handoff, provisioning/caller reports,
activation contract, native baseline report and spike limitations. Existing offline results are
historical; no test suite or Swift build was rerun for this documentation review. Progress remains
2/25 plan tasks, 0/2 sprint tasks and 8/32 overall.

Independent review identified the temporary-namespace survival risk and one-shot/repeat-run gap;
both are incorporated above. The supervisor's ordinary startup rejection was also checked in code.
