# Mac Control protocol v1

**Contract revision:** 1 · **Date:** 2026-09-05 · **Status:** frozen for the standalone spike.
This is an implementation contract, not a running service or a compatibility claim. Changes found
necessary by the spike must update this document and its fixtures before production implementation.
See the [specification](../../specs/mac-control-coordinator.md) and
[inventory](../../verification/mac-control/environment.md).

## Purpose and boundary

Coordinate foreground UI testing across participating project sessions. Penumbra and Game One
are user-reported examples; occasional interruption is the problem, not every test invocation.
Source reads, builds, unit tests and verified noninterfering inspection need no desktop grant.
An activating launch, focus change, click, key, paste or other interfering UI-test action does.
Do not infer noninterference from a test's name or a shell command returning no visible output.

The broker owns the queue, human decision UI and serialized state. Only its supervised executor
may consume grants. A client receives no permission to run an arbitrary legacy script. This is
coordination among cooperating clients, not exclusion of every same-user input producer.

## Endpoint, ownership and framing

- One broker per user/login session on this Mac. Resolve the OS per-user temporary directory
  independently of client-supplied paths; use its `com.lucesumbrarum.MacControl/control.sock` child.
  Never fall back to a project directory, synced storage, TCP, or a client-supplied socket path.
- Private directory 0700, socket 0600, same effective UID. Verify directory/file ownership and
  reject symlinks at creation and connection. Check peer UID on both sides; it is a boundary
  against other users, not a claim to authenticate a malicious process with the same UID.
- Hold a process-lifetime exclusive lock on a verified private lock file before binding. A second
  broker must exit without touching the socket. Stale socket cleanup requires owning that lock,
  failed liveness verification, and rechecking the same socket identity before unlinking. An
  ambiguous existing owner produces unavailable; PID absence alone is insufficient.
- The broker starts in `recovering`. It may serve status but cannot reserve control until old
  owned workers are reconciled. No queue, grant or capability is restored after restart.
  Broker availability is `recovering` or `ready`, with a separate `interventionRequired` condition
  and remedy when reconciliation is ambiguous. This is separate from a request's state of that name.
- Wire format: UTF-8 JSON object followed by LF, one compact object per line. Maximum **65,536
  bytes before LF**; reject the 65,537th byte without buffering more. Escaped newlines are allowed
  within text; raw multiline JSON, BOM, invalid UTF-8, duplicate keys, nonfinite numbers, unknown
  fields/operations and unsupported `v` reject. Maximum nesting 12; no coercion of strings/numbers.
- Partial-frame timeout 3 seconds; at most 32 accepted-but-unanswered messages per connection,
  32 registered clients, 128 nonterminal requests globally, 8 per client. Resource exhaustion
  returns `busy`; it never drops an existing reservation or evicts a replay record to make space.
- Framing errors close the connection, triggering owner-loss handling. Semantic errors return a
  bounded error with no action. Parsing, status wait and UI work must never block stop/watchdogs.

## Envelopes and identity

Every client frame has `v: 1`, `id` (caller correlation ID), `op` and `body`. After registration it
also has `generation`, `clientId`, `incarnation`, all required. Registration rejects those three
fields. All fields listed for an operation are required unless explicitly described as optional.

Envelope `id` is a decimal-string integer from 1 to 2^53−1; send new calls in strictly increasing
ID order on a connection. Other identifiers and idempotency keys are 1–64 ASCII letters/digits/underscore/hyphen. Broker-issued
generation, client, incarnation, request and grant IDs contain at least 128 random bits. Capabilities
contain 256 random bits, encoded as 64 lowercase hex characters. Do not write capabilities to logs,
files, command-line arguments, environment variables or project state.

Success: `{v, id, ok:true, generation, body}`. Error:
`{v, id, ok:false, generation, error:{code, remedy}}`; `generation` is null only before a broker
generation can be reported. `remedy` is a plain string of at most 512 UTF-8 bytes, never raw parser
input, credentials or typed content. A response is at most one frame; status is paginated.

One persistent CLI connection registers one owner and incarnation. Provider/session/parent labels
are display hints, not credentials. `CODEX_THREAD_ID` can supply a correlation label; never find a
session by scanning transcripts. Reconnect registers a new owner/incarnation and cannot resume an
old grant. A future adapter must keep the owning CLI alive while waiting or executing; repeated
short-lived shell invocations cannot impersonate that connection. Invocation and sandbox viability
are measured in task 1.3, not assumed here.

