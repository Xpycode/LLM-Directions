"""Isolated real-filesystem bootstrap tests; never touch the native namespace."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import recovery_bootstrap as bootstrap
from recovery_snapshot import MarkerLock, fingerprint


class BootstrapTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve() / "marker"
        self.root.mkdir(mode=0o700)
        self.marker = self.root / "lock"
        self.marker.write_bytes(b"unresolved")
        self.marker.chmod(0o600)
        self.history = b"original crash: failed, missing ledger; outcome unknown"
        self.history_path = Path(self.temp.name) / "history"
        self.history_path.write_bytes(self.history)
        self.owner = MarkerLock.acquire(self.root)
        self.addCleanup(self.owner.close)
        self.boot = "11111111-1111-1111-1111-111111111111"
        self.now = 100
        self.raw = bootstrap.capture_baseline(self.owner, observe=self.observe,
                                              clock=lambda: self.now,
                                              provenance="isolated fixture capture")
        # This pin represents the test harness's external trust store, not a
        # self-authenticating field in the report being loaded.
        self.pin = bootstrap.digest(self.raw)
        self.baseline = bootstrap.load_baseline(self.raw, trusted_sha256=self.pin,
                                               provenance="test harness retained pin")
        self.boot = "22222222-2222-2222-2222-222222222222"
        self.now = 200

    def observe(self):
        return dict(boot=self.boot, session="fixture-session", checked_ns=self.now,
                    inventory_complete=True, executors=[])

    def initialize(self, **kwargs):
        args = dict(observe=self.observe, clock=lambda: self.now,
                    history=self.history, trusted_history_sha256=bootstrap.digest(self.history))
        args.update(kwargs)
        return bootstrap.initialize_fenced(self.owner, self.baseline, **args)

    def test_success_retains_evidence_inode_lock_and_permanent_fence(self):
        identity = self.marker.stat().st_ino
        result = self.initialize()
        self.assertEqual(result["result"], "initializedFenced")
        self.assertFalse(result["launch_eligible"])
        self.assertFalse(result["native_recovery_verified"])
        self.assertEqual(self.marker.read_bytes(), b"clean")
        self.assertEqual(self.marker.stat().st_ino, identity)
        self.assertEqual(self.history_path.read_bytes(), self.history)
        self.assertEqual(bytes.fromhex(result["history_hex"]), self.history)
        self.assertEqual(bytes.fromhex(result["baseline_hex"]), self.raw)
        self.assertEqual(set(result).intersection({"run", "capability", "events"}), set())
        self.assertEqual(json.loads((self.root / bootstrap.ARTIFACTS[2]).read_bytes()), result)
        self.assertTrue(all((self.root / name).exists() for name in bootstrap.ARTIFACTS))
        with self.assertRaisesRegex(ValueError, "snapshotBusy"):
            MarkerLock.acquire(self.root)
        with self.assertRaises(ValueError):
            self.initialize()

    def test_capture_read_only(self):
        self.boot = "11111111-1111-1111-1111-111111111111"
        before = fingerprint(self.root.stat()), fingerprint(self.marker.stat())
        bootstrap.capture_baseline(self.owner, observe=self.observe, clock=lambda: self.now,
                                   provenance="another independent capture")
        self.assertEqual(before, (fingerprint(self.root.stat()), fingerprint(self.marker.stat())))
        self.assertEqual(list(self.root.iterdir()), [self.marker])

    def test_committed_audit_binds_post_initialization_marker(self):
        result = self.initialize()
        self.assertEqual(result["schema"], "legacyBootstrap/v2")
        self.assertEqual(result["initialized_marker_stamp"],
                         json.loads(bootstrap.encode(fingerprint(self.marker.stat()))))
        pending = json.loads((self.root / bootstrap.ARTIFACTS[0]).read_bytes())
        self.assertNotIn("initialized_marker_stamp", pending)
        self.assertEqual(dict(result, result="pending", initialized_marker_stamp=None),
                         dict(pending, initialized_marker_stamp=None))

    def test_clean_marker_rewrite_after_initialization_is_not_continuity(self):
        for stage in ["markerFlushed", "committedCreated", "committedWritten",
                      "committedFlushed", "committedPublished", "committedDirectoryFlushed"]:
            with self.subTest(stage=stage):
                fixture = BootstrapTests("test_capture_read_only")
                fixture.setUp()
                try:
                    def boundary(current):
                        if current == stage:
                            fixture.owner.write_marker(b"unresolved:intervening-run")
                            fixture.owner.write_marker(b"clean")
                            # Make the metadata change deterministic even on a
                            # filesystem with coarse modification timestamps.
                            info = fixture.marker.stat()
                            os.utime(fixture.marker, ns=(info.st_atime_ns, info.st_mtime_ns + 1))
                    with self.assertRaisesRegex(ValueError, "interveningStateChange"):
                        fixture.initialize(boundary=boundary)
                    self.assertTrue((fixture.root / bootstrap.ARTIFACTS[0]).exists())
                    self.assertEqual(fixture.history_path.read_bytes(), fixture.history)
                finally:
                    fixture.doCleanups()

    def test_same_boot_even_changed_session_blocks(self):
        self.boot = "11111111-1111-1111-1111-111111111111"
        with self.assertRaisesRegex(ValueError, "sameBoot"):
            self.initialize(observe=lambda: dict(self.observe(), session="new-session"))
        self.assertEqual(self.marker.read_bytes(), b"unresolved")

    def test_bad_inventory_context_unknown_boot_and_stale_samples(self):
        changes = [dict(inventory_complete=False), dict(executors=[{"pid": 1}]),
                   dict(executors=None), dict(boot="unknown"), dict(boot=""),
                   dict(boot="00000000-0000-0000-0000-000000000000"),
                   dict(checked_ns=199), dict(checked_ns=201), dict(session="")]
        for change in changes:
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.initialize(observe=lambda: dict(self.observe(), **change))
        self.assertEqual(self.marker.read_bytes(), b"unresolved")

    def test_unreadable_inventory_propagates_and_leaves_marker(self):
        with self.assertRaises(OSError):
            self.initialize(observe=lambda: (_ for _ in ()).throw(OSError("unreadable")))
        self.assertEqual(self.marker.read_bytes(), b"unresolved")

    def test_context_drift(self):
        count = 0
        def observe():
            nonlocal count
            count += 1
            return dict(self.observe(), session=str(count))
        with self.assertRaisesRegex(ValueError, "contextDrift"):
            self.initialize(observe=observe)

    def test_untrusted_missing_corrupt_and_mutated_baseline(self):
        for raw, pin, provenance in [(self.raw, "0" * 64, "external"),
                                     (b"", self.pin, "external"),
                                     (b"{", bootstrap.digest(b"{"), "external"),
                                     (self.raw, self.pin, "")]:
            with self.subTest(raw=raw[:10]), self.assertRaises(ValueError):
                bootstrap.load_baseline(raw, trusted_sha256=pin, provenance=provenance)
        self.baseline = bootstrap.TrustedBaseline(self.raw + b" ", self.pin, "external")
        with self.assertRaisesRegex(ValueError, "untrustedEvidence"):
            self.initialize()

    def test_history_missing_or_untrusted(self):
        for kwargs in [dict(history=b""), dict(trusted_history_sha256="0" * 64)]:
            with self.assertRaises(ValueError):
                self.initialize(**kwargs)
        self.assertEqual(self.marker.read_bytes(), b"unresolved")

    def test_retained_native_report_loader_and_inconsistent_samples(self):
        # Read only repository evidence; this neither accesses its marker path
        # nor promotes a hash computed here into a real native trust decision.
        path = Path(__file__).resolve().parents[3] / "verification/mac-control/native-context-2026-09-09.json"
        raw = path.read_bytes()
        loaded = bootstrap.load_baseline(raw, trusted_sha256=bootstrap.digest(raw),
                                        provenance="offline parser fixture only")
        self.assertEqual(loaded.raw, raw)
        data = json.loads(raw)
        data["metadataVerification"]["contextSamples"][0]["boot"] = self.boot
        changed = bootstrap.encode(data)
        with self.assertRaisesRegex(ValueError, "contextDrift"):
            bootstrap.load_baseline(changed, trusted_sha256=bootstrap.digest(changed),
                                    provenance="offline inconsistent fixture")
        with self.assertRaisesRegex(ValueError, "untrustedEvidence"):
            bootstrap.load_baseline(changed, trusted_sha256=bootstrap.digest(raw),
                                    provenance="offline pinned original")

    def test_marker_admission_and_restoration_detected(self):
        self.owner.write_marker(b"unresolved:new-admission")
        self.owner.write_marker(b"unresolved")
        with self.assertRaisesRegex(ValueError, "baselineContinuityLost"):
            self.initialize()

    def test_namespace_change_detected(self):
        (self.root / "intervening-run").write_bytes(b"evidence")
        with self.assertRaisesRegex(ValueError, "baselineContinuityLost"):
            self.initialize()

    def test_replaced_marker_detected(self):
        replacement = self.root / "replacement"
        replacement.write_bytes(b"unresolved")
        replacement.chmod(0o600)
        replacement.replace(self.marker)
        with self.assertRaises(ValueError):
            self.initialize()

    def test_namespace_permissions_and_closed_owner(self):
        self.root.chmod(0o755)
        with self.assertRaises(ValueError):
            self.initialize()
        self.root.chmod(0o700)
        self.owner.close()
        with self.assertRaises(ValueError):
            self.initialize()

    def test_intervening_admission_after_samples(self):
        def boundary(stage):
            if stage == "verified":
                self.owner.write_marker(b"unresolved:admitted")
        with self.assertRaisesRegex(ValueError, "interveningStateChange"):
            self.initialize(boundary=boundary)
        self.assertFalse((self.root / bootstrap.ARTIFACTS[0]).exists())

    def test_stale_during_durable_preparation_stays_fenced(self):
        def boundary(stage):
            if stage == "pendingDirectoryFlushed":
                self.now += bootstrap.WINDOW_NS + 1
        with self.assertRaisesRegex(ValueError, "staleContext"):
            self.initialize(boundary=boundary)
        self.assertEqual(self.marker.read_bytes(), b"unresolved")
        self.assertTrue((self.root / bootstrap.ARTIFACTS[0]).exists())

    def test_fault_at_each_boundary_never_removes_fence(self):
        stages = ["verified", "pendingCreated", "pendingWritten", "pendingFlushed",
                  "pendingDirectoryFlushed", "markerFlushed", "committedCreated",
                  "committedWritten", "committedFlushed", "committedPublished",
                  "committedDirectoryFlushed"]
        for stage in stages:
            with self.subTest(stage=stage):
                fixture = BootstrapTests("test_capture_read_only")
                fixture.setUp()
                try:
                    def boundary(current):
                        if current == stage:
                            raise OSError("simulated crash")
                    with self.assertRaises(OSError):
                        fixture.initialize(boundary=boundary)
                    if stage == "verified":
                        self.assertEqual(fixture.marker.read_bytes(), b"unresolved")
                    else:
                        self.assertTrue((fixture.root / bootstrap.ARTIFACTS[0]).exists())
                    self.assertEqual(fixture.history_path.read_bytes(), fixture.history)
                finally:
                    fixture.doCleanups()

    def test_real_write_and_flush_failures_stay_blocked(self):
        for target in ["os.write", "flush_file", "flush_directory", "os.link"]:
            with self.subTest(target=target):
                fixture = BootstrapTests("test_capture_read_only")
                fixture.setUp()
                try:
                    with patch("recovery_bootstrap." + target, side_effect=OSError("disk fault")):
                        with self.assertRaises(OSError):
                            fixture.initialize()
                    self.assertTrue((fixture.root / bootstrap.ARTIFACTS[0]).exists())
                finally:
                    fixture.doCleanups()

    def test_artifact_deletion_replacement_and_mutation_rejected(self):
        for stage, name in [("pendingFlushed", bootstrap.ARTIFACTS[0]),
                            ("pendingDirectoryFlushed", bootstrap.ARTIFACTS[0]),
                            ("committedFlushed", bootstrap.ARTIFACTS[1])]:
            for operation in ["delete", "replace", "mutate"]:
                with self.subTest(stage=stage, operation=operation):
                    fixture = BootstrapTests("test_capture_read_only")
                    fixture.setUp()
                    try:
                        def boundary(current):
                            if current != stage:
                                return
                            artifact = fixture.root / name
                            if operation == "delete":
                                artifact.unlink()
                            elif operation == "replace":
                                raw = artifact.read_bytes()
                                artifact.unlink()
                                artifact.write_bytes(raw)
                            else:
                                artifact.write_bytes(b"corrupt")
                        with self.assertRaises((ValueError, OSError)):
                            fixture.initialize(boundary=boundary)
                        if stage.startswith("pending"):
                            self.assertEqual(fixture.marker.read_bytes(), b"unresolved")
                        else:
                            self.assertTrue((fixture.root / bootstrap.ARTIFACTS[0]).exists())
                    finally:
                        fixture.doCleanups()


if __name__ == "__main__":
    unittest.main()
