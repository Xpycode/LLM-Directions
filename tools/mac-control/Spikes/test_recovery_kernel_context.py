"""Offline adapter tests. Native kernels and dylib loading are always mocked."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, call, patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import recovery_kernel_context as context


class KernelContextTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.path = Path(self.temporary.name).resolve() / 'inventory.dylib'
        self.path.write_bytes(b'offline fixture: never loaded as executable code')
        self.digest = hashlib.sha256(self.path.read_bytes()).hexdigest()
        self.library = Mock()
        self.library.mc_inventory.return_value = 0
        self.kernel = Mock()
        self.kernel.boot.return_value = '12345678-1234-1234-1234-123456789abc'
        self.kernel.session.return_value = (42, 16)
        self.clock = Mock(return_value=123456789)
        self.loader = self.start(patch.object(context.C, 'CDLL', return_value=self.library))
        self.start(patch.object(context, '_Kernel', return_value=self.kernel))
        for name, value in (('getuid', 501), ('geteuid', 501), ('getpid', 101)):
            self.start(patch.object(context.os, name, return_value=value))

    def start(self, patcher):
        result = patcher.start()
        self.addCleanup(patcher.stop)
        return result

    def capture(self):
        return context.capture_context(self.clock, self.path, self.digest)

    def rejected(self, stage):
        with self.assertRaises(context.ContextFailure) as caught:
            self.capture()
        self.assertEqual(caught.exception.stage, stage)
        self.assertNotIn('private', str(caught.exception))

    def test_single_query_valid_context_and_no_global_scan_or_process_reads(self):
        result = self.capture()
        context.context_snapshot(result)
        self.assertEqual(result['executors'], [])
        self.assertEqual(result['checked_ns'], self.clock.return_value)
        self.library.mc_inventory.assert_called_once_with(501, 101)
        self.assertEqual(self.kernel.mock_calls, [call.boot(), call.session(),
                                                 call.boot(), call.session()])
        self.loader.assert_called_once_with(str(self.path))
        self.assertEqual(self.library.mc_inventory.argtypes,
                         [context.C.c_uint32, context.C.c_int])
        self.assertIs(self.library.mc_inventory.restype, context.C.c_int)

    def test_each_native_rejection_and_unknown_code_never_produces_context(self):
        cases = dict(context._STATUS_STAGES)
        cases.update({2: 'kernelInventoryStatus', -6: 'kernelInventoryStatus'})
        for status, stage in cases.items():
            with self.subTest(status=status):
                self.library.mc_inventory.reset_mock()
                self.library.mc_inventory.return_value = status
                self.rejected(stage)
                self.library.mc_inventory.assert_called_once_with(501, 101)
        self.clock.assert_not_called()

    def test_malformed_native_return(self):
        for status in (False, True, None, 0.0, '0', [], {}):
            with self.subTest(status=status):
                self.library.mc_inventory.return_value = status
                self.rejected('kernelInventoryStatus')

    def test_native_exception_sanitized_without_retry(self):
        self.library.mc_inventory.side_effect = OSError('private native data')
        self.rejected('kernelInventoryQuery')
        self.library.mc_inventory.assert_called_once()

    def test_bad_digest_rejected_before_load_or_inventory(self):
        for digest in ('0' * 64, self.digest.upper(), '', None, b'a' * 64):
            with self.subTest(digest=digest):
                self.digest = digest
                self.rejected('kernelLibrary')
        self.loader.assert_not_called()
        self.library.mc_inventory.assert_not_called()

    def test_empty_or_oversized_library_rejected_before_load(self):
        for size in (0, context.MAX_LIBRARY_BYTES + 1):
            with self.subTest(size=size):
                with self.path.open('wb') as stream:
                    stream.truncate(size)
                self.rejected('kernelLibrary')
        self.loader.assert_not_called()

    def test_nonsymlink_canonical_library_required(self):
        original = self.path
        link = original.parent / 'alias.dylib'
        link.symlink_to(original)
        parent_link = original.parent / 'parent-alias'
        parent_link.symlink_to(original.parent, target_is_directory=True)
        for path in (link, parent_link / original.name, 'relative.dylib',
                     str(original.parent) + '/./inventory.dylib', original.parent,
                     str(original) + '\x00'):
            with self.subTest(path=path):
                self.path = path
                self.rejected('kernelLibrary')
        self.loader.assert_not_called()

    def test_changed_artifact_during_load_rejects(self):
        def load(_):
            self.path.write_bytes(b'changed private artifact')
            return self.library
        self.loader.side_effect = load
        self.rejected('kernelLibrary')
        self.library.mc_inventory.assert_not_called()

    def test_short_or_growing_hash_read_rejects_and_closes_descriptor(self):
        payload = self.path.read_bytes()
        real_close = context.os.close
        for chunks in ([b''], [payload, b'growth']):
            with self.subTest(chunks=chunks), \
                    patch.object(context.os, 'read', side_effect=chunks), \
                    patch.object(context.os, 'close', wraps=real_close) as close:
                self.rejected('kernelLibrary')
                close.assert_called_once()
        self.loader.assert_not_called()

    def test_replaced_file_at_open_rejects_before_loading(self):
        real_open = context.os.open
        def replace_then_open(path, flags):
            replacement = self.path.parent / 'replacement'
            replacement.write_bytes(self.path.read_bytes())
            replacement.replace(self.path)
            return real_open(path, flags)
        with patch.object(context.os, 'open', side_effect=replace_then_open):
            self.rejected('kernelLibrary')
        self.loader.assert_not_called()

    def test_load_and_missing_symbol_failures_are_fixed(self):
        self.loader.side_effect = OSError('private library path')
        self.rejected('kernelLibrary')
        self.loader.side_effect = None
        self.loader.return_value = object()
        self.rejected('kernelLibrary')

    def test_invalid_initial_boot(self):
        for boot in (None, '', 'not-a-uuid', '0' * 36,
                     '00000000-0000-0000-0000-000000000000'):
            with self.subTest(boot=boot):
                self.kernel.boot.return_value = boot
                self.rejected('boot')
        self.library.mc_inventory.assert_not_called()

    def test_invalid_initial_session(self):
        for session in ((0, 16), (42, 17), (42, 0x1010), (True, 16),
                        (42, -1), (42, 2**32 + 16), [42, 16], (42,), None):
            with self.subTest(session=session):
                self.kernel.session.return_value = session
                self.rejected('session')
        self.library.mc_inventory.assert_not_called()

    def test_initial_caller_bounds_and_exact_types(self):
        for operation, value in (('getuid', 502), ('geteuid', 0),
                                 ('geteuid', 2**31), ('geteuid', True),
                                 ('getpid', 0), ('getpid', 2**31), ('getpid', True)):
            with self.subTest(operation=operation, value=value), \
                    patch.object(context.os, operation, return_value=value):
                self.rejected('caller')
        self.loader.assert_not_called()

    def test_boot_session_and_caller_drift(self):
        for method, changed in (('boot', '22345678-1234-1234-1234-123456789abc'),
                                ('session', (43, 16)), ('session', (42, 48))):
            native = getattr(self.kernel, method)
            with self.subTest(method=method):
                native.side_effect = [native.return_value, changed]
                self.rejected('contextRecheck')
                native.side_effect = None
        for operation, before, after in (('getuid', 501, 502), ('geteuid', 501, 502),
                                          ('getpid', 101, 102)):
            with self.subTest(operation=operation), \
                    patch.object(context.os, operation, side_effect=[before, after]):
                self.rejected('contextRecheck')
        self.clock.assert_not_called()

    def test_invalid_timestamp_and_clock_exception(self):
        for timestamp in (0, -1, True, 1.0, None, '123', 2**64):
            with self.subTest(timestamp=timestamp):
                self.clock.return_value = timestamp
                self.rejected('timestamp')
        self.clock.side_effect = OSError('private clock detail')
        self.rejected('timestamp')

    def test_clock_and_trusted_library_arguments_are_mandatory(self):
        with self.assertRaises(TypeError):
            context.capture_context()
        with self.assertRaises(TypeError):
            context.probe_main(self.clock)
        self.loader.assert_not_called()

    def test_wire_success_and_candidate_failure(self):
        for status, expected_exit in ((0, 0), (1, 1), (-4, 1)):
            self.library.mc_inventory.return_value = status
            output = io.StringIO()
            with self.subTest(status=status), contextlib.redirect_stdout(output):
                self.assertEqual(context.probe_main(self.clock, self.path, self.digest),
                                 expected_exit)
            result = json.loads(output.getvalue())
            if status == 0:
                context.context_snapshot(result)
            else:
                self.assertEqual(result, dict(schema='contextFailure/v1',
                                              stage=context._STATUS_STAGES[status]))
                self.assertNotIn('executors', result)
            self.assertLess(len(output.getvalue()), 1024)


if __name__ == '__main__':
    unittest.main()
