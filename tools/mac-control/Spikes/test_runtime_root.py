"""Shared exclusion regressions using private roots; no native observation/input."""
import contextlib
import io
from itertools import product
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import recovery_acquire
import recovery_caller
import recovery_preflight
import runtime_root
import supervisor
from recovery_snapshot import MarkerLock, fingerprint


class RuntimeRootTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.parent = Path(temporary.name).resolve()
        self.root = self.make_root(self.parent)
        for item in (
            patch.object(runtime_root, 'TRUSTED_RUNTIME_ROOT', self.root),
            patch.object(runtime_root.os, 'confstr', return_value=str(self.parent)),
        ):
            item.start()
            self.addCleanup(item.stop)

    def make_root(self, parent):
        root = parent / 'directions-stop-spike'
        root.mkdir(mode=0o700)
        marker = root / 'lock'
        marker.write_bytes(b'clean')
        marker.chmod(0o600)
        return root

    def test_divergent_lookup_cannot_acquire_second_namespace_or_launch(self):
        alternate = self.parent / 'alternate'
        alternate.mkdir(mode=0o700)
        other = self.make_root(alternate)
        original = supervisor.experiment_lock()
        try:
            before = [(p.read_bytes(), fingerprint(p.stat()))
                      for p in (self.root / 'lock', other / 'lock')]
            with patch.object(runtime_root.os, 'confstr', return_value=str(alternate)), \
                 patch.object(supervisor, 'mac_clock'), \
                 patch.object(supervisor, 'verified_artifacts', return_value=({}, {})), \
                 patch.object(supervisor, '_run_owned') as launch:
                with self.assertRaisesRegex(ValueError, 'runtimeRootMismatch'):
                    supervisor.run('unused')
                launch.assert_not_called()
            original.recheck()
            self.assertEqual(before, [(p.read_bytes(), fingerprint(p.stat()))
                                     for p in (self.root / 'lock', other / 'lock')])
            with self.assertRaises(ValueError):
                supervisor.experiment_lock()
        finally:
            original.close()

    def test_missing_directory_or_marker_is_not_created(self):
        (self.root / 'lock').unlink()
        with self.assertRaises(OSError):
            supervisor.experiment_lock()
        self.assertEqual(list(self.root.iterdir()), [])
        self.root.rmdir()
        with self.assertRaises(OSError):
            supervisor.experiment_lock()
        self.assertFalse(self.root.exists())

    def test_unresolved_marker_and_metadata_survive_rejection(self):
        marker = self.root / 'lock'
        marker.write_bytes(b'unresolved')
        before = fingerprint(marker.stat())
        with self.assertRaisesRegex(ValueError, 'unresolved previous spike'):
            supervisor.experiment_lock()
        self.assertEqual(marker.read_bytes(), b'unresolved')
        self.assertEqual(fingerprint(marker.stat()), before)

    def test_lookup_alias_to_same_pin_still_contends(self):
        alias = self.parent / 'alias'
        alias.symlink_to(self.parent, target_is_directory=True)
        owner = supervisor.experiment_lock()
        try:
            with patch.object(runtime_root.os, 'confstr', return_value=str(alias)):
                self.assertEqual(runtime_root.trusted_runtime_root(), self.root)
                with self.assertRaisesRegex(ValueError, 'snapshotBusy'):
                    supervisor.experiment_lock()
        finally:
            owner.close()

    def test_malformed_lookup_rejects_before_marker_acquisition(self):
        for value in (None, '', 'relative', '//double', 5, '/bad\x00path'):
            with self.subTest(value=value), \
                 patch.object(runtime_root.os, 'confstr', return_value=value), \
                 patch.object(supervisor.MarkerLock, 'acquire') as acquire:
                with self.assertRaisesRegex(ValueError, 'invalidRuntimeLookup'):
                    supervisor.experiment_lock()
                acquire.assert_not_called()

    def test_symlink_pin_or_marker_and_unsafe_mode_reject(self):
        marker = self.root / 'lock'
        marker.chmod(0o644)
        with self.assertRaises(ValueError):
            supervisor.experiment_lock()
        marker.chmod(0o600)
        saved = self.root / 'saved'
        marker.rename(saved)
        marker.symlink_to(saved)
        with self.assertRaises(OSError):
            supervisor.experiment_lock()
        alias = self.parent / 'alias'
        alias.symlink_to(self.root, target_is_directory=True)
        with patch.object(runtime_root, 'TRUSTED_RUNTIME_ROOT', alias):
            with self.assertRaisesRegex(ValueError, 'untrustedRuntimeRoot'):
                supervisor.experiment_lock()

    def test_native_cli_mismatch_rejects_before_clock_observation_or_mutation(self):
        # Arguments need not exist: rejection precedes any transaction operation.
        cases = (
            (recovery_acquire, 'capture', ['--evidence-directory', '/unused/evidence',
             '--anchor-directory', '/unused/anchor', '--archive-directory', '/unused/archive',
             '--history-source', '/unused/history', '--operator-record', 'fixture']),
            (recovery_preflight, 'inspect-legacy', ['--baseline', '/unused/baseline',
             '--baseline-sha256', 'unused', '--history', '/unused/history',
             '--history-sha256', 'unused', '--provenance', 'fixture']),
        )
        for (module, operation, arguments), mode in product(
                cases, ('argument', 'lookup', 'clockOnly', 'observerOnly')):
            expected = '/wrong/root' if mode == 'argument' else str(self.root)
            injections = ({'clock': lambda: 1} if mode == 'clockOnly' else
                          {'observe': lambda: None} if mode == 'observerOnly' else {})
            with self.subTest(operation=operation, mode=mode), \
                 patch.object(runtime_root.os, 'confstr', return_value=str(self.parent / 'missing')), \
                 patch.object(module, 'capture_bounded_context') as observe, \
                 patch.object(supervisor, 'mac_clock') as clock, \
                 patch.object(module, 'capture' if operation == 'capture' else 'inspect_legacy') as action, \
                 contextlib.redirect_stdout(io.StringIO()):
                code = module.main([operation, '--marker-directory', expected, *arguments], **injections)
                self.assertEqual(code, 1)
                observe.assert_not_called()
                clock.assert_not_called()
                action.assert_not_called()

    def test_native_activation_rejects_different_held_root_before_observation(self):
        alternate = self.parent / 'alternate'
        alternate.mkdir(mode=0o700)
        other = self.make_root(alternate)
        owner = MarkerLock.acquire(other, create=False)
        try:
            with patch.object(recovery_caller, 'capture_bounded_context') as observe, \
                 patch.object(recovery_caller, 'mac_clock') as clock:
                with self.assertRaisesRegex(ValueError, 'runtimeRootMismatch'):
                    recovery_caller.activate_retained(owner, None, None, history=None,
                        trusted_history_sha256=None, transition_slot=None,
                        acknowledgement_slot=None, provenance='fixture')
                observe.assert_not_called()
                clock.assert_not_called()
            owner.recheck()
            self.assertEqual(owner.read_marker(139), b'clean')
        finally:
            owner.close()


if __name__ == '__main__':
    unittest.main()
