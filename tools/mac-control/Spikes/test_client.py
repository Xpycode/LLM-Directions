"""Real-pipe client tests with a synthetic Python peer; never launches the native harness."""
import contextlib
import io
import json
from pathlib import Path
import selectors
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

import client


def stub_peer(mode):
    def emit(**fields):
        print(json.dumps(fields), flush=True)

    # Enter through the real client's request/heartbeat and fault-injection paths.
    assert json.loads(sys.stdin.readline())["op"] == "typeText"
    assert json.loads(sys.stdin.readline())["op"] == "heartbeat"
    if mode.startswith("crash-"):
        emit(event="recoveryTrace", row={"source": "supervisor", "event": "workerExited",
                                        "ns": str(time.monotonic_ns()), "exitCode": -9})
        emit(event="stopping", reason="workerExited")
        # A misleading generic success must never pass an intentional crash case.
        emit(event="result", reason="workerExited", result="measured", drainVerified=True)
        if mode != "crash-truncated":
            emit(event="recoveryTraceSaved", rows=2 if mode == "crash-mismatch" else 1)
        raise SystemExit(2)
    if mode.startswith("focus-"):
        emit(event="stopping", reason="wrongFocus")
        fields = {} if mode == "focus-missing" else {"focus": {"result": "measured"}}
        emit(event="result", reason="wrongFocus", result="measured", drainVerified=True, **fields)
        if mode in ("focus-focusSinkStillOpen", "focus-focusSinkExitFailed"):
            emit(event=mode.removeprefix("focus-"))
        return
    last_heartbeat = time.monotonic_ns()
    emit(event="trace", directory="synthetic-peer-no-native-trace")
    time.sleep(0.05) # Separate actual fault origin from last heartbeat.
    emit(event="receipt", count=11)
    if mode == "heartbeat":
        selector = selectors.DefaultSelector()
        selector.register(sys.stdin, selectors.EVENT_READ)
        # EOF or a continued heartbeat proves the client did not inject the intended fault.
        assert not selector.select(3 - (time.monotonic_ns() - last_heartbeat) / 1e9)
        selector.close()
        reason = "clientHeartbeatLost"
    else:
        assert sys.stdin.read() == "" # Disconnect must really close the inherited pipe.
        reason = "clientEOF"
    detected = time.monotonic_ns()
    stop = {"event": "stopping", "reason": reason, "detectionNs": str(detected),
            "lastClientLivenessNs": str(last_heartbeat)}
    if mode == "missing-timestamp":
        stop.pop("detectionNs")
    if mode == "wrong-reason":
        stop["reason"] = reason = "clientStop"
    if mode == "late":
        stop["detectionNs"] = str(detected + 4_000_000_000)
    emit(**stop)
    emit(event="result", reason=reason, result="measured", drainVerified=True)
    if mode in ("targetStillOpen", "targetExitFailed", "workerExitFailed"):
        emit(event=mode)
    if mode == "duplicate":
        emit(event="result", reason=reason, result="measured", drainVerified=True)
    if mode == "partial":
        print('{"unfinished":', end="", flush=True)


