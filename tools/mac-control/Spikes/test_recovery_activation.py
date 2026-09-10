"""Activation and actual launcher admission in private offline namespaces only."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import recovery_activation as activation
import recovery_bootstrap as bootstrap
import recovery_seal as sealing
from recovery_snapshot import MarkerLock, fingerprint
import supervisor
import runtime_root


NAMES = {"activation.intent", "activation.receipt.tmp", "activation.receipt.json"}
CONSUMED = "activation.consumed"
RUN = "abcdef0123456789" * 2


class ActivationTests(unittest.TestCase):
    def fixture(self):
        fixture = ActivationTests()
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        fixture.parent = Path(temp.name).resolve()
        fixture.root = fixture.parent / "directions-stop-spike"
        fixture.root.mkdir(mode=0o700)
        fixture.marker = fixture.root / "lock"
        fixture.marker.write_bytes(b"unresolved")
        fixture.marker.chmod(0o600)
        fixture.owner = MarkerLock.acquire(fixture.root, create=False)
        self.addCleanup(fixture.owner.close)
        fixture.boot = "11111111-1111-1111-1111-111111111111"
        fixture.now = 100
        fixture.history = b"\x00failed historical run; outcome unknown\xff"
        fixture.history_path = fixture.parent / "history"
        fixture.history_path.write_bytes(fixture.history)
        raw = bootstrap.capture_baseline(fixture.owner, observe=fixture.observe,
                                        clock=lambda: fixture.now,
                                        provenance="offline original acquisition")
        fixture.baseline = bootstrap.load_baseline(
            raw, trusted_sha256=bootstrap.digest(raw), provenance="independent baseline pin")
        fixture.boot = "22222222-2222-2222-2222-222222222222"
        fixture.now = 200
        external = fixture.parent / "external-seal"
        external.mkdir(mode=0o700)
        fixture.seal = sealing.initialize_sealed(
            fixture.owner, fixture.baseline, seal_directory=str(external),
            provenance="independently retained completion", **fixture.context())
        fixture.now = 300
        return fixture

    def observe(self):
        return dict(boot=self.boot, session="fixture-session", checked_ns=self.now,
                    inventory_complete=True, executors=[])

    def context(self):
        return dict(history=self.history, trusted_history_sha256=bootstrap.digest(self.history),
                    observe=self.observe, clock=lambda: self.now)

    def activate(self, **changes):
        args = dict(self.context(), provenance="independent activation acquisition")
        args.update(changes)
        return activation.activate(self.owner, self.seal, self.baseline, **args)

    def request(self, ack, **changes):
        args = dict(self.context(), acknowledgement=ack, seal=self.seal, baseline=self.baseline)
        args.update(changes)
        return activation.ActivationRequest(**args)

    def gate(self, request=None, run=RUN):
        self.owner.close()
        with patch.object(supervisor.os, "confstr", return_value=str(self.parent)), \
             patch.object(runtime_root, "TRUSTED_RUNTIME_ROOT", self.root):
            if request is None:
                return supervisor.experiment_lock(run)
            return supervisor.experiment_lock(run, activation=request)

    def state(self):
        entries = {}
        for path in self.root.iterdir():
            raw = os.readlink(path) if path.is_symlink() else path.read_bytes()
            entries[path.name] = (fingerprint(path.lstat()), raw)
        return fingerprint(self.root.stat()), entries, self.history_path.read_bytes()

    def test_activation_only_preserves_clean_marker_and_all_historical_evidence(self):
        fixture = self.fixture()
        marker = fingerprint(fixture.marker.stat())
        history = {name: (fixture.root / name).read_bytes() for name in bootstrap.ARTIFACTS}
        with patch.object(supervisor.subprocess, "Popen", side_effect=AssertionError("no launch")):
            ack = fixture.activate()
        self.assertIs(type(ack), activation.TrustedActivation)
        self.assertEqual(ack.trusted_sha256, bootstrap.digest(ack.raw))
        self.assertEqual(fixture.marker.read_bytes(), b"clean")
        self.assertEqual(fingerprint(fixture.marker.stat()), marker)
        self.assertEqual(set(p.name for p in fixture.root.iterdir()), {"lock", *bootstrap.ARTIFACTS, *NAMES})
        for name, raw in history.items():
            self.assertEqual((fixture.root / name).read_bytes(), raw)
        self.assertEqual(fixture.history_path.read_bytes(), fixture.history)
        tmp = (fixture.root / "activation.receipt.tmp").stat()
        published = (fixture.root / "activation.receipt.json").stat()
        self.assertEqual((tmp.st_dev, tmp.st_ino, tmp.st_nlink),
                         (published.st_dev, published.st_ino, 2))
        with self.assertRaises(ValueError):
            fixture.gate()

    def test_actual_launcher_consumes_once_and_returns_same_held_marker_inode(self):
        fixture = self.fixture()
        ack = fixture.activate()
        inode = fixture.marker.stat().st_ino
        owner = fixture.gate(fixture.request(ack))
        self.addCleanup(owner.close)
        self.assertEqual(fixture.marker.read_bytes(), b"unresolved:" + RUN.encode())
        self.assertEqual(fixture.marker.stat().st_ino, inode)
        owner.recheck()
        self.assertTrue((fixture.root / CONSUMED).is_file())
        self.assertIn(RUN.encode(), (fixture.root / CONSUMED).read_bytes())
        with self.assertRaisesRegex(ValueError, "snapshotBusy"):
            MarkerLock.acquire(fixture.root, create=False)
        owner.close()
        before = fixture.state()
        with self.assertRaises(ValueError):
            fixture.gate(fixture.request(ack), run="1" * 32)
        self.assertEqual(fixture.state(), before)

    def test_cleanup_to_clean_cannot_replay_permanent_consumption(self):
        fixture = self.fixture()
        ack = fixture.activate()
        owner = fixture.gate(fixture.request(ack))
        try:
            owner.write_marker(b"clean")
        finally:
            owner.close()
        consumed = (fixture.root / CONSUMED).read_bytes()
        before = fixture.state()
        for request in [None, fixture.request(ack)]:
            with self.subTest(explicit=request is not None), self.assertRaises(ValueError):
                fixture.gate(request, run="2" * 32)
        self.assertEqual(fixture.state(), before)
        self.assertEqual((fixture.root / CONSUMED).read_bytes(), consumed)

    def test_invalid_run_and_request_fail_before_mutation(self):
        fixture = self.fixture()
        ack = fixture.activate()
        fixture.owner.close()
        before = fixture.state()
        for run in [None, "", "bad", "A" * 32, "0" * 31, True, 42]:
            with self.subTest(run=run), self.assertRaises((ValueError, TypeError)):
                fixture.gate(fixture.request(ack), run=run)
            self.assertEqual(fixture.state(), before)
        for request in [ack, {}, b"receipt", object()]:
            with self.subTest(request=type(request)), self.assertRaises((ValueError, TypeError)):
                fixture.gate(request)
            self.assertEqual(fixture.state(), before)

    def test_partial_orphan_and_symlink_names_block_ordinary_launcher(self):
        for name in {*NAMES, CONSUMED, *bootstrap.ARTIFACTS}:
            for symlink in [False, True]:
                with self.subTest(name=name, symlink=symlink):
                    fixture = self.fixture()
                    # Construct an orphan fixture; no production repair/removal API is used.
                    for artifact in bootstrap.ARTIFACTS:
                        (fixture.root / artifact).unlink()
                    path = fixture.root / name
                    if symlink:
                        path.symlink_to(fixture.parent / "absent-target")
                    else:
                        path.write_bytes(b"partial")
                        path.chmod(0o600)
                    fixture.owner.close()
                    before = fixture.state()
                    with self.assertRaises(ValueError):
                        fixture.gate()
                    self.assertEqual(fixture.state(), before)

    def test_acknowledgement_loader_requires_independent_pin_and_provenance(self):
        fixture = self.fixture()
        ack = fixture.activate()
        retained = activation.load_activation(ack.raw, trusted_sha256=ack.trusted_sha256,
                                              provenance=ack.provenance)
        self.assertEqual(retained, ack)
        for pin in [None, "", "0" * 64, ack.trusted_sha256.upper()]:
            with self.subTest(pin=pin), self.assertRaises(ValueError):
                activation.load_activation(ack.raw, trusted_sha256=pin, provenance=ack.provenance)
        for provenance in [None, "", " ", "wrong acquisition", 42]:
            with self.subTest(provenance=provenance), self.assertRaises(ValueError):
                activation.load_activation(ack.raw, trusted_sha256=ack.trusted_sha256,
                                           provenance=provenance)

    def test_malformed_noncanonical_and_missing_ack_fields_reject(self):
        fixture = self.fixture()
        ack = fixture.activate()
        data = json.loads(ack.raw)
        cases = [b"", b"{", b"[]", ack.raw + b"\n", json.dumps(data, indent=2).encode(),
                 bootstrap.encode(dict(data, unexpected=True))]
        cases += [bootstrap.encode({k: v for k, v in data.items() if k != key}) for key in data]
        for raw in cases:
            with self.subTest(raw=raw[:50]), self.assertRaises(ValueError):
                activation.load_activation(raw, trusted_sha256=bootstrap.digest(raw),
                                           provenance=ack.provenance)

    def test_activation_rejects_wrong_trust_and_context_without_mutation(self):
        changes = [dict(trusted_history_sha256="0" * 64), dict(history=b"other"),
                   dict(provenance=""), dict(provenance=None)]
        context_changes = [dict(boot="11111111-1111-1111-1111-111111111111"),
                           dict(boot="33333333-3333-3333-3333-333333333333"),
                           dict(session="changed"), dict(inventory_complete=False),
                           dict(executors=[{"pid": 1}]), dict(checked_ns=299)]
        fixture = self.fixture()
        changes += [dict(observe=lambda value=value: dict(fixture.observe(), **value))
                    for value in context_changes]
        before = fixture.state()
        for change in changes:
            with self.subTest(change=change), self.assertRaises(ValueError):
                fixture.activate(**change)
            self.assertEqual(fixture.state(), before)

    def test_actual_launcher_rechecks_context_and_trust_before_consumption(self):
        fixture = self.fixture()
        ack = fixture.activate()
        fixture.owner.close()
        before = fixture.state()
        changes = [dict(trusted_history_sha256="0" * 64), dict(history=b"different"),
                   dict(acknowledgement=activation.TrustedActivation(ack.raw, "0" * 64, ack.provenance)),
                   dict(acknowledgement=activation.TrustedActivation(ack.raw, ack.trusted_sha256, "wrong"))]
        for change in [dict(session="changed"), dict(inventory_complete=False),
                       dict(executors=[{"pid": 1}]), dict(checked_ns=299)]:
            changes.append(dict(observe=lambda change=change: dict(fixture.observe(), **change)))
        for change in changes:
            with self.subTest(change=change), self.assertRaises(ValueError):
                fixture.gate(fixture.request(ack, **change))
            self.assertEqual(fixture.state(), before)

    def test_activation_artifact_corruption_replacement_topology_and_marker_restore_block_gate(self):
        for operation in ["corrupt", "replace", "mode", "extra-link", "symlink", "marker-restore"]:
            with self.subTest(operation=operation):
                fixture = self.fixture()
                ack = fixture.activate()
                path = fixture.root / "activation.receipt.json"
                if operation == "corrupt":
                    path.write_bytes(b"corrupt")
                elif operation == "replace":
                    raw = path.read_bytes()
                    path.unlink()
                    path.write_bytes(raw)
                    path.chmod(0o600)
                elif operation == "mode":
                    path.chmod(0o644)
                elif operation == "extra-link":
                    os.link(path, fixture.parent / "external-link")
                elif operation == "symlink":
                    path.unlink()
                    path.symlink_to(fixture.root / "activation.receipt.tmp")
                else:
                    fixture.owner.write_marker(b"unresolved:intervening")
                    fixture.owner.write_marker(b"clean")
                    info = fixture.marker.stat()
                    os.utime(fixture.marker, ns=(info.st_atime_ns, info.st_mtime_ns + 1))
                fixture.owner.close()
                before = fixture.state()
                with self.assertRaises((ValueError, OSError)):
                    fixture.gate(fixture.request(ack))
                self.assertEqual(fixture.state(), before)

    def interrupted(self, fixture):
        retained = []
        def sink(transition):
            retained.append(transition)
            raise OSError("death after retained publication checkpoint before directory flush")
        with self.assertRaises(OSError):
            fixture.activate(checkpoint_sink=sink)
        self.assertEqual(len(retained), 1)
        self.assertIs(type(retained[0]), activation.TrustedTransition)
        self.assertTrue((fixture.root / "activation.receipt.json").is_file())
        return retained[0]

    def test_explicit_reconcile_retained_checkpoint_then_actual_launcher_admission(self):
        fixture = self.fixture()
        transition = self.interrupted(fixture)
        with self.assertRaises(ValueError):
            fixture.gate()
        fixture.owner = MarkerLock.acquire(fixture.root, create=False)
        self.addCleanup(fixture.owner.close)
        fixture.now = 400
        retained = activation.load_transition(transition.raw, trusted_sha256=transition.trusted_sha256,
                                              provenance=transition.provenance)
        ack = activation.reconcile(fixture.owner, retained, fixture.seal, fixture.baseline,
                                   provenance="explicit independent reconciliation", **fixture.context())
        self.assertIs(type(ack), activation.TrustedActivation)
        self.assertEqual(fixture.marker.read_bytes(), b"clean")
        owner = fixture.gate(fixture.request(ack))
        self.addCleanup(owner.close)
        self.assertEqual(fixture.marker.read_bytes(), b"unresolved:" + RUN.encode())

    def test_reconcile_missing_untrusted_or_changed_checkpoint_refuses_without_mutation(self):
        fixture = self.fixture()
        transition = self.interrupted(fixture)
        for evidence in [None, transition.raw,
                         activation.TrustedTransition(transition.raw, "0" * 64, transition.provenance),
                         activation.TrustedTransition(transition.raw, transition.trusted_sha256, "wrong")]:
            before = fixture.state()
            with self.subTest(evidence=type(evidence)), self.assertRaises(ValueError):
                activation.reconcile(fixture.owner, evidence, fixture.seal, fixture.baseline,
                                     provenance="explicit reconciliation", **fixture.context())
            self.assertEqual(fixture.state(), before)
        info = fixture.root.stat()
        os.utime(fixture.root, ns=(info.st_atime_ns, info.st_mtime_ns + 1))
        before = fixture.state()
        with self.assertRaises(ValueError):
            activation.reconcile(fixture.owner, transition, fixture.seal, fixture.baseline,
                                 provenance="explicit reconciliation", **fixture.context())
        self.assertEqual(fixture.state(), before)

    def test_repeated_activation_never_overwrites_existing_transaction(self):
        fixture = self.fixture()
        fixture.activate()
        before = fixture.state()
        with self.assertRaises(ValueError):
            fixture.activate()
        self.assertEqual(fixture.state(), before)

    def test_explicit_admission_never_recreates_missing_namespace_or_marker(self):
        for missing in ["directory", "marker"]:
            with self.subTest(missing=missing):
                fixture = self.fixture()
                ack = fixture.activate()
                fixture.owner.close()
                if missing == "directory":
                    fixture.root.rename(fixture.parent / "retained-original")
                else:
                    fixture.marker.unlink()
                with self.assertRaises((ValueError, OSError)):
                    fixture.gate(fixture.request(ack))
                if missing == "directory":
                    self.assertFalse(fixture.root.exists())
                else:
                    self.assertFalse(fixture.marker.exists())

    def test_transition_is_not_an_acknowledgement_and_loader_rejects_corruption(self):
        fixture = self.fixture()
        transition = self.interrupted(fixture)
        fixture.owner.close()
        before = fixture.state()
        with self.assertRaises(ValueError):
            fixture.gate(fixture.request(transition))
        self.assertEqual(fixture.state(), before)
        cases = [b"", b"[]", transition.raw + b"\n"]
        data = json.loads(transition.raw)
        cases += [bootstrap.encode(dict(data, unexpected=True))]
        cases += [bootstrap.encode({k: v for k, v in data.items() if k != key}) for key in data]
        for raw in cases:
            with self.subTest(raw=raw[:50]), self.assertRaises(ValueError):
                activation.load_transition(raw, trusted_sha256=bootstrap.digest(raw),
                                           provenance=transition.provenance)

    def test_marker_write_boundary_and_final_clock_cannot_restore_away_intervening_run(self):
        for operation in ["marker-written", "final-clock", "slow-final-flush"]:
            with self.subTest(operation=operation):
                fixture = self.fixture()
                ack = fixture.activate()
                final_clock = False
                def rewrite():
                    fixture.marker.write_bytes(b"unresolved:intervening-run")
                    fixture.marker.write_bytes(b"unresolved:" + RUN.encode())
                    info = fixture.marker.stat()
                    os.utime(fixture.marker, ns=(info.st_atime_ns, info.st_mtime_ns + 1))
                def boundary(stage):
                    nonlocal final_clock
                    if operation == "marker-written" and stage == "admissionMarkerWritten":
                        rewrite()
                    if stage == "admissionMarkerFlushed":
                        final_clock = True
                def clock():
                    if final_clock:
                        if operation == "final-clock":
                            rewrite()
                        elif operation == "slow-final-flush":
                            return fixture.now + bootstrap.WINDOW_NS + 1
                    return fixture.now
                with self.assertRaises(ValueError):
                    fixture.gate(fixture.request(ack, boundary=boundary, clock=clock))
                self.assertTrue((fixture.root / CONSUMED).exists())
                self.assertEqual(fixture.marker.read_bytes(), b"unresolved:" + RUN.encode())
                before = fixture.state()
                with self.assertRaises(ValueError):
                    fixture.gate(fixture.request(ack), run="5" * 32)
                self.assertEqual(fixture.state(), before)


if __name__ == "__main__":
    unittest.main()
