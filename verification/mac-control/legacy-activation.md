# Activation and one-shot startup admission

September 9, 2026 · offline implementation and real-filesystem/process tests.
Host: arm64, macOS 27.0 (26A5425a), Python 3.14.7.

`recovery_activation.py` now implements activation, explicit interrupted-publication reconciliation
and permanent one-shot consumption. `supervisor.run` and its actual `experiment_lock` route accept
an explicit trusted activation request before entering the experiment body. No CLI discovers or
loads authority automatically. No native bootstrap, desktop input or live recovery test occurred.

## Transaction and evidence

Activation repeats the [completion-seal preflight](legacy-completion-seal.md) under the existing
marker lock. It exclusively creates and fully flushes `activation.intent`, flushes its directory,
then writes/flushed-stages `activation.receipt.tmp` and publishes `activation.receipt.json` as an
exclusive hard link. Exact original audit/marker continuity is retained. Snapshots check expected
names, private owned files, exact bytes/fingerprints and link topology between transitions.

Each intended creation changes directory metadata. APFS also changes directory link counts when
regular names are added, which the first tests exposed. The implementation holds directory
identity/mode/ownership fixed across its own creations, records resulting full fingerprints, and
requires exact full equality between those operations. It never compares an old directory size,
link count or timestamp against a namespace it intentionally changed.

After receipt publication, a trusted optional checkpoint sink can independently retain a
`TrustedTransition`: exact post-publication root/marker fingerprints, activation artifacts,
completion-seal hash, activation identity, observations and provenance. The checkpoint explicitly
does not attest completion. Activation flushes the published directory, refreshes context and
rechecks the full snapshot before returning a `TrustedActivation` acknowledgement. Its clean
marker and all historical outcomes remain unchanged; activation itself launches nothing.

The caller must independently retain acquired acknowledgement bytes, pin and provenance. This
module provides no native pin store or implicit report trust. A callback that saves nothing supplies
no recovery witness, even if complete-looking transaction files survive. Trusted in-process callers,
bounded native observation dependencies and conforming fixed-name executors remain assumptions.

## Explicit reconciliation after publication interruption

A pre-publication stamp cannot authenticate metadata produced by a later hard link. Therefore
`reconcile` requires the independently retained **post-publication** transition checkpoint from the
original owner. It cannot construct one from surviving intent/receipt files, accept a completion
receipt in its place or repair a partial transaction. Missing or changed evidence stays fenced.

With that witness, reconciliation validates exact current equality, the original initialization
seal/baseline/history and fresh same-boot/session empty inventory. It re-flushes the intent and
receipt inode and the directory, refreshes context again and returns a new acknowledgement.
This establishes durability anew; it does not claim the old process completed its flush.
Consumed transactions cannot reconcile because their namespace/marker no longer matches.

## Actual startup route and consumption

The optional `ActivationRequest` passed to `supervisor.run(..., activation=...)` reaches the real
`experiment_lock` before `_run_owned`. It carries independently pinned acknowledgement/seal/history
and explicit observation dependencies. This route acquires an existing namespace/marker with
`create=False`, validates the run ID and all evidence, and refreshes context before mutation.

It exclusively creates and fully flushes permanent `activation.consumed`, binding activation and
fresh run IDs, then flushes the directory. After rechecking files and context, it writes
`unresolved:<run ID>` through the existing marker inode and uses the full device-cache flush helper.
The post-write fingerprint is captured before any fault callback; final time and exact snapshot
checks precede returning the still-held owner. Exceptions release ownership but retain evidence.

The consumption name remains after success, failure, process death and later cleanup to `clean`.
Neither ordinary startup nor a repeated explicit request can consume that activation again.
Ordinary startup rejects every bootstrap/activation name, including orphaned files or dangling
symlinks. The existing CLI does not pass an activation request. Admission is not a foreground
grant: native artifact checks, the agreed test window and the experiment's input/ledger guards
remain required. A subsequent run needs its separate resolved-ledger path, not receipt replay.

## Verification

- Behavioral tests enter the actual launch gate for successful held-inode admission, invalid
  requests/run IDs, context/trust/schema failures, missing namespaces, corrupt/replaced files and
  replay after normal cleanup. Activation-only tests prohibit subprocess launch.
- Eighteen process-death boundaries cover activation publication/checkpoint/durability and
  consumption creation/write/flush/admission. An independently retained original checkpoint permits
  explicit post-crash reconciliation and exactly one admission; a receipt without that witness does not.
- Storage tests inject zero/short writes and actual file/directory flush failures. No incomplete
  operation returns admission ownership; fences and historical bytes survive.
- A supervisor-entry regression invokes real `run` and `experiment_lock`, substituting only native
  artifact/clock lookup and the downstream experiment body. It verifies consumption and unresolved
  marker persistence before that body, lock exclusion, and unreachable replay.

Review and tests fixed the APFS link-count assumption and a marker-write callback gap. Additional
checks bind acknowledged marker metadata to the original seal and reject a late final flush or
clock-boundary mutation. Independent final review found no remaining concrete blocker within the
offline trusted-caller scope. Final full suite: **318 tests in 40.092 seconds — 317 passed,
one existing sandbox boot-query skip**. Whitespace checks passed.

```bash
python3 -B -m unittest discover -s tools/mac-control/Spikes -p 'test_*.py'
git diff --check
```

These tests establish isolated process-crash behavior, not native power-loss persistence,
filesystem timestamp guarantees or input recovery. No live marker access or new native baseline
acquisition occurred; existing parser tests use retained repository evidence only.

## Next boundary

Prepare the concrete native caller and independently durable pin/checkpoint retention, including
private persistent directories and native flush/metadata checks. Keep prospective baseline/history
provenance intact. Complete that reviewable handoff before any boot-transition or live bootstrap
request. The historical runtime marker remains unresolved. Native checkpoint compilation and a
new foreground recovery case are separate; task 1.3/Gate A and progress counts remain open.
