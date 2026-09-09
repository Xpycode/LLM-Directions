# Legacy activation preparation

September 9, 2026 · design review and isolated regression tests. This records the original design;
[activation is now implemented offline](legacy-activation.md), with the checkpoint refinement below.

The next activation transaction must preserve initialization evidence and consume its authority
once. Removing bootstrap fences is not the transaction. The current launcher continues to reject
all initialization artifacts, including a successful initialization. No native marker was accessed.

## Review finding and prerequisite fix

The initializer previously checked only `clean` after its marker write. A test rewrote the marker
to an intervening unresolved run and back to `clean` at six later transaction boundaries; all six
were incorrectly accepted. This is a fault-injection test under the owned lock, not evidence that
a conforming concurrent launcher can acquire that lock.

`legacyBootstrap/v2` now captures the actual clean-marker fingerprint immediately after its durable
write, binds it in the committed audit as `initialized_marker_stamp`, and rechecks it before
publication work and at completion. Pending evidence precedes this observation, so it has no such
field. The only defined pending/committed differences are `result` and this committed-only field.
The regression also verifies those exact differences and the retained historical bytes.
It explicitly advances marker mtime to make the metadata change deterministic. Fingerprints detect
observable metadata changes, not arbitrary write history on every filesystem; native timestamp
resolution/continuity assumptions still require validation alongside trusted ownership.

This fingerprint closes the tested write-and-restore gap during initialization and supplies an
input for later continuity checks. It is **not** a transaction-completion seal: a committed name can
be visible before the final directory flush. Neither version of the audit alone enables activation.
Version 1 must never be upgraded by observing and stamping its current clean marker retrospectively.

## Completion seal and activation preflight contract

Before implementing activation, extend the initializer to produce an externally retained completion
seal under its original uninterrupted `MarkerLock`, after all publication/flush/recheck steps.
Bind a new transaction ID, exact pending and committed bytes/digests, baseline/history pins and
acquisition provenance, post-clean marker fingerprint, directory identity, final directory metadata,
artifact fingerprints/topology and initialization boot/session. Retain the seal outside the marker
directory so its own creation does not change the directory metadata it records. The trusted caller
must independently retain its digest and acquisition provenance; hashing an arbitrary loaded seal
does not authenticate it. Failure to retain the seal leaves initialization fenced.

A later read-only preflight must acquire the same existing namespace without creation and require:

- Externally authenticated seal, baseline and history; exact supported schemas/types, canonical
  bounded generated audit/seal bytes, no duplicate keys, missing fields or unrecognized transaction
  artifacts. Preserve baseline/history as their exact externally pinned original bytes; never
  require re-encoding historical evidence to the generated audit's canonical format.
- Marker bytes `clean` with the sealed fingerprint; same directory identity and final metadata.
  Reading may alter access time, which is excluded from the existing fingerprint. A changed marker
  restored to `clean` with a detectable fingerprint change, recreated namespace or unaccounted-for
  directory change rejects.
- Private regular files owned by this UID; pending has one link; committed staging and publication
  are exactly two names for one inode with two links. Evidence and marker inodes are distinct.
  Each named path, descriptor, byte sequence and fingerprint remains consistent throughout.
- Pending/committed match the exact v2 differences above and the completion seal. Missing, corrupt,
  mismatched, stale or v1 evidence never produces a candidate.
- Two independently acquired bounded native context samples, bracketed by the local continuous
  clock, matching the sealed initialization boot/session and differing from the old baseline boot.
  Complete empty executor inventories are required; unreadability is failure. Never compare
  continuous-clock timestamps across boots. Recheck files and ownership after observations.

Success returns only `activationCandidate`, with launch eligibility and native recovery verification
false. It is not a cacheable capability: any later mutation must repeat checks under retained ownership.
The trust model covers cooperating fixed-name executors and launchers, not hostile same-UID writers.

## Durable activation and launcher contract

The future transaction retains every initialization artifact. It exclusively creates an activation
intent binding a new activation ID, the completion seal and current observations; flushes the intent
and directory; then writes/flushed-stages an activation receipt and exclusively publishes it by hard
link. Recheck bytes, topology, ownership and marker continuity around each boundary. No overwrite,
fence deletion, repair, automatic retry or historical outcome change is permitted.
Each intended name/link creation changes directory metadata: verify the prior checkpoint immediately
before it and record the resulting expected namespace/topology afterward. The external completion
acknowledgement must bind final activation directory metadata. Later startup/reconciliation validates
these recorded allowed transitions and that final checkpoint, not equality with the pre-activation
directory fingerprint. Apply the same explicit transition accounting to consumption creation.

The writer's **durable commit point** is successful receipt-file flush followed by successful
directory flush of its published name, with all final checks passed under the original lock.
Publication alone is not this point. `write_marker` currently performs ordinary fsync; any future
admission needing the bootstrap device-cache guarantee must additionally use `flush_file`.

