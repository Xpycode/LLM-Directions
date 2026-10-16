# LE16 — test effects and finite acceptance

Implemented 2026-10-16 against the frozen LE01 scenarios. This is source review plus disposable
shell evidence, not observed Codex/Claude host acceptance or a live app test. E1 remains required.

## Changes and interface

- `34_testing.md` owns the command/class/data/startup/authorization/process/result contract,
  originating-Mac recovery record and finite acceptance rules. Existing API examples are explicitly
  instructional, not run authorization. The unconditional three-run checklist is now justified repeats.
- `commands/test-app.md` consumes that contract, checks actual backend presence/schema, prepares a
  scoped plan and supports available authorized or manual alternatives. Removed the assumed AppProbe
  checkout, unconditional launch/cleanup, and repeated permission prompt when scope already exists.
- `commands/check.md` applies the same boundaries to audits and preserves open artifact acceptance.
  No general runner framework or project-specific safe command was introduced.

LE08 can link the recovery contract: originating Mac, exact target/state, original state or backup,
authorized actions and expiry, restoration steps, evidence and unresolved status survive handoff.
Expired scope never authorizes cleanup; another Mac cannot establish local recovery.

## Frozen scenario walkthroughs

These are instruction traces with expected dispositions, not measurements of host compliance.

| Scenario | Trace through revised source | Disposition |
|---|---|---|
| S09 no-control build | test-app §1 separates build from launch and supplies full containing-folder path/app name | Artifact handoff only; no automatic app action |
| S10 app-hosted tests | Testing effects table + test-app §1 require inspecting TEST_HOST/startup before execution | App-hosted cases blocked under no-control; inspected headless subset may run |
| S11 missing AppProbe | test-app §2 checks actual inventory/docs before any invocation | Missing backend recorded; available authorized alternative or finite manual batch; no invented command |
| S12 support-data deletion | Testing isolation contract + test-app §3 inject disposable namespaces through startup and disable production work | Unsafe cleanup cannot run against live state; production untouched verification is required, not claimed performed here |
| S13 expired window on another Mac | Testing recovery contract + test-app §4 retain machine, target, scope/expiry and restoration evidence | Recovery stays open on originating Mac; no timer-derived authority or false restoration |
| S14 producer 7 / formatter 0 | Testing results contract + fixture below capture immediate PIPESTATUS and owned child wait | Failure preserved; wrapper/name collision cannot supply success |
| S17 finite acceptance | Testing acceptance contract + test-app §3–4 + check preamble verify integrated expectations and provenance | One finite remaining batch; valid evidence reused; repeats require reason; manual gates remain open |
| S08 / S22 scoped lifecycle | test-app §1/§3 respect keep-running and existing exact authorization | No default cleanup or redundant approval; only authorized target/actions |

## Validation evidence

Executed successfully:

```text
bash -n verification/lean/test-safety/check.sh
bash verification/lean/test-safety/check.sh
PASS: producer exit 7 survives successful formatter; raw log retained during evaluation
PASS: exact receipt selects owned child; unrelated wrapper, same-name decoy and reused PID rejected
PASS: wait on directly owned child returns actual exit 7
```

The fixture uses a disposable directory, a failing shell function, `tee`, a successful formatter,
and one directly spawned shell child that exits on its own. Process-selection adversaries are a
synthetic inventory: exact PID/start/executable matching rejects a wrapper, same-name decoy and
stale start token. This demonstrates the identity rule, not an OS-wide process monitor. No apps
are launched, signalled or controlled; no production state is touched. The structured temporary
result records producer 7/tee 0/formatter 0 and `passed:false`; temporary files are removed on exit.

The prescribed `rg -n 'AppProbe|headless|hosted|isolat|timeout|exit|acceptance'` search over the three
source files was reviewed: policy matches establish the contract; remaining XCTest timeouts are
API examples; existing timing/teardown sections retain their narrower evidence semantics. AppProbe
has no remaining assumed location or runnable hardcoded invocation in these files. Those examples
and historical Mac-control observations do not authorize a new live test.

Remaining gate: E1 must observe actual host choices and acceptance handoffs using isolated projects
and appropriate authorization. This local walkthrough does not close AC12/AC13 host evidence.
