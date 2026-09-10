"""Synthetic process death exercises the real launch fence, never native input.

Surviving seal bytes are not a returned external completion acknowledgement.
These fixtures establish process-crash behavior, not power-loss durability.
"""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import supervisor
import runtime_root
import test_bootstrap_process as bootstrap_process


# Reuse the established independent child acquisition, replacing only its
# initialization API and explicit temporary external completion destination.
CHILD = bootstrap_process.CHILD.replace(
    "from recovery_snapshot import MarkerLock",
    "from recovery_snapshot import MarkerLock\nfrom recovery_seal import initialize_sealed")
CHILD = CHILD.replace(
    "result = initialize_fenced(owner, retained,",
    "result = initialize_sealed(owner, retained, "
    "seal_directory=str(root.parent / 'external-seal'), "
    "provenance='synthetic isolated completion acquisition',")
CHILD = CHILD.replace(
    "assert result['result'] == 'initializedFenced' and result['launch_eligible'] is False",
    "assert digest(result.raw) == result.trusted_sha256\n"
    "    print(result.trusted_sha256, flush=True)")


class SealProcessTests(unittest.TestCase):
    def test_death_at_every_boundary_never_returns_pin_or_opens_real_launch_gate(self):
        stages = ('verified', 'pendingCreated', 'pendingWritten', 'pendingFlushed',
                  'pendingDirectoryFlushed', 'markerFlushed', 'committedCreated',
                  'committedWritten', 'committedFlushed', 'committedPublished',
                  'committedDirectoryFlushed', 'sealCreated', 'sealWritten',
                  'sealFlushed', 'sealPublished', 'sealDirectoryFlushed', 'success')
        for stage in stages:
            with self.subTest(stage=stage), tempfile.TemporaryDirectory() as temporary:
                parent = Path(temporary).resolve()
                root = parent / 'directions-stop-spike'
                root.mkdir(mode=0o700)
                external = parent / 'external-seal'
                external.mkdir(mode=0o700)
                child = subprocess.run([sys.executable, '-B', '-c', CHILD, str(root), stage],
                                       cwd=Path(__file__).resolve().parent,
                                       capture_output=True, timeout=5)
                self.assertEqual(child.returncode, 0 if stage == 'success' else 19,
                                 child.stderr.decode())
                if stage == 'success':
                    self.assertRegex(child.stdout.decode().strip(), r'^[0-9a-f]{64}$')
                    self.assertTrue((external / 'seal.json').exists())
                else:
                    self.assertEqual(child.stdout, b'')
                if stage in ('sealPublished', 'sealDirectoryFlushed'):
                    # Complete-looking publication survived without the caller
                    # obtaining authority. Never derive a replacement pin here.
                    self.assertTrue((external / 'seal.json').exists())
                before = {p.name: p.read_bytes() for p in root.iterdir()}
                expected = ('unresolved previous spike' if stage == 'verified'
                            else 'bootstrap remains fenced')
                with patch.object(supervisor.os, 'confstr', return_value=str(parent)), \
                     patch.object(runtime_root, 'TRUSTED_RUNTIME_ROOT', root):
                    with self.assertRaisesRegex(ValueError, expected):
                        supervisor.experiment_lock()
                self.assertEqual({p.name: p.read_bytes() for p in root.iterdir()}, before)
                owner = supervisor.MarkerLock.acquire(root, create=False)
                owner.close()
                if stage != 'verified':
                    self.assertTrue((root / 'bootstrap.pending').exists())


if __name__ == '__main__':
    unittest.main()
