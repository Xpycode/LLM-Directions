# Mac Control Coordinator Specification

**Status:** Review — inventory/protocol complete; runtime implementation not started
**Created / last updated:** 2026-09-05
**Owner:** Directions; personal, local macOS companion
**Plan:** [Implementation plan](../IMPLEMENTATION_PLAN.md)
**Evidence:** [Research and compatibility notes](mac-control-research.md)
**Execution contract:** [Protocol revision 1](../tools/mac-control/Protocol.md) ·
[static verification](../verification/mac-control/protocol.md); product acceptance remains unverified.

## Problem Statement

Several coding sessions run across the user's projects at once. A session testing a desktop app
can change focus, move the pointer, or type while the user is writing elsewhere. Separate prompts
inside agent conversations do not provide one visible schedule, reliable handover, or a shared
stop mechanism. The user needs to decide when to lend the desktop and know when it is theirs again.

User clarification (2026-09-05): this happens occasionally during UI tests from Penumbra, Game One,
or any session doing similar work; most testing is not disturbing. A supplied Conjoyn example shows
shell AppleScript via System Events alongside a read-only Swift AX inspector. Schedule interfering
actions across projects while leaving verified noninterfering inspection and background work free.

Directions currently documents an AppProbe test overlay and an execution prompt, but has no shared
desktop owner. AppProbe is absent at its documented local path. Existing AX/CGEvent harnesses can
change focus and send input independently. Checkout collision warnings solve a different problem.

## Proposed Solution

### One-Liner

A local menu-bar helper lets sessions request short, exclusive periods of foreground Mac control,
with human approval, a five-second countdown, visible progress, and an enforced stop for supported tools.

### Key Capabilities

1. One queue shared by all participating projects and agent providers in the active login session.
2. A request names the project, session, target apps, purpose, planned steps, and maximum duration.
3. Yes / No / Wait decisions, followed by a cancellable five-second countdown only after Yes.
4. A compact overlay shows owner, time allowance remaining, current step, and Stop.
5. Supported action executors reject input outside the grant and acknowledge that input has stopped.

### Scope and working assumptions

- Personal use on the user's Macs; local-only operation. Each Mac has an independent queue.
- Codex and Claude are desired clients. Their exact installed desktop backends are **unverified**.
- Native AppKit helper and a CLI are the proposed v1 delivery. MCP is added only if the backend
  inventory proves it is needed for an actual client; it is not a second implementation of the broker.
- Proposed source location: isolated `tools/mac-control/` package in this master, with its own
  README, build commands, and scoped instructions. The repository root remains documentation-first.
- Proposed identity: `Mac Control`, bundle ID `com.lucesumbrarum.MacControl`; minimum macOS 14,
  subject to the compatibility spike. Follow `14_project-identity.md` for signing.
- Requests use whole seconds, from 1 to 600 seconds; no default automatic approval or renewal.
  These are proposed product defaults, not constraints supplied by the user.
- Planning is authorized. This document does not claim deployment or runtime compatibility.

### User flow and placement

1. The agent prepares its build and test plan without foreground interaction. It submits a request
   immediately before the first focus-changing or input action, including an activating launch.
2. A nonactivating panel appears near the top-right of the current display, avoiding the menu bar.
   The menu-bar item opens the queue. Merely showing a request does not change the key window.
3. The user explicitly selects **Yes, start**, **No**, or **Wait**. No rejects that request. Wait
   moves it to a deferred list until the user selects Review; it never starts after a delay.
4. Yes reserves the single slot and starts **5 → 4 → 3 → 2 → 1 → 0**. No input is permitted
   during countdown. Cancel or a failed preflight invalidates the pending grant.
5. At zero, after readiness is revalidated, control starts. The approved duration starts now.
   The panel becomes a compact, nonactivating progress overlay with an always-visible Stop control.
6. Completion or Stop enters **Stopping**. Only after the executor confirms quiescence does the
   helper announce **Control returned**. The next queued request requires its own Yes and countdown.

```text
Mac control requested
CropBatch · Export regression · Codex session 7F2A
Up to 2 min 30 sec · 7 planned steps
Open export → change settings → verify output
Please avoid using the mouse and keyboard while testing is active.
[ No ]  [ Wait ]  [ Yes, start ]

After approval: Starting in 5…                         [ Cancel ]

● CropBatch · Export regression          01:42 allowance remaining
Step 3 of 7 · Checking export settings
[ Stop and return control ]                    2 requests waiting
```

