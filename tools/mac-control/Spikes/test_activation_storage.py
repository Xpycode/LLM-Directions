"""Actual activation/admission filesystem faults in private offline fixtures."""
import os
import unittest
from unittest.mock import patch

import recovery_activation as activation
from recovery_snapshot import MarkerLock
import test_recovery_activation as fixtures
import supervisor
import runtime_root


class ActivationStorageTests(unittest.TestCase):
    def fixture(self):
        helper = fixtures.ActivationTests()
        self.addCleanup(helper.doCleanups)
        return helper.fixture()

    def test_activation_directory_flush_failures_do_not_acknowledge(self):
        for failed_call in (1, 2):
            with self.subTest(failed_call=failed_call):
                fixture = self.fixture()
                original = activation.flush_directory
                count = 0
                def flush(fd):
                    nonlocal count
                    count += 1
                    if count == failed_call:
                        raise OSError("directory flush failed")
                    original(fd)
                with patch.object(activation, "flush_directory", side_effect=flush):
                    with self.assertRaises(OSError):
                        fixture.activate()
                self.assertEqual(fixture.marker.read_bytes(), b"clean")
                before = fixture.state()
                with self.assertRaises(ValueError):
                    fixture.gate()
                self.assertEqual(fixture.state(), before)

    def test_consumption_flush_failure_blocks_retry_and_releases_owner(self):
        for function in ("flush_directory", "flush_file"):
            with self.subTest(function=function):
                fixture = self.fixture()
                ack = fixture.activate()
                with patch.object(activation, function, side_effect=OSError("flush failed")):
                    with self.assertRaises(OSError):
                        fixture.gate(fixture.request(ack))
                self.assertTrue((fixture.root / activation.CONSUMED).exists())
                owner = MarkerLock.acquire(fixture.root, create=False)
                owner.close()
                before = fixture.state()
                for request in (None, fixture.request(ack)):
                    with self.assertRaises(ValueError):
                        fixture.gate(request)
                self.assertEqual(fixture.state(), before)

    def test_zero_writes_reject_and_short_writes_complete(self):
        for target in ("intentCreated", "receiptCreated", "consumptionCreated"):
            for short in (False, True):
                with self.subTest(target=target, short=short):
                    fixture = self.fixture()
                    ack = fixture.activate() if target == "consumptionCreated" else None
                    active = False
                    real_write = os.write
                    def boundary(stage):
                        nonlocal active
                        if stage == target:
                            active = True
                    def write(fd, raw):
                        if active:
                            return real_write(fd, raw[:67]) if short else 0
                        return real_write(fd, raw)
                    with patch("recovery_bootstrap.os.write", side_effect=write):
                        if short:
                            if ack is None:
                                ack = fixture.activate(boundary=boundary)
                                owner = fixture.gate(fixture.request(ack))
                            else:
                                owner = fixture.gate(fixture.request(ack, boundary=boundary))
                            owner.close()
                            self.assertEqual(fixture.marker.read_bytes(),
                                             b"unresolved:" + fixtures.RUN.encode())
                        else:
                            with self.assertRaises(ValueError):
                                if ack is None:
                                    fixture.activate(boundary=boundary)
                                else:
                                    fixture.gate(fixture.request(ack, boundary=boundary))
                            self.assertEqual(fixture.marker.read_bytes(), b"clean")
                    with self.assertRaises(ValueError):
                        fixture.gate()

    def test_reconciliation_flush_failure_does_not_modify_or_admit(self):
        for function in ("flush_directory", "flush_file"):
            with self.subTest(function=function):
                fixture = self.fixture()
                helper = fixtures.ActivationTests()
                transition = helper.interrupted(fixture)
                before = fixture.state()
                with patch.object(activation, function, side_effect=OSError("reflush failed")):
                    with self.assertRaises(OSError):
                        activation.reconcile(fixture.owner, transition, fixture.seal, fixture.baseline,
                                             provenance="new independent reconciliation",
                                             **fixture.context())
                self.assertEqual(fixture.state(), before)
                with self.assertRaises(ValueError):
                    fixture.gate()

    def test_supervisor_run_enters_actual_admission_before_experiment_body(self):
        fixture = self.fixture()
        ack = fixture.activate()
        request = fixture.request(ack)
        fixture.owner.close()
        entered = []
        def body(paths, codes, run_id, owner, clock, focus_loss, worker_crash):
            # Substitute only downstream native work; run and experiment_lock
            # perform their real validation, consumption and ownership path.
            entered.append(run_id)
            self.assertEqual(owner.read_marker(139), b"unresolved:" + run_id.encode())
            self.assertTrue((fixture.root / activation.CONSUMED).exists())
            with self.assertRaisesRegex(ValueError, "snapshotBusy"):
                MarkerLock.acquire(fixture.root)
            return 2
        with patch.object(supervisor.os, "confstr", return_value=str(fixture.parent)), \
             patch.object(runtime_root, "TRUSTED_RUNTIME_ROOT", fixture.root), \
             patch.object(supervisor, "mac_clock", return_value=lambda: fixture.now), \
             patch.object(supervisor, "verified_artifacts", return_value=({}, {})), \
             patch.object(supervisor, "_run_owned", side_effect=body):
            self.assertEqual(supervisor.run("unused-native-artifacts", worker_crash=True,
                                            activation=request), 2)
            with self.assertRaises(ValueError):
                supervisor.run("unused-native-artifacts", worker_crash=True, activation=request)
        self.assertEqual(len(entered), 1)
        owner = MarkerLock.acquire(fixture.root)
        owner.close()


if __name__ == "__main__":
    unittest.main()
