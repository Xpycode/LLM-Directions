# LE09 routing and deployment integration — October 16, 2026

The selected shortened inline map is the generator's default preview/write output.
`--format detailed` retains the previous full trigger table. Both formats use one
eligible-file loop; duplicate/unknown formats fail before destination writes.
The generated body matches the frozen LE07 `routing/inline.md` byte for byte.
Both global templates were regenerated without replacing their host-specific text.

Both deployers render the placeholder using literal Python replacement, regenerate
the same inline map with the absolute master base, validate markers and resolvable
guide/command paths, and only then mutate installation targets. This also validates
templates when the global-file install is skipped. Claude now preflights settings
JSON and merge expressions before command copying. Its whole-file global replacement
is explicit and backed up. Codex validates ordered outer markers and preserves
personal bytes outside its block, including CRLF and absent final newlines.
Neither preflight promises transactional rollback of every subsequent I/O failure.

The Codex skill and both repository entry points resolve `reference/...` from the
master root. Standalone commands go directly to complete canonical command files;
topical fallback reads only the relevant host template's routing section. The
coordinator updated consumer setup to write the resolved absolute master path and
the same fallback, rather than depending on this repository's entry point.
The independent fixture gives the consumer a conflicting same-name reference and
verifies the master-root path contract. This is deterministic path validation,
not observed host/model instruction-following; E1 remains open.

## Disposable validation

- `bash verification/lean/test-guidance-index.sh`: 50 generator invocations pass,
  including both formats, canonical eligibility, contamination preservation,
  arguments, marker/bootstrap failures, outside-body bytes/mode and idempotence.
- `bash verification/lean/test-deployment.sh`: 20 deployer invocations pass using
  copied masters and disposable homes, including actual Claude settings/hooks.
  Missing globals and dry runs, spaces, shared routes, contaminated input,
  missing commands, invalid template/outer markers, bad settings/templates,
  personal text, Claude replacement backups and stable output are covered.
  Failure cases assert the entire disposable home inventory remains unchanged;
  an outside consumer sentinel inventory is checked after each invocation.
- The same fixture compares the frozen old App-Websites checker with the current
  master on an archive-only session row: old exits 1, current exits 0, neither
  changes retained evidence. It verifies website routing to `24_web-gotchas.md`
  and preserves the website's `./check-invariants.sh` guidance, with no Swift
  build prescribed by its root entry point.
- Shell syntax checks and `python3 verification/lean/measure.py --routing` pass.
  Routing remains the frozen 47-domain / 60-case / 480-row comparison, not an
  integrated host benchmark. Final integrated measurement belongs to LE13.

Only disposable fixture installs were applied. A read-only Codex dry run also
validated the current live outer markers; no live installation or consumer edit
was performed. No app control, commits, fetches or pushes were performed.

## Consumer inventory and preservation-first recipe

`deployment/inventory.py` reads Magpie and App-Websites with optional Git locks
disabled, copies selected instructions/checkers into temporary snapshots, compares
those copies and records hashes, byte sizes, differing-line counts and dirty status
in `deployment/inventory.json`. Entry points and old checker scripts are retained
under `deployment/snapshots/`; numbered guides are represented by hashes rather
than introducing another persistent full guide mirror. Each source is rehashed
after copying. No consumer checker or build was executed in its live project.

| Consumer | Instructions/checkers inventoried | Exact master duplicates | Dirty/untracked status entries |
|---|---:|---:|---:|
| `/Users/sim/ProgrammingProjects/1-macOS/Magpie` | 42 | 5 | 36 |
| `/Users/sim/ProgrammingProjects/3-Websites/App-Websites` | 185 | 25 | 80 |

Magpie's root CLAUDE.md contains unique stack, project layout, signing/build and
workflow context. App-Websites' root and app-specific CLAUDE.md files contain
website invariants, project ownership and deployment context. Preserve them.
App-Websites' `docs/AGENTS.md` and nested Aloft/Penumbra copies retain placeholders
such as `[build command]` and generic `swift build`/`swiftlint`/`swift test` steps;
these are cleanup candidates, not suitable instructions for the website.
Three App-Websites `docs/scripts/sync-session-index.sh` copies have identical old
hash `98fca1b3b832576fb974d2b783b622c8953414c3e5567ed883f825d98dffec69`,
different from master hash `feb545ec43accb320f3d12895a5448f2410597dc886bcdc784a1062b1e5dcf2b`.
The frozen checker fixture makes that actual legacy-version difference reproducible.

For a separately authorized cleanup: recheck source hashes/dirty status first;
save all dirty and unique content; compare each differing guide contextually.
Consumer-only lines are potential additions or old universal text, not proof that
deletion is safe. Move verified project-specific additions to the appropriate
project entry point/decision before removing any mirror. Replace only verified
redundant guides with master discovery, retain missing/renamed-guide differences
for manual resolution, and replace placeholder nested instructions with real
website checks. Point session checking at the verified absolute master script
with an explicit consumer sessions directory. Re-run the fixture and actual
authorized project checks before deleting copies. No bulk cleanup is authorized.

## Initial-byte tradeoff

At this integration, rendered global templates are 6,880 Codex / 18,123 Claude
bytes; repository entry points are 4,173 / 1,483 bytes. Standalone repository
instructions therefore increase by 558 Codex / 1,483 Claude bytes against LE01.
Installed global-plus-repository totals are 11,053 Codex / 19,606 Claude bytes,
down 1,067 / 142 from LE01. LE13 found an initial 26-byte Claude regression;
trimming redundant repository prose resolved it without removing safeguards.
This preserves standalone discovery and safety; it is an unresolved rollout
tradeoff for E1, not a universal size reduction. LE13 must remeasure final files
after coordinator integration; frozen LE07 candidates were not altered.