- Use `NSStatusItem`, `NSPanel`, `NSButton`, and native labels/progress views. No primary sidebar,
  split panes, or raw SwiftUI interactive controls are needed; this follows `47_project-ui-conventions.md`.
- Yes has no default Return/Space binding. Keyboard approval requires explicitly focusing the
  request through the helper and navigating to Yes. Existing typing must never approve a request.
- The overlay can be moved by the user; doing so while active first stops control. It must remain
  reachable in supported Spaces/full-screen/display configurations without covering the test target.
- Proposed emergency shortcut: Control–Option–Command–Escape. Verify registration and actual delivery,
  including conflicts and lost monitoring. Plain Escape remains available to the target app.
- Closing a pending panel means Wait. Closing an active overlay means Stop. Hide is not a running state.
- At expiry, stop first. The session can request more time afterward; it cannot extend the deadline.
- Step text is reported by the runner. Unknown totals show a current activity, never an invented
  percentage. Completion may happen early; remaining allowance is not an ETA.

## Acceptance Criteria

All criteria are unverified until implementation. IDs map to the plan and verification report.

### Requests and handover

- [ ] **AC01:** Given two sessions in different projects request simultaneously, when the helper
  handles them, then both appear once and at most one can be reserved or active.
- [ ] **AC02:** Given the user is typing in another app, when a request appears and they press
  Return/Space, then focus stays with that app and the request remains unapproved.
- [ ] **AC03:** Given a pending request, when No is selected, then its client receives a terminal
  rejection and zero focus/input actions occur; automatic retries do not recreate the prompt.
- [ ] **AC04:** Given a pending request, when Wait or close is selected, then it is deferred until
  explicit Review and a later Yes; elapsed time, idle detection, and another session finishing cannot start it.
- [ ] **AC05:** Given a ready request, when Yes is selected, then 5 through 0 are shown over five
  monotonic seconds, zero automation events occur before zero, and the next request cannot start.
- [ ] **AC06:** Given countdown, when Cancel, target loss, lock, or requester disconnect occurs,
  then no grant starts; any later attempt needs a new Yes and countdown.
- [ ] **AC07:** Given an active grant, when step updates arrive, then the overlay shows the correct
  owner, target, remaining allowance, and current step within one second without changing focus.
- [ ] **AC08:** Given an early successful finish, when release is acknowledged, then Control returned
  appears and the next queued session still waits for explicit approval.

### Enforcement and recovery

- [ ] **AC09:** Given no grant, an expired grant, another client's grant, or an old helper generation,
  when a supported executor receives an action, then it rejects it and produces zero input events.
- [ ] **AC10:** Given an active sequence, when Stop, the emergency shortcut, or expiry is processed,
  then admission closes immediately, no subsequent step starts, and the executor is quiescent within
  one second on the supported test machine. Already-delivered actions are not rolled back.
- [ ] **AC11:** Given cancellation while an action is in flight, when cancellation is requested,
  then no next owner starts until cancellation/draining is acknowledged. A failure after one second
  remains visibly Stopping — intervention required; it never falsely reports Control returned.
- [ ] **AC12:** Given an active session or helper/runner connection is lost, when its watchdog detects
  the loss (within three seconds), then no further input is admitted and the executor stops. Restart
  discards all old grants and does not resume old requests automatically.
- [ ] **AC13:** Given a Mac sleeps, locks, or changes login session, when control resumes, then the
  old grant is invalid and requires new human approval. Changing wall-clock time cannot extend it.
- [ ] **AC14:** Given the user clicks/types/scrolls or focus changes unexpectedly during control,
  when the supported intervention monitor detects it, then automation stops; it never fights to
  reclaim focus. If reliable physical/synthetic event separation is unavailable, mark that adapter
  unsupported for this guarantee rather than silently allowing conflicting input.
- [ ] **AC15:** Given pending work for app A, when app A is replaced, quits, or the focused target is
  no longer the expected instance/window before dispatch, then input stops without reaching app B.
- [ ] **AC16:** Given the helper, required permissions, or emergency-stop monitoring is unavailable,
  when a request tries to start, then it remains blocked with a concrete remedy and zero input.

