"""One-shot wrapper rejection/consumption with private paths and no native calls."""
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch


class AcquiredPreflightRunTests(unittest.TestCase):
    def setUp(self):
        source = Path(__file__).resolve().parents[3] / 'verification/mac-control/acquired-preflight-kernel.py'
        spec = importlib.util.spec_from_file_location('acquired_preflight_run', source)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name).resolve()
        config = dict(self.module.CONFIG)
        for key in ('MARKER', 'SLOTS', 'ARCHIVE', 'ANCHOR'):
            config[key] = root / key
            config[key].mkdir(mode=0o700)
        config['trusted_runtime_root'] = lambda path: path
        self.module.CONFIG = config
        self.module.REPORT = root / 'journal.jsonl'
        library_root = root / 'library'
        library_root.mkdir(mode=0o700)
        self.module.LIBRARY = library_root / 'inventory.dylib'
        self.module.LIBRARY.write_bytes(b'private fixture, never loaded')
        self.module.PIN = hashlib.sha256(self.module.LIBRARY.read_bytes()).hexdigest()

    def result(self, **overrides):
        data = dict(schema='recoveryPreflight/v1', operation='inspect-acquired',
            result='acquiredPreflightObserved', marker_unchanged=True,
            launch_eligible=False, native_recovery_verified=False)
        data.update(overrides)
        return subprocess.CompletedProcess([], 0, json.dumps(data).encode(), b'')

    def run_wrapper(self):
        with contextlib.redirect_stdout(io.StringIO()):
            return self.module.main(['run'])

    def test_success_consumes_journal_and_forwards_persistent_pin(self):
        with patch.object(self.module.subprocess, 'run', return_value=self.result()) as run:
            self.assertEqual(self.run_wrapper(), 0)
            command = run.call_args.args[0]
            self.assertEqual(command[command.index('--inventory-library') + 1], str(self.module.LIBRARY))
            self.assertEqual(command[command.index('--inventory-sha256') + 1], self.module.PIN)
            before = self.module.REPORT.read_bytes()
            with self.assertRaisesRegex(ValueError, 'consumed'):
                self.run_wrapper()
            self.assertEqual(self.module.REPORT.read_bytes(), before)
            run.assert_called_once()

    def test_failure_timeout_and_authority_claim_consume_journal(self):
        for result in (self.result(launch_eligible=True), self.result(native_recovery_verified=True),
                       self.result(result='unresolved'),
                       subprocess.CompletedProcess([], 1, b'{}', b'failure'),
                       subprocess.CompletedProcess([], 0, b'not json', b''),
                       subprocess.CompletedProcess([], 0, b'[]', b''),
                       subprocess.CompletedProcess([], 0, b'x' * 16385, b''),
                       subprocess.TimeoutExpired([], 45)):
            with self.subTest(result=result):
                # Separate fresh private test journal per attempt; never repair a production journal.
                self.module.REPORT = self.module.REPORT.with_name(self.module.REPORT.name + 'x')
                kwargs = dict(side_effect=result) if isinstance(result, Exception) else dict(return_value=result)
                with patch.object(self.module.subprocess, 'run', **kwargs):
                    self.assertEqual(self.run_wrapper(), 1)
                records = [json.loads(line) for line in self.module.REPORT.read_text().splitlines()]
                self.assertEqual(records[-1]['stage'], 'unresolved')
                with self.assertRaisesRegex(ValueError, 'consumed'):
                    self.run_wrapper()

    def test_inspect_never_runs_child_and_changed_library_rejects(self):
        with patch.object(self.module.subprocess, 'run') as run, contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(self.module.main(['inspect']), 0)
            self.assertFalse(self.module.REPORT.exists())
            self.module.LIBRARY.write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError, 'library changed'):
                self.run_wrapper()
            run.assert_not_called()
            self.assertFalse(self.module.REPORT.exists())
            self.module.LIBRARY.unlink()
            with self.assertRaises(FileNotFoundError):
                self.run_wrapper()
            run.assert_not_called()


if __name__ == '__main__':
    unittest.main()
