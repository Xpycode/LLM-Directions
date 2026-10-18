"""No host/network launch: test inventory acceptance against wire shapes."""
import unittest
import json
from pathlib import Path

from probe_codex import inventory, assess
import runner
from test_host_policy import direct_tools


class InventoryTests(unittest.TestCase):
    def test_assessment_enforces_policy_without_granting_acceptance(self):
        folder = Path(__file__).parent / "transport-probe-2026-10-17"
        captured = json.loads((folder / "requests.json").read_text())
        messages = json.loads((folder / "rpc.json").read_text())
        captured[0]["body"]["tools"] = direct_tools()
        captured[0]["body"]["input"] = []
        self.assertEqual(assess(captured, messages)["status"], "inspection-only")
        captured[0]["body"]["tools"][2]["parameters"]["additionalProperties"] = True
        self.assertEqual(assess(captured, messages)["status"], "blocked")

    def test_malformed_surface_retains_policy_diagnostics(self):
        for body in (None, {"tools": None}, {"tools": [None]}, {"input": [None]},
                     {"tools": [{"type": "namespace", "name": [], "tools": None}]},
                     {"input": [{"type": "additional_tools", "tools": None}]}):
            self.assertTrue(inventory(body)["policy_errors"])

    def test_top_level_broker_inventory(self):
        result = inventory({"tools": runner.TOOLS})
        self.assertEqual(result["unexpected_tools"], [])
        self.assertEqual(result["missing_direct_broker_tools"], [])

    def test_additional_tools_namespace_cannot_pass_as_empty(self):
        result = inventory({"input": [{"type": "additional_tools", "tools": [
            {"type": "namespace", "name": "functions", "tools": [
                {"type": "custom", "name": "exec", "description": "tools.sha256"}]}]}]})
        self.assertEqual(result["unexpected_tools"], ["functions.exec"])
        self.assertEqual(result["missing_direct_broker_tools"], sorted(t["name"] for t in runner.TOOLS))

    def test_native_tool_alongside_broker_is_rejected(self):
        result = inventory({"tools": runner.TOOLS + [{"type": "function", "name": "apply_patch"}]})
        self.assertEqual(result["unexpected_tools"], ["apply_patch"])

    def test_absent_inventory_leaves_all_broker_tools_missing(self):
        self.assertEqual(len(inventory({})["missing_direct_broker_tools"]), 4)

    def test_wrong_namespace_does_not_impersonate_broker(self):
        result = inventory({"tools": [{"type": "namespace", "name": "other", "tools": runner.TOOLS}]})
        self.assertEqual(len(result["unexpected_tools"]), 4)
        self.assertEqual(len(result["missing_direct_broker_tools"]), 4)

    def test_retained_wire_includes_nested_broker_and_disabled_host_warning(self):
        folder = Path(__file__).parent / "transport-probe-2026-10-17"
        captured = json.loads((folder / "requests.json").read_text())
        messages = json.loads((folder / "rpc.json").read_text())
        result = assess(captured, messages)
        self.assertEqual(result["status"], "blocked")
        self.assertTrue(result["expected_terminal_rejection"])
        self.assertTrue(set(t["name"] for t in runner.TOOLS).issubset(result["inventories"][0]["nested_text_declarations"]))
        self.assertTrue(any("fail closed" in w for w in result["warnings"]))
        self.assertFalse(assess(captured * 2, messages)["expected_terminal_rejection"])
        captured[0]["path"] = "/unexpected"
        self.assertFalse(assess(captured, messages)["expected_terminal_rejection"])
