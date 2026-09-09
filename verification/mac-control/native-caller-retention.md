# Native caller and independent witness retention

September 9, 2026 · isolated implementation and process-crash validation.

Continuation: [persistent provisioning and independent restart identity](persistent-witness-provisioning.md)
now implement the slot/anchor dependency below. Deployment-location validation remains pending.

`recovery_caller.activate_retained` now connects the existing activation transaction to the native
bounded context helper and continuous clock. It preflights two explicit independent witness slots,
persists the original post-publication transition through the activation callback, and persists the
returned completion acknowledgement before returning it to the caller. It retains marker ownership
and never launches an experiment. Failure propagates without implicit reconciliation or retry.

`recovery_retention` stores the exact acquired evidence bytes, digest, type and provenance in an
exclusive immutable slot. Supported types are baseline, completion seal, transition and activation.
History remains the original separately pinned byte sequence supplied to the activation API.
The caller must supply an independently authenticated directory identity, acquired before the slot
is populated. The slot is not an authority-discovery mechanism.

## Persistence and trust boundary

Each slot is an already provisioned canonical absolute directory, owned by this UID with mode 700.
Every path component is opened without following symlinks. The native caller requires separate
transition/acknowledgement slots outside the marker namespace; neither may contain the other.
The caller must also keep them outside the initializer's external seal directory. Retention does
not provision directories, choose defaults, repair files, overwrite a slot or delete evidence.

The writer exclusively creates `witness.tmp`, writes all bounded canonical bytes, flushes the file
with the existing native device-cache helper, and publishes `witness.json` by exclusive hard link.
Directory flush and exact byte, metadata, identity, path and two-link topology checks precede return.
Partial writes are completed; zero writes, failed flushes and changed evidence reject.

An explicit reload requires the previously authenticated slot identity, complete publication,
private regular files, exact topology, supported schema and matching payload pin/provenance. It
flushes the file and directory anew before returning evidence. This is a persistence operation,
not a read-only probe. It does not claim the interrupted retention call completed.

Publication ambiguity differs from activation completion: the witness payload was acquired
**before retention began**. A surviving published witness can therefore be retained anew without
inventing the original observation. A surviving activation receipt still cannot manufacture a
witness. A stored transition can only load as a transition; explicit `activation.reconcile` remains
necessary before admission. An acknowledgement retention failure leaves the independent transition
available, but neither automatically reconciles nor returns an acknowledgement.

The trust anchor is the caller-authenticated slot plus its original trusted writer, not a digest
read from arbitrary JSON. Authentication of that anchor must survive caller restart independently
of these files. Computing its identity from a discovered directory at reload is prohibited.
The model excludes hostile same-UID writers and deletion/inode-reuse attacks. Exact filesystem
checks do not turn this into a cryptographic provenance system.

## Concrete native handoff

The importable caller is ready for isolated review. There is deliberately no command that discovers
live authority or invokes bootstrap/activation. Before live use, prepare the following configuration:

1. Explicit canonical marker path from the independently acquired baseline, unchanged original
   baseline/history bytes and their acquisition pins/provenance. Preserve the historical failed
   outcome. Do not regenerate these pins from surviving reports.
2. A machine-local persistent private evidence parent outside temporary directories, Syncthing and
   the runtime/seal namespaces. Provision separate immutable slots for baseline, seal, transition,
   activation and each explicit reconciliation acknowledgement. Flush new directories and their
   parents; authenticate and independently retain each slot's path/device/inode before acquisition.
   **Provisioning and durable external trust-anchor retention remain to be implemented/reviewed.**
   The current tests provision fixture slots and keep their identity in the test owner; they do not
   establish that external native trust-anchor lifecycle.
3. Validate native file/directory flush results and metadata continuity in that persistent location,
   using disposable files only. The isolated tests exercise local flush calls, but establish neither
   power-loss persistence nor the behavior of the eventual persistent deployment location.
4. Obtain the separately agreed boot transition. Acquire the original marker with
   `MarkerLock.acquire(explicit_path, create=False)`. Missing/replaced temporary runtime state fails;
   do not recreate it or transplant the old baseline. Use `capture_bounded_context(clock=mac_clock())`
   for the fresh bounded native observations. Retain a read-only proof before live initialization.
5. Following the explicit live initialization/activation request, retain the seal returned by the
   original initializer in its authenticated witness slot. Pass the still-held owner and those
   exact baseline/seal/history values to `activate_retained`, with explicit `WitnessSlot` objects.
   Failure ends this action; inspect retained evidence before any separate reconciliation request.
6. A later foreground case requires its own agreed window, rebuilt native checkpoint binaries and
   fresh native observation dependencies in `ActivationRequest`. Pass it through the existing
   supervisor entry after releasing the original owner. Permanent consumption prevents replay.

No live marker was accessed, no native activation/initialization was invoked, and no Swift build,
boot transition, installation or desktop input occurred. Historical recovery remains unresolved;
task 1.3/Gate A and progress counts remain open.

## Verification

Twelve added behavioral tests cover exact retention, wrong trust/type, corrupt/unsafe/replaced
paths, duplicate attempts, partial and failed writes/flushes, final-boundary mutation, caller slot
preflight, acknowledgement-storage failure and five real subprocess-death boundaries. The caller
integration substitutes only native context/clock; activation, storage and actual one-shot launch
gating use their real implementations. The downstream native experiment is not launched.

The new test module initially failed because the retention implementation did not exist, then
passed after implementation. Final full suite: **330 tests, 329 passed, one existing sandbox
boot-query skip (38.735 seconds)**. Targeted suite: 12 passed (1.373 seconds). Whitespace and new
handoff-link checks passed. Changes remain uncommitted alongside preserved prior session work.

```bash
python3 -B -m unittest discover -s tools/mac-control/Spikes -p test_recovery_retention.py
python3 -B -m unittest discover -s tools/mac-control/Spikes -p 'test_*.py'
git diff --check
```