For envelope replay, retain a keyed fingerprint of the validated frame and the reply for the latest 128 completed IDs and
all outstanding IDs (maximum 32). An exact retransmission of a retained ID waits for or replays
that same reply; it never executes again. Changed content for a retained ID returns
`idempotencyConflict`. An ID at or below the accepted high-water mark that is no longer retained
returns `staleMessage`, with no effect. Never reinterpret an old ID as a new operation. A cached
snapshot is historical; clients must merge by stateVersion and fetch current status as needed.
Request `key` and immutable `stepId` additionally protect business operations retried under new IDs.
Validate connection generation/owner/incarnation before any replay lookup. Execute retries also
require a currently active valid grant before returning a cached reply. A release already accepted
may replay its original acknowledgement after stopping, solely for that original owner/frame;
this cannot dispatch, renew, or acquire control. Revoke evicts cached status replies containing
capabilities (retaining the high-water mark); a retry of such an ID returns staleMessage. Fresh
status still reports the current state.
`generation/clientId/incarnation` must match the live connection, not merely values supplied by it.
An `execute` additionally needs the current grant capability. A client cannot select its identity.

## Client operations

| Operation | Body | Result and constraints |
|---|---|---|
| `register` | `provider`, `project`, `sessionLabel`; optional `parentLabel` | Returns `clientId`, `incarnation`, limits, `heartbeatIntervalMs:1000`, `lossTimeoutMs:3000`; one registration per connection |
| `heartbeat` | `{}` | Refreshes that connection's liveness only; never extends a deadline |
| `request` | `key`, `purpose`, `durationSeconds`, `targets`, `steps` | Validates and freezes scope; returns `requestId`, `revision:1`, `state`, `stateVersion`; no capability yet |
| `status` | `requestId`, `afterVersion`, `waitMs` | Own request only; full snapshot, at most 30,000 ms wait; zero means immediate; capability present only for this connection's current active grant |
| `queueStatus` | `offset`, `limit` | Sanitized labels/state only, limit 1–16; no manifests, text, capability or other clients' results |
| `progress` | `requestId`, `sequence`, `stepId`, `activity` | Own active request only; increasing integer sequence, bounded plain activity; UI refresh within 1,000 ms; no authorization or renewal |
| `execute` | `requestId`, `grantId`, `capability`, `stepId` | Executes the next immutable manifest step only; no replacement selector/text/action fields; returns recorded step outcome or `inFlight` |
| `cancel` | `requestId` | Own nonterminal request; removes pending work, cancels countdown or begins stop; terminal request returns its outcome |
| `release` | `requestId`, `grantId`, `capability` | Early finish, including incomplete plans; enters stopping before returning accepted; final outcome is obtained from status |

`provider` is `codex`, `claude` or `other`. Labels and activity are at most 128 UTF-8 bytes; purpose
512. Display strings reject control/bidi formatting characters and render as plain text. No terminal
escape sequences or markup. `sequence`, `afterVersion`, `stateVersion` and pagination values are
nonnegative exact integers at most 2^53−1. `stepId` in progress is a manifest ID or null for unknown
current activity. It cannot claim that an unexecuted action completed; execution results remain
authoritative. Stale/duplicate progress returns `ignored`, without changing the display.

`status` snapshots include stateVersion, state, reason (nullable), own recorded step outcomes,
current activity, readiness remedies, countdown/remaining allowance, and grantId/capability only
while active. StateVersion increases for any observable change; equal versions are immutable.
They never contain typed payloads. Client wait timeouts return the current snapshot and request ID,
not permission. A CLI must remain able to heartbeat and cancel during its wait or an in-flight step.

There is **no client approve, yes, review, renew, force-release or quiescent operation**. Such frames
reject with `unknownOperation`. Other-owner status/action/cancel returns `wrongOwner` without a
request snapshot. Generation is checked before owner, owner before grant/scope, and all before dispatch.

## Immutable scope and replay

- Duration is an integer 1–600 seconds. Each request has 1–8 targets and 1–128 ordered steps;
  total serialized request must fit one frame. Target/step IDs are unique within the request.
- `target` fields: `targetId`, `bundleId`, `artifact` and `instance`. `artifact` contains canonical
  absolute executable `path` and lowercase SHA-256 `sha256`. `instance` is either null (not yet
  launched) or `{pid, startIdentity, codeIdentity}` verified by the broker before decision and
  again at use. PID alone is never identity. A changed artifact/instance invalidates approval.
- `step` fields: `stepId`, `label`, `targetId`, `kind`, `arguments`. Kinds: `activate`, `launch`,
  `quit`, `axPress`, `typeText`. Unsupported kinds, coordinate input, shell commands, automation of
  permission dialogs/the coordinator, arbitrary AppleScript, and detached workers reject.
