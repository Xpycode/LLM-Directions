"""Synthetic traces exercise false-pass rejection, not native AppKit focus behavior."""
import copy
import unittest

from focus_evidence import focus_result


class FocusEvidenceTests(unittest.TestCase):
    def trace(self):
        def row(source, event, ns, **fields):
            return dict(source=source, event=event, ns=str(ns), **fields)
        trace = [row("supervisor", "launched", 1, child="focusSink", pid=123),
                 row("focusSink", "ready", 2, pid=123, active=False),
                 row("target", "becameActive", 3),
                 row("supervisor", "focusInjection", 100, pid=123),
                 row("focusSink", "activationRequested", 110),
                 row("target", "resignedActive", 120),
                 row("focusSink", "becameActive", 130, frontmostPID=123, isActive=True),
                 row("worker", "stopping", 140, reason="wrongFocus", focusCheck="frontmost"),
                 row("worker", "stopped", 150, heldKeysEmpty=True),
                 row("supervisor", "stopping", 160, reason="wrongFocus"),
                 row("focusSink", "focusSample", 2_000_000_100, frontmostPID=123, isActive=True),
                 row("supervisor", "observationEnded", 2_000_000_200),
                 row("supervisor", "observationFenceRequested", 2_000_000_160),
                 row("focusSink", "observationComplete", 2_000_000_180, frontmostPID=123, isActive=True),
                 row("target", "observationComplete", 2_000_000_180, frontmostPID=123, isActive=False)]
        trace += [row("target", "keyDown", n + 10, matchesSamplePrefix=True) for n in range(6)]
        trace += [row("focusSink", "focusSample", n * 100_000_000, frontmostPID=123, isActive=True)
                  for n in range(1, 20)]
        return trace

    def test_complete_focus_evidence(self):
        self.assertEqual(focus_result(self.trace(), 123)["result"], "measured")

    def test_missing_each_required_event_fails(self):
        trace = self.trace()
        for index in range(21):
            if index == 10: # Individual regular samples are redundant within the 200ms bound.
                continue
            with self.subTest(index=index):
                self.assertNotEqual(focus_result(trace[:index] + trace[index + 1:], 123)["result"], "measured")

    def test_other_stop_routes_cannot_pass(self):
        for reason, cause in (("unownedInput", "frontmost"), ("readinessLost", "none"),
                              ("wrongFocus", "instance"), ("wrongFocus", "windowUnavailable")):
            trace = self.trace()
            trace[7].update(reason=reason, focusCheck=cause)
            trace[9]["reason"] = reason
            self.assertNotEqual(focus_result(trace, 123)["result"], "measured")

    def test_readiness_lost_requires_frontmost_cause(self):
        trace = self.trace()
        trace[7]["reason"] = trace[9]["reason"] = "readinessLost"
        self.assertEqual(focus_result(trace, 123)["result"], "measured")

    def test_interference_reactivation_and_late_input_fail(self):
        for source, event, fields in (
                ("focusSink", "inputReceived", {"tag": 0}),
                ("focusSink", "resignedActive", {}), ("focusSink", "closed", {}),
                ("focusSink", "error", {}), ("target", "becameActive", {}),
                ("supervisor", "admittedPair", {}), ("worker", "posted", {"down": True}),
                ("worker", "posted", {"down": False})):
            trace = self.trace() + [dict(source=source, event=event, ns="200", **fields)]
            with self.subTest(event=event, fields=fields):
                self.assertNotEqual(focus_result(trace, 123)["result"], "measured")

    def test_reserved_cleanup_before_worker_closure_is_allowed(self):
        trace = self.trace() + [dict(source="worker", event="posted", ns="145", down=False)]
        self.assertEqual(focus_result(trace, 123)["result"], "measured")

    def test_identity_order_duplicates_stale_samples_and_future_timestamps_fail(self):
        base = self.trace()
        for index, changes in ((0, {"pid": 999}), (1, {"active": True}), (3, {"pid": 999}),
                               (4, {"ns": "141"}), (6, {"ns": "100"}), (7, {"ns": True}),
                               (10, {"frontmostPID": 999}), (10, {"isActive": False}),
                               (10, {"ns": "2000000201"}),
                               (11, {"ns": "2000000159"})):
            trace = copy.deepcopy(base)
            trace[index].update(changes)
            with self.subTest(index=index, changes=changes):
                self.assertNotEqual(focus_result(trace, 123)["result"], "measured")
        self.assertNotEqual(focus_result(base + [base[4]], 123)["result"], "measured")
        self.assertNotEqual(focus_result(base, None)["result"], "measured")

    def test_single_final_sample_cannot_prove_the_interval(self):
        trace = [r for r in self.trace() if r["event"] != "focusSample" or int(r["ns"]) > 2_000_000_000]
        self.assertNotEqual(focus_result(trace, 123)["result"], "measured")


if __name__ == "__main__":
    unittest.main()
