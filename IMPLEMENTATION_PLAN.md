# Implementation Plan — Mac Control Coordinator

**Created:** 2026-09-05 · **Status:** Tasks 1.1–1.2 complete; task 1.3 loss timing and Escape/key passed; focus-loss/recovery proof pending

## Goal

Give participating coding sessions scheduled, human-approved foreground Mac control with a shared
queue, five-second countdown, visible time/steps, and reliable cancellation for verified input paths.

## Acceptance Criteria

- [ ] Human Yes is required; typing cannot approve; No/Wait/countdown cancellation produce no input.
- [ ] Two real clients cannot overlap countdown or control; every new owner needs approval.
- [ ] Stop, expiry, disconnect, and restart invalidate grants and drain the supported input executor.
- [ ] Progress/Stop stay visible without stealing focus; unsupported routes cannot claim protection.
- [ ] Directions schedules activating launches and testing while background work can continue.
- [ ] Pilot proves the actual client workflow and safe install/update/removal on the first Mac.

## Specs

- [Feature specification and AC01–AC24](specs/mac-control-coordinator.md)
- [Research, local gap analysis, and backend compatibility](specs/mac-control-research.md)

## Execution rules and boundaries

- Planning delivered documents only. Execution completed inventory/protocol and the separately
  user-approved Stop, disconnect and heartbeat-loss cases. Further foreground cases need an agreed window;
  task listing alone authorizes neither desktop input nor installation.
- Build an isolated package in `tools/mac-control/`; do not turn the documentation repository root
  into an app project. `C` below means `tools/mac-control` and `V` means `verification/mac-control`.
- Wave 1 may create C as a non-package directory for protocol fixtures and a standalone spike.
  Task 2.1 adds the production package structure after that spike passes; it does not require an empty directory.
- Unchecked tasks' source/test paths and commands below are **planned**, not already passing checks.
  Task 1.2's protocol and JSON fixtures now exist. Swift package tests become runnable after task 2.1.
  Validation reports live in V with machine, versions,
  date, exact command, result, and limitation. Never mark a spike successful from documentation alone.
- Tasks are one bounded change with a roughly 15–30 minute first work chunk. Split a task at its
  stated boundary if it grows; do not claim a total delivery estimate before Wave 1 measurements.
- User requested lower agents: use a fast model for inventories/fixtures/docs, a balanced model
  for bounded implementation, and deep reasoning for lifecycle/integration review. Tasks in one
  wave may run in parallel only with disjoint file ownership; serialize shared core edits.
- Use the Swift concurrency skill when implementing isolation/cancellation. Keep UI state on the
  main actor and use a serialized core state machine. Native AppKit controls follow the UI spec.
- Foreground experiments require an explicitly scheduled human test window. Before the helper is
  trusted, use a supervised disposable harness and a direct test-window prompt; never self-approve.
- Do not commit, install globally, alter TCC, or deploy automatically merely because a task is listed.
  Future execution authorization determines deployment scope; preserve existing global handlers.

## Tasks

### Wave 1 — Establish compatibility and the enforcement contract

- [x] **1.1 Inventory the actual clients and backends** → `V/environment.md`, research matrix
  - Completed 2026-09-05: [local inventory](verification/mac-control/environment.md) records M1 Max,
    versions, identity hints, absent AppProbe and false shell-child permission preflights. User
    confirms occasional cross-project UI testing; Conjoyn screenshot supplies a shell/AppleScript
    example. This closes inventory, not live backend compatibility or Gate A.
  - Success: names/versions, session identity sources, permissions, action paths, and first-Mac
    target recorded; distinguish native computer use from shell AX/CGEvent. Recheck AppProbe path.
    No secret config values or transcript content collected. AC18, AC24.
  - Backpressure: record `sw_vers`, `xcodebuild -version`, client version queries, and targeted path
    checks individually; audit every matrix row as documented / installed / live-verified.

