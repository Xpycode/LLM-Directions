# Kernel inventory contract review

September 10, 2026 · Wave 1 / task 1.3 · offline prototype only; recovery incomplete.

## Finding

The [fifth acquisition failure](inventory-contract-review.md#capture-outcome-and-handoff)
does not identify which process changed. Requiring the entire user's process list to
remain equal couples recovery to unrelated process churn. Replacing `proc_listpids`
with `KERN_PROC_UID` while retaining that equality would preserve the obstacle.

`KERN_PROC_UID` is not an atomic snapshot of process incarnations. It can support a
different, conditional claim: **no conforming executor capable of continuing execution
survives at observation completion, while launch exclusion remains held**. That is
not proof that no executor existed earlier, that old events drained, or that recovery
may proceed. Existing event, provenance, boot, marker and activation checks still apply.

## Source evidence

Apple's [process iterator](https://github.com/apple-oss-distributions/xnu/blob/main/bsd/kern/kern_proc.c#L3827-L3946)
rechecks allocation against the process count under the list lock, then collects PIDs.
It skips SIDL and shadow entries. Callbacks happen after unlocking; vanished processes
may be omitted and reused PIDs may refer to replacements. Lookup handles exec shadows
and has a zombie fallback. Allocation and transition waits are not time-bounded.

The [sysctl handler](https://github.com/apple-oss-distributions/xnu/blob/main/bsd/kern/kern_sysctl.c#L711-L889)
filters effective UID during callbacks and returns ENOMEM when output space is
insufficient. Successful output is not historical completeness: vanished callbacks
are not reported as missing. UID must also be checked in each returned record because
filtering and record filling are separate reads.

[Native exec naming](https://github.com/apple-oss-distributions/xnu/blob/main/bsd/kern/kern_exec.c#L894-L913)
derives the kernel command name from the final name component. The
[16-byte limit](https://github.com/apple-oss-distributions/xnu/blob/main/bsd/sys/param.h#L87-L92)
means `MacControlExecutor` appears as `MacControlExecut`; `StopSpikeWorker` fits.
These public sources support the design but do not verify the exact beta host build.

## Preconditions and proof

1. Every covered launcher must acquire the same exclusion before fork/spawn and keep
   it through exec/admission. Observation must not proceed until earlier holders
   release; contention may fail closed without waiting or retrying. This
   must cover the scanned effective UID across sessions; an omitted SIDL process must
   not later become a worker while the observer holds the lock.
2. A conforming worker keeps its effective UID, native executable identity and expected
   kernel command name. The last condition is **additional to path-based matching**.
   Aliases, case variations, interpreter wrappers, later renames and self-renaming are
   not silently covered. A name collision may block; it must never enable recovery.
3. The caller holds the relevant marker/storage locks throughout observation and its
   consuming transaction. Context freshness and boot/session checks remain required.

Assume a conforming executor still capable of execution at completion. Launch exclusion
means it already existed and was eligible when PIDs were collected. Continuous survival
precludes reuse of its PID; its fixed UID and name make the callback a candidate.
Therefore an accepted result with no candidates contradicts its survival. This is a
conditional inference, not a guarantee about arbitrary same-UID processes or queued events.

The current supervisor verifies canonical nonsymlink artifacts with the literal
`StopSpikeWorker` basename and acquires `experiment_lock` before `_run_owned` launches
children. The worker source contains no self-renaming, exec, fork or UID mutation.
That establishes the canonical current launch path's naming under the nonhostile
cooperation assumptions. Arbitrary aliases and future launchers are not silently covered.

## Shared-root counterexample

Apple's [Libc fallback](https://github.com/apple-oss-distributions/Libc/blob/main/gen/confstr.c#L211-L231)
uses writable `TMPDIR`, then `P_tmpdir`, if the directory helper fails for
`_CS_DARWIN_USER_TEMP_DIR`. Consequently, successful `os.confstr(65537)` does not
unconditionally identify one shared root. This is a source-level counterexample;
there is no evidence the current host actually took that fallback.

The coordinator reproduced its effect with the real `supervisor.experiment_lock`
and real private OS locks, mocking only `supervisor.os.confstr`: create two 0700
children of one `TemporaryDirectory`, return each in turn, acquire both owners before
releasing either, and recheck both markers as `unresolved`. Both acquisitions succeeded.
A third acquisition selecting the first directory failed while its owner remained held.
No child process or worker was launched and no live marker was accessed. The fixture
was removed after closing both owners. The executable heredoc ran via `python3 -B`
on macOS 27.0 (26A5425a), Python 3.14.7, and exited 0.

This demonstrates correct exclusion **within** one selected root, not exclusion
between independently selected roots. The capture caller already pins its expected
canonical runtime path; the general supervisor chooses a root independently.
Neither existing nor proposed inventory scans can enforce a missing shared namespace.

The next bounded prerequisite is a trusted shared-root selection contract for the
current launcher and capture caller, with a regression for divergent directory lookup.
It must retain the existing marker and reject disagreement before launch; silently
creating a new namespace or migrating the unresolved marker is not an acceptable fix.
This prerequisite blocks live replacement, not offline prototype validation.

## Prototype contract

The isolated `Spikes/recovery_inventory.c` prototype is compiled against the installed
SDK so it reads `struct kinfo_proc` through named fields, not guessed ctypes offsets.
It is not imported by `recovery_context.py` or installed in the native caller.

- Make one fixed-capacity `KERN_PROC_UID` query. No size-query/retry loop or fallback.
- Reject errors, full/oversized/partial output, malformed rows, duplicate/nonpositive
  PIDs, unexpected UID, invalid start tuples, and missing caller.
- Compare every returned kernel name against the SDK-truncated fixed worker names.
  A matching zombie or prefix collision also blocks; do not reread its path to dismiss it.
- Do not open unrelated process paths or require equality with another global PID set.
- Expose only fixed status codes. Zero means the prototype's validated rows contain no
  candidate; it is **not** a verifier context, an `inventory_complete` assertion or an
  authorization to restart. No process names, paths or complete inventory are emitted.

Any future integration must retain the existing external continuous-clock deadline,
output limits, context checks and bounded helper cleanup. A timeout rejects the result;
it cannot promise immediate termination of a helper stuck inside the kernel. Never
wait indefinitely during cleanup or let a late successful query authorize a transaction.

## Replacement gate

Before the live adapter can change, review evidence for the kernel-name invariant and
launch exclusion for the actual supported launch paths. Source inspection plus an
explicit supported-launch contract can establish these preconditions; this is not a
requirement to test every historical or hypothetical future implementation. The
shared-root counterexample above is currently unresolved. If either cannot be established,
reject the name-only replacement; do not map prototype success to the existing context
schema. Then review the integration, actual helper boundary and caller before any new
acquisition. A mocked query cannot close this gate.

All five failed transactions and both consumed observation journals remain preserved.
The runtime marker remains unresolved. No new acquisition, initialization, activation,
reboot or foreground window is included in this continuation. Task 1.3 / Gate A and
Wave 2 task 2.1 remain incomplete.

## Assignments and validation

Fresh-context Astra reviewed Apple's iterator and the conditional absence proof.
Fresh-context Sol owns the isolated C prototype and tests; the coordinator owns the
contract, consumer/launcher inspection, counterexample, records and Git. Astra's
independent contract and C source reviews found no blocker to the isolated prototype.

Validation on macOS 27.0 (26A5425a), arm64, Python 3.14.7, Apple clang 21.0.0:

```sh
python3 -B -m unittest tools/mac-control/Spikes/test_recovery_inventory.py -v
xcrun clang -std=c11 -Wall -Wextra -Werror -fsyntax-only tools/mac-control/Spikes/recovery_inventory.c
```

The focused suite ran **19 tests in 1.423 seconds, all passed**; production-source syntax
validation exited 0 without warnings. Tests compile the actual C implementation against
SDK structs and replace only the sysctl boundary. They check that the test dylib has no
native `_sysctl` reference. Coverage includes malformed rows after a candidate, duplicate
PIDs, truncation/collisions, matching zombies, unrelated inventory changes, full/partial
buffers, UID mismatch and caller omission. Builds are temporary and no native inventory
query is executed. Different supplied arrays do not simulate the kernel iterator itself;
its coverage argument remains conditional on the source proof and launch preconditions.

Existing recovery source and callers are unchanged, so their broader suite was not rerun.
Whitespace checks passed. The existing index checker still reports 45 missing entries
because it omits archived rows; a combined live/archive audit has no missing targets and
the same three already-recorded unindexed logs. No index repair or push was performed.

Outcome: bounded contract review and isolated prototype complete; **task 1.3 / Gate A
remain blocked/incomplete**. Next: shared-root selection contract and its divergence
regression, before integration. This checkpoint does not request another native attempt.
