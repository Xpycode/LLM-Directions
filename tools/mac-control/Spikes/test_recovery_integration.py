"""Real supervisor and writer, synthetic peers/clock/identities; no native input."""
from pathlib import Path
import threading
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import recovery_record as model
from recovery_storage import RecordWriter
from test_recovery_record import identity
import test_focus_supervisor as fixture
from test_worker_crash import CrashTransport


class StorageTransport(CrashTransport):
    def __init__(self, fault=None):
        super().__init__()
        self.fault = fault
        self.entered, self.release = threading.Event(), threading.Event()
        self.stall_ns = None
        self.stop_during_stall = False
        self.sent_after_stop = []
        self.stopped = False
        self.durable_at_dispatch = []
        self.heartbeats_during_stall = 0

    def recovery_setup(self, runtime, run_id, children, paths, artifact_codes):
        bound_identity = identity()
        bound_identity["run"] = run_id
        for role in ("worker", "target"):
            bound_identity[role]["pid"] = children[role].pid
        if self.fault == "setup-timeout":
            return SimpleNamespace(poll=lambda: None, close=lambda: None)
        root = Path(runtime) / "recovery"
        root.mkdir(mode=0o700)
        self.record_path = root / "record.json"
        self.record_writer = RecordWriter(root)
        original = self.record_writer._write

        def write(data):
            record = model.parse(data)
            if record["state"] == "uncertain" and record["sequence"] == 4:
                if self.fault in ("timeout", "stop"):
                    self.entered.set()
                    if not self.release.wait(3):
                        raise OSError("test stalled writer unreleased")
                elif self.fault == "failure":
                    raise OSError("injected disk failure")
            original(data)

        self.record_writer._write = write
        return SimpleNamespace(poll=lambda: (bound_identity, self.record_writer),
                               close=self.record_writer.close,
                               wait_released=self.record_writer.finished.wait)

    def select(self, timeout):
        # Let the actual writer run; simulated deadlines still advance deterministically.
        time.sleep(0.001)
        if self.entered.is_set() and self.stall_ns is None:
            self.stall_ns = self.ns
        if (self.fault == "stop" and self.stall_ns is not None and not self.stopped
                and self.ns - self.stall_ns >= 250_000_000):
            self.queue(self.client, {"v": 1, "op": "stop"})
        return super().select(timeout)

    def write(self, fd, data):
        import json
        peer = next((p for p in self.peers.values() if p.stdin.fileno() == fd), None)
        if peer:
            row = json.loads(data)
            if row["op"] == "event":
                self.durable_at_dispatch.append((row["sequence"], model.parse(self.record_path.read_bytes())))
                if self.stopped:
                    self.sent_after_stop.append(row)
            if row["op"] == "heartbeat" and self.entered.is_set() and not self.release.is_set():
                self.heartbeats_during_stall += 1
            if row["op"] == "stop":
                self.stopped = True
                self.stop_during_stall = self.entered.is_set() and not self.release.is_set()
                self.release.set()  # Stop was serviced before the write could complete.
        return super().write(fd, data)

    def close(self):
        self.release.set()
        if isinstance(self.record_writer, RecordWriter):
            self.record_writer.close()
            if not self.record_writer.finished.wait(2):
                raise AssertionError("test writer leaked")


