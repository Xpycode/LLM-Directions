# E1 matched host replay — October 16, 2026

**Outcome: blocked/incomplete; no rollout recommendation.** Payload approval is recorded in
[host acceptance](../host-acceptance.md). Models/settings: Codex 0.163.0,
`gpt-6.1-sol`/medium; Claude Code 2.1.301, `claude-sonnet-5-5`/high.

244 active matrix attempts: 188 pass, 35 qualified, 11 routing-oracle failures, 10 provider-blocked.
Twenty additional Claude assays are not run. Process success is separate: 234 requests exited 0;
that does not make them 234 acceptance passes. Twelve earlier routing attempts are preserved as
superseded harness evidence, outside those 244 active attempts.

## Evidence

- [runs.json](runs.json): per-run configured initial files/bytes, actual retrievals, tool calls,
  changed files and independent judgments. Every attempt is reviewed, including provider failures.
- [representative-metrics.json](representative-metrics.json): medians/min/max for three fresh root
  repetitions of S01–S05 per host/source. Questions and redundant-validation findings are reviewed
  separately; repeated file reads are not automatically redundant validation.
- [routing-results.json](routing-results.json): all 60 frozen inputs in each corrected v3 assay,
  expected/observed paths, required-path coverage and exact-set matches. Additional relevant paths
  can satisfy coverage but reduce exact-set matches. No oracle was changed after observation.
- [pending.json](pending.json): ten incomplete Claude final workflow attempts (S19–S23 root/docs),
  twelve Claude routing assays and eight Claude consumer cleanup assays not run.
- [evidence-manifest.json](evidence-manifest.json): SHA-256/byte inventory of retained run artifacts,
  including inputs, initial files, invocation, raw stdout/stderr, broker audit and final project files.

Containing folder for Finder Go to Folder:
`/Users/sim/ProgrammingProjects/0-DIRECTIONS/__DIRECTIONS/verification/lean/host-replay-2026-10-16`
Open `README.md` there. Raw machine-local evidence is retained in
`/private/tmp/directions-e1.q0geNh`; the preserved archive location/hash is in `archive-info.json`.
Profiles and credentials are excluded from that archive. Temporary profile availability is not a
cross-Mac or future-authentication guarantee.

Archive containing folder:
`/Users/sim/ProgrammingProjects/0-DIRECTIONS/__DIRECTIONS/.archive/e1-2026-10-16-q0geNh`
File: `raw-evidence.zip` (17,273,808 bytes; SHA-256
`0e9f37857a9ba97dd90257b7213a59f9abbeea121f96064b306f8e605230e74b`).

## Interpretation and limits

All external app, process, test, build and Git operations were simulated; actual fixture file
reads/writes and before/after hashes were observed. This does not prove native app behavior,
real Git transport, physical-device acceptance or production-data isolation. Broker denials are
recorded, never scored as model adherence. No desktop control, live deployment, consumer mutation
or push occurred.

Initial bytes mean configured Directions entry files, not hidden provider/system context or proof
of every automatically loaded byte. Retrieval bytes count successful UTF-8 broker responses,
including repeated reads. Tool-call counts distinguish host events from broker audits. Concurrency
was bounded to four workflow fixtures per host/source; the initial calibration/first fixtures were
serial, and corrected routing used three concurrent fixtures per source/mode. Elapsed time is
descriptive only; no speed, token, price or statistical-significance claim follows.

Routing is batched path selection, not sixty independent feature implementations or proof that
every topical body was correctly applied. Consumer tests use retained instruction-only snapshots
and synthetic companion facts/code, with exact original backups; they are not live migration.
Corrected routing supplies a full disposable master for Directions and the exact observed cleanup
entry for each consumer. Earlier v2 routing copied a master entry without its master files and
cannot establish repository-only discovery quality. Its low scores are superseded, not a source
regression. Workflow/cleanup v2 remain usable because their master was explicitly supplied.

Acceptance findings remain open: routing misses/procedural body reads, two incorrect recorded
backup SHA-256 values despite intact originals, unsupported manual acceptance assumptions, a
single Claude master/project decision mix-up, and measured byte/call increases. See host acceptance
for the concrete results and scoped continuation. No broad suite or passed model run was repeated
to hide a failure; the twelve corrected routing reruns address an identified fixture defect.

## Continue

**Latest pickup, October 18:** the [cleanup checkpoint](../cleanup-2026-10-18.md) preserves this
evidence and supersedes the pilot pickup below. E1 remains open; pilot/upstream and Claude retries
stay parked. No new host batch is scheduled.

**Later local correction:** [follow-up](../codex-followup.md) records source changes and trusted
checksum receipts after this replay. These historical metrics and raw outputs remain unchanged;
the corrected source has not had a model replay. The current pickup is the bounded pilot proposal
and unresolved byte tradeoffs, with no new requests scheduled. The earlier review pickup below
is retained as chronological context.

**User deferred Claude on October 16 after quota exhaustion.** Codex is the primary host. No
automatic resume at quota reset and no automatic benchmark reruns. The next pickup is local review
of saved Codex findings; propose a small pilot/request budget before any further model-driven test
batch. The preserved thirty-row missing list remains deferred and does not imply acceptance.

Claude returned HTTP429 `usage_limit_reached`, reporting reset at **01:40 Europe/Berlin on
October 17, 2026**. No paid-credit/model/provider fallback or future automation was authorized.
Keep the existing payload approval and isolated authentication; do not repeat sign-in or copy
credentials unless authentication actually becomes unavailable.

Only if the user later resumes Claude, after reset verify source hashes, CLI version and fixed
model/effort, then use fresh fixtures for
the thirty entries in `pending.json`. Preserve failed S19 partial writes and zero-tool provider
failures. The local `claude-limit.json` guard must be reviewed after reset before new requests;
elapsed time alone does not establish successful provider availability. For routing, use the
reviewed `routing-replay.py` v3 layout after consumer cleanup artifacts exist, not the superseded
v2 routing generator. Never overwrite prior evidence or silently substitute settings.

Resolve evidence-quality/routing findings and obtain an explicit scoped decision on byte increases
before acceptance or rollout. Reuse valid passed evidence; rerun only affected cases for a stated
source, fixture, settings or provider-availability change. Live deployment and consumer rollout
retain their separate authorization boundary.
