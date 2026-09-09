"""Native supervisor fault sequencing with substituted children; no native launch."""
import json
import unittest

import test_focus_supervisor as fixture
from supervisor import valid_checkpoint


class CrashTransport(fixture.SyntheticTransport):
    def __init__(self, missing_post=False, missing_fence=False, checkpoint_fault=None):
        super().__init__()
        self.missing_post, self.missing_crash_fence = missing_post, missing_fence
        self.kill_evidence = []
        self.commands = []
        self.checkpoint_fault = checkpoint_fault

    def popen(self, *args, **kwargs):
        peer = super().popen(*args, **kwargs)
        original = peer.kill

        def kill():
            self.kill_evidence.append((peer.name, list(self.delivered)))
            original()

        peer.kill = kill
        return peer

    def write(self, fd, data):
        peer = next((p for p in self.peers.values() if p.stdin.fileno() == fd), None)
        if peer:
            row = json.loads(data)
            self.commands.append((peer.name, row))
            if row["op"] == "observeEnd":
                if not self.missing_crash_fence:
                    self.emit("target", "observationComplete", pid=self.peers['target'].pid,
                              isActive=True, frontmostPID=self.peers['target'].pid)
                return len(data)
        count = super().write(fd, data)
        if peer and row["op"] == "event" and row["sequence"] == 12:
            queue = self.queues[self.peers["worker"].stdout.fileno()]
            checkpoint = queue.pop()
            if self.missing_post:
                queue.pop()  # Last up receipt/checkpoint exist, but posting is absent.
            fault = self.checkpoint_fault
            if fault == "run":
                checkpoint["run"] = "another-run"
            elif fault == "held":
                checkpoint["heldKeysEmpty"] = False
            elif fault == "stale":
                checkpoint["sequence"] = 10
            elif fault == "tag":
                checkpoint["tag"] -= 1
            if fault != "missing":
                queue.append(checkpoint)
            if fault == "duplicate":
                queue.append(checkpoint)
        return count


