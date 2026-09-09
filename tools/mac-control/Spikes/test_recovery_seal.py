"""Completion/preflight contract in private fixtures; no native recovery or input."""
import json
import os
from pathlib import Path
import unittest

import recovery_bootstrap as bootstrap
import recovery_seal as seal_module
import test_recovery_bootstrap as bootstrap_tests
from recovery_snapshot import MarkerLock, fingerprint


class SealTests(unittest.TestCase):
    def fixture(self):
        fixture = bootstrap_tests.BootstrapTests("test_capture_read_only")
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        fixture.seal_directory = Path(fixture.temp.name).resolve() / "external-seal"
        fixture.seal_directory.mkdir(mode=0o700)
        return fixture

    def initialize(self, fixture, **changes):
        args = dict(seal_directory=str(fixture.seal_directory),
                    provenance="independent offline completion acquisition",
                    observe=fixture.observe, clock=lambda: fixture.now,
                    history=fixture.history,
                    trusted_history_sha256=bootstrap.digest(fixture.history))
        args.update(changes)
        return seal_module.initialize_sealed(fixture.owner, fixture.baseline, **args)

    def preflight(self, fixture, seal, **changes):
        args = dict(history=fixture.history,
                    trusted_history_sha256=bootstrap.digest(fixture.history),
                    observe=fixture.observe, clock=lambda: fixture.now)
        args.update(changes)
        return seal_module.preflight(fixture.owner, seal, fixture.baseline, **args)

    def state(self, fixture):
        return (fingerprint(fixture.root.stat()),
                {p.name: (fingerprint(p.lstat()), p.read_bytes())
                 for p in fixture.root.iterdir() if p.is_file()},
                fixture.history_path.read_bytes())

    def test_success_retains_lock_evidence_and_returns_only_candidate(self):
        fixture = self.fixture()
        marker_inode = fixture.marker.stat().st_ino
        seal = self.initialize(fixture)
        self.assertIs(type(seal), seal_module.TrustedSeal)
        self.assertEqual(seal.trusted_sha256, bootstrap.digest(seal.raw))
        self.assertEqual((fixture.seal_directory / "seal.json").read_bytes(), seal.raw)
        self.assertEqual(fixture.marker.stat().st_ino, marker_inode)
        self.assertEqual(fixture.marker.read_bytes(), b"clean")
        self.assertEqual(set(p.name for p in fixture.root.iterdir()),
                         {"lock", *bootstrap.ARTIFACTS})
        before = self.state(fixture)
        calls = []
        def observe():
            calls.append(True)
            return fixture.observe()
        result = self.preflight(fixture, seal, observe=observe)
        self.assertEqual(result["result"], "activationCandidate")
        self.assertIs(result["launch_eligible"], False)
        self.assertIs(result["native_recovery_verified"], False)
        self.assertEqual(len(calls), 2)
        self.assertEqual(self.state(fixture), before)
        self.assertEqual(fixture.history_path.read_bytes(), fixture.history)
        with self.assertRaisesRegex(ValueError, "snapshotBusy"):
            MarkerLock.acquire(fixture.root)

    def test_seal_binds_exact_artifacts_marker_directory_and_provenance(self):
        fixture = self.fixture()
        seal = self.initialize(fixture)
        data = json.loads(seal.raw)
        self.assertEqual(data["schema"], "legacyCompletion/v1")
        self.assertRegex(data["transaction_id"], r"^[0-9a-f]{32}$")
        self.assertEqual(data["directory"], str(fixture.root))
        self.assertEqual(data["provenance"], seal.provenance)
        self.assertEqual(data["stamps"], json.loads(bootstrap.encode([
            fingerprint(fixture.root.stat()), fingerprint(fixture.marker.stat())])))
        self.assertEqual(set(data["artifacts"]), set(bootstrap.ARTIFACTS))
        for name, artifact in data["artifacts"].items():
            raw = (fixture.root / name).read_bytes()
            self.assertEqual(artifact["hex"], raw.hex())
            self.assertEqual(artifact["sha256"], bootstrap.digest(raw))
            self.assertEqual(artifact["stamp"],
                             json.loads(bootstrap.encode(fingerprint((fixture.root / name).stat()))))

    def test_missing_wrong_pins_and_provenance_reject(self):
        fixture = self.fixture()
        seal = self.initialize(fixture)
        for pin in [None, "", "0" * 64, seal.trusted_sha256.upper()]:
            with self.subTest(pin=pin), self.assertRaises(ValueError):
                seal_module.load_seal(seal.raw, trusted_sha256=pin, provenance=seal.provenance)
        for provenance in [None, "", " ", "unrelated acquisition", 42]:
            with self.subTest(provenance=provenance), self.assertRaises(ValueError):
                seal_module.load_seal(seal.raw, trusted_sha256=seal.trusted_sha256,
                                      provenance=provenance)
        with self.assertRaises(TypeError):
            seal_module.load_seal(seal.raw, provenance=seal.provenance)

    def test_malformed_noncanonical_and_unsupported_seals_reject(self):
        fixture = self.fixture()
        seal = self.initialize(fixture)
        data = json.loads(seal.raw)
        cases = [b"", b"{", b"[]", b"null", seal.raw + b"\n",
                 json.dumps(data, indent=2).encode(),
                 b'{"schema":"legacyCompletion/v1",' + seal.raw[1:]]
        for key, value in [("schema", "legacyCompletion/v0"), ("transaction_id", "bad"),
                           ("stamps", []), ("directory", 7), ("extra", True)]:
            cases.append(bootstrap.encode(dict(data, **{key: value})))
        for key in data:
            cases.append(bootstrap.encode({k: v for k, v in data.items() if k != key}))
        for raw in cases:
            with self.subTest(raw=raw[:70]), self.assertRaises(ValueError):
                seal_module.load_seal(raw, trusted_sha256=bootstrap.digest(raw),
                                      provenance=seal.provenance)

    def test_preflight_revalidates_manually_constructed_untrusted_seal(self):
        fixture = self.fixture()
        seal = self.initialize(fixture)
        for candidate in [None, seal.raw,
                          seal_module.TrustedSeal(seal.raw, "0" * 64, seal.provenance),
                          seal_module.TrustedSeal(seal.raw, seal.trusted_sha256, "wrong")]:
            with self.subTest(candidate=type(candidate)), self.assertRaises(ValueError):
                self.preflight(fixture, candidate)

    def test_baseline_and_history_require_original_external_pins(self):
        fixture = self.fixture()
        seal = self.initialize(fixture)
        before = self.state(fixture)
        for changes in [dict(history=b""), dict(history=fixture.history + b"changed"),
                        dict(trusted_history_sha256="0" * 64),
                        dict(history=b"different pinned history",
                             trusted_history_sha256=bootstrap.digest(b"different pinned history"))]:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.preflight(fixture, seal, **changes)
        fixture.baseline = bootstrap.TrustedBaseline(fixture.raw, "0" * 64,
                                                     fixture.baseline.provenance)
        with self.assertRaises(ValueError):
            self.preflight(fixture, seal)
        self.assertEqual(self.state(fixture), before)

    def test_original_noncanonical_baseline_and_binary_history_are_preserved(self):
        fixture = self.fixture()
        fixture.raw = json.dumps(json.loads(fixture.raw), indent=3).encode() + b"\n"
        fixture.baseline = bootstrap.load_baseline(
            fixture.raw, trusted_sha256=bootstrap.digest(fixture.raw),
            provenance="externally retained original formatting")
        fixture.history = b"\x00 historical opaque evidence \xff\n"
        fixture.history_path.write_bytes(fixture.history)
        seal = self.initialize(fixture)
        self.assertEqual(self.preflight(fixture, seal)["result"], "activationCandidate")
        committed = json.loads((fixture.root / bootstrap.ARTIFACTS[2]).read_bytes())
        self.assertEqual(bytes.fromhex(committed["baseline_hex"]), fixture.raw)
        self.assertEqual(bytes.fromhex(committed["history_hex"]), fixture.history)

    def test_even_pinned_v1_malformed_or_inconsistent_audits_never_form_candidate(self):
        # Deliberately re-pin adversarial synthetic snapshots in this offline
        # harness to reach semantic audit validation beyond the digest check.
        for mutation in ["v1", "numeric-false", "extra", "missing-marker",
                         "pending-mismatch", "noncanonical", "duplicate-key"]:
            with self.subTest(mutation=mutation):
                fixture = self.fixture()
                seal = self.initialize(fixture)
                path = fixture.root / bootstrap.ARTIFACTS[2]
                data = json.loads(path.read_bytes())
                if mutation == "v1":
                    data["schema"] = "legacyBootstrap/v1"
                elif mutation == "numeric-false":
                    data["launch_eligible"] = 0
                elif mutation == "extra":
                    data["unexpected"] = True
                elif mutation == "missing-marker":
                    del data["initialized_marker_stamp"]
                elif mutation == "pending-mismatch":
                    path = fixture.root / bootstrap.ARTIFACTS[0]
                    data = json.loads(path.read_bytes())
                    data["historical_outcome"] = "successful"
                changed = bootstrap.encode(data)
                if mutation == "noncanonical":
                    changed += b"\n"
                elif mutation == "duplicate-key":
                    changed = b'{"schema":"legacyBootstrap/v2",' + changed[1:]
                path.write_bytes(changed)
                replacement = json.loads(seal.raw)
                replacement["stamps"] = json.loads(bootstrap.encode([
                    fingerprint(fixture.root.stat()), fingerprint(fixture.marker.stat())]))
                for name in bootstrap.ARTIFACTS:
                    artifact = fixture.root / name
                    raw = artifact.read_bytes()
                    replacement["artifacts"][name] = dict(
                        hex=raw.hex(), sha256=bootstrap.digest(raw),
                        stamp=json.loads(bootstrap.encode(fingerprint(artifact.stat()))))
                raw = bootstrap.encode(replacement)
                candidate = seal_module.TrustedSeal(raw, bootstrap.digest(raw), seal.provenance)
                before = self.state(fixture)
                with self.assertRaises(ValueError):
                    self.preflight(fixture, candidate)
                self.assertEqual(self.state(fixture), before)

    def test_context_inventory_and_stale_samples_reject_read_only(self):
        fixture = self.fixture()
        seal = self.initialize(fixture)
        before = self.state(fixture)
        changes = [dict(boot="11111111-1111-1111-1111-111111111111"),
                   dict(boot="33333333-3333-3333-3333-333333333333"),
                   dict(session="another-session"), dict(inventory_complete=False),
                   dict(executors=[{"pid": 1}]), dict(executors=None),
                   dict(checked_ns=199), dict(checked_ns=201), dict(checked_ns=True)]
        for change in changes:
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.preflight(fixture, seal, observe=lambda: dict(fixture.observe(), **change))
        self.assertEqual(self.state(fixture), before)

    def test_two_context_samples_must_agree(self):
        fixture = self.fixture()
        seal = self.initialize(fixture)
        samples = iter([fixture.observe(), dict(fixture.observe(), session="drift")])
        with self.assertRaises(ValueError):
            self.preflight(fixture, seal, observe=lambda: next(samples))

    def test_context_before_initialization_rejects_even_with_matching_clock(self):
        fixture = self.fixture()
        seal = self.initialize(fixture)
        fixture.now = 100
        before = self.state(fixture)
        with self.assertRaises(ValueError):
            self.preflight(fixture, seal)
        self.assertEqual(self.state(fixture), before)

    def test_later_preflight_reacquires_existing_namespace_read_only(self):
        fixture = self.fixture()
        seal = self.initialize(fixture)
        fixture.owner.close()
        fixture.owner = MarkerLock.acquire(fixture.root, create=False)
        self.addCleanup(fixture.owner.close)
        fixture.now = 400
        retained = seal_module.load_seal(seal.raw, trusted_sha256=seal.trusted_sha256,
                                         provenance=seal.provenance)
        before = self.state(fixture)
        self.assertEqual(self.preflight(fixture, retained)["result"], "activationCandidate")
        self.assertEqual(self.state(fixture), before)

    def test_unreadable_inventory_and_slow_clock_reject(self):
        fixture = self.fixture()
        seal = self.initialize(fixture)
        before = self.state(fixture)
        def unreadable():
            raise OSError("inventory unreadable")
        with self.assertRaises(OSError):
            self.preflight(fixture, seal, observe=unreadable)
        ticks = iter([fixture.now, fixture.now + bootstrap.WINDOW_NS + 1])
        with self.assertRaises(ValueError):
            self.preflight(fixture, seal, clock=lambda: next(ticks))
        self.assertEqual(self.state(fixture), before)

    def test_marker_restore_and_namespace_metadata_changes_reject(self):
        for change in ["marker-restore", "extra-name", "root-mode", "root-mtime"]:
            with self.subTest(change=change):
                fixture = self.fixture()
                seal = self.initialize(fixture)
                if change == "marker-restore":
                    fixture.owner.write_marker(b"unresolved:intervening")
                    fixture.owner.write_marker(b"clean")
                    info = fixture.marker.stat()
                    os.utime(fixture.marker, ns=(info.st_atime_ns, info.st_mtime_ns + 1))
                elif change == "extra-name":
                    (fixture.root / "activation.unrecognized").write_bytes(b"unknown")
                elif change == "root-mode":
                    fixture.root.chmod(0o755)
                else:
                    info = fixture.root.stat()
                    os.utime(fixture.root, ns=(info.st_atime_ns, info.st_mtime_ns + 1))
                before = self.state(fixture)
                with self.assertRaises(ValueError):
                    self.preflight(fixture, seal)
                self.assertEqual(self.state(fixture), before)

    def test_artifact_bytes_modes_links_and_replacements_reject(self):
        for name in bootstrap.ARTIFACTS:
            for operation in ["missing", "corrupt", "replace", "mode", "link", "symlink"]:
                with self.subTest(name=name, operation=operation):
                    fixture = self.fixture()
                    seal = self.initialize(fixture)
                    path = fixture.root / name
                    if operation == "missing":
                        path.unlink()
                    elif operation == "corrupt":
                        path.write_bytes(b"corrupt")
                    elif operation == "replace":
                        raw = path.read_bytes()
                        path.unlink()
                        path.write_bytes(raw)
                        path.chmod(0o600)
                    elif operation == "mode":
                        path.chmod(0o644)
                    elif operation == "link":
                        os.link(path, fixture.seal_directory / "extra-evidence-link")
                    else:
                        raw = path.read_bytes()
                        target = fixture.seal_directory / "substitute"
                        target.write_bytes(raw)
                        path.unlink()
                        path.symlink_to(target)
                    before = self.state(fixture)
                    with self.assertRaises((ValueError, OSError)):
                        self.preflight(fixture, seal)
                    self.assertEqual(self.state(fixture), before)

    def test_mutation_during_observation_is_rechecked(self):
        fixture = self.fixture()
        seal = self.initialize(fixture)
        calls = 0
        def observe():
            nonlocal calls
            calls += 1
            if calls == 2:
                (fixture.root / bootstrap.ARTIFACTS[0]).write_bytes(b"changed during context")
            return fixture.observe()
        with self.assertRaises(ValueError):
            self.preflight(fixture, seal, observe=observe)

    def test_final_clock_callback_mutation_rejects_without_repair(self):
        fixture = self.fixture()
        seal = self.initialize(fixture)
        calls = 0
        def clock():
            nonlocal calls
            calls += 1
            if calls == 2:
                fixture.owner.write_marker(b"unresolved:changed-at-final-clock")
            return fixture.now
        with self.assertRaises(ValueError):
            self.preflight(fixture, seal, clock=clock)
        self.assertEqual(fixture.marker.read_bytes(), b"unresolved:changed-at-final-clock")
        self.assertTrue(all((fixture.root / name).exists() for name in bootstrap.ARTIFACTS))

    def test_closed_owner_and_replaced_namespace_reject(self):
        for operation in ["close", "replace-marker", "replace-directory"]:
            with self.subTest(operation=operation):
                fixture = self.fixture()
                seal = self.initialize(fixture)
                if operation == "close":
                    fixture.owner.close()
                elif operation == "replace-marker":
                    fixture.marker.unlink()
                    fixture.marker.write_bytes(b"clean")
                    fixture.marker.chmod(0o600)
                else:
                    fixture.root.rename(fixture.root.with_name("old-marker"))
                    fixture.root.mkdir(mode=0o700)
                with self.assertRaises(ValueError):
                    self.preflight(fixture, seal)

    def test_no_retrospective_or_repeated_sealing(self):
        for initialized_with_seal in [False, True]:
            with self.subTest(initialized_with_seal=initialized_with_seal):
                fixture = self.fixture()
                if initialized_with_seal:
                    self.initialize(fixture)
                    another = fixture.seal_directory.with_name("another-seal")
                    another.mkdir(mode=0o700)
                    fixture.seal_directory = another
                else:
                    fixture.initialize()
                before = self.state(fixture)
                with self.assertRaises(ValueError):
                    self.initialize(fixture)
                self.assertEqual(self.state(fixture), before)
                self.assertEqual(list(fixture.seal_directory.iterdir()), [])

    def test_seal_boundary_exceptions_return_no_acknowledgement_and_retain_lock(self):
        for stage in ["sealCreated", "sealWritten", "sealFlushed",
                      "sealPublished", "sealDirectoryFlushed"]:
            with self.subTest(stage=stage):
                fixture = self.fixture()
                returned = []
                def boundary(current):
                    if current == stage:
                        raise OSError("simulated external seal failure")
                with self.assertRaises(OSError):
                    returned.append(self.initialize(fixture, boundary=boundary))
                self.assertEqual(returned, [])
                self.assertEqual(fixture.marker.read_bytes(), b"clean")
                self.assertTrue(all((fixture.root / name).exists() for name in bootstrap.ARTIFACTS))
                fixture.owner.recheck()
                with self.assertRaisesRegex(ValueError, "snapshotBusy"):
                    MarkerLock.acquire(fixture.root)

    def test_external_directory_must_be_existing_empty_private_and_disjoint(self):
        for operation in ["same", "child", "ancestor", "missing", "nonempty", "public", "symlink"]:
            with self.subTest(operation=operation):
                fixture = self.fixture()
                target = fixture.seal_directory
                if operation == "same":
                    target = fixture.root
                elif operation == "child":
                    target = fixture.root / "seal-child"
                    target.mkdir(mode=0o700)
                elif operation == "ancestor":
                    target = fixture.root.parent
                elif operation == "missing":
                    target = target.with_name("missing")
                elif operation == "nonempty":
                    (target / "retained").write_bytes(b"preserve")
                elif operation == "public":
                    target.chmod(0o755)
                else:
                    link = target.with_name("seal-link")
                    link.symlink_to(target, target_is_directory=True)
                    target = link
                before = self.state(fixture)
                with self.assertRaises((ValueError, OSError)):
                    self.initialize(fixture, seal_directory=str(target))
                self.assertEqual(self.state(fixture), before)
                self.assertFalse((fixture.root / bootstrap.ARTIFACTS[0]).exists())


if __name__ == "__main__":
    unittest.main()