class ClientPipeTests(unittest.TestCase):
    def run_peer(self, mode, *, teardown_timeout=False, save_failure=False):
        original_popen = subprocess.Popen
        owned = []
        prior_signals = {s: signal.getsignal(s) for s in (signal.SIGINT, signal.SIGTERM)}

        def fake_launch(argv, **kwargs):
            self.assertEqual(Path(argv[1]).name, "supervisor.py")
            self.assertEqual("--focus-loss" in argv, mode.startswith("focus-"))
            self.assertEqual("--worker-crash" in argv, mode.startswith("crash-"))
            child = original_popen([sys.executable, "-B", __file__, "--stub", mode], **kwargs)
            owned.append(child)
            if teardown_timeout:
                actual_wait = child.wait

                def timeout_wait(*args, **kw):
                    actual_wait(timeout=2) # Reap the synthetic peer; simulate missing teardown proof.
                    raise subprocess.TimeoutExpired(child.args, 6)

                child.wait = timeout_wait
            return child

        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory) / "evidence"
            runtime.mkdir()
            if save_failure:
                (runtime / "client-evidence.json").mkdir()
            try:
                with patch.object(client.subprocess, "Popen", side_effect=fake_launch), \
                     patch.object(client.tempfile, "mkdtemp", return_value=str(runtime)), \
                     patch.object(client, "mac_clock", return_value=time.monotonic_ns), \
                     contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                    case = "worker-crash" if mode.startswith("crash-") else (
                        "focus-loss" if mode.startswith("focus-") else (
                            "heartbeat-loss" if mode == "heartbeat" else "disconnect"))
                    code = client.run_case("unused-native-artifacts", case)
                audit = None if save_failure else json.loads((runtime / "client-evidence.json").read_text())
                if audit is not None:
                    self.assertEqual((runtime / "client-evidence.json").stat().st_mode & 0o777, 0o600)
                return code, audit
            finally:
                for sig, previous in prior_signals.items():
                    signal.signal(sig, previous)
                for child in owned:
                    if child.poll() is None:
                        child.kill() # Only an owned synthetic Python fixture, never native apps.
                    subprocess.Popen.wait(child, timeout=2)
                    child.stdout.close()

    def test_disconnect_records_actual_close_and_passes(self):
        code, audit = self.run_peer("disconnect")
        self.assertEqual(code, 0)
        self.assertTrue(audit["casePassed"])
        self.assertEqual(audit["fault"]["case"], "disconnect")
        self.assertLessEqual(int(audit["fault"]["beforeNs"]), int(audit["fault"]["afterNs"]))
        self.assertEqual(audit["liveness"]["result"], "measured")
        self.assertEqual(audit["supervisorExitCode"], 0)

    def test_heartbeat_fault_keeps_pipe_open_and_withholds_heartbeats(self):
        code, audit = self.run_peer("heartbeat")
        self.assertEqual(code, 0)
        self.assertEqual(audit["fault"]["case"], "heartbeat-loss")
        self.assertGreaterEqual(audit["liveness"]["heartbeatAgeAtDetectionMs"], 3000)

    def test_supervisor_drain_success_cannot_hide_invalid_detection(self):
        for mode in ("missing-timestamp", "wrong-reason", "late"):
            with self.subTest(mode=mode):
                code, audit = self.run_peer(mode)
                self.assertEqual(code, 2)
                self.assertFalse(audit["casePassed"])
                self.assertEqual(audit["supervisorResult"]["result"], "measured")

    def test_duplicate_or_partial_output_fails(self):
        for mode in ("duplicate", "partial"):
            with self.subTest(mode=mode):
                code, audit = self.run_peer(mode)
                self.assertEqual(code, 2)
                self.assertTrue(audit["errors"])

    def test_teardown_timeout_overrides_measured_results(self):
        code, audit = self.run_peer("disconnect", teardown_timeout=True)
        self.assertEqual(code, 2)
        self.assertIn("supervisorTeardownTimeout", audit["errors"])
        self.assertFalse(audit["casePassed"])

    def test_child_teardown_failure_overrides_early_drain_success(self):
        for mode in ("targetStillOpen", "targetExitFailed", "workerExitFailed"):
            with self.subTest(mode=mode):
                code, audit = self.run_peer(mode)
                self.assertEqual(code, 2)
                self.assertIn(mode, audit["errors"])
                self.assertFalse(audit["casePassed"])

    def test_evidence_save_failure_prevents_success(self):
        code, _ = self.run_peer("disconnect", save_failure=True)
        self.assertEqual(code, 2)

    def test_focus_case_requires_specific_evidence_and_sink_teardown(self):
        for mode, expected in (("focus-valid", 0), ("focus-missing", 2),
                               ("focus-focusSinkStillOpen", 2), ("focus-focusSinkExitFailed", 2)):
            with self.subTest(mode=mode):
                code, audit = self.run_peer(mode)
                self.assertEqual(code, expected)
                self.assertEqual(audit["casePassed"], expected == 0)

    def test_worker_crash_retains_independent_rows_without_claiming_drain(self):
        for mode in ("crash-valid", "crash-truncated", "crash-mismatch"):
            with self.subTest(mode=mode):
                code, audit = self.run_peer(mode)
                self.assertEqual(code, 2)
                self.assertFalse(audit["casePassed"])
                self.assertFalse(audit["restartEligible"])
                self.assertEqual(len(audit["recoveryTrace"]), 1)
                self.assertEqual(audit["recoveryTraceComplete"], mode == "crash-valid")


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--stub":
        stub_peer(sys.argv[2])
    else:
        unittest.main()