- [x] **1.2 Freeze the protocol and lifecycle fixtures** → `C/Protocol.md`, `C/Fixtures/protocol/`
  - Completed 2026-09-05: revision 1, six parseable JSON files with 86 declarative scenarios,
    AC01–AC16/AC21 branch review, and independent review fixes. See
    [static verification](verification/mac-control/protocol.md); no runtime behavior verified.
  - Success: message/version/size limits, private endpoint, client incarnation, idempotency,
    immutable request scope, state transitions, deadlines, deny/wait outcomes, and cancellation
    handshake specified; fixtures include wrong owner and stale generation. AC01, AC09, AC21.
  - Backpressure: parse fixture JSON with `python3 -m json.tool <fixture>`; review the transition
    table against every AC01–AC16 branch. No agent-facing approval endpoint.

- [ ] **1.3 Prove bounded input and stop in a disposable target** → `C/Spikes/`, `V/stop-spike.md`
  - Live intervention 2026-09-07: [Escape and physical-key cases passed](verification/mac-control/intervention-live.md)
    with 8.233833/1.490500 ms drains, 12 matching events and six prefixes each. All processes exited 0;
    window ended. Next: separate disposable focus-loss fixture; broader intervention/recovery still pending.
  - Preparation 2026-09-07: [Escape/physical-key window ready](verification/mac-control/prepared-intervention-window.md);
    32 offline tests passed; the subsequently approved live results are above. Manual app switching can stop
    on physical input before the focus check, so independent focus-loss needs a separate fixture.
  - Live recheck 2026-09-07: [both loss-timing cases passed](verification/mac-control/loss-timing-live.md).
    Actual loss-to-detection upper bounds 0.054708/2680.620666 ms; drains 15.640375/0.260625 ms.
    Both clients/supervisors and all owned native children exited 0. Window finished; intervention,
    clipboard and recovery remain pending. AC12 and Gate A stay incomplete.
  - Offline follow-up 2026-09-06: [loss instrumentation](verification/mac-control/loss-instrumentation.md)
    adds real fault/heartbeat brackets, supervisor detection/receive timestamps, conservative deadline
    assertions and teardown-failure rejection. 32 offline tests passed, including real pipes to a
    synthetic Python peer. Independent review findings fixed. Next: agreed live timing recheck.
  - Partial result 2026-09-06: [disconnect and heartbeat-loss drains](verification/mac-control/loss-cases.md)
    passed at 11.109334/10.571042 ms; both targets/workers exited. Heartbeat age at detection was
    3003.094042 ms; client loss-injection times are unlogged, so exact detection latency is unproven.
    Subsequent offline instrumentation is recorded above; those assertions still need a live recheck.
    This remains an active task 1.3 evidence gap, not a new backlog item or a completed AC12.
  - Partial result 2026-09-05: [standalone harness](tools/mac-control/Spikes/README.md) built and
    [first live case](verification/mac-control/stop-spike.md) passed from the actual Codex session:
    six correct characters, 12/12 event receipts/origins, 11.716291 ms input drain, both children
    exited. Requires approved execution outside the shell sandbox; no TCC changes. The subsequent
    disconnect/heartbeat-loss results are above. Crash/recovery, clipboard and intervention still
    block completion and Gate A; 16 offline tests do not substitute for those experiments.
  - Success: tiny owned AX action path demonstrates targeting, text-event boundaries, worker
    supervision, crash stop, input-origin handling, global shortcut, focus loss, and clipboard
    cleanup. Measure AC10's one-second stop and AC12's three-second disconnect limits. AC10–AC16, AC22.
    The standalone spike accepts a minimal typed CLI request and stop signal; invoke it from one
    actual installed agent session to prove transport access without requiring the production CLI.
  - Backpressure: compile/run the minimal spike only in the approved test window; record target
    event timestamps for stop mid-entry and wrong-focus cases. No real editor or user store used.

**Gate A:** 1.1–1.3 must show that at least one path usable by the user's actual sessions can be
controlled and stopped using the minimal spike client. This is executor/transport viability, not full
provider compatibility, which remains Wave 5's gate. If native backends cannot comply, select the CLI path
only if it covers the required test workflow. If no path does, stop executor/UI expansion and
revise the plan around the evidence. An advisory popup is not a successful substitute.

