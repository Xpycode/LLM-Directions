"""Read-only snapshot checks in fresh namespaces; no native or global marker access."""
import fcntl
import os
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

import recovery_record as model
import recovery_snapshot as adapter
import recovery_storage as storage
from test_recovery_record import identity


class RecoverySnapshotTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="recovery-snapshot-test-")
        self.root = Path(self.temp.name).resolve()
        self.marker_root = self.root / "marker"
        self.runtime = self.root / "run"
        self.recovery = self.runtime / "recovery"
        for directory in (self.marker_root, self.runtime, self.recovery):
            directory.mkdir(mode=0o700)
        self.raw = model.encode(model.new_record(identity()))
        self.marker = b"unresolved:" + identity()["run"].encode("ascii")
        self.put(self.marker_root / "lock", self.marker)
        self.put(self.recovery / "record.lock", b"")
        self.put(self.recovery / "record.json", self.raw)

    def tearDown(self):
        self.temp.cleanup()

    @staticmethod
    def put(path, data):
        path.write_bytes(data)
        path.chmod(0o600)

    def snapshot(self):
        return adapter.locked_snapshot(self.marker_root, self.runtime)

    def blocked(self):
        with self.assertRaises(adapter.SnapshotError):
            with self.snapshot():
                self.fail("unsafe snapshot was yielded")

    def test_exact_bytes_both_locks_held_and_released_without_writes(self):
        paths = (self.marker_root / "lock", self.recovery / "record.lock",
                 self.recovery / "record.json")
        before = [(path.read_bytes(), adapter.fingerprint(path.stat())) for path in paths]
        with self.snapshot() as snapshot:
            self.assertEqual(snapshot.marker, self.marker)
            self.assertEqual(snapshot.record, self.raw)
            snapshot.recheck()
            for path in paths[:2]:
                fd = os.open(path, os.O_RDONLY)
                try:
                    with self.assertRaises(BlockingIOError):
                        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                finally:
                    os.close(fd)
        self.assertEqual(before, [(path.read_bytes(), adapter.fingerprint(path.stat()))
                                  for path in paths])
        with self.assertRaisesRegex(adapter.SnapshotError, "snapshotClosed"):
            snapshot.recheck()
        for path in paths[:2]:
            fd = os.open(path, os.O_RDONLY)
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            finally:
                os.close(fd)

    def test_either_lock_contention_fails_promptly(self):
        for path in (self.marker_root / "lock", self.recovery / "record.lock"):
            with self.subTest(path=path.name):
                fd = os.open(path, os.O_RDONLY)
                try:
                    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    started = time.monotonic()
                    self.blocked()
                    self.assertLess(time.monotonic() - started, 1)
                finally:
                    os.close(fd)
        with self.snapshot():
            pass

    def test_pending_and_unknown_entries_fail_without_repair(self):
        for name in ("pending.json", "unexpected", "record.json.extra"):
            path = self.recovery / name
            self.put(path, b"retain")
            self.blocked()
            self.assertEqual(path.read_bytes(), b"retain")
            path.unlink()

    def test_missing_files_are_never_created(self):
        for path in (self.marker_root / "lock", self.recovery / "record.lock",
                     self.recovery / "record.json"):
            data = path.read_bytes()
            path.unlink()
            self.blocked()
            self.assertFalse(path.exists())
            self.put(path, data)

    def test_legacy_clean_mismatched_and_oversized_marker(self):
        for data in (b"", b"clean", b"unresolved", b"unresolved:another-run", b"x" * 140):
            self.put(self.marker_root / "lock", data)
            self.blocked()
            self.assertEqual((self.marker_root / "lock").read_bytes(), data)

    def test_bad_and_oversized_record_or_nonempty_storage_lock(self):
        for data in (b"", b"{}", b"x" * (model.MAX_BYTES + 1)):
            self.put(self.recovery / "record.json", data)
            self.blocked()
        self.put(self.recovery / "record.json", self.raw)
        self.put(self.recovery / "record.lock", b"unexpected")
        self.blocked()

    def test_unsafe_permissions_and_owner(self):
        paths = (self.marker_root, self.runtime, self.recovery, self.marker_root / "lock",
                 self.recovery / "record.lock", self.recovery / "record.json")
        for path in paths:
            mode = path.stat().st_mode & 0o777
            path.chmod(0o755 if path.is_dir() else 0o644)
            self.blocked()
            path.chmod(mode)
        with patch.object(adapter.os, "geteuid", return_value=os.geteuid() + 1):
            self.blocked()

    def test_symlink_hardlink_and_fifo_files(self):
        for path in (self.marker_root / "lock", self.recovery / "record.lock",
                     self.recovery / "record.json"):
            data = path.read_bytes()
            outside = self.root / "outside"
            path.rename(outside)
            path.symlink_to(outside)
            self.blocked()
            path.unlink()
            os.link(outside, path)
            self.blocked()
            path.unlink()
            os.mkfifo(path, 0o600)
            self.blocked()
            path.unlink()
            path.mkdir(mode=0o600)
            self.blocked()
            path.rmdir()
            self.assertEqual(outside.read_bytes(), data)
            outside.rename(path)

    def test_noncanonical_and_symlink_directories(self):
        link = self.root / "alias"
        link.symlink_to(self.root, target_is_directory=True)
        for marker, runtime in ((Path("relative"), self.runtime),
                                (str(self.marker_root) + "/../marker", self.runtime),
                                (link / "marker", self.runtime),
                                (self.marker_root, link / "run")):
            with self.assertRaises(adapter.SnapshotError):
                with adapter.locked_snapshot(marker, runtime):
                    self.fail("unsafe path accepted")
        moved = self.runtime / "actual"
        self.recovery.rename(moved)
        self.recovery.symlink_to(moved, target_is_directory=True)
        self.blocked()

    def test_file_replacement_even_with_identical_bytes_is_rejected(self):
        for path in (self.marker_root / "lock", self.recovery / "record.lock",
                     self.recovery / "record.json"):
            replacement = self.root / "replacement"
            self.put(replacement, path.read_bytes())
            with self.assertRaisesRegex(adapter.SnapshotError, "snapshotChanged"):
                with self.snapshot():
                    os.replace(replacement, path)

    def test_content_mutation_rejected_at_explicit_recheck(self):
        with self.assertRaises(adapter.SnapshotError):
            with self.snapshot() as snapshot:
                self.put(self.recovery / "record.json", self.raw + b" ")
                snapshot.recheck()

    def test_marker_mutation_and_restoration_still_rejected(self):
        with self.assertRaises(adapter.SnapshotError):
            with self.snapshot():
                self.put(self.marker_root / "lock", b"clean")
                self.put(self.marker_root / "lock", self.marker)

    def test_namespace_rename_and_replacement_rejected(self):
        for path in (self.marker_root, self.runtime, self.recovery):
            moved = path.with_name(path.name + "-old")
            with self.assertRaises(adapter.SnapshotError):
                with self.snapshot():
                    path.rename(moved)
                    path.mkdir(mode=0o700)
            path.rmdir()
            moved.rename(path)

    def test_ancestor_namespace_replacement_rejected(self):
        moved = self.root.with_name(self.root.name + "-old")
        try:
            with self.assertRaises(adapter.SnapshotError):
                with self.snapshot():
                    self.root.rename(moved)
                    self.root.mkdir(mode=0o700)
        finally:
            if moved.exists():
                self.root.rmdir()
                moved.rename(self.root)

    def test_pending_appearing_during_context_rejected(self):
        with self.assertRaises(adapter.SnapshotError):
            with self.snapshot():
                self.put(self.recovery / "pending.json", b"retain")
        self.assertEqual((self.recovery / "pending.json").read_bytes(), b"retain")

    def test_pending_created_and_removed_during_context_rejected(self):
        with self.assertRaisesRegex(adapter.SnapshotError, "snapshotChanged"):
            with self.snapshot():
                self.put(self.recovery / "pending.json", b"retain")
                (self.recovery / "pending.json").unlink()

    def test_real_inflight_writer_lock_retained_after_close(self):
        (self.recovery / "record.lock").unlink()
        (self.recovery / "record.json").unlink()
        writer = storage.RecordWriter(self.recovery)
        entered, release = threading.Event(), threading.Event()
        original = storage.flush_file

        def stall(fd):
            entered.set()
            if not release.wait(3):
                raise OSError("fixture timeout")
            original(fd)

        try:
            with patch.object(storage, "flush_file", stall):
                writer.submit(self.raw)
                self.assertTrue(entered.wait(2))
                writer.close()
                self.assertFalse(writer.finished.is_set())
                started = time.monotonic()
                self.blocked()
                self.assertLess(time.monotonic() - started, 1)
                release.set()
                self.assertTrue(writer.finished.wait(2))
            with self.snapshot() as snapshot:
                self.assertEqual(snapshot.record, self.raw)
        finally:
            release.set()
            writer.close()
            self.assertTrue(writer.finished.wait(3))


