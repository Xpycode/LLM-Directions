# Implementation Plan — Mac Control Coordinator

**Created:** 2026-09-05 · **Status:** Tasks 1.1–1.2 complete; task 1.3 loss timing, Escape/key and focus-loss passed; live recovery proof pending

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

- September 9 delivery review completed: [bounded path to pilot](verification/mac-control/delivery-review.md).
  [Native-preflight CLI/runbook](verification/mac-control/native-preflight.md) now implements disposable
  provision/reload and read-only legacy inspection. [Native storage checks passed](verification/mac-control/storage-and-provenance-review.md);
  original whole-report pins were not located. The [prospective acquisition caller](verification/mac-control/prospective-acquisition.md)
  is now implemented/reviewed in private fixtures; native acquisition/reload precedes any later-boot
  inspection. Gate A still includes recovery and the
  remaining interruption/clipboard cases; legacy initialization alone cannot close it.
- September 9 session close: user asked about time to a usable tool and was surprised by 2/25
  completed tasks. Next session starts with a bounded delivery review before more infrastructure:
  identify the shortest path through live recovery to a pilot (one input path, queue, Yes/No,
  countdown, Stop). This is a proposed focus, not approval to skip Gate A or reduce acceptance scope.
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
  - Latest continuation: [inventory disappearance contract](verification/mac-control/inventory-contract-review.md)
    implemented/reviewed; 406 broad-suite passes/one skip and 29 final focused passes.
    One native observation passed with marker unchanged. Fresh acquisition then failed at
    observation 3/final/inventoryAfterFirstScanChanged after retention; no reload/retry.
    Preserve all five transactions. Next review bounded inventory-change handling before
    another capture; task 1.3/Gate A remain open.
  - Latest continuation: [native identity-read review](verification/mac-control/identity-read-review.md)
    added fixed errno/return categories; 397 tests passed/one skip and independent review passed.
    One native observation failed with `processIdentityFirstScanReadMissing` (zero/ESRCH), marker
    unchanged. No capture/retry. Next review all-process stability/completeness against real
    process churn; no identity exclusion or gate relaxation is authorized by this result.
  - Latest authorized capture: [precise native failure](verification/mac-control/fresh-caller-review.md#authorized-native-outcome)
    at observation 3/final/processIdentityFirstScanRead after baseline retention. Journal preserved;
    no reload/retry. Four failed transactions retained. Next offline native-adapter read review.
  - September 10 caller preparation: [fresh caller review](verification/mac-control/fresh-caller-review.md)
    passed read-only location inspection, 23 focused tests and independent review. Exact fresh
    capture/reload caller is ready for separately agreed native scope; no capture run. Gate A open.
  - September 10 offline review/fixes: [final-observation packet](verification/mac-control/final-observation-review.md)
    distinguishes first/second identity scan read vs malformed data and acquisition observations 1–4.
    Tracked caller uses append-only timeout/outcome reporting; both late failures have regressions.
    Final suite 386 passed/one skip; independent review passed. Selected offline scope complete,
    task 1.3/Gate A open. Next prepare/review fresh caller configuration before separate native scope.
  - September 10 continuation: [inventory-boundary review](verification/mac-control/inventory-boundary-review.md)
    separates raised-query, malformed-inventory and observed-PID-change diagnostics without
    changing completeness or retry rules. Full suite: 369 passed/one existing skip; final focused
    suite: 34 passed. One native diagnostic passed with unchanged marker. Subsequently authorized
    acquisition failed at `processIdentity` in final observation after baseline retention.
    Witness/archive/anchor preserved; no reload/retry. Review that failure next; task 1.3/Gate A open.
  - Latest diagnostic continuation September 9: [safe stages and fresh attempt](verification/mac-control/context-probe-diagnostics.md).
    367 full-suite passes/one skip; 14 final probe tests passed. Three native diagnostics passed,
    then fresh capture failed at `inventoryAfterFirstScan`. Preserve both partial transactions;
    next inventory-boundary review, no automatic retry/reboot or Gate A completion.
  - Latest native attempt September 9: [acquisition failed before baseline retention](verification/mac-control/prospective-acquisition-live.md).
    Bounded context failure reproduced read-only, then later diagnostic probes passed. Preserve
    the partial transaction; no retry, reload or reboot. Next: safe probe-stage diagnostics before
    a separately arranged fresh acquisition. Nine focused tests passed; Gate A remains open.
  - Prospective acquisition September 9: [capture/reload caller and procedure](verification/mac-control/prospective-acquisition.md)
    use existing storage schemas/APIs, bind the acquired-now historical archive in a freshly retained
    baseline, and pass nine focused tests. Native acquisition is next; no live marker access or recovery pass.
  - Native storage September 9: [location validation/provenance search](verification/mac-control/storage-and-provenance-review.md)
    passed disposable provision and separate-process reload at both local parents. Original writer
    records lack whole-report pins. Next review prospective acquisition/retention using existing APIs;
    no marker access or recovery pass, no reboot requested.
  - Runnable preflight September 9: [CLI and native procedure](verification/mac-control/native-preflight.md)
    pass 13 focused tests, including separate-process provision/reload and read-only rejection cases.
    Native storage locations and original independently retained provenance remain unverified;
    no native initialization, build or recovery pass. Existing repeat-run and Gate A gaps remain.
  - Persistent provisioning September 9: [independent restart identities](verification/mac-control/persistent-witness-provisioning.md)
    create immutable slots and a separate configured anchor; crash, replacement, flush and caller
    integration tests pass. Next deployment-location validation/read-only native preflight;
    historical marker unresolved and no persistent installation or live bootstrap occurred.
  - Native caller continuation September 9: [caller/witness retention](verification/mac-control/native-caller-retention.md)
    implements explicit activation with independent transition/acknowledgement slots and crash tests.
    Persistent slot provisioning and external trust-anchor retention remain before native use;
    historical marker unresolved, no live bootstrap or recovery pass.
  - Activation continuation September 9: [activation and one-shot startup](verification/mac-control/legacy-activation.md)
    implement intent/receipt durability, independently witnessed explicit reconciliation, permanent
    consumption and actual supervisor-entry integration. Native caller/pin retention preparation next;
    historical marker unresolved and Gate A open.
  - Completion continuation September 9: [seal and read-only preflight](verification/mac-control/legacy-completion-seal.md)
    retain external completion evidence only during fresh initialization, validate pinned audit/context
    and exact namespace continuity. Storage faults and subprocess death retain startup fences. Next
    activation/one-shot consumption with launcher integration; no native bootstrap or recovery pass.
  - Activation preparation September 9: [reviewed contract/native handoff](verification/mac-control/legacy-activation-preparation.md)
    defines completion seal, durable commit, interrupted-publication handling and one-shot admission.
    Reproduced/fixed clean-marker rewrite acceptance at six initialization boundaries; v2 audit binds
    post-clean fingerprint. Next completion seal/read-only preflight offline; launcher remains fenced.
  - Bootstrap continuation September 9: [fenced initialization](verification/mac-control/legacy-bootstrap-implementation.md)
    checks independently pinned provenance, different boot and exact namespace continuity; retains
    durable fence/full audit. Launcher rejects all bootstrap artifacts. Offline process-death tests
    enter the actual launch gate. Next separate activation review and concrete native handoff.
  - Native preflight September 9: [inventory visibility passed](verification/mac-control/native-context-live.md)
    outside sandbox; locked legacy marker bytes/metadata and boot baseline retained unchanged.
    [Legacy bootstrap review](verification/mac-control/legacy-bootstrap-review.md) requires a separately
    tested initialization transaction and verified later boot; no marker clear or recovery pass.
  - Locked continuation September 9: [post-teardown reconciliation](verification/mac-control/recovery-reconciliation.md)
    borrows original marker ownership and waits for setup/writer release, including late construction.
    Bounded context helpers share the continuous clock; all verdicts remain non-authorizing.
    Next native context visibility and historical-marker review; no native recovery pass.
  - Supervisor continuation September 9: [single-reader integration](verification/mac-control/recovery-supervisor.md)
    gates fault injection on independent final-ack binding and collects native-format EOF/waits.
    Review fixed post-signal reservation race; synthetic verifier integration stays non-authorizing.
    Next retained-evidence reconciliation under the existing lock; native validation remains pending.
  - Native transport continuation September 9: [wire/ack adapter](verification/mac-control/recovery-native.md)
    adapts Swift schemas, requires explicit continuous clock, returns exact writer acknowledgement
    bytes and supports target EOF after fence. Twelve offline tests; text-progress review fix applied.
    Next single-reader supervisor integration offline; native recovery remains unverified.
  - Context continuation September 9: [Darwin inventory probe](verification/mac-control/recovery-context.md)
    adds bounded UID enumeration, stable process/path/context checks and locked-adapter integration.
    Fifteen offline tests passed; native visibility and observer/ack transport remain unverified.
    Next native transport preparation offline; historical marker remains unresolved.
  - Adapter continuation September 9: [locked snapshot and owned evidence](verification/mac-control/recovery-adapter.md)
    connect actual files/locks/pipes/waits to the verifier. Final acknowledgement requires collected
    receipts/checkpoints followed by observed worker liveness, fixing delayed-poll false acceptance.
    Next Darwin context/inventory probe offline; native integration and historical marker remain unresolved.
  - Verifier continuation September 9: [read-only evidence checker](verification/mac-control/recovery-verifier.md)
    binds marker/record, checkpoints, receipts, owned exits and observation; separate new-boot path.
    Offline candidates never authorize restart. Next trusted snapshot/evidence adapter in isolated tests;
    historical marker and native recovery remain unresolved.
  - Admission continuation September 9: [durable admission](verification/mac-control/recovery-admission.md)
    connects OS identity setup, pair reservations and checkpoint/write acknowledgements to crash-mode
    dispatch. Real-writer tests cover Stop/heartbeats during stalled I/O; early-bound and receipt-kind
    review findings fixed. Next read-only restart/reconciliation verifier offline; no native recovery claim.
  - Further offline continuation September 9: [checkpoint/storage](verification/mac-control/checkpoint-storage.md)
    wires checkpoint transport into controlled-crash sequencing and adds a separately tested writer.
    89 tests passed; Swift edit uncompiled. Next: verified OS identities and admission integration,
    including write deadlines and Stop/watchdogs during stalled I/O. Marker remains unresolved.
  - Offline continuation September 9: [versioned record model](verification/mac-control/recovery-record.md)
    adds strict parsing, cumulative checkpoint transitions and simulated durable acknowledgements.
    Runtime remains unchanged. Next: worker checkpoint transport and nonblocking persistence;
    retain the legacy unresolved marker and keep Gate A open.
  - Review September 9: [reconciliation contract](verification/mac-control/worker-crash-reconciliation.md)
    retains the unresolved marker. `posted` precedes local held-state update; the marker lacks run
    identity and traces are not a pre-dispatch durable ledger. Next bounded work: versioned spike
    record parser/transitions offline, then explicit worker checkpoint and nonblocking persistence.
  - Live September 9: [worker-crash observation retained](verification/mac-control/worker-crash-live.md).
    Six correct characters, 12 matched events; EOF detection upper bound 1.794583 ms; target fence
    at 2032.261375 ms. Worker exited -9, target 0, all processes closed. No closure/drain proof;
    marker unresolved and window ended. Next: offline evidence-specific reconciliation contract review.
  - Prepared September 9: [native worker-crash case](verification/mac-control/prepared-worker-crash-window.md).
    61 offline tests passed. Six complete pairs precede owned-worker kill; independent client trace
    and target fence preserve evidence. Case intentionally retains unresolved marker and failure exit.
    Next: agreed compilation/foreground window for one case; no native run yet.
  - Observer September 9: [independent subprocess observer passed](verification/mac-control/recovery-observer.md).
    57 tests passed; standalone trace retains worker EOF/closure and recorder fence across synthetic
    supervisor death. Next: prepare native between-pairs worker-crash source/transport with offline
    tests, preserving parent identity. Native supervisor-death and held-key cleanup remain unproven.
  - Offline September 9: [recovery preparation](verification/mac-control/recovery-preparation.md).
    49 tests passed: synthetic crash/hung-event handling and isolated real lock retention after
    abrupt process exit. Next: independent observer fixture using synthetic subprocesses; existing
    in-memory trace/target EOF lifetime cannot support a supervisor-crash measurement. No live recovery pass.
  - Final September 9: [independent focus-loss case passed](verification/mac-control/focus-loss-live.md).
    Detection11.248584ms, drain0.04275ms, all12 events and fences, zero sink input, all exits0.
    Prior marker reconciled from full retained evidence; final marker clean. Recovery/clipboard still pending.
  - Latest September 9: [focus detection/drain measured, shutdown failed](verification/mac-control/focus-loss-shutdown.md).
    Detection16.80225ms, drain0.045292ms, 12 matching events, no sink input. Worker SIGTRAP makes
    overall case fail. Fixed cached-clock underflow and rebuilt; unresolved marker/retest pending.
  - Retry 2026-09-09: [marker reconciled; startup fixed](verification/mac-control/focus-loss-retry.md).
    Unowned input stopped the worker before typing; both children exited 0, marker clean. Focus-loss
    evidence remains absent. Prepare bounded input-origin diagnostics before another agreed window.
  - Attempt 2026-09-09: [focus sink startup failed before input](verification/mac-control/focus-loss-startup.md).
    AppKit singleton construction fixed and recompiled; corrected artifact not launched. Both owned
    children exited; unresolved marker retained. Reconciliation review/new window precede any retry.
  - Preparation 2026-09-09: [independent focus-loss fixture and window](verification/mac-control/prepared-focus-window.md)
    add an owned focus sink, explicit cause/foreground checks, two evidence fences and offline
    client/supervisor/oracle coverage. Native build/live run await the scheduled window; task remains open.
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
| 1 / 1.3 continuation | 2026-09-10 | — | Sol owned diagnostic source/tests; coordinator owned acquisition regression, integration/state/Git; Astra independently reviewed. 369 broad passes/one skip, 34 final focused passes; one locked native diagnostic passed. [Evidence and authorized acquisition failure](verification/mac-control/inventory-boundary-review.md). Capture failed in final process-identity observation after retention; no reload/retry. Local execution commits; no push. Gate A remains open. |
| 1 / 1.3 offline fixes | 2026-09-10 | Selected scope complete | Sol owned identity diagnostics/tests; coordinator owned acquisition reporting, journal runner/caller, integration, docs and Git; Astra independently reviewed. [Final-observation review and validation](verification/mac-control/final-observation-review.md): 386 full-suite passes/one skip. Scoped local execution commit; no push. Native recovery/Gate A remain open; next prepare/review fresh caller configuration before separate native scope. |
| 2–7 | Not started | — | No implementation/build/desktop test performed |
| 1 / 1.3 native capture | 2026-09-10 | Failed/incomplete | User authorized exact caller; coordinator repeated inspect and ran once. Observation 3/final/processIdentityFirstScanRead failed after retention; journal retained, no reload/retry. [Outcome](verification/mac-control/fresh-caller-review.md#authorized-native-outcome). No source changes; local checkpoint, no push. Gate A open. |
| 1 / 1.3 fresh caller | 2026-09-10 | Preparation complete | Coordinator prepared configuration and ran location/syntax checks plus 23 focused tests; fresh-context Astra reviewed independently with no blocker. [Exact proposed operation](verification/mac-control/fresh-caller-review.md). Native scope pending; task/Gate A incomplete. Scoped local commit; no push. |
| 1 / 1.3 identity-read continuation | 2026-09-10 | Blocked/incomplete | Sol owned identity adapter/tests; coordinator owned context integration, regressions, single-observation caller, records and Git; Astra independently reviewed and teardown finding was fixed. [397 passes/one skip and native ESRCH result](verification/mac-control/identity-read-review.md). Marker unchanged; no capture/retry. Local execution commit, no push. Next inventory completeness/stability contract review; task 1.3/Gate A open. |
| 1 / 1.3 inventory contract | 2026-09-10 | Blocked/incomplete | Sol owned context source/tests; coordinator owned helper integration, native callers, records and Git; Astra reviewed proof, final implementation and callers independently. [406 broad passes/one skip, 29 final focused passes, native probe pass and capture failure](verification/mac-control/inventory-contract-review.md). Capture failed at observation 3/final/inventoryAfterFirstScanChanged; fifth transaction preserved, no reload/retry. Scoped local execution commit; no push. Next bounded inventory-change contract review; Gate A remains open. |
