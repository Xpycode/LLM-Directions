# A long local `xcodebuild test` run that "hangs" for hours is usually the Mac idle-sleeping — wrap it in `caffeinate -is` + per-test timeouts

**Tags:** caffeinate -is, xcodebuild test, idle sleep, waitUntilExit, -test-timeouts-enabled, -default-test-execution-time-allowance, SIGKILL, Process

**Source:** TimeCodeEditor — Wave 6.2 build/test run (2026-06-30). A `clean test` ran ~100 tests, then sat on a single test for **~2.5 hours** with no progress; root cause was the laptop idle-sleeping while unattended, not the code. Pairs with [[141-exiftool-geotag-end-to-end-test-no-fixtures]] and [[144-elicit-verification-verdicts-corrupt-output-and-couldnt-run]] (the real-`Process` integration tests this bites).

## The problem
You kick off `xcodebuild … test` (especially a suite with **integration tests that spawn real subprocesses** — ffmpeg/ffprobe/exiftool/git), step away, and come back to what looks like a dead hang: the same test "started" with no "passed", and the whole run frozen for far longer than any test should take.

Two facts conspire:

1. **The Mac idle-sleeps mid-run.** When the display/system sleeps, a spawned child process can be suspended or **SIGKILL'd**, but your test is parked in `Process.waitUntilExit()` (or a blocking read on the child's stdout/stderr pipe). The child is gone; the wait never returns. **Deadlock.**
2. **`xcodebuild` has no overall watchdog by default.** Nothing aborts the stuck test — it blocks *indefinitely* (observed: 2h22m and still "alive"), so you can't tell "slow" from "wedged forever."

The tell-tale signature (confirm before you blame the code):
```bash
ps -o etime= -p <xcodebuild-pid>          # elapsed wall time — wildly larger than the suite should take
pgrep -fl "ffmpeg|ffprobe"                # NO child process == its subprocess was killed (sleep)
# in the build log: the LAST "Test Case … started" has no matching "… passed"
grep -E "Test Case.*(started|passed)" build.log | tail -4
```
If the same test passes instantly on a re-run, it was **environmental (sleep), not a bug** — don't go hunting a phantom regression.

## The recipe

**1 — Prevent sleep for the whole run with `caffeinate`.** `-i` blocks *idle* sleep, `-s` blocks *system* sleep while on AC power; together they keep an unattended run alive:
```bash
caffeinate -is xcodebuild -project App.xcodeproj -scheme App \
  -destination 'platform=macOS' test
```

**2 — Add a per-test watchdog so a genuine hang fails fast instead of blocking for hours.** A stuck test aborts after the allowance and reports failure (you learn *which* test and move on):
```bash
caffeinate -is xcodebuild … test \
  -test-timeouts-enabled YES \
  -default-test-execution-time-allowance 120 \
  -maximum-test-execution-time-allowance 300
```
- `-test-timeouts-enabled YES` turns on the timeout machinery (off by default for the whole-suite case).
- `-default-test-execution-time-allowance <sec>` is the per-test budget; `-maximum-…` is the ceiling an individual test may request via `executionTimeAllowance`.

**3 — Reuse a warm build to re-run quickly.** After the kill, drop `clean` — the incremental `test` recompiles only what changed and re-runs the suite in a fraction of the time; great for confirming a suspected hang was just sleep.

**Why this is the right fix (not chasing the test):** the deadlock is in the *environment's* interaction with a real subprocess, not the test logic. `caffeinate -is` removes the trigger; the timeout flags turn "silent infinite hang" into "one failed test with a name." Make it your default wrapper for any local `xcodebuild test` that runs real external tools or that you'll leave unattended.
