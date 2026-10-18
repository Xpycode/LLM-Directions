# Supported broker-only host policy

Policy ID: `directions-broker-only-v1`. Established October 17, 2026 for the bounded,
read-only Codex pilot. This is the supported admission contract, not a claim that a live host
has passed it. **No live host configuration is currently admitted.** E1 remains open.

## Tool boundary

The complete model-visible registry must contain exactly one of each direct function:
`discover`, `list_files`, `read_file`, `sha256`. Names and JSON parameter schemas must match
`runner.TOOLS` exactly; App Server's registration `inputSchema` becomes `parameters` on the
Responses wire. Descriptions may differ; no executable wrapper or extra tool metadata is allowed.
Order is irrelevant. Inspect both `tools` and `input[].additional_tools`; duplicate names fail.

All four functions must dispatch exclusively to the confined broker. `discover` returns only
these four schemas. No shell, writes, apps, browser/web, delegation, user-input, sleep/clock,
goals, MCP resource/template discovery, tool search, or arbitrary code executor is supported.
Empty results, promises to avoid a tool, a read-only filesystem sandbox, or disabled execution
behind an advertised wrapper do not satisfy this policy. Code Mode wrappers and namespaced
aliases are rejected even if they mention the four broker functions in text.

There is no “equivalent accounting” exception for extra tools in v1. Supporting a wrapper or a
native helper requires a separately reviewed policy revision with complete dispatch mediation,
accounting and isolation evidence. Do not silently widen this allowlist to make a probe pass.

## Admission and continued enforcement

The future adapter must implement all of these conditions before a live host is admitted:

1. Pin executable hash/version, effective config, model/effort, policy ID and broker/schema hashes.
   Use an isolated home/profile/environment and a new ephemeral thread. Reject unrecognized
   configuration, fallback, restored tools and manifest changes before any provider request.
2. Capture the actual complete outgoing registry and compare names, multiplicity and schemas on
   every request, including continuations. No additional tool declarations may be hidden in host
   instructions. Check before forwarding to a provider; a post-send log is only diagnostic evidence.
3. Verify host enforcement independently of model compliance: every allowed function reaches the
   broker once; forbidden/unknown calls and unsolicited server requests stop the batch before any
   side effect. Inspect paths the host could execute internally without a client callback. If those
   cannot be disabled or mediated, reject the host. An inventory pass alone cannot prove this.
4. Account for discovery, complete response envelopes, errors, repeated reads and each parallel
   call under the existing per-session and batch budgets. Enforce the frozen read allowlists,
   link/path denials and real SHA-256 receipts. No retries or provider/model fallback.
5. Retain cap, timeout, disconnect, malformed-call and provider-failure evidence, partial output,
   actual elapsed time and verified teardown of the owned process tree. Retain both successful
   allowed dispatch and denied-call evidence using disposable fixtures.

`host_policy.py` implements the advertisement subset; `probe_codex.py` reports its errors.
It does not enforce provider forwarding, validate hidden instructions, mediate native dispatch,
or grant launch acceptance. `inspection-only` is the strongest possible rejection-probe outcome.
The existing fake runner stays fake-only; this policy does not integrate a live adapter.

## Host disposition and supported interfaces

| Candidate | Disposition | Evidence / requirement |
|---|---|---|
| Codex 0.163.0, October 17 isolated configuration | Rejected | Extra advertised tools; broker functions behind disabled Code Mode. See [retained diagnostic](transport-validation.md). No dispatch was tested. |
| Other configuration of the same pinned binary | Unverified | Must pass every admission condition. No working replacement setting is established. |
| Inert transcript host | Local enforcement fixture only | Existing runner checks pass; it cannot establish actual CLI/provider acceptance. |
| Claude | Deferred | No attempt, retry or host substitution under this policy. |