### Wave 2 — Package, ownership, queue, and time

- [ ] **2.1 Scaffold the isolated Swift package and test harness** → `C/Package.swift`, `C/AGENTS.md`, `C/README.md`, `C/Sources/`, `C/Tests/`
  - Depends on: Gate A.
  - Success: Core library, AppKit executable, CLI executable, fake clock, and recording executor
    fixtures build without a root package; deployment target follows the spike.
  - Backpressure: `swift build --package-path tools/mac-control`; `swift test --package-path tools/mac-control`.

- [ ] **2.2 Implement private IPC and client identity** → `C/Sources/ControlCore/Transport/`, `C/Tests/TransportTests/`
  - Depends on: 2.1 (sequential within wave).
  - Success: single broker endpoint, framing bounds, peer validation, connection incarnations,
    idempotent replies, safe stale-endpoint recovery, and no arbitrary shell execution. AC09, AC21.
  - Backpressure: `swift test --package-path tools/mac-control --filter TransportTests` including
    malformed frames, two binders, reconnect, ownership mismatch, and unsafe endpoint fixtures.

- [ ] **2.3 Implement request queue and human decision transitions** → `C/Sources/ControlCore/Queue/`, `C/Tests/QueueTests/`
  - Depends on: 2.1; may parallel 2.2 with separate files.
  - Success: single reservation, FIFO ready queue, explicit deferred Review, terminal rejection,
    request cancellation/disconnect, and decisions bound to immutable request revision. AC01, AC03–AC06, AC21.
  - Backpressure: `swift test --package-path tools/mac-control --filter QueueTests` with simultaneous
    approvals/cancel, reordered replies, duplicate requests, and no automatic deferred starts.

- [ ] **2.4 Implement countdown, deadlines, and liveness** → `C/Sources/ControlCore/Grant/`, `C/Tests/GrantTests/`
  - Depends on: 2.2, 2.3 (sequential).
  - Success: five-second countdown precedes grant, duration starts at activation, monotonic expiry,
    heartbeat failure and broker generation invalidate grants; sleep/lock cannot renew them. AC05–AC06, AC09, AC12–AC13.
  - Backpressure: `swift test --package-path tools/mac-control --filter GrantTests`; fake-clock
    boundary tests immediately before/at/after zero and deadline, restart, clock jumps, and sleep.

### Wave 3 — Enforce input and prove quiescence

- [ ] **3.1 Implement typed action admission and target checks** → `C/Sources/ControlCore/Execution/`, `C/Tests/AdmissionTests/`
  - Depends on: Wave 2.
  - Success: actual dispatch checks grant, owner, immutable scope, instance identity, deadline and
    stop state; only one action is in flight; changed request content needs reapproval. AC09, AC15, AC21.
  - Backpressure: `swift test --package-path tools/mac-control --filter AdmissionTests`; target
    replacement and mutated action fixtures must yield zero recorded input. Replay an admitted step
    ID after a lost reply: return its recorded outcome with no second event; reconnect/stale capabilities reject.

- [ ] **3.2 Implement the bounded AX worker** → `C/Sources/ControlExecutor/`, `C/Tests/ExecutorTests/`
  - Depends on: 3.1.
  - Success: activation, AX press, and bounded text entry reuse the proven spike contract;
    per-event cancellation, expected-focus checks, owned-child supervision and clipboard change-count
    cleanup; no detached script escape or unrestricted run-shell API. AC10, AC14–AC15, AC22.
  - Backpressure: `swift test --package-path tools/mac-control --filter ExecutorTests`; approved
    disposable-target run records typing, cancellation between events, clipboard conflict, and held-key cleanup.

