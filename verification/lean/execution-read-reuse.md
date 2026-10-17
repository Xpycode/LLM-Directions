# Execution/log read reuse — October 17, 2026

Selected local review and guidance scope complete. The retained [read attribution](read-attribution-2026-10-17/README.md#confirmed-opportunities-and-limits)
supports reusing unchanged complete procedures and batching closeout amendments. It does not
support removing required source acceptance, changed-record verification or archive ordering.

`commands/log.md` now owns the narrow reuse rule: complete first reads remain required; reuse
requires the same canonical identity, unchanged content and complete retained task/context.
Changed identity/content, incomplete/compacted context or uncertainty requires rereading. Fresh
agents perform their own required reads. Authorization and recovery triggers are checked against
current scope independently of retained instructions. Records inherit the same safeguards.

Known closeout amendments may be batched before final changed-record readback and link validation.
Another record change requires another verification. Post-edit source acceptance and archive/link
verification before retirement remain required. Later documentation-only edits do not require
repeating still-valid source checks. `commands/execute.md` Step 4 points to the log's reuse rule
while retaining automatic pre-clear close and complete first use. No adapter, cache or runtime
mechanism was added, and no initial command-read requirement was removed.

## Evidence and validation

The saved report identifies identical, unwritten procedure rereads (final S05 r3 audit 10 after 8)
and log rereads before amendment (final S04 r1 audit 32 after 29; S05 r2 audit 39 after 34).
Later reads of changed records remain justified. Those historical events motivated this wording;
none has been rescored, and their bytes are not counterfactual savings or additive median effects.

One fresh-context task owner edited the coupled commands. Coordinator clarified record safeguards
and owns integration, report, records and Git. A separate fresh read-only reviewer read both full
commands and saved evidence. The record-safeguard ambiguity identified during review was resolved
by explicitly inheriting the procedure conditions. Final review reports no remaining findings;
index readback still respects targeted access and the prohibition on whole-index format reads.

Validation: reviewed the complete source diff against first-read, stale-context/concurrent-edit,
fresh-agent, changed-record, source-acceptance, archive and recovery cases; ran
`python3 -B verification/lean/test-integration.py` (47 routes, recursive shared references, reviewed
guide pins and unchanged Mac-control plan) and `git diff --check`, both passing. Reviewer also
ran scoped whitespace validation. No new test mirrors these prose rules. Unchanged baseline,
deployment, routing and unrelated fixture suites were not rerun.

Executed UTF-8 byte counts against parent checkpoint `77a673d`:

| Command | Before | After | Change |
|---|---:|---:|---:|
| execute | 13,208 | 13,317 | +109 |
| log | 12,829 | 13,709 | +880 |

This adds 989 instruction bytes to clarify reuse and required safeguards. It establishes no
observed reduction in host reads, tokens, runtime or cost; the net runtime tradeoff is unmeasured.
Historical replay/manifests/receipts remain unchanged. E1 remains open; no rollout recommended.
No host/provider request, network test, desktop/app control, consumer migration, deployment or push.

## Next boundary

The identified narrow status/reuse source follow-ups are locally complete. Review remaining E1
host-evidence gaps and byte tradeoffs before selecting acceptance work. No further host batch is
scheduled; pilot/upstream, thirty Claude observations and Mac-control recovery remain parked.
