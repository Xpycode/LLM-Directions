# Directions Lean and Efficient Workflow Specification

**Status:** Reviewed and planned — implementation not approved or started.
**Created:** 2026-09-09
**Last Updated:** 2026-09-10

**Implementation plan:** [Directions lean efficiency](directions-lean-efficiency-plan.md).
The [planning review](../verification/directions-lean-efficiency-planning.md) records the follow-up
Sol/Luna review, official web sources and concrete decisions/validation gates. Policy proposals below
remain proposals until their named plan decision is resolved.

## Problem Statement

Directions accumulates context and maintenance work through long instruction files, repeated
procedures, mirrored task status, and index checks that can report false drift. Conflicting lifecycle
instructions also make agents choose between obsolete and current behavior. This affects the solo
developer using Codex and Claude Code across projects and Macs.

The current foundation is sound: shared commands, thin host adapters, on-demand universal guidance,
dependency-aware execution and persistent evidence. Improve that foundation incrementally, retaining
the safeguards and behavior the owner deliberately requested.

## Review Method and Baseline

The owner requested a review using Sol, Luna and the web. Sol independently reviewed workflow
overhead; Luna reviewed instruction loading, generation and deployment. The coordinating agent
checked repository evidence, ran an index-generation preview, reproduced the archive-checker defect
in a disposable fixture and consulted official OpenAI/Anthropic documentation. Reviewer agreement
is corroboration, not proof. This was a targeted documentation/workflow audit, not a full runtime audit.

Measurements taken on 2026-09-09; bytes are UTF-8 file sizes, not token counts:

| Artifact | Baseline |
|---|---|
| `CODEX-GLOBAL-TEMPLATE.md` | 107 lines; 8,406 bytes |
| Generated index region in that template | 5,444 bytes, including opening marker; 64.8% of template |
| `CLAUDE-GLOBAL-TEMPLATE.md` | 349 lines; 19,385 bytes; same 5,444-byte index region |
| Repository `AGENTS.md` | 58 lines; 3,615 bytes |
| `52_context-management.md` | 1,070 lines; 33,813 bytes |
| `commands/log.md` | 278 lines; 16,803 bytes |
| `commands/execute.md` | 165 lines; 11,104 bytes |

File size demonstrates potential loading overhead, not measured latency or cost savings.

## Findings and Proposed Dispositions

Paths and line numbers identify the reviewed version; they may move during implementation.

| ID / priority | Evidence and consequence | Proposed disposition |
|---|---|---|
| F01 / High — archive false positives | `commands/log.md:103-112` archives old rows, but `scripts/sync-session-index.sh:73-85` compares files only with the live index. A two-log fixture with one live and one archived row returned exit 1 and reported the archived session missing. | Compare live and archived records together. Retain real missing/orphan detection; never auto-delete records. This already has a maintenance Backlog item. |
| F02 / High — conflict files become guidance | `scripts/gen-directions-index.sh:74-82` accepts every numbered Markdown file except redirect stubs. Preview emitted both `22_macos-platform.md` and its Syncthing conflict copy; installed Codex instructions also contained the duplicate. `.gitignore:22` hides conflict files from normal status. `deploy-codex.sh:59-63` regenerates the index during deployment. | Filter conflict/backup artifacts and validate generation before installation. Preserve excluded files for separate reconciliation; do not delete their unique contents. |
| F03 / High — contradictory context procedures | `52_context-management.md:673-714` prescribes separate `RESUME.md` files and deleting completed plans; `commands/log.md:25` uses a session-log Resume block and `commands/execute.md:120-123` archives the plan and evidence. | Make commands authoritative for lifecycle procedures. Reduce the context guide to operational principles and canonical links; retain useful tutorials/examples as optional reference material. |
| F04 / Medium — always-loaded router overhead | The Codex index consumes 64.8% of its global template. Broad keywords can load long topic docs for incidental mentions. | Compare a compact domain router plus detailed on-demand index with a shortened inline map. Keep necessary safeguards visible and test routing recall before choosing. |
| F05 / Medium — full logging load at execution boundaries | `commands/execute.md:125-140` invokes all of `commands/log.md` after selected task/wave completion or a genuine stop. Conditional app cleanup, Mac handoff and model integration occupy `log.md:149-268`. | Preserve automatic checkpointing and the current closeout contract initially. Extract a short core and selectively loaded subprocedures; change full-command loading instructions consistently. |
| F06 / Medium — repeated task status | `commands/make-plan.md:142-163` mirrors plan tasks into `TASKS.md`; `execute.md:87-95` synchronizes plan/tracker/state; `log.md:134-139` archives tasks and recalculates progress. Live task 1.3 occupies `TASKS.md:44-96` as well as plan/state evidence. | Evaluate the active plan as canonical for its task status/evidence, with TASKS holding backlog/inbox and state holding one execution pointer. Define migration and progress reporting before removing mirrors. |
| F07 / Medium — rigid task/commit granularity | `commands/make-plan.md:64-68` favors tasks under 30 minutes; `IMPLEMENTATION_PLAN-template.md:34-35` and `commands/execute.md:159-165` specify one task per commit. | Prefer independently verifiable outcomes and coherent validated commits. Consider allowing several related small tasks in one commit; preserve scoped diffs, reversibility and user commit restrictions. |
| F08 / Medium — delegation overhead for small work | `commands/execute.md:72-85` requires fresh task packets and coordinator integration for parallel independent tasks. Dispatch/review may exceed the benefit for small documentation/configuration changes. | Evaluate a proportionality rule: delegate when independent work or review benefits justify dispatch/integration. Preserve fresh context, ownership and dependency rules whenever agents are used. No universal duration threshold is established. |
| F09 / Low — collision checks on read-only status | `commands/status.md:113-133` applies the Claude process check to all modes; Codex already omits it unless another session is mentioned. | Evaluate restricting the detector to arrival, worktree/branch-changing operations or known concurrency. Retain warnings before risky shared-checkout actions. |
| F10 / Low — duplicated global/repository instructions | Repository `AGENTS.md:9-58` repeats universal routing, preservation and template-ownership guidance from `CODEX-GLOBAL-TEMPLATE.md:7-44`; both load in this repository. | Keep repository-specific facts and validation local; consolidate universal policy without breaking operation when global installation is absent. Keep Claude/Codex stable facts aligned. |
| F11 / Medium — obsolete deployment entry point | `install-directions.sh:47-63` copies commands and the raw template, requesting manual path edits; it does not refresh an existing global file. `README.md:232-233` still exposes this older installer alongside `redeploy.sh`. | Retire the old entry point or make it a compatible wrapper around the supported deployer. Preserve arguments, existing personal configuration and explicit installation boundaries. |

