"""Prospective acquisition through the CLI parser in private fixture namespaces."""
import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import recovery_acquire as acquire
import recovery_bootstrap as bootstrap
import recovery_retention as retention
from recovery_snapshot import fingerprint


class AcquisitionTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        self.marker, self.evidence, self.anchor, self.archive = [self.root / n for n in
            ('marker', 'evidence', 'anchor', 'archive')]
        for p in (self.marker, self.evidence, self.anchor, self.archive):
            p.mkdir(mode=0o700)
        (self.marker / 'lock').write_bytes(b'unresolved')
        (self.marker / 'lock').chmod(0o600)
        self.source = self.root / 'source.json'
        self.source.write_bytes(b'original failure report; unauthenticated history acquired now\n')
        self.common = ['--evidence-directory', str(self.evidence), '--anchor-directory', str(self.anchor),
                       '--archive-directory', str(self.archive)]
        self.args = ['capture', *self.common, '--marker-directory', str(self.marker),
                     '--history-source', str(self.source), '--operator-record', 'private fixture acquisition']
        self.now = 100
        self.boot = '11111111-1111-1111-1111-111111111111'

    def observe(self):
        return dict(boot=self.boot, session='fixture', checked_ns=self.now,
                    inventory_complete=True, executors=[])

    def invoke(self, args=None):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = acquire.main(self.args if args is None else args, observe=self.observe, clock=lambda: self.now)
        return code, json.loads(out.getvalue())

    def stamps(self):
        return fingerprint(self.marker.stat()), fingerprint((self.marker / 'lock').stat())

    def test_capture_and_actual_fresh_process_reload(self):
        stamps = self.stamps()
        code, report = self.invoke()
        self.assertEqual(code, 0, report)
        self.assertEqual(stamps, self.stamps())
        self.assertEqual((self.archive / 'history.json').read_bytes(), self.source.read_bytes())
        self.assertFalse(report['launch_eligible'])
        self.assertEqual(report['acquisition']['classification'], 'historicalCopyAcquiredNow')
        result = subprocess.run([sys.executable, '-B', acquire.__file__, 'reload', *self.common],
                                capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(json.loads(result.stdout)['baseline_sha256'], report['baseline_sha256'])
        self.assertEqual(self.invoke()[0], 1)  # No repeat acquisition/overwrite.

    def test_archive_corruption_rejects(self):
        self.assertEqual(self.invoke()[0], 0)
        (self.archive / 'history.json').write_bytes(b'changed')
        self.assertEqual(self.invoke(['reload', *self.common])[0], 1)

    def test_probe_failure_reports_stage_and_preserves_failed_transaction(self):
        from recovery_probe import ProbeFailure
        with patch.object(self, 'observe', side_effect=ProbeFailure('inventoryAfterFirstScanChanged')):
            code, report = self.invoke()
        self.assertEqual(code, 1)
        self.assertEqual(report['failure_stage'], 'inventoryAfterFirstScanChanged')
        self.assertEqual(report['failure_observation'], 1)
        self.assertEqual(report['failure_phase'], 'baseline')
        self.assertFalse(report['launch_eligible'])
        self.assertFalse(report['native_recovery_verified'])
        self.assertEqual(list((self.evidence / 'baseline').iterdir()), [])
        self.assertEqual((self.marker / 'lock').read_bytes(), b'unresolved')
        self.assertEqual((self.archive / 'history.json').read_bytes(), self.source.read_bytes())

    def late_probe_failure(self, failed_call, stage='processIdentity'):
        from recovery_probe import ProbeFailure
        stamps = self.stamps()
        samples = [self.observe() for _ in range(failed_call - 1)]
        samples.append(ProbeFailure(stage))  # Both historical and refined stages survive.
        with patch.object(self, 'observe', side_effect=samples) as observer:
            code, report = self.invoke()
        self.assertEqual(observer.call_count, failed_call)
        self.assertEqual(code, 1)
        self.assertEqual(report['failure_stage'], stage)
        self.assertEqual(report['failure_observation'], failed_call)
        self.assertEqual(report['failure_phase'], 'final')
        self.assertFalse(report['launch_eligible'])
        self.assertFalse(report['native_recovery_verified'])
        self.assertEqual(stamps, self.stamps())
        self.assertEqual((self.marker / 'lock').read_bytes(), b'unresolved')
        self.assertTrue((self.evidence / 'baseline/witness.json').exists())
        roots = (self.evidence, self.anchor, self.archive)
        def artifacts():
            return {str(p): p.read_bytes() for root in roots for p in root.rglob('*') if p.is_file()}
        retained = artifacts()
        with patch.object(self, 'observe') as observer:
            self.assertEqual(self.invoke()[0], 1)
            observer.assert_not_called()
        self.assertEqual(artifacts(), retained)
        # In a separate process, evidence-only reload still grants no authority
        # and cannot assert that this interrupted acquisition completed.
        reloaded = subprocess.run([sys.executable, '-B', acquire.__file__, 'reload', *self.common],
                                  capture_output=True, text=True, timeout=15)
        self.assertEqual(reloaded.returncode, 0, reloaded.stdout)
        report = json.loads(reloaded.stdout)
        self.assertEqual(report['result'], 'acquiredEvidenceReloaded')
        self.assertIsNone(report['marker_unchanged'])
        self.assertFalse(report['launch_eligible'])
        self.assertFalse(report['native_recovery_verified'])
        self.assertEqual(artifacts(), retained)

    def test_first_final_observation_failure_preserves_without_retry(self):
        self.late_probe_failure(3)

    def test_second_final_observation_failure_preserves_without_retry(self):
        self.late_probe_failure(4, 'processIdentitySecondScanMalformed')

    def test_replaced_baseline_slot_is_not_discovered(self):
        self.assertEqual(self.invoke()[0], 0)
        (self.evidence / 'baseline').rename(self.root / 'old-baseline')
        (self.evidence / 'baseline').mkdir(mode=0o700)
        self.assertEqual(self.invoke(['reload', *self.common])[0], 1)

    def test_source_ancestor_symlink_and_fifo_reject_before_provision(self):
        link = self.root / 'link'
        link.symlink_to(self.root)
        self.args[self.args.index('--history-source') + 1] = str(link / 'source.json')
        self.assertEqual(self.invoke()[0], 1)
        self.args[self.args.index('--history-source') + 1] = str(self.source)
        self.source.unlink()
        os.mkfifo(self.source)
        self.assertEqual(self.invoke()[0], 1)
        self.assertEqual(list(self.anchor.iterdir()), [])

    def test_overlap_and_nonempty_archive_reject(self):
        self.args[self.args.index('--archive-directory') + 1] = str(self.evidence)
        self.assertEqual(self.invoke()[0], 1)
        self.args[self.args.index('--archive-directory') + 1] = str(self.archive)
        (self.archive / 'prior').write_bytes(b'preserve')
        self.assertEqual(self.invoke()[0], 1)
        self.assertEqual(list(self.anchor.iterdir()), [])

    def test_archive_flush_failure_preserves_and_cannot_retry(self):
        with patch.object(acquire, 'flush_directory', side_effect=OSError('flush')):
            self.assertEqual(self.invoke()[0], 1)
        self.assertEqual((self.archive / 'history.json').read_bytes(), self.source.read_bytes())
        self.assertEqual(self.invoke()[0], 1)
        self.assertEqual((self.marker / 'lock').read_bytes(), b'unresolved')

    def test_final_marker_change_fails_and_preserves_witness(self):
        original = retention.retain
        def retain(*args, **kwargs):
            original(*args, **kwargs)
            (self.marker / 'lock').write_bytes(b'clean')
        with patch.object(retention, 'retain', side_effect=retain):
            self.assertEqual(self.invoke()[0], 1)
        self.assertTrue((self.evidence / 'baseline/witness.json').exists())
        self.assertEqual((self.marker / 'lock').read_bytes(), b'clean')
        # Reload is evidence-only; cannot assert the interrupted caller completed.
        code, report = self.invoke(['reload', *self.common])
        self.assertEqual(code, 0)
        self.assertIsNone(report['marker_unchanged'])
        self.assertFalse(report['native_recovery_verified'])

    def test_provenance_mismatch_rejected_even_with_authenticated_slot(self):
        self.assertEqual(self.invoke()[0], 0)
        args = type('Args', (), dict(operation='reload', evidence_directory=str(self.evidence),
                    anchor_directory=str(self.anchor), archive_directory=str(self.archive)))()
        baseline, _ = acquire.load_acquired(args)
        changed = bootstrap.TrustedBaseline(baseline.raw, baseline.trusted_sha256, 'different provenance')
        with patch.object(retention, 'load', return_value=changed):
            self.assertEqual(self.invoke(['reload', *self.common])[0], 1)

    def test_later_boot_still_requires_namespace_continuity(self):
        self.assertEqual(self.invoke()[0], 0)
        args = type('Args', (), dict(operation='reload', evidence_directory=str(self.evidence),
                    anchor_directory=str(self.anchor), archive_directory=str(self.archive)))()
        baseline, meta = acquire.load_acquired(args)
        directory, stamps, _ = bootstrap._baseline_data(baseline)
        from recovery_preflight import main
        raw = self.root / 'retained-baseline.json'
        raw.write_bytes(baseline.raw)
        argv = ['inspect-legacy', '--marker-directory', directory, '--baseline', str(raw),
                '--baseline-sha256', baseline.trusted_sha256, '--history', str(self.archive / 'history.json'),
                '--history-sha256', meta['history_sha256'], '--provenance', baseline.provenance]
        def inspect():
            with contextlib.redirect_stdout(io.StringIO()):
                return main(argv, observe=self.observe, clock=lambda: self.now)
        self.assertEqual(inspect(), 1)
        self.boot = '22222222-2222-2222-2222-222222222222'
        self.assertEqual(inspect(), 0)
        (self.marker / 'extra').touch()
        self.assertEqual(inspect(), 1)


if __name__ == '__main__':
    unittest.main()
