# Codex findings — local corrections, October 16

**October 18 checkpoint:** [cleanup verification](cleanup-2026-10-18.md) records current source
sizes after the launch exception. The October 16–17 measurements and receipts below are historical;
they do not pin today's templates or testing guide. E1 remains open and pilot work stays parked.

User authorized the review recommendations. Coupled guidance and generated routing were changed
serially; no subagents or additional CLI model sessions were launched. This is a local source
follow-up to E1, not acceptance, rollout or a replacement for the preserved replay results.

## Dispositions

| Finding | Local correction | Remaining gate |
|---|---|---|
| S19 docs records two incorrect hashes and falsely claims all match | `reference/task-state.md` requires executed standard checksum computation or trusted receipts, per-file verification, and blocked reconciliation when hash verification is unavailable | Corrected host behavior unobserved |
| S17 docs prescribes unsupported selection/isolation capabilities | `34_testing.md` requires inspected implementation/configuration or verified documentation; missing support becomes a proposed requirement and a blocked executable case | Corrected host behavior unobserved |
| Build-only routing omits testing guide | Generator explicitly routes builds/tests to `34_testing.md` for effects and no-control limits; both global templates regenerated | Corrected path selection unobserved |
| Path-only assay reads topical bodies | Generator explicitly preserves path-only read limits | Corrected adherence unobserved |
| Final Directions globals misses mental-model path | Restore code-validation/red-flag wording among the three retained header triggers | One observed miss; no statistical regression claim or changed oracle |
| Byte/call increases | Retain measurements and unaccepted tradeoffs; do not claim universal savings | User tradeoff decision remains open |

## Historical local receipts and source provenance — October 16

[Computed receipts](codex-followup-receipts.json) contain executed Python SHA-256 results and
per-file comparisons against archived original fixture inputs. Seven preserved files match their
original bytes; five model-recorded hashes match and two do not. The archive hash and ZIP CRC pass.
This corrects the evidence available to reviewers; it does not turn the failed S19 verification
claim into a pass. Original outputs and the archive remain untouched.

The October 16 receipt identifies all six then-modified source files by before/after hash and byte count.
`final-source-manifest.json` remains the historical replay-source manifest, not a manifest of this
corrected candidate. Before-source hashes refer to the previously clean source files at local HEAD.
Existing baseline/final replay metrics therefore describe the pre-correction sources. Each global
template grows another 185 source bytes; runtime retrieval effects have not been measured.

## Historical focused local validation — October 16

- Generator preservation/validation suite: 50 invocations pass.
- Integrated references/routes and unchanged unrelated guides/Mac plan: pass (47 routes).
- Eight disposable task-state tests pass; 85 frozen baseline hashes pass.
- Static routing accounting: 47 domains, 60 cases, 480 rows pass; this is not observed routing.
- Disposable deployment validation: 40 invocations pass, including preservation, repeat installs,
  dry runs and rejection before writes. No live deployment occurred.
- Shell syntax and diff whitespace pass; session index is 62/62 in sync. Source receipt hashes,
  generated template bodies and current handoff links pass final local checks.

## Optional next pilot — proposed, not launched

The review replaces the undefined eight-tool-turn budget below with explicit proposed call and
byte limits. **No pilot is authorized or scheduled.** The historical harness does not implement
these limits or an actual checksum tool. The later [local runner](pilot/README.md) supplies a
confined checksum tool and fake-host enforcement checks; live transport integration and validation
remain prerequisites before any launch. The proposal below retains its original acceptance scope.

The user subsequently authorized local implementation and validation only. [Runner evidence](pilot/validation.md)
records 31 tests, frozen original/candidate inputs and an independently reviewed fake-host integration.
The local runner scope is complete; corrected host behavior and real transport remain unobserved.

Limit the proposed batch to **three fresh Codex sessions**, serially, against one frozen corrected
candidate, using the historical Codex model/effort (`gpt-6.1-sol`/medium). Record CLI version and
settings; any mismatch needs disclosure before launch. Preserve original fixtures, prompts, oracles,
sources and outputs. Store narrowed pilot fixtures separately and label their reduced coverage.

| Session | Scope and scoring | Tool calls | Returned tool bytes |
|---|---|---:|---:|
| S19 docs checksum diagnostic | Use a disposable copy of the preserved interrupted-migration evidence. Check every recorded original/copy digest using executed receipts, identify the two historical false values, and report reconciliation blocked if verification is unavailable. No migration writes. This checks evidence handling, not full migration or idempotence acceptance. | 24 | 96,000 |
| S17 docs | Retain the original sparse implementation/test evidence and request. Reuse valid evidence, identify the integrated reachability gap, and give one finite remaining batch. Unsupported selection/isolation operations must be labeled proposed requirements with executable cases blocked; no claimed user/test execution. | 24 | 64,000 |
| Directions globals routing | Complete disposable master, globals present, original `no-control` and `domain-02` inputs. Return both unique IDs; required paths are `34_testing.md` and `02_mental-model.md`. No topical-body reads, writes or external-operation requests. | 8 | 32,000 |

