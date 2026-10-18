"""Headless in-memory policy checks; no host, network, app or profile access."""
import copy
import unittest

from host_policy import check_surface
import runner


def direct_tools():
    return [{"type": "function", "name": t["name"],
             "parameters": copy.deepcopy(t["inputSchema"])} for t in runner.TOOLS]


class HostPolicyTests(unittest.TestCase):
    def test_direct_wire_and_additional_tools(self):
        tools = direct_tools()
        self.assertEqual(check_surface({"tools": tools}), [])
        self.assertEqual(check_surface({"tools": tools[:2], "input": [
            {"type": "additional_tools", "tools": tools[2:]}]}), [])

    def test_duplicates_across_surfaces(self):
        self.assertTrue(check_surface({"tools": direct_tools(), "input": [
            {"type": "additional_tools", "tools": direct_tools()[:1]}]}))

    def test_schema_widening_and_missing_schema(self):
        for change in (lambda t: t.pop("parameters"),
                       lambda t: t["parameters"].update(additionalProperties=0),
                       lambda t: t["parameters"].update(additionalProperties=True)):
            tools = direct_tools()
            change(tools[2])
            self.assertTrue(check_surface({"tools": tools}))

    def test_extras_wrappers_and_impostors(self):
        for extra in ({"type": "function", "name": "exec"},
                      {"type": "namespace", "name": "broker", "tools": direct_tools()},
                      {"type": "custom", "name": "sha256"}):
            self.assertTrue(check_surface({"tools": direct_tools() + [extra]}))

    def test_missing_and_registration_format_rejected(self):
        self.assertTrue(check_surface({"tools": direct_tools()[:-1]}))
        self.assertTrue(check_surface({"tools": runner.TOOLS}))

    def test_malformed_inventory_fails_closed(self):
        for body in (None, {}, {"tools": None}, {"input": "text"},
                     {"tools": [None]}, {"tools": [{"name": []}]},
                     {"input": [None]},
                     {"input": [{"type": "additional_tools", "tools": None}]}):
            self.assertTrue(check_surface(body))


if __name__ == "__main__":
    unittest.main()