- `activate`/`launch`/`quit` arguments are `{}`; their scope comes entirely from the target.
  Each quit step names one preflighted instance, never a dynamic wildcard. Fresh-build handoff
  enumerates all copies before approval; any newly discovered copy stops that plan for reapproval.
- `axPress` arguments: `window`, `element`. `typeText`: `window`, `element`, `text`. A selector
  is `{role, identifier, title}`; identifier/title may be null, but at least one must be present.
  Match exact values; all non-null fields must match one unique element/window. No fuzzy fallback.
  Selector strings are at most 256 UTF-8 bytes. Focus mismatch/ambiguous resolution stops input.
- Text is at most 4,096 UTF-8 bytes per step, retained in memory only and erased on terminal state.
  It is transported during request creation, never repeated in execute/status/logs. Freeze and
  compare the validated typed request (including actual text bytes) directly while retained;
  for terminal request/envelope replay retain only a keyed fingerprint, not the text. Use HMAC-SHA256
  with a random in-memory generation key over a deterministic typed encoding: object keys sorted,
  arrays ordered, explicit type/length tags and UTF-8 string bytes, no Unicode normalization.
  A retransmit is fully validated before its fingerprint is computed. Do not rely on raw JSON
  formatting or client-supplied hashes to establish immutability. Hash artifacts independently.
- A null instance may bind exactly once after an approved launch of the specified artifact;
  verify the resulting process identity before any later action. Activation is a one-use expected
  focus transition to that bound process with a bounded timeout, not a license to reclaim focus.
  A crash, replacement process or unexpected new window never silently rebinds.
- Target lifecycle is checked both when validating ordered manifests and immediately at dispatch:
  `launch` requires an unbound null instance and no earlier launch for that target; its result
  binds only the newly launched process whose artifact/start/code identity is verified.
  `activate`, `quit`, `axPress` and `typeText` require an already-bound live instance. Input before
  the corresponding launch, launch of a pre-bound target, reuse after quit, and post-launch identity
  mismatch reject with `targetChanged` and zero new input. A same-app fresh-build handoff uses
  distinct target IDs for the old bound instances and the new unbound artifact.
- A duplicate request key with equal validated content returns the existing request/outcome.
  Changed content with the same key returns `idempotencyConflict`. Scope edits require a new key,
  human intent and a new Yes. Wait never creates a replacement request.
- Store replay records for the full connection lifetime, including denied/cancelled requests.
  Limit 256 request keys per connection; at that limit reject new keys until a deliberate new
  connection, not silently evict records. Directions must not reconnect or change keys automatically
  to get around No. Cross-connection automatic request retries are prohibited.
- Mark each step consumed atomically before the first side effect. The next ordered step cannot
  start until the preceding one succeeded; at most one step is in flight. A lost reply for the same
  step returns `inFlight` or its stored result, never another click/paste. Indeterminate completion
  stops the sequence and remains `unknown`; it never makes the step retryable.
- After revocation, even duplicate execute calls reject as stale/invalid grant. An owner may read
  recorded outcomes through status while its connection remains open. That read performs no input.

## Serialized transitions and human decisions

One global slot covers countdown, active, stopping and interventionRequired. Queue selection and
decision acceptance are atomic with reservation. There can be at most one awaitingDecision panel;
all other ready requests remain FIFO queued. No panel for the next owner is approved in advance.

| From | Event and guard | To / effect |
|---|---|---|
| new | Valid request; client alive | queued; repeated key returns original |
| queued | Slot free, head of FIFO | awaitingDecision |
| awaitingDecision | Human No bound to current request/revision | denied; terminal; zero input |
| awaitingDecision or blocked | Human Wait or pending panel close | deferred; no timer-based return |
| deferred | Human Review | Append to FIFO queued; never approve directly |
| awaitingDecision | Human Yes; current revision, live client, free slot, readiness all true | countdown; reserve slot, record start instant |
| awaitingDecision | Readiness false on Yes | blocked with remedy; no reservation/input |
| blocked | Human Review after remedy | queued; fresh Yes still required |
| countdown | Continuous clock reaches five seconds; environment and readiness revalidated | active; issue capability, start duration now |
| countdown | Cancel/Stop, target loss, lock/sleep, visibility/monitor/permission loss, owner loss | cancelled; no grant issued; release slot after confirming no worker admitted |
| queued/awaitingDecision/blocked/deferred | Owner cancel or disconnect/watchdog loss | cancelled; remove pending request |
| active | Stop/shortcut/cancel, release, expiry, failed action, intervention, target/environment/owner loss, worker-channel EOF or executor heartbeat age >=3,000 ms | stopping; invalidate capability and close dispatch before notifying worker |
| stopping | Verified drain, final outcome known | finished for release; expired for deadline; cancelled for stop; failed for execution/environment error; slot released |
| stopping | One-second stop deadline without verified drain | interventionRequired; retain slot, visible reason |
| interventionRequired | Verified reconciliation, including late matching worker acknowledgement | Same terminal outcome as stopping; release slot only with proof |
| any terminal | Duplicate request/status/cancel from original owner | Same outcome; zero input |