Batch ceiling: **three host sessions, 56 tool calls and 192,000 returned tool bytes**, no retries.
Count each requested tool invocation, including errors and built-in discovery, as one call;
parallel requests count separately. Returned bytes mean UTF-8 tool-response content including
errors and repeated reads, not just file retrieval. The runner must stop before dispatching a call
beyond the cap or delivering a response beyond the byte cap. Stop the batch on a cap, timeout,
provider failure or confinement breach, preserve partial evidence and mark affected cases incomplete.
A completed oracle failure is retained without a retry. Proposed watchdog: 180 seconds per session;
record termination grace and actual elapsed time rather than claiming an exact wall-time ceiling.

Request at most 1,200 final-output tokens per session as a brevity target, **not an enforced token
or subscription-cost cap**. Tool limits, byte limits and watchdogs do not bound hidden reasoning,
provider-internal context or exact subscription consumption. The former S17/S19 docs attempts used
18/103 tool calls; the new S19 diagnostic is deliberately narrower to avoid budgeting another full
migration. No Claude requests, broad matrix, parallel agents, provider/model fallback or live
consumer work is included.

Before requesting launch, complete these local prerequisites without a model request:

1. Freeze and hash the candidate's full source/reference inputs, rendered entries, pilot fixtures,
   runner, tool schemas and scoring rules. Keep the historical final-source manifest unchanged.
2. Supply a read-only confined standard SHA-256 tool or runner-owned receipts, with per-path byte
   counts and hashes computed from actual bytes. Check original/copy equality independently.
   Locally verify missing files and symlink escapes fail honestly; simulated success is insufficient.
3. Implement and exercise call/response-byte/watchdog enforcement with a fake local host, including
   error calls, parallel calls, oversized responses and partial-evidence retention. Confinement must
   continue to reject master/outside writes; no native shell, apps, web or delegation tools.
4. Show exact configured entry/prompt/fixture byte sizes for each session and available retrieval
   sizes, separately from measured reads. The 11,238-byte entry total below is for this checkout's
   path, not a promised scratch-render input size. Do not silently reduce fixture evidence to fit.

Routing success covers this Directions/globals two-input diagnostic only. It cannot close the
historical Magpie body-read finding, repository-only/consumer routing, or the full frozen matrix.
An honest unavailable S19 result passes only the evidence-honesty check; successful checksum-backed
reconciliation and an idempotent migration repeat remain unverified. Even three successful sessions
would not close E1 or establish corrected runtime efficiency.

## Reviewed byte tradeoffs — current candidate

**Subsequent authorized rollout, October 17:** both local installations refreshed and 110 project
roots migrated to master routing; [evidence and retained backups](rollout-2026-10-17/README.md).
This supersedes the no-deployment scope below for this Mac only; E1 and runtime claims are unchanged.