A receipt filename or self-described `completed` value cannot tell a new process whether the old
writer finished its directory flush. Therefore restarted activation is blocked by default. A
separate explicit reconciliation must validate and flush the complete transaction anew under the
lock, with fresh context and unchanged seal/marker evidence, before it can establish a new durable
completion acknowledgement. Partial or conflicting transactions remain blocked; do not implement
that reconciliation implicitly in the ordinary launcher. Implementation review refined this:
reconciliation requires an independently retained checkpoint acquired by the original writer
**after** final receipt publication. It binds the exact resulting directory metadata. Without that
checkpoint, surviving files cannot reconstruct missing continuity evidence.

The future launcher must use an independently retained completion acknowledgement, reacquire the
same lock, validate the full chain and fresh native context/inventory, and check the sealed marker
fingerprint. Before any process launch, exclusively create and durably flush a permanent consumption
record binding activation ID and a fresh run ID; flush the directory, then write and fully flush
`unresolved:<run ID>` through the existing marker inode. Keep ownership through admission.

The consumption record makes activation one-shot: later normal cleanup to `clean` cannot replay
the receipt. Death after consumption but before run creation is blocked and requires separately
reviewed reconciliation. Subsequent ordinary runs require their own resolved ledger/startup path;
they cannot use this bootstrap receipt. Activation neither restores a grant nor requests foreground
control. Existing historical outcomes remain failed/unknown and non-retryable.

## Required offline acceptance matrix

| Boundary or fault | Required result |
|---|---|
| Missing/corrupt audit or seal; wrong external pin; v1 audit | Block before mutation |
| Wrong type/mode/owner/link topology, extra name, inode replacement | Block and preserve evidence |
| Intervening run followed by clean restoration | Fingerprint mismatch; no candidate |
| Same baseline boot, changed initialization boot/session, stale clock | Block; no timestamp comparison across boots |
| Incomplete/unreadable inventory or live executor | Block before activation or admission |
| Partial write, failed file/directory flush, death before intent publication | Initialization fences retained |
| Death after receipt publication but before acknowledged durability | Ordinary startup blocks; explicit reconciliation required |
| Successful activation with no fresh foreground request | No app launch or input |
| Death at consumption creation/write/flush/directory flush/marker write | No second consumption or automatic retry |
| Successful run cleanup followed by receipt replay | Permanent consumption blocks replay |

Use private real files/locks and Python process death, entering the actual launcher for rejection
and eventual admission tests. Current tests cover initialization only. They do not establish this
future activation matrix, native boot behavior, or power-loss durability.

## Concrete native handoff

1. Finish and independently review completion-seal, activation and one-shot launcher integration;
   pass the matrix above before asking for a boot transition. Preserve the existing historical
   [baseline](native-context-2026-09-09.json), [native acquisition report](native-context-live.md)
   and worker-crash evidence with independently retained pins/provenance. Do not derive authority
   from a digest supplied inside those files.
2. Prepare the exact read-only probe invocation and explicit trusted runtime namespace on the same
   Mac. Verify all participating launchers use this lock/fence contract. Arrange a boot transition
   separately with the user; no reboot command or foreground window is authorized by this document.
3. After that transition, collect fresh native boot/session and complete inventory under the
   existing lock with `create=False`. If the OS removed its temporary namespace or changed the
   recorded identity/metadata, stop and retain the failure: do not recreate it or transplant the
   baseline into a different namespace. That requires a separate bootstrap design.
4. Retain the read-only proof for review before an explicit live initialization/activation request.
   Execute only the reviewed transaction after authorization; retain its completion evidence and
   independently verify native flush behavior. Any incomplete operation stays fenced.
5. Native checkpoint compilation and one new disposable foreground crash case require their own
   prepared window. Previous binaries predate the changed checkpoint transport. Bootstrap success
   does not pass worker/broker recovery, clipboard, broader intervention or task 1.3/Gate A.

## Validation and next step

The two new regression tests first failed against the old initializer (seven assertions across
schema and six rewrite boundaries), then passed after the v2 fingerprint fix. Targeted initialization
suite: 20 tests passed. Full suite: **266 tests in 29.506 seconds — 265 passed, one existing
sandbox boot-query skip**. These include the existing subprocess-death/actual-launcher rejection
tests, now exercising v2 initialization. No native build or live recovery run occurred.

Independent design review identified missing completion provenance, pre-flush receipt ambiguity and
one-shot receipt replay. This contract records those constraints; none is claimed implemented.
The [completion seal and read-only preflight](legacy-completion-seal.md) are now implemented in
isolated fixtures, followed by [activation/consumption and its process-death matrix](legacy-activation.md).
Next: native caller and independent pin retention preparation. No live
bootstrap has occurred, and the historical unresolved marker remains untouched.
