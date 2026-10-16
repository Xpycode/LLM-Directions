# LE07 routing experiment — October 16, 2026

Provisional format selection: **shortened inline map**. Its static reachability and
installed-global byte conditions pass for both hosts. The compact domain router fails
the ordinary topical-path byte condition after its extra index read. Neither result
is observed host recall; AC04 and E1 remain open. No rollout recommendation is made.

## Reproducible artifacts and method

Run `python3 verification/lean/measure.py --routing` for the concise check, or
`python3 verification/lean/measure.py --routing-json` for all 480 accounting rows and
candidate SHA-256 hashes. `--check-baseline` continues to verify the immutable 85-file
LE01 snapshot. All candidate Markdown is concrete UTF-8 content under `routing/`.
`inline.md` and `router.md` are replacement managed bodies; the four host fixtures
splice only that body into frozen global templates. Both candidates preserve all
other global-template bytes. `repository.md` preserves frozen AGENTS.md and adds a
standalone fallback. There was no repository CLAUDE.md in LE01; the separate
`repository-claude.md` is a proposed concise durable repository entry point.

Measurements render `[LOCAL_DIRECTIONS_PATH]` to the actual absolute master path,
count UTF-8 bytes, and keep retrieved guide/command bytes fixed at LE01 values to
isolate routing cost from other tasks. Initial globals and repo instructions are
counted separately from subsequent reads. One complete file read is one modeled
retrieval call; discovery, batching, cache behavior, tool overhead and host-specific
skill auto-loading are not measured. The frozen manifest supplies source hashes;
the full JSON supplies candidate hashes. Host/version/model/effort, actual tool calls,
questions, writes, elapsed times and three-run distributions are **unavailable**.
There are no token, latency or statistical claims.

## Coverage and dispositions

`routing-cases.json` contains 47 concrete natural requests, one per currently eligible
canonical guide, plus 13 ordinary-command, continuation, incidental-keyword, safety,
and missing-global cases. Each carries explicit required paths and a disposition.
The checker verifies exact equality with the live LE03 eligibility output, resolves
every expected path, and accounts for every case in both hosts, with and without
globals, for both candidates (60 × 2 × 2 × 2 = 480). It does not classify prose or
assert that a model obeyed a rule. Domain labels and filenames were reviewed against
the supplied requests; all paths are directly discoverable in the inline map and
in the two-stage detailed index. Ambiguous requests explicitly allow inspection of
canonical filenames and TRIGGERS headers; such additional discovery must be recorded
in E1 and is not claimed free here.

The inline candidate retains the first three generated trigger terms (or title
fallback), complete filenames and shared intent-matching/safety instructions.
Incidental quoted words cause no guide reads in the oracle. Commands go directly
to the complete canonical command, including slashless `status arrive`, `log clear`,
and natural-language continuation. Explicit no-agent/no-commit limits survive.
Secrets, dirty work, multi-Mac recovery and UI constraints have dedicated cases;
the UI safety case reads both 36 and 47. No-control build handoff routes testing
guidance but never authorizes a launch. These are expected outcomes requiring E1
observation, not a successful behavioral test.

## Installed global plus repository comparison

| Host / candidate | Baseline initial | Candidate initial | Website retrieval bytes / calls | Website total | Plain status total | Typo-only total |
|---|---:|---:|---:|---:|---:|---:|
| Codex inline | 12,120 | 11,119 | 13,740 / 1 | 24,859 | 19,331 | 11,119 |
| Codex router | 12,120 | 8,586 | 19,297 / 2 | 27,883 | 16,798 | 8,586 |
| Claude inline | 19,748 | 19,376 | 13,740 / 1 | 33,116 | 27,588 | 19,376 |
| Claude router | 19,748 | 16,843 | 19,297 / 2 | 36,140 | 25,055 | 16,843 |

