# Read-only Darwin context and executor inventory probe

September 9, 2026 · offline preparation on arm64 macOS · Python 3.14.7.

`Spikes/recovery_context.py` provides `capture_context`, an explicit callable for the locked
recovery adapter. It does not install a runtime default or touch the historical marker.

The probe reads the current boot UUID and caller security session through the existing Darwin
identity adapter. It enumerates effective-UID processes with a bounded `proc_listpids` buffer;
errors, empty results, full buffers, partial PID bytes and invalid/duplicate PIDs reject. The
caller must appear. Two full process/path scans and three enumerations must agree, with context
and caller identity rechecked at the end. Unreadable processes, including non-candidates and
zombies, conservatively block instead of disappearing from the inventory.

Every `MacControlExecutor` or `StopSpikeWorker` basename across all build paths and UID sessions
produces a blocking candidate. Candidate PID/start data is diagnostic only: the verifier rejects
any candidate without needing a code hash. No name, path or saved PID grants signalling authority.
Unrelated process paths are not returned or persisted.

The installed SDK's `libproc.h` and `sys/proc_info.h` were checked. Apple's
[libproc declaration](https://github.com/apple-oss-distributions/xnu/blob/main/libsyscall/wrappers/libproc/libproc.h)
and [kernel enumeration implementation](https://github.com/apple-oss-distributions/xnu/blob/main/bsd/kern/proc_info.c)
support the byte-count ABI, effective-UID filter and conservative full-buffer rejection.

## Validation

Fifteen offline tests cover enumeration errors/truncation, candidates in old build paths,
unreadable processes/paths, changing PID sets, PID reuse, UID/parent/start/path drift, invalid
sessions, context/caller drift and malformed paths. A real private-directory integration enters
through `check_recovery` with the actual probe and mocked kernel calls. It checks an inert new-boot
candidate, blocks worker presence and enumeration failure, and confirms all file bytes unchanged.
The tests deliberately do not establish native enumeration visibility or boot freshness.

Independent review found no blocking issue within the documented contract and checked the SDK ABI.
Suggested inter-scan drift, malformed-path and caller-drift coverage was added and passed.
Final full suite: **186 tests in 26.376 seconds — 185 passed, one existing sandbox boot-query
skip**. All 15 context tests passed. `git diff --check` passed. No native scan/build/launch,
historical marker access, commit or push occurred; prior dirty edits remain preserved.

```bash
python3 -B -m unittest discover -s tools/mac-control/Spikes -p test_recovery_context.py
python3 -B -m unittest discover -s tools/mac-control/Spikes -p 'test_*.py'
git diff --check
```

## Limits and next work

Completeness applies to conforming fixed-name workers, under cooperating broker/storage locks.
It does not cover hostile same-UID code or renamed/exec-replaced workers. Finite samples cannot
exclude activity between samples; launchers must honor the lock. Existing path checks may reject
unrelated processes conservatively. Native inventory visibility has not been smoke-tested here.
OS calls can block, so use an external deadline outside active input/Stop handling. A current
security-session identifier alone does not prove a fresh login. Results never authorize restart.

Next: wire the independent native observer and durable-acknowledgement transport offline, preserving
owned parent identities and worker supervision, then prepare the separately agreed native validation
window. Historical marker remains unresolved and untouched; Swift checkpoint source remains
uncompiled. Task 1.3/Gate A, clipboard and broader intervention proof remain open.
