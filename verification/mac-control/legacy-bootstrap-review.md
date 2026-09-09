# Legacy marker bootstrap review

September 9, 2026 · independent read-only review and prospective preparation.

**Retain the unresolved marker.** The historical worker-crash report lacks a run-bound durable
ledger and post-state checkpoint. Its receipts and process exits cannot resolve that uncertainty
on the same login. This review grants no marker-write, reboot, native-launch or retry authority.
Task 1.3 and Gate A remain open.

## Contract boundary

[`Protocol.md`](../../tools/mac-control/Protocol.md) requires exclusive ownership, complete clean
executor inventory and proof that no old admitted event remains uncertain before bootstrap.
Missing same-login history requires verified new login/boot; freshness must have recorded OS
evidence. The current verifier deliberately requires a valid old run record even for its
`newBootCandidate` path. Legacy bootstrap is a separate procedure, not a parser exception.

The [historical review](worker-crash-reconciliation.md) and retained report remain unchanged.
Do not attach a newly observed boot or run identity to that old crash. A current boot UUID and
security-session identifier describe the present context, not freshness relative to the crash.
The prospective route below uses a subsequently verified **different boot**; it does not claim
that a changed security-session number proves a new login.

## Prospective baseline and transition

1. Establish a read-only baseline under the existing exclusive marker lock, without creating a
   missing namespace. Independently sample native boot/session and complete executor inventory
   before and after reading the marker. Require stable context, empty inventory, private namespace
   and descriptor identity, unchanged marker bytes/metadata, and retained ownership throughout.
   Record the marker class/hash and OS evidence, with explicit acquisition provenance. A report
   hash binds evidence bytes; it does not confer ownership or authenticate a later replay.
2. Preserve this baseline and the historical failure evidence. The baseline means only that the
   legacy uncertainty was present on the sampled boot. It is not same-boot reconciliation or a
   fabricated historical ledger. A separate native observation report must establish whether
   these baseline checks actually succeeded; this document itself records no native result.
3. After a separately agreed boot transition, independently verify a boot UUID different from
   that baseline. Under exclusive ownership, repeat complete native inventory and stable context
   checks, establish continuity of the marker namespace/state, and reject any unaccounted-for
   intervening launch, marker replacement or input admission. All cooperating launchers must honor
   the lock. This proof concerns conforming fixed-name executors, not hostile renamed processes.
4. Review the collected proof and an exact durable bootstrap transaction before requesting any
   live mutation. A new boot establishes that pre-transition processes/events cannot survive;
   empty current inventory and admission exclusion address the current boot. Neither result alone
   authorizes an automatic clean-marker write or a new experiment.

## Preparation required before any write

Define a dedicated bootstrap record and transaction rather than converting the legacy marker into
a fictional resolved run. Specify the trusted source and preservation of baseline provenance,
current OS evidence, exact lock/namespace checks, and how intervening state changes are detected.
Keep historical outcomes failed/unknown and non-retryable; never restore capabilities or replay input.

The transaction must retain exclusive ownership through final checks, evidence persistence and
durable clean initialization. Specify atomic replacement and flush ordering, crash recovery,
namespace validation and failure handling. Avoid replacing the inode that supplies the held lock;
the design must show how all launchers continue to share one exclusion domain. Any partial,
changed or unverified state must remain blocked. No executable clearing recipe is approved here.

Offline tests must cover same/unknown boot, untrusted or stale baseline, changed marker or namespace,
lock contention, missing/corrupt evidence, incomplete/unreadable inventory, live executor candidates,
context drift, intervening admission, failed durable writes and crashes at each transaction boundary.
A success fixture must preserve historical evidence and prove that clean initialization cannot
itself dispatch input. Native bootstrap validation remains separately required by Gate A.

The immediate next step is to retain the independently collected read-only baseline, then prepare
and review this separate bootstrap implementation and its tests. A foreground crash window alone
does not supply bootstrap proof or authorization to clear the historical marker.
