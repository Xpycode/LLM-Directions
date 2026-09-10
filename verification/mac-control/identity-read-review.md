# Native identity-read review

September 10, 2026 · Wave 1 / task 1.3 · Mac-control recovery remains incomplete.

## Finding and implementation

The [fourth failed capture](fresh-caller-review.md#authorized-native-outcome) discarded
the native return count and errno at `processIdentityFirstScanRead`. Its cause cannot
be recovered from the retained stage. The adapter's 136-byte structure layout matches
the installed Darwin SDK; no ABI mismatch or incorrectly accepted identity was found.

Apple's [libproc source](https://github.com/apple-oss-distributions/xnu/blob/main/libsyscall/wrappers/libproc/libproc.c)
converts a failed `__proc_info` return of -1 to zero while
preserving errno. The adapter now clears ctypes' thread-local errno immediately before
the single call and reads it immediately afterward. Only an exact full-size return
produces an identity row. Full-size reads ignore errno; every rejected return still fails.

Fixed kinds distinguish `Query` (call exception/invalid return type), `Missing` (zero
with ESRCH), `Denied` (zero with EPERM/EACCES), `NativeError` (zero with another nonzero
errno), `Zero` (zero without errno), and unexpected `Negative`, `Short`, or `Oversize`
returns. These are native observations, not an explanation of the historical failure.
No PID, path, raw error text or arbitrary errno value enters diagnostics.

`recovery_context.py` preserves these kinds at first-scan, second-scan and immediate
recheck boundaries. The existing helper schema and strict parent validation are unchanged;
historical generic stages remain accepted. All inventory, path, UID, incarnation,
equality and deadline checks remain; no exclusions or retries were introduced.

## One-shot observation caller

[identity-read-observation.py](identity-read-observation.py) uses the original fixed
local marker namespace with `MarkerLock.acquire(create=False)`. It exclusively creates
an append-only report before observation and saves a started record before the one
bounded helper call. Marker bytes and fingerprints must remain unchanged. Both authority
flags stay false. It does not capture/reload witnesses, repair the marker, initialize,
activate, launch an app, signal discovered processes, or send desktop input.

Independent review found that a cleanup exception could skip the final diagnostic append.
A regression reproduced that loss; the caller now records a fixed teardown failure while
preserving the native failure stage and forcing an unresolved result. Report reuse is
rejected. Interrupted writes remain incomplete evidence; process creation and filesystem
flush times are not bounded by the helper deadline.

## Validation and ownership

Sol owned `recovery_identity.py` and its tests in a fresh context. Coordinator owned
context integration, acquisition/context/probe regressions, observation caller/tests,
verification, records and Git. Coupled source work was serialized at the fixed exception
interface. Fresh-context Astra independently reviewed the final source and caller;
the teardown finding was fixed and the final review found no remaining blocker.

ABI checked against `/Library/Developer/CommandLineTools/SDKs/MacOSX.sdk/usr/include/sys/proc_info.h`
and the declarations in adjacent `libproc.h`; tests assert size and identity-field offsets.
Environment: M1 Max, macOS 27.0 (26A5425a), Python 3.14.7.

The acquisition regression was RED before integration: the refined native category was
reduced to `helperExit`. The cleanup regression was RED before its fix: the journal ended
at `started`. Focused integration ran 78 tests in 2.948 seconds, one existing native smoke
skip; the five final caller tests passed afterward. Tests use fake native calls and private
files; subprocess tests retain the actual adapter/helper/parent parser. Existing identity
smoke tests also query the current process/security session; one native boot query skips
in the sandbox. They do not access the runtime marker or send input. The new tests establish
diagnostic propagation and failure preservation, not native recovery.

Full suite: `python3 -B -m unittest discover -s tools/mac-control/Spikes -p 'test_*.py'`:
**398 tests in 46.367 seconds; 397 passed, one existing skip.** `git diff --check` passed.

## Native outcome

After final independent review, the execution continuation ran exactly once outside
the sandbox using approved tool access:

```bash
python3 -B -I verification/mac-control/identity-read-observation.py
```

The [three-record journal](identity-read-observation-2026-09-10.jsonl) retains prepared,
started and final unresolved records. The observation failed in **148.157750 ms** at
`processIdentityFirstScanReadMissing`: the native call returned zero with ESRCH.
The current read reported a missing process; this does not identify the process or
retroactively explain any previous capture. Marker bytes/fingerprints were unchanged,
both authority flags remained false, and no retry or acquisition followed.

This is evidence of a compatibility obstacle in the current all-process stability
contract, not an ABI problem. An enumerated process can become unavailable before its
identity is read. Ignoring it would remove a completeness check, and repeated attempts
would not measure reliability. Next review the inventory completeness contract against
this observation before preparing another capture; any proposed relaxation needs explicit
absence/identity-race proof and independent review. The consumed caller must not be rerun.

Independent follow-up review identified the precise question: what authoritative OS
evidence proves complete absence of conforming executors under the held broker lock when
an enumerated PID becomes unreadable, without assuming that PID was irrelevant? The
protocol requires complete inventory and verified possible executors; this adapter imposes
readability/stability on every UID process. A defensible revised proof, or concrete reason
the existing preconditions will now hold, is needed before another capture. No other live
Wave 1 case can start while the supervisor rejects the unresolved marker and activation
remains unverified. The selected execution therefore ends **blocked/incomplete**.

## Remaining boundary

Task 1.3 and Gate A stay open. Preserve all four failed acquisition transactions and
the historical unresolved marker. Wave 2 task 2.1 remains blocked. Recovery, clipboard
cleanup and remaining intervention acceptance still require live evidence and a separately
agreed foreground window. The separate lean-efficiency plan remains outside this run.
