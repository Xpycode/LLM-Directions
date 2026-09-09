"""Admission controller tests with explicit fake acknowledgements and clocks."""
import unittest
from pathlib import Path
import tempfile
import threading
from types import SimpleNamespace
from unittest.mock import patch

import recovery_record as model
from recovery_admission import Admission, AdmissionError, RecoverySetup
from test_recovery_record import identity


class FakeWriter:
    def __init__(self):
        self.pending = None
        self.closed = False
        self.ready = True
        self.saved = []

    def submit(self, data):
        self.pending = data
        self.saved.append(model.parse(data))

    def poll(self):
        if self.pending is None or not self.ready:
            return None
        data, self.pending = self.pending, None
        return SimpleNamespace(data=data, error=None)

    def close(self):
        self.closed = True


class AdmissionTests(unittest.TestCase):
    def create(self):
        writer = FakeWriter()
        admission = Admission(writer, identity(), 0)
        admission.poll(1)
        return admission, writer

    def test_both_events_durable_before_down_and_up_cannot_replay(self):
        admission, writer = self.create()
        admission.reserve(1001, 2)
        self.assertFalse(admission.permits(1, 1001))
        self.assertEqual(writer.saved[-1]["events"], [
            dict(sequence=1, tag=1001, kind="down"), dict(sequence=2, tag=1002, kind="up")])
        admission.poll(3)
        self.assertTrue(admission.permits(1, 1001))
        admission.consume(1, 1001)
        self.assertFalse(admission.permits(1, 1001))
        self.assertFalse(admission.permits(2, 999))
        admission.consume(2, 1002)
        self.assertFalse(admission.permits(3, 1003))

    def test_checkpoint_must_be_durable_before_next_pair(self):
        admission, writer = self.create()
        admission.reserve(1001, 2)
        admission.poll(3)
        admission.consume(1, 1001)
        admission.consume(2, 1002)
        proof = SimpleNamespace(admitted={1001, 1002}, posted={1001, 1002},
                                received={1001: 1, 1002: 2}, verified_origin={1001, 1002},
                                received_kind={1001: "down", 1002: "up"},
                                posted_kind={1001: "down", 1002: "up"},
                                duplicate=False, valid_text={1001}, down_counts={1001: 1})
        admission.resolve(2, proof, 4)
        self.assertFalse(admission.resolved)
        admission.poll(5)
        self.assertTrue(admission.resolved)
        admission.reserve(1003, 6)
        self.assertEqual(writer.saved[-1]["state"], "uncertain")

    def test_stop_during_write_blocks_late_ack_and_cleanup_uncertainty_remains(self):
        admission, writer = self.create()
        admission.reserve(1001, 2)
        admission.stop()
        admission.poll(3)
        self.assertFalse(admission.permits(1, 1001))
        self.assertEqual(admission.record["sequence"], 2)
        self.assertEqual(admission.record["state"], "uncertain")
        self.assertTrue(writer.closed)

    def test_ack_at_deadline_is_rejected(self):
        admission, writer = self.create()
        admission.reserve(1001, 2)
        with self.assertRaisesRegex(AdmissionError, "recordWriteTimeout"):
            admission.poll(2 + admission.WRITE_NS)
        self.assertTrue(writer.closed)
        self.assertFalse(admission.permits(1, 1001))

    def test_failure_or_wrong_ack_stops_without_dispatch(self):
        for result in (SimpleNamespace(data=None, error="failure"),
                       SimpleNamespace(data=b"wrong", error=None)):
            admission, writer = self.create()
            admission.reserve(1001, 2)
            writer.poll = lambda: result
            with self.assertRaises(AdmissionError):
                admission.poll(3)
            self.assertFalse(admission.permits(1, 1001))
            self.assertTrue(writer.closed)


class SetupTests(unittest.TestCase):
    def test_cancel_during_writer_construction_waits_for_late_resource_release(self):
        entered, publish, released = threading.Event(), threading.Event(), threading.Event()
        closed = threading.Event()
        def writer(directory):
            entered.set()
            if not publish.wait(3):
                raise ValueError('fixture timeout')
            return SimpleNamespace(close=closed.set, finished=released)
        with tempfile.TemporaryDirectory() as directory, \
                patch('recovery_identity.capture_identity', return_value=identity()), \
                patch('recovery_admission.RecordWriter', side_effect=writer):
            setup = RecoverySetup(directory, 'run-1', {}, {},
                                  {'worker': 'a' * 64, 'target': 'b' * 64})
            try:
                self.assertTrue(entered.wait(2))
                setup.close()
                self.assertFalse(setup.wait_released(0.01))
                publish.set()
                self.assertTrue(setup.finished.wait(2))
                self.assertTrue(closed.is_set())
                self.assertFalse(setup.wait_released(0.01))
                released.set()
                self.assertTrue(setup.wait_released(0.1))
            finally:
                publish.set()
                released.set()
                setup.close()
                self.assertTrue(setup.finished.wait(2))

    def test_artifact_hash_changed_since_prelaunch_blocks_setup(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch("recovery_identity.capture_identity", return_value=identity()):
                setup = RecoverySetup(directory, "run-1", {}, {},
                                      {"worker": "c" * 64, "target": "b" * 64})
                try:
                    self.assertTrue(setup.finished.wait(2))
                    with self.assertRaisesRegex(AdmissionError, "recoveryIdentityUnavailable"):
                        setup.poll()
                    self.assertFalse((Path(directory) / "recovery").exists())
                finally:
                    setup.close()

    def test_stop_during_identity_setup_prevents_late_writer_creation(self):
        entered, release = threading.Event(), threading.Event()

        def capture(*args):
            entered.set()
            if not release.wait(3):
                raise ValueError("test timeout")
            return identity()

        with tempfile.TemporaryDirectory() as directory:
            with patch("recovery_identity.capture_identity", side_effect=capture):
                setup = RecoverySetup(directory, "run-1", {}, {},
                                      {"worker": "a" * 64, "target": "b" * 64})
                try:
                    self.assertTrue(entered.wait(2))
                    setup.close()
                    self.assertIsNone(setup.poll())
                    self.assertFalse(setup.finished.is_set())
                    self.assertFalse(setup.wait_released(0.01))
                finally:
                    release.set()
                    self.assertTrue(setup.finished.wait(2))
                    self.assertTrue(setup.wait_released(0.1))
                self.assertFalse((Path(directory) / "recovery").exists())


if __name__ == "__main__":
    unittest.main()
