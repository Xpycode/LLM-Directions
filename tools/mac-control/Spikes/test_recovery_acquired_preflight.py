"""Retained-acquisition preflight tests with every native boundary substituted."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import recovery_acquire as acquire
import recovery_preflight as preflight
from recovery_snapshot import MarkerLock, fingerprint


class AcquiredPreflightTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.marker, self.evidence, self.anchor, self.archive = [
            self.root / name for name in ('marker', 'evidence', 'anchor', 'archive')]
        for path in (self.marker, self.evidence, self.anchor, self.archive):
            path.mkdir(mode=0o700)
        (self.marker / 'lock').write_bytes(b'unresolved')
        (self.marker / 'lock').chmod(0o600)
        self.history = self.root / 'history.json'
        self.history.write_bytes(b'failed historical fixture acquired prospectively\n')
        self.old_boot = '11111111-1111-1111-1111-111111111111'
        self.boot = self.old_boot
        self.now = 100
        acquisition = ['capture', '--marker-directory', str(self.marker),
            '--evidence-directory', str(self.evidence), '--anchor-directory', str(self.anchor),
            '--archive-directory', str(self.archive), '--history-source', str(self.history),
            '--operator-record', 'private fixture retained acquisition']
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(acquire.main(acquisition, observe=self.observe,
                                         clock=lambda: self.now), 0)
        self.boot = '22222222-2222-2222-2222-222222222222'
        self.now = 200
        self.library = (str(self.root / 'inventory.dylib'), 'a' * 64)
        self.args = ['inspect-acquired', '--marker-directory', str(self.marker),
            '--evidence-directory', str(self.evidence), '--anchor-directory', str(self.anchor),
            '--archive-directory', str(self.archive), '--inventory-library', self.library[0],
            '--inventory-sha256', self.library[1]]

    def observe(self):
        return dict(boot=self.boot, session='fixture', checked_ns=self.now,
                    inventory_complete=True, executors=[])

    def invoke_native(self, args=None, *, root_guard=None, clock=None):
        calls = []
        continuous_clock = clock or (lambda: self.now)

        def bounded(**kwargs):
            calls.append(kwargs)
            return self.observe()

        output = io.StringIO()
        guard = root_guard or (lambda expected: self.marker)
        with patch.object(preflight, 'trusted_runtime_root', side_effect=guard) as trusted, \
             patch('supervisor.mac_clock', return_value=continuous_clock) as mac_clock, \
             patch.object(preflight, 'capture_bounded_context', side_effect=bounded), \
             contextlib.redirect_stdout(output):
            code = preflight.main(self.args if args is None else args)
        return code, json.loads(output.getvalue()), calls, trusted, mac_clock, continuous_clock

    def marker_snapshot(self):
        return (fingerprint(self.marker.stat()), fingerprint((self.marker / 'lock').stat()),
                (self.marker / 'lock').read_bytes(),
                sorted(path.name for path in self.marker.iterdir()))

    def test_later_boot_uses_explicit_pin_for_both_read_only_observations(self):
        before = self.marker_snapshot()
        code, report, calls, trusted, mac_clock, continuous_clock = self.invoke_native()
        self.assertEqual(code, 0, report)
        self.assertEqual(report['result'], 'acquiredPreflightObserved')
        self.assertEqual(report['inventory_sha256'], self.library[1])
        self.assertEqual(report['history_sha256'], report['acquisition']['history_sha256'])
        self.assertFalse(report['launch_eligible'])
        self.assertFalse(report['native_recovery_verified'])
        self.assertTrue(report['marker_unchanged'])
        self.assertEqual(before, self.marker_snapshot())
        trusted.assert_called_once_with(str(self.marker))
        mac_clock.assert_called_once_with()
        self.assertEqual(calls, [dict(clock=continuous_clock, inventory_library=self.library)] * 2)

    def test_same_boot_and_marker_namespace_mutation_reject(self):
        self.boot = self.old_boot
        self.assertEqual(self.invoke_native()[1]['reason'], 'sameBoot')
        self.boot = '22222222-2222-2222-2222-222222222222'
        (self.marker / 'extra').touch()
        code, report, calls, _, _, _ = self.invoke_native()
        self.assertEqual(code, 1)
        self.assertEqual(report['reason'], 'baselineContinuityLost')
        self.assertEqual(calls, [])

    def test_corrupt_archive_rejects_before_marker_acquisition(self):
        (self.archive / 'history.json').write_bytes(b'corrupt')
        with patch.object(preflight.MarkerLock, 'acquire', side_effect=AssertionError('marker opened')):
            code, report, calls, _, _, _ = self.invoke_native()
        self.assertEqual(code, 1)
        self.assertEqual(calls, [])
        self.assertEqual(report['result'], 'unresolved')

    def test_corrupt_anchor_rejects_before_marker_acquisition(self):
        (self.anchor / 'anchor.json').write_bytes(b'corrupt')
        with patch.object(preflight.MarkerLock, 'acquire', side_effect=AssertionError('marker opened')):
            code, report, calls, _, _, _ = self.invoke_native()
        self.assertEqual(code, 1)
        self.assertEqual(calls, [])
        self.assertEqual(report['result'], 'unresolved')

    def test_overlap_rejects_before_retained_reload(self):
        args = list(self.args)
        args[args.index('--archive-directory') + 1] = str(self.marker)
        with patch.object(preflight.acquire, 'load_acquired',
                          side_effect=AssertionError('retained evidence loaded')):
            code, report, calls, _, _, _ = self.invoke_native(args)
        self.assertEqual(code, 1)
        self.assertEqual(report['reason'], 'anchorNamespacesNotSeparate')
        self.assertEqual(calls, [])

    def test_library_flags_are_required_and_invalid_before_marker_access(self):
        for missing in ('--inventory-library', '--inventory-sha256'):
            args = list(self.args)
            index = args.index(missing)
            del args[index:index + 2]
            with self.subTest(missing=missing), \
                 patch.object(preflight.MarkerLock, 'acquire', side_effect=AssertionError('opened')), \
                 patch.object(preflight, 'trusted_runtime_root', side_effect=AssertionError('root')), \
                 contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as raised:
                preflight.main(args)
            self.assertEqual(raised.exception.code, 2)
        args = list(self.args)
        args[args.index('--inventory-sha256') + 1] = 'A' * 64
        with patch.object(preflight.MarkerLock, 'acquire', side_effect=AssertionError('opened')), \
             patch.object(preflight, 'trusted_runtime_root', side_effect=AssertionError('root')), \
             patch.object(preflight.acquire, 'load_acquired', side_effect=AssertionError('loaded')), \
             contextlib.redirect_stdout(io.StringIO()) as output:
            code = preflight.main(args)
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(output.getvalue())['reason'], 'invalidInventoryConfiguration')

    def test_injected_observer_is_ambiguous_and_never_reloads_or_observes(self):
        output = io.StringIO()
        observer = unittest.mock.Mock(return_value=self.observe())
        with patch.object(preflight, 'trusted_runtime_root') as trusted, \
             patch.object(preflight.acquire, 'load_acquired') as load, \
             contextlib.redirect_stdout(output):
            code = preflight.main(self.args, observe=observer, clock=lambda: self.now)
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(output.getvalue())['reason'], 'ambiguousInventoryObserver')
        trusted.assert_not_called()
        load.assert_not_called()
        observer.assert_not_called()

    def test_native_root_is_enforced_even_with_injected_clock(self):
        output = io.StringIO()
        with patch.object(preflight, 'trusted_runtime_root',
                          side_effect=ValueError('runtimeRootMismatch')) as trusted, \
             patch.object(preflight.acquire, 'load_acquired') as load, \
             patch.object(preflight, 'capture_bounded_context') as observer, \
             contextlib.redirect_stdout(output):
            code = preflight.main(self.args, clock=lambda: self.now)
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(output.getvalue())['reason'], 'runtimeRootMismatch')
        trusted.assert_called_once_with(str(self.marker))
        load.assert_not_called()
        observer.assert_not_called()

    def test_missing_marker_rejects(self):
        self.marker.rename(self.root / 'missing-marker')
        self.assertEqual(self.invoke_native()[0], 1)

    def test_changed_marker_rejects(self):
        (self.marker / 'lock').write_bytes(b'unresolved changed')
        self.assertEqual(self.invoke_native()[0], 1)

    def test_clean_marker_rejects(self):
        (self.marker / 'lock').write_bytes(b'clean')
        self.assertEqual(self.invoke_native()[0], 1)

    def test_busy_marker_rejects_without_observation(self):
        owner = MarkerLock.acquire(self.marker, create=False)
        try:
            code, report, calls, _, _, _ = self.invoke_native()
        finally:
            owner.close()
        self.assertEqual(code, 1)
        self.assertEqual(report['reason'], 'snapshotBusy')
        self.assertEqual(calls, [])


if __name__ == '__main__':
    unittest.main()
