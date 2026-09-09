# Focus-loss startup attempt — 2026-09-09

**Result:** failed before input. Task 1.3/Gate A remain open. The user approved the prepared
two-minute window; one case ran, with no retry. Screen control ended and the final process scan
found no StopSpike executables. No text target was launched and zero events were admitted/received.

## Evidence

- macOS 27.0 (26A5425a), machine label M1-Max, Apple Swift 6.3.3, Python 3.14.7.
- Initial build passed: temporary artifact directory `directions-stop-build.SXEm0V`.
- Exact fresh worker's outside-sandbox nonprompting preflight: Accessibility, event posting and
  input monitoring all true. No old test processes found. Prior temporary runtime directory was
  absent; the harness created its private lock. This is not a production bootstrap proof.
- Ran `python3 -B tools/mac-control/Spikes/client.py --artifacts
  /var/folders/ly/b2sk443n0hq1_z9mgf4q8f4w0000gn/T/directions-stop-build.SXEm0V --case focus-loss`.
- Worker PID 66410 started and passed preflight. Focus sink PID 66411 crashed before `ready`.
  Supervisor stopped on `focusSinkEOF`; worker reported stopped/held-keys-empty and exited 0.
  Sink exited -5 (SIGTRAP). Client/supervisor returned 2; `casePassed:false`, no drain measurement.
- [Portable trace, client evidence and artifact hashes](focus-loss-startup-2026-09-09.json).
  Runtime trace directory: `directions-stop-spike-dt576jb4`; client: `directions-stop-client-h61uu9d7`.
- Crash report: `~/Library/Logs/DiagnosticReports/StopSpikeFocusSink-2026-09-09-123047.ips`.
  Its AppKit diagnostic states: "More than one NSApplication instance was created."
  Stack includes `NSApplication.init`, `sharedApplication` and `finishLaunching`.

## Fix and remaining work

The fixture incorrectly called `FocusSinkApplication()` directly. It now obtains
`FocusSinkApplication.shared` before delegate/run setup, with a checked subclass cast. This follows
the crash diagnostic's singleton-factory instruction. Recompilation passed into fresh temporary
directory `directions-stop-build.IdAV2D`. That corrected artifact has **not** been launched.
This is an intermediate test fixture; no app was relaunched outside the completed window.

The runtime marker remains **unresolved**, preserved after the sink's abnormal exit. No marker was
cleared and no TCC/install/deployment/commit changes occurred. Before another live case, review a
narrow reconciliation based on the retained no-input trace and owned-child exits; process absence
alone is not a recovery proof. Then agree a fresh window. Do not claim focus-loss compatibility
from compilation or this aborted run. Clipboard, recovery and other Gate A cases remain pending.
