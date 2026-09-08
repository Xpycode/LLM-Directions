# Mac-control environment inventory

**Date:** 2026-09-05 · **Task:** 1.1 · **Status:** inventory complete; live control compatibility unverified.

Later task 1.3 evidence: [first live disposable Stop case](stop-spike.md) passed outside the shell
sandbox. This inventory remains the earlier snapshot; it does not itself establish compatibility.

## Environment

First-Mac candidate: **M1 Max**, from the existing machine-local
`~/.claude/this-mac` label. The preferred `~/.config/directions/this-mac` file is absent.
Architecture is arm64. Hardware model could not be queried in this sandbox, so the label is
not an independent hardware verification. The second Mac was not inspected.

| Exact command | Observed result | Limitation |
|---|---|---|
| `sw_vers` | macOS 27.0, build 26A5421a | Current local OS, not a supported deployment baseline |
| `xcodebuild -version` | Xcode 26.6, build 17F113 | Version query only |
| `uname -m` | arm64 | Does not identify the chip model |
| `sysctl -n hw.model` | Operation not permitted | No hardware model obtained |
| `codex --version` | codex-cli 0.153.4 | Also warned that PATH aliases could not be created; query exited successfully |
| `claude --version` | 2.1.260 (Claude Code) | No Claude session started |
| `swift --version` | Apple Swift 6.3.3; driver 1.148.6; target arm64-apple-macosx28.0 | Compiler-reported target differs from running OS; no compilation attempted |
| `codex --help` | Local CLI help available | Does not identify the current host version or prove desktop integration |
| `claude --help` | Local CLI help available, including `--session-id`, `--resume`, `--fork-session` | Options observed, not exercised |

The executable symlinks resolve to:

- Codex: `~/.codex/packages/standalone/releases/0.153.4-aarch64-apple-darwin/bin/codex`.
- Claude: `~/.local/share/claude/versions/2.1.260`.

Python `plistlib` inspection of `/Applications/Claude.app/Contents/Info.plist` found version/build
**1.46388.4**, bundle ID `com.anthropic.claudefordesktop`. `/Applications/Codex.app` is absent;
this does not establish whether another host or install path is in use. An attempt to obtain
parent executable names with `/bin/ps -p <parent-pid> -o ppid=,comm=` was denied by the sandbox.
No process arguments, conversation lists, transcripts, credentials, or session-ID values were collected.

## Targeted backend checks

Checks used `pathlib.Path.exists()` for each listed path and `shutil.which()` for each executable.

| Path or executable | Result | Interpretation |
|---|---|---|
| `/Users/sim/ProgrammingProjects/9-TESTING/AppProbe` | Absent | Exact source path referenced by `commands/test-app.md` |
| `/Applications/AppProbe.app` | Absent | No app at this location |
| `~/Applications/AppProbe.app` | Absent | No app at this location |
| `/Users/sim/ProgrammingProjects/0-DIRECTIONS/AppProbe` | Absent | Additional nearby source check |
| `appprobe`, `cliclick`, `dialog` on PATH | Not found | No claim about other unsearched locations |
| `osascript` on PATH | `/usr/bin/osascript` | Script runner present; no script or Apple Event sent |
| `swift` on PATH | `/usr/bin/swift` | Candidate for a standalone owned executor spike |
| `python3` on PATH | `/opt/homebrew/bin/python3` | Used for metadata and nonprompting permission probes |

The current session exposes shell execution and local image inspection, but its exposed tool
catalog has no native Mac computer-use action tool. This describes this session, not all Codex
installations. Shell execution has run successfully; shared-CLI transport and controlled input
have not been tested.

Configuration inspection extracted only MCP server names and hook event names:

- `~/.claude.json`: XcodeBuildMCP, apple-docs, chrome-devtools, sosumi, swiftlens, vestige.
- `~/.claude/settings.json`: PreToolUse, SessionStart, Stop, UserPromptSubmit hook events;
  no `mcpServers` entries in that file. `settings.local.json` absent.
- `~/.codex/config.toml`: a `blender` MCP table and its nested environment table. Environment
  values were not collected. This is a targeted file check, not an enumeration of every plugin,
  profile, project configuration, or remotely supplied tool.

Configured server names do not prove that servers are connected, identify the interrupting path,
or establish a cancellation boundary. Hook commands and permission rules were not changed.

## Session identity sources

| Client | Observed source | Contract still needed |
|---|---|---|
| Current Codex shell | `CODEX_THREAD_ID` is present; value withheld | Use as a display/correlation hint only; broker must issue ownership and connection incarnation |
| Installed Claude CLI | Local help exposes an explicit UUID session option, resume, and fork | Verify identity propagation inside an actual Claude session during integration |
| Current shell's Claude environment | `CLAUDE_SESSION_ID` and `CLAUDE_CODE_SESSION_ID` absent | This is a Codex child, so absence says nothing about a real Claude shell |