class HeldMarkerLockTests(RecoverySnapshotTests):
    """Run the complete snapshot adversarial suite with retained ownership too."""

    def setUp(self):
        super().setUp()
        self.owner = adapter.MarkerLock.acquire(self.marker_root)

    def tearDown(self):
        self.owner.close()
        super().tearDown()

    def snapshot(self):
        return adapter.locked_snapshot(self.marker_root, self.runtime, held_lock=self.owner)

    def test_exact_bytes_both_locks_held_and_released_without_writes(self):
        # The marker remains owned after snapshot exit; only the writer lock ends.
        before = [(p.read_bytes(), adapter.fingerprint(p.stat())) for p in
                  (self.marker_root / "lock", self.recovery / "record.json")]
        original = adapter.fcntl.flock
        with patch.object(adapter.fcntl, "flock", wraps=original) as flock:
            with self.snapshot() as snapshot:
                self.assertEqual(snapshot.marker, self.marker)
                self.assertEqual(snapshot.record, self.raw)
            self.assertEqual(flock.call_count, 1)  # Storage only.
        self.assertEqual(before, [(p.read_bytes(), adapter.fingerprint(p.stat())) for p in
                                 (self.marker_root / "lock", self.recovery / "record.json")])
        with self.assertRaisesRegex(adapter.SnapshotError, "snapshotBusy"):
            adapter.MarkerLock.acquire(self.marker_root)
        self.owner.recheck()
        with self.assertRaisesRegex(adapter.SnapshotError, "snapshotClosed"):
            snapshot.recheck()
        self.owner.close()
        self.owner.close()
        owner = adapter.MarkerLock.acquire(self.marker_root)
        owner.close()

    def test_either_lock_contention_fails_promptly(self):
        with self.assertRaisesRegex(adapter.SnapshotError, "snapshotBusy"):
            adapter.MarkerLock.acquire(self.marker_root)
        fd = os.open(self.recovery / "record.lock", os.O_RDONLY)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            started = time.monotonic()
            self.blocked()
            self.assertLess(time.monotonic() - started, 1)
            self.owner.recheck()
        finally:
            os.close(fd)
        with self.snapshot():
            pass

    def test_missing_files_are_never_created(self):
        # A replaced marker invalidates ownership permanently; isolate each case.
        for path in (self.recovery / "record.lock", self.recovery / "record.json"):
            data = path.read_bytes()
            path.unlink()
            self.blocked()
            self.assertFalse(path.exists())
            self.put(path, data)
        (self.marker_root / "lock").unlink()
        self.blocked()
        self.assertFalse((self.marker_root / "lock").exists())

    def test_file_replacement_even_with_identical_bytes_is_rejected(self):
        for path in (self.recovery / "record.lock", self.recovery / "record.json",
                     self.marker_root / "lock"):
            replacement = self.root / "replacement"
            self.put(replacement, path.read_bytes())
            with self.assertRaises(adapter.SnapshotError):
                with self.snapshot():
                    os.replace(replacement, path)

    def test_owner_lifetime_checked_on_entry_and_exit(self):
        with self.assertRaisesRegex(adapter.SnapshotError, "markerLockClosed"):
            with self.snapshot():
                self.owner.close()
        self.blocked()

    def test_raw_descriptor_or_lookalike_is_not_ownership(self):
        for fake in (self.owner._fd, object()):
            with self.assertRaisesRegex(adapter.SnapshotError, "untrustedMarkerLock"):
                with adapter.locked_snapshot(self.marker_root, self.runtime, held_lock=fake):
                    self.fail("asserted ownership accepted")
        with self.assertRaises(TypeError):
            adapter.MarkerLock(self.owner._fd)

    def test_borrower_failure_never_releases_marker(self):
        with self.assertRaisesRegex(RuntimeError, "fixture"):
            with self.snapshot():
                raise RuntimeError("fixture")
        with self.assertRaisesRegex(adapter.SnapshotError, "snapshotBusy"):
            adapter.MarkerLock.acquire(self.marker_root)
        with self.snapshot():
            pass

    def test_wrong_directory_rejected(self):
        other = self.root / "other-marker"
        other.mkdir(mode=0o700)
        self.put(other / "lock", self.marker)
        with self.assertRaisesRegex(adapter.SnapshotError, "markerLockPathMismatch"):
            with adapter.locked_snapshot(other, self.runtime, held_lock=self.owner):
                self.fail("wrong marker path accepted")

    def test_closed_and_reused_private_descriptor_rejected_without_closing_reuse(self):
        fd = self.owner._fd
        os.close(fd)
        self.blocked()
        reused = os.open(self.recovery / "record.json", os.O_RDONLY)
        try:
            self.assertEqual(reused, fd)
            self.blocked()
            self.owner.close()
            self.assertEqual(os.pread(reused, len(self.raw), 0), self.raw)
        finally:
            os.close(reused)

    def test_owner_marker_io_and_creation(self):
        self.owner.write_marker(b"clean")
        self.assertEqual(self.owner.read_marker(64), b"clean")
        self.owner.write_marker(self.marker)
        with self.snapshot():
            pass
        self.owner.close()
        (self.marker_root / "lock").unlink()
        with self.assertRaises(OSError):
            adapter.MarkerLock.acquire(self.marker_root)
        self.owner = adapter.MarkerLock.acquire(self.marker_root, create=True)
        self.assertEqual((self.marker_root / "lock").stat().st_mode & 0o777, 0o600)
        self.owner.write_marker(self.marker)
        with self.snapshot():
            pass


if __name__ == "__main__":
    unittest.main()
