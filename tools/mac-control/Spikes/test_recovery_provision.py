"""Private real-file provisioning and restart; no live configuration or input."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import recovery_provision as provision
import recovery_retention as retention
import recovery_caller as caller
import recovery_bootstrap as bootstrap
from recovery_snapshot import identity
import test_recovery_activation as fixtures


class ProvisionTests(unittest.TestCase):
    def fixture(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        parent = Path(temp.name).resolve()
        evidence, anchor = parent / "evidence", parent / "trusted-config"
        for path in (evidence, anchor):
            path.mkdir(mode=0o700)
        return evidence, anchor

    def test_restart_loads_original_slot_identities_after_witness_retention(self):
        evidence, anchor = self.fixture()
        slots = provision.provision(evidence, trusted_anchor_directory=anchor)
        helper = fixtures.ActivationTests()
        self.addCleanup(helper.doCleanups)
        fixture = helper.fixture()
        slots["seal"].retain(fixture.seal)
        restored = provision.load(evidence, trusted_anchor_directory=anchor)
        self.assertEqual(restored, slots)
        self.assertEqual(retention.load(restored["seal"].directory, kind="seal",
            trusted_directory_identity=restored["seal"].trusted_identity), fixture.seal)
        for role, slot in restored.items():
            self.assertEqual(slot.trusted_identity, identity((evidence / role).stat()))
        with self.assertRaises(ValueError):
            provision.provision(evidence, trusted_anchor_directory=anchor)

    def test_missing_corrupt_replaced_or_unsafe_state_is_not_recreated(self):
        for fault in ("missing-slot", "replaced-slot", "copied-anchor", "corrupt", "mode", "extra"):
            with self.subTest(fault=fault):
                evidence, anchor = self.fixture()
                provision.provision(evidence, trusted_anchor_directory=anchor)
                if fault == "missing-slot":
                    (evidence / "transition").rmdir()
                elif fault == "replaced-slot":
                    (evidence / "transition").rename(evidence.parent / "old-transition")
                    (evidence / "transition").mkdir(mode=0o700)
                elif fault == "copied-anchor":
                    anchor.rename(evidence.parent / "old-anchor")
                    anchor.mkdir(mode=0o700)
                    for name in provision.NAMES:
                        old = evidence.parent / "old-anchor" / name
                        # Preserve manifest hard-link topology in the replacement.
                        if name == "anchor.json":
                            os.link(anchor / "anchor.tmp", anchor / name)
                        else:
                            (anchor / name).write_bytes(old.read_bytes())
                            (anchor / name).chmod(0o600)
                elif fault == "corrupt":
                    (anchor / "anchor.json").write_bytes(b"{}")
                elif fault == "mode":
                    (evidence / "transition").chmod(0o755)
                else:
                    (anchor / "unexpected").touch()
                with self.assertRaises((ValueError, OSError)):
                    provision.load(evidence, trusted_anchor_directory=anchor)
                if fault == "missing-slot":
                    self.assertFalse((evidence / "transition").exists())

    def test_unsafe_or_overlapping_roots_reject_before_mutation(self):
        evidence, anchor = self.fixture()
        for invalid in (evidence, evidence.parent, evidence / "nested"):
            with self.subTest(invalid=invalid), self.assertRaises((ValueError, OSError)):
                provision.provision(evidence, trusted_anchor_directory=invalid)
        link = evidence.parent / "link"
        link.symlink_to(anchor)
        with self.assertRaises((ValueError, OSError)):
            provision.provision(evidence, trusted_anchor_directory=link)
        self.assertEqual(list(evidence.iterdir()), [])
        self.assertEqual(list(anchor.iterdir()), [])

    def test_real_process_death_fences_partial_provisioning(self):
        source = r'''
import os, sys
import recovery_provision as p
def boundary(stage):
    if stage == sys.argv[3]:
        os._exit(23)
p.provision(sys.argv[1], trusted_anchor_directory=sys.argv[2], boundary=boundary)
'''
        for stage in ("fenceCreated", "fenceFlushed", "fenceDirectoryFlushed", "slotCreated:seal",
                      "slotsDirectoryFlushed", "manifestCreated", "manifestFlushed", "anchorPublished",
                      "anchorDirectoryFlushed"):
            with self.subTest(stage=stage):
                evidence, anchor = self.fixture()
                child = subprocess.run([sys.executable, "-B", "-c", source, str(evidence), str(anchor), stage],
                    cwd=Path(__file__).resolve().parent, capture_output=True, timeout=10)
                self.assertEqual(child.returncode, 23, child.stderr.decode())
                if stage in ("anchorPublished", "anchorDirectoryFlushed"):
                    self.assertEqual(set(provision.load(evidence, trusted_anchor_directory=anchor)),
                                     set(provision.ROLES))
                else:
                    with self.assertRaises((ValueError, OSError)):
                        provision.load(evidence, trusted_anchor_directory=anchor)
                with self.assertRaises(ValueError):
                    provision.provision(evidence, trusted_anchor_directory=anchor)

    def test_failed_reload_flush_returns_no_slots(self):
        evidence, anchor = self.fixture()
        provision.provision(evidence, trusted_anchor_directory=anchor)
        for name in ("flush_file", "flush_directory"):
            with patch.object(provision, name, side_effect=OSError("flush failed")):
                with self.assertRaises(OSError):
                    provision.load(evidence, trusted_anchor_directory=anchor)

    def test_fresh_process_reloads_anchor_without_in_memory_identity_pins(self):
        evidence, anchor = self.fixture()
        slots = provision.provision(evidence, trusted_anchor_directory=anchor)
        source = r'''
import json, sys
import recovery_provision as p
slots = p.load(sys.argv[1], trusted_anchor_directory=sys.argv[2])
print(json.dumps({role: [slot.directory, slot.trusted_identity] for role, slot in slots.items()}))
'''
        child = subprocess.run([sys.executable, "-B", "-c", source, str(evidence), str(anchor)],
            cwd=Path(__file__).resolve().parent, capture_output=True, timeout=10)
        self.assertEqual(child.returncode, 0, child.stderr.decode())
        self.assertEqual(json.loads(child.stdout),
                         {role: [slot.directory, list(slot.trusted_identity)] for role, slot in slots.items()})

    def test_restored_slots_enter_actual_native_caller_and_one_shot_gate(self):
        evidence, anchor = self.fixture()
        provision.provision(evidence, trusted_anchor_directory=anchor)
        slots = provision.load(evidence, trusted_anchor_directory=anchor)
        helper = fixtures.ActivationTests()
        self.addCleanup(helper.doCleanups)
        fixture = helper.fixture()
        # Substitute only native clock/context, preserving caller/activation,
        # provision/retention, marker locking and actual admission implementation.
        with patch.object(caller, "mac_clock", return_value=lambda: fixture.now), \
             patch.object(caller, "capture_bounded_context", side_effect=lambda **kw: fixture.observe()):
            ack = caller.activate_retained(fixture.owner, fixture.seal, fixture.baseline,
                history=fixture.history, trusted_history_sha256=bootstrap.digest(fixture.history),
                transition_slot=slots["transition"], acknowledgement_slot=slots["activation"],
                provenance="provisioned caller fixture")
        restored = provision.load(evidence, trusted_anchor_directory=anchor)
        retained = retention.load(restored["activation"].directory, kind="activation",
                                  trusted_directory_identity=restored["activation"].trusted_identity)
        self.assertEqual(retained, ack)
        owner = fixture.gate(fixture.request(retained))
        owner.close()
        with self.assertRaises(ValueError):
            fixture.gate(fixture.request(retained))

    def test_creation_flush_failure_preserves_fence_and_final_mutation_rejects(self):
        evidence, anchor = self.fixture()
        original = provision.flush_directory
        def flush(fd):
            if (anchor / "anchor.fence").exists():
                raise OSError("directory flush failure after fence")
            original(fd)
        with patch.object(provision, "flush_directory", side_effect=flush):
            with self.assertRaises(OSError):
                provision.provision(evidence, trusted_anchor_directory=anchor)
        with self.assertRaises(ValueError):
            provision.provision(evidence, trusted_anchor_directory=anchor)
        with self.assertRaises(ValueError):
            provision.load(evidence, trusted_anchor_directory=anchor)
        evidence, anchor = self.fixture()
        def boundary(stage):
            if stage == "anchorDirectoryFlushed":
                (evidence / "seal").rename(evidence.parent / "original-seal")
                (evidence / "seal").mkdir(mode=0o700)
        with self.assertRaises(ValueError):
            provision.provision(evidence, trusted_anchor_directory=anchor, boundary=boundary)

    def test_root_replacement_at_publication_or_reload_flush_rejects(self):
        for operation in ("publish-evidence", "publish-anchor", "load-evidence", "load-anchor"):
            with self.subTest(operation=operation):
                evidence, anchor = self.fixture()
                target = evidence if operation.endswith("evidence") else anchor
                changed = False
                def replace():
                    nonlocal changed
                    if not changed:
                        changed = True
                        target.rename(target.parent / ("original-" + target.name))
                        target.mkdir(mode=0o700)
                if operation.startswith("publish"):
                    def boundary(stage):
                        if stage == "anchorPublished":
                            replace()
                    with self.assertRaises(ValueError):
                        provision.provision(evidence, trusted_anchor_directory=anchor, boundary=boundary)
                else:
                    provision.provision(evidence, trusted_anchor_directory=anchor)
                    original = provision.flush_directory
                    def flush(fd):
                        original(fd)
                        replace()
                    with patch.object(provision, "flush_directory", side_effect=flush):
                        with self.assertRaises(ValueError):
                            provision.load(evidence, trusted_anchor_directory=anchor)

    def test_every_provision_directory_flush_failure_returns_no_slots(self):
        # Count observed flush boundaries from a real success, then fail each
        # boundary in a fresh namespace; all partial artifacts are preserved.
        evidence, anchor = self.fixture()
        original = provision.flush_directory
        calls = 0
        def count(fd):
            nonlocal calls
            calls += 1
            original(fd)
        with patch.object(provision, "flush_directory", side_effect=count):
            provision.provision(evidence, trusted_anchor_directory=anchor)
        for failed in range(1, calls + 1):
            with self.subTest(failed=failed):
                evidence, anchor = self.fixture()
                current = 0
                def flush(fd):
                    nonlocal current
                    current += 1
                    if current == failed:
                        raise OSError("injected directory flush failure")
                    original(fd)
                with patch.object(provision, "flush_directory", side_effect=flush):
                    with self.assertRaises(OSError):
                        provision.provision(evidence, trusted_anchor_directory=anchor)
                if (anchor / "anchor.fence").exists():
                    with self.assertRaises(ValueError):
                        provision.provision(evidence, trusted_anchor_directory=anchor)
                if not (anchor / "anchor.json").exists():
                    with self.assertRaises(ValueError):
                        provision.load(evidence, trusted_anchor_directory=anchor)


if __name__ == "__main__":
    unittest.main()