class WorkerCrashTests(unittest.TestCase):
    def execute(self, **options):
        rig = CrashTransport(**options)
        return fixture.FocusSupervisorTests().run_transport(
            rig=rig, focus_loss=False, worker_crash=True)

    def test_six_complete_pairs_before_owned_kill_and_full_mirror_after_teardown(self):
        rig, code, trace, marker = self.execute()
        self.assertEqual(code, 2)
        self.assertEqual(marker, b"unresolved")
        self.assertEqual(len(rig.kill_evidence), 1)
        role, delivered = rig.kill_evidence[0]
        self.assertEqual(role, "worker")
        posts = {r["tag"] for source, r in delivered if source == "worker" and r["event"] == "posted"}
        receipts = {r["tag"] for source, r in delivered if source == "target"
                    and r["event"] in ("keyDown", "keyUp")}
        self.assertEqual(len(posts), 12)
        self.assertEqual(posts, receipts)
        checkpoints = [r for source, r in delivered if source == "worker" and r["event"] == "checkpoint"]
        self.assertEqual(checkpoints[-1]["sequence"], 12)
        self.assertIsInstance(checkpoints[-1]["run"], str)
        self.assertTrue(checkpoints[-1]["heldKeysEmpty"])
        self.assertEqual(len([r for _, r in rig.commands if r["op"] == "event"]), 12)
        injection = next(r for r in trace if r["event"] == "workerCrashInjected")
        stop = next(r for r in trace if r["event"] == "stopping")
        self.assertEqual(stop["reason"], "workerExited")
        self.assertLessEqual(int(injection["beforeNs"]), int(injection["afterNs"]))
        self.assertLessEqual(int(injection["afterNs"]), int(stop["detectionNs"]))
        events = [r["event"] for r in trace]
        self.assertLess(events.index("observationComplete"), events.index("targetExited"))
        self.assertEqual(next(r for r in trace if r["event"] == "workerExited")["exitCode"], -9)
        self.assertEqual([r["row"] for r in rig.outputs if r["event"] == "recoveryTrace"], trace)
        self.assertEqual(rig.outputs[-1], {"event": "recoveryTraceSaved", "rows": len(trace)})
        result = next(r for r in rig.outputs if r["event"] == "result")
        self.assertFalse(result["drainVerified"])
        self.assertTrue(result["crashInjected"])
        self.assertFalse(result["restartEligible"])
        self.assertFalse(rig.peers["target"].killed)

    def test_missing_last_post_never_injects_crash(self):
        rig, code, trace, marker = self.execute(missing_post=True)
        self.assertEqual(code, 2)
        self.assertEqual(marker, b"unresolved")
        self.assertFalse(rig.kill_evidence)
        self.assertFalse(any(r["event"] == "workerCrashInjected" for r in trace))

    def test_missing_fence_keeps_observation_incomplete(self):
        _, code, trace, marker = self.execute(missing_fence=True)
        self.assertEqual(code, 2)
        self.assertEqual(marker, b"unresolved")
        self.assertIn("observationFenceTimeout", [r["event"] for r in trace])
        self.assertNotIn("observationComplete", [r["event"] for r in trace])

    def test_missing_or_invalid_checkpoint_prevents_controlled_crash(self):
        for fault in ("missing", "run", "held", "stale", "tag"):
            with self.subTest(fault=fault):
                rig, code, trace, marker = self.execute(checkpoint_fault=fault)
                self.assertEqual(code, 2)
                self.assertEqual(marker, b"unresolved")
                self.assertFalse(any(r["event"] == "workerCrashInjected" for r in trace))
                self.assertEqual(len([r for _, r in rig.commands if r["op"] == "event"]), 12)

    def test_checkpoint_parser_rejects_duplicate_boundary_and_ambiguous_types(self):
        row = dict(event="checkpoint", ns="123", run="a" * 32, sequence=12,
                   tag=1012, heldKeysEmpty=True)
        self.assertTrue(valid_checkpoint(row, "a" * 32, 12, 1012, 10))
        self.assertFalse(valid_checkpoint(row, "a" * 32, 12, 1012, 12))
        for change in (dict(tag=True), dict(sequence=True), dict(heldKeysEmpty=1),
                       dict(source="target"), dict(extra="field")):
            self.assertFalse(valid_checkpoint(dict(row, **change), "a" * 32, 12, 1012, 10))

    def test_early_bound_cannot_bypass_recovery_setup(self):
        class EarlyBound(CrashTransport):
            def popen(self, *args, **kwargs):
                peer = super().popen(*args, **kwargs)
                if peer.name == "worker":
                    self.queues[peer.stdout.fileno()].appendleft(dict(event="bound", ns=str(self.ns)))
                return peer

        rig = EarlyBound()
        _, code, trace, _ = fixture.FocusSupervisorTests().run_transport(
            rig=rig, focus_loss=False, worker_crash=True)
        self.assertEqual(code, 2)
        self.assertFalse(any(r["op"] == "event" for _, r in rig.commands))
        self.assertEqual(next(r for r in trace if r["event"] == "stopping")["reason"], "unexpectedWorkerBound")

    def test_wrong_receipt_kind_or_duplicate_post_cannot_resolve(self):
        for fault in ("kind", "duplicate-post"):
            class BadEvidence(CrashTransport):
                def write(self, fd, data):
                    count = super().write(fd, data)
                    row = json.loads(data)
                    if row.get("op") == "event" and row["sequence"] == 2:
                        if fault == "kind":
                            self.queues[self.peers["target"].stdout.fileno()][-1]["event"] = "keyDown"
                        else:
                            queue = self.queues[self.peers["worker"].stdout.fileno()]
                            checkpoint = queue.pop()
                            queue.append(dict(queue[-1]))
                            queue.append(checkpoint)
                    return count

            with self.subTest(fault=fault):
                rig = BadEvidence()
                _, code, trace, _ = fixture.FocusSupervisorTests().run_transport(
                    rig=rig, focus_loss=False, worker_crash=True)
                self.assertEqual(code, 2)
                self.assertFalse(any(r["event"] == "workerCrashInjected" for r in trace))
                self.assertEqual(next(r for r in trace if r["event"] == "stopping")["reason"],
                                 "harnessError" if fault == 'kind' else "recordCheckpointMismatch")


if __name__ == "__main__":
    unittest.main()
