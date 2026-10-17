# Saved-read attribution — October 17, 2026

Selected scope complete: analyzed the eighteen retained Codex root runs for S01 (status),
S04 (task-A-only closeout) and S05 (two-wave continuation), baseline/final with three repetitions.
No host request, benchmark rerun, desktop action, deployment or consumer edit. Historical scores,
sources, manifests and replay metrics remain unchanged; corrected-host behavior is unobserved.

## Evidence and accounting

[Computed receipts](receipts.json) record every successful file read, its one-based broker audit
ordinal, returned UTF-8 bytes, response hash, provenance category and previous-read/write markers.
[Analyzer](analyze.py) reads the retained archive without extracting or executing it. It verifies
the archive hash/CRC, ninety manifested audit/fixture/initial/prompt/answer files, every audited
response hash/byte count, per-run retrieval/call totals and the six published group medians.
Its repeat annotations are mechanical observations, not automatic judgments of waste.

Reproduce from the repository root with:

```bash
python3 -B verification/lean/read-attribution-2026-10-17/analyze.py
```

Raw evidence folder for Finder Go to Folder:
`/Users/sim/ProgrammingProjects/0-DIRECTIONS/__DIRECTIONS/.archive/e1-2026-10-16-q0geNh`
File: `raw-evidence.zip`. The ignored archive is machine-local; receipts do not guarantee its
availability on another Mac. Input inventories are in
`/Users/sim/ProgrammingProjects/0-DIRECTIONS/__DIRECTIONS/verification/lean/host-replay-2026-10-16`.
No authentication profiles or credentials are needed for this offline analysis.

Retrieval bytes below count successful `read_file` responses, including repeated reads. Listings,
writes and simulated-operation responses are excluded from that metric. Configured initial bytes
are the preserved entry-file inventory, not proof of automatic host delivery or hidden context.
The archival scratch-path totals differ from today's checkout-rendered entries.

| Scenario | Baseline retrieval median | Final retrieval median | Retrieval change | Configured + retrieval change |
|---|---:|---:|---:|---:|
| S01 status | 17,174 | 20,195 | +3,021 | +1,945 |
| S04 selected-task closeout | 48,269 | 54,352 | +6,083 | +5,007 |
| S05 two-wave continuation | 49,732 | 58,581 | +8,849 | +7,773 |

Configured entries are constant within each group: 12,105 baseline and 11,029 final, a reduction
of 1,076. Thus addition preserves these retrieval medians. These are descriptive source-byte
observations for n=3, not token, cost, speed or causal-efficiency estimates.

## Status: instruction growth, no demonstrated duplicate reads

All six status runs make eight file reads and one listing; none repeats a file read. Each baseline
run retrieves 4,586 skill + 8,207 status command + 3,615 project entry + 766 fixture-record bytes.
Each final run retrieves 5,115 + 10,141 + 4,173 + the same 766 bytes. The exact increase is
**529 adapter + 1,934 command + 558 repository-entry = 3,021 bytes**. No extra fixture evidence
explains this regression.

The archived adapters require reading the complete command. Of the status command's growth,
375 bytes are in the default section, 427 in arrival and 1,132 in collision handling. The latter
**1,559 bytes** concern conditional paths during an ordinary read-only status request, but they
were part of the mandatory command read. They are a prospective factoring opportunity, not
instruction-following failures or bytes proven removable without a source change.

The state, plan, tracker, index and current session handoff support the explicitly requested plan
selection, 0/2 count, unavailable-device gate and independently ready task. Reading the handoff
is justified by that explicit request. The sole index row and current anchored handoff could
potentially be narrowed by 124 bytes total with suitable range reads; that is a small scope
opportunity, not a cause of the 3,021-byte increase.

The repository entry also appears in the configured initial inventory. Its explicit read is
**uncertain as duplication**: the inventory does not establish that the host actually supplied
its contents. Do not subtract those 3,615/4,173 bytes as confirmed savings.

## Execution: larger guidance plus variable record work

One complete pass through the skill, execute command, log command, model guide and repository
entry is 43,880 baseline bytes. Final adds the required task-state reference and totals 46,918:

| One-pass instruction component | Baseline | Final | Change |
|---|---:|---:|---:|
| Directions skill | 4,586 | 5,115 | +529 |
| Execute command | 11,104 | 13,208 | +2,104 |
| Log command | 17,024 | 12,829 | -4,195 |
| Model guidance | 7,551 | 8,261 | +710 |
| Task-state reference | 0 | 3,332 | +3,332 |
| Repository entry | 3,615 | 4,173 | +558 |
| Total | 43,880 | 46,918 | +3,038 |

These reads follow the archived workflow's requirements, with the same entry-delivery uncertainty
noted above. The additional task-state contract covers canonical status, evidence, current handoff
and archive ordering. Removing it or required verification is not justified by this byte comparison.

The following table separates instruction reads (including any repeated instruction) from all
other fixture-file reads: records, text sources and the optional fixture explanation. It is an
exact additive accounting for each run, not a necessity classification.