Official OpenAI documentation describes [dynamic tool registration and client callbacks](https://learn.chatgpt.com/docs/app-server)
as experimental. That supports a candidate dispatch interface, not replacement of the native
registry. The [configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference)
describes Code Mode namespace exclusions/direct-call settings and individual feature flags;
the inspected documentation does not establish a replace-all native-tool control for the pinned
binary. A namespace excluded from Code Mode is not thereby proven absent from direct execution.
These are documentation findings, not a proof that every possible configuration is incapable.

Do not enable Code Mode, patch the vendor binary, rewrite provider requests to conceal extra tools,
borrow subscription credentials for another client, or switch to a paid API to bypass this blocker.
Any different host/authentication design is a separate proposal with its own scope and evidence.

## Next dependency

Find and verify a documented host control that supplies the exact direct registry and disables
internal alternatives. If none is available, retain the unsupported-host result and seek an
upstream tool-registry control rather than integrating an unconfined adapter. Once a candidate
exists, validate its actual registry and dispatch locally, then implement the remaining
[transport gates](validation.md#remaining-gates). Remote provider validation and any model pilot
still need explicit scope. Existing call/byte limits, Claude deferral and byte-tradeoff decisions
are unchanged; policy adoption closes no acceptance gate.

## Registry-control verification — October 17

**No supported complete-registry control verified.** This bounded follow-up checked current
official documentation and offline experimental protocol schemas from the same pinned 0.163.0
binary. It does not prove every configuration impossible. No new wire request, dispatch test,
provider request or pilot ran; E1 remains open.

| Candidate control | Documented scope | Policy result |
|---|---|---|
| `dynamicTools` | Experimental registration and client callbacks | No documented replacement of native tools. |
| Code Mode namespace settings | Direct-only or excluded nested exposure | No complete-registry or internal-dispatch guarantee; enabling Code Mode remains out of scope. |
| MCP `enabled_tools` / `disabled_tools`; app tool switches | Per-server or per-app filtering | Does not establish a native-tool allowlist. |
| Feature flags and managed pins | Individual capabilities | No exact four-function registry contract. Managed `unified_exec=false` still permits one-shot execution. |
| Sandbox / permissions | Filesystem and command access | Does not replace the registry or mediate every tool surface. |

Sources opened: [App Server](https://learn.chatgpt.com/docs/app-server),
[configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference),
[managed configuration](https://learn.chatgpt.com/docs/enterprise/managed-configuration),
and [permissions](https://learn.chatgpt.com/docs/permissions). These are documentation findings;
current documentation alone does not establish pinned-binary behavior.

Offline `app-server generate-json-schema --experimental --out <fresh scratch>/schema` exited zero
with isolated `HOME`, `CODEX_HOME`, working directory and environment. Version/hash match the
retained transport pin. The binary warned that it refused temporary-home PATH helper creation.
[Schema receipts](registry-control-schema-2026-10-17.json) retain property extracts and full-file
hashes for `ThreadStartParams`, `ThreadResumeParams` and `TurnStartParams`. None has an explicit
complete-registry replacement/allowlist field. Generic `config` accepts arbitrary keys, which is
not evidence of a supported control. `selectedCapabilityRoots` describes exposing capabilities,
not suppressing native alternatives. No undocumented setting was tried.

The existing wire rejection remains the actual registry evidence. Dispatch cannot be accepted
from schema inspection. Next dependency is an upstream documented registry-and-dispatch control
with support for the pinned host (or a separately scoped host-design proposal). No upstream
message was sent. Earlier captures, source, budgets and policy are preserved.

A [local upstream request draft](upstream-registry-request.md) now states the observed limitation,
requested contract and acceptance examples. It is unsent; it grants no host admission or pilot scope.

Follow-up validation: six policy tests and eight diagnostic tests passed headlessly; `git diff
--check` passed. No implementation changed and no independent-agent review was performed in this
bounded verification. Receipt hashes were checked against the generated scratch schemas.

File folder for Finder Go to Folder:
`/Users/sim/ProgrammingProjects/0-DIRECTIONS/__DIRECTIONS/verification/lean/pilot`
Open `host-policy.md` there.

## Local verification — October 17

Fourteen focused headless tests pass (six policy, eight diagnostic). They use in-memory wire
objects and retained captures only, with no host/network/app launch or profile access. They cover
exact schemas including JSON boolean/integer distinctions, duplicate tools across surfaces,
extras/wrappers/impostors, missing tools, malformed inventories, retained-wire rejection, and a
synthetic valid registry yielding only `inspection-only` before schema alteration blocks it.

```bash
python3 -B -m unittest discover -s /Users/sim/ProgrammingProjects/0-DIRECTIONS/__DIRECTIONS/verification/lean/pilot -p 'test_host_policy.py' -v
python3 -B -m unittest discover -s /Users/sim/ProgrammingProjects/0-DIRECTIONS/__DIRECTIONS/verification/lean/pilot -p 'test_probe_codex.py' -v
```

A fresh read-only independent reviewer found no policy-establishment blocker. Its diagnostic
finding (malformed inventory raised before structured error reporting) was fixed and the delta
reviewed; the affected suite passed. The coordinator then added the synthetic valid/altered-schema
assessment test and ran both final suites. Python syntax and diff whitespace checks pass; session
index coverage is 63/63. These results establish the local policy checker only. No new live host
run, actual dispatch, provider acceptance or pilot result is claimed. Prior captures/analyses and
the fake-runner freeze remain unchanged.
