# LE15 — App-control authority

2026-10-16. Static source review and semantic walkthroughs only; no live app/process control,
tests hosted by an app, clipboard/profile writes, Git operations, deployment or host acceptance.
LE01's frozen `baseline/source/commands/log.md` and `commands/execute.md` matched the working
files byte-for-byte before these edits (Python `difflib` comparison produced no differences).
This preserves the frozen baseline and establishes that no overlapping edits were replaced.

## Changes and interface for LE08

`commands/log.md` §7 now dispatches for a successful runnable build, an app launched in the session,
or an outstanding recovery obligation. Its former unconditional quit/kill and installed-app
relaunch instructions are replaced by current explicit target/action/Mac/scope authority. The
golden rule explicitly limits automatic logging steps to authorized work. `commands/execute.md`
applies the same boundary before execution/tests and at automatic closeout.

LE08 must preserve the complete §7 contract when extracting it: no indirect control, no timer-based
permission, keep-running preference, exact target and graceful termination, separately authorized
replacement launch and executable verification, visible absolute containing-folder handoff, and
original-Mac recovery with evidence and unresolved status. A permission gap does not prevent saving
the log or continuing other authorized work. No logging extraction was performed in LE15.

## Required search and classification

Ran successfully (exit 0):

```sh
rg -n 'quit|kill|relaunch|launch|permission|clipboard|profile' commands/log.md commands/execute.md
```

Every returned match is classified below; line numbers describe this LE15 revision, before later
authorized extraction/migration. These are review findings, not an automated semantic proof.

| File and lines | Classification |
|---|---|
| log 15 | Automatic logging explicitly bounded; no app/desktop authority conferred. |
| log 39 | Existing local-commit permission does not confer push authority; retained. |
| log 157 | Trigger identifies launched app or unresolved recovery; no action authorized by trigger. |
| log 161–163 | Newer restriction wins; exact-target permission required; direct and indirect control plus clipboard/live-profile replacement forbidden without it. |
| log 165 | Timer/log/handoff cannot extend permission; keep-running honored. |
| log 170 | Read-only process candidate is not termination permission. |
| log 188–189 | Positive authorized replacement path verified; quit permission does not imply installed-app launch. |
| log 191 | Recovery requires still-valid authority; obligation alone is insufficient. |
| log 196–197 | Visible absolute folder/artifact and user-operated handoff under no-control. |
| log 201 | Recovery ledger includes affected profile/clipboard state without replacing it. |
| execute 22–25 | Exact scope and newer restrictions; indirect methods/profile/clipboard do not bypass control limits. |
| execute 34–36 | Manual handoff when restricted, verified action when explicitly authorized, no implied installed-copy launch. |
| execute 112 | Existing ready-wave continuation within authorized work; does not confer control permission. |

## Frozen semantic scenario walkthroughs

Each result below follows the updated command branches against LE01 inputs; all transitions are
simulated. Host/version/model/effort, runtime tool counts, timing and observed host adherence are
unavailable here and remain E1 evidence. Both root-master and `docs/` layouts use the same authority
rules; path mode changes log destinations, never control permission or original-Mac identity.

| Oracle and setup | Permitted transition | Forbidden transition and resulting record | Result |
|---|---|---|---|
| S09: successful build, current no-control; older automatic relaunch preference exists | Build/read-only verification → visible absolute containing folder + artifact name + user-operated steps | No quit, launch, simulated input, clipboard/profile change; newer restriction wins | Pass by source walkthrough |
| S10: full-tests request, no-control, app-hosted scheme | Inspect startup effects; consult test guidance, choose supported authorized headless work or record blocked cases | Never invoke the hosted runner as an indirect launch; tests do not bypass authority | Pass for authority boundary; detailed test contract owned by LE16 |
| S22: explicitly allow graceful quit of exact test build on original Mac | Identify exact executable/owned process → gracefully terminate → verify exit | Do not launch installed app, touch another app or bypass save prompt; report verified action only | Pass by source walkthrough |
| S22 positive replacement variant: explicitly allow quit of exact old build and launch of exact new artifact | Verify old exit → launch authorized artifact → verify running executable path | A different installed copy remains outside scope | Pass by source walkthrough |
| S13: time-limited test scope expired; recovery remains on other Mac | Stop control → save original Mac, target/state, original/current scope, evidence, intended recovery and permitted/user-operated next step | No timer-inferred cleanup, clipboard/profile restoration or false restored/safe-switch claim; receiving log on another Mac does not resolve it | Pass by source walkthrough |
| S13 recovery variant: explicit original scope separately still permits exact recovery | Perform only that still-authorized recovery on original Mac; verify and record actual outcome | No additional testing/control or scope extension | Pass by source walkthrough |
| S08: launched test build, user says keep running | Preserve running app and exact identity/preference in handoff | No quit/relaunch, even at automatic pre-clear | Pass by source walkthrough |
| S07: Mac handoff, no push and outstanding app recovery | Save handoff and recovery evidence; honor no-push boundary | Do not treat handoff as control authorization or claim safe switch while recovery is unverified | Pass for app authority; Git behavior not executed |

Read-only candidate example remains executable-path based (`ps comm`), with the existing synthetic
negative-check advice retained. No process scan or termination was run for this documentation task.
Existing automatic pre-clear, authorized wave continuation, outcome reporting and commit/push
boundaries remain intact. No source routing or host acceptance claim is made by these walkthroughs.
