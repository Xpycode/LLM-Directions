# Stop spike — first live case, task 1.3

**Date:** 2026-09-05 · **Status:** first mid-entry Stop case passed; task 1.3 and Gate A remain open.
**Environment:** M1 Max label, arm64, macOS 27.0 (26A5421a), Swift 6.3.3, Python 3.14.7.
Versions rechecked with `sw_vers`, `xcrun swiftc --version`, and `python3 --version`.

**Follow-up 2026-09-06:** [disconnect and heartbeat-loss experiments](loss-cases.md) passed their
input-drain checks. Detection instrumentation remains incomplete; task 1.3 and Gate A stay open.
The remainder of this report preserves the first case's historical results and approval boundary.

## Live result

The user explicitly approved compiling and running the disposable `stop-mid-entry` test. After
fixing the startup/text-target issues below, the actual Codex session ran the minimal client with
approved shell execution outside the sandbox. **Six correct characters, 12/12 matching event
receipts and source identities, input drain 11.716291 ms after client Stop.** No admission occurred
after Stop. The only later post was the reserved cleanup key-up; no post followed worker closure.
The five-second countdown measured 5,004.888416 ms. The target remained observable for about two
seconds after Stop, and both owned processes exited with code 0. The experiment marker is clean.

[Sanitized portable evidence](stop-mid-entry-2026-09-05.json) preserves event timing/counts,
sample-prefix results, artifact hashes and the original trace hash without text content.
Independent replay verified every matching post/receipt, prefix, cleanup boundary and process exit.
The 11.716291 ms figure measures final input receipt/admission closure; it is not worker-exit latency.

Exact final commands:

```bash
bash tools/mac-control/Spikes/build.sh
/var/folders/ly/b2sk443n0hq1_z9mgf4q8f4w0000gn/T/directions-stop-build.jYXWma/StopSpikeTarget.app/Contents/MacOS/StopSpikeTarget --self-check
python3 -B tools/mac-control/Spikes/client.py --artifacts /var/folders/ly/b2sk443n0hq1_z9mgf4q8f4w0000gn/T/directions-stop-build.jYXWma --case stop-mid-entry
```

- Fresh app: `/var/folders/ly/b2sk443n0hq1_z9mgf4q8f4w0000gn/T/directions-stop-build.jYXWma/StopSpikeTarget.app`.
  Launched by the supervisor; exact executable checked via the kernel path and POSIX `realpath`.
  It closed after observation; no test worker/app remains running from the successful run.
- Full machine-local trace: `/var/folders/ly/b2sk443n0hq1_z9mgf4q8f4w0000gn/T/directions-stop-spike-7eu0axxx/events.jsonl`.
- Worker 92323 and target 92324 were recorded at launch and confirmed exited by their owning
  supervisor's wait/reap. Their exit records match; this is stronger evidence than PID absence.

## Runtime findings and fixes

1. Swift compilation exposed ambiguous `greatestFiniteMagnitude`; made geometry types explicitly
   `CGFloat`. Both standalone files now compile with Swift 6 complete concurrency checks.
2. Python's `os.confstr` name table omits the Darwin temp-directory extension. Used the installed
   SDK's `_CS_DARWIN_USER_TEMP_DIR` numeric ABI value, 65537; the OS query resolves correctly.
3. All worker permission checks were false inside the shell sandbox and true outside it, measured
   by the same executable's nonprompting `--preflight` mode. The successful actual worker also
   reported all three true. No TCC settings changed. The in-memory target self-check also required
   outside-sandbox execution; its sandboxed attempt aborted before a window.
