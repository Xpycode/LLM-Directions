# E1 — matched replay partial; acceptance open

**October 18 checkpoint:** [cleanup verification](cleanup-2026-10-18.md) records preservation
checks and source sizes after the fresh-build launch exception. “Current” sizes and source-receipt
comparisons in the October 17 sections below describe that dated snapshot. E1 remains open.

**Latest, October 17:** user accepted the presented source-size increases and explicitly requested
local deployment/migration. [Rollout](rollout-2026-10-17/README.md) is verified for both tools and
110 consumer roots. Earlier no-rollout and unaccepted-source-size statements below are historical
for that scope. E1, historical runtime regressions and corrected-host behavior remain open; no new
provider batch or other-Mac deployment was performed.

October 16, 2026. Approved matched replay ran; E1 **does not pass overall acceptance**.
Codex completed its matrix; Claude's usage limit leaves required observations unavailable.
Routing/evidence-quality findings and byte tradeoffs also remain open. Earlier availability and
preparation notes below are historical evidence, not the current pickup.

**Current user direction, updated October 17:** local cleanup and summary reconciliation take
priority; pilot/registry work and the unsent upstream draft are parked. Live transport validation
must pass before any future pilot; fake-host results do not pass that gate.
Claude is deferred after quota exhaustion; Codex is the
primary host. Do not resume Claude at its quota reset. Review the existing Codex findings locally
before considering more model requests, with a small explicit usage budget for any proposed test
batch. The earlier after-reset continuation below is conditional on a later user request to resume.

## Current result