- [ ] **3.3 Implement revoke, drain, and failed-stop handling** → `C/Sources/ControlCore/Stopping/`, `C/Tests/StopTests/`
  - Depends on: 3.2.
  - Success: stop closes admission before cancellation; no next owner until quiescence; only owned
    worker processes may be terminated; unresolved stop stays interventionRequired. AC10–AC13, AC23.
  - Backpressure: `swift test --package-path tools/mac-control --filter StopTests`; inject a hung
    action, dropped connection, worker crash, helper crash, stale process identity, and late completion.

- [ ] **3.4 Verify two-client exclusivity at the executor boundary** → `C/Tests/TwoClientTests/`, `V/enforcement.md`
  - Depends on: 3.3.
  - Success: two real IPC clients cannot overlap actions or reuse stopped grants; old managed
    workers are reconciled on helper restart; actual event evidence meets AC01, AC09–AC13, AC21.
  - Backpressure: `swift test --package-path tools/mac-control --filter TwoClientTests`; record
    repeated simultaneous acquisition/expiry/cancel runs and real-worker stop latency.

- [ ] **3.5 Implement fresh-build handoff and interrupted-launch recovery** → `C/Sources/ControlExecutor/FreshBuildHandoff.swift`, `C/Tests/HandoffTests/`
  - Depends on: 3.3; may follow 3.4 sequentially to avoid executor-file conflicts.
  - Success: enumerate only the named app's instances across paths, request graceful quit, respect
    unsaved prompts, verify all old instances exited, and launch/verify the immutable approved
    artifact. Stop after quit records freshLaunchPending and cannot launch without a new grant. AC19.
  - Backpressure: `swift test --package-path tools/mac-control --filter HandoffTests`; disposable
    same-app instances from two paths, a save-prompt fixture, changed artifact, and Stop before quit,
    while waiting for quit, after quit, and before launch; assert exact resulting executable identity.

**Gate B:** no visible Control returned until the event recorder and worker acknowledgement agree.
Tasks 3.1–3.5 complete before Wave 4. Unmet cancellation timing or unknown worker liveness blocks
the foreground pilot and new grants.

### Wave 4 — Native request and progress interface

- [ ] **4.1 Add menu-bar queue and safe request panel** → `C/Sources/MacControlApp/QueueController.swift`, `RequestPanel.swift`, `C/Tests/DecisionBindingTests/`
  - Depends on: Gate B.
  - Success: native nonactivating panel, target/session/duration/steps, Yes/No/Wait, explicit
    deferred Review, no default approval key, immutable decision binding. AC02–AC04, AC21.
  - Backpressure: `swift build --package-path tools/mac-control`; `swift test --package-path tools/mac-control --filter DecisionBindingTests`;
    manual disposable-editor test: ordinary Return/Space and first click cannot accidentally approve.

- [ ] **4.2 Add countdown and running overlay** → `C/Sources/MacControlApp/CountdownPanel.swift`, `ProgressPanel.swift`
  - Depends on: 4.1.
  - Success: cancellable 5→0, correct time allowance/current step, Stop, and Stopping/returned
    states bound to core events; missing progress stays honest. AC05–AC08, AC11.
  - Backpressure: `swift build --package-path tools/mac-control`; replay protocol fixtures into
    the running UI and record time/update behavior in `V/ui.md`.

- [ ] **4.3 Wire emergency stop and environment loss** → `C/Sources/MacControlApp/InterventionMonitor.swift`, `C/Tests/InterventionTests/`
  - Depends on: 4.2.
  - Success: proven shortcut, physical intervention, unexpected focus, permission/monitor loss,
    lock/sleep, and unavailable visibility revoke control; no forced input suppression. AC06, AC13–AC16, AC20.
  - Backpressure: `swift test --package-path tools/mac-control --filter InterventionTests` plus
    approved native smoke run of the shortcut, monitor disablement, and physical input.

- [ ] **4.4 Verify placement and accessibility** → `C/Sources/MacControlApp/PanelPlacement.swift`, `V/ui.md`
  - Depends on: 4.3.
  - Success: keyboard/VoiceOver flow, Stop reachability, full-screen/Spaces/Stage Manager/display
    changes verified; unsupported configurations visibly block start. AC02, AC07, AC20.
  - Backpressure: manual matrix in V/ui.md with actual OS/display setup, result, and limitations;
    build after any placement changes. Do not add new ornamental UI or settings scope.