Provider session labels cannot themselves authorize an action. Reconnection, stale owner rejection,
and private endpoint access remain protocol/transport work in tasks 1.2, 1.3, and Wave 5.

## Permissions: nonprompting preflight only

Ran the following exact probe through `python3` in the current Codex shell:

```python
import ctypes

checks = [
    ("/System/Library/Frameworks/ApplicationServices.framework/ApplicationServices", "AXIsProcessTrusted"),
    ("/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics", "CGPreflightListenEventAccess"),
    ("/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics", "CGPreflightPostEventAccess"),
]
for library, name in checks:
    function = getattr(ctypes.CDLL(library), name)
    function.restype = ctypes.c_bool
    function.argtypes = []
    print(name, function())
```

All three returned **false**. These results apply to this Python child in this sandbox and
execution context. They do not establish the permission state of Claude.app, another terminal,
the host application, or a future signed helper. No permission-request API, TCC database access,
event tap, screenshot, clipboard access, activation, or input dispatch was used.

## Action paths and evidence level

| Path | Evidence level now | Remaining requirement |
|---|---|---|
| Owned AX/CGEvent executor through a shared CLI | Documented cookbook precedent; compiler installed; executor absent | Prove its own permission preflight, IPC access, bounded input, cancellation and drain in task 1.3 |
| Current Codex → shell → shared CLI | Shell invocation live-verified for read-only probes; proposed CLI absent | No control/transport compatibility claim until spike and Wave 5 |
| Claude → shell → shared CLI | Client installed; session integration not run | Real Claude invocation, identity and full lifecycle verification |
| Codex native computer use | Prior documentation only; no such tool exposed here | Actual tool availability and controllable stop boundary |
| Claude native computer use | Prior documentation plus installed client; availability unverified | Actual enabled backend, lock coexistence and stop boundary |
| AppProbe | Absent at checked source/app/PATH locations | Locate a real installation before considering an adapter |
| Independent osascript/AX/CGEvent automation | Script runner/compiler installed; cookbook documents focus/paste behavior | Remains outside coordinator protection unless converted to bounded owned actions |
| Configured MCP routes | Names observed only | Identify any route involved before investigating its input/stop behavior |

## Result and next action

The user clarified that interruptions occur **occasionally during UI tests** from Penumbra,
Game One, or any other session needing desktop interaction. Most testing is not disturbing.
The requirement is shared scheduling at the interfering action boundary across projects, not a
Penumbra-specific fix or a requirement to block all testing/background work.

The user's supplied screenshot provides a concrete third-project example: `osascript` tells
`System Events` to address process `Conjoyn`. Its action body is collapsed, so the screenshot
does not establish whether that specific invocation activated the app, clicked, typed, or only
inspected it. It does establish a shell/AppleScript route that the coordinator must account for;
it is not evidence of native provider computer-use invocation.

The same screenshot shows a Swift inspector and `screencapture -x -l <window-id>`. Read-only source
inspection of the referenced `/tmp/conjoyn-review-inspect.swift` found `AXUIElementCopyAttributeValue`,
running-app enumeration, and window-list reads; there is no activation, AX mutation, input posting,
or AppleScript execution in that file. The inspector was **not run** and its captured output/image
was not read. This distinguishes the shown inspection source from the unknown AppleScript body;
it does not certify every screenshot/inspection workflow as noninterfering. Temporary source may
later disappear; the supplied screenshot and this dated source observation are the evidence.

A bounded independent source inventory inspected project guidance and representative source in
`/Users/sim/ProgrammingProjects/1-macOS/Penumbra` and `.../GameOne` without running either project:

- Penumbra's `docs/reviews/2026-09-04/ReviewProbes.swift` contains model/service XCTest probes,
  not a foreground input executor. No corresponding checked-in AX/AppleScript test driver was
  found in the bounded inventory. Production `KeyInputView.swift` uses a local event monitor;
  that consumes app input and is not evidence of the external automation that produced it.
- GameOne's project guidance says there is no automated test target. Its `GameScene.swift`
  receives keyDown/keyUp/flagsChanged through AppKit/SpriteKit and makes its view first responder;
  no checked-in automation driver or shared stop protocol was found in the bounded inventory.
- This source inventory is not a complete search of transient scripts or historical sessions.
  It neither contradicts the reported UI tests nor attributes their synthetic input to app code.

Task 1.1 can now close: installed clients, identity sources, permission observations, first-Mac
candidate, input route categories and a concrete user-supplied shell route are recorded. Exact
legacy action bodies and cancellation behavior remain unverified; arbitrary AppleScript cannot
be claimed compatible merely by putting a request panel in front of it.

Proceed to protocol task 1.2 using the owned CLI executor as a candidate bounded replacement for
participating foreground test actions. Gate A stays closed until task 1.3 proves the path in the
plan's explicitly agreed foreground window with the actual executable's own permission checks.
No application was built, launched, installed, or controlled during this inventory.
