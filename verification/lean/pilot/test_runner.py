"""Local boundary tests; never launch a model, provider CLI, network or app."""
import hashlib
import json
import os
from pathlib import Path
import signal
import tempfile
import unittest

import runner


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="directions-pilot-test-")
        self.base = Path(self.temp.name)
        self.root = self.base / "fixture"
        self.root.mkdir()
        (self.root / "hello").write_text("héllo\n")

    def tearDown(self):
        self.temp.cleanup()

    def run_case(self, events, limits=None, extra=None, more=None):
        transcript = self.base / "transcript.json"
        transcript.write_text(json.dumps({"events": events}))
        session = {"id": "S19", "root": str(self.root), "transcript": str(transcript),
                   "limits": limits or {}}
        session.update(extra or {})
        config = self.base / "config.json"
        config.write_text(json.dumps({"sessions": [session] + (more or [])}))
        evidence = self.base / "evidence"
        result = runner.run_batch(config, evidence)
        self.assertEqual(result, json.loads((evidence / "summary.json").read_text()))
        if result["sessions"][0]["process_launched"]:
            self.assertIsNotNone(result["sessions"][0]["exit_code"])
        return result, evidence

    @staticmethod
    def call(tool, path="hello", ident=1):
        return {"id": ident, "tool": tool, "arguments": {} if tool == "discover" else {"path": path}}

    def test_receipts_reads_discovery_and_utf8_accounting(self):
        result, evidence = self.run_case([self.call("discover"), self.call("list_files", "."),
                                         self.call("sha256"), self.call("read_file"), {"final": "done"}])
        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["calls"], 4)
        responses = (evidence / "S19-responses.ndjson").read_bytes()
        self.assertEqual(result["returned_bytes"], len(responses))
        parsed = [json.loads(line) for line in responses.splitlines()]
        self.assertEqual(parsed[2]["result"], {"path": "hello", "bytes": 7,
                         "sha256": hashlib.sha256("héllo\n".encode()).hexdigest()})

    def test_missing_file_is_counted_error_then_continue(self):
        result, evidence = self.run_case([self.call("sha256", "missing"), {"final": "unavailable"}])
        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["calls"], 1)
        self.assertIn("FileNotFoundError", (evidence / "S19-responses.ndjson").read_text())

    def test_parallel_members_count_errors_and_stop_before_extra_dispatch(self):
        more = [{"id": "S17", "root": str(self.root), "transcript": str(self.base / "transcript.json")}]
        result, evidence = self.run_case([{"calls": [self.call("read_file", "missing", 1),
                                                    self.call("read_file", ident=2),
                                                    self.call("read_file", ident=3)]}],
                                        {"tool_calls": 2}, more=more)
        self.assertEqual(result["calls"], 2)
        self.assertEqual(result["requested_calls"], 3)
        self.assertEqual(result["status"], "stopped")
        self.assertEqual(result["unstarted_sessions"], ["S17"])
        self.assertEqual(len((evidence / "S19-responses.ndjson").read_text().splitlines()), 2)

    def test_oversized_response_preserved_not_delivered(self):
        result, evidence = self.run_case([self.call("read_file")], {"returned_bytes": 3})
        self.assertEqual(result["returned_bytes"], 0)
        self.assertEqual((evidence / "S19-responses.ndjson").read_bytes(), b"")
        events = [json.loads(line) for line in (evidence / "audit.ndjson").read_text().splitlines()]
        self.assertFalse(events[1]["delivered"])
        self.assertIn("response", events[1])

    def test_exact_response_boundary_passes(self):
        expected = runner.wire({"id": 1, "result": {"path": "hello", "text": "héllo\n"}})
        result, _ = self.run_case([self.call("read_file"), {"final": "done"}],
                                  {"returned_bytes": len(expected)})
        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["returned_bytes"], len(expected))

    def test_confinement_paths_and_links(self):
        for index, path in enumerate(["../outside", "/etc/passwd", "linked", "hard", "sub/file"]):
            with self.subTest(path=path):
                # Separate cases keep evidence exclusive.
                if (self.base / "evidence").exists():
                    import shutil
                    shutil.rmtree(self.base / "evidence")
                if index == 0:
                    (self.base / "outside").write_text("secret")
                    (self.root / "linked").symlink_to(self.base / "outside")
                    os.link(self.base / "outside", self.root / "hard")
                    (self.root / "sub").symlink_to(self.base, target_is_directory=True)
                result, _ = self.run_case([self.call("sha256", path)])
                self.assertEqual(result["status"], "stopped")
                self.assertIn("Breach", result["sessions"][0]["reason"])
        self.assertEqual((self.base / "outside").read_text(), "secret")

    def test_writes_and_native_tools_stop_without_effect(self):
        for tool in ["write_file", "shell", "web", "apps", "delegate"]:
            with self.subTest(tool=tool):
                if (self.base / "evidence").exists():
                    import shutil
                    shutil.rmtree(self.base / "evidence")
                result, _ = self.run_case([self.call(tool)])
                self.assertEqual(result["status"], "stopped")
                self.assertEqual((self.root / "hello").read_text(), "héllo\n")

    def test_routing_allowlist_blocks_topical_read(self):
        result, _ = self.run_case([self.call("read_file")], extra={"allowed_read_paths": ["AGENTS.md"]})
        self.assertEqual(result["status"], "stopped")
        self.assertIn("allowlist", result["sessions"][0]["reason"])

    def test_timeout_preserves_partial_and_terminates(self):
        result, evidence = self.run_case([self.call("sha256"), {"sleep": 30}],
                                        {"timeout_seconds": .2, "termination_grace_seconds": .1})
        item = result["sessions"][0]
        self.assertEqual(result["calls"], 1)
        self.assertIn("TimeoutError", item["reason"])
        self.assertEqual(item["exit_code"], -signal.SIGTERM)
        self.assertGreater(len((evidence / "S19-stdout.raw").read_bytes()), 0)

    def test_kill_after_term_grace(self):
        result, _ = self.run_case([{"ignore_term": True}, self.call("sha256"), {"sleep": 30}],
                                 {"timeout_seconds": .2, "termination_grace_seconds": .05})
        item = result["sessions"][0]
        self.assertTrue(item["kill_required"])
        self.assertEqual(item["exit_code"], -signal.SIGKILL)

    def test_host_failure_and_partial_protocol_preserved(self):
        result, evidence = self.run_case([{"raw": "partial"}, {"exit": 7}])
        self.assertEqual(result["status"], "stopped")
        self.assertEqual(result["sessions"][0]["exit_code"], 7)
        self.assertEqual((evidence / "S19-stdout.raw").read_bytes(), b"partial")

    def test_caps_cannot_increase(self):
        for limits in [{"tool_calls": 25}, {"returned_bytes": 96001}, {"timeout_seconds": 181},
                       {"tool_calls": 1.5}, {"returned_bytes": True}]:
            with self.subTest(limits=limits), self.assertRaises(ValueError):
                self.run_case([], limits)

    def test_evidence_in_fixture_or_master_refused(self):
        transcript = self.base / "transcript.json"
        transcript.write_text('{"events":[]}')
        config = self.base / "config.json"
        config.write_text(json.dumps({"sessions": [{"id": "S19", "root": str(self.root),
                                                    "transcript": str(transcript)}]}))
        for evidence in [self.root / "evidence", runner.MASTER / "evidence"]:
            with self.assertRaises(ValueError):
                runner.run_batch(config, evidence)

    def test_watchdog_interrupts_blocked_response_delivery(self):
        (self.root / "large").write_text("a" * 90000)
        request = json.dumps(self.call("read_file", "large")) + "\n"
        result, evidence = self.run_case([{"raw": request}, {"sleep": 30}],
                                        {"timeout_seconds": .2, "termination_grace_seconds": .1})
        self.assertEqual(result["status"], "stopped")
        self.assertLess(result["sessions"][0]["elapsed_seconds"], 3)
        delivered = (evidence / "S19-responses.ndjson").read_bytes()
        self.assertEqual(result["returned_bytes"], len(delivered))
        self.assertLess(len(delivered), 90100)
        events = [json.loads(line) for line in (evidence / "audit.ndjson").read_text().splitlines()]
        self.assertFalse(events[1]["delivered"])

    def test_final_cannot_hide_call(self):
        request = self.call("shell")
        request["final"] = "pretend complete"
        result, _ = self.run_case([request])
        self.assertEqual(result["status"], "stopped")
        self.assertEqual(result["requested_calls"], 1)
        self.assertEqual(result["calls"], 0)

    def test_master_ancestor_not_a_fixture(self):
        with self.assertRaises(ValueError):
            self.run_case([], extra={"root": str(runner.MASTER.parent)})

    def test_invalid_root_open_is_durable_incomplete(self):
        result, evidence = self.run_case([], extra={"root": str(self.root / "hello")})
        self.assertEqual(result["status"], "stopped")
        self.assertEqual(result["sessions"][0]["status"], "incomplete")
        self.assertIn("NotADirectoryError", result["sessions"][0]["reason"])
        self.assertFalse(result["sessions"][0]["process_launched"])
        self.assertTrue((evidence / "audit.ndjson").exists())

    def test_batch_max_calls_serial_no_retry_after_completed_failure(self):
        sessions = []
        for name, count in [("S19", 24), ("S17", 24), ("routing", 8)]:
            transcript = self.base / (name + ".json")
            transcript.write_text(json.dumps({"events": [self.call("sha256")] * count +
                                             [{"final": {"oracle": "fail"}}]}))
            sessions.append({"id": name, "root": str(self.root), "transcript": str(transcript)})
        config = self.base / "config.json"
        config.write_text(json.dumps({"sessions": sessions}))
        result = runner.run_batch(config, self.base / "evidence")
        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["calls"], 56)
        self.assertEqual(len(result["sessions"]), 3)
        self.assertTrue(all(s["final"]["oracle"] == "fail" for s in result["sessions"]))

    def test_response_envelope_limit_not_only_file_content(self):
        size = len("héllo\n".encode())
        result, evidence = self.run_case([self.call("read_file")], {"returned_bytes": size})
        self.assertEqual(result["status"], "stopped")
        self.assertEqual(result["returned_bytes"], 0)
        self.assertEqual((evidence / "S19-responses.ndjson").read_bytes(), b"")


if __name__ == "__main__":
    unittest.main()
