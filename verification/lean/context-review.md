# LE05 — Context lifecycle review

Reviewed 2026-10-16 against the current `commands/execute.md`, `commands/log.md` and frozen
`verification/lean/scenarios.md`. This is static semantic review, not a host replay or runtime
performance measurement. LE01 baseline and LE15 authority work were prerequisites supplied by the
coordinator. No Git, deployment, project-state, tracker or plan changes were made by this task.

## Changes and retained scope

- `52_context-management.md` is a concise practical guide with command links for lifecycle actions.
  Removed competing separate-handoff, plan-deletion and duplicate-close recipes from prose,
  tables, diagrams and quick references. Removed unsupported speedups, token-reduction tables,
  context percentages and fixed-time/message compaction prescriptions.
- `reference/context-examples.md` retains router, nested-instruction, conditional-loading,
  request and evidence examples. Its project conventions are explicitly illustrative. The guide
  links it optionally and says not to load it by default; the reference links back to the guide
  and authoritative commands. No new global or automatic route was added.
- `00_base.md` now uses the session-log Resume block, archives completed plans with evidence and
  links preserved, and closes once. Its unsupported effort ratio/context ceiling were removed.
  Existing task-size, review, commit, delegation and branch-policy prescriptions remain for LE11;
  the old task-size table is retained in the optional reference with command/user limits explicit.

## Required search classification

Ran:

```bash
rg -n 'RESUME|[Dd]elete|[Aa]rchiv|[0-9]+%' 52_context-management.md reference/context-examples.md 00_base.md
```

Every remaining match:

| File:line | Classification |
|---|---|
| `52_context-management.md:87` | Required archive-before-retirement with incoming links preserved |
| `52_context-management.md:89` | Explicit prohibition of separate `RESUME.md` and evidence deletion |
| `52_context-management.md:97` | Retention table: incomplete plan active, archive only after verified completion |
| `00_base.md:317` | Keep incomplete/blocked plan active; archive after required acceptance |
| `00_base.md:379` | User trigger phrase “last 10%”; not a context budget, speedup or efficiency claim |
| `00_base.md:417` | Plan revision preserves task identity/evidence; completion archives history |
| `00_base.md:427` | File-tree annotation matches archive lifecycle |

The optional reference has no matches. A broader `/log` scan confirmed each workflow has one
close and acknowledges execution's automatic close; no milestone triggers a second session-close.

## Scenario walkthroughs

| Scenario | Expected and reviewed outcome |
|---|---|
| Paused mid-task / selected scope ends (S04) | Current plan remains active; execution invokes log pre-clear once, saving exact pickup, unfinished edits and gates in the session log. Next task is not started outside selected scope. No separate handoff file. |
| Resume with old handoffs (S15, S18) | Current state selects the active plan and current session-log handoff. Older logs remain evidence. Conflicting pointers route to selection workflow, not automatic execution of historical instructions. |
| Blocked dependency (S06) | A stays unchecked with its gate; independent authorized B may proceed. Genuine end-of-run blocker gets one pre-clear close. No false completion or archival. |
| Completed implementation with manual gate (S20) | Plan stays active until required acceptance passes. Once whole-plan verification passes, archive plan/evidence, repair incoming links, retire active copy and close once. Selected-task completion never implies whole-plan completion. |
| Two ready waves (S05) | Continue authorized ready work; neither the context guide nor base guide adds an intermediate logging stop. |
| No-control / no-push / recovery (S07–S09, S13) | Guide routes authority to current commands, preserves explicit limits and recovery; logging/reset does not create permission. |

## Checks and limits

Python read-only checks passed for whitespace, existence of local Markdown link targets, balanced
code fences and absence of affirmative obsolete lifecycle recipes across all three content files.
The first lifecycle regex also matched the explicit “Do not create” prohibition; the check was
corrected to distinguish that negative instruction and rerun successfully. Fixed an inherited
nested code fence in the extracted bug-report example.

No application build/test is appropriate for these Markdown changes. No Git checks were run under
the task's no-Git ownership restriction; coordinator integration owns diff/status checks. No host
latency, token-use or behavior benchmark is claimed. Later command changes should rerun the static
walkthrough; LE06/LE08/LE10/LE11 retain their separate policy, handoff and procedure ownership.