4. Directly spawned AppKit targets had no Launch Services launch date. Bind/recheck kernel process
   start time, UID, supervisor parent PID and exact executable instead. Foundation also normalizes
   `/private/var` to `/var`; a read-only Swift probe confirmed the mismatch with Python. Kernel
   `proc_pidpath` plus POSIX `realpath` now gives consistent equality. See Apple's
   [kernel process identity fields](https://github.com/apple/darwin-xnu/blob/main/bsd/kern/proc_info.c).
5. Initial activation/AX publication is asynchronous. Added a one-use two-second initial wait,
   with no input before exact focus verification; subsequent loss still stops without focus reclaim.
6. The first input attempt delivered all events and drained in 11.847209 ms, but inserted zero
   characters. The disposable view had no text system. Added retained text storage, layout manager
   and container, plus a passing in-memory `--self-check`. Apple's
   [designated initializer contract](https://developer.apple.com/documentation/appkit/nstextview/init%28frame%3Atextcontainer%3A%29)
   explains why the two-argument initializer needs these components.
7. Separated `drainVerified` from successful text insertion: wrong text still fails the experiment,
   while fully accounted-for input can leave a clean retry marker. No-input failures now report
   `drainMs:null`, not a misleading zero-millisecond result.

The failed text trace remains unchanged at `directions-stop-spike-0r41e84k/events.jsonl` under the
same temporary parent. Its conservative unresolved marker was reconciled under exclusive lock
only after independent replay proved all 12 events and both successful child exits, and marker
mtime/ctime showed no intervening run. `reconciliation.json` beside that trace records its hash,
marker identity and reason. This narrowly resolves a known text-target failure; it is **not** the
protocol's missing/corrupt-ledger or crash-recovery proof. The old test remains failed.

## Delivered

[Standalone source and runbook](../../tools/mac-control/Spikes/README.md): owned AppKit target,
AX-checked/CGEvent worker, Python supervisor and actual-session CLI driver, isolated build script,
and offline evidence/parser tests. The first recorded test is automatic Stop after six disposable
characters, with target event timestamps and a two-second post-stop observation interval.

No arbitrary target or shell operation is exposed. Source checks cover target/instance/focus,
one-event admission, paired key-up cleanup, both sides' heartbeat handling, nonblocking supervisor
transport, and a private lock against simultaneous spike runs. Only the case above has live evidence;
other branches remain unverified. A dirty marker refuses crash retries; full production recovery is
explicitly absent. The clipboard is unused; clipboard cleanup remains a separate unproven case.

## Checks actually run

| Exact command/check | Result | Limit |
|---|---|---|
| `python3 -B -m unittest discover -s tools/mac-control/Spikes -p test_supervisor.py -v` | 16 tests passed | Synthetic trace rows only |
| `bash tools/mac-control/Spikes/build.sh` | Passed after fixes | Local standalone artifacts; no production package |
| Fresh target executable `--self-check` outside sandbox | Passed | In-memory insertion; no window/input posting |
| Minimal client `--case stop-mid-entry` outside sandbox | Passed, exit 0 | One case; exact command/evidence above |
| `bash -n tools/mac-control/Spikes/build.sh` | Passed | Shell syntax only, no compilation |
| Python `ast.parse` on each `Spikes/*.py` | Parsed | Syntax only |
| Targeted `rg` and independent source/installed-SDK and trace review | Findings addressed | Narrow case, not full protocol acceptance |
| `git diff --check` | Passed at preparation handoff | Whitespace only |

Offline regressions require actual receipt/closure agreement and reject late, missing or duplicate
events, wrong/missing origin, no input, missing text insertion and target loss. The actual fixed
client sample is checked against the request-size boundary. Native input drain is measured only for
the recorded live case above.

## Independent review

- Removed fsync from active watchdog/Stop paths. A pre-launch dirty marker blocks crash retries;
  bounded in-memory traces are flushed after teardown. Supervisor output is nonblocking.
- Replaced the premature “Stopped” button label with “Stop requested”.
- Added sample-prefix/count checks after AppKit key handling; event arrival alone is insufficient.
- Retained the AppKit delegate across the run loop explicitly.
- Continued owned-event observation during cleanup after admission closes.
- Used target-reported worker PID/tag for PID-directed event origins. Installed CoreGraphics
  headers document process-specific routing; a global tap observation is not required for those
  synthetic events. Physical input discrimination still needs the separate live case.
- Reduced the fixed sample to 110 characters to fit the 128-character spike limit; added a
  regression using the actual client constant.
- Bounded client writes and total wait, and drain its output through EOF before evaluating results.

Independent runtime review checked the kernel identity/path fixes and the initial binding wait.
Final trace replay confirmed the six correct prefixes, all 12 event identities, cleanup-only posting
after Stop and matching successful child exits. Global tap-origin discrimination remains unverified.

## Approval boundary and remaining evidence

The saved [plan](../../IMPLEMENTATION_PLAN.md) requires an explicitly scheduled foreground test
window before compiling/running this spike. The user granted that window for this case. Native
artifacts were built, launched, tested and closed; no clipboard/permission changes, installation,
global deployment or commits occurred.

Task 1.3 stays unchecked, task 2.1 stays blocked, and Gate A stays closed pending disconnect,
physical intervention/focus loss, clipboard and startup/recovery evidence. Next: schedule the
prepared disconnect and heartbeat-loss cases; do not treat approval for this one case as a standing
window for other foreground experiments. Generic `measured` supports only its recorded case.

The user reiterated that multiple sessions must queue for the screen. This is already specified:
one ready FIFO, Yes per owner, Wait until explicit Review, and no handoff until verified drain.
The experimental run lock prevents overlapping spike runs; it is not the production queue.
