"""Exercise the tracked observation caller with private files and a fake probe."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from recovery_probe import ProbeFailure
import runtime_root

path = Path(__file__).resolve().parents[3] / 'verification/mac-control/identity-read-observation.py'
spec = importlib.util.spec_from_file_location('identity_observation', path)
caller = importlib.util.module_from_spec(spec)
spec.loader.exec_module(caller)


class ObservationTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        root = Path(directory.name).resolve()
        self.marker = root / 'directions-stop-spike'
        self.marker.mkdir()
        self.report = root / 'observation.jsonl'
        self.owner = Mock()
        self.owner.read_marker.return_value = b'unresolved'
        self.observe = Mock(return_value=dict(inventory_complete=True, executors=[]))
        for item in (patch.object(caller, 'MARKER', self.marker),
                     patch.object(runtime_root, 'TRUSTED_RUNTIME_ROOT', self.marker),
                     patch.object(caller, 'REPORT', self.report),
                     patch.object(caller.os, 'confstr', return_value=str(root)),
                     patch.object(caller.MarkerLock, 'acquire', return_value=self.owner),
                     patch.object(caller, '_stamps', return_value=('same',)),
                     patch.object(caller, 'mac_clock', return_value=iter((1, 2)).__next__),
                     patch.object(caller, 'capture_bounded_context', self.observe)):
            item.start()
            self.addCleanup(item.stop)

    def invoke(self):
        with contextlib.redirect_stdout(io.StringIO()):
            return caller.main()

    def records(self):
        return [json.loads(line) for line in self.report.read_text().splitlines()]

    def test_success_preserves_starts_and_cannot_be_reused(self):
        self.assertEqual(self.invoke(), 0)
        records = self.records()
        self.assertEqual([r['result'] for r in records], ['prepared', 'started', 'observed'])
        self.assertTrue(records[-1]['marker_unchanged'])
        self.assertTrue(all(not r['launch_eligible'] and not r['native_recovery_verified']
                            for r in records))
        self.owner.close.assert_called_once()
        self.assertEqual(self.invoke(), 1)
        self.observe.assert_called_once()
        self.assertEqual(self.records(), records)

    def test_probe_failure_is_retained_without_retry(self):
        self.observe.side_effect = ProbeFailure('processIdentityFirstScanReadMissing')
        self.assertEqual(self.invoke(), 1)
        self.assertEqual(self.records()[-1]['failure_stage'], 'processIdentityFirstScanReadMissing')
        self.assertTrue(self.records()[-1]['marker_unchanged'])
        self.observe.assert_called_once()
        self.owner.close.assert_called_once()

    def test_opt_in_kernel_observation_uses_pinned_library_and_fresh_report(self):
        library = ('/private/tmp/fixture.dylib', 'a' * 64)
        fresh_report = self.report.with_name('kernel.jsonl')
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(caller.main(inventory_library=library, report_path=fresh_report), 0)
            self.assertEqual(caller.main(inventory_library=library, report_path=fresh_report), 1)
        self.assertFalse(self.report.exists())
        rows = [json.loads(line) for line in fresh_report.read_text().splitlines()]
        self.assertEqual(rows[-1]['schema'], 'kernelInventoryObservation/v1')
        self.assertEqual(rows[-1]['inventory_library_sha256'], 'a' * 64)
        self.assertTrue(rows[-1]['marker_unchanged'])
        self.observe.assert_called_once_with(clock=unittest.mock.ANY, inventory_library=library)

    def test_marker_change_overrides_success(self):
        self.owner.read_marker.side_effect = (b'unresolved', b'changed')
        self.assertEqual(self.invoke(), 1)
        self.assertEqual(self.records()[-1]['result'], 'unresolved')
        self.assertFalse(self.records()[-1]['marker_unchanged'])

    def test_close_failure_preserves_native_failure_diagnosis(self):
        self.observe.side_effect = ProbeFailure('processIdentityFirstScanReadMissing')
        self.owner.close.side_effect = OSError('private teardown detail')
        self.assertEqual(self.invoke(), 1)
        final = self.records()[-1]
        self.assertEqual(final['result'], 'unresolved')
        self.assertEqual(final['failure_stage'], 'processIdentityFirstScanReadMissing')
        self.assertEqual(final['teardown_failure'], 'OSError')
        self.assertNotIn('private', self.report.read_text())

    def test_setup_failure_consumes_report_without_observation(self):
        self.owner.read_marker.return_value = b'clean'
        self.assertEqual(self.invoke(), 1)
        self.observe.assert_not_called()
        self.assertEqual([r['result'] for r in self.records()], ['prepared', 'unresolved'])
        self.owner.close.assert_called_once()


if __name__ == '__main__':
    unittest.main()