### Wave 5 — Actual agent clients and Directions workflow

- [ ] **5.1 Implement CLI request/status/progress/action lifecycle** → `C/Sources/MacControlCLI/`, `C/Tests/CLITests/`
  - Depends on: Wave 4; protocol/transport already available.
  - Success: typed JSON operations, stable client/request IDs, bounded waits, explicit outcomes,
    no approval API, and no caller-controlled execution outside the grant. AC03–AC04, AC09, AC21.
  - Backpressure: `swift test --package-path tools/mac-control --filter CLITests`; end-to-end
    request/wait/deny/approve/stop from two CLI processes using the disposable target.

- [ ] **5.2 Verify Codex client integration** → `C/Integrations/codex.md`, `V/codex.md`
  - Depends on: 5.1.
  - Success: real installed Codex session registers and performs the shared CLI workflow;
    unrelated background work continues; native provider path remains explicitly unsupported
    unless separately demonstrated. AC17–AC18, AC21.
  - Backpressure: record actual session request, Wait, later approval, progress, Stop, and stale
    retry outcomes; verify no changes to host sandbox/approval semantics. Add only a proven adapter.

- [ ] **5.3 Verify Claude client integration** → `C/Integrations/claude.md`, `V/claude.md`
  - Depends on: 5.1; may parallel 5.2 read-only/client work, but never parallel desktop control.
  - Success: same lifecycle from installed Claude; do not remove provider lock files or assume
    interactive hook defer; preserve native permissions. AC17–AC18, AC21.
  - Backpressure: same actual-session cases as 5.2; then interleave Codex/Claude requests and
    demonstrate one shared reservation and mandatory approval per owner when both paths work.
    An unavailable provider is recorded unsupported with AC18 evidence, never marked integration-passed.

- [ ] **5.4 Add shared Directions control procedure and routing** → `commands/test-app.md`, `34_testing.md`, new `48_mac-control.md`, `CODEX-GLOBAL-TEMPLATE.md`, `CLAUDE-GLOBAL-TEMPLATE.md`
  - Depends on: 5.2, 5.3.
  - Success: one read-on-demand procedure; gate before first disrupting launch/focus/input;
    missing helper/adapter leaves foreground testing pending; safe background work continues;
    timeout/Stop requires reapproval; fresh-build scheduling preserves existing authorization. AC17–AC19.
  - Backpressure: `rg -n 'control|grant|foreground|launch|unsupported' <touched-files>`;
    inspect/run `scripts/gen-directions-index.sh` as documented; `git diff --check`.
    Reconcile AppProbe-only wording without claiming AppProbe is installed.

**Gate C:** before deployment, at least one actual user workflow must pass the production CLI
integration. Two-client exclusion is always required. Cross-provider compatibility is claimed only
after both providers pass; an unsupported provider is an explicit coverage limitation and cannot
silently fall back to unguarded foreground control.

### Wave 6 — Package and validate deployment without broad rollout

- [ ] **6.1 Add reproducible app packaging and diagnostics** → `C/scripts/build-app.sh`, `C/Resources/Info.plist`, `C/Sources/MacControlCLI/Doctor.swift`
  - Depends on: Wave 5 and Gate C.
  - Success: fresh runnable bundle with stable identity, recorded signing strategy, required-only
    permissions, helper/worker version check, and doctor reporting adapter support; no secrets shown. AC16, AC18.
  - Backpressure: `bash -n tools/mac-control/scripts/build-app.sh`; run that script, inspect bundle
    identity/signature, and run packaged CLI doctor. Record exact artifact path.

