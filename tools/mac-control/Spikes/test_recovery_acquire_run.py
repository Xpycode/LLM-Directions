"""Wrapper journal tests with synthetic children and private reports only."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import recovery_acquire_run as runner


class RunnerTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        self.report = self.root / 'report.jsonl'
        self.configuration = dict(transaction='private-fixture')
        self.prepared = (json.dumps(dict(configuration=self.configuration, stage='prepared')) + '\n').encode()
        self.report.write_bytes(self.prepared)
        self.report.chmod(0o600)
        self.operations = [('capture', ['fixture-capture']), ('reload', ['fixture-reload'])]

    def result(self, operation, **changes):
        result = dict(schema='prospectiveAcquisitionReport/v1', operation=operation,
            result='prospectiveBaselineRetained' if operation == 'capture' else 'acquiredEvidenceReloaded',
            launch_eligible=False, native_recovery_verified=False,
            baseline_sha256='a' * 64, acquisition=dict(acquisition_id='fixture'),
            marker_unchanged=True if operation == 'capture' else None)
        result.update(changes)
        return subprocess.CompletedProcess([operation], 0, json.dumps(result).encode(), b'')

    def invoke(self, **kwargs):
        return runner.run_operations(self.operations, report_path=self.report,
            configuration=self.configuration, cwd=self.root, **kwargs)

    def records(self):
        return [json.loads(line) for line in self.report.read_bytes().splitlines()]

    def test_success_then_consumed_journal_never_replays(self):
        with patch.object(runner.subprocess, 'run', side_effect=[self.result('capture'), self.result('reload')]) as child:
            result = self.invoke()
            self.assertEqual(child.call_count, 2)
        self.assertEqual(result['capture']['baseline_sha256'], result['reload']['baseline_sha256'])
        self.assertEqual([r['stage'] for r in self.records()],
                         ['prepared', 'started', 'finished', 'started', 'finished', 'verified'])
        before = self.report.read_bytes()
        with patch.object(runner.subprocess, 'run') as child, self.assertRaises(ValueError):
            self.invoke()
        child.assert_not_called()
        self.assertEqual(before, self.report.read_bytes())

    def test_timeout_retains_bounded_partial_output_and_stops(self):
        error = subprocess.TimeoutExpired(['fixture'], 45,
            output=b'x' * (runner.MAX_RETAINED_OUTPUT + 1), stderr=b'partial\xff')
        with patch.object(runner.subprocess, 'run', side_effect=error) as child:
            with self.assertRaisesRegex(runner.AcquisitionRunFailure, '^timeout$'):
                self.invoke()
        self.assertEqual(child.call_count, 1)
        result = self.records()[-1]
        self.assertEqual(result['failure'], 'timeout')
        self.assertIsNone(result['exit_code'])
        self.assertEqual(len(result['stdout']), runner.MAX_RETAINED_OUTPUT)
        self.assertTrue(result['stdout_truncated'])
        self.assertEqual(result['stderr'], 'partial\ufffd')
        self.assertTrue(self.report.read_bytes().startswith(self.prepared))

    def test_actual_child_timeout_is_recorded_and_reaped(self):
        # Real subprocess timeout path, never the native acquisition caller.
        source = 'import sys,time; print("partial",flush=True); time.sleep(60)'
        self.operations[0] = ('capture', [sys.executable, '-B', '-I', '-c', source])
        children = []
        original = subprocess.Popen
        def launch(*args, **kwargs):
            child = original(*args, **kwargs)
            children.append(child)
            return child
        with patch.object(subprocess, 'Popen', side_effect=launch):
            with self.assertRaisesRegex(runner.AcquisitionRunFailure, '^timeout$'):
                self.invoke(timeout=0.5)
        self.assertEqual(len(children), 1)
        self.assertIsNotNone(children[0].returncode)
        self.assertEqual(self.records()[-1]['stdout'], 'partial\n')
        self.assertEqual(self.records()[-1]['failure'], 'timeout')
        with self.assertRaises(ChildProcessError):
            os.waitpid(children[0].pid, os.WNOHANG)

    def test_reload_timeout_keeps_completed_capture(self):
        with patch.object(runner.subprocess, 'run', side_effect=[self.result('capture'),
                subprocess.TimeoutExpired(['fixture-reload'], 45, output=b'reloading')]):
            with self.assertRaises(runner.AcquisitionRunFailure):
                self.invoke()
        records = self.records()
        self.assertEqual(records[2]['operation'], 'capture')
        self.assertIsNone(records[2]['failure'])
        self.assertEqual(records[-1]['operation'], 'reload')
        self.assertEqual(records[-1]['failure'], 'timeout')

    def test_child_failure_is_saved_before_stopping(self):
        with patch.object(runner.subprocess, 'run', return_value=
                subprocess.CompletedProcess(['fixture'], 1, b'{"result":"unresolved"}', b'')) as child:
            with self.assertRaises(runner.AcquisitionRunFailure):
                self.invoke()
        self.assertEqual(child.call_count, 1)
        self.assertEqual(self.records()[-1]['exit_code'], 1)
        self.assertEqual(self.records()[-1]['failure'], 'childExit')

    def test_real_capture_late_failures_are_saved_without_reload(self):
        from test_recovery_acquire import AcquisitionTests
        for failed_call in (3, 4):
            with self.subTest(failed_call=failed_call):
                fixture = AcquisitionTests()
                fixture.setUp()
                try:
                    self.report.write_bytes(self.prepared)
                    module_root = str(Path(runner.__file__).parent)
                    source = f'''import sys
sys.path.insert(0, {module_root!r})
import recovery_acquire as acquire
from recovery_probe import ProbeFailure
calls = 0
def observe():
    global calls
    calls += 1
    if calls == {failed_call}: raise ProbeFailure('processIdentityFirstScanRead')
    return dict(boot='11111111-1111-1111-1111-111111111111', session='fixture',
                checked_ns=100, inventory_complete=True, executors=[])
raise SystemExit(acquire.main(sys.argv[1:], observe=observe, clock=lambda: 100))'''
                    self.operations[0] = ('capture', [sys.executable, '-B', '-I', '-c', source, *fixture.args])
                    with self.assertRaisesRegex(runner.AcquisitionRunFailure, '^childExit$'):
                        self.invoke()
                    records = self.records()
                    self.assertEqual([r.get('operation') for r in records[1:]], ['capture', 'capture'])
                    failed = json.loads(records[-1]['stdout'])
                    self.assertEqual(failed['failure_observation'], failed_call)
                    self.assertEqual(failed['failure_phase'], 'final')
                    self.assertEqual(failed['failure_stage'], 'processIdentityFirstScanRead')
                    self.assertFalse(failed['launch_eligible'])
                    self.assertFalse(failed['native_recovery_verified'])
                    self.assertTrue((fixture.evidence / 'baseline/witness.json').exists())
                    self.assertEqual((fixture.marker / 'lock').read_bytes(), b'unresolved')
                finally:
                    fixture.doCleanups()

    def test_launch_failure_records_fixed_reason(self):
        with patch.object(runner.subprocess, 'run', side_effect=OSError('private/path')):
            with self.assertRaises(runner.AcquisitionRunFailure):
                self.invoke()
        self.assertEqual(self.records()[-1]['failure'], 'launch')
        self.assertNotIn('private/path', self.report.read_text())

    def test_invalid_capture_stops_before_reload(self):
        for changes in (dict(marker_unchanged=False), dict(launch_eligible=True),
                        dict(native_recovery_verified=True), dict(baseline_sha256='bad')):
            with self.subTest(changes=changes):
                self.report.write_bytes(self.prepared)
                with patch.object(runner.subprocess, 'run', return_value=self.result('capture', **changes)) as child:
                    with self.assertRaises(runner.AcquisitionRunFailure):
                        self.invoke()
                self.assertEqual(child.call_count, 1)
                self.assertEqual(self.records()[-1]['stage'], 'rejected')

    def test_reload_mismatch_never_verifies(self):
        with patch.object(runner.subprocess, 'run', side_effect=[self.result('capture'),
                self.result('reload', baseline_sha256='b' * 64)]):
            with self.assertRaises(runner.AcquisitionRunFailure):
                self.invoke()
        self.assertEqual(self.records()[-1]['stage'], 'rejected')

    def test_partial_append_preserves_prior_capture_and_blocks_reuse(self):
        original = runner._append
        def append(fd, record):
            if record.get('operation') == 'reload':
                os.write(fd, b'{"interrupted":')
                raise OSError('fixture disk fault')
            original(fd, record)
        with patch.object(runner, '_append', side_effect=append), \
                patch.object(runner.subprocess, 'run', return_value=self.result('capture')) as child:
            with self.assertRaises(OSError):
                self.invoke()
        self.assertEqual(child.call_count, 1)
        lines = self.report.read_bytes().splitlines()
        self.assertEqual(json.loads(lines[2])['operation'], 'capture')
        self.assertEqual(lines[-1], b'{"interrupted":')
        with patch.object(runner.subprocess, 'run') as child, self.assertRaises(ValueError):
            self.invoke()
        child.assert_not_called()

    def test_flush_failure_stops_before_child(self):
        with patch.object(runner, 'flush_file', side_effect=OSError('flush')), \
                patch.object(runner.subprocess, 'run') as child:
            with self.assertRaises(OSError):
                self.invoke()
        child.assert_not_called()
        self.assertTrue(self.report.read_bytes().startswith(self.prepared))


if __name__ == '__main__':
    unittest.main()
