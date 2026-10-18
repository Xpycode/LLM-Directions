# Codex transport prerequisite — October 17, 2026

**Blocked/incomplete. No pilot ran.** The tested configuration does not provide a usable,
broker-only advertised tool surface. This is evidence about one configuration of the pinned
binary, not proof that every configuration is incapable. E1 and all pilot gates remain open.

## Actual host evidence

`probe_codex.py` started the installed Codex app-server with a new disposable `HOME`,
`CODEX_HOME` and working directory, no inherited credentials/provider environment, strict config,
four dynamic broker tools, read-only sandbox, disabled native feature flags and zero provider
retry settings. A loopback HTTP server captured the request and returned terminal HTTP 400;
it supplied no model output or tool instructions. No OpenAI/Claude model request was configured.
This is an actual CLI protocol probe with an inert endpoint, not real-provider acceptance.

- Pinned executable: `/Users/sim/.codex/packages/standalone/releases/0.163.0-aarch64-apple-darwin/bin/codex`.
  Version: `codex-cli 0.163.0`; SHA-256:
  `8813367285524ac798dd96d1b071aea30d58708c7226fd236cd275cf1cfdee31`.
- One `/v1/responses` request reached the local endpoint; its requested model/effort were
  `gpt-6.1-sol` / medium. The error notification says `willRetry:false`; the turn failed as intended.
  This tests one terminal rejection, not disconnect, stream or timeout retry behavior.
- The request advertises `functions.exec`, wait/input tools, clock sleep and collaboration tools.
  Its nested textual declarations include the four broker tools plus goal, MCP-resource and clock
  functions. They are not four direct structured broker tools. The host warns that disabled Code
  Mode will fail closed. Advertisement does not establish that any of these tools can execute;
  no dispatch was tested. Enabling the host without a verified tool policy is not a solution.
- The directly owned parent exited zero; measured probe interval was about 0.626 seconds.
  Descendant teardown and outbound-network traffic were not independently instrumented.
  The configuration targeted loopback only, with no credentials; this is not a network-capture claim.

The first sandboxed attempt could not bind loopback and launched no CLI. The narrowly scoped
rerun was approved automatically. The initial analyzer missed `additional_tools`; raw output is
retained. The final `result-reviewed.json` supersedes both earlier analyses without replacing them.
No second host run was needed to reanalyze the exact captured request.

## Retained evidence and checks

Folder for Finder Go to Folder:
`/Users/sim/ProgrammingProjects/0-DIRECTIONS/__DIRECTIONS/verification/lean/pilot/transport-probe-2026-10-17`

Open `result-reviewed.json` for the current analysis, `requests.json` for the actual wire request,
`rpc.json` for protocol/warning/error events, `config.toml` for tested settings, and `manifest.json`
for computed evidence hashes. Raw scratch folder:
`/private/tmp/directions-codex-transport-probe-20261017-b`.

Six no-network regression tests pass: direct broker tools, additional-tool namespaces, native extras,
absent inventory, namespace impersonation and retained-wire replay with nested declarations,
disabled-host warning, wrong-path and repeated-request rejection. Command:

```bash
python3 -B -m unittest discover -s /Users/sim/ProgrammingProjects/0-DIRECTIONS/__DIRECTIONS/verification/lean/pilot -p 'test_probe_codex.py' -v
```

A fresh-context independent reviewer checked host capabilities and the retained probe, identified
the nested-tool/disabled-host qualifications and requested the retained-wire regression and stricter
inventory checks. These corrections are incorporated; no independent live-provider result is claimed.
The probe is diagnostic tooling, not a reusable acceptance runner or live adapter. The existing
fake-only runner and historical freeze were unchanged.

## Next dependency

The [supported policy](host-policy.md), `directions-broker-only-v1`, now requires exactly four
direct broker functions with exact schemas and no extra paths; there is no equivalent-accounting
exception in v1. The retained configuration is rejected; no live configuration is yet admitted.
Find a supported registry control meeting that contract and verify the
actual advertised surface and dispatch before integrating a pilot adapter. Current documentation
describes [dynamic tool registration](https://learn.chatgpt.com/docs/app-server) and
[individual feature settings](https://learn.chatgpt.com/docs/config-file/config-reference);
neither inspected interface established a replace-all native-tool policy.

Then implement actual envelope accounting, launch-time frozen-manifest enforcement and failure/
watchdog/teardown cases from [the remaining gates](validation.md#remaining-gates). Remote provider
validation needs its own explicit scope; no pilot, Claude retry, fallback, desktop control, live
deployment, consumer migration or push follows from this probe. Existing budget and byte decisions
are unchanged.
