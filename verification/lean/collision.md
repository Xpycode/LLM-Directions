# LE12 collision boundary trace

October 16, 2026. Implements the LE06 decision after LE10's lifecycle edits. This is a source-level
semantic walkthrough, not a live detector test or host acceptance (E1). No Git operation, process
scan, checkout change or desktop control was performed. Hook sources were read and left unchanged.

## Boundary matrix

| Scenario | Expected behavior | Source trace / result |
|---|---|---|
| Plain status, no known concurrent session | No detector call | `commands/status.md` triggered-check table explicitly skips it. Pass. |
| Full/context, no known concurrent session | No detector call | Same table covers full; existing mode alias remains. Pass. |
| Arrive/sit down/switch/behind? | Supported detector check; unavailable detection disclosed | Arrive step 5 reaches triggered table; aliases still select arrive. Pass. |
| Known same-checkout concurrency, any mode | Preserve warning even with silent detector | Trigger table + output interpretation + Codex fallback retain known risk. Pass. |
| Claude guard emits warning | Surface warning; coordinate one Git driver or isolate | Claude-only block retains existing invocation. Pass. |
| Detector absent, missing tools or unreadable process | Never infer no collision from silence | Silent output caveat matches guard's early exits; Codex does not run it. Pass. |
| Codex arrival/mutation | Report unsupported automatic detection; use known session information | Explicit fallback; no invented detector. Pass. |
| Two distinct worktrees | Distinct HEADs, no same-checkout claim; coordinate shared refs/admin | Guard resolves toplevels; status and Rule 5 qualify isolation. Pass. |
| Worktree add, remove, branch deletion, prune | Identity and concurrency preflight, target not in use for removal | Worktree steps 1/3/4 explicitly apply Rule 5. Pass. |
| Checkout/switch/branch mutation, merge/rebase/pull | Same preflight before mutation | Rule 5 covers these plus continue/abort; guide-wide precondition covers all recipes. Pass. |
| Reset/cherry-pick/stash/path checkout recovery | Same preflight before mutation | Rule 5 enumerates recovery mutations; guide-wide precondition includes tables/cheatsheets. Pass. |
| Failed `cd` from repo A to intended repo B | Stop; A's remote cannot establish B's state | Arrive step 2, worktree step 1 and guide precondition explicitly reject this inference. Pass as walkthrough; no failed live directory change used. |
| Existing SessionStart | Startup detection retained | Read `hooks/session-start.sh` lines 112–127: sibling guard resolution/invocation remains; neither hook edited. Pass as source review. |

## Entry-path audit

`commands/status.md` arrival's offered pull now requires Rule 5 before acting. Status itself remains
read-only and cannot authorize a mutation. `commands/worktree.md` covers creation and its separately
authorized cleanup instructions, including a merge/rebase before cleanup. Rule 5's guide-wide
precondition applies to Rules 1/1a (pull/reset/stash/merge), 1b (bootstrap/reset), 1c (switch/cherry-pick/
branch deletion), Rule 3's checkout/rebase, Rule 5 worktrees, and the pre-flight/quick-reference tables.
Identity is checked before remote claims even when no mutation follows.

The separate `32_git-workflow.md` owner added the Rule 5 preflight reference before Branch Strategy,
covering branch examples and recovery recipes; this was coordinated without editing that file here.
`commands/execute.md` routes Git operations through that guide. `commands/setup.md` routes its Git
initialization through the same guide. No new automatic hook or lock mechanism was introduced.

## Checks performed

The following exact source searches returned the expected trigger, warning, identity and mutation
references; each match was read in context (search counts alone are not semantic verification):

```bash
rg -n 'session-guard|collision|concurr|checkout|branch' commands/status.md commands/worktree.md 37_multi-mac-discipline.md
rg -n 'Rule 5|preflight|merge/rebase|failed.*cd|different worktrees|SessionStart|Codex' commands/status.md commands/worktree.md 37_multi-mac-discipline.md 32_git-workflow.md
rg -n 'git (checkout|switch|merge|rebase|worktree|branch|reset|cherry-pick|pull)|32_git|37_multi' commands/*.md 32_git-workflow.md reference/*.md
```

An ancillary search for `reference/log*.md` hit a shell no-match error; no validation relies on it.
An initial wiring search also named nonexistent `hooks/settings-hooks.json`; the actual
`hooks/session-start.sh` invocation was subsequently read directly. Git diff/status checks remain
the coordinator's responsibility under exclusive Git ownership. LE10's task-state status paragraphs
were preserved; no plan, state, tracker, deployment or consumer file was edited by this task.
