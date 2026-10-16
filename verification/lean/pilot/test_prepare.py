#!/usr/bin/env python3
"""Local archive, fixture and freeze integrity tests; never contacts a model."""
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

import prepare


REPO = Path(__file__).resolve().parents[3]
ARCHIVE = REPO / ".archive/e1-2026-10-16-q0geNh/raw-evidence.zip"


class FileSafetyTests(unittest.TestCase):
    def test_missing_and_symlink_fail_honestly(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            with self.assertRaisesRegex(ValueError, "missing regular"):
                prepare.regular_bytes(root / "absent")
            (root / "outside").write_bytes(b"real")
            (root / "link").symlink_to(root / "outside")
            with self.assertRaisesRegex(ValueError, "symlink"):
                prepare.regular_bytes(root / "link")
            (root / "directory-link").symlink_to(root, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "symlink"):
                prepare.regular_bytes(root / "directory-link/outside")
            (root / "hardlink").hardlink_to(root / "outside")
            with self.assertRaisesRegex(ValueError, "hardlinked"):
                prepare.regular_bytes(root / "hardlink")

    def test_unsafe_relative_names(self):
        for name in ("../outside", "/outside", "inside/../../outside"):
            with self.assertRaises(ValueError):
                prepare.relative_name(name)


@unittest.skipUnless(ARCHIVE.is_file(), "machine-local historical archive absent")
class HistoricalPreparationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.output = Path(cls.tmp.name).resolve() / "frozen"
        cls.result = prepare.prepare(REPO, cls.output)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_original_evidence_and_reduced_scope(self):
        with zipfile.ZipFile(ARCHIVE) as archive:
            original = json.loads(archive.read(prepare.S17_BASE + "fixture.json"))
            for name, content in original["files"].items():
                self.assertEqual((self.output / "sessions/S17/project" / name).read_bytes(), content.encode())
            self.assertEqual((self.output / "sessions/S17/prompt.txt").read_bytes(), original["prompt"].encode())
            self.assertFalse((self.output / "sessions/S17/project/docs/USER_ACCEPTANCE_2026-10-16.md").exists())
            inventory = archive.read(prepare.S19_BASE + "project/migration/inventory.md")
            self.assertEqual(inventory, (self.output / "sessions/S19/project/migration/inventory.md").read_bytes())
        receipts = json.loads((self.output / "provenance/S19-computed-receipts.json").read_bytes())["comparisons"]
        self.assertEqual(len(receipts), 7)
        self.assertTrue(all(row["equal"] for row in receipts))
        self.assertEqual([row["source"] for row in receipts if not row["recorded_matches"]], ["docs/IMPLEMENTATION_PLAN.md", "docs/sessions/2026-10-16.md"])
        self.assertFalse((self.output / "sessions/S19/S19-computed-receipts.json").exists())

    def test_complete_source_render_and_manifest(self):
        manifest = json.loads((self.output / "manifest.json").read_bytes())
        self.assertEqual(manifest["historical_source_files"], 91)
        self.assertEqual(len(list((self.output / "historical/rendered").rglob("*.*"))), 91)
        for source in prepare.current_sources(REPO):
            relative = source.relative_to(REPO)
            if relative.as_posix() not in prepare.MUTABLE:
                self.assertEqual((self.output / "source" / relative).read_bytes(), source.read_bytes())
        root = self.output / "sessions/routing"
        entry = (root / "globals/AGENTS.md").read_bytes()
        self.assertIn(str(root / "master").encode(), entry)
        self.assertNotIn(b"[LOCAL_DIRECTIONS_PATH]", entry)
        self.assertNotIn(str(REPO).encode(), (root / "master/codex/skills/directions/SKILL.md").read_bytes())
        for case in ("S17", "S19"):
            case_root = self.output / "sessions" / case
            for entry_path in ("project/AGENTS.md", "globals/AGENTS.md"):
                rendered_entry = (case_root / entry_path).read_bytes()
                self.assertNotIn(str(REPO).encode(), rendered_entry)
                if entry_path.startswith("globals/"):
                    self.assertIn(str(case_root / "master").encode(), rendered_entry)
                else:
                    self.assertEqual(rendered_entry, (case_root / "master/AGENTS.md").read_bytes())
        with zipfile.ZipFile(ARCHIVE) as archive:
            for name in prepare.MUTABLE:
                self.assertEqual((self.output / "source" / name).read_bytes(), archive.read("source/final/" + name))
        self.assertTrue(prepare.verify_manifest(self.output))
        sizes = self.result["sizes"]["routing"]
        self.assertEqual(sizes["configured_entry_total_bytes"], sum((root / p).stat().st_size for p in ("globals/AGENTS.md", "master/AGENTS.md")))
        self.assertIsNone(sizes["measured_retrieval_bytes"])
        self.assertLess(sizes["readable_retrieval_total_bytes"], sizes["available_retrieval_total_bytes"])
        self.assertNotIn("master/34_testing.md", sizes["readable_retrieval_bytes"])
        s17 = self.result["sizes"]["S17"]
        self.assertEqual(len(s17["configured_fixture_evidence_file_bytes"]), 9)
        self.assertEqual(s17["configured_fixture_evidence_total_bytes"], sum(s17["configured_fixture_evidence_file_bytes"].values()))
        self.assertEqual(len(self.result["sizes"]["S19"]["configured_fixture_evidence_file_bytes"]), 15)

    def test_exclusive_output(self):
        with self.assertRaises(FileExistsError):
            prepare.prepare(REPO, self.output)

    def test_output_must_be_outside_checkout(self):
        with self.assertRaisesRegex(ValueError, "separate"):
            prepare.prepare(REPO, REPO / "forbidden-pilot-output")

    def test_extra_directory_symlink_rejected(self):
        link = self.output / "outside-link"
        link.symlink_to(Path("/private/tmp"), target_is_directory=True)
        try:
            with self.assertRaisesRegex(ValueError, "symlink"):
                prepare.verify_manifest(self.output)
        finally:
            link.unlink()

    def test_manifest_detects_alteration_missing_and_symlink(self):
        target = self.output / "sessions/S19/project/migration/inventory.md"
        original = target.read_bytes()
        try:
            target.write_bytes(original + b"changed")
            with self.assertRaisesRegex(ValueError, "changed"):
                prepare.verify_manifest(self.output)
            target.unlink()
            with self.assertRaisesRegex(ValueError, "inventory"):
                prepare.verify_manifest(self.output)
            target.symlink_to(self.output / "source/AGENTS.md")
            with self.assertRaisesRegex(ValueError, "symlink"):
                prepare.verify_manifest(self.output)
        finally:
            target.unlink(missing_ok=True)
            target.write_bytes(original)
        self.assertTrue(prepare.verify_manifest(self.output))

    def test_altered_archive_rejected_before_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            altered = root / "altered.zip"
            data = bytearray(ARCHIVE.read_bytes())
            data[100] ^= 1
            altered.write_bytes(data)
            with self.assertRaisesRegex(ValueError, "pinned"):
                prepare.prepare(REPO, root / "must-not-exist", altered)
            self.assertFalse((root / "must-not-exist").exists())


if __name__ == "__main__":
    unittest.main()