An unsupported adapter returns terminal `unsupported` before queue insertion. Helper unavailability
is a local CLI `unavailable` result, not a fallback input path. Busy/recovering helpers cannot issue
grants. After restart an old request is unavailable; no replay history resurrects it.

Only the in-process UI can emit `humanYes`, `humanNo`, `humanWait`, `humanReview`. Events carry
request ID, revision and the displayed stateVersion; stale panel events reject without side effects.
Request appearance must not activate the helper. Return/Space typed elsewhere has no transition.
Keyboard Yes requires explicit helper focus and navigation; it is never a default button or first
click-through action. Closing/moving an active overlay and loss of Stop visibility trigger Stop.

## Time, intervention and cancellation handshake

- Use a continuous monotonic clock that includes sleep. Absolute instants shared with workers
  are decimal-string nanoseconds on that same boot clock; clients never supply authoritative time.
  UI countdown is `ceil(max(0, end-now)/1s)`; display 5 at Yes and 0 at activation after five seconds.
  Duration starts at activation. Dispatch requires `now < deadline`; equality is already expired.
- Explicit sleep/lock/login loss invalidates countdown and active work independently of timers.
  Wake cannot consume an overdue countdown callback. Wall-clock adjustments and progress/heartbeat
  never renew control. Missing overlay, monitoring, target or permissions fails closed with remedy.
- Client and executor send heartbeats every 1,000 ms; heartbeat age **>=3,000 ms** is loss. EOF is
  immediate loss. Watchdogs run separately from action waits. Loss closes admission immediately
  when detected; drain still has the one-second stop budget. Measure detection and drain separately.
  The broker watches client and worker connections; the worker independently watches its broker.
  Worker loss while its process is still alive triggers revoke/owned-worker reconciliation and
  the same one-second interventionRequired deadline; it never frees the slot on disconnect alone.
- Emergency/physical-input/focus observers deliver stop to the same serialized admission gate.
  Supported synthetic-event tagging must distinguish owned events from physical intervention;
  inability to do so makes that adapter unsupported. Never suppress physical input.
- Before each step and each individual synthetic event, executor checks generation, owner,
  incarnation, immutable target, deadline, live supervision and stop epoch. No pre-posted event
  queue. AX call deadlines and event scheduling bounds must be proven by task 1.3.
- Worker transport is a private inherited channel, separate from client IPC. Broker sends
  `dispatch(generation, workerIdentity, grantId, stopEpoch, stepId, deadlineNs, frozenStep)`.
  Worker reports `started` and `result` with matching identities. No client can send worker replies.
- Stop increments stopEpoch and closes admission **before** emitting
  `revoke(generation, grantId, stopEpoch, reason, stopDeadlineNs)` to the worker. Worker closes
  admission, cancels pending events, releases any held synthetic keys, conditionally restores its
  clipboard snapshot, then sends `quiescent(generation, grantId, stopEpoch, lastStepId, lastEventNs,
  heldKeysEmpty, cleanupResult, stepDisposition)`. `stepDisposition` names the last admitted step
  and records `notStarted`, `completed(result)` or `indeterminate`; it must match the broker's
  admission record. A mismatched or old acknowledgement cannot release the slot. Indeterminate
  input stays recorded as `unknown` and non-retryable even after quiescence is proved. A request
  may end cancelled/expired with an unknown step; early release with an unknown step ends failed,
  never successful finished. Status exposes that distinction without replaying the action.
- Stop also drains on early release and expiry. Already-delivered actions are not rolled back.
  Clipboard restoration is allowed only while the pasteboard change count still matches the
  worker's write. User clipboard changes survive; clipboard/text data never appears in reports.
- The supervisor may terminate only its verified owned worker on failed cooperative stop; reserve
  enough of the one-second budget to verify exit. Exact response/termination thresholds are spike
  measurements. Worker exit proves no future dispatch by that worker, not that an already-posted
  OS event disappeared: pending event delivery/held-key uncertainty retains interventionRequired.
