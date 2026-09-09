"""Adapter integration using real pipes/waits/files and synthetic identities/inventory.

No native binaries or input APIs. Fake identity start/code and OS probe deliberately
do not establish Darwin process inventory, launch identity, or native recovery.
"""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

import recovery_record as model
from recovery_storage import RecordWriter
from recovery_evidence import OwnedEvidence, check_recovery
from recovery_verifier import OBSERVATION_NS


PEER = r'''
import json, os, sys, threading, time
role, fault, run = sys.argv[1:4]
def emit(event, **fields):
    print(json.dumps(dict(event=event, run=run, ns=time.monotonic_ns(), **fields)), flush=True)
if role == 'worker':
    output = os.fdopen(int(sys.argv[4]), 'w')
    ack = os.fdopen(int(sys.argv[5]))
    sys.stdin.readline()
    if fault == 'partial':
        sys.stdout.write('{"event":'); sys.stdout.flush(); sys.exit(0)
    if fault == 'oversize':
        print('x' * 1025, flush=True); sys.exit(0)
    if fault == 'duplicate-key':
        print('{"event":"posted","event":"checkpoint"}', flush=True); sys.exit(0)
    if fault == 'forged-exit':
        emit('workerExited', status=0); sys.exit(0)
    for seq in range(1, 5):
        kind = 'down' if seq % 2 else 'up'
        row = dict(sequence=seq, tag=1000 + seq, kind=kind, origin_pid=os.getpid())
        output.write(json.dumps(row) + '\n'); output.flush()
        emit('posted', sequence=seq, tag=1000 + seq, kind=kind)
        if not (fault == 'delayed-receipt' and seq == 4):
            if not ack.readline(): sys.exit(4)
        if seq % 2 == 0 and fault != 'missing-checkpoint':
            emit('checkpoint', sequence=seq, tag=1000 + seq, held=[])
    output.close()
    if fault != 'delayed-receipt': sys.stdin.readline()
    sys.exit(17)
else:
    input_events = os.fdopen(int(sys.argv[4]))
    ack = os.fdopen(int(sys.argv[5]), 'w')
    def read_events():
        for line in input_events:
            row = json.loads(line)
            if fault == 'delayed-receipt' and row['sequence'] == 4: time.sleep(0.2)
            if fault == 'wrong-kind': row['kind'] = 'down'
            if fault == 'wrong-origin': row['origin_pid'] += 1
            emit('receipt', **row)
            if fault == 'duplicate-receipt': emit('receipt', **row)
            if fault != 'delayed-receipt' or row['sequence'] != 4:
                ack.write('ack\n'); ack.flush()
    reader = threading.Thread(target=read_events)
    reader.start()
    line = sys.stdin.readline()
    if line:
        reader.join(2)
        if reader.is_alive(): sys.exit(8)
        if fault != 'missing-fence': emit('observationComplete')
        if fault == 'after-fence':
            emit('receipt', sequence=5, tag=1005, kind='down', origin_pid=1)
    sys.exit(7 if fault == 'target-failure' else 0)
'''


class RecoveryEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="recovery-evidence-test-")
        self.root = Path(self.temp.name).resolve()
        self.marker_dir, self.run_dir = self.root / "marker", self.root / "run"
        self.marker_dir.mkdir(mode=0o700)
        self.run_dir.mkdir(mode=0o700)
        (self.run_dir / "recovery").mkdir(mode=0o700)
        self.children = {}
        self.observer = None

    def tearDown(self):
        if self.observer is not None:
            self.observer.close()
        for child in self.children.values():
            if child.stdin:
                child.stdin.close()
        for child in self.children.values():
            try:
                child.wait(timeout=0.5)
            except subprocess.TimeoutExpired:
                child.kill()  # Only these fixed Python fixtures created by this test.
                child.wait(timeout=2)
            child.stdout.close()
            child.stderr.close()
        self.temp.cleanup()

    def write(self, path, data):
        path.write_bytes(data)
        path.chmod(0o600)

    def start(self, fault="none", bind=True):
        self.fault, self.bind = fault, bind
        read_events, write_events = os.pipe()
        read_ack, write_ack = os.pipe()
        run = "a" * 32
        try:
            for role, fds in (("worker", (write_events, read_ack)), ("target", (read_events, write_ack))):
                self.children[role] = subprocess.Popen(
                    [sys.executable, "-B", "-c", PEER, role, fault, run, *map(str, fds)],
                    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    pass_fds=fds)
        finally:
            for fd in (read_events, write_events, read_ack, write_ack):
                os.close(fd)
        self.identity = dict(boot="synthetic-boot", session="synthetic-login", run=run,
                             **{role: dict(pid=child.pid, start="synthetic-start", code="b" * 64)
                                for role, child in self.children.items()})
        record = model.new_record(self.identity)
        for tag in (1001, 1003):
            record = model.reserve_pair(record, tag)
            record = model.checkpoint(record, dict(identity=self.identity, sequence=record["sequence"],
                                                    tag=tag + 1, held=[], receipts=record["events"]))
        self.raw = model.encode(record)
        self.write(self.marker_dir / "lock", b"unresolved:" + run.encode())
        self.write(self.run_dir / "recovery/record.lock", b"")
        self.write(self.run_dir / "recovery/record.json", self.raw)
        self.observer = OwnedEvidence(self.identity, self.children)
        # Synthetic stand-in for an independent final durable acknowledgement.
        # The snapshot reader must not manufacture this from its own disk read.
        self.children["worker"].stdin.write(b"start\n")
        self.children["worker"].stdin.flush()

    def until(self, condition, seconds=3):
        deadline = time.monotonic() + seconds
        while not condition():
            self.assertLess(time.monotonic(), deadline, "fixture evidence timeout")
            self.observer.pump(0.01)

    def finish(self, interval=5_000_000):
        self.until(lambda: len(self.observer.rows["posts"]) >= 4
                   and len(self.observer.rows["receipts"]) >= 4
                   and (len(self.observer.rows["checkpoints"]) == 2 or self.fault == "missing-checkpoint"))
        if self.bind:
            try:
                self.observer.bind_durable_record(self.raw)
            except ValueError:
                return
        self.children["worker"].stdin.write(b"finish\n")
        self.children["worker"].stdin.flush()
        self.until(lambda: "worker" in self.observer.exits and "worker" in self.observer.streams)
        threshold = max(self.observer.exits["worker"]["ns"], self.observer.streams["worker"]["eof_ns"])
        self.until(lambda: time.monotonic_ns() >= threshold + interval)
        with patch("recovery_verifier.OBSERVATION_NS", interval):
            self.observer.request_observation()
        self.until(lambda: len(self.observer.exits) == len(self.observer.streams) == 2)

    def probe(self):
        return dict(boot=self.identity["boot"], session=self.identity["session"],
                    checked_ns=time.monotonic_ns(), inventory_complete=True, executors=[])

    def result(self, probe=None, observer=True, interval=5_000_000):
        # Most rejection fixtures shorten only the observation duration; one
        # end-to-end success below exercises the actual two-second default.
        with patch("recovery_verifier.OBSERVATION_NS", interval):
            return check_recovery(self.marker_dir, self.run_dir, probe or self.probe,
                                  self.observer if observer else None)

    def test_real_owned_streams_waits_and_locked_snapshot(self):
        self.start()
        self.finish(OBSERVATION_NS)
        result = self.result(interval=OBSERVATION_NS)
        self.assertEqual(result.result, "sameBootCandidate", result)
        self.assertFalse(result.restart_eligible)
        self.assertFalse(result.native_recovery_verified)
        self.assertEqual((self.marker_dir / "lock").read_bytes(), b"unresolved:" + b"a" * 32)
        self.assertEqual((self.run_dir / "recovery/record.json").read_bytes(), self.raw)
        evidence = self.observer.evidence()
        self.assertEqual(evidence["exits"]["worker"]["status"], 17)
        evidence["posts"].clear()
        self.assertEqual(len(self.observer.evidence()["posts"]), 4)

    def test_partial_oversized_duplicate_key_and_forged_exit_frames(self):
        for fault in ("partial", "oversize", "duplicate-key", "forged-exit"):
            with self.subTest(fault=fault):
                # Subtests need independent retained children and namespaces.
                case = RecoveryEvidenceTests()
                case.setUp()
                try:
                    case.start(fault)
                    with self.assertRaises(ValueError):
                        case.until(lambda: len(case.observer.exits) == 2)
                    self.assertEqual(case.result().result, "blocked")
                finally:
                    case.tearDown()

    def test_semantic_faults_and_extra_rows_are_not_filtered(self):
        for fault in ("duplicate-receipt", "wrong-kind", "wrong-origin", "missing-checkpoint",
                      "missing-fence", "after-fence", "target-failure"):
            with self.subTest(fault=fault):
                case = RecoveryEvidenceTests()
                case.setUp()
                try:
                    case.start(fault)
                    case.finish()
                    self.assertEqual(case.result().result, "blocked")
                finally:
                    case.tearDown()

    def test_live_or_unread_owned_process_does_not_become_exit_proof(self):
        self.start()
        with self.assertRaises(ValueError):
            self.observer.evidence()
        self.assertEqual(self.result().result, "blocked")

    def test_inventory_and_context_failures_block(self):
        self.start()
        self.finish()
        for change in (dict(inventory_complete=False), dict(executors=[self.identity["worker"]]),
                       dict(checked_ns=1), dict(checked_ns=2**63 - 1)):
            with self.subTest(change=change):
                self.assertEqual(self.result(lambda: dict(self.probe(), **change)).result, "blocked")
        count = 0
        def changing():
            nonlocal count
            count += 1
            return dict(self.probe(), session="one" if count == 1 else "two")
        self.assertEqual(self.result(changing).result, "blocked")

    def test_record_replaced_after_observation_cannot_be_rebound(self):
        self.start()
        self.finish()
        changed = model.parse(self.raw)
        changed["revision"] += 1
        self.write(self.run_dir / "recovery/record.json", model.encode(changed))
        self.assertEqual(self.result().result, "blocked")
        with self.assertRaises(ValueError):
            self.observer.bind_durable_record(model.encode(changed))
        self.assertEqual(self.result().result, "blocked")

    def test_namespace_change_during_probe_blocks_and_preserves_change(self):
        self.start()
        self.finish()
        def changed():
            self.write(self.marker_dir / "lock", b"unresolved:changed")
            return self.probe()
        self.assertEqual(self.result(changed).result, "blocked")
        self.assertEqual((self.marker_dir / "lock").read_bytes(), b"unresolved:changed")

    def test_new_boot_requires_fresh_probe_and_no_old_trace(self):
        self.start()
        self.finish()
        probe = lambda: dict(self.probe(), boot="different-synthetic-boot")
        self.assertEqual(self.result(probe).result, "blocked")
        result = self.result(probe, observer=False)
        self.assertEqual(result.result, "newBootCandidate", result)
        self.assertFalse(result.restart_eligible)

    def test_report_dictionary_cannot_supply_owned_observation(self):
        self.start()
        self.finish()
        result = check_recovery(self.marker_dir, self.run_dir, self.probe, self.observer.evidence())
        self.assertEqual(result.result, "blocked")

    def test_missing_durable_acknowledgement_cannot_be_filled_from_snapshot(self):
        self.start(bind=False)
        self.finish()
        self.assertEqual(self.result().result, "blocked")
        self.assertIsNone(self.observer.digest)

    def test_early_fence_request_permanently_rejects_evidence(self):
        self.start()
        self.until(lambda: len(self.observer.rows["checkpoints"]) == 2)
        self.children["worker"].stdin.write(b"finish\n")
        self.children["worker"].stdin.flush()
        self.until(lambda: "worker" in self.observer.exits and "worker" in self.observer.streams)
        with self.assertRaises(ValueError):
            self.observer.request_observation()
        with self.assertRaises(ValueError):
            self.observer.pump()
        self.assertEqual(self.result().result, "blocked")

    def test_delayed_pump_cannot_hide_receipt_after_actual_worker_exit(self):
        self.start("delayed-receipt")
        self.children["worker"].wait(timeout=2)
        exit_bound = time.monotonic_ns()
        self.until(lambda: len(self.observer.rows["receipts"]) == 4)
        self.assertGreater(self.observer.rows["receipts"][-1]["ns"], exit_bound)
        with self.assertRaises(ValueError):
            self.observer.bind_durable_record(self.raw)
        self.assertEqual(self.result().result, "blocked")

    def test_bind_before_collecting_boundary_is_rejected(self):
        self.start()
        with self.assertRaises(ValueError):
            self.observer.bind_durable_record(self.raw)
        self.assertEqual(self.result().result, "blocked")

    def test_actual_writer_acknowledgement_binds_collected_boundary(self):
        self.start(bind=False)
        self.until(lambda: len(self.observer.rows["checkpoints"]) == 2
                   and len(self.observer.rows["receipts"]) == 4)
        recovery = self.run_dir / "recovery"
        (recovery / "record.lock").unlink()
        (recovery / "record.json").unlink()
        writer = RecordWriter(recovery)
        def acknowledge(record):
            writer.submit(model.encode(record))
            deadline = time.monotonic() + 3
            while True:
                self.assertLess(time.monotonic(), deadline)
                result = writer.poll()
                if result is not None:
                    self.assertIsNone(result.error)
                    return result.data
                time.sleep(0.001)
        try:
            record = model.new_record(self.identity)
            acknowledge(record)
            # Replay storage transitions for this completed synthetic fixture;
            # dispatch admission ordering belongs to test_recovery_integration.
            for tag in (1001, 1003):
                record = model.reserve_pair(record, tag)
                acknowledge(record)
                count = record["sequence"]
                actual = [{key: row[key] for key in ("sequence", "tag", "kind")}
                          for row in self.observer.rows["receipts"][:count]]
                checkpoint = self.observer.rows["checkpoints"][count // 2 - 1]
                record = model.checkpoint(record, dict(identity=self.identity, sequence=count,
                                                        tag=checkpoint["tag"], held=checkpoint["held"],
                                                        receipts=actual))
                ack = acknowledge(record)
            self.observer.bind_durable_record(ack)
        finally:
            writer.close()
            self.assertTrue(writer.finished.wait(3))
        self.finish()
        self.assertEqual(self.result().result, "sameBootCandidate")


if __name__ == "__main__":
    unittest.main()
