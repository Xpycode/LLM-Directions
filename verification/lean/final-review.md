# LE14 independent integration review

October 16, 2026. Fresh independent task context; inherited model, no further agents. This review
inspected the active master instructions, LE14 contract, final implementation and integration
evidence, recent implementation commits, and frozen baseline source. Archived consumer snapshots
were treated as evidence, not active instructions. Only this report is owned by the reviewer.
No live deployment, consumer migration, Git mutation or app/desktop control was performed.

## Findings and disposition

### R1 — P2: plain logging lacked a valid current-handoff target — corrected

`commands/log.md` §1 restricted Resume to pre-clear mode, while its new §2 required a specific
Resume anchor and `reference/task-state.md` explicitly allowed plain logging to refresh the current
pickup. A plain log after changed facts could therefore retain stale pickup instructions or link
to a nonexistent section. The frozen log did not have the new current-pointer requirement; this
was an integration contradiction rather than a demand for additional closeout ceremony.

Returned to coordinator. The coordinator changed the template and §2 to permit a uniquely
identified Resume with changed pickup and obligations in plain mode, explicitly without the
pre-clear-only model/sync ceremony. Reviewer reread the corrected source and traced plain/no-change,
plain/changed-pickup and pre-clear paths against `reference/task-state.md`; the contradiction is
resolved at source level. Host behavior remains E1. Integration must include the additional 123
log bytes in its workflow subtotals.

### R2 — P2: Claude settings preflight accepts a deterministic hook failure — corrected

`redeploy.sh` checks that existing `hooks` is an object, but does not check the event/group shape
consumed by `hooks/install.sh`. Disposable reproduction: seed a fresh home with
`{"hooks":{"SessionStart":42}}`, copy the master into scratch, initialize only that disposable
master's Git metadata, and invoke its redeployer. Result: exit **5**, **13 commands installed** and
**CLAUDE.md created**, followed by jq `Cannot iterate over number (42)`. No live home was used.

This is a predictable malformed-input failure, distinct from the documented absence of rollback
for later I/O failures. The new preflight claims validation before installation writes, so it
should validate the hook consumer shapes/expressions against the effective merged settings before
copying commands, including settings produced by the preference template.

Returned to coordinator/LE09 owner. The correction stages the recursive preference and permission
merges, validates every hook event/group/entry and status-line object, and exercises the installer's
lookup/append expressions before installation writes. It also ensures empty object/array preference
changes are actually installed, so the live merge matches the validated preview. Expanded deployment
fixtures cover malformed live and template settings, skip-settings, and a valid structural repair.

Reviewer independently reran the original disposable reproduction against corrected source, its
`--skip-settings` variant, and malformed hooks introduced only by the template: all three now exit
**1** before writes, with the complete disposable-home inventory unchanged. The correction and
fixture diff were inspected. R2 is resolved; the expanded-suite result is recorded by LE09/integration,
not claimed as reviewer execution. Later I/O failures still retain the documented nontransactional
boundary.

## Preservation and workflow review

- The checker retains live/archive union semantics, linked-target precedence and visible orphan
  evidence; the conflict-name correction includes digits/underscore/dot/hyphen and avoids repeated
  conflict-row insertion. The targeted fixture's byte/order assertions cover retained evidence.
- Task ownership is consistently selected-plan path plus ID. The new canonical reference retains
  originals before reconciliation, publishes verified pointers before mirror retirement, and keeps
  incomplete acceptance active. The eight tests are disposable record-contract rehearsals, not a
  Markdown migration engine. The archival test now exercises a real evidence link and preserves
  original bytes. Existing Mac-control records are not migrated by this work.
- Execute retains whole-plan continuation, selected-scope boundaries, fresh task ownership and
  genuine-end automatic logging. No-agent/no-commit restrictions and independent blocked tasks
  remain explicit. Current handoff supersedes historical Resume blocks without deleting recovery.
- App-control references preserve exact-target authorization, newer no-control restrictions,
  keep-running exceptions and original-Mac recovery. Test guidance separates source/build success
  from app-hosted/manual acceptance. Passing fixtures do not authorize launch or cleanup.
- Generator eligibility is shared across detailed and inline formats. Validation precedes marker
  replacement; outside-marker bytes and contamination are retained. Codex separately validates
  its outer managed markers and preserves personal bytes. Claude whole-file replacement remains
  explicit and backed up. Neither deployer should be described as generally transactional.
- Collision narrowing preserves arrival, known concurrency and mutation boundaries; Codex's
  detector limitation is explicit. There is no unsupported no-collision inference from silence.

No further material source findings were identified in these reviewed areas. This is not an
exhaustive fault-injection review of pre-existing deployer I/O recovery or every legacy document.

## Evidence limits and acceptance

The coordinator's aggregate results were inspected, not rerun wholesale. Reviewer independently
ran the disposable malformed-hook reproduction, its three corrected-source rejection checks, and
reread the R1 correction. No claim is made that the reviewer executed the aggregate fixture suite.

Routing's 47 domains, 60 cases and 480 rows establish filename/path coverage and modeled accounting.
The expected routes are supplied by an oracle; the checker does not infer routes from requests.
Truncating trigger lists can still lose semantic recall, and filename/header fallback can add real
reads. Repository-only behavior and incidental-word avoidance require fresh host observation.
E1 therefore remains necessary even though all expected files are present.

The smaller installed entry totals (Codex 12,120→11,053 and Claude 19,748→19,606 bytes) are source
accounting, not tokens or runtime improvement. Standalone entry growth and complex logging-path
growth remain explicit unresolved tradeoffs. Dispatch efficiency, tool calls, repeated checks,
unnecessary questions and actual constraint preservation are unavailable until matched host runs.

The isolated Claude `--bare` authentication failure does not establish that the normal user profile
is unauthenticated. No matched paired-host matrix was completed. Retain E1 and its affected acceptance
criteria open; no rollout recommendation follows from this review. Root Mac-control plan/task 1.3
and Gate A remain outside this work; the integration preservation check is the recorded hash evidence.

Both material findings are resolved at the source/targeted-fixture level. Local independent review
is complete; overall acceptance remains pending E1 and the explicit rollout tradeoffs.
