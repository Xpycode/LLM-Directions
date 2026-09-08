# Protocol contract verification — task 1.2

**Date:** 2026-09-05 · **Machine:** M1 Max label, arm64, macOS 27.0 (26A5421a).
**Tooling:** Python 3.14.7 for JSON parsing; no Swift compilation or app execution.
**Contract:** [Protocol.md](../../tools/mac-control/Protocol.md), revision 1.
**Scope:** static contract/fixture verification, not implementation acceptance or Gate A.

Later execution: [task 1.3 first live Stop case](stop-spike.md) now has separate measured evidence.
The checks and next-action text below are the original task 1.2 snapshot.

## Checks performed

- Ran `python3 -m json.tool` with each of the six
  `tools/mac-control/Fixtures/protocol/*.json` files as stdin: all parsed successfully.
- Checked fixture version, required scenario fields and globally unique IDs: **86 declarative
  scenarios**; AC01–AC16 and AC21 all represented. These are future test oracles, not passing
  behavioral tests. Raw malformed-byte scenarios are descriptions because invalid JSON cannot
  itself be stored as a parseable JSON fixture.
- Checked wire-example IDs are decimal strings within 1…2^53−1 and compact frame sizes fit the
  65,536-byte limit. Positive wire examples are illustrative; no production decoder exists yet.
- Manually reviewed the transition table against each AC01–AC16 branch below. The review tests
  specification completeness only; native UI focus, input delivery and timing require live evidence.

Reproduction of JSON parsing:

```bash
for fixture in tools/mac-control/Fixtures/protocol/*.json; do
  python3 -m json.tool < "$fixture" > /dev/null || exit 1
done
```

## Acceptance-branch review

Fixture IDs below occur in `tools/mac-control/Fixtures/protocol/`.

| Criterion | Contract branch / representative fixture IDs | Result and remaining proof |
|---|---|---|
| AC01 | Atomic FIFO selection/reservation; `two-projects`, `stale-panel`, `agent-cannot-approve` | Defined; two real clients still required |
| AC02 | No default keyboard Yes or inactive click-through; `typing-is-not-approval` | Defined; real AppKit focus/keyboard test required |
| AC03 | Terminal No, request-key/envelope replay, no reconnect workaround; `no-and-request-retry`, `replay-cap-does-not-evict`, `terminal-replay-without-payload` | Defined; no runtime prompt behavior tested |
| AC04 | Wait/close/deferred FIFO Review and no timed start; `wait-needs-review`, `close-pending-means-wait`, `review-does-not-approve`, `wait-timeout-is-not-consent` | Defined |
| AC05 | One reserved slot, five monotonic seconds, duration from activation; `countdown-boundary`, `two-projects` | Defined; rendering/timer accuracy unmeasured |
| AC06 | Countdown cancellation on Cancel, target loss, lock, sleep, owner disconnect and unavailable monitoring/visibility; all `countdown-*` cases | Defined; zero-input behavior requires executor evidence |
| AC07 | Owner-bound increasing progress, one-second UI refresh, no focus change; `progress-and-early-release`, `stale-progress` | Defined; UI refresh unmeasured |
| AC08 | Release drains before returned-control, next owner still needs Yes, unknown step cannot report success; `progress-and-early-release`, `release-unknown-step` | Defined |
| AC09 | Validate live connection/generation, owner, grant and time before dispatch/replay; `no-grant`, `expired-grant`, `wrong-owner`, `old-generation`, `old-incarnation`, `cached-execute-after-revoke` | Defined; actual action boundary unimplemented |
| AC10 | Immediate admission closure for Stop/shortcut/expiry, no next step, one-second drain; all `stop-*` cases | Defined; latency and held-key cleanup must be measured |
| AC11 | Stop epoch and step disposition acknowledgement, unknown delivery retains slot; `failed-drain`, `late-matching-drain`, `worker-exit-with-event-uncertainty`, `cancel-unknown-step` | Defined; worker/process/event reconciliation unproven |
| AC12 | Client/broker/worker EOF and exact three-second watchdog threshold, independent worker stop, crash ledger and clean bootstrap; `owner-heartbeat-boundary`, `connection-eof`, `broker-crash`, `worker-heartbeat-loss`, `worker-channel-eof`, `recovery-*`, `clean-bootstrap` | Defined; OS evidence and actual transport/watchdogs required |
| AC13 | Sleep/lock/login invalidation; continuous deadlines unaffected by wall time; `active-sleep`, `active-lock`, `active-loginChanged`, `wall-clock-does-not-extend`, `restart-does-not-resume` | Defined; native notifications and clock behavior untested |
| AC14 | Physical key/click/scroll/unexpected focus stops; unsupported when origins cannot be distinguished; `intervention-*`, `unreliable-origin-monitor` | Defined; actual input-origin distinction remains a blocking experiment |
| AC15 | Preflighted artifact, instance, window and ordered binding checks; `target-*`, `launch-bound-target`, `input-before-launch`, `launch-identity-mismatch` | Defined; actual process/AX identity verification untested |
| AC16 | Concrete remedies, blocked start, no auto-approval after permission fix, monitoring loss stops; `blocked-permission`, `remedy-does-not-approve`, `absent-helper`, `active-monitor-loss` | Defined; native permissions unchanged |
| AC21 | Framing/size/depth bounds, unknown operations, immutable keys, increasing envelope IDs with replay cache, stale progress and consumed step results; replay, wire and cache fixtures | Defined; parseable fixtures do not prove a production parser rejects malformed bytes |

Additional scenarios record AC17 background work, AC18 unsupported legacy scripts, AC19 interrupted
fresh launch, and AC22 clipboard ownership. AC20–AC24 remain subject to the feature's later full
acceptance matrix; task 1.2 does not mark any product acceptance criterion complete.

## Independent review and resolutions

A separate agent reviewed the contract and fixtures against the feature specification. The material
findings led to these changes:

| Finding | Resolution |
|---|---|
| Null/pre-bound target behavior allowed ambiguous launch/input | Added explicit per-kind instance lifecycle, ordered validation, one-time launch binding and zero-input rejection cases |
| Broker restart had no crash-surviving source for worker/event reconciliation | Added a private supervision ledger saved before dispatch, startup availability states, clean-marker proof procedure and explicit unavailable remedies |
| Worker connection loss had no explicit bounded active transition | Added worker EOF and heartbeat threshold to stopping, separate watchdog ownership and one-second failed-drain behavior |
| Duplicate envelope IDs were undefined | Added increasing IDs, bounded replay fingerprints/cache, high-water rejection after eviction, and lost-reply fixtures |
| Quiescent acknowledgement omitted the last step's disposition | Added notStarted/completed/indeterminate disposition; unknown steps stay non-retryable; release cannot turn uncertainty into success |
| Reply cache could bypass revocation or retain text/capabilities | Validate execute grant before replay; use keyed fingerprints; erase terminal text and revoked capability status replies; add regression cases |

Review found contract gaps; these fixes are design changes, not proof of successful runtime recovery.
The independent reviewer rechecked the affected clauses and regression fixtures after fixes and
reported no remaining direct contradiction in those changes.
The bounded spike must demonstrate startup/recovery evidence in its actual sandbox, permissions,
and worker implementation before the production package or full UI proceeds.

## Next

Task 1.3: prepare the disposable executor/target spike against this contract. The plan requires an
explicit foreground test window for compilation/execution of that spike. No such window has been
agreed, and no build, desktop input, screenshot capture, clipboard mutation, installation or global
configuration change occurred during task 1.2. The user's Conjoyn screenshot was evidence, not
authorization to interact with that live session.