class RecoveryIntegrationTests(unittest.TestCase):
    def test_supervisor_reconciles_after_teardown_under_original_lock(self):
        rig = StorageTransport()
        rig.locked_reconciliation = True
        try:
            _, code, trace, marker = fixture.FocusSupervisorTests().run_transport(
                rig=rig, focus_loss=False, worker_crash=True)
        finally:
            rig.close()
        verdict = next(row for row in trace if row['event'] == 'recoveryReconciliation')
        self.assertEqual(verdict['result'], 'sameBootCandidate', verdict)
        self.assertFalse(verdict['restartEligible'])
        self.assertFalse(verdict['nativeRecoveryVerified'])
        self.assertEqual(code, 2)
        self.assertEqual(marker, b'unresolved:' + rig.run_id.encode())
        events = [row['event'] for row in trace]
        self.assertGreater(events.index('recoveryReconciliation'), events.index('targetExited'))
        self.assertTrue(rig.record_writer.finished.is_set())

    def execute(self, fault=None):
        rig = StorageTransport(fault)
        try:
            return fixture.FocusSupervisorTests().run_transport(rig=rig, focus_loss=False, worker_crash=True)
        finally:
            rig.close()

    def test_real_writer_durable_pairs_and_checkpoints_gate_crash(self):
        rig, code, trace, marker = self.execute()
        self.assertEqual(code, 2)
        self.assertEqual(marker, b"unresolved")
        self.assertEqual(len(rig.durable_at_dispatch), 12)
        for sequence, record in rig.durable_at_dispatch:
            self.assertEqual(record["state"], "uncertain")
            self.assertEqual(record["sequence"], sequence if sequence % 2 == 0 else sequence + 1)
            self.assertEqual(record["events"][-1]["kind"], "up")
        injection = next(i for i, row in enumerate(trace) if row["event"] == "workerCrashInjected")
        records = [row for row in trace[:injection] if row["event"] == "recordDurable"]
        self.assertEqual(records[-1]["sequence"], 12)
        self.assertEqual(records[-1]["disposition"], "resolved")
        bound = next(i for i, row in enumerate(trace) if row['event'] == 'recoveryEvidenceBound')
        self.assertLess(bound, injection)
        collected = next(row['evidence'] for row in trace if row['event'] == 'recoveryEvidenceCollected')
        self.assertEqual(collected['record_sha256'], trace[bound]['recordSHA256'])
        self.assertEqual(set(collected['streams']), {'worker', 'target'})
        # Synthetic context only: real OS enumeration is deliberately not invoked.
        from recovery_verifier import verify
        raw = model.encode(rig.record_writer._last)
        context = dict(boot=collected['identity']['boot'], session=collected['identity']['session'],
                       checked_ns=rig.ns, inventory_complete=True, executors=[])
        verdict = verify(b'unresolved:' + collected['identity']['run'].encode(), raw, context, collected)
        self.assertEqual(verdict.result, 'sameBootCandidate', verdict)
        self.assertFalse(verdict.restart_eligible)

    def test_missing_final_ack_or_exit_before_ack_never_injects_crash(self):
        from test_recovery_admission import FakeWriter
        for fault in ('missing', 'exit-before-ack', 'wrong-bytes'):
            rig = CrashTransport()
            class FinalAck(FakeWriter):
                def poll(self):
                    if self.pending is not None:
                        record = model.parse(self.pending)
                        if record['sequence'] == 12 and record['state'] == 'resolved':
                            if fault == 'missing':
                                return None
                            if fault == 'exit-before-ack':
                                rig.peers['worker'].returncode = -9
                            if fault == 'wrong-bytes':
                                return SimpleNamespace(data=b'wrong', error=None)
                    return super().poll()
            rig.record_writer = FinalAck()
            with self.subTest(fault=fault):
                _, code, trace, marker = fixture.FocusSupervisorTests().run_transport(
                    rig=rig, focus_loss=False, worker_crash=True)
                self.assertEqual(code, 2)
                self.assertEqual(marker, b'unresolved')
                self.assertFalse(any(r['event'] == 'workerCrashInjected' for r in trace))
                self.assertFalse(any(r['event'] == 'recoveryEvidenceBound' for r in trace))

    def test_partial_eof_and_stream_pressure_prevent_binding(self):
        for fault in ('partial', 'pressure'):
            class BadStream(CrashTransport):
                def read(self, fd, size):
                    data = super().read(fd, size)
                    worker = self.peers.get('worker')
                    if worker and fd == worker.stdout.fileno() and b'"checkpoint"' in data:
                        if fault == 'partial':
                            self.queues[fd].clear()
                            worker.returncode = -9
                            return data[:-1]
                        return b'x' * 1025
                    return data
            with self.subTest(fault=fault):
                _, code, trace, marker = fixture.FocusSupervisorTests().run_transport(
                    rig=BadStream(), focus_loss=False, worker_crash=True)
                self.assertEqual(code, 2)
                self.assertEqual(marker, b'unresolved')
                self.assertFalse(any(r['event'] == 'workerCrashInjected' for r in trace))

    def test_late_receipt_after_bound_crash_remains_in_collected_evidence(self):
        class LateReceipt(CrashTransport):
            def popen(self, *args, **kwargs):
                peer = super().popen(*args, **kwargs)
                original = peer.kill
                def kill():
                    original()
                    if peer.name == 'worker':
                        self.emit('target', 'keyUp', tag=self.base + 12, sourcePID=peer.pid)
                peer.kill = kill
                return peer
        rig = LateReceipt()
        _, code, trace, marker = fixture.FocusSupervisorTests().run_transport(
            rig=rig, focus_loss=False, worker_crash=True)
        self.assertEqual((code, marker), (2, b'unresolved'))
        collected = next(r['evidence'] for r in trace if r['event'] == 'recoveryEvidenceCollected')
        self.assertEqual(len(collected['receipts']), 13)
        from recovery_verifier import verify
        context = dict(boot=collected['identity']['boot'], session=collected['identity']['session'],
                       checked_ns=rig.ns, inventory_complete=True, executors=[])
        verdict = verify(b'unresolved:' + collected['identity']['run'].encode(),
                         model.encode(rig.record_writer.saved[-1]), context, collected)
        self.assertEqual(verdict.result, 'blocked')

    def test_stop_and_timeout_are_serviced_while_writer_stalls(self):
        for fault, reason in (("stop", "clientStop"), ("timeout", "recordWriteTimeout")):
            with self.subTest(fault=fault):
                rig, code, trace, marker = self.execute(fault)
                self.assertEqual(code, 2)
                self.assertEqual(marker, b"unresolved")
                stop = next(r for r in trace if r["event"] == "stopping")
                self.assertEqual(stop["reason"], reason)
                self.assertTrue(rig.stop_during_stall)
                self.assertGreater(rig.heartbeats_during_stall, 0)
                self.assertEqual(len(rig.durable_at_dispatch), 2)
                self.assertFalse(rig.sent_after_stop)
                self.assertFalse(any(r["event"] == "workerCrashInjected" for r in trace))

    def test_write_failure_and_setup_timeout_never_reach_fault_injection(self):
        for fault, reason, count in (("failure", "recordWriteFailed", 2),
                                     ("setup-timeout", "recoverySetupTimeout", 0)):
            with self.subTest(fault=fault):
                rig, code, trace, marker = self.execute(fault)
                self.assertEqual(code, 2)
                self.assertEqual(marker, b"unresolved")
                self.assertEqual(next(r for r in trace if r["event"] == "stopping")["reason"], reason)
                self.assertEqual(len(rig.durable_at_dispatch), count)
                self.assertFalse(any(r["event"] == "workerCrashInjected" for r in trace))


if __name__ == "__main__":
    unittest.main()
