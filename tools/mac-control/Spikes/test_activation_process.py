"""Python death at activation/admission boundaries; synthetic files and context only."""
import json
from pathlib import Path
import subprocess
import sys
import unittest

import recovery_activation as activation
import recovery_bootstrap as bootstrap
from recovery_snapshot import MarkerLock
import test_recovery_activation as fixtures


CHILD = r'''
import json, os, sys
from pathlib import Path
from unittest.mock import patch
import recovery_activation as activation
import recovery_bootstrap as bootstrap
import recovery_seal as sealing
import supervisor
from recovery_snapshot import MarkerLock
parent, mode, stage, retain = Path(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4] == 'yes'
inputs = json.loads((parent / 'trusted-inputs.json').read_bytes())
def load(loader, data):
    return loader(bytes.fromhex(data['hex']), trusted_sha256=data['pin'], provenance=data['provenance'])
baseline = load(bootstrap.load_baseline, inputs['baseline'])
seal = load(sealing.load_seal, inputs['seal'])
history = bytes.fromhex(inputs['history'])
def observe():
    return dict(boot='22222222-2222-2222-2222-222222222222', session='fixture-session',
                checked_ns=400, inventory_complete=True, executors=[])
args = dict(history=history, trusted_history_sha256=inputs['history_pin'], observe=observe, clock=lambda: 400)
def crash(current):
    if current == stage:
        os._exit(23)
def sink(transition):
    # The original acquiring caller explicitly persists bytes AND its separately
    # retained pin/provenance. Restart never infers trust from the receipt file.
    raw = bootstrap.encode(dict(hex=transition.raw.hex(), pin=transition.trusted_sha256,
                                provenance=transition.provenance))
    with (parent / 'acquired-transition.json').open('xb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
if mode == 'activate':
    owner = MarkerLock.acquire(parent / 'directions-stop-spike', create=False)
    try:
        activation.activate(owner, seal, baseline, provenance='child original activation acquisition',
                            checkpoint_sink=sink if retain else None, boundary=crash, **args)
    finally:
        owner.close()
elif mode == 'consume':
    ack = load(activation.load_activation, inputs['ack'])
    request = activation.ActivationRequest(acknowledgement=ack, seal=seal, baseline=baseline,
                                           boundary=crash, **args)
    with patch.object(supervisor.os, 'confstr', return_value=str(parent)):
        owner = supervisor.experiment_lock('abcdef0123456789' * 2, activation=request)
    owner.close()
else:
    raise AssertionError(mode)
'''


class ActivationProcessTests(unittest.TestCase):
    def fixture(self, *, acknowledged=False):
        harness = fixtures.ActivationTests()
        self.addCleanup(harness.doCleanups)
        fixture = harness.fixture()
        def packed(evidence):
            return dict(hex=evidence.raw.hex(), pin=evidence.trusted_sha256,
                        provenance=evidence.provenance)
        inputs = dict(baseline=packed(fixture.baseline), seal=packed(fixture.seal),
                      history=fixture.history.hex(), history_pin=bootstrap.digest(fixture.history))
        ack = fixture.activate() if acknowledged else None
        if ack is not None:
            inputs['ack'] = packed(ack)
        (fixture.parent / 'trusted-inputs.json').write_bytes(bootstrap.encode(inputs))
        fixture.owner.close()
        return fixture, ack

    def child(self, fixture, mode, stage, retain=False):
        process = subprocess.run(
            [sys.executable, '-B', '-c', CHILD, str(fixture.parent), mode, stage,
             'yes' if retain else 'no'], cwd=Path(__file__).resolve().parent,
            capture_output=True, timeout=10)
        self.assertEqual(process.returncode, 23, process.stderr.decode())

    def test_death_at_every_activation_boundary_blocks_actual_ordinary_launcher(self):
        stages = ('activationVerified', 'intentCreated', 'intentWritten', 'intentFlushed',
                  'intentDirectoryFlushed', 'receiptCreated', 'receiptWritten', 'receiptFlushed',
                  'receiptPublished', 'transitionRetained', 'activationDirectoryFlushed',
                  'activationAcknowledged')
        for stage in stages:
            with self.subTest(stage=stage):
                fixture, _ = self.fixture()
                self.child(fixture, 'activate', stage, retain=True)
                self.assertEqual(fixture.marker.read_bytes(), b'clean')
                self.assertTrue(all((fixture.root / name).exists() for name in bootstrap.ARTIFACTS))
                before = fixture.state()
                with self.assertRaises(ValueError):
                    fixture.gate()
                self.assertEqual(fixture.state(), before)
                owner = MarkerLock.acquire(fixture.root, create=False)
                owner.close()

    def test_death_after_retained_checkpoint_can_explicitly_reconcile_then_admit_once(self):
        fixture, _ = self.fixture()
        self.child(fixture, 'activate', 'transitionRetained', retain=True)
        with self.assertRaises(ValueError):
            fixture.gate()
        acquired = json.loads((fixture.parent / 'acquired-transition.json').read_bytes())
        transition = activation.load_transition(bytes.fromhex(acquired['hex']),
                                                trusted_sha256=acquired['pin'],
                                                provenance=acquired['provenance'])
        fixture.owner = MarkerLock.acquire(fixture.root, create=False)
        self.addCleanup(fixture.owner.close)
        fixture.now = 500
        ack = activation.reconcile(fixture.owner, transition, fixture.seal, fixture.baseline,
                                   provenance='explicit restart reconciliation', **fixture.context())
        owner = fixture.gate(fixture.request(ack))
        self.addCleanup(owner.close)
        self.assertEqual(fixture.marker.read_bytes(), b'unresolved:' + fixtures.RUN.encode())
        owner.write_marker(b'clean')
        owner.close()
        before = fixture.state()
        with self.assertRaises(ValueError):
            fixture.gate(fixture.request(ack), run='3' * 32)
        self.assertEqual(fixture.state(), before)

    def test_receipt_publication_without_original_checkpoint_does_not_enable_reconciliation(self):
        fixture, _ = self.fixture()
        self.child(fixture, 'activate', 'receiptPublished')
        self.assertTrue((fixture.root / 'activation.receipt.json').exists())
        self.assertFalse((fixture.parent / 'acquired-transition.json').exists())
        fixture.owner = MarkerLock.acquire(fixture.root, create=False)
        self.addCleanup(fixture.owner.close)
        before = fixture.state()
        with self.assertRaises(ValueError):
            activation.reconcile(fixture.owner, None, fixture.seal, fixture.baseline,
                                 provenance='missing original checkpoint', **fixture.context())
        self.assertEqual(fixture.state(), before)
        with self.assertRaises(ValueError):
            fixture.gate()

    def test_death_during_consumption_never_allows_second_consumption(self):
        stages = ('consumptionCreated', 'consumptionWritten', 'consumptionFlushed',
                  'consumptionDirectoryFlushed', 'admissionMarkerWritten', 'admissionMarkerFlushed')
        for stage in stages:
            with self.subTest(stage=stage):
                fixture, ack = self.fixture(acknowledged=True)
                marker_inode = fixture.marker.stat().st_ino
                self.child(fixture, 'consume', stage)
                self.assertTrue((fixture.root / fixtures.CONSUMED).exists())
                self.assertEqual(fixture.marker.stat().st_ino, marker_inode)
                fixture.now = 500
                before = fixture.state()
                for request in [None, fixture.request(ack)]:
                    with self.subTest(explicit=request is not None), self.assertRaises(ValueError):
                        fixture.gate(request, run='4' * 32)
                    self.assertEqual(fixture.state(), before)


if __name__ == '__main__':
    unittest.main()