- [ ] **6.2 Add opt-in install/update/removal with a temporary-home dry run** → `C/scripts/install.sh`, `C/Tests/InstallFixtures/`, `C/README.md`
  - Depends on: 6.1.
  - Success: explicit dry-run/install/uninstall, graceful drain before replacement, private runtime
    state, no default login item, preserve unrelated config, no live grants restored. Existing
    Directions deployers only link to opt-in setup; no automatic new permission grant. AC23–AC24.
  - Backpressure: `bash -n tools/mac-control/scripts/install.sh`; temporary-home install/update/
    removal fixture including active-worker refusal and unrelated-file preservation; `git diff --check`.

### Wave 7 — Acceptance, independent review, and pilot handoff

- [ ] **7.1 Run the full acceptance matrix** → `V/acceptance.md`, spec checkboxes
  - Depends on: Wave 6.
  - Success: each AC01–AC24 has evidence or a clearly blocking failure; two real clients and,
    when both integrations pass, a real cross-provider queue;
    Stop/expiry/crash/restart, clipboard, physical intervention, and fresh-build scenarios covered.
    AC24 gets two-Mac evidence only when the second Mac is actually available.
  - Backpressure: `swift test --package-path tools/mac-control`; packaged disposable-target
    acceptance run in the approved test window; report latency and unsupported environments.

- [ ] **7.2 Independent lifecycle and integration review** → `V/review.md`
  - Depends on: 7.1.
  - Success: reviewer checks wrong-owner/target, mutated request, stale generation, hidden worker,
    hook failure, UI accidental consent, and false-returned-control cases; resolve material findings.
  - Backpressure: rerun only checks affected by review fixes; every finding links to resolution/evidence.

- [ ] **7.3 Pilot launch and Directions handoff** → `V/pilot.md`, `PROJECT_STATE.md`, `TASKS.md`
  - Depends on: 7.2; installation scope must be authorized for execution.
  - Success: first-Mac pilot uses exact fresh artifact, previous helper instances exit gracefully,
    running executable path verified; unsupported backends and second-Mac status visible; setup and
    rollback instructions concrete. Keep wider rollout pending until actual-session pilot succeeds.
  - Backpressure: record first-Mac Yes/Wait/Stop experience, exact executable path, and safe return
    of control; `git diff --check`; `git status --short`. Use `/log` when executing the handoff.

## Sprint and dependencies

**25 tasks across 7 waves.** Tasks 1.1–1.2 are complete and archived. Current Sprint now contains
1.3 and 2.1 only; 2.1 remains behind Gate A. Later tasks are in Backlog. Task-level dependencies override any within-wave parallelism.
The first milestone is **Gate A**, not a polished overlay. The second is **Gate B**, proven enforcement.

## Blocked Tasks / Open Gates

- UI-test interruption scope is identified across projects; the Conjoyn example shows shell
  AppleScript/System Events. Exact legacy actions remain unverified; task 1.3 must prove a bounded
  replacement usable by actual sessions. No native or legacy backend is declared supported yet.
- Global Stop and physical-input discrimination require live measurement in task 1.3.
- User reiterated shared screen scheduling across simultaneous sessions on 2026-09-05. Preserve
  one FIFO ready queue, human Yes per turn, explicit Review after Wait, and drain before handoff
  in tasks 2.3/3.4; the spike's mutual-exclusion lock is not a substitute for the queue.
- AppProbe adapter is outside v1 unless source/tooling is found and an actual need established.
- Second-Mac validation cannot be represented by a local simulation; track it separately if unavailable.

## Operational Learnings

- Hooks alone are not a reliable control boundary; official docs describe coverage and error gaps.
- AX automation can affect focus and clipboard even when described as headless.
- Approval time and action dispatch are distinct; restart, late replies and changed requests must not
  make an old approval authorize new input.

## Execution Log

| Wave | Started | Completed | Evidence |
|---|---|---|---|
| Planning | 2026-09-05 | 2026-09-05 | Spec, primary-source research, repository audit, independent planning review |
| 1 | 2026-09-05 | — | Tasks 1.1–1.2 complete; task 1.3 built and first live Stop case passed; broader proof pending |
| 2–7 | Not started | — | No implementation/build/desktop test performed |