### Workflow and usability

- [ ] **AC17:** Given builds, source reads, or verified noninterfering inspection, when another
  session holds control, then that background work continues without a desktop grant.
- [ ] **AC18:** Given an unsupported backend or direct legacy harness, when Directions reaches
  foreground testing, then it reports the missing adapter and leaves that test pending; it does
  not substitute an unguarded script or describe an advisory prompt as enforced protection.
- [ ] **AC19:** Given a successful fresh app build, when handoff would quit/activate the app, then
  existing launch authorization is preserved but foreground disruption waits for the control grant.
  Every running copy of that same app is gracefully asked to quit, unsaved-work prompts are respected,
  and all old copies exit before the exact approved artifact launches; its running executable is verified.
  Stop after old copies exit leaves freshLaunchPending and performs no launch until a new grant.
- [ ] **AC20:** Given supported full-screen, Spaces, multi-display, and Stage Manager configurations,
  when a request/countdown/run occurs, then approval and Stop remain reachable. If the display or
  visibility conditions become unsafe, control stops before further actions.
- [ ] **AC21:** Given malformed/oversized requests, duplicate request IDs, out-of-order progress, or
  lost CLI replies, when retried, then identity and state remain consistent and no duplicate grant starts.
- [ ] **AC22:** Given AX typing temporarily uses the clipboard, when the step ends or is cancelled,
  then it restores its snapshot only if the pasteboard still has its own change count; subsequent
  user clipboard content is preserved. Clipboard contents are not logged.
- [ ] **AC23:** Given an installed helper, when it is updated or removed, then active input stops
  before replacement, unrelated apps/settings survive, and stale executors cannot reconnect with old grants.
- [ ] **AC24:** Given two physical Macs, when each has active clients, then runtime grants and queue
  state remain independent; no runtime control files travel through Git or Syncthing.

## Technical Considerations

### Architecture decision (proposed)

**Choose:** a small native helper owning queue, approval UI, and grant state, plus a typed CLI
connection and a supervised action executor. Keep state transitions serialized in one core module.

**Alternatives:** swiftDialog offers a quick UI but needs the same custom broker/executor and adds
another UI process to supervise. Hook-only gating does not control in-flight commands and has
documented error/coverage gaps. Provider-specific controls are useful but do not establish a shared
Codex/Claude/tool queue. A VM or a second Mac is a possible later isolation strategy.

**Consequence:** the early deliverable is a tested protocol and one compatible action path, followed
by native UI. Do not build a general automation platform or promise that arbitrary same-user programs
are locked out. The helper coordinates participating clients; it is not a macOS security boundary.

### Integration gate

Before committing to a backend, record its installed version, session identification, action path,
focus/clipboard effects, batching, cancellation API, child-process behavior, and actual hook coverage.
Prove these properties using a disposable test app and harmless text, never the user's active editor.

The first proposed real backend is an owned AX-by-name executor, following existing cookbook
experience. Prefer targeting known elements over coordinate clicks. This is a small adapter for
app activation, element press, and bounded text entry; discovery and test-plan generation stay outside it.
Whether this path satisfies the user's currently interrupting sessions remains an implementation gate.

Codex/Claude may call the same CLI with explicit session identity. Hooks may detect legacy entry points
and return an immediate denial pointing to the helper. They must not wait indefinitely for the user,
return a blanket permission allow, or stand in for executor-level validation. Any MCP bridge uses the
same protocol and tests. Native provider computer-use integration stays unverified until cancellation
and interception are demonstrated on the installed version. AppProbe is optional future integration.

### State machine and queue

```text
queued → awaitingDecision → countdown → active → stopping → finished
                     ├→ denied
                     └→ deferred → awaitingDecision (human Review only)
countdown → cancelled
active → stopping (stop / expiry / error / disconnect / intervention)
stopping → interventionRequired (cannot prove quiescence)
```

- One slot covers countdown, active, stopping, and interventionRequired. Other ready requests use
  FIFO order. A deferred request leaves the ready queue; Review appends it to that queue.
- No agent-facing approve operation. Only helper UI decisions can reserve a request. A duplicate
  request with the same client/key returns its existing outcome. A new request after No requires
  renewed user intent in that session; Directions must not loop around a rejection.