- Broker loss triggers the independent worker watchdog; worker loss triggers the supervisor's
  reconciliation. Never kill the agent, terminal, target app or unrelated process as stop cleanup.
  New broker startup must reconcile known owned workers and any uncertain in-flight event boundary
  before declaring idle. Dismissing an error cannot stand in for evidence.
- Maintain a crash-surviving supervision ledger in the private machine-local runtime directory,
  separate from outcome history. Before enabling a worker or dispatching a step, atomically write
  and durably flush its boot/login identity, worker PID/start/code identity, generation, grant ID,
  stop epoch, admitted step ID and event-boundary disposition. Include only owned process identities;
  no capability, payload, path or selector. Persist an uncertain boundary before posting, and resolve
  it only after verified completion/drain. Failure to save disables dispatch and begins stop.
  Clear a worker record only after verified exit and resolved event/held-key cleanup. Keep a clean
  ledger marker across broker exits; runtime history is not restored as authority.
- Missing/corrupt/incomplete ledger data is not proof of an idle desktop. Startup stays recovering
  (with interventionRequired true on ambiguity) until it proves no previous managed worker can dispatch and
  no admitted event remains uncertain. Initial bootstrap needs the same no-old-worker proof; if
  this execution context cannot obtain it, report the missing verification instead of starting.
  A verified new boot rules out old processes/events, but a new broker generation alone does not.
  Same-login reconciliation must not treat PID lookup alone or a new socket as that proof.
- Bootstrap procedure under the exclusive broker lock: require a complete OS process inventory
  for this UID and verify identities for every possible managed executor. All conforming workers
  must keep the fixed executable name `MacControlExecutor`, a stable recorded worker code identity,
  and no detached/renamed/exec-replaced descendants. A name matches a candidate, never authority
  to terminate it. An unreadable candidate or incomplete enumeration is ambiguity, not absence.
  A clean initial marker may be durably created only when no managed executor exists and either
  this is a verified new login/boot with no old event boundary, or the previous ledger proves all
  admitted work resolved. Missing same-login ledger plus unknown prior events requires a new
  login/boot and verified clean worker inventory; it cannot be cleared by clicking Dismiss.
  The first-run helper/installer reports `unavailable` with that concrete remedy when proof cannot
  be obtained. Implementation must record which OS evidence established login/boot freshness;
  an absent config file or a claimed first install is not proof. Gate A must test this startup path.
- Control returned requires no admitted work, no possible future owned input, and cleanup resolved.
  Real acceptance runs additionally require target event timestamps showing no later synthetic
  input. Unit fixtures describe the required result; they cannot prove one-second quiescence.
- Fresh handoff stopped after quitting records `freshLaunchPending` as outcome metadata; launching
  the unchanged approved artifact requires a new request/grant. Stop cleanup never activates it.

## Errors, data and fixture contract

Stable errors: `invalidMessage`, `unsupportedVersion`, `unknownOperation`, `busy`, `wrongOwner`,
`staleGeneration`, `staleIncarnation`, `invalidGrant`, `expiredGrant`, `idempotencyConflict`,
`staleMessage`, `invalidState`, `outOfOrderStep`, `targetChanged`, `unsupported`, `unavailable`.
Invalid actions produce zero additional input; errors on an active owned target/step that invalidate
safe continuation also stop the sequence. An unrelated client's bad request cannot steal the slot.

In-memory requests contain payloads; public queue/status/logs do not. Persist at most the latest
100 sanitized outcomes (labels, outcome, timestamps), never live identity/capabilities, text, paths,
selectors, screenshots or clipboard snapshots. Private history is not a replay/approval database.
Runtime data is machine-local and outside Git/Syncthing. Settings changes cannot revive grants.

[`Fixtures/protocol/`](Fixtures/protocol/) contains declarative scenarios, **not runnable client
requests**. `fixtureVersion:1`, `cases` with unique `id`, `criteria`, `given`, `when`, `expect`;
events use test-clock milliseconds and symbolic identities. `expect` describes the state/input
oracle for later tests. `wire-examples.json` separately contains representative valid wire frames
and semantic rejection examples. The standalone spike implements an experimental subset;
the production protocol runtime does not exist yet.

Backpressure: parse every fixture using `python3 -m json.tool <fixture>`. Review each AC01–AC16
branch against the transition table and record results in
[`verification/mac-control/protocol.md`](../../verification/mac-control/protocol.md).
