# Mac Control Coordinator — Research and Compatibility

**Checked:** 2026-09-05. Documentation review plus targeted local inventory; no installation or live desktop-control test.
**Spec:** [Mac Control Coordinator](mac-control-coordinator.md)

**Execution update, 2026-09-05:** the [first owned-executor Stop case](../verification/mac-control/stop-spike.md)
now passes from an actual Codex session with approved execution outside the shell sandbox. Six
characters and 12 matching events drained in 11.716291 ms. This is one case; Gate A, full recovery,
physical intervention, clipboard and production/provider integration remain unproven. The matrix
below preserves the original inventory baseline rather than claiming full adapter support.

Local versions, identity hints, exact path checks, and nonprompting permission results are recorded
in [the environment inventory](../verification/mac-control/environment.md). The user identifies
occasional UI-test interruptions across projects and supplied a Conjoyn shell/AppleScript example;
the accompanying inspected Swift source only reads AX/window metadata. Installation and source
inspection are not evidence of controlled-input compatibility.

## Local gap analysis

| Evidence | Existing behavior | Gap / implication |
|---|---|---|
| `commands/test-app.md`, steps 2, 6–7 | Launch, then ask about running a plan; AppProbe `--overlay` documented | Gate must precede the first disrupting launch, not only the final run |
| `MACHINES.md`, AppProbe entry; missing documented path on this Mac | AX-by-name fallback already expected | AppProbe cannot be assumed to supply UI or cancellation |
| `cookbook/139-ax-drive-swiftui-settings-form-verify.md` | AX targeting, focus changes, clipboard paste | An apparently headless harness can still interfere with the user |
| `hooks/session-guard.sh` | Warns of shared checkout sessions | No desktop queue or exclusion |
| `64_codex.md`, `deploy-codex.sh` | Guidance and skill deployment; native lifecycle port deferred | Do not assume deployed hooks or add a whole hooks port |
| `hooks/install.sh`, Claude templates | Existing Claude hook installation | New adapter registration must preserve unrelated handlers |
| `47_project-ui-conventions.md` | Native AppKit controls preferred | Native helper fits; no new primary sidebar required |

## Primary web sources

The following are documented capabilities, not claims about installed versions on either Mac.

| Source | Finding | Design implication |
|---|---|---|
| [OpenAI Computer Use](https://learn.chatgpt.com/docs/computer-use) | Scoped background Mac operation and per-app approval are described | Prefer noninterfering paths where verified; no shared timed third-party queue established |
| [OpenAI hooks](https://learn.chatgpt.com/docs/hooks) | PreToolUse covers many local/MCP tools; specialized paths can opt out, write_stdin does not rerun it; hook errors can continue | Hooks are supplementary; executor must enforce grants and stop independently |
| [Claude computer use](https://code.claude.com/docs/en/computer-use) | Per-session app approval, Escape stop, and a machine-wide lock held until session exit | Useful provider controls; lock lifecycle does not equal short reusable cross-provider grants |
| [Claude hooks](https://code.claude.com/docs/en/hooks) | PreToolUse can deny; command/http/MCP hook timeouts do not block. Defer is limited to noninteractive single-tool flows | Do not implement Wait as an indefinitely blocking hook or assume interactive defer works |
| [swiftDialog timers/progress](https://swiftdialog.app/advanced/timer-progress/) and [live updates](https://swiftdialog.app/advanced/command-file/) | Countdown/progress and external status updates are available | Viable visual prototype, but not the broker or cancellation mechanism |
| [swiftDialog buttons](https://swiftdialog.app/basic-use/buttons/) | Configurable user choices | Still needs accidental-approval/focus validation; no runtime dependency proposed |
| [Apple NSStatusItem](https://developer.apple.com/documentation/appkit/nsstatusitem) | Native menu-bar item | Entry point for queue and status |
| [Apple NSPanel](https://developer.apple.com/documentation/appkit/nspanel) and [nonactivatingPanel](https://developer.apple.com/documentation/appkit/nswindow/stylemask-swift.struct/nonactivatingpanel) | Floating utility panel and nonactivating style | Suitable request/countdown/progress surface; validate keyboard behavior |
| [Apple window collection behavior](https://developer.apple.com/documentation/appkit/nswindow/collectionbehavior-swift.struct) | Spaces and full-screen participation options | Verify combinations on real display setups; no blanket visibility promise |
| [Apple frontmostApplication](https://developer.apple.com/documentation/appkit/nsworkspace/frontmostapplication) | Observes the app receiving key events | Observation is not an OS-level exclusive desktop lock |
| [Apple CGEvent tap creation](https://developer.apple.com/documentation/coregraphics/cgevent/tapcreate(tap:place:options:eventsofinterest:callback:userinfo:)) and [AX trust](https://developer.apple.com/documentation/applicationservices/1460720-axisprocesstrusted) | Input observation/control depends on permission and available event taps | Preflight monitoring; stop on loss; do not inherit old cookbook permission assumptions |

## Compatibility matrix to complete during execution

| Path | Current evidence | Required experiment before support |
|---|---|---|
| Owned AX action executor via CLI | Documented cookbook precedent; Swift 6.3.3 installed; executor absent; current Python child permission preflights false | Own executable permission check; two clients, wrong focus, bounded input, cancel/drain, clipboard conflict |
| Codex calling shared CLI | CLI 0.153.4 installed; read-only shell invocation live-verified; CODEX_THREAD_ID present; shared CLI absent | Label ownership, transport access, wait/retry, deny, crash, stale grant, no blanket host approval |
| Claude calling shared CLI | CLI 2.1.260 installed; explicit session-ID option in local help; no actual-session verification | Same contract tests; preserve native permissions |
| Codex native Computer Use | Prior official documentation; no native Mac input tool exposed in this session | Prove actual availability, action interception, stop API, batching and hook bypass behavior |
| Claude native computer use | Prior official documentation; Claude.app 1.46388.4 installed; native input availability unverified | Prove coexistence with provider lock and reusable short grants; do not delete its lock |
| AppProbe | Absent at documented 9-TESTING source path, checked app paths, and PATH | Locate installed source/version first; optional adapter only |
| Arbitrary osascript/CGEvent scripts | Script runner/compiler installed; cookbook documents independent input routes; no input dispatched | Unsupported unless converted to typed, bounded supervised actions |
| Conjoyn shell UI-test example | User screenshot shows osascript → System Events → Conjoyn; collapsed action body unknown; referenced Swift inspector source performs read-only AX/window queries | Gate any activation/mutation/input before dispatch; preserve noninterfering inspection; no arbitrary script wrapping as a supported executor |

## Recommendation and confidence

Native AppKit is a documented fit for the requested UI. The queue and time allowance are ordinary
local application state. The material uncertainty is the input backend: a popup, prompt, or hook
cannot guarantee cancellation of arbitrary in-flight automation. Build the v1 around one owned,
bounded executor and prove the actual user clients can use it before polishing the interface.

Other agent dashboards can inform presentation, but none reviewed here establishes the entire
requested cross-provider timed-control contract. This is a scoped research result, not proof that
no such product exists. Current provider documentation must be rechecked when adapters are built.