**Latest decision, October 17:** user accepted the presented standalone increases (+558 Codex /
+1,483 Claude), arrival load-set increase (+1,909) and execution/log reuse guidance (+989).
[Decision and limits](../../decisions.md#2026-10-17---accept-the-reviewed-instruction-size-increases).
Earlier unaccepted wording below is superseded for those specific source-size items only.
Historical runtime regressions, other unlisted tradeoffs and corrected-host verification remain
open. This does not authorize deployment, consumer migration or another host batch; E1 stays unchecked.

**Current summary, October 17:** local source cleanup is committed in `dc9ce95`; reviewed
cross-project guidance and preservation artifacts are committed in `3407355` and `b9c2a89`.
The [cleanup review](local-cleanup-review.md) and
[guidance provenance](../guidance-review-2026-10-17/README.md) define those separate scopes.
Executed rendering with this checkout's absolute master path gives:

| Initial instructions | Frozen baseline | Current source | Difference |
|---|---:|---:|---:|
| Codex global + repository | 12,120 | 11,238 | -882 |
| Claude global + repository | 19,748 | 18,686 | -1,062 |
| Repository only, Codex | 3,615 | 4,173 | +558 |
| Repository only, Claude | 0 | 1,483 | +1,483 |

Both global-plus-repository entry totals now meet the smaller-entry requirement locally.
Standalone increases and complex-path tradeoffs remain unaccepted. The task-state reference is
3,717 bytes, 385 above the historical integration version; affected workflow subtotals therefore
increase by 385. These are source measurements, not corrected-host retrieval or runtime savings.
Five of the six October 16 corrective-source receipts still match; Claude's template receipt is
historical and predates cleanup. Frozen manifests and replay outputs have not been rewritten.
E1 remains open; thirty Claude observations are deferred. Pilot/upstream work is parked and live
transport must pass before any future pilot. No new host request or rollout is authorized here.

[Saved-read attribution](read-attribution-2026-10-17/README.md) explains the historical S01/S04/S05
increases from the eighteen retained root runs. Status growth is entirely instruction bytes;
execution combines required contract/record work with confirmed unchanged procedure/log rereads.
Its receipts preserve per-run accounting and median variability. [Conditional status factoring](status-factoring.md)
is now committed in `77a673d`: the core is 31.4% smaller, but arrival's combined load set is larger.
Local checks/review pass; no observed host improvement or accepted byte tradeoff follows.
[Execution/log reuse guidance](execution-read-reuse.md) is now committed in `f125e42`; it preserves
required reads, current scope and final verification. Next: review E1 evidence gaps and byte tradeoffs
before selecting acceptance work; replay scores and E1 remain unchanged.

### Historical local measurement sequence

The following dated passes retain their original measurements. Their references to “current”
describe that pass only; the summary above owns today's source accounting.

October 17 second local pass: consolidated project detection (including the master's root state
file) and replaced the unconditional Xcode kill/clean/launch recipe with the canonical testing
and app-handoff references. Existing user requests take precedence over a startup question.
This removes 914 template-source bytes and 848 rendered bytes from the preceding candidate;
Claude global + repository is now **18,686 bytes**, 1,062 below the frozen baseline. Codex remains
11,238 bytes, 882 below baseline. Executed UTF-8 measurements, 47-route/reference integration,
50 disposable generator invocations, generator shell syntax and `git diff --check` pass.
Generated routing bytes were unchanged by this pass, and template master references resolve.
This is serial local template maintenance; no live-host observation or independent review claimed.
The earlier measurements and replay evidence below remain historical, not current source totals.

October 17 local cleanup supersedes the Claude entry total below: shortened the template source
comment and command-catalog explanation by 257 bytes, preserving their instructions. Rendered
Claude global + repository is now 19,534 bytes, 214 below the frozen 19,748-byte baseline.
Codex remains 11,238 bytes, 882 below baseline. Executed local UTF-8 measurement and
`python3 -B verification/lean/test-integration.py` passed: 47 routes, shared reference paths and
unchanged unrelated guide/Mac-plan bytes. `git diff --check` passed. Historical source receipts
below remain unchanged; the Claude template now has this additional edit. No runtime efficiency
or rollout acceptance follows. User clarified local cleanup as the goal; registry/pilot work and
the unsent upstream request are parked, not the next maintenance dependency.

Executed local measurement on October 16 renders `[LOCAL_DIRECTIONS_PATH]` using this checkout's
absolute path, then counts UTF-8 bytes plus the repository entry. All six corrective-source hashes
still match the computed receipt. These current source totals supersede the earlier integration
totals for this candidate only; historical replay measurements remain unchanged.

| Initial instructions | Frozen baseline | Current candidate | Difference |
|---|---:|---:|---:|
| Codex global + repository | 12,120 | 11,238 | -882 |
| Claude global + repository | 19,748 | 19,791 | +43 |
| Repository only, Codex | 3,615 | 4,173 | +558 |
| Repository only, Claude | 0 | 1,483 | +1,483 |

The corrections add 185 bytes per global template and 385 bytes to the task-state reference.
Consequently, the integration report's once-per-file execution/closeout and Mac/recovery subtotals
each grow another 385 bytes when they include that reference. These are source subtotals, not
observed host costs. Claude no longer satisfies the plan's smaller-entry-per-host requirement:
trim redundant prose with affected validation, or obtain an explicit scoped acceptance exception.
Claude's testing deferral does not waive this requirement.

### Historical replay totals and open tradeoffs

For the preserved pre-correction Codex replay, configured initial bytes plus median actual retrieval
bytes give the following descriptive totals. Initial bytes were constant within each three-run
group, so addition preserves the median. They exclude prompt/tool-envelope/hidden host context and
are not token, cost or speed estimates. Scratch paths differ from this checkout's source rendering.

| Workflow | Baseline | Historical final | Change |
|---|---:|---:|---:|
| Status S01 | 29,279 | 31,224 | +1,945 (+6.6%) |
| Small fix S02 | 15,824 | 15,306 | -518 (-3.3%) |
| Ordinary log S03 | 40,707 | 37,458 | -3,249 (-8.0%) |
| Selected-task closeout S04 | 60,374 | 65,381 | +5,007 (+8.3%) |
| Two-wave continuation S05 | 61,837 | 69,610 | +7,773 (+12.6%) |

Source: [representative metrics](host-replay-2026-10-16/representative-metrics.json).
No corrected-candidate runtime total is available. Recommended disposition, **not user acceptance**:

- Retain preservation, authority and recovery safeguards. Consider their documented standalone and
  complex-path source increases as explicit scoped tradeoffs, rather than removing safeguards to
  achieve a byte target.
- Keep status/closeout/continuation runtime regressions open. Attribute existing saved reads to
  required work versus avoidable retrieval before proposing changes or another benchmark.
- Keep Claude's entry-size requirement separate from its thirty deferred observations. A Codex-only
  pilot cannot establish Claude acceptance. No universal efficiency or rollout claim follows.

E1 stays unchecked. Claude's thirty rows remain deferred. No independent agent review of these
corrections is claimed; model-driven validation remains unverified within the no-new-test scope.
