# Conditional status procedures — October 17, 2026

Selected local maintenance scope: keep `commands/status.md` as the complete command entry and
extract arrival/collision detail into canonical master references. Ordinary status/full with no
known concurrency loads neither reference. Arrival loads both; known concurrency in any mode
loads collision detail. Mutation preflight still applies independently of status authorization.

The original arrival and collision section headings remain as routing stubs, preserving incoming
anchors. Master resolution follows the logging core convention: adapter resolution, managed
global master, or verified real repository source; never a consumer copy or guessed install path.
The entry retains full/context/arrival aliases, lean/full output contracts and execution reminders.
Extracted procedures retain identity before remote/fetch claims, failed-directory-change handling,
explicit pull authority and Rule 5, known-concurrency warnings, Claude-only detector boundaries,
Codex detection limitations, silence caveats, shared-worktree qualifications and unchanged startup
checks. This extraction does not change their policy.

## Source-byte accounting

Executed UTF-8 measurements against parent checkpoint `d493514`, whose status command SHA-256 is
`c430d7fe9d70b760641ab04d7b6c8b1a8ad371185bbb13a148afbfeeb54ba676`:

| Source / explicit load set | Bytes | Difference from old complete status command |
|---|---:|---:|
| Previous complete command | 10,149 | — |
| Current command core | 6,958 | -3,191 (31.4%) |
| Arrival reference alone | 2,849 | — |
| Collision reference alone | 2,251 | — |
| Core + collision | 9,209 | -940 |
| Core + arrival + collision | 12,058 | +1,909 |

These are static source/load-set subtotals, excluding adapters, project records, master-resolution
lookups and other conditional guides. They are neither observed host retrieval nor token, latency,
cost or runtime savings. Arrival's larger subtotal remains an unaccepted complex-path tradeoff.
Existing rendered global/repository entries are unchanged. Historical replay, frozen manifests,
attribution receipts and acceptance scores are unchanged. E1 stays open.

## Validation and ownership

One fresh-context implementer owned the coupled command, extracted references and fixtures;
the coordinator owns integration wiring, evidence, shared records and Git. The existing integration
guard now checks reachable shared references recursively, including links from extracted status
procedures. The aggregate local runner includes the new status fixture.

Commands run from the repository root:

```bash
python3 -B verification/lean/test-status-references.py
python3 -B verification/lean/test-integration.py
python3 -B verification/lean/measure.py --check-baseline
bash -n verification/lean/run-checks.sh
git diff --check
```

Five status tests pass: aliases/conditional-load cases, master/install/consumer-decoy fixtures,
core output contract, arrival identity/authority ordering, and collision host/worktree caveats.
The first disposable-path test exposed macOS `/var` versus `/private/var` identity; resolving its
temporary root fixed the fixture, and all five passed on rerun. The routing model rehearses the
documented contract and reads copied sources; it is not a production interpreter or proof that
an agent follows the instructions. Integration checks pass for 47 routes, recursively reachable
references, reviewed guide pins and the unchanged Mac-control plan; 85 frozen files match.
Shell syntax and whitespace checks pass. Unchanged deployment/generator suites were not rerun.

A fresh-context read-only reviewer compared the old command against the core and both references,
reviewed integration wiring and fixture limits, and independently reran the five status tests,
integration guard, shell syntax and scoped whitespace check. No findings. This is source-contract
review, not host acceptance or proof of runtime loading, detector behavior or installed resolution.
The scoped source/test/report checkpoint excludes overlapping prior state and acceptance work.
No host request, network test, desktop/app control, live deployment, consumer migration or push.

## Next local follow-up

Review the saved execution-read findings for a narrow way to reuse unchanged procedure/log
content while retaining required acceptance, changed-record verification and recovery checks.
This is a follow-up proposal, not an instruction to resume E1, the parked pilot/upstream work,
thirty deferred Claude observations or Mac-control recovery.