The initial user-facing review emphasized F01–F06. This spec also retains the independent reviewers'
additional findings F07–F11 so the full review survives the session.

## Proposed Solution

**One-liner:** reduce instruction loading and duplicated bookkeeping while preserving reliable,
authorized execution and recoverable session state.

Key capabilities:

1. Correct index generation/checking with meaningful missing, orphan and conflict handling.
2. One authoritative procedure for each lifecycle operation, loaded only when applicable.
3. Concise global routing that reliably discovers relevant guidance in both hosts.
4. Clear ownership of task status and evidence, with fewer manual synchronizations.
5. Measured workflow simplification, including proportionate delegation and commit granularity.

User flow: invoke the same familiar command or natural-language request; load relevant guidance;
perform authorized work and appropriate verification; record the outcome once with discoverable
pointers; resume without reconstructing history or answering redundant maintenance questions.

Suggested sequence, not an approved implementation plan:

1. Fix and verify F01–F02 independently of broader policy changes.
2. Resolve F03 and simplify F05 loading while preserving automatic closeout behavior.
3. Benchmark F04 and F06 alternatives; migrate only after requirements and ownership are clear.
4. Resolve F07–F11 based on measured value and compatibility requirements.

## Acceptance Criteria

All boxes remain unchecked until implementation and verification supply evidence.

- [ ] **AC01 / F01:** Given session records split between live and archived indexes, when the checker
  runs, then archived records are recognized, true missing/orphan records remain detectable, and
  no existing row or session file is removed. Verify suffixed-date records and absence of an archive;
  a row's explicit suffixed log target takes precedence over its unsuffixed displayed date.
- [ ] **AC02 / F02:** Given canonical numbered docs plus conflict/backup copies and redirect stubs,
  when the index is generated, then only canonical eligible documents are routed, each once;
  excluded artifacts remain intact and the deployed preview contains no conflict filename.
- [ ] **AC03 / F03:** Given a completed plan or session handoff, when current guidance is followed,
  then plan evidence is archived and the canonical Resume location is unambiguous; topic guides
  do not introduce conflicting lifecycle procedures.
- [ ] **AC04 / F04,F10:** Given a representative routing matrix for both hosts, when lean entry points
  are used, then required domain/safety guidance is discovered and measured instruction bytes are
  reduced against the corresponding baseline without losing repository-specific instructions.
- [ ] **AC05 / F05:** Given ordinary logging without Mac handoff or launched test apps, when logging
  runs, then it saves required state without loading those inapplicable subprocedures. Given their
  actual trigger, the relevant safeguards still apply. Automatic execution closeout remains intact
  unless an explicit later decision changes its user-visible behavior.
- [ ] **AC06 / F06:** Given a plan-task transition, when status is recorded and the session resumes,
  then task completion/gates derive from one defined authoritative record, state links resolve,
  backlog issues remain discoverable and historical evidence is retained through migration.
- [ ] **AC07 / F07:** Given a coherent validated change spanning small related tasks, when commit
  guidance is applied, then accepted granularity rules permit a reviewable scoped commit without
  imposing an arbitrary time split; no-commit restrictions still prevail.