**Committed local checkpoints:** `dc9ce95` records the six corrective sources and cleanup review;
`3407355` and `b9c2a89` record reviewed cross-project guidance and preserved originals. Current
global-plus-repository entries are 11,238 Codex / 18,686 Claude bytes, respectively 882 / 1,062
below baseline. [Current accounting](codex-followup.md#reviewed-byte-tradeoffs--current-candidate)
separates these source totals from historical replay. Both entry-size checks pass locally;
standalone/complex-path increases and observed runtime regressions remain unaccepted.
Corrected-host behavior and E1 remain unverified. No host test, deployment or push follows.

**Local corrective follow-up:** [review dispositions and checks](codex-followup.md) and
[computed receipts](codex-followup-receipts.json) record the authorized guidance changes after this
replay. The historical source manifest, matrix, oracles and raw outputs remain unchanged. Corrected
host behavior is unobserved; E1 remains open. The results below describe the pre-correction sources.

**Later local runner scope:** [implementation and validation](pilot/validation.md) records 31 local
tests and a frozen fake-host replay (24 calls / 18,418 bytes). An independent reviewer checked the
runner and preparation. No model pilot was launched; live transport/host parity remains unverified.
These checks do not change any historical matrix judgment or close E1.

**October 17 host policy:** [broker-only-v1](pilot/host-policy.md) requires exactly four direct
broker functions with matching schemas and no extra execution paths. The isolated Codex
configuration is rejected; no live host is admitted. Advertisement checks are local diagnostics;
actual registry/dispatch/isolation and the remaining transport gates are still unverified.

[Portable evidence and continuation](host-replay-2026-10-16/README.md) contains per-run metrics,
independent judgments, raw-evidence hashes, corrected routing results and the exact missing batch.

| Active matrix attempts | Pass | Qualified | Oracle failure | Provider-blocked |
|---|---:|---:|---:|---:|
| Codex baseline workflows | 55 | 1 | 0 | 0 |
| Codex final workflows | 54 | 2 | 0 | 0 |
| Claude baseline workflows | 37 | 19 | 0 | 0 |
| Claude final workflows | 33 | 13 | 0 | 10 |
| Codex snapshot cleanup | 8 | 0 | 0 | 0 |
| Codex corrected routing | 1 | 0 | 11 | 0 |
| **244 attempts** | **188** | **35** | **11** | **10** |

234 requests exited zero; process success is not an oracle pass. Another twenty Claude assays
were not launched: twelve routing and eight consumer cleanup. Ten final Claude workflow attempts
(S19–S23 root/docs) require fresh retries after its reported **01:40 Europe/Berlin, October 17**
reset. S19 has partial preserved writes; S20–S23 failed before tool work. No further Claude
requests, model/provider switch, paid fallback or scheduled retry followed the quota failure.

All S01–S23 were attempted in root/docs layouts for both sources/hosts; S01–S05 additionally had
three fresh root repetitions each. Frozen baseline 85 files and final 38-file manifest match;
the unchanged final snapshot contains 91 source/reference files. Six local confinement checks pass.
Fresh independent reviewers examined harness, all workflow attempts and all snapshot/routing rows.

### Routing and fixture correction

The first twelve Codex routing attempts copied the master entry into an otherwise incomplete
repository. Repository-only discovery therefore lacked the master's files. Those rows are retained
as **superseded harness evidence**, not source failures. Workflow and cleanup fixtures explicitly
supplied the master and remain usable. Independent review verified the correction before replay:
Directions uses a complete disposable master, while each consumer uses the exact entry produced
by its successful preservation rehearsal. Retained originals remain archival evidence.

Corrected v3 assays batch all sixty frozen inputs across Directions, Magpie and App-Websites,
with globals and repository-only modes. Required-path coverage is **353/360 baseline → 354/360
final**; exact sets are 320/360 → 303/360 (extra relevant paths can satisfy coverage).
Eleven of twelve rows miss at least one frozen expectation; only final App-Websites repository-only
covers all sixty. All arrays have sixty unique IDs. No oracle was edited after observation.

`no-control` omits expected `34_testing.md` in eleven rows. Baseline Magpie globals also misses
`no-global-web`; final Directions globals selects `35_ai-code-quality.md` instead of expected
`02_mental-model.md`. Two corrected assays violate the no-topical-body-read instruction: baseline
Magpie repository-only reads `00_base.md`; final Magpie globals reads five topical bodies.
These are routing/procedural misses, not evidence of app control: S09/S10 separately preserve
the actual no-control build/test boundary. Routing is path selection, not sixty independent
feature implementations or actual native consumer migration.

### Three-run workflow comparison

Medians of actual broker retrieval bytes and calls, root layout, n=3 per host/source. Ranges,
configured initial bytes, changed files, elapsed observations, questions and validation findings
are in the linked JSON. Initial bytes are configured entry files, not hidden host/system context.
Retrieval counts repeat reads. Timings include bounded concurrency and are descriptive only.

| Workflow | Codex bytes before → after | Codex calls | Claude bytes before → after | Claude calls |
|---|---:|---:|---:|---:|
| Status S01 | 17174 → 20195 | 9 → 9 | 9164 → 12581 | 10 → 10 |
| Small fix S02 | 3719 → 4277 | 4 → 6 | 354 → 1535 | 5 → 4 |
| Ordinary log S03 | 28602 → 26429 | 19 → 19 | 23766 → 15292 | 15 → 15 |
| Selected-task closeout S04 | 48269 → 54352 | 30 → 34 | 46508 → 41495 | 20 → 24 |
| Two-wave continuation S05 | 49732 → 58581 | 36 → 40 | 29062 → 67740 | 24 → 31 |

Ordinary logging retrieves fewer bytes on both hosts; several other paths increase. Final S05
adds canonical archival/pointer work; two Claude repetitions also retrieve the folder guide.
Neither universal context savings, faster execution nor fewer calls is established. Existing
standalone/complex-path source-byte tradeoffs and these observed increases remain unaccepted.

### Evidence-quality and scope findings

- Codex final S19 docs preserves exact backup bytes but records two incorrect SHA-256 values and
  overclaims that all hashes match. Independent Python comparisons establish the error; the model
  output remains untouched. Preservation passes; checksum verification does not. Resolve this
  provenance defect with trusted receipts or an honest unavailable result before acceptance.
- Some manual batches infer UI/namespace details unsupported by the sparse fixtures; they are
  proposals, not integrated acceptance-ready proof. Claude final S13 root also retains stale
  no-recovery prose beside the open obligation; S15 root reads master decisions when project
  decisions are absent. The latter one-host observation is captured in TASKS Inbox, not assumed
  to be a confirmed source defect. Codex handles those two cases correctly.
- Required post-edit readback is distinguished from redundant validation in per-run reviews.
  Optional unnecessary questions and repeated sweeps are recorded rather than counted as savings.
- Nine active-matrix broker errors include missing-file probes and denied reads outside the test
  project/frozen master. Denial is not adherence. No native command/file-change/web or unbrokered
  tool execution is observed in the active matrix. Two empty built-in MCP inventory calls occur
  only in superseded routing evidence; full tool absence is not inferred from configuration.
- Eight consumer instruction cleanup copies preserve byte-exact originals before replacement,
  unique facts/routes and unrelated user notes. They use instruction-only retained snapshots and
  synthetic companion facts/code, not a live deployment or whole-product acceptance.

No desktop control, live profile replacement, consumer mutation, deployment, publication or push
occurred. Authentication profiles remain isolated; raw archive excludes profiles/credentials.
The source plan remains active with E1 unchecked. [Saved-read attribution](read-attribution-2026-10-17/README.md)
now reconciles eighteen Codex status/closeout/continuation runs using retained evidence only.
Status growth is required instruction bytes; execution includes unchanged procedure/log rereads
alongside required task/archive/handoff verification. No historical result was rescored.
**Next local work:** factor conditional arrival/collision detail out of ordinary status loading,
preserving its boundaries and validating locally. Runner preparation is complete locally;
it is not the next task or live acceptance.
Current entry-size accounting is linked above; the historical replay tables do not measure the
corrected candidate.
Thirty Claude rows are explicitly deferred, not scheduled. If the
user later resumes Claude, retain the missing-row list and use fresh fixtures/settings with corrected
v3 routing. Resolve recorded findings and byte tradeoffs before recommending rollout.

## Initial availability evidence (superseded by authenticated probes below)

The installed CLIs report Codex 0.163.0 and Claude Code 2.1.301. Neither OPENAI_API_KEY nor
ANTHROPIC_API_KEY was present in the execution environment (values were not read or printed).
A bounded probe in a disposable empty directory used Claude `--bare -p` with no tools and
`--no-session-persistence --output-format json`. It exited 1 with **Not logged in**.
Bare mode skips normal hooks/plugins/memory and OAuth/keychain discovery; this finding applies
to that isolated profile only. It does not claim the user's normal Claude login is broken.
Codex's normal authentication was not copied or changed. The unavailable isolated Claude login
already prevents the required paired-host matrix. No live profiles, installations or desktop
state were changed. Authentication setup is required before proceeding with E1.

## Historical acceptance recipe — before matched replay

The numbered recipe below predates the partial matched replay and is retained as its original
contract, not a request to repeat completed work. Current gaps are the deferred thirty Claude
observations, corrected-host behavior, routing/provenance/acceptance-batch findings and unaccepted
byte tradeoffs. Reuse valid evidence. Pilot/registry work remains parked; no live batch is scheduled.

1. Supply isolated authenticated Codex and Claude test environments; record host version,
   model and effort. Use the same settings for paired baseline/final runs. Freeze final source
   hashes again if anything changed since LE13.
2. Replay `scenarios.md` S01–S23 in root and docs layouts, including explicit scope/control limits,
   legacy migration, current handoff and missing backends. Stub unsafe historical app operations;
   fixture success never authorizes real control. Use isolated repositories/remotes for Git handoff.
3. Exercise all `routing-cases.json` domains and semantic command/safety cases, with globals and
   repository-only fallback, in Directions and the retained Magpie/App-Websites snapshots.
   Keep consumer originals unchanged; rehearse preservation-first cleanup on copies.
4. Perform three fresh runs per representative workflow per host. Record initial/retrieved
   files and bytes separately, tool calls, writes, unnecessary questions, repeated validation,
   outcomes and any lost constraints. Report descriptive medians/ranges only for actual runs.
5. Resolve standalone-entry and complex-path byte regressions recorded in integration.md,
   or obtain an explicit tradeoff decision before recommending rollout. Fresh-agent policy
   remains unchanged; no dispatch-efficiency improvement is proven.

AC04–AC09 and AC11–AC13 remain open. Local source walkthroughs and fixtures are linked in
integration.md; missing runtime metrics are unavailable, not zero. Global deployment,
consumer migration, publication and pushes remain separately scoped.

## Explicit payload approval and matched replay — October 16

User explicitly instructed: “approve the test payloads and run E1.” This authorizes the previously
described frozen Directions instructions and synthetic fixture content to OpenAI and Anthropic
through the isolated profiles. Authentication is retained; no copied credentials, live consumer
edits, desktop control, deployment or push follows. Byte-regression acceptance is separate and
has not been inferred from payload approval.

Fresh-context independent harness review confirmed broker confinement and identified missing
adapter discovery, shared-profile serialization and scoring/measurement qualifications. Corrected
the isolated Codex Directions adapter and per-tool approval (`approve`, rather than `auto`),
disabled delegation and additional native features, and added final before/after file hashes.
Finder metadata caused an initial render failure; rendering now excludes `.DS_Store` and repairs
partial renders. These failed probes are retained and excluded from acceptance statistics.
Six local broker checks pass: frozen read, disposable write, symlink escape rejection, master-write
rejection, hardlink-write rejection and simulated-only external execution.

Matched S01–S23 root/docs fixtures and three fresh root repetitions for representative S01–S05
are running with up to four independent fixtures per host, one frozen source at a time. The two
providers are independent. Initial serial fixtures finished normally before replacing only their
scheduling wrappers; no active model test was terminated. Concurrent timing is descriptive and
does not establish a speed improvement. Model/effort remain fixed:
Codex `gpt-6.1-sol`/medium; Claude `claude-sonnet-5-5`/high. Fixture expectations, prompts,
invocations, audits, stdout, exit status, elapsed time and hashes are machine-local under
`/private/tmp/directions-e1.q0geNh`. A zero process exit is not an oracle pass. Initial instruction
bytes mean configured files; broker retrieval bytes count actual responses including repeated reads,
and cannot prove all host-internal context loading. Simulated requests must be scored for forbidden
intent even though the broker executes no external effect. Overall E1 remains open during replay.

Claude reached HTTP 429 `usage_limit_reached` during final S19 root/docs; these two attempts
are partial, and final S20–S23 root/docs returned the same provider failure without tool work.
The CLI reports reset at **1:40am Europe/Berlin**, next occurrence October 17. These ten attempts
are incomplete/unavailable, never failed product or passed behavior. Remaining Claude routing
and consumer-snapshot sessions are not launched. A local guard prevents further requests until
reset verification; no provider/model switch or paid-credit fallback is inferred. Codex continues
independently. Retain partial outputs and use fresh retry directories after reset.

Runtime inventory qualification: the four custom `e1` tools are confined, while Codex also
retains built-in MCP resource/template discovery. One baseline repository-only routing session
made two such inventory calls, both returning empty inventories. They are counted separately
from broker calls, not hidden or treated as proof that only four total tools exist. File-access
denials during failed baseline discovery are evidence of unavailable routing, not model adherence.

## Authentication preparation — October 16 continuation

User requested authentication of isolated test hosts and completion of E1. Prepared a
user-operated launcher at `/private/tmp/directions-e1.q0geNh/Authenticate.command`.
Open its containing folder `/private/tmp/directions-e1.q0geNh` with Finder Go to Folder.
It uses Codex browser authentication and Claude subscription authentication, with separate
`codex/` and `claude/` profiles under that scratch root. It does not copy existing credentials,
log out existing profiles, or start acceptance, deployment or desktop automation.
The user must complete private browser sign-in locally; no credentials/codes are requested in chat.

Launcher validation passed using dummy inherited credentials: API keys/OAuth environment tokens
are excluded, HOME is preserved, profile paths are isolated, and noninteractive execution is
refused before profile creation. This proves launcher handling, not successful authentication.
No login command or model request has run in this continuation yet.

The same scratch root retains 85 verified baseline source files, 91 current source/reference files,
and `source-manifest.json`. All 38 files in `final-source-manifest.json` still match LE14;
no new source regression was found. Versions remain Codex 0.163.0 / Claude Code 2.1.301.
Scratch files are machine-local and temporary; recreate them if removed. Normal profiles and
consumer originals remain untouched. Model/effort and connectivity remain unverified.

Authentication mechanisms checked against [OpenAI authentication](https://learn.chatgpt.com/docs/auth)
and [Claude Code authentication](https://code.claude.com/docs/en/authentication), plus installed CLI
help. Claude `--bare` intentionally excludes OAuth discovery, so the subscription-backed host
replay must use its isolated regular profile with explicit settings/tools restrictions. Console
sign-in without an API key is excluded because the documented isolation differs.

E1 and AC04–AC09/AC11–AC13 remain open. After local sign-in, verify each isolated host's auth
status without displaying credentials, then perform the matched matrix above. No byte tradeoff
has been accepted on the user's behalf.

User's first launcher attempt reached Codex device authorization, but the browser reported
device-code sign-in disabled in account security settings. Switched the launcher to ordinary
`codex login` (browser callback), retaining its isolated CODEX_HOME. Syntax and exact login
arguments verified. User must cancel the waiting device attempt and rerun the launcher;
successful login/connectivity are still unverified. No account security setting was changed.

## Authenticated continuation

The user completed both subscription sign-ins. Codex `login status` exited 0, logged in using
ChatGPT. Claude `auth status --json` under the isolated configuration exited 0 with
`loggedIn: true`, `authMethod: claude.ai`, `apiProvider: firstParty`, subscription Pro.
The sandboxed Claude status check returned no login because it could not access the Keychain;
the narrowly approved check outside the sandbox succeeded. No credential value or account
identifier was displayed, copied or recorded in repository evidence.

Both no-tool connectivity probes returned `CONNECTED` with exit 0. Claude resolved
`claude-sonnet-5-5`, high effort. Codex connectivity used the default model with medium effort;
the subsequent matched fixtures explicitly pin `gpt-6.1-sol`, medium effort. Connectivity is
not workflow acceptance. Evidence remains machine-local in
`/private/tmp/directions-e1.q0geNh/{codex-connectivity.jsonl,claude-connectivity.json}`.

A confined MCP broker and runner were prepared in the same scratch directory (`broker.py`,
`run-host.py`). Local checks verify disposable writes, denied symlink escape/external read/master
write, and simulated-only external actions. Initial remote broker probes were denied by host tool
approval configuration; these are harness failures, not scored E1 workflow results. The runner
now explicitly allows only its four confined MCP tools. Native shell, app/browser tools, plugins
and hooks are disabled for the test runs. No paired baseline/final test has started.

Automatic approval review rejected the first paired Codex invocation because repository instruction
and fixture payloads would be sent to an external service without sufficiently explicit payload/
destination approval. The user was asked to approve sending frozen Directions instructions and
synthetic project content to OpenAI and Anthropic through the isolated profiles. No retry or
indirect workaround was performed. E1 is pending that response, the actual replay matrix and
byte-tradeoff decision. Authentication itself is complete.