Baseline website totals are 25,860 / 33,488; baseline status totals are
20,332 / 27,960 (Codex / Claude). Plain status retrieves 8,212 bytes in one call;
typo-only retrieves zero. The full rendered index costs **5,557 bytes and one read**.
Inline reduces every modeled installed-global total by 1,001 bytes for Codex and
372 for Claude. Router saves 3,534 / 2,905 on command-only paths, but increases each
ordinary topical total by **2,023 / 2,652 bytes**. Therefore router is rejected for
this integration. No aggregate average hides that regression.

## No-global comparison and limits

| Host / candidate | Repository initial | Website retrieval bytes / calls | Website total | Status total |
|---|---:|---:|---:|---:|
| Codex inline | 4,239 | 20,620 / 2 | 24,859 | 12,451 |
| Codex router | 4,239 | 23,644 / 3 | 27,883 | 12,451 |
| Claude inline | 1,253 | 31,863 / 2 | 33,116 | 9,465 |
| Claude router | 1,253 | 34,887 / 3 | 36,140 | 9,465 |

The no-global topical path reads the named master host template for its routing,
then the guide (plus the index for router). Commands require no template/index
lookup. Absolute master discovery is embedded in the repository fixture. If the
master is unavailable, report the missing guidance and do not substitute copied
consumer guides or silently claim successful routing.

Standalone initial bytes increase by **624 Codex / 1,253 Claude** against LE01's
3,615-byte AGENTS.md / absent CLAUDE.md. LE01 lacked the explicit standalone master
fallback; there is no defensible equivalent successful no-global baseline total,
so JSON totals/deltas for that baseline are null. This capability cost is an
explicit unresolved rollout tradeoff, not a byte-saving claim. E1 must assess the
fallback, template read side effects, real recall and incidental non-matches.
LE09 may improve the standalone path but must remeasure it and preserve discovery.

## Exact LE09 integration interface

1. Use LE03's single validated eligible-file enumeration for all output. Retain
   canonical filename exclusions, redirect exclusions, argument/marker validation,
   and pre-write failure semantics. Add `--format inline|detailed`; make inline the
   documented normal preview/write format and detailed the previous full-index
   preview. Reject unknown/duplicate formats before writes. `--base` still changes
   rendering only, never the source root. `--write` preserves bytes outside the
   existing DIRECTIONS-INDEX marker pair.
2. Generate inline rows from the same descriptions using three trigger terms,
   title fallback and full filenames, matching `routing/inline.md`; retain the
   shared safety, semantic matching, complete-command and ambiguity instructions.
   Do not maintain a separately hand-edited route list. No new production detailed
   index is required by the selected format; the rejected candidate's canonical
   detailed-index location would have been `<master>/DIRECTIONS-INDEX.md`.
3. Regenerate both global template managed bodies. Preserve other host-specific
   behavior and newer coordinator changes rather than copying entire frozen
   candidate templates over production. Add/reconcile standalone master discovery
   in repository AGENTS.md and CLAUDE.md, retaining local facts and all safeguards.
   Consumer generation/setup must produce a usable master path without globals;
   do not silently depend on this master's repository entry point being inherited.
4. Both deployers must render and validate the same inline output **before any
   installation write**. Pass the actual master base, require resolvable command
   and guide paths, and retain existing Codex marked-block personal-text
   preservation and Claude explicit backed-up whole-file replacement. Update
   the Codex skill's installed reference resolution consistently. No live install.
5. Extend disposable deployment fixtures for both hosts, missing globals, paths
   with spaces, contaminated master input, invalid markers, idempotence, and
   outside-path write checks. Re-run guidance/deployment fixtures and this static
   comparison. Candidate fixtures remain frozen experiment inputs; integrated
   production bytes need a separate final measurement in LE13, not substitution
   into these historical fixtures.

Actual validation: `--routing` passes 47-domain equality and 480 rows;
`--check-baseline` passes 85 unchanged hashes/byte counts. `git diff --check` is
run as a final whitespace check. All local writes are experiment artifacts and
the additive measure.py mode; no production template, deployer or Git state changed.
