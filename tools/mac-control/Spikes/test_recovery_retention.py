"""Retention uses real private files; activation fixtures supply synthetic context."""
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

import recovery_activation as activation
import recovery_retention as retention
import recovery_caller as caller
import recovery_bootstrap as bootstrap
from recovery_snapshot import identity
import test_recovery_activation as fixtures


class RetentionTests(unittest.TestCase):
    def fixture(self):
        helper = fixtures.ActivationTests()
        self.addCleanup(helper.doCleanups)
        fixture = helper.fixture()
        directory = fixture.parent / "independent-witness"
        directory.mkdir(mode=0o700)
        return fixture, directory, identity(directory.stat())

    def test_checkpoint_survives_interruption_and_reaches_actual_gate_once(self):
        fixture, directory, pin = self.fixture()
        def sink(value):
            retention.retain(directory, value, trusted_directory_identity=pin)
            raise OSError("activation interrupted after independent retention")
        with self.assertRaises(OSError):
            fixture.activate(checkpoint_sink=sink)
        witness = retention.load(directory, kind="transition", trusted_directory_identity=pin)
        self.assertIs(type(witness), activation.TrustedTransition)
        ack = activation.reconcile(fixture.owner, witness, fixture.seal, fixture.baseline,
                                   provenance="explicit retained witness", **fixture.context())
        owner = fixture.gate(fixture.request(ack))
        owner.close()
        with self.assertRaises(ValueError):
            fixture.gate(fixture.request(ack))

    def test_exact_bytes_pin_and_provenance_round_trip_without_launch(self):
        fixture, directory, pin = self.fixture()
        before = fixture.state()
        with patch("subprocess.Popen", side_effect=AssertionError("no launch")):
            retention.retain(directory, fixture.seal, trusted_directory_identity=pin)
            result = retention.load(directory, kind="seal", trusted_directory_identity=pin)
        self.assertEqual(result, fixture.seal)
        self.assertEqual(fixture.state(), before)
        with self.assertRaises(ValueError):
            retention.load(directory, kind="activation", trusted_directory_identity=pin)
        with self.assertRaises(ValueError):
            retention.retain(directory, fixture.seal, trusted_directory_identity=pin)

    def test_wrong_root_identity_and_unsafe_paths_reject(self):
        fixture, directory, pin = self.fixture()
        with self.assertRaises(ValueError):
            retention.retain(directory, fixture.seal, trusted_directory_identity=(pin[0], pin[1] + 1))
        self.assertEqual(list(directory.iterdir()), [])
        directory.chmod(0o755)
        with self.assertRaises(ValueError):
            retention.retain(directory, fixture.seal, trusted_directory_identity=pin)
        directory.chmod(0o700)
        link = fixture.parent / "linked-witness"
        link.symlink_to(directory)
        with self.assertRaises((ValueError, OSError)):
            retention.retain(link, fixture.seal, trusted_directory_identity=pin)

    def test_partial_publication_never_loads_or_overwrites(self):
        for stage in ("witnessCreated", "witnessWritten", "witnessFlushed"):
            with self.subTest(stage=stage):
                fixture, directory, pin = self.fixture()
                def boundary(current):
                    if current == stage:
                        raise OSError("interrupted")
                with self.assertRaises(OSError):
                    retention.retain(directory, fixture.seal, trusted_directory_identity=pin,
                                     boundary=boundary)
                with self.assertRaises(ValueError):
                    retention.load(directory, kind="seal", trusted_directory_identity=pin)
                with self.assertRaises(ValueError):
                    retention.retain(directory, fixture.seal, trusted_directory_identity=pin)

    def test_published_witness_can_establish_new_durability_but_flush_failure_rejects(self):
        fixture, directory, pin = self.fixture()
        def boundary(stage):
            if stage == "witnessPublished":
                raise OSError("interrupted before directory flush")
        with self.assertRaises(OSError):
            retention.retain(directory, fixture.seal, trusted_directory_identity=pin, boundary=boundary)
        for function in ("flush_file", "flush_directory"):
            with patch.object(retention, function, side_effect=OSError("flush failure")):
                with self.assertRaises(OSError):
                    retention.load(directory, kind="seal", trusted_directory_identity=pin)
        self.assertEqual(retention.load(directory, kind="seal", trusted_directory_identity=pin),
                         fixture.seal)

    def test_corruption_extra_link_and_root_replacement_reject(self):
        for operation in ("corruption", "link", "replacement", "mode", "extra"):
            with self.subTest(operation=operation):
                fixture, directory, pin = self.fixture()
                retention.retain(directory, fixture.seal, trusted_directory_identity=pin)
                if operation == "corruption":
                    (directory / "witness.json").write_bytes(b"{}")
                elif operation == "link":
                    os.link(directory / "witness.json", fixture.parent / "extra-link")
                elif operation == "replacement":
                    directory.rename(fixture.parent / "original-witness")
                    directory.mkdir(mode=0o700)
                elif operation == "mode":
                    (directory / "witness.json").chmod(0o644)
                else:
                    (directory / "unexpected").touch()
                with self.assertRaises(ValueError):
                    retention.load(directory, kind="seal", trusted_directory_identity=pin)

    def test_native_caller_retains_both_witnesses_and_keeps_marker_owned(self):
        fixture, directory, pin = self.fixture()
        ack_dir = fixture.parent / "acknowledgement"
        ack_dir.mkdir(mode=0o700)
        ack_pin = identity(ack_dir.stat())
        # Enter the actual caller, substituting only native clock/context. All
        # activation, retention, flushes and downstream launch gating are real.
        with patch.object(caller, "mac_clock", return_value=lambda: fixture.now), \
             patch.object(caller, "capture_bounded_context", side_effect=lambda **kw: fixture.observe()):
            ack = caller.activate_retained(fixture.owner, fixture.seal, fixture.baseline,
                history=fixture.history, trusted_history_sha256=bootstrap.digest(fixture.history),
                transition_slot=caller.WitnessSlot(str(directory), pin),
                acknowledgement_slot=caller.WitnessSlot(str(ack_dir), ack_pin), provenance="native caller fixture")
        fixture.owner.recheck()
        self.assertIs(type(retention.load(directory, kind="transition", trusted_directory_identity=pin)),
                      activation.TrustedTransition)
        self.assertEqual(retention.load(ack_dir, kind="activation", trusted_directory_identity=ack_pin), ack)
        owner = fixture.gate(fixture.request(ack))
        owner.close()

    def test_caller_bad_slots_reject_before_activation(self):
        fixture, directory, pin = self.fixture()
        before = fixture.state()
        slot = caller.WitnessSlot(str(directory), pin)
        with self.assertRaises(ValueError):
            caller.activate_retained(fixture.owner, fixture.seal, fixture.baseline,
                history=fixture.history, trusted_history_sha256=bootstrap.digest(fixture.history),
                transition_slot=slot, acknowledgement_slot=slot, provenance="fixture")
        self.assertEqual(fixture.state(), before)
        self.assertEqual(list(directory.iterdir()), [])

    def test_real_process_death_at_retention_boundaries(self):
        source = r'''
import json, os, sys
from pathlib import Path
import recovery_retention as retention
import recovery_seal as seals
directory, stage, source, dev, inode = sys.argv[1:]
data = json.loads(Path(source).read_bytes())
value = seals.load_seal(bytes.fromhex(data['hex']), trusted_sha256=data['pin'], provenance=data['provenance'])
def boundary(current):
    if current == stage:
        os._exit(23)
retention.retain(directory, value, trusted_directory_identity=(int(dev), int(inode)), boundary=boundary)
'''
        for stage in ("witnessCreated", "witnessWritten", "witnessFlushed", "witnessPublished",
                      "witnessDirectoryFlushed"):
            with self.subTest(stage=stage):
                fixture, directory, pin = self.fixture()
                source_path = fixture.parent / "independent-original-input.json"
                source_path.write_bytes(bootstrap.encode(dict(hex=fixture.seal.raw.hex(),
                    pin=fixture.seal.trusted_sha256, provenance=fixture.seal.provenance)))
                result = subprocess.run([sys.executable, "-B", "-c", source, str(directory), stage,
                    str(source_path), str(pin[0]), str(pin[1])], cwd=Path(__file__).resolve().parent,
                    capture_output=True, timeout=10)
                self.assertEqual(result.returncode, 23, result.stderr.decode())
                if stage in ("witnessPublished", "witnessDirectoryFlushed"):
                    self.assertEqual(retention.load(directory, kind="seal", trusted_directory_identity=pin),
                                     fixture.seal)
                else:
                    with self.assertRaises(ValueError):
                        retention.load(directory, kind="seal", trusted_directory_identity=pin)
                with self.assertRaises(ValueError):
                    fixture.gate()

    def test_short_zero_and_failed_file_writes(self):
        for operation in ("short", "zero", "flush"):
            with self.subTest(operation=operation):
                fixture, directory, pin = self.fixture()
                original = os.write
                def write(fd, raw):
                    return 0 if operation == "zero" else original(fd, raw[:73])
                target = "recovery_bootstrap.flush_file" if operation == "flush" else "recovery_bootstrap.os.write"
                kwargs = dict(side_effect=OSError("file flush failed")) if operation == "flush" else dict(side_effect=write)
                with patch(target, **kwargs):
                    if operation == "short":
                        retention.retain(directory, fixture.seal, trusted_directory_identity=pin)
                    else:
                        with self.assertRaises((ValueError, OSError)):
                            retention.retain(directory, fixture.seal, trusted_directory_identity=pin)
                if operation == "short":
                    self.assertEqual(retention.load(directory, kind="seal", trusted_directory_identity=pin), fixture.seal)
                else:
                    with self.assertRaises(ValueError):
                        retention.load(directory, kind="seal", trusted_directory_identity=pin)

    def test_final_retention_recheck_rejects_mutation(self):
        fixture, directory, pin = self.fixture()
        def boundary(stage):
            if stage == "witnessDirectoryFlushed":
                (directory / "witness.json").write_bytes(b"corrupt")
        with self.assertRaises(ValueError):
            retention.retain(directory, fixture.seal, trusted_directory_identity=pin, boundary=boundary)

    def test_caller_ack_storage_failure_keeps_transition_and_does_not_return_ack(self):
        fixture, directory, pin = self.fixture()
        ack_dir = fixture.parent / "failed-ack"
        ack_dir.mkdir(mode=0o700)
        ack_pin = identity(ack_dir.stat())
        original = retention.retain
        def retain(path, value, **kwargs):
            if str(path) == str(ack_dir):
                raise OSError("ack retention failed")
            return original(path, value, **kwargs)
        with patch.object(caller, "mac_clock", return_value=lambda: fixture.now), \
             patch.object(caller, "capture_bounded_context", side_effect=lambda **kw: fixture.observe()), \
             patch.object(retention, "retain", side_effect=retain):
            with self.assertRaises(OSError):
                caller.activate_retained(fixture.owner, fixture.seal, fixture.baseline,
                    history=fixture.history, trusted_history_sha256=bootstrap.digest(fixture.history),
                    transition_slot=caller.WitnessSlot(str(directory), pin),
                    acknowledgement_slot=caller.WitnessSlot(str(ack_dir), ack_pin), provenance="fixture")
        fixture.owner.recheck()
        self.assertIs(type(retention.load(directory, kind="transition", trusted_directory_identity=pin)),
                      activation.TrustedTransition)
        with self.assertRaises(ValueError):
            retention.load(ack_dir, kind="activation", trusted_directory_identity=ack_pin)
        with self.assertRaises(ValueError):
            fixture.gate()


if __name__ == "__main__":
    unittest.main()