| Scenario/source | Repetition | Instructions | Other fixture reads | Total retrieval |
|---|---:|---:|---:|---:|
| S04 baseline | 1 | 43,880 | 6,308 | 50,188 |
| S04 baseline | 2 | 43,880 | 4,004 | 47,884 |
| S04 baseline | 3 | 43,880 | 4,389 | 48,269 |
| S04 final | 1 | 46,918 | 8,292 | 55,210 |
| S04 final | 2 | 46,918 | 7,434 | 54,352 |
| S04 final | 3 | 46,918 | 4,279 | 51,197 |
| S05 baseline | 1 | 43,880 | 5,852 | 49,732 |
| S05 baseline | 2 | 43,880 | 5,511 | 49,391 |
| S05 baseline | 3 | 60,904 | 7,739 | 68,643 |
| S05 final | 1 | 46,918 | 5,787 | 52,705 |
| S05 final | 2 | 46,918 | 11,663 | 58,581 |
| S05 final | 3 | 59,747 | 5,335 | 65,082 |

The total-median-bearing S04 runs are baseline r3 and final r2: +3,038 one-pass instructions
and +3,045 fixture reads account arithmetically for +6,083. S05 uses baseline r1 and final r2:
+3,038 instructions and +5,811 fixture reads account for +8,849. This compares different runs;
it does not isolate a causal effect. In particular, independently median fixture reads for S05
are 5,852 baseline and 5,787 final. Adding those medians to independently median instructions
would not reproduce the median total. Matched-repetition retrieval deltas also vary:
S04 +5,022/+6,468/+2,928; S05 +2,973/+9,190/-3,561.

Task acceptance requires post-edit source reads; completing S05 also requires retained plan/evidence
and valid incoming links before retirement. Archival itself was required in both versions; the
final task-state contract makes link verification before retirement explicit.
Changed plan/state/tracker/log/index readbacks serve
that verification. Historical reviewers accepted these outcomes, including the archive/compatibility
pointer when the broker lacked move/delete. Record-length differences and multiple updated log
versions contribute to the variable fixture totals. The evidence does not justify treating all
record growth, repeated reads or whole-record verification as removable overhead.

## Confirmed opportunities and limits

Audit references below mean `runs/<run>/evidence/audit.jsonl` inside the archive. Ordinals are
one-based and are reproduced in receipts. Each listed pair has identical response hashes with
no intervening write to that file.

| Run | Later audit event ← earlier | Bytes | Disposition |
|---|---|---:|---|
| codex-baseline-S05-root-v2-r3 | 11 ← 9, commands/log.md | 17,024 | Avoidable unchanged procedure reread |
| codex-final-S05-root-v2-r3 | 10 ← 8, commands/log.md | 12,829 | Avoidable unchanged procedure reread |
| codex-final-S04-root-v2-r1 | 32 ← 29, session log | 1,875 | Reuse retained content before appending check results |
| codex-final-S05-root-v2-r2 | 39 ← 34, session log | 2,555 | Reuse retained content before appending check results |

Later reads of the newly amended logs verify different bytes and are reasonable. Other unchanged
source reads are tiny (23-byte sample, 14/16-byte other file); original reviews already distinguish
required per-task acceptance and untouched-file preservation from extra source revalidation. For
example, S04 final r1 events 25/26 repeat accepted source reads (37 bytes); S05 final r1 events
37/38 repeat both accepted source reads (39 bytes). Retain the first post-edit acceptance and
needed scope-preservation check; reuse their results if only documentation changed afterward.
The receipts enumerate other unchanged responses without declaring all of them avoidable.

The original reviews also flag repeated simulated diff/status validation. Those responses affect
calls and all-returned bytes, not successful-file retrieval totals. Later record edits justify
checking changed documentation; they do not require repeating unchanged source acceptance.
The model guide and full command bodies were required reads; their conditional/host-specific
portions can be reviewed for factoring, not silently skipped in these old runs.

These examples overlap the run totals above. They must not be added to median differences as an
independent savings estimate. No saved run has been rescored and no counterfactual host replay
establishes the effect of removing them.

## Validation and ownership

Fresh task contexts independently analyzed status and execution traces; the coordinator integrated
their findings and owns this report/accounting. A separate fresh read-only reviewer reproduced the
receipts and checked the claims against raw events. Its optimized-Python finding is fixed: the
analyzer explicitly refuses execution when assertions are disabled. Normal output reproduces the
retained JSON byte-for-byte; `PYTHONOPTIMIZE=1` exits nonzero before emitting claims. The reviewer
confirmed this narrow correction with no remaining findings. This is local evidence verification,
not a host replay or independent acceptance of the source changes.

## Next local step and acceptance boundary

Prioritize a compact ordinary-status command with arrival/collision detail loaded through one
canonical conditional reference. Preserve complete reading of the command entry, all mode routing,
repository identity, known-concurrency warnings and the Codex detector limitation. Validate local
entry/reference paths and disposable boundary fixtures; a new host request is a separate scope.
The status evidence supports this narrower change more directly than another broad benchmark.

For future execution tuning, retain already-read unchanged procedures and batch closeout record
updates before one final changed-record verification; preserve required task acceptance, archive
ordering and recovery checks. These recommendations are prospective, not accepted byte tradeoffs.

Local analysis does not pass E1. Thirty Claude observations remain deferred; corrected-host
behavior, standalone/complex-path tradeoffs and transport admission remain open. Pilot/upstream
and Mac-control work stay parked. No rollout, deployment or push follows this report.
