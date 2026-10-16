# LE08 — Conditional logging extraction

2026-10-16. Static instruction walkthrough and source-byte accounting against LE01's frozen
`baseline/source/commands/log.md` and `commands/execute.md`. These are not live host runs. LE02's
16 checker cases, LE05 lifecycle review, LE15 control authority and LE16 test-safety evidence were
supplied as prerequisites. Reviewed their reports and the current source before extraction.

## Owned changes and preserved core

- `commands/log.md` remains a complete-read command. It retains mode selection, inference, dated
  append/refresh, Goal/Progress/Decisions/Next, Resume/Sync, state digest and structural checks,
  capped live index plus archive-union check, reusable learning/decision routing, deferred issue
  capture/counts, task archival/progress, phase/readiness, model fit and honest handoff reporting.
- `reference/log/app-handoff.md` holds LE15's app authority and exact-target lifecycle procedure,
  visible absolute artifact handoff and unresolved original-Mac recovery. Recovery explicitly
  retains original state/backup, expiry and restoration steps from LE16's testing contract.
- `reference/log/mac-handoff.md` retains selective staging, Mac identity, trailer formatting and
  parser verification, remote failure/branch handling and truthful sync reporting. No-commit and
  no-push apply independently; a commit request alone does not authorize push. Unresolved recovery
  prevents a safe-switch claim.
- `reference/log/claude-integration.md` preserves the optional phase-marker integration, loaded
  only by Claude Code for pre-clear/Mac-handoff. Codex does not load it or touch Claude markers.
- `commands/execute.md` still closes automatically only at genuine execution endings. Its added
  dispatch instruction follows the logging core's absolute master and actual triggers.

Only conditional bodies were moved; historical explanations in the core were shortened. Task-state
authority/progress formulas remain for LE10, deliberately unchanged by this extraction. This task
does not change plan/state/tracker files, deploy, commit, push, run apps or manipulate the desktop.

## Frozen scenarios and continuation

Each row is a source walkthrough in both root-master and `docs/` consumer layouts. Destinations
change with layout, never authority. The common required outputs are the refreshed session, current
state and live/archive index validation; pre-clear adds exact Resume and model fit. Missing historical
index entries are surfaced, orphan rows retained, and maintenance warnings cannot fabricate success.

| Scenario | Dispatch / transition | Required outcome and limits | Static result |
|---|---|---|---|
| S03 ordinary documentation log | Core only; no runnable build, app launch, recovery or Mac request | Save ordinary session/state/index; route actual reusable evidence and deferred issues; no app/Mac/Claude reference, commit or push | Pass |
| S04 only A, then clear | Execute ends selected scope → core pre-clear | A evidence and exact outcome retained; B not started; Resume names B, prerequisites, unfinished edits, gates and deferred counts; no second close | Pass |
| S05 two ready waves | Execute Step 2 continues; no log dispatch between waves | Start authorized second wave without renewed wave permission; only final execution ending invokes core | Pass |
| S06 A needs unavailable device, B independent | A remains unchecked; B proceeds; genuine end blocker → core pre-clear | Exact missing device gate/evidence and remaining work saved; no fabricated acceptance, premature archival or project-wide stop while B is ready | Pass |
| S07 leave Mac, no push | Core → Mac reference; app reference only if recovery/build/launch also applies | Preserve session/state/index, branch/local commits and machine obligations; authorized scoped commit only; no push or false synced/safe-switch claim | Pass |
| S08 launched app, keep running | Core → app reference | No quit/relaunch; exact app/build identity and keep-running preference saved, including in plain mode | Pass |
| S09 successful build, no desktop control | Execute's build handoff and/or core → app reference | Visible absolute containing-folder path, exact artifact and validation result plus user-operated steps; no launch/quit, input, clipboard/profile writes or indirect control | Pass |
| S13 expired test scope, other-Mac recovery | Core → app reference even without a current-session build; add Mac reference only for Mac-handoff | Save originating Mac, target/process/state/backup, original/current scope/expiry, restoration steps, actual evidence and unresolved status; no timer permission, false restoration or safe-switch claim | Pass |
| Whole plan complete | Execute verifies required acceptance, archives with evidence/links, then core pre-clear once | Exact plan-complete outcome; Resume actual follow-up; no additional manual `/log clear` request | Pass |
| Explicit no-log or immediate stop | Execute Step 4 and core honor restriction | No automatic logging writes despite ordinary close trigger | Pass |
| No-commit and/or no-push | Core honors each limit; conditional Mac reference repeats them | Authorized evidence saving continues; restrictions never become logging-induced Git permission | Pass |

