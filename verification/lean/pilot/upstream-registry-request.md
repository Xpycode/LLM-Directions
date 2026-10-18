# Draft request for exclusive dynamic tool registry control in Codex App Server

Status: local draft, October 17, 2026. Intended recipient: Codex App Server maintainers.

## Request

Please document a supported way to make client-supplied dynamic functions the complete
model-visible tool registry and the exclusive dispatch targets for an App Server thread.
If no such control exists, please consider an explicit opt-in mode with this contract.
The client needs both exact advertisement and host enforcement before using App Server for a
bounded read-only evaluation. Prompt instructions and filesystem sandboxing do not supply
that tool boundary.

Does Codex 0.163.0 support this contract? If so, what exact configuration and protocol fields
enforce it, including continuations and internal native-tool dispatch? If support requires a
different release, please identify that release and its documented guarantees.

## Observed configuration and result

The inspected installation reports `codex-cli 0.163.0`. Its executable SHA-256 is
`8813367285524ac798dd96d1b071aea30d58708c7226fd236cd275cf1cfdee31`.

An isolated CLI probe used empty temporary homes and working directory, no inherited credentials,
a read-only sandbox, disabled web search and native feature flags, and four dynamic broker tools.
The only configured inference endpoint was a loopback HTTP server returning terminal HTTP 400.
It supplied no model output or tool calls.

The single captured Responses request advertised `functions.exec`, wait/input, clock and
collaboration surfaces. The four broker functions appeared in nested textual tool declarations,
rather than as direct structured functions. The host warned that Code Mode was unavailable and
would fail closed. These observations establish advertisement for this configuration only;
they do not establish that the extra tools execute, or that every configuration behaves this way.

Offline experimental protocol schemas expose `dynamicTools` on `thread/start`, but we did not
identify an explicit complete-registry replacement field. A generic `config` object does not
establish which settings, if any, provide that guarantee.

The documented [dynamic tool interface](https://learn.chatgpt.com/docs/app-server) provides
registration and client callbacks. We could not establish exclusive native-tool replacement
from that interface or the [configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference).

## Required behavior

1. Accept a closed set of direct function names and JSON parameter schemas. For this evaluation
   the set is exactly `discover`, `list_files`, `read_file`, and `sha256`. Reject duplicates,
   conflicting registrations and unsupported configuration before inference.
2. Advertise only that set on every request, including continuations. Apply the restriction to
   top-level tools, additional tools and executable declarations in host instructions. Do not add
   wrappers, aliases, native helpers or discovery paths.
3. Route every allowed call exclusively to the registered client callback. Disable alternative
   native execution paths. Reject unknown, forbidden and malformed calls before any tool side
   effect, independently of whether the model follows instructions.
4. Expose the effective registry and enforcement mode before provider forwarding, so the client
   can compare them with its pinned manifest and stop on changes. Refuse thread restoration,
   fallback or configuration changes that would widen the boundary.
5. Document the supported versions, policy precedence and lifecycle behavior. Unsupported modes
   must fail closed; accepting a setting while silently retaining native tools is insufficient.

The client remains responsible for confined filesystem access, call/byte budgets, error-envelope
accounting and watchdog/teardown checks. Registry support is one prerequisite for those checks.

## Acceptance examples

| Scenario | Expected result |
|---|---|
| New thread with the four registered functions | Exact direct names and schemas on the outgoing request; no other executable tool declarations. |
| Call to each allowed function using disposable fixtures | One corresponding client callback per call; no native substitute. |
| Shell, write, web, app, delegation, goal, clock or resource-discovery call | Rejected before a side effect; no hidden native handler executes. |
| Unknown tool or malformed arguments | Terminal policy failure before execution. |
| Parallel calls | Each call individually validated and delivered at most once, or the batch stops under the documented failure policy. |
| Continuation or attempted restoration with additional tools | Rejected before forwarding a widened registry. |
| Unsupported option or unavailable enforcement implementation | Explicit failure before inference. |

These cases can first be exercised with a local scripted endpoint and disposable broker fixtures.
Passing them would establish local registry/dispatch behavior; real-provider acceptance remains
a separate check.

## Sanitized evidence excerpt

The following projection retains names and outcomes from the captured-request analysis. It omits
local paths and request content; it is not a complete wire request or a dispatch trace.

```json
{
  "version": "codex-cli 0.163.0",
  "request_count": 1,
  "model_outputs": 0,
  "tool_dispatch_tested": false,
  "tool_names": [
    "functions.exec",
    "functions.wait",
    "functions.request_user_input",
    "functions.request_user_input_async",
    "clock.sleep",
    "collaboration.followup_task",
    "collaboration.interrupt_agent",
    "collaboration.list_agents",
    "collaboration.send_message",
    "collaboration.spawn_agent",
    "collaboration.wait_agent"
  ],
  "missing_direct_broker_tools": ["discover", "list_files", "read_file", "sha256"],
  "warnings": [
    "Code Mode is unavailable because code-mode host is disabled. Code mode will fail closed; enable `features.code_mode_host` and install `codex-code-mode-host`."
  ]
}
```

The desired Responses function registry is below. These are wire definitions, not App Server
registration objects; registration uses `inputSchema` in place of `parameters` and includes a
description. Object key order and tool order are immaterial.

```json
[
  {"type":"function","name":"discover","parameters":{"type":"object","properties":{},"required":[],"additionalProperties":false}},
  {"type":"function","name":"list_files","parameters":{"type":"object","properties":{"path":{"type":"string"}},"required":["path"],"additionalProperties":false}},
  {"type":"function","name":"read_file","parameters":{"type":"object","properties":{"path":{"type":"string"}},"required":["path"],"additionalProperties":false}},
  {"type":"function","name":"sha256","parameters":{"type":"object","properties":{"path":{"type":"string"}},"required":["path"],"additionalProperties":false}}
]
```

## Local evidence for review

Submission body ends above this heading. The following repository links and handling notes are
local review material and should be omitted from an external submission.

- [Host policy and control verification](host-policy.md).
- [Transport diagnostic and limitations](transport-validation.md).
- [Reviewed capture analysis](transport-probe-2026-10-17/result-reviewed.json).
- [Tested configuration](transport-probe-2026-10-17/config.toml).
- [Offline protocol schema receipts](registry-control-schema-2026-10-17.json).

These links resolve inside the local repository. The sanitized excerpt above is sufficient for
the initial capability request; raw captures and local evidence have not been approved for
external upload. This draft has not been sent.