- [ ] **AC08 / F08:** Given small coupled work or substantial independent tasks, when the execution
  strategy is chosen under the agreed policy, then it is proportionate; any delegated work has fresh
  context and exclusive ownership, and explicit user agent/scope restrictions are honored.
- [ ] **AC09 / F09:** Given the agreed collision-check policy, when normal status or a risky
  shared-checkout transition occurs, then checks run at the specified boundary and warnings do not
  falsely imply Codex has an installed process detector.
- [ ] **AC10 / F11:** Given the retained legacy installation entry point, when exercised in a temporary
  home, then it delegates safely or gives an actionable retirement message; it never silently installs
  unresolved path placeholders or overwrites unrelated personal instructions.
- [ ] **AC11 / all:** Given unchanged representative scenarios before and after simplification, when
  evaluated with the same host/model/effort, then the report records instruction bytes, tool calls,
  files updated, unnecessary questions and successful completion. Required safety/continuity checks
  all pass; observed efficiency improvements and any regressions are reported without invented gains.

## Technical Considerations and Validation

- Retain `commands/*.md` as the procedural source; do not create host-specific command copies.
  Any shared subprocedures must be canonically linked, not repeated in each adapter.
- Keep template ownership: change versioned templates/generators, not installed managed blocks.
  A specification or local fixture run does not authorize global deployment or consumer migration.
- Reuse existing shell/Python tooling; no new framework or external service is required.
- Use disposable fixtures for archive/checker edge cases, generation contamination, and installation
  preservation/idempotence. `bash -n` applies when shell files change; Markdown checks apply now.
- Benchmark `status`, a small standalone fix and execution handoff first. Include a blocked dependency,
  a multi-wave continuation, explicit no-agent/no-commit restrictions and Mac handoff as regression
  scenarios. Distinguish simulated walkthroughs from actual host behavior.
- Record versions/settings and repeated observations for latency claims. Do not infer token counts
  from bytes or claim that shrinking documentation alone guarantees speed or cost improvement.
- Preserve dirty work, dependency-local blocking, real acceptance gates, selective revalidation,
  continuous authorized execution, foreground permissions and separate push/deploy authorization.

## Out of Scope

- Implementing or deploying changes during this review/planning request.
- Replacing the active Mac-control plan, resolving its runtime blocker or claiming its gates passed.
- Deleting Syncthing conflicts, session history or execution evidence to achieve a size target.
- A wholesale rewrite, copied universal docs, new command vocabulary, model migration or new service.
- Weakening validation or approval boundaries solely to reduce calls or questions.

## Open Questions

| Question | Status / proposed default |
|---|---|
| Compact inline map or two-stage domain/index loading? | Benchmark both; choose based on bytes and correct routing, not size alone. |
| Which task/status record becomes canonical, and how do legacy consumers migrate? | Plan ownership is proposed; define compatibility and progress reporting before migration. |
| Should full pre-clear logging stop after selected task/wave completion? | Sol suggested this, but earlier September 9 work explicitly added automatic closeout. Preserve behavior; first reduce loading/bookkeeping. Changing semantics needs a separate decision. |
| Should independent small tasks bypass agent dispatch? | Evaluate proportionality without reversing deliberately strengthened fresh-agent execution requirements. |
| Which commit and collision-check policy changes are worth adopting? | Retain F07/F09 for evaluation; no new policy is active from this draft. |
| What numerical reduction should gate rollout? | Establish scenario baselines first; no percentage speedup or token target is asserted. |
| Does the old installer have callers needing compatibility? | Inspect references/arguments before choosing retirement versus wrapper. |

## Sources and Related Records

Official sources consulted during the review on 2026-09-09:

- [OpenAI: AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md) — instruction
  discovery/merging supports treating global and repository guidance as a combined loading budget.
- [OpenAI: Build skills](https://learn.chatgpt.com/docs/build-skills) — metadata first, full instructions
  when selected; supports progressive disclosure, not a measured Directions performance claim.
- [Anthropic: Effective context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
  — minimal sufficient instructions and selective retrieval support the proposed context strategy.
- [Anthropic: Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)
  — begin with simple solutions and add orchestration when task needs justify it.

These principles inform proposals; local measurements determine whether they help Directions.
The broad speedup figures in `52_context-management.md:33,275-289` are not this project's baseline
and should be removed, qualified or supported when that guide is revised.

- [Session review and capture](../sessions/2026-09-09.md#directions-lean-review--first-spec)
  (daily log is locally saved and Git-ignored; this spec retains the portable findings).
- [Existing execution-workflow review](../verification/wave-execution-workflow.md) — preserve recent intent.
- [Task tracker](../TASKS.md) — existing index maintenance plus this review's follow-up.
- [Project state](../PROJECT_STATE.md) — discovery pointer; Mac-control execution remains separate.

**Next:** explicitly execute the linked lean-efficiency plan when ready; LE01 freezes the baseline,
then independent correctness fixes can proceed. Mac-control execution remains separate.
