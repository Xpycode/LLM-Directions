"""Real isolated seal persistence faults; native stores and apps are unreachable."""
import os
import unittest
from unittest.mock import patch

import recovery_bootstrap as bootstrap
import test_recovery_seal as seal_tests


class SealStorageTests(unittest.TestCase):
    def fixture(self):
        helper = seal_tests.SealTests("test_success_retains_lock_evidence_and_returns_only_candidate")
        self.addCleanup(helper.doCleanups)
        return helper, helper.fixture()

    def test_external_flush_failure_returns_no_seal_and_keeps_fences(self):
        helper, fixture = self.fixture()
        with patch("recovery_seal.flush_directory", side_effect=OSError("external flush failed")):
            with self.assertRaises(OSError):
                helper.initialize(fixture)
        self.assertEqual(fixture.marker.read_bytes(), b"clean")
        self.assertTrue(all((fixture.root / name).exists() for name in bootstrap.ARTIFACTS))
        self.assertTrue((fixture.seal_directory / "seal.json").exists())
        # A visible published file is not a returned/acquired completion pin.
        self.assertEqual(fixture.history_path.read_bytes(), fixture.history)

    def test_zero_write_and_file_flush_failure_preserve_partial_seal(self):
        for fault in ("zero-write", "file-flush"):
            with self.subTest(fault=fault):
                helper, fixture = self.fixture()
                writing_seal = False
                def boundary(stage):
                    nonlocal writing_seal
                    if stage == "sealCreated":
                        writing_seal = True
                real_write, real_flush = os.write, bootstrap.flush_file
                def write(fd, raw):
                    return 0 if writing_seal and fault == "zero-write" else real_write(fd, raw)
                def flush(fd):
                    if writing_seal and fault == "file-flush":
                        raise OSError("file flush failed")
                    real_flush(fd)
                with patch("recovery_bootstrap.os.write", side_effect=write), \
                     patch("recovery_bootstrap.flush_file", side_effect=flush):
                    with self.assertRaises((OSError, ValueError)):
                        helper.initialize(fixture, boundary=boundary)
                self.assertTrue((fixture.seal_directory / "seal.tmp").exists())
                self.assertFalse((fixture.seal_directory / "seal.json").exists())
                self.assertTrue((fixture.root / bootstrap.ARTIFACTS[0]).exists())

    def test_short_writes_are_completed_before_returning_pin(self):
        helper, fixture = self.fixture()
        real_write = os.write
        with patch("recovery_bootstrap.os.write",
                   side_effect=lambda fd, raw: real_write(fd, raw[:97])):
            seal = helper.initialize(fixture)
        self.assertEqual((fixture.seal_directory / "seal.json").read_bytes(), seal.raw)
        self.assertEqual(helper.preflight(fixture, seal)["result"], "activationCandidate")

    def test_namespace_change_during_initialization_is_not_silently_adopted(self):
        helper, fixture = self.fixture()
        def boundary(stage):
            if stage == "markerFlushed":
                (fixture.seal_directory / "intervening").write_bytes(b"preserve")
        with self.assertRaisesRegex(ValueError, "sealNamespaceChanged"):
            helper.initialize(fixture, boundary=boundary)
        self.assertEqual((fixture.seal_directory / "intervening").read_bytes(), b"preserve")
        self.assertFalse((fixture.seal_directory / "seal.tmp").exists())

    def test_replaced_external_directory_and_changed_seal_reject(self):
        for operation in ("replace-directory", "corrupt", "unlink", "extra-link"):
            with self.subTest(operation=operation):
                helper, fixture = self.fixture()
                def boundary(stage):
                    if stage != "sealPublished":
                        return
                    path = fixture.seal_directory / "seal.json"
                    if operation == "replace-directory":
                        fixture.seal_directory.rename(fixture.seal_directory.with_name("retained-old-seal"))
                        fixture.seal_directory.mkdir(mode=0o700)
                    elif operation == "corrupt":
                        path.write_bytes(b"altered seal")
                    elif operation == "unlink":
                        path.unlink()
                    else:
                        os.link(path, fixture.seal_directory.parent / "unexpected-link")
                with self.assertRaises((ValueError, OSError)):
                    helper.initialize(fixture, boundary=boundary)
                self.assertEqual(fixture.marker.read_bytes(), b"clean")
                self.assertTrue((fixture.root / bootstrap.ARTIFACTS[0]).exists())


if __name__ == "__main__":
    unittest.main()
