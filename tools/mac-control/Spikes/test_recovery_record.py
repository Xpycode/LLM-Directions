"""Offline model tests; synthetic evidence is not OS identity or quiescence proof."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

import recovery_record as model


def identity():
    return dict(boot="boot-1", session="login-1", run="run-1",
                worker=dict(pid=101, start="start-1", code="a" * 64),
                target=dict(pid=102, start="start-2", code="b" * 64))


def event(sequence):
    return dict(sequence=sequence, tag=1000 + sequence,
                kind="down" if sequence % 2 else "up")


def evidence(record):
    return dict(identity=identity(), sequence=record["sequence"],
                tag=record["events"][-1]["tag"], held=[],
                receipts=copy.deepcopy(record["events"]))


class RecoveryRecordTests(unittest.TestCase):
    def acknowledged(self, gate, record):
        request = gate.stage(record)
        # Stand-in storage adapter: real isolated file, explicit simulated ack.
        # This does not test crash durability or an asynchronous runtime writer.
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "record.json"
            path.write_bytes(request)
            gate.acknowledge(path.read_bytes())

    def pair(self):
        gate = model.WriteGate(model.new_record(identity()))
        self.acknowledged(gate, model.admit(gate.record, event(1)))
        gate.consume_dispatch()
        self.acknowledged(gate, model.admit(gate.record, event(2)))
        gate.consume_dispatch()
        return gate

    def test_uncertainty_must_be_acknowledged_before_dispatch(self):
        gate = model.WriteGate(model.new_record(identity()))
        self.assertFalse(gate.dispatch_ready)
        data = gate.stage(model.admit(gate.record, event(1)))
        self.assertFalse(gate.dispatch_ready)
        gate.acknowledge(data)
        self.assertTrue(gate.dispatch_ready)
        self.assertEqual(gate.record["state"], "uncertain")
        gate.consume_dispatch()
        self.assertFalse(gate.dispatch_ready)
        with self.assertRaises(ValueError):
            gate.consume_dispatch()

    def test_complete_checkpoint_is_only_a_candidate_after_exit_and_observation(self):
        gate = self.pair()
        resolved = model.checkpoint(gate.record, evidence(gate.record))
        self.acknowledged(gate, resolved)
        self.assertFalse(gate.dispatch_ready)
        proof = dict(identity=identity(), worker_exited=True, target_exited=True,
                     observation_complete=True, sequence=2, tag=1002)
        self.assertTrue(model.recovery_candidate(gate.record, proof))
        for field in ("worker_exited", "target_exited", "observation_complete"):
            bad = dict(proof, **{field: False})
            self.assertFalse(model.recovery_candidate(gate.record, bad))
        bad = copy.deepcopy(proof)
        bad["identity"]["worker"]["start"] = "reused-pid"
        self.assertFalse(model.recovery_candidate(gate.record, bad))

    def test_posted_or_unreturned_key_up_cannot_resolve(self):
        gate = self.pair()
        for bad in ({"posted": True}, dict(evidence(gate.record), held=[0]),
                    dict(evidence(gate.record), sequence=1)):
            with self.assertRaises(ValueError):
                model.checkpoint(gate.record, bad)

    def test_stale_mismatched_and_duplicate_evidence_rejected(self):
        gate = self.pair()
        good = evidence(gate.record)
        variants = [dict(good, tag=999), dict(good, receipts=good["receipts"] * 2),
                    dict(good, receipts=good["receipts"][:-1])]
        for field in ("run", "boot", "session"):
            bad = copy.deepcopy(good)
            bad["identity"][field] = "other"
            variants.append(bad)
        for bad in variants:
            with self.assertRaises(ValueError):
                model.checkpoint(gate.record, bad)
        later = model.admit(gate.record, event(3))
        with self.assertRaises(ValueError):
            model.checkpoint(later, good)

    def test_legacy_corrupt_unknown_and_extra_data_block(self):
        valid = model.new_record(identity())
        bad_records = []
        for key, value in (("version", 2), ("version", True), ("state", "clean"),
                           ("payload", "forbidden"), ("sequence", True)):
            bad_records.append(dict(valid, **{key: value}))
        for field in ("boot", "session", "run"):
            bad = copy.deepcopy(valid)
            bad["identity"][field] = ""
            bad_records.append(bad)
        bad = copy.deepcopy(valid)
        bad["identity"]["worker"]["start"] = ""
        bad_records.append(bad)
        for raw in [b"", b"clean", b"unresolved", b"{", b"null",
                    b'{"version":1,"version":1}', b"[" * 2000,
                    b" " * (model.MAX_BYTES + 1)] + [json.dumps(r).encode() for r in bad_records]:
            with self.subTest(raw=raw[:80]), self.assertRaises(ValueError):
                model.parse(raw)

    def test_round_trip_and_invalid_internal_boundaries(self):
        gate = self.pair()
        self.assertEqual(model.parse(model.encode(gate.record)), gate.record)
        for key, value in (("sequence", 9), ("checkpoint", 2), ("state", "resolved")):
            with self.assertRaises(ValueError):
                model.encode(dict(gate.record, **{key: value}))
        for change in (dict(sequence=4), dict(tag=1001), dict(kind="down")):
            with self.assertRaises(ValueError):
                model.admit(model.admit(model.new_record(identity()), event(1)),
                            dict(event(2), **change))

    def test_failed_write_and_stop_reject_late_ack(self):
        for stop in (False, True):
            gate = self.pair()
            data = gate.stage(model.checkpoint(gate.record, evidence(gate.record)))
            gate.stop() if stop else gate.write_failed()
            with self.assertRaises(ValueError):
                gate.acknowledge(data)
            self.assertFalse(gate.dispatch_ready)
            self.assertEqual(gate.record["state"], "uncertain")
            with self.assertRaises(ValueError):
                gate.stage(model.admit(gate.record, event(3)))

    def test_wrong_ack_or_overlapping_write_closes_admission(self):
        for fault in ("wrong", "overlap"):
            gate = self.pair()
            next_record = model.admit(gate.record, event(3))
            gate.stage(next_record)
            with self.assertRaises(ValueError):
                if fault == "wrong":
                    gate.acknowledge(model.encode(gate.record))
                else:
                    gate.stage(next_record)
            self.assertFalse(gate.dispatch_ready)

    def test_loaded_resolved_record_does_not_authorize_replay(self):
        gate = self.pair()
        resolved = model.checkpoint(gate.record, evidence(gate.record))
        loaded = model.WriteGate(model.parse(model.encode(resolved)))
        self.assertFalse(loaded.dispatch_ready)
        with self.assertRaises(ValueError):
            loaded.stage(resolved)

    def test_failed_admission_write_cannot_restore_old_resolved_boundary(self):
        gate = self.pair()
        self.acknowledged(gate, model.checkpoint(gate.record, evidence(gate.record)))
        data = gate.stage(model.admit(gate.record, event(3)))
        gate.write_failed()
        self.assertEqual(gate.record["state"], "uncertain")
        self.assertEqual(gate.record["sequence"], 3)
        self.assertEqual(gate.record["checkpoint"], 2)
        self.assertFalse(gate.dispatch_ready)
        with self.assertRaises(ValueError):
            gate.acknowledge(data)

    def test_unused_dispatch_permit_cannot_be_overwritten(self):
        gate = model.WriteGate(model.new_record(identity()))
        self.acknowledged(gate, model.admit(gate.record, event(1)))
        with self.assertRaises(ValueError):
            gate.stage(model.admit(gate.record, event(2)))
        self.assertFalse(gate.dispatch_ready)

    def test_records_and_snapshots_do_not_alias_caller_data(self):
        original = identity()
        record = model.new_record(original)
        original["run"] = "changed"
        gate = model.WriteGate(record)
        record["identity"]["run"] = "changed"
        snapshot = gate.record
        snapshot["identity"]["run"] = "changed"
        self.assertEqual(gate.record["identity"], identity())

    def test_receipt_boolean_is_not_sequence_one(self):
        gate = self.pair()
        bad = evidence(gate.record)
        bad["receipts"][0]["sequence"] = True
        with self.assertRaises(ValueError):
            model.checkpoint(gate.record, bad)


if __name__ == "__main__":
    unittest.main()
