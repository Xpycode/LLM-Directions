# Lean-efficiency planning review

**Completed:** 2026-09-10. **Scope:** spec review and implementation planning only.
**Deliverable:** [14-task plan](../specs/directions-lean-efficiency-plan.md).

## Verdict

The spec is suitable for staged implementation after separating confirmed correctness defects from
measured routing choices and workflow-policy decisions. Its original F01–F11 and AC01–AC11 remain
the scope. No acceptance box is checked by this review; no implementation or deployment was performed.

Sol (`gpt-5.6-sol`) independently reviewed lifecycle, bookkeeping, granularity and scheduling.
Luna (`gpt-5.6-luna`) independently reviewed the checker, generator, entry points and installer.
Both received fresh task contexts and read repository files; neither edited files. The coordinator
checked the spec, current workflow/template/state, overlapping dirty diffs and official web sources.

## Findings incorporated into the plan

| Finding | Evidence and resolution |
|---|---|
| Existing work must remain resumable | Root `IMPLEMENTATION_PLAN.md` is the active Mac-control plan with task 1.3 unresolved. Keep this plan separately linked under `specs/`, with distinct LE IDs. The July `OPTIMIZATION-PLAN.md` does not replace current evidence. |
| F01 includes two parser defects | `scripts/sync-session-index.sh` reads only the live index and independently extracts displayed dates plus link targets. A suffixed link with an unsuffixed display date can invent another record. LE02 tests archive union and link precedence. Luna also ran the read-only checker: 60 local files versus 16 live entries; those raw counts are not a count of true lost records. |
| Session and guidance conflict files need different treatment | Generator conflict copies must not become guidance (LE03). Unindexed session conflicts may contain unique history and remain surfaced for reconciliation (LE02). Neither is deleted. |
| F03 extends beyond the cited paragraph | `52_context-management.md` repeats plan deletion and separate `RESUME.md` recipes in later diagrams/tables, including lines 976 and 1033. LE05 checks the whole guide. Existing legacy Resume files remain evidence; changing future guidance is not permission to delete them. |
| F05 need not break full-command loading | Keep `commands/log.md` as a small complete dispatcher/core and read conditional references only on their trigger. LE08 preserves automatic run-ending pre-clear and avoids closeout between ready waves. LE09/LE13 verify installed command references resolve from the master. |
| F06 is a compatibility migration | LE06 defines task authority, progress denominators, no-plan/multiple-plan fallback and interrupted migration before LE10 changes commands. The live Mac-control plan is not the migration fixture. |
| F07–F09 need consistent policy surfaces | Serialize shared `execute.md`/planning/template changes. Sol recommends coherent validated commits and proportional dispatch; the plan records these as proposals, retaining recent user-required agent behavior until a concrete change is accepted. Collision checks remain at risky transitions. |
| F04/F10 need routing proof, not just a smaller file | Compare both router candidates with combined global/repository loading and extra lookup costs. Include all current domains, incidental mentions, missing-global fallback and both hosts. Real host observations remain E1. |
| F11 cannot safely be a blind wrapper | `install-directions.sh` copies raw templates; `redeploy.sh` has different replacement semantics for existing Claude instructions. Luna found no automation callers in its repository scan. Prefer an actionable no-write retirement stub, with existing/absent personal-file fixtures. Unknown external callers are not assumed absent. |

## Source checks

Official pages were opened and relevant sections inspected during September 9–10, 2026:

- [OpenAI: Custom instructions with AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md)
  describes global/project instruction discovery and concatenation. This supports measuring the
  combined initial instruction set and testing repository fallback. It does not establish a speed gain.
- [OpenAI: Build skills](https://learn.chatgpt.com/docs/build-skills) describes metadata-first skill
  discovery and loading the full selected skill. This supports concise entry points and conditional
  references while preserving the complete procedural skill/command contract.
- [Anthropic: Effective context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
  recommends a small sufficient set of relevant context. The plan translates that principle into
  local routing and continuity tests, not assumed model performance.
- [Anthropic: Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)
  recommends adding orchestration complexity when it improves task outcomes, acknowledging cost and
  latency tradeoffs. This informs the proportionality experiment without overriding user instructions.

## Plan validation and limits

The schedule freezes the baseline first, names prerequisites and exclusive file ownership, serializes
shared lifecycle edits, maps every acceptance criterion to tasks, and separates local checks from
fresh-host acceptance. Planned fixture commands are explicitly future artifacts. No application
build or Swift test is appropriate for these planning-only Markdown changes.

Sol's final schedule review identified two defects, both corrected: LE09 now checks reference
resolution with an independent fixture and LE13 checks LE08's actual extracted references; and an
unaccepted delegation exception now selects a tested preservation default instead of blocking all
integration. An unmet AC08 remains explicitly open rather than being reported as satisfied.

Current Sprint remains Mac-control work. The queued plan is linked from the existing maintenance
backlog and state, rather than displacing that sprint under the normal make-plan synchronization step.
On explicit activation, update the execution pointer and select a focused set of LE tasks.

The plan's policy/migration contract is an implementation prerequisite, not a reason to defer writing
the plan or to block independent index fixes. Global deployment, real consumer migration and pushes
remain separately scoped. Observed efficiency and host success remain unverified.
