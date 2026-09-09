"""Offline recovery preparation: synthetic workers and an isolated real OS lock.

No native artifacts, desktop input, permission queries or live runtime marker.
Synthetic worker termination tests supervisor policy, not macOS input quiescence.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import supervisor
import test_focus_supervisor as fixture


class FaultTransport(fixture.SyntheticTransport):
    def __init__(self, fault):
        super().__init__()
        self.fault = fault
        self.injected_ns = None
        self.commands = []

    def write(self, fd, data):
        peer = next((p for p in self.peers.values() if p.stdin.fileno() == fd), None)
        if peer is not None:
            row = json.loads(data)
            self.commands.append((self.ns, peer.name, row))
            if peer.name == "worker" and row["op"] == "event":
                if self.injected_ns is None:
                    self.injected_ns = self.ns
                    if self.fault == "crash":
                        peer.returncode = -9
                # No post or receipt: the pair is uncertain once admitted.
                return len(data)
            if (peer.name == "worker" and row["op"] == "stop"
                    and self.injected_ns is not None):
                return len(data)  # Hung worker cannot acknowledge cancellation.
        return super().write(fd, data)


class RecoverySupervisorTests(unittest.TestCase):
    def test_crash_and_hung_call_keep_uncertain_input_blocked(self):
        # The pipe fixture now exposes EOF on exit, so the read boundary detects
        # this injected crash before the loop's final owned-wait check.
        for fault, reason in (("crash", "workerEOF"), ("hung", "eventReceiptTimeout")):
            with self.subTest(fault=fault):
                rig = FaultTransport(fault)
                _, code, trace, marker = fixture.FocusSupervisorTests().run_transport(
                    rig=rig, focus_loss=False)
                self.assertEqual(code, 2)
                self.assertEqual(marker, b"unresolved")
                result = next(row for row in rig.outputs if row["event"] == "result")
                self.assertEqual(result["reason"], reason)
                self.assertEqual(result["result"], "inconclusiveOrFailed")
                self.assertFalse(result["drainVerified"])
                self.assertIsNone(result["drainMs"])
                self.assertEqual(result["admittedEvents"], 2)
                self.assertEqual(result["receivedEvents"], 0)
                events = [row for _, _, row in rig.commands if row["op"] == "event"]
                self.assertEqual(len(events), 1)  # No next event or automatic retry.
                stop = next(row for row in trace if row["event"] == "stopping")
                detection = int(stop["detectionNs"])
                self.assertLessEqual(detection - rig.injected_ns, 410_000_000)
                kills = [row for row in trace if row["event"] == "ownedWorkerKilled"]
                if fault == "hung":
                    self.assertTrue(rig.peers["worker"].killed)
                    self.assertEqual(len(kills), 1)
                    self.assertGreaterEqual(int(kills[0]["ns"]) - detection, 500_000_000)
                    self.assertLessEqual(int(kills[0]["ns"]) - detection, 510_000_000)
                else:
                    self.assertFalse(kills)
                self.assertFalse(rig.peers["target"].killed)
                self.assertTrue(all(peer.stdin.closed for peer in rig.peers.values()))
                self.assertTrue(all(peer.poll() is not None for peer in rig.peers.values()))


class RecoveryLockTests(unittest.TestCase):
    def test_bootstrap_artifacts_block_clean_or_empty_marker_without_modification(self):
        for name in ('bootstrap.pending', 'bootstrap.committed.json', 'bootstrap.committed.tmp'):
            for kind in ('file', 'directory', 'broken-link'):
                for marker_value in (b'clean', b''):
                    with self.subTest(name=name, kind=kind, marker=marker_value), \
                            tempfile.TemporaryDirectory() as directory:
                        root = Path(directory) / 'directions-stop-spike'
                        root.mkdir(mode=0o700)
                        marker = root / 'lock'
                        marker.write_bytes(marker_value)
                        marker.chmod(0o600)
                        artifact = root / name
                        if kind == 'file':
                            artifact.write_bytes(b'partial')
                        elif kind == 'directory':
                            artifact.mkdir()
                        else:
                            artifact.symlink_to(root / 'missing')
                        with patch.object(supervisor.os, 'confstr', return_value=directory):
                            with self.assertRaisesRegex(ValueError, 'bootstrap remains fenced'):
                                supervisor.experiment_lock()
                        self.assertEqual(marker.read_bytes(), marker_value)
                        self.assertTrue(artifact.exists() or artifact.is_symlink())
                        owner = supervisor.MarkerLock.acquire(root.resolve())
                        owner.close()  # Failure released ownership without clearing evidence.

    def test_new_run_marker_binds_identity_and_never_migrates_on_restart(self):
        with tempfile.TemporaryDirectory(prefix="run-marker-test-") as directory:
            with patch.object(supervisor.os, "confstr", return_value=directory):
                fd = supervisor.experiment_lock("a" * 32)
                fd.close()
                marker = Path(directory) / "directions-stop-spike" / "lock"
                expected = b"unresolved:" + b"a" * 32
                self.assertEqual(marker.read_bytes(), expected)
                with self.assertRaisesRegex(ValueError, "unresolved previous spike"):
                    supervisor.experiment_lock("b" * 32)
                self.assertEqual(marker.read_bytes(), expected)

    def test_process_death_releases_lock_but_does_not_authorize_retry(self):
        # Actual experiment_lock, flock and fsync in a private test namespace.
        # The child owns no worker; its death tests marker persistence only.
        source = """