- Freeze the approved request revision and a finite typed step manifest: target identities, action
  classes, selectors, text/payload digests, and limits. Caller changes require a new approval. Resolving
  an approved selector to a live AX handle does not authorize changing that selector or its payload.
- Bind a grant to a broker-generation ID, request ID, client identity, target app instances, scoped
  actions, and a monotonic deadline. Session labels are display metadata, not ownership credentials.
- The broker issues an opaque random capability scoped to that sequence and live connection incarnation.
  It is not a reusable shell permission. Each step ID is admitted/consumed atomically at most once;
  retries return its recorded result and cannot repeat input. A lost result never means retry the click.
- Same session/subagent labels do not imply shared authority: use a per-connection client ID and
  explicit parent/child labels. Do not infer identity by choosing the newest transcript or process.
- Heartbeats demonstrate client liveness, not progress. Proposed interval: one second, loss threshold:
  three seconds. Progress updates never renew a grant. Broker restart generates a new generation.
- Pending/active grants are in memory. Preferences and a bounded outcome history may persist;
  startup clears transient work. No automatic restart/resume of an input sequence.
- Use an injected continuous monotonic clock that includes sleep for deadlines, and explicit
  sleep/lock/login-session invalidation for both countdown and active state. Wake must never dispatch
  an overdue zero-timer. Disconnect removes queued/deferred requests as well as revoking active work.

### IPC and executor boundary

- Proposed transport: length-bounded newline-delimited JSON over a user-owned Unix-domain socket
  in a verified private runtime directory under the macOS per-user temporary directory. Verify
  ownership, peer UID, and no unsafe symlink replacement. A single broker binds the endpoint;
  stale endpoint recovery must first prove no live broker owns it.
- Runtime directory mode is 0700 and socket access is user-only. No fallback to a project or synced
  directory. The helper runs with the user's privileges; it has no privileged daemon or root executor.
- Settings/history: `~/Library/Application Support/com.lucesumbrarum.MacControl/`, mode restricted
  to the user. Runtime sockets, tokens, queue, logs, and build artifacts stay outside synced projects.
- Versioned operations: register, request, status, progress, execute, cancel, release. Request includes
  project/session labels, target IDs, purpose, steps, duration, and idempotency key. Responses distinguish
  queued, deferred, denied, active, expired, unsupported, and unavailable. No shell-text interpolation.
- CLI polling/wait calls return within 30 seconds with a request ID; host tool timeout is never an
  approval. Input is a structured allowlisted operation, not an arbitrary shell command after a check.
- At actual dispatch, the supervised executor revalidates ownership, target, deadline, and stop state.
  Only one action can be in flight. Validate every event in a text/gesture batch; cap batching so
  cancellation meets AC10. Do not hand clients reusable permission to run unchecked scripts.
- V1 action classes are activate/launch an explicitly identified artifact, gracefully quit the
  named app instances for handoff, AX press of an approved selector, and bounded text entry into
  an approved target. Test-app writes caused by those approved steps are allowed on disposable data;
  arbitrary shell commands, system-setting changes, permission approval, and detached jobs are excluded.
  The immutable-manifest rule prohibits changing approved requests, not the app state a test is meant to change.
- Bind targets to PID plus process-start/code identity, approved artifact identity, and expected
  window/AX selector. Recheck at every action boundary. Record expected executor-driven activation as
  a bounded one-time transition; any other focus change stops control rather than refocusing.
- Initial event bound: one synthetic event admitted per checkpoint, no pre-posted text queue.
  AX calls have a bounded response deadline validated by the spike. A managed job tracks its owned
  worker/process group and start identity; detached descendants are forbidden. PID alone never
  authorizes termination. Quiescence means all admitted work acknowledged or owned workers exited,
  with the disposable target's event recorder confirming no later synthetic events in acceptance tests.
- Revoke admission before cancelling. Terminate only owned input workers if cooperative cancellation
  fails; never kill the whole agent, user app, terminal, or unrelated process. Target app operations
  already triggered may finish independently, which must not be confused with continued input.
- Connection loss stops workers even if the overlay crashes. A new broker may not announce a free
  desktop until old managed workers have been reconciled; unknown worker state blocks new grants.
- interventionRequired retains the slot until explicit remediation proves managed input has stopped.
  A dismiss button or expired timer alone cannot clear it.
