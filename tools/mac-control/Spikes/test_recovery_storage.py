"""Real files/thread/lock in fresh temporary namespaces; no native harness or live marker."""
import fcntl
import os
from pathlib import Path
import tempfile
import threading
import time
import subprocess
import sys
import unittest
from unittest.mock import patch

import recovery_record as model
import recovery_storage as storage
from test_recovery_record import identity, event


class RecoveryStorageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="recovery-storage-test-")
        self.root = Path(self.temp.name)
        self.writer = storage.RecordWriter(self.root)

    def tearDown(self):
        self.writer.close()
        self.assertTrue(self.writer.finished.wait(3), "writer did not release its resources")
        self.temp.cleanup()

    def result(self):
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            result = self.writer.poll()
            if result is not None:
                return result
            time.sleep(0.001)
        self.fail("missing writer result")

    def bootstrap(self):
        prepared = model.new_record(identity())
        self.writer.submit(model.encode(prepared))
        self.assertIsNone(self.result().error)
        return prepared

    def test_flush_and_atomic_replace_precede_acknowledgement(self):
        prepared = self.bootstrap()
        next_record = model.admit(prepared, event(1))
        gate = model.WriteGate(prepared)
        raw = gate.stage(next_record)
        self.writer.submit(raw)
        result = self.result()
        self.assertIsNone(result.error)
        self.assertEqual(result.data, raw)
        self.assertEqual((self.root / "record.json").read_bytes(), raw)
        gate.acknowledge(result.data)
        self.assertTrue(gate.dispatch_ready)
        self.assertEqual((self.root / "record.json").stat().st_mode & 0o777, 0o600)
        self.assertFalse((self.root / "pending.json").exists())

    def test_stalled_flush_does_not_block_stop_or_release_lock_early(self):
        prepared = self.bootstrap()
        entered, release = threading.Event(), threading.Event()
        original = storage.flush_file

        def stall(fd):
            entered.set()
            if not release.wait(3):
                raise OSError("fixture timeout")
            original(fd)

        gate = model.WriteGate(prepared)
        raw = gate.stage(model.admit(prepared, event(1)))
        try:
            with patch.object(storage, "flush_file", stall):
                self.writer.submit(raw)
                self.assertTrue(entered.wait(2))
                # Stop is called while the real writer thread cannot finish I/O.
                self.assertIsNone(self.writer.poll())
                gate.stop()
                self.writer.close()
                self.assertFalse(release.is_set())
                self.assertFalse(self.writer.finished.is_set())
                self.assertFalse(gate.dispatch_ready)
                fd = os.open(self.root / "record.lock", os.O_RDWR)
                try:
                    with self.assertRaises(BlockingIOError):
                        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                finally:
                    os.close(fd)
                release.set()
                self.assertTrue(self.writer.finished.wait(2))
                self.assertIsNone(self.writer.poll())  # Cancelled completion cannot revive input.
                with self.assertRaises(ValueError):
                    gate.acknowledge(raw)
        finally:
            release.set()

    def test_failed_flush_retains_previous_record_and_never_dispatches(self):
        prepared = self.bootstrap()
        gate = model.WriteGate(prepared)
        raw = gate.stage(model.admit(prepared, event(1)))
        with patch.object(storage, "flush_file", side_effect=OSError("disk failure")):
            self.writer.submit(raw)
            result = self.result()
        self.assertIsNotNone(result.error)
        self.assertIsNone(result.data)
        gate.write_failed()
        self.assertFalse(gate.dispatch_ready)
        self.assertEqual(model.parse((self.root / "record.json").read_bytes()), prepared)
        with self.assertRaises(ValueError):
            self.writer.submit(raw)

    def test_failed_directory_flush_cannot_acknowledge_visible_new_record(self):
        prepared = self.bootstrap()
        raw = model.encode(model.admit(prepared, event(1)))
        with patch.object(storage, "flush_directory", side_effect=OSError("directory failure")):
            self.writer.submit(raw)
            result = self.result()
        self.assertIsNotNone(result.error)
        self.assertIsNone(result.data)
        self.assertEqual((self.root / "record.json").read_bytes(), raw)

    def test_short_writes_are_completed_and_zero_write_fails(self):
        prepared = self.bootstrap()
        raw = model.encode(model.admit(prepared, event(1)))
        original = os.write
        with patch.object(storage.os, "write", lambda fd, data: original(fd, data[:7])):
            self.writer.submit(raw)
            self.assertIsNone(self.result().error)
        next_raw = model.encode(model.admit(model.parse(raw), event(2)))
        with patch.object(storage.os, "write", return_value=0):
            self.writer.submit(next_raw)
            self.assertIsNotNone(self.result().error)

    def test_nonempty_namespace_and_symlink_are_rejected(self):
        self.bootstrap()
        with self.assertRaises(ValueError):
            storage.RecordWriter(self.root)
        with tempfile.TemporaryDirectory() as directory:
            link = Path(directory) / "link"
            link.symlink_to(self.root, target_is_directory=True)
            with self.assertRaises((OSError, ValueError)):
                storage.RecordWriter(link)
        self.writer.close()
        self.assertTrue(self.writer.finished.wait(2))
        with self.assertRaises(ValueError):
            storage.RecordWriter(self.root)  # Existing record is never bootstrap proof.

    def test_invalid_or_stale_revision_and_overlapping_request_close_writer(self):
        prepared = self.bootstrap()
        self.writer.submit(model.encode(model.admit(prepared, event(1))))
        with self.assertRaises(ValueError):
            self.writer.submit(model.encode(prepared))
        self.assertIsNone(self.writer.poll())

    def test_existing_pending_file_is_not_followed_or_overwritten(self):
        prepared = self.bootstrap()
        other = self.root / "other"
        other.write_text("preserve")
        (self.root / "pending.json").symlink_to(other)
        self.writer.submit(model.encode(model.admit(prepared, event(1))))
        self.assertIsNotNone(self.result().error)
        self.assertEqual(other.read_text(), "preserve")

    def test_changed_identity_rejected_after_completed_write(self):
        prepared = self.bootstrap()
        changed = model.admit(prepared, event(1))
        changed["identity"]["run"] = "other-run"
        with self.assertRaises(ValueError):
            self.writer.submit(model.encode(changed))
        self.assertEqual(model.parse((self.root / "record.json").read_bytes()), prepared)

    def test_replace_failure_retains_old_record(self):
        prepared = self.bootstrap()
        with patch.object(storage.os, "replace", side_effect=OSError("replace failure")):
            self.writer.submit(model.encode(model.admit(prepared, event(1))))
            self.assertIsNotNone(self.result().error)
        self.assertEqual(model.parse((self.root / "record.json").read_bytes()), prepared)
        self.assertFalse((self.root / "pending.json").exists())

    def test_stalled_directory_flush_withholds_ack_even_when_record_is_visible(self):
        prepared = self.bootstrap()
        raw = model.encode(model.admit(prepared, event(1)))
        entered, release = threading.Event(), threading.Event()
        original = storage.flush_directory

        def stall(fd):
            entered.set()
            if not release.wait(3):
                raise OSError("fixture timeout")
            original(fd)

        try:
            with patch.object(storage, "flush_directory", stall):
                self.writer.submit(raw)
                self.assertTrue(entered.wait(2))
                self.assertEqual((self.root / "record.json").read_bytes(), raw)
                self.assertIsNone(self.writer.poll())
                release.set()
                self.assertEqual(self.result().data, raw)
        finally:
            release.set()

    def test_abrupt_process_death_leaves_partial_attempt_blocked(self):
        # Actual writer process exits between writing and flushing the next record.
        # No native worker/input; process exit is the storage fault only.
        source = """
import os, sys, time
import recovery_record as model
import recovery_storage as storage
from test_recovery_record import identity, event
writer = storage.RecordWriter(sys.argv[1])
prepared = model.new_record(identity())
writer.submit(model.encode(prepared))
deadline = time.monotonic() + 3
while writer.poll() is None:
    if time.monotonic() > deadline: os._exit(19)
    time.sleep(0.001)
storage.flush_file = lambda fd: os._exit(17)
writer.submit(model.encode(model.admit(prepared, event(1))))
writer.finished.wait(3)
os._exit(20)
"""
        with tempfile.TemporaryDirectory(prefix="writer-crash-test-") as directory:
            child = subprocess.run([sys.executable, "-B", "-c", source, directory],
                                   cwd=Path(__file__).resolve().parent,
                                   capture_output=True, timeout=5)
            self.assertEqual(child.returncode, 17, child.stderr.decode())
            root = Path(directory)
            self.assertTrue((root / "pending.json").exists())
            self.assertEqual(model.parse((root / "record.json").read_bytes())["state"], "prepared")
            with self.assertRaises(ValueError):
                storage.RecordWriter(root)

    def test_unsafe_directory_permissions_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            os.chmod(directory, 0o755)
            with self.assertRaises(ValueError):
                storage.RecordWriter(directory)


if __name__ == "__main__":
    unittest.main()
