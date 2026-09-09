"""Read-only identity tests; no app launch or runtime namespace access."""
import hashlib
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

import recovery_identity as identity


class IdentityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.paths = {}
        self.children = {}
        self.rows = {}
        for pid, role in enumerate(('worker', 'target'), 401):
            path = Path(self.temp.name).resolve() / role
            path.write_bytes(role.encode())
            self.paths[role] = path
            self.children[role] = Mock(pid=pid, poll=Mock(return_value=None))
            self.rows[pid] = (pid, os.getpid(), 501, 501, 501, 123, pid)
        self.kernel = Mock()
        self.kernel.boot.return_value = '12345678-1234-1234-1234-123456789abc'
        self.kernel.session.return_value = (42, 0x10)
        self.kernel.process.side_effect = lambda pid: self.rows[pid]
        self.kernel.path.side_effect = lambda pid: str(self.paths['worker' if pid == 401 else 'target'])
        self.stack = [patch.object(identity, '_Kernel', return_value=self.kernel),
                      patch.object(identity.os, 'getuid', return_value=501),
                      patch.object(identity.os, 'geteuid', return_value=501)]
        for item in self.stack:
            item.start()
            self.addCleanup(item.stop)

    def capture(self):
        return identity.capture_identity('a' * 32, self.children, self.paths)

    def test_success(self):
        result = self.capture()
        self.assertEqual(result['worker']['code'], hashlib.sha256(b'worker').hexdigest())
        self.assertEqual(result['worker']['start'], '123-401')
        self.assertEqual(result['session'], '42')

    def test_wrong_parent_uid_and_start(self):
        original = self.rows[401]
        for offset, value in ((1, 999999), (2, 502), (3, 502), (4, 502), (5, 0), (6, 1000000)):
            with self.subTest(offset=offset):
                row = list(original)
                row[offset] = value
                self.rows[401] = tuple(row)
                with self.assertRaises(ValueError):
                    self.capture()

    def test_wrong_path(self):
        self.kernel.path.return_value = '/wrong'
        self.kernel.path.side_effect = None
        with self.assertRaises(ValueError):
            self.capture()

    def test_dead_child(self):
        self.children['worker'].poll.return_value = 0
        with self.assertRaises(ValueError):
            self.capture()

    def test_identity_drift_during_hash(self):
        original = identity._digest
        def drift(path):
            result = original(path)
            self.rows[401] = (*self.rows[401][:-1], 999)
            return result
        with patch.object(identity, '_digest', side_effect=drift):
            with self.assertRaises(ValueError):
                self.capture()

    def test_invalid_session(self):
        for session in ((0, 16), (0xffffffff, 16), (0xfffffffe, 16), (42, 0), (42, 17), (42, 0x1010)):
            with self.subTest(session=session):
                self.kernel.session.return_value = session
                with self.assertRaises(ValueError):
                    self.capture()

    def test_session_drift(self):
        self.kernel.session.side_effect = [(42, 16), (43, 16)]
        with self.assertRaises(ValueError):
            self.capture()

    def test_boot_drift(self):
        self.kernel.boot.side_effect = [self.kernel.boot.return_value, '22345678-1234-1234-1234-123456789abc']
        with self.assertRaises(ValueError):
            self.capture()

    def test_kernel_failure_and_duplicate_pid(self):
        self.kernel.process.side_effect = OSError('unavailable')
        with self.assertRaises(ValueError):
            self.capture()
        self.kernel.process.side_effect = lambda pid: self.rows[pid]
        self.children['target'] = self.children['worker']
        self.paths['target'] = self.paths['worker']
        with self.assertRaises(ValueError):
            self.capture()

    def test_root_caller(self):
        with patch.object(identity.os, 'geteuid', return_value=0):
            with self.assertRaises(ValueError):
                self.capture()

    def test_artifact_replaced_during_read(self):
        original = identity.os.read
        def replace(fd, size):
            result = original(fd, size)
            new = self.paths['worker'].with_suffix('.new')
            new.write_bytes(b'changed')
            new.replace(self.paths['worker'])
            return result
        with patch.object(identity.os, 'read', side_effect=replace):
            with self.assertRaises(ValueError):
                self.capture()

    def test_symlink_and_oversize_refused(self):
        link = self.paths['worker'].with_suffix('.link')
        link.symlink_to(self.paths['worker'])
        with self.assertRaises(ValueError):
            identity._digest(link)
        with patch.object(identity, 'MAX_ARTIFACT_BYTES', 1):
            with self.assertRaises(ValueError):
                self.capture()


@unittest.skipUnless(sys.platform == 'darwin', 'Darwin read-only ABI smoke check')
class KernelSmokeTests(unittest.TestCase):
    def test_current_process_only(self):
        kernel = identity._Kernel()
        row = kernel.process(os.getpid())
        self.assertEqual(row[:4], (os.getpid(), os.getppid(), os.geteuid(), os.getuid()))
        self.assertGreater(row[5], 0)
        self.assertTrue(Path(kernel.path(os.getpid())).is_absolute())
    def test_boot_query_availability(self):
        kernel = identity._Kernel()
        try:
            boot = kernel.boot()
        except OSError as error:
            self.skipTest(f'boot sysctl unavailable (errno {error.errno}); capture fails closed')
        self.assertTrue(boot)

    def test_session_query(self):
        kernel = identity._Kernel()
        session, attributes = kernel.session()
        self.assertIsInstance(session, int)
        self.assertIsInstance(attributes, int)


class SyscallValidationTests(unittest.TestCase):
    def setUp(self):
        self.kernel = object.__new__(identity._Kernel)
        self.kernel.lib = Mock()
        self.kernel.security = Mock()

    def test_truncated_process_struct(self):
        self.kernel.lib.proc_pidinfo.return_value = 135
        with self.assertRaises(ValueError):
            self.kernel.process(123)

    def test_missing_or_truncated_path(self):
        for count in (0, -1, 4096, 4):
            self.kernel.lib.proc_pidpath.return_value = count
            with self.assertRaises(ValueError):
                self.kernel.path(123)

    def test_session_status_failure(self):
        self.kernel.security.SessionGetInfo.return_value = -60500
        with self.assertRaises(ValueError):
            self.kernel.session()

    def test_malformed_boot(self):
        self.kernel.lib.sysctlbyname.return_value = 0
        with self.assertRaises(ValueError):
            self.kernel.boot()


if __name__ == '__main__':
    unittest.main()
