# Fenced legacy bootstrap implementation

September 9, 2026 · isolated offline preparation; historical runtime marker untouched.

This implements the [separate bootstrap contract](legacy-bootstrap-review.md), not a recovery
exception for the old crash trace. A prospective baseline must be explicitly trusted by an
independently retained digest and provenance. The initialization procedure requires a different
freshly observed boot, complete empty executor inventory and unchanged marker/namespace identity.
Current-run evidence and historical reports remain distinct.

## Transaction and launcher boundary

All work stays under the caller's existing `MarkerLock`. Initialization first preserves a durable
`bootstrap.pending` fence containing the evidence, then writes the clean marker through its existing
inode and records committed evidence. The fence is deliberately retained after success. Removing
the final fence would introduce another activation/crash transaction; that is outside this change.

The existing spike launcher rejects `bootstrap.pending`, `bootstrap.committed.tmp` and
`bootstrap.committed.json` before reading or changing the marker. Files, directories and dangling
symlinks all count as fences. A clean marker alone therefore cannot enable a run after interrupted
initialization. A successful offline initialization is `initializedFenced`, never launch permission,
native recovery proof or replay of a previous request.

The module has no runtime default, CLI, installer, process signalling or foreground action.
Live use of the prospective baseline requires its independently trusted provenance; calculating
a digest from an arbitrary report and passing that digest back does not authenticate the report.

`capture_baseline` records a prospective locked observation. `load_baseline` accepts those immutable
bytes or the already retained native-baseline report only against an explicit external pin.
Initialization revalidates that pin and schema on every call. Same boot, changed session alone,
unknown/zero boot UUID, stale samples, incomplete inventory, changed metadata, existing bootstrap
artifacts and missing/untrusted history all reject before marker mutation.

Pending and committed files retain original baseline/history bytes and their digests. New files
use exclusive creation; committed staging is atomically published by exclusive hard link, preserving
both names. Every file's identity, contents and metadata are rechecked before it counts as evidence.
The marker inode is never replaced. Any normal interrupted transaction retains unresolved state or
at least one startup fence; there is no automatic cleanup or retry path. This assumes cooperating
launchers and a trusted caller, not a hostile same-UID actor deleting evidence after a clean write.

## Verification

Full suite: **264 tests in29.321 seconds — 263 passed, one existing sandbox boot-query skip**.
Tracked-diff and new-file whitespace checks passed. Independent final review found no remaining
blocker within the documented trust boundary. No live baseline/marker access, reboot, native app
launch, build, commit, push or installation occurred in this continuation.

The tests use real private files, locks and flushes with synthetic boot/context observations.
They verify evidence preservation, same-inode initialization, held ownership, trust rejection,
context drift, intervening admission, namespace changes, stale durable preparation and write/flush
failures. Review found missing pending/staging identity checks; those were fixed and tested with
deletion, replacement and corruption at their preparation boundaries.

A separate Python subprocess exits abruptly at each of11 transaction boundaries, plus one normal
success case. Every resulting state is then offered to the actual `experiment_lock` entry point;
all remain blocked without marker modification. Startup tests additionally cover pending/staged/
committed artifacts as regular files, directories and dangling links with clean or empty markers.
These are process-death tests, not power-loss or native boot-transition verification.

```bash
python3 -B -m unittest discover -s tools/mac-control/Spikes -p 'test_*.py'
git diff --check
```

## Next boundary

The [activation contract and native handoff](legacy-activation-preparation.md) are now reviewed.
Its prerequisite v2 audit binds the post-clean marker fingerprint and rejects intervening rewrites;
the earlier verification above describes the v1 implementation. The
[completion seal/read-only preflight](legacy-completion-seal.md) and
[activation/one-shot admission](legacy-activation.md) are implemented offline. Next prepare the
native caller and independent pin retention before any live mutation or requested boot transition.
The current native baseline remains evidence
of the present boot, not a verified subsequent boot. Historical recovery remains unresolved;
task1.3/Gate A, native checkpoint compilation and the next foreground crash test remain open.