For Claude Code, pre-clear/Mac-handoff additionally reads the host reference and uses the actual next
action over a missing/stale phase marker. The core still emits one model-fit reminder. Plain Claude
logging loads no host reference. Codex skips the host branch in every row.

## Absolute reference resolution

Reviewed three invocation routes: adapter-resolved master; installed command with managed `Local
master:`; repository-only command with the parent of `commands/` validated as the master. For this
checkout each resolves to `/Users/sim/ProgrammingProjects/0-DIRECTIONS/__DIRECTIONS`, then appends
`reference/log/app-handoff.md`, `reference/log/mac-handoff.md` or
`reference/log/claude-integration.md`. All three files exist there. An installed command is never
used as the relative reference root. Missing root/reference validation requires location repair,
not a guessed consumer-project copy. This is source-path validation; actual installed-host replay
belongs to LE13/E1. No installation was mutated for this walkthrough.

## Static loaded bytes versus frozen baseline

UTF-8 filesystem bytes, not tokens, timing or observed host reads. Count scope is the command and
new conditional procedure files only, each once. Session/project/tracker/index data and other
on-demand guides are excluded from both sides because their content/read extent depends on the
fixture. In particular model selection, testing recovery and multi-Mac reconciliation may add guide
reads; these totals must not be represented as all-session context savings. For ordinary S03 there
is no model-fit, testing or Mac guide trigger. Initial means the command selected on invocation;
retrieved means additional workflow files mandated by that scenario.

| File | Frozen LE01 bytes | Current bytes |
|---|---:|---:|
| `commands/log.md` | 17024 | 12021 |
| `commands/execute.md` | 11104 | 12713 |
| `reference/log/app-handoff.md` | 0 (inline in frozen log) | 4225 |
| `reference/log/mac-handoff.md` | 0 (inline in frozen log) | 3387 |
| `reference/log/claude-integration.md` | 0 (inline in frozen log) | 1471 |

| Scenario / host | Initial current files / bytes | Retrieved current files / bytes | Current total | Frozen initial + retrieved | Difference |
|---|---|---|---:|---:|---:|
| S03 ordinary, either host | log / 12021 | none / 0 | 12021 | log 17024 + 0 | -5003 |
| Direct pre-clear, Codex | log / 12021 | none / 0 | 12021 | log 17024 + 0 | -5003 |
| Direct pre-clear, Claude | log / 12021 | host / 1471 | 13492 | log 17024 + 0 | -3532 |
| S07 Mac handoff, Codex, no app trigger | log / 12021 | Mac / 3387 | 15408 | log 17024 + 0 | -1616 |
| S07 Mac handoff, Claude, no app trigger | log / 12021 | Mac + host / 4858 | 16879 | log 17024 + 0 | -145 |
| S08/S09/S13 plain app/recovery log, either host | log / 12021 | app / 4225 | 16246 | log 17024 + 0 | -778 |
| Mac + app/recovery, Codex | log / 12021 | app + Mac / 7612 | 19633 | log 17024 + 0 | +2609 |
| Mac + app/recovery, Claude | log / 12021 | app + Mac + host / 9083 | 21104 | log 17024 + 0 | +4080 |
| S04/S06 execution ending, Codex, no app trigger | execute / 12713 | log / 12021 | 24734 | execute 11104 + log 17024 | -3394 |
| S04/S06 execution ending, Claude, no app trigger | execute / 12713 | log + host / 13492 | 26205 | execute 11104 + log 17024 | -1923 |
| S05 ongoing wave, either host | execute / 12713 | none / 0 | 12713 | execute 11104 + 0 | +1609 |

The frozen baseline predates LE15's authority expansion; the larger combined branches and execute
file include that safety work. Extraction is not claimed to reduce every scenario. Runtime tool
calls, latency, unnecessary questions, repeated validations, actual files changed per scenario and
observed constraint loss remain unavailable until host replay. Source walkthrough found no lost
required constraints; that is not proof of host adherence.

## Checks run

Read-only Python checked all five content files for trailing whitespace and balanced code fences;
verified reference existence, and measured the bytes above. Reviewed the required control/trigger
search across the core, execution and references. No application tests fit Markdown extraction.
No Git commands were run under task ownership restrictions; coordinator owns diff/status checks.
Remaining acceptance: LE13 reference/deployment integration and E1 matched host replay.
