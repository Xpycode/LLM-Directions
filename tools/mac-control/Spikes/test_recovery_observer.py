"""Actual OS pipes/processes, fixed Python peers only; no native control."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from recovery_observer import run


class ObserverTests(unittest.TestCase):
    def experiment(self, fault="supervisor-crash"):
        with tempfile.TemporaryDirectory(prefix="observer-test-") as directory:
            path = Path(directory) / "evidence.json"
            result = run(path, fault)
            self.assertEqual(json.loads(path.read_text()), result)
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            self.assertTrue(all(code is not None for code in result["exits"].values()))
            self.assertFalse(result["nativeDrainVerified"])
            self.assertFalse(result["restartEligible"])
            return result

    def test_supervisor_crash_preserves_recorder_and_worker_eof(self):
        result = self.experiment()
        self.assertEqual(result["result"], "passed", result)
        self.assertTrue(result["transportContained"])
        self.assertTrue(result["syntheticDrainComplete"])
        self.assertTrue(result["recorderSurvivedSupervisor"])
        self.assertEqual(result["forcedChildren"], [])
        trace = result["trace"]
        fence = next(r for r in trace if r["source"] == "observer")
        source_eof = next(r for r in trace if r["event"] == "sourceEOF")
        recorder_fence = next(r for r in trace if r["source"] == "recorder"
                              and r["event"] == "observationComplete")
        self.assertLessEqual(source_eof["receivedNs"], fence["ns"])
        self.assertLessEqual(fence["ns"], recorder_fence["ns"])

    def test_hung_worker_requires_owned_cleanup_and_cannot_pass(self):
        result = self.experiment("hung-worker")
        self.assertEqual(result["result"], "inconclusiveOrFailed")
        self.assertEqual(result["forcedChildren"], ["worker"])
        self.assertFalse(result["transportContained"])
        self.assertFalse(result["syntheticDrainComplete"])

    def test_retained_writer_is_detected_instead_of_hiding_eof_loss(self):
        result = self.experiment("retained-writer")
        self.assertEqual(result["result"], "inconclusiveOrFailed")
        self.assertIn("TimeoutError", result["error"])
        self.assertFalse(any(r["event"] == "commandEOF" for r in result["trace"]))

    def test_missing_recorder_fence_cannot_pass(self):
        result = self.experiment("missing-fence")
        self.assertEqual(result["result"], "inconclusiveOrFailed")
        self.assertTrue(result["transportContained"])
        self.assertFalse(result["syntheticDrainComplete"])

    def test_late_unadmitted_receipt_cannot_pass(self):
        result = self.experiment("late-receipt")
        self.assertEqual(result["result"], "inconclusiveOrFailed")
        self.assertTrue(result["transportContained"])
        self.assertFalse(result["syntheticDrainComplete"])

    def test_existing_evidence_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "evidence.json"
            path.write_text("preserve")
            with self.assertRaises(FileExistsError):
                run(path)
            self.assertEqual(path.read_text(), "preserve")

    def test_recorder_exit_failure_overrides_complete_fences(self):
        result = self.experiment("recorder-exit-failure")
        self.assertEqual(result["result"], "inconclusiveOrFailed")
        self.assertEqual(result["exits"]["recorder"], 7)
        self.assertTrue(any(r["source"] == "recorder" and r["event"] == "observationComplete"
                            for r in result["trace"]))

    def test_save_failure_raises_after_owned_children_are_reaped(self):
        launched = []
        real_popen = subprocess.Popen

        def launch(*args, **kwargs):
            child = real_popen(*args, **kwargs)
            launched.append(child)
            return child

        with tempfile.TemporaryDirectory() as directory:
            with patch("recovery_observer.subprocess.Popen", side_effect=launch), \
                    patch("recovery_observer.json.dump", side_effect=OSError("disk failure")):
                with self.assertRaisesRegex(OSError, "disk failure"):
                    run(Path(directory) / "evidence.json")
        self.assertEqual(len(launched), 3)
        self.assertTrue(all(child.poll() is not None for child in launched))


if __name__ == "__main__":
    unittest.main()
