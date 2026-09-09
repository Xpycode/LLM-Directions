"""Held-lock decisions with real isolated files, owned peers and synthetic OS context."""
import fcntl
import os
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from recovery_snapshot import MarkerLock
from supervisor import reconcile_after_teardown
import test_recovery_evidence as evidence_fixture


class ReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.fixture = evidence_fixture.RecoveryEvidenceTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.tearDown)
        self.fixture.start()
        self.fixture.finish()
        self.owner = MarkerLock.acquire(self.fixture.marker_dir)
        self.addCleanup(self.owner.close)
        self.setup = SimpleNamespace(close=lambda: None, wait_released=lambda timeout: True)

    def verdict(self, probe=None):
        import time
        with patch('supervisor.capture_bounded_context', lambda **_: (probe or self.fixture.probe)()), \
                patch('recovery_verifier.OBSERVATION_NS', 5_000_000):
            return reconcile_after_teardown(self.owner, self.fixture.run_dir, self.setup,
                                            self.fixture.observer, time.monotonic_ns)

    def assert_still_locked(self):
        fd = os.open(self.fixture.marker_dir / 'lock', os.O_RDONLY)
        try:
            with self.assertRaises(BlockingIOError):
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        finally:
            os.close(fd)
        self.assertEqual((self.fixture.marker_dir / 'lock').read_bytes(),
                         b'unresolved:' + b'a' * 32)

    def test_success_keeps_original_owner_and_never_grants_restart(self):
        def probe():
            self.assert_still_locked()
            return self.fixture.probe()
        verdict = self.verdict(probe)
        self.assertEqual(verdict.result, 'sameBootCandidate', verdict)
        self.assertFalse(verdict.restart_eligible)
        self.assert_still_locked()

    def test_pending_writer_release_prevents_probe(self):
        calls = []
        self.setup.wait_released = lambda timeout: calls.append(timeout) or False
        with patch('supervisor.capture_bounded_context') as probe:
            import time
            verdict = reconcile_after_teardown(self.owner, self.fixture.run_dir, self.setup,
                                                self.fixture.observer, time.monotonic_ns)
        self.assertEqual(verdict.reason, 'recoveryResourcesPending')
        self.assertEqual(calls, [2.0])
        probe.assert_not_called()
        self.assert_still_locked()

    def test_pending_storage_lock_fails_even_when_release_claims_complete(self):
        fd = os.open(self.fixture.run_dir / 'recovery/record.lock', os.O_RDONLY)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.assertEqual(self.verdict().result, 'blocked')
        finally:
            os.close(fd)
        self.assert_still_locked()

    def test_missing_observer_still_waits_for_pending_setup(self):
        import time
        calls = []
        self.setup.wait_released = lambda timeout: calls.append(timeout) or False
        verdict = reconcile_after_teardown(self.owner, self.fixture.run_dir, self.setup,
                                            None, time.monotonic_ns)
        self.assertEqual(verdict.reason, 'recoveryResourcesPending')
        self.assertEqual(calls, [2.0])
        self.assert_still_locked()

    def test_context_change_or_probe_failure_stays_blocked(self):
        for fault in ('session', 'inventory', 'error'):
            count = 0
            def probe():
                nonlocal count
                count += 1
                row = self.fixture.probe()
                if count == 2:
                    if fault == 'session':
                        row['session'] = 'different-session'
                    elif fault == 'inventory':
                        row['executors'] = [dict(pid=123)]
                    else:
                        raise ValueError('deadline')
                return row
            with self.subTest(fault=fault):
                self.assertEqual(self.verdict(probe).result, 'blocked')
                self.assert_still_locked()

    def test_changed_record_or_closed_owner_invalidates_decision(self):
        path = self.fixture.run_dir / 'recovery/record.json'
        original = path.read_bytes()
        def probe():
            path.write_bytes(original + b' ')
            return self.fixture.probe()
        self.assertEqual(self.verdict(probe).result, 'blocked')
        self.assert_still_locked()
        self.owner.close()
        self.assertEqual(self.verdict().result, 'blocked')


if __name__ == '__main__':
    unittest.main()
