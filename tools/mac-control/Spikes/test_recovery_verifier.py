"""Synthetic normalized evidence; no native processes, runtime locks or markers.

Fixtures start at the public offline verifier API. They do not bypass a native
adapter: that adapter has deliberately not been implemented or authorized yet.
"""
import copy
import hashlib
import json
from pathlib import Path
import unittest

import recovery_record as model
from recovery_verifier import OBSERVATION_NS, verify
from test_recovery_record import identity


def fixture():
    record = model.new_record(identity())
    for tag in (1001, 1003):
        record = model.reserve_pair(record, tag)
        record = model.checkpoint(record, dict(
            identity=identity(), sequence=record["sequence"], tag=tag + 1,
            held=[], receipts=copy.deepcopy(record["events"])))
    raw = model.encode(record)
    context = dict(boot="boot-1", session="login-1", checked_ns=OBSERVATION_NS + 200,
                   inventory_complete=True, executors=[])
    evidence = dict(
        identity=identity(), record_sha256=hashlib.sha256(raw).hexdigest(),
        posts=[dict(event, ns=10 * event["sequence"]) for event in record["events"]],
        receipts=[dict(event, ns=10 * event["sequence"] + 1, origin_pid=101)
                  for event in record["events"]],
        checkpoints=[dict(run="run-1", sequence=seq, tag=1000 + seq, held=[], ns=seq * 10 + 2)
                     for seq in (2, 4)],
        exits={role: dict(identity=identity()[role], status=-9 if role == "worker" else 0,
                          ns=100 if role == "worker" else OBSERVATION_NS + 130,
                          method="ownedWait") for role in ("worker", "target")},
        streams={role: dict(complete=True, eof_ns=101 if role == "worker" else OBSERVATION_NS + 140)
                 for role in ("worker", "target")},
        fence=dict(run="run-1", target=identity()["target"], requested_ns=OBSERVATION_NS + 101,
                   acknowledged_ns=OBSERVATION_NS + 120), end_ns=OBSERVATION_NS + 150)
    return [b"unresolved:run-1", raw, context, evidence]