import os, sys
from unittest.mock import patch
import supervisor
with patch.object(supervisor.os, 'confstr', return_value=sys.argv[1]):
    fd = supervisor.experiment_lock()
    print('locked', flush=True)
    sys.stdin.buffer.read(1)
    os._exit(17)  # Abrupt exit: no Python cleanup or marker reconciliation.
"""
        with tempfile.TemporaryDirectory(prefix="recovery-lock-test-") as directory:
            child = subprocess.Popen(
                [sys.executable, "-B", "-c", source, directory],
                cwd=Path(__file__).resolve().parent,
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            try:
                # communicate bounds the run; the child exits abruptly while the
                # kernel lock is still held and the marker remains unresolved.
                out, err = child.communicate(b"x", timeout=5)
                self.assertEqual(child.returncode, 17, err.decode())
                self.assertEqual(out, b"locked\n")
                marker = Path(directory) / "directions-stop-spike" / "lock"
                self.assertEqual(marker.read_bytes(), b"unresolved")
                with patch.object(supervisor.os, "confstr", return_value=directory):
                    with self.assertRaisesRegex(ValueError, "unresolved previous spike"):
                        supervisor.experiment_lock()
                self.assertEqual(marker.read_bytes(), b"unresolved")
            finally:
                if child.poll() is None:
                    child.kill()
                    child.communicate(timeout=5)

    def test_live_owner_blocks_second_acquisition_and_preserves_marker(self):
        with tempfile.TemporaryDirectory(prefix="recovery-lock-test-") as directory:
            with patch.object(supervisor.os, "confstr", return_value=directory):
                fd = supervisor.experiment_lock()
                try:
                    with self.assertRaises(ValueError):
                        supervisor.experiment_lock()
                    marker = Path(directory) / "directions-stop-spike" / "lock"
                    self.assertEqual(marker.read_bytes(), b"unresolved")
                finally:
                    fd.close()

    def test_unknown_marker_is_never_repaired(self):
        for value in (b"garbage", b"clean\n"):
            with self.subTest(value=value), tempfile.TemporaryDirectory() as directory:
                root = Path(directory) / "directions-stop-spike"
                root.mkdir(mode=0o700)
                lock = root / "lock"
                lock.write_bytes(value)
                lock.chmod(0o600)
                with patch.object(supervisor.os, "confstr", return_value=directory):
                    with self.assertRaisesRegex(ValueError, "unresolved previous spike"):
                        supervisor.experiment_lock()
                self.assertEqual(lock.read_bytes(), value)


if __name__ == "__main__":
    unittest.main()