- Foreground observation and event-source tagging reduce accidental interference; they do not prove
  exclusion from arbitrary software. Verify physical-input detection and held-key cleanup in the spike.

### Permissions, data, and lifecycle

- Overlay display itself must not demand broad desktop permissions. Request Accessibility/input
  monitoring only for the selected action/stop path. Screen Recording is optional for screenshot
  workflows, not a prerequisite for a text-based progress display. Never request Full Disk Access.
- Permission prompts stay native and require the user's interaction. The helper cannot approve
  its own permission request, nor can a test click the coordinator's Yes button for the user.
- Keep purpose, step labels, outcomes, and timestamps only; no screenshot, typed text, clipboard,
  shell command, or transcript capture in coordinator logs. Proposed retention: latest 100 outcomes.
- Agent-provided text is plain, bounded display content. Same-user automation is trusted to follow
  the protocol; this is not protection against a malicious Accessibility-authorized process.
- Quit/update uses the same stop-and-drain path. No launch-at-login registration in the first pilot.
- Fresh-build quit/relaunch standing authorization still applies. The grant adds scheduling, not
  another build authorization. After Stop/expiry, foreground cleanup also requires a new grant;
  input-worker shutdown and conditional clipboard restoration are bounded stop cleanup only.
- Fresh handoff records the approved artifact and quit/launch phase. Stop before quitting prevents
  handoff; Stop after the old instances exit records freshLaunchPending. A later approved request
  launches that exact artifact after checking it has not changed. No automatic launch after Stop.
- Use disposable test data. Do not copy the cookbook's real-store mutation examples into acceptance tests.

## Verification Strategy

Unit tests use a fake monotonic clock and deterministic event recorder. Integration tests use two
real clients, an owned worker, connection failures, and a disposable target app that records actions.
Assert no-input outcomes at the executor boundary, not only a green UI state or successful hook return.
Measure stop latency, final event timestamps, target identity, and absence of activity from stale clients.

Native acceptance tests cover accidental approval while typing, VoiceOver/keyboard navigation,
countdown cancellation, current-step display, stop delivery, multi-display/Spaces visibility, and
fresh-build handoff. Foreground tests themselves require a scheduled human-approved test window;
before the helper is proven, use a one-time explicit test-window prompt and a supervised harness.
Never treat a helper approving its own test as evidence of human consent.

## Out of Scope

- Universal interception of all macOS input producers or a security sandbox for hostile agents.
- Cloud coordination, remote unlocking, Windows/Linux, simultaneous fast-user-switching desktops.
- Automatic permission approval, time extensions, idle-triggered starts, or suppression of user input.
- Full AppProbe replacement, arbitrary shell wrapping, automatic recovery of half-completed app work.
- General session dashboards, token/cost monitoring, screenshots/video logs, App Store distribution.
- Migrating every historical project harness or installing a full unrelated Codex hooks port.

## Open Questions and Gates

| Question | State | Planned resolution |
|---|---|---|
| Which tools currently interrupt the user? | Occasional cross-project UI tests; Conjoyn example shows shell AppleScript/System Events; local inventory complete | Concrete action bodies and bounded executor compatibility are still measured in task 1.3; see environment evidence |
| Can those backends be stopped and checked at dispatch? | Blocks their adapter, not core design | Tasks 1.2–1.3; unsupported routes stay pending |
| Can synthetic vs physical input and global Stop be distinguished reliably? | Blocks foreground pilot | Task 1.3; no unsupported guarantee |
| Are both Macs' OS/signing/TCC configurations compatible? | First-Mac pilot only until measured | Task 1.1 and separate second-Mac verification |
| Is isolated tools/mac-control the desired long-term home? | Proposed reversible default | Keep package boundaries explicit; extraction can follow later |
| Duration cap, shortcut, and panel placement? | Proposed defaults above | Validate in pilot; preference changes do not alter grant semantics |

## Related

- [Test workflow](../commands/test-app.md), [testing guidance](../34_testing.md)
- [UI conventions](../47_project-ui-conventions.md), [Mac platform](../22_macos-platform.md)
- [Multi-Mac discipline](../37_multi-mac-discipline.md), [machine registry](../MACHINES.md)
- [AX form automation precedent](../cookbook/139-ax-drive-swiftui-settings-form-verify.md)
