"""CLI boundary tests in private fixtures; native observation is substituted."""
import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import recovery_bootstrap as bootstrap
import recovery_preflight as preflight
from recovery_snapshot import MarkerLock, fingerprint


class PreflightTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        self.marker = self.root / 'marker'
        self.marker.mkdir(mode=0o700)
        (self.marker / 'lock').write_bytes(b'unresolved')
        (self.marker / 'lock').chmod(0o600)
        self.boot = '11111111-1111-1111-1111-111111111111'
        self.now = 100
        owner = MarkerLock.acquire(self.marker)
        try:
            raw = bootstrap.capture_baseline(owner, observe=self.observe,
                clock=lambda: self.now, provenance='original fixture acquisition')
        finally:
            owner.close()
        self.baseline = self.root / 'baseline.json'
        self.baseline.write_bytes(raw)
        self.history = self.root / 'history.json'
        self.history.write_bytes(b'original failed fixture')
        # Pins retained by the original fixture owner, separate from the report.
        self.args = ['inspect-legacy', '--marker-directory', str(self.marker),
            '--baseline', str(self.baseline), '--baseline-sha256', bootstrap.digest(raw),
            '--history', str(self.history), '--history-sha256', bootstrap.digest(self.history.read_bytes()),
            '--provenance', 'original fixture owner retained both pins']
        self.boot = '22222222-2222-2222-2222-222222222222'
        self.now = 200

    def observe(self):
        return dict(boot=self.boot, session='fixture', checked_ns=self.now,
                    inventory_complete=True, executors=[])

    def invoke(self, args=None, observe=None):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = preflight.main(self.args if args is None else args,
                observe=observe or self.observe, clock=lambda: self.now)
        return code, json.loads(output.getvalue())

    def snapshot(self):
        return (fingerprint(self.marker.stat()), fingerprint((self.marker / 'lock').stat()),
                (self.marker / 'lock').read_bytes(), sorted(p.name for p in self.marker.iterdir()))

    def test_later_boot_report_is_read_only_and_non_authorizing(self):
        before = self.snapshot()
        code, report = self.invoke()
        self.assertEqual(code, 0)
        self.assertEqual(report['result'], 'legacyPreflightObserved')
        self.assertFalse(report['launch_eligible'])
        self.assertFalse(report['native_recovery_verified'])
        self.assertTrue(report['marker_unchanged'])
        self.assertEqual(before, self.snapshot())

    def test_same_boot_and_missing_provenance_reject_unchanged(self):
        before = self.snapshot()
        self.boot = '11111111-1111-1111-1111-111111111111'
        self.assertEqual(self.invoke()[1]['reason'], 'sameBoot')
        self.args[-1] = ''
        self.assertEqual(self.invoke()[1]['reason'], 'missingExternalProvenance')
        self.assertEqual(before, self.snapshot())

    def test_wrong_pin_does_not_open_marker_or_observe(self):
        self.args[self.args.index('--history-sha256') + 1] = '0' * 64
        with patch.object(preflight.MarkerLock, 'acquire', side_effect=AssertionError('opened')):
            code, report = self.invoke(observe=lambda: self.fail('observed'))
        self.assertEqual(code, 1)
        self.assertEqual(report['reason'], 'untrustedEvidence')

    def test_malformed_pinned_baseline_returns_json_without_runtime_access(self):
        for raw in (b'[]', b'null', b'{}', b'{"lockedBaseline":null}'):
            with self.subTest(raw=raw):
                self.baseline.write_bytes(raw)
                self.args[self.args.index('--baseline-sha256') + 1] = bootstrap.digest(raw)
                with patch.object(preflight.MarkerLock, 'acquire', side_effect=AssertionError('opened')):
                    code, report = self.invoke(observe=lambda: self.fail('observed'))
                self.assertEqual(code, 1)
                self.assertEqual(report['result'], 'unresolved')

    def test_missing_namespace_is_not_created(self):
        missing = self.root / 'absent'
        self.args[self.args.index('--marker-directory') + 1] = str(missing)
        self.assertEqual(self.invoke()[0], 1)
        self.assertFalse(missing.exists())

    def test_replaced_marker_and_unreadable_inventory_reject(self):
        with patch.object(preflight, 'capture_bounded_context', side_effect=ValueError('bounded context unresolved')):
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = preflight.main(self.args, clock=lambda: self.now)
            self.assertEqual(code, 1)
        (self.marker / 'lock').rename(self.root / 'original-lock')
        (self.marker / 'lock').write_bytes(b'unresolved')
        (self.marker / 'lock').chmod(0o600)
        self.assertEqual(self.invoke()[1]['reason'], 'baselineContinuityLost')

    def test_intervening_marker_write_is_rejected(self):
        def observe():
            (self.marker / 'lock').write_bytes(b'clean')
            return self.observe()
        self.assertEqual(self.invoke(observe=observe)[0], 1)
        self.assertEqual((self.marker / 'lock').read_bytes(), b'clean')

    def test_busy_marker_is_not_bypassed(self):
        owner = MarkerLock.acquire(self.marker)
        try:
            before = self.snapshot()
            self.assertEqual(self.invoke()[1]['reason'], 'snapshotBusy')
            self.assertEqual(before, self.snapshot())
        finally:
            owner.close()

    def test_missing_inventory_and_stale_observation_reject(self):
        before = self.snapshot()
        for change in ({'inventory_complete': False}, {'checked_ns': 201}):
            with self.subTest(change=change):
                self.assertEqual(self.invoke(observe=lambda: dict(self.observe(), **change))[0], 1)
        self.assertEqual(before, self.snapshot())

    def test_evidence_fifo_rejects_without_blocking_and_no_pin_is_inferred(self):
        import os
        self.baseline.unlink()
        os.mkfifo(self.baseline)
        self.assertEqual(self.invoke()[1]['reason'], 'missingOrOversizeEvidence')

    def test_storage_symlink_and_absent_review_reject_before_writes(self):
        evidence, anchor = self.root / 'evidence', self.root / 'anchor'
        for path in (evidence, anchor):
            path.mkdir(mode=0o700)
        link = self.root / 'link'
        link.symlink_to(anchor)
        args = ['storage-provision', '--evidence-directory', str(evidence),
                '--anchor-directory', str(link), '--location-review', 'fixture']
        self.assertEqual(self.invoke(args)[0], 1)
        args[-3], args[-1] = str(anchor), ''
        self.assertEqual(self.invoke(args)[1]['reason'], 'missingExternalProvenance')
        self.assertEqual(list(evidence.iterdir()), [])
        self.assertEqual(list(anchor.iterdir()), [])

    def test_partial_storage_and_flush_failure_preserved(self):
        evidence, anchor = self.root / 'evidence', self.root / 'anchor'
        for path in (evidence, anchor):
            path.mkdir(mode=0o700)
        args = ['storage-provision', '--evidence-directory', str(evidence),
                '--anchor-directory', str(anchor), '--location-review', 'isolated fixture only']
        with patch('recovery_provision.flush_directory', side_effect=OSError('flush failed')):
            self.assertEqual(self.invoke(args)[0], 1)
        (anchor / 'partial').write_bytes(b'preserve')
        self.assertEqual(self.invoke(args)[0], 1)
        self.assertEqual((anchor / 'partial').read_bytes(), b'preserve')

    def test_real_cli_provision_and_fresh_process_reload(self):
        evidence, anchor = self.root / 'evidence', self.root / 'anchor'
        for path in (evidence, anchor):
            path.mkdir(mode=0o700)
        args = ['--evidence-directory', str(evidence), '--anchor-directory', str(anchor),
                '--location-review', 'isolated fixture only; no deployment claim']
        def command(operation):
            result = subprocess.run([sys.executable, '-B', str(Path(preflight.__file__)), operation, *args],
                capture_output=True, text=True, timeout=15)
            return result.returncode, json.loads(result.stdout)
        first, second = command('storage-provision'), command('storage-reload')
        self.assertEqual(first[0], 0, first)
        self.assertEqual(second[0], 0, second)
        self.assertEqual(first[1]['slots'], second[1]['slots'])
        self.assertEqual(first[1]['root_fingerprints'], second[1]['root_fingerprints'])
        self.assertEqual(first[1]['validated_root_mode'], '0700')
        self.assertFalse(second[1]['launch_eligible'])
        self.assertEqual(command('storage-provision')[0], 1)
        (evidence / 'seal').rmdir()
        self.assertEqual(command('storage-reload')[0], 1)
        self.assertFalse((evidence / 'seal').exists())


if __name__ == '__main__':
    unittest.main()
