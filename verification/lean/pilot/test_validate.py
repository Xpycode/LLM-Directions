"""Integration regressions for frozen execution and pre-write output isolation."""
from pathlib import Path
import sys
import tempfile
import unittest

import prepare
import validate


REPO = Path(__file__).resolve().parents[3]


@unittest.skipUnless((REPO / ".archive/e1-2026-10-16-q0geNh/raw-evidence.zip").is_file(),
                     "machine-local historical archive absent")
class ValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.base = Path(cls.temp.name).resolve()
        cls.frozen = cls.base / "frozen"
        prepare.prepare(REPO, cls.frozen)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_alias_into_freeze_refused_before_writes(self):
        alias = self.base / "alias"
        alias.symlink_to(self.frozen, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "real absolute"):
            validate.validate(self.frozen, alias / "must-not-exist")
        self.assertFalse((self.frozen / "must-not-exist").exists())
        self.assertTrue(prepare.verify_manifest(self.frozen))

    def test_live_master_output_refused_before_writes(self):
        output = REPO / "pilot-validation-must-not-exist"
        self.assertFalse(output.exists())
        with self.assertRaisesRegex(ValueError, "live master"):
            validate.validate(self.frozen, output)
        self.assertFalse(output.exists())

    def test_verified_frozen_runner_preserves_snapshot_without_bytecode(self):
        previous = sys.dont_write_bytecode
        try:
            sys.dont_write_bytecode = False
            report = validate.validate(self.frozen, self.base / "smoke")
            self.assertFalse(sys.dont_write_bytecode)
        finally:
            sys.dont_write_bytecode = previous
        self.assertEqual(report["independent_checksum_receipts"], 14)
        self.assertEqual(report["result"]["calls"], 24)
        self.assertEqual(report["result"]["status"], "complete")
        self.assertTrue(report["snapshot_unchanged_before_and_after"])
        self.assertFalse((self.frozen / "tools/__pycache__").exists())


if __name__ == "__main__":
    unittest.main()