class RecoveryVerifierTests(unittest.TestCase):
    def blocked(self, args):
        result = verify(*args)
        self.assertEqual(result.result, "blocked", result)
        self.assertFalse(result.restart_eligible)
        self.assertFalse(result.native_recovery_verified)

    def test_complete_evidence_is_only_read_only_candidate(self):
        args = fixture()
        before = copy.deepcopy(args)
        result = verify(*args)
        self.assertEqual(result.result, "sameBootCandidate", result)
        self.assertFalse(result.restart_eligible)
        self.assertFalse(result.native_recovery_verified)
        self.assertEqual(args, before)

    def test_legacy_missing_corrupt_and_unbound_markers(self):
        for marker in (b"", b"clean", b"unresolved", b"unresolved:other", b"unresolved:run-1\n", None):
            with self.subTest(marker=marker):
                args = fixture()
                args[0] = marker
                self.blocked(args)
        for raw in (None, b"", b"unresolved", b"{", b"null", b"[" * 2000,
                    b'{"version":1,"version":1}', b" " * (model.MAX_BYTES + 1)):
            args = fixture()
            args[1] = raw
            self.blocked(args)

    def test_every_required_field_is_required(self):
        for index in (2, 3):
            for key in fixture()[index]:
                with self.subTest(index=index, key=key):
                    args = fixture()
                    del args[index][key]
                    self.blocked(args)

    def test_identity_mismatch_and_pid_reuse(self):
        for field in ("boot", "session", "run"):
            args = fixture()
            args[3]["identity"][field] = "other"
            self.blocked(args)
        for role in ("worker", "target"):
            for field, value in (("pid", 999), ("start", "reused"), ("code", "c" * 64)):
                args = fixture()
                args[3]["exits"][role]["identity"][field] = value
                self.blocked(args)

    def test_same_boot_session_change_is_not_boot_proof(self):
        args = fixture()
        args[2]["session"] = "new-session"
        self.blocked(args)

    def test_inventory_requires_complete_empty_result(self):
        for boot in ("boot-1", "boot-2"):
            for field, value in (("inventory_complete", False), ("inventory_complete", 1),
                                 ("executors", [identity()["worker"]]), ("executors", None)):
                args = fixture()
                args[2].update(boot=boot, **{field: value})
                if boot == "boot-2":
                    args[3] = None
                self.blocked(args)

    def test_new_boot_handles_uncertain_boundary_without_reusing_old_clock(self):
        args = fixture()
        uncertain = model.reserve_pair(model.parse(args[1]), 1005)
        args[1] = model.encode(uncertain)
        args[2].update(boot="boot-2", session="login-2", checked_ns=1)
        args[3] = None
        result = verify(*args)
        self.assertEqual(result.result, "newBootCandidate", result)
        self.assertFalse(result.restart_eligible)
        self.assertFalse(result.native_recovery_verified)
        args[2]["boot"] = "boot-1"
        self.blocked(args)

    def test_new_boot_does_not_upgrade_legacy_or_mix_traces(self):
        args = fixture()
        args[2]["boot"] = "boot-2"
        self.blocked(args)
        args[3] = None
        args[0] = b"unresolved"
        self.blocked(args)
        args[0] = b"unresolved:run-1"
        args[1] = b"{}"
        self.blocked(args)

    def test_prepared_uncertain_or_newer_admission_blocks_same_boot(self):
        for record in (model.new_record(identity()),
                       model.reserve_pair(model.new_record(identity()), 1001),
                       model.reserve_pair(model.parse(fixture()[1]), 1005)):
            args = fixture()
            args[1] = model.encode(record)
            args[3]["record_sha256"] = hashlib.sha256(args[1]).hexdigest()
            self.blocked(args)

    def test_exact_raw_record_snapshot_binding(self):
        args = fixture()
        args[1] = json.dumps(model.parse(args[1]), indent=2).encode()
        self.blocked(args)

    def test_receipts_and_posts_preserve_kind_order_origin_and_multiplicity(self):
        for stream in ("posts", "receipts"):
            for fault in ("missing", "duplicate", "reverse", "kind", "tag", "boolean", "late"):
                with self.subTest(stream=stream, fault=fault):
                    args = fixture()
                    rows = args[3][stream]
                    if fault == "missing":
                        rows.pop()
                    elif fault == "duplicate":
                        rows.append(copy.deepcopy(rows[-1]))
                    elif fault == "reverse":
                        rows.reverse()
                    elif fault == "late":
                        rows[-1]["ns"] = args[3]["end_ns"] + 1
                    else:
                        key, value = {"kind": ("kind", "up"), "tag": ("tag", 999),
                                      "boolean": ("sequence", True)}[fault]
                        rows[0][key] = value
                    self.blocked(args)
        args = fixture()
        args[3]["receipts"][0]["origin_pid"] = 102
        self.blocked(args)

    def test_checkpoint_cannot_be_inferred_from_post_or_stale_pair(self):
        for fault in ("missing", "duplicate", "held", "early", "stale", "wrong-run"):
            args = fixture()
            rows = args[3]["checkpoints"]
            if fault == "missing":
                rows.pop()
            elif fault == "duplicate":
                rows.append(copy.deepcopy(rows[-1]))
            else:
                key, value = {"held": ("held", [0]), "early": ("ns", 39),
                              "stale": ("sequence", 2), "wrong-run": ("run", "other")}[fault]
                rows[-1][key] = value
            self.blocked(args)

    def test_exit_and_stream_closure_required_not_pid_absence(self):
        for role in ("worker", "target"):
            for key, value in (("method", "pidAbsent"), ("status", None), ("status", True), ("ns", 1)):
                args = fixture()
                args[3]["exits"][role][key] = value
                self.blocked(args)
            args = fixture()
            args[3]["streams"][role]["complete"] = False
            self.blocked(args)
        args = fixture()
        args[3]["exits"]["target"]["status"] = 1
        self.blocked(args)

    def test_fence_duration_boundary_order_and_identity(self):
        for key, value in (("requested_ns", OBSERVATION_NS + 100),
                           ("acknowledged_ns", OBSERVATION_NS + 99),
                           ("acknowledged_ns", OBSERVATION_NS + 131), ("run", "other")):
            args = fixture()
            args[3]["fence"][key] = value
            self.blocked(args)
        args = fixture()
        args[3]["fence"]["target"]["start"] = "reused"
        self.blocked(args)
        args = fixture()
        args[3]["fence"]["requested_ns"] += 1
        self.assertEqual(verify(*args).result, "sameBootCandidate")

    def test_future_boolean_and_reversed_timestamps(self):
        for value in (True, 0, -1, 2**63, "1", None):
            args = fixture()
            args[3]["end_ns"] = value
            self.blocked(args)
        args = fixture()
        args[2]["checked_ns"] = args[3]["end_ns"] - 1
        self.blocked(args)
        args = fixture()
        args[3]["posts"][0]["ns"] = 25
        self.blocked(args)

    def test_late_receipt_before_fence_still_blocks(self):
        args = fixture()
        args[3]["receipts"][-1]["ns"] = args[3]["exits"]["worker"]["ns"] + 1
        self.blocked(args)

    def test_receipt_can_precede_post_acknowledgement(self):
        args = fixture()
        for row in args[3]["receipts"]:
            row["ns"] -= 2
        self.assertEqual(verify(*args).result, "sameBootCandidate")

    def test_next_pair_receipt_cannot_precede_previous_checkpoint(self):
        args = fixture()
        for row, ns in zip(args[3]["receipts"], (1, 2, 3, 4)):
            row["ns"] = ns
        self.blocked(args)

    def test_retained_native_report_cannot_retroactively_supply_record(self):
        path = Path(__file__).resolve().parents[3] / "verification/mac-control/worker-crash-2026-09-09.json"
        raw = path.read_bytes()
        args = fixture()
        args[0], args[1] = b"unresolved", raw
        self.blocked(args)
        self.assertEqual(path.read_bytes(), raw)


if __name__ == "__main__":
    unittest.main()
