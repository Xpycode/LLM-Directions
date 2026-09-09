"""Synthetic subprocess tests only; never launch the native context probe."""
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

import recovery_probe as probe


class ProbeTests(unittest.TestCase):
    context = dict(boot='boot', session='42', checked_ns=987654321,
                   inventory_complete=True, executors=[])

    def run_source(self, source, timeout=2, clock=time.monotonic_ns):
        with patch.object(probe, '_probe_command',
                          return_value=[sys.executable, '-I', '-c', source]):
            return probe.capture_bounded_context(timeout, clock=clock)

    def test_valid_context_preserves_timestamp(self):
        self.assertEqual(self.run_source(f'print({json.dumps(self.context)!r})'),
                         self.context)

    def test_command_uses_exact_supervisor_clock(self):
        command = probe._probe_command()
        self.assertEqual(command[:4], [sys.executable, '-B', '-I', '-c'])
        self.assertIn('from supervisor import mac_clock', command[4])
        self.assertIn('probe_main(clock=mac_clock())', command[4])

    def test_strict_output(self):
        malformed = ['', '{}', '[]', '{', json.dumps(self.context) + '{}',
                     json.dumps(self.context).replace('987654321', 'true'),
                     json.dumps(self.context).replace('987654321', 'NaN'),
                     json.dumps(self.context)[:-1] + ',"checked_ns":1}',
                     json.dumps(dict(self.context, executors=[{'pid': 123}])),
                     json.dumps(dict(self.context, extra=True))]
        for output in malformed:
            with self.subTest(output=output), self.assertRaises(ValueError):
                self.run_source(f'print({output!r})')

    def test_failed_helper_stage_survives_without_accepting_context(self):
        error = dict(schema='contextFailure/v1', stage='processPath')
        with self.assertRaises(ValueError) as caught:
            self.run_source(f'print({json.dumps(error)!r}); raise SystemExit(1)')
        self.assertEqual(caught.exception.stage, 'processPath')
        with self.assertRaises(ValueError):
            self.run_source(f'print({json.dumps(error)!r})')

    def test_actual_helper_entry_serializes_safe_failure(self):
        # Enter the actual helper with only the native boundary substituted.
        directory = os.path.dirname(probe.__file__)
        source = (f'import sys; sys.path.insert(0, {directory!r}); '
                  'import recovery_context as c; '
                  '\ndef fail(clock): raise c.ContextFailure("processPath")\n'
                  'c.capture_context = fail\n'
                  'raise SystemExit(c.probe_main(clock=lambda: 1))')
        with self.assertRaises(ValueError) as caught:
            self.run_source(source)
        self.assertEqual(caught.exception.stage, 'processPath')

    def test_untrusted_helper_diagnostic_is_not_echoed(self):
        for output in ('private/path', '{"schema":"contextFailure/v1","stage":"private/path"}',
                       '{"schema":"contextFailure/v1","stage":"processPath","extra":1}',
                       '{"schema":"contextFailure/v1","stage":"processPath","stage":"boot"}'):
            with self.subTest(output=output), self.assertRaises(ValueError) as caught:
                self.run_source(f'print({output!r}); raise SystemExit(1)')
            self.assertEqual(caught.exception.stage, 'helperExit')
            self.assertNotIn('private/path', str(caught.exception))

    def test_output_limit_and_nonzero_exit(self):
        for source in ('print("x" * 1000000)',
                       f'print({json.dumps(self.context)!r}); raise SystemExit(1)',
                       'import os; os.write(1, b"\\xff")'):
            with self.subTest(source=source), self.assertRaises(ValueError):
                self.run_source(source)

    def test_timeout_kills_and_reaps_only_owned_helper(self):
        real_popen = subprocess.Popen
        children = []
        def launch(*args, **kwargs):
            child = real_popen(*args, **kwargs)
            children.append(child)
            return child
        started = time.monotonic()
        with patch.object(probe.subprocess, 'Popen', side_effect=launch):
            with self.assertRaises(ValueError) as caught:
                self.run_source('import time; time.sleep(60)', timeout=0.1)
            self.assertEqual(caught.exception.stage, 'deadline')
        self.assertLess(time.monotonic() - started, 2)
        self.assertEqual(len(children), 1)
        self.assertIsNotNone(children[0].returncode)
        with self.assertRaises(ChildProcessError):
            os.waitpid(children[0].pid, os.WNOHANG)

    def test_exit_deadline_after_stdout_eof(self):
        with self.assertRaises(ValueError):
            self.run_source('import os,time; os.close(1); time.sleep(60)', timeout=0.1)

    def test_even_inheritable_lock_descriptor_is_closed(self):
        with tempfile.TemporaryFile() as lock:
            os.set_inheritable(lock.fileno(), True)
            source = (f'import os; fd={lock.fileno()}; '
                      '\ntry: os.fstat(fd)\nexcept OSError: pass\n'
                      'else: raise SystemExit(1)\n'
                      f'print({json.dumps(self.context)!r})')
            self.assertEqual(self.run_source(source), self.context)
            os.fstat(lock.fileno())

    def test_invalid_deadline_never_launches(self):
        with patch.object(probe.subprocess, 'Popen') as launch:
            for timeout in (0, -1, True, None, '2', float('nan'), float('inf'),
                            31, 10**1000):
                with self.subTest(timeout=timeout), self.assertRaises(ValueError):
                    probe.capture_bounded_context(timeout)
            launch.assert_not_called()

    def test_continuous_clock_jump_expires_deadline(self):
        # Simulate system sleep after launch without sleeping or native clocks.
        ticks = iter((10_000_000_000, 70_000_000_000))
        started = time.monotonic()
        with self.assertRaises(ValueError):
            self.run_source('import time; time.sleep(60)', timeout=2,
                            clock=lambda: next(ticks))
        self.assertLess(time.monotonic() - started, 1)

    def test_launch_failure_is_unresolved(self):
        with patch.object(probe.subprocess, 'Popen', side_effect=OSError('fixture')):
            with self.assertRaises(ValueError) as caught:
                probe.capture_bounded_context()
            self.assertEqual(caught.exception.stage, 'launch')

    def test_output_limit_stage(self):
        with self.assertRaises(ValueError) as caught:
            self.run_source('print("x" * 1000000)')
        self.assertEqual(caught.exception.stage, 'outputLimit')


if __name__ == '__main__':
    unittest.main()
