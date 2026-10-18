# LE13 — final local integration

**October 18 checkpoint:** [cleanup verification](cleanup-2026-10-18.md) records current source
sizes and checks. October 17 “current” measurements below remain dated historical snapshots.

October 16, 2026. Local source/fixture acceptance only; E1 remains open. The coordinator integrated
fresh agents' owned changes; no live deployment, consumer migration, desktop control or push.
Source snapshots and their SHA-256 manifest remain unchanged. At this integration checkpoint,
the unrelated Mac-control plan and initially dirty numbered guides matched their frozen bytes;
its task 1.3/Gate A remain open.

## Current checkpoint boundary — October 17

Latest scope update: user accepted the listed source-size increases and authorized
[local deployment and instruction routing migration](rollout-2026-10-17/README.md). Both tools and
110 consumer roots are refreshed. Earlier rollout-pending wording below describes the preceding
checkpoint; E1, historical runtime regressions and corrected-host behavior remain unverified.

Local corrective sources are committed in `dc9ce95`; reviewed guidance is committed in
`3407355` and `b9c2a89`. See the [cleanup review](local-cleanup-review.md) and
[guidance provenance](../guidance-review-2026-10-17/README.md). The integration guard now uses
explicit reviewed receipts for five intentionally changed guides/profile; the Mac-control plan
still matches its frozen pin. Historical manifests and the tables below remain unchanged.
Current rendered entries are **11,238 Codex / 18,686 Claude bytes**, versus **12,120 / 19,748**
frozen bytes. See [current accounting](codex-followup.md#reviewed-byte-tradeoffs--current-candidate).
The partial [host replay](host-acceptance.md) observes the older source; corrected-host behavior,
E1 acceptance and rollout remain open. Pilot/upstream work is parked.

## Validation

`bash verification/lean/run-checks.sh` runs the final sources together: 85 baseline hashes,
16 session-index cases, 50 generator invocations, 12 retirement cases, producer/process safety,
eight task-state cases, 40 deployment invocations, 47 domains/60 cases/480 static routing rows,
final actual template routes/reference paths, preservation checks, shell syntax and diff whitespace.
Deployment runs only in disposable masters/homes. Consumer inventory is read-only; the old website
checker is replayed on disposable sessions. See deployment.md for the retained hashes and recipes.

Integration corrections: the first final-source test counted four deliberate safety references
as duplicate domain rows; its matcher now counts only routing bullets. Final Claude global+repo
bytes initially regressed by 26; redundant repository prose was shortened, preserving the fallback
and safety text. The task-state archival fixture now starts with an accepted plan, updates a real
Markdown evidence link and the state/tracker pointers before retirement, and retains original bytes.
The optional context reference's policy-pending sentence was reconciled with the accepted decision.

LE14 then found and resolved two P2 issues: plain logging now has a valid current Resume target
when pickup changes; Claude preflight validates effective merged hook settings before any install
write. The hook correction also applies empty-container template changes consistently with its
preview. The original aggregate suite passed with 20 deployment invocations; the affected expanded
deployment suite then passed 40, plus eight task-state tests, final routing/reference preservation,
shell syntax and whitespace. The independent reviewer replayed three malformed-setting cases,
all rejected with unchanged disposable homes. No redundant whole-suite rerun is claimed.
See final-review.md and final-source-manifest.json for dispositions and source provenance.

## Final byte accounting

Historical integrated candidate, before the October 16 corrective follow-up. See
[current candidate accounting](codex-followup.md#reviewed-byte-tradeoffs--current-candidate):
the first corrective pass added 185 bytes per host; later Claude cleanup reduced its entry.
The task-state reference remains 385 bytes above this historical version.
The following tables remain unchanged as historical evidence.

UTF-8 source bytes, not tokens, elapsed time or observed host reads. Render global placeholders
with this checkout's absolute master path. Initial totals include the host's repository entry file.
The frozen baseline had no repository CLAUDE.md. LE07's candidate report remains an experiment;
these final integrated numbers supersede it for implemented source.

| Initial instructions | Frozen | Final | Difference |
|---|---:|---:|---:|
| Codex global + repository | 12120 | 11053 | -1067 |
| Claude global + repository | 19748 | 19606 | -142 |
| Repository only, Codex | 3615 | 4173 | +558 |
| Repository only, Claude | 0 | 1483 | +1483 |
| Context guide | 33813 | 7201 | -26612 |

The optional context examples retain another 10287 bytes, loaded only when needed. Standalone
topical fallback may additionally read the global template's routing section; actual host read
extent is unknown. Standalone increases are explicit unresolved rollout tradeoffs.

The following workflow subtotal includes command files, the mandatory task-state reference when
progress changes, and triggered logging references, once each. It excludes project data, indexes,
model/testing/multi-Mac guides and entry files from both sides; it is not total session context.
Final log is 12829 bytes, execute 13208, task-state 3332, app reference 4225, Mac reference 3387,
Claude reference 1471. Frozen log/execute are 17024/11104.

| Scenario subtotal | Frozen | Final | Difference |
|---|---:|---:|---:|
| Ordinary log, no progress change | 17024 | 12829 | -4195 |
| Ordinary log with task-state update | 17024 | 16161 | -863 |
| Codex execution ending, task progress, no app trigger | 28128 | 29369 | +1241 |
| Claude execution ending, task progress, no app trigger | 28128 | 30840 | +2712 |
| Codex Mac + recovery handoff, task progress | 17024 | 23773 | +6749 |
| Claude Mac + recovery handoff, task progress | 17024 | 25244 | +8220 |

These increases include new authority, recovery and canonical-record safeguards. They are reported,
not accepted on the user's behalf. Ordinary-path bytes improve; every-path efficiency is not claimed.
At this checkpoint, runtime tool calls, files written, unnecessary questions, repeated validations,
model recall, constraint loss and speed were **unavailable**. Later partial observations are in
[host acceptance](host-acceptance.md); they do not measure the corrected candidate or close E1.
Fixture writes are confined to scratch
paths and deterministic fixture call counts are not substituted for those runtime metrics.

## Complete frozen scenario disposition

All rows are source walkthroughs unless an executable fixture is explicitly named. They cover
root and docs layouts through migration.md and the deployment/setup fallback contract. None closes E1.

| Cases | Local evidence and result | Remaining observation |
|---|---|---|
| S01 status; S21 failed directory change | collision.md: plain read-only path, identity and detector limitations pass | Actual host routing and calls |
| S02 small fix with limits; S16 bounded spike | granularity.md and policy-and-migration.md: limits, result/work limit/exit pass | Proportional host behavior |
| S03 ordinary log; S04 selected task; S05 continuation; S06 independent blocked task | logging.md + execute/log final review: correct scope, continuation and genuine-end closeout | Actual outputs and unnecessary questions |
| S07 Mac handoff; S08 keep-running; S09 no-control build; S13 expired recovery; S22 scoped control | control-authority.md and canonical app/Mac references: explicit scope and original-Mac obligations retained | Safe simulated host replay, no live control implied |
| S10 app-hosted tests; S11 absent backend; S12 destructive test setup; S17 finite acceptance | test-safety.md: inspect effects, disposable data, backend check and finite batch pass | Host selection/acceptance behavior |
| S14 failing producer | Executable fixture preserves exit 7 despite formatter 0; PID/start/executable checks reject wrappers and stale identity | Host reporting of actual failure |
| S15 current Resume; S18 plan selection; S19 interruption; S20 manual gate | Eight disposable task-state fixtures and migration walkthrough: counts, history, interruption, gate and archive ordering pass | Actual command instruction-following |
| S23 copied web instructions | deployment.md + old checker fixture: website invariants and unique content retained, cleanup recipe prepared | Snapshot-only host cleanup rehearsal |

AC01/AC02/AC10 have executable local evidence. AC03 has static lifecycle/link evidence. Other
criteria retain their E1 gate. Fresh-agent delegation remains the accepted default; no new
dispatch exception or observed dispatch-efficiency claim was introduced. Rollout is not recommended
until host acceptance and the explicit byte tradeoffs are resolved. See host-acceptance.md.
