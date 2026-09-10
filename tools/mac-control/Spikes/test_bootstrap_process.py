"""Actual Python process death at bootstrap boundaries in private temporary roots.

The contexts and evidence are synthetic. This tests crash persistence and the
actual launch gate, not native boot transitions, power loss or desktop recovery.
"""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import supervisor
import runtime_root


CHILD = r'''
import os, sys
from pathlib import Path
from recovery_snapshot import MarkerLock
from recovery_bootstrap import capture_baseline, load_baseline, initialize_fenced, digest
root, stage = Path(sys.argv[1]), sys.argv[2]
marker = root / 'lock'
marker.write_bytes(b'unresolved')
marker.chmod(0o600)
owner = MarkerLock.acquire(root)
def context(boot, ns):
    return dict(boot=boot, session='fixture-session', checked_ns=ns,
                inventory_complete=True, executors=[])
try:
    baseline = capture_baseline(owner, observe=lambda: context('11111111-1111-1111-1111-111111111111', 100),
                                clock=lambda: 100, provenance='synthetic isolated crash fixture')
    # Test-only trust root: these bytes were just acquired by this same fixture.
    retained = load_baseline(baseline, trusted_sha256=digest(baseline),
                             provenance='synthetic isolated crash fixture')
    def crash(point):
        if point == stage:
            os._exit(19)
    history = b'synthetic historical failed evidence'
    result = initialize_fenced(owner, retained,
        observe=lambda: context('22222222-2222-2222-2222-222222222222', 200),
        clock=lambda: 200, history=history, trusted_history_sha256=digest(history), boundary=crash)
    assert result['result'] == 'initializedFenced' and result['launch_eligible'] is False
finally:
    owner.close()
'''


class BootstrapProcessTests(unittest.TestCase):
    def test_process_death_and_success_all_remain_blocked_at_real_launch_gate(self):
        stages = ('verified', 'pendingCreated', 'pendingWritten', 'pendingFlushed',
                  'pendingDirectoryFlushed', 'markerFlushed', 'committedCreated',
                  'committedWritten', 'committedFlushed', 'committedPublished',
                  'committedDirectoryFlushed', 'success')
        for stage in stages:
            with self.subTest(stage=stage), tempfile.TemporaryDirectory() as temporary:
                parent = Path(temporary).resolve()
                root = parent / 'directions-stop-spike'
                root.mkdir(mode=0o700)
                child = subprocess.run([sys.executable, '-B', '-c', CHILD, str(root), stage],
                                       cwd=Path(__file__).resolve().parent,
                                       capture_output=True, timeout=5)
                self.assertEqual(child.returncode, 0 if stage == 'success' else 19,
                                 child.stderr.decode())
                before = (root / 'lock').read_bytes()
                expected = 'unresolved previous spike' if stage == 'verified' else 'bootstrap remains fenced'
                with patch.object(supervisor.os, 'confstr', return_value=str(parent)), \
                     patch.object(runtime_root, 'TRUSTED_RUNTIME_ROOT', root):
                    with self.assertRaisesRegex(ValueError, expected):
                        supervisor.experiment_lock()
                self.assertEqual((root / 'lock').read_bytes(), before)
                owner = supervisor.MarkerLock.acquire(root)
                owner.close()
                if stage != 'verified':
                    self.assertTrue((root / 'bootstrap.pending').exists())
                if stage == 'success':
                    self.assertEqual(before, b'clean')
                    self.assertTrue((root / 'bootstrap.committed.json').exists())


if __name__ == '__main__':
    unittest.main()
