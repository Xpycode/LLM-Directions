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

    def test_kernel_command_is_explicit_and_uses_continuous_clock(self):
        command = probe._probe_command(('/private/tmp/explicit.dylib', 'a' * 64))
        self.assertIn('from recovery_kernel_context import probe_main', command[4])
        self.assertIn('clock=mac_clock()', command[4])
        self.assertIn("library_path='/private/tmp/explicit.dylib'", command[4])
        self.assertIn("library_sha256='" + 'a' * 64 + "'", command[4])
        compile(command[4], '<helper>', 'exec')

    def test_invalid_library_configuration_never_launches(self):
        with patch.object(probe.subprocess, 'Popen') as launch:
            for configuration in ('path', (), ('relative', 'a' * 64),
                                  ('/absolute', 'wrong'), ('/absolute', None)):
                with self.subTest(configuration=configuration), self.assertRaises(probe.ProbeFailure):
                    probe.capture_bounded_context(inventory_library=configuration)
            launch.assert_not_called()

    def test_kernel_failures_survive_wire_without_fallback(self):
        stages = ('kernelLibrary', 'kernelInventoryQuery', 'kernelInventoryCandidate',
                  'kernelInventoryArgument', 'kernelInventoryAlloc', 'kernelInventoryQueryError',
                  'kernelInventoryMalformed', 'kernelInventoryCallerMissing', 'kernelInventoryStatus')
        for stage in stages:
            error = dict(schema='contextFailure/v1', stage=stage)
            with self.subTest(stage=stage), self.assertRaises(probe.ProbeFailure) as caught:
                self.run_source(f'print({json.dumps(error)!r}); raise SystemExit(1)')
            self.assertEqual(caught.exception.stage, stage)

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

    def test_inventory_diagnostic_refinements_survive_exact_wire_validation(self):
        stages = (
            'inventoryInitialQuery', 'inventoryInitialMalformed',
            'inventoryAfterFirstScanQuery', 'inventoryAfterFirstScanMalformed',
            'inventoryAfterFirstScanChanged', 'inventoryAfterSecondScanQuery',
            'inventoryAfterSecondScanMalformed', 'inventoryAfterSecondScanChanged',
        )
        for stage in stages:
            error = dict(schema='contextFailure/v1', stage=stage)
            with self.subTest(stage=stage), self.assertRaises(ValueError) as caught:
                self.run_source(f'print({json.dumps(error)!r}); raise SystemExit(1)')
            self.assertEqual(caught.exception.stage, stage)

    def test_process_identity_diagnostics_and_legacy_stage_survive_wire_validation(self):
        stages = (
            'processIdentityFirstScanRead', 'processIdentityFirstScanMalformed',
            'processIdentitySecondScanRead', 'processIdentitySecondScanMalformed',
            'processIdentity',
        )
        for stage in stages:
            error = dict(schema='contextFailure/v1', stage=stage)
            with self.subTest(stage=stage), self.assertRaises(ValueError) as caught:
                self.run_source(f'print({json.dumps(error)!r}); raise SystemExit(1)')
            self.assertEqual(caught.exception.stage, stage)

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

    def test_native_malformed_inventory_reaches_exact_helper_wire_stage(self):
        # Keep the real native inventory validator, capture flow, helper entry,
        # subprocess boundary and parent parser. Only Darwin calls are fixtures.
        directory = os.path.dirname(probe.__file__)
        for failure_call, expected in (
                (2, 'inventoryAfterFirstScanMalformed'),
                (3, 'inventoryAfterSecondScanMalformed')):
            source = f'''import os, sys
sys.path.insert(0, {directory!r})
import recovery_context as c
class ProcList:
    def __init__(self): self.calls = 0
    def __call__(self, kind, uid, buffer, capacity):
        self.calls += 1
        if self.calls == {failure_call}:
            if self.calls == 2: return 3
            buffer[0] = buffer[1] = os.getpid()
            return 2 * c.C.sizeof(c.C.c_int)
        buffer[0] = os.getpid()
        return c.C.sizeof(c.C.c_int)
proc = ProcList()
kernel = object.__new__(c._Kernel)
kernel.lib = type('Lib', (), {{}})()
kernel.lib.proc_listpids = proc
kernel.boot = lambda: '12345678-1234-1234-1234-123456789abc'
kernel.session = lambda: (42, 16)
kernel.process = lambda pid: (pid, 1, os.geteuid(), os.geteuid(), os.geteuid(), 123, 456)
kernel.path = lambda pid: '/usr/bin/python3'
original = c.capture_context
c._Kernel = lambda: kernel
def checked(clock):
    try: return original(clock=clock)
    except c.ContextFailure as error:
        if error.stage != {expected!r} or proc.calls != {failure_call}:
            raise c.ContextFailure('kernel')
        raise
c.capture_context = checked
raise SystemExit(c.probe_main(clock=lambda: 1))'''
            with self.subTest(expected=expected), self.assertRaises(ValueError) as caught:
                self.run_source(source)
            self.assertEqual(caught.exception.stage, expected)

    def test_native_process_identity_failures_reach_parent_without_retry_or_details(self):
        # Exercise the inherited IdentityKernel.process implementation and the
        # real capture, helper wire, subprocess boundary, and parent parser.
        directory = os.path.dirname(probe.__file__)
        cases = (
            (1, 'exception', 'processIdentityFirstScanReadQuery'),
            (1, 'malformed', 'processIdentityFirstScanMalformed'),
            (3, 'short', 'processIdentitySecondScanReadShort'),
            (3, 'malformed', 'processIdentitySecondScanMalformed'),
            (1, 'missing', 'processIdentityFirstScanReadMissing'),
            (2, 'denied', 'processRecheckReadDenied'),
            (3, 'zero', 'processIdentitySecondScanReadZero'),
        )
        for failure_call, mode, expected in cases:
            source = f'''import ctypes as C, errno, os, sys
sys.path.insert(0, {directory!r})
import recovery_context as c
import recovery_identity as identity
class Lib:
    def __init__(self): self.calls = 0
    def proc_pidinfo(self, pid, flavor, arg, target, size):
        self.calls += 1
        if self.calls == {failure_call} and {mode!r} == 'exception':
            raise OSError('private/process/native-detail')
        if self.calls == {failure_call} and {mode!r} == 'short':
            return size - 1
        if self.calls == {failure_call} and {mode!r} in ('missing', 'denied', 'zero'):
            C.set_errno({{'missing': errno.ESRCH, 'denied': errno.EPERM, 'zero': 0}}[{mode!r}])
            return 0
        info = C.cast(target, C.POINTER(identity._BSDInfo)).contents
        info.pid = pid + (self.calls == {failure_call} and {mode!r} == 'malformed')
        info.ppid = 1
        info.uid = info.ruid = info.svuid = os.geteuid()
        info.seconds, info.micros = 123, 456
        return C.sizeof(identity._BSDInfo)
kernel = object.__new__(c._Kernel)
kernel.lib = Lib()
kernel.boot = lambda: '12345678-1234-1234-1234-123456789abc'
kernel.session = lambda: (42, 16)
kernel.pids = lambda uid: (os.getpid(),)
kernel.path = lambda pid: '/usr/bin/python3'
original = c.capture_context
c._Kernel = lambda: kernel
def checked(clock):
    try: return original(clock=clock)
    except c.ContextFailure as error:
        if error.stage != {expected!r} or kernel.lib.calls != {failure_call}:
            raise c.ContextFailure('kernel')
        raise
c.capture_context = checked
raise SystemExit(c.probe_main(clock=lambda: 1))'''
            with self.subTest(expected=expected), self.assertRaises(ValueError) as caught:
                self.run_source(source)
            self.assertEqual(caught.exception.stage, expected)
            self.assertNotIn('private', str(caught.exception))

    def test_confirmed_disappearance_crosses_native_adapter_and_helper_boundary(self):
        # Real ctypes identity/enumeration adapters, capture and subprocess wire;
        # substitute only libproc calls. No real process inventory is queried.
        directory = os.path.dirname(probe.__file__)
        for mode, expected in (('absent', None),
                               ('listed', 'inventoryAfterFirstScanChanged'),
                               ('reappeared', 'inventoryAfterSecondScanChanged'),
                               ('denied', 'processIdentityFirstScanReadDenied')):
            source = f'''import ctypes as C, errno, os, sys
sys.path.insert(0, {directory!r})
import recovery_context as c
import recovery_identity as identity
caller = os.getpid()
missing = caller + 1
class Lib:
    def __init__(self): self.inventories = 0; self.missing_reads = 0
    def proc_listpids(self, kind, uid, buffer, capacity):
        self.inventories += 1
        values = [caller]
        if self.inventories == 1 or {mode!r} == 'listed' or (
                self.inventories == 3 and {mode!r} == 'reappeared'):
            values.append(missing)
        for index, pid in enumerate(values): buffer[index] = pid
        return len(values) * C.sizeof(C.c_int)
    def proc_pidinfo(self, pid, flavor, arg, target, size):
        if pid == missing:
            self.missing_reads += 1
            C.set_errno(errno.EPERM if {mode!r} == 'denied' else errno.ESRCH)
            return 0
        info = C.cast(target, C.POINTER(identity._BSDInfo)).contents
        info.pid, info.ppid = pid, 1
        info.uid = info.ruid = info.svuid = os.geteuid()
        info.seconds, info.micros = 123, 456
        return C.sizeof(identity._BSDInfo)
kernel = object.__new__(c._Kernel)
kernel.lib = Lib()
kernel.boot = lambda: '12345678-1234-1234-1234-123456789abc'
kernel.session = lambda: (42, 16)
kernel.path = lambda pid: '/usr/bin/python3'
c._Kernel = lambda: kernel
original = c.capture_context
def checked(clock):
    try: return original(clock=clock)
    finally:
        if kernel.lib.missing_reads != 1: raise c.ContextFailure('kernel')
c.capture_context = checked
raise SystemExit(c.probe_main(clock=lambda: 987654321))'''
            with self.subTest(mode=mode):
                if expected is None:
                    result = self.run_source(source)
                    self.assertTrue(result['inventory_complete'])
                    self.assertEqual(result['executors'], [])
                    self.assertEqual(result['checked_ns'], 987654321)
                else:
                    with self.assertRaises(probe.ProbeFailure) as caught:
                        self.run_source(source)
                    self.assertEqual(caught.exception.stage, expected)

    def test_untrusted_helper_diagnostic_is_not_echoed(self):
        for output in ('private/path', '{"schema":"contextFailure/v1","stage":"private/path"}',
                       '{"schema":"contextFailure/v1","stage":"processPath","extra":1}',
                       '{"schema":"contextFailure/v1","stage":"processPath","stage":"boot"}',
                       '{"schema":"contextFailure/v1","stage":"inventoryAfterFirstScanChanged","extra":1}',
                       '{"schema":"contextFailure/v1","stage":"inventoryAfterFirstScanChanged","stage":"boot"}'):
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
