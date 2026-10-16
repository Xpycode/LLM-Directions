# Local bounded pilot runner

This directory implements local preparation and enforcement checks for the reviewed
[three-session proposal](../codex-followup.md#optional-next-pilot--proposed-not-launched).
E1 remains open. No model session, provider connection or pilot is launched by these tools.

The runner launches only its bundled inert transcript host. That host replays JSON requests;
it cannot execute a configured shell command or substitute a provider executable. This tests
the local transport and broker, not Codex CLI behavior or provider-internal tool discovery.
A live adapter must be integrated and validated separately before a launch can be proposed.

The proposed session ceilings remain S19: 24 calls / 96,000 response bytes; S17: 24 / 64,000;
routing: 8 / 32,000. The batch ceiling is 56 / 192,000, with no retries. UTF-8 response
content, errors and discovery count; parallel requests count individually. The watchdog
records actual elapsed time and termination grace. These limits do not bound hidden reasoning,
tokens or subscription consumption.

Only confined file discovery, reading and standard SHA-256 receipts are exposed. There is no
write, simulation, shell, web, app or delegation tool. The freeze includes original evidence,
corrected source inputs, exact rendered entries, prompts, schemas, scoring rules and runner
implementation. Configured inputs and available retrieval bytes are recorded separately from
responses actually delivered during a replay.

S19 is a read-only checksum diagnostic, with preserved originals and copies; it cannot establish
completed migration or idempotence. S17 retains the original sparse evidence and request.
Routing covers only Directions with globals and the two frozen `no-control` / `domain-02`
inputs. None of these checks closes historical consumer or Claude findings.

Validation results, exact invocation paths and remaining limitations are recorded in
[validation.md](validation.md).
