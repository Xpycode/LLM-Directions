"""Offline oracle/parser tests; imports do not launch apps or call permission/input APIs."""
import unittest

from supervisor import Evidence, decode_frame, request_text
from client import SAMPLE
from loss_timing import loss_timing


class LossTimingTests(unittest.TestCase):
    def timing(self, elapsed=3_000_000_000, case="heartbeat-loss", **changes):
        fault = {"case": case, "beforeNs": "4000000000", "afterNs": "4000000100"}
        heartbeat = {"beforeNs": "3900000000", "afterNs": "3900000100"}
        stop = {"reason": "clientEOF" if case == "disconnect" else "clientHeartbeatLost",
                "detectionNs": str(4_000_000_000 + elapsed), "lastClientLivenessNs": "3900000050",
                "clientReceivedNs": str(4_000_001_000 + max(0, elapsed))}
        return loss_timing(case, changes.get("fault", fault), changes.get("heartbeat", heartbeat),
                           changes.get("stop", stop))

    def test_exact_loss_deadline_and_one_nanosecond_over(self):
        for elapsed, expected in ((2_999_999_999, "measured"), (3_000_000_000, "measured"),
                                  (3_000_000_001, "inconclusiveOrFailed")):
            with self.subTest(elapsed=elapsed):
                self.assertEqual(self.timing(elapsed)["result"], expected)

    def test_heartbeat_age_is_separate_from_loss_duration(self):
        result = self.timing(2_950_000_000)
        self.assertEqual(result["result"], "measured")
        self.assertEqual(result["lossToDetectionUpperBoundMs"], 2950)
        self.assertGreater(result["heartbeatAgeAtDetectionMs"], 3000)
        self.assertGreater(result["heartbeatThresholdOvershootMs"], 0)

    def test_detection_inside_close_bracket_is_valid(self):
        result = self.timing(50, case="disconnect")
        self.assertEqual(result["result"], "measured")
        self.assertEqual(result["lossToDetectionLowerBoundMs"], 0)

    def test_interval_upper_bound_does_not_hide_late_detection(self):
        result = self.timing(3_000_000_001)
        self.assertLess(result["lossToDetectionLowerBoundMs"], 3000)
        self.assertEqual(result["reason"], "lossDeadlineExceeded")

    def test_missing_wrong_or_malformed_evidence_fails(self):
        for changes in ({"fault": None}, {"heartbeat": None}, {"stop": None},
                        {"stop": {"reason": "clientStop"}},
                        {"fault": {"case": "disconnect"}},
                        {"heartbeat": {"beforeNs": True, "afterNs": "3900000100"}},
                        {"heartbeat": {"beforeNs": "0", "afterNs": "3900000100"}},
                        {"heartbeat": {"beforeNs": "9" * 21, "afterNs": "3900000100"}},
                        {"heartbeat": {"beforeNs": "3900000101", "afterNs": "3900000100"}},
                        {"fault": {"case": "heartbeat-loss", "beforeNs": "4000000000", "afterNs": "1"}}):
            with self.subTest(changes=changes):
                self.assertEqual(self.timing(**changes)["result"], "inconclusiveOrFailed")

    def test_detection_before_injection_or_liveness_in_future_fails(self):
        self.assertEqual(self.timing(-1, case="disconnect")["result"], "inconclusiveOrFailed")
        stop = {"reason": "clientEOF", "detectionNs": "4000000050",
                "lastClientLivenessNs": "4000000051", "clientReceivedNs": "4000000200"}
        self.assertEqual(self.timing(case="disconnect", stop=stop)["result"], "inconclusiveOrFailed")

    def test_future_detection_or_unfinished_injection_cannot_pass(self):
        stop = {"reason": "clientEOF", "detectionNs": "4000000500",
                "lastClientLivenessNs": "3900000050", "clientReceivedNs": "4000000499"}
        self.assertEqual(self.timing(case="disconnect", stop=stop)["result"], "inconclusiveOrFailed")
        stop.update(detectionNs="4000000001", clientReceivedNs="4000000002")
        self.assertEqual(self.timing(case="disconnect", stop=stop)["result"], "inconclusiveOrFailed")

    def test_heartbeat_watchdog_cannot_pass_before_threshold(self):
        self.assertEqual(self.timing(1)["reason"], "watchdogBeforeLossThreshold")

    def test_other_cases_have_no_loss_timing_claim(self):
        self.assertEqual(loss_timing("stop-mid-entry", None, None, None), {"result": "notApplicable"})


class EvidenceTests(unittest.TestCase):
    def complete(self):
        evidence = Evidence()
        evidence.worker_pid = 4321
        evidence.reserve_pair(101)
        evidence.stop_ns = 1_000_000_000
        for tag, event in ((101, "keyDown"), (102, "keyUp")):
            evidence.observe("worker", {"event": "posted", "tag": tag, "ns": "900000000"})
            evidence.observe("worker", {"event": "ownedObserved", "tag": tag, "ns": "950000000"})
            evidence.observe("target", {"event": event, "tag": tag, "ns": "1100000000",
                                        "count": 1, "matchesSamplePrefix": True, "sourcePID": 4321})
        evidence.observe("worker", {"event": "stopped", "heldKeysEmpty": True, "ns": "1200000000"})
        return evidence

    def test_complete_delivery_and_closure_measures_drain(self):
        result = self.complete().result(True)
        self.assertEqual(result["result"], "measured")
        self.assertEqual(result["drainMs"], 200)
        self.assertEqual(result["gateA"], "closed")

    def test_exit_without_target_receipt_cannot_pass(self):
        evidence = self.complete()
        evidence.received.pop(102)
        self.assertEqual(evidence.result(True)["result"], "inconclusiveOrFailed")

    def test_late_event_after_worker_exit_fails_one_second_limit(self):
        evidence = self.complete()
        evidence.received[102] = 2_000_000_001
        self.assertEqual(evidence.result(True)["result"], "inconclusiveOrFailed")

    def test_missing_admission_closure_cannot_pass(self):
        evidence = self.complete()
        evidence.closed_ns = None
        self.assertEqual(evidence.result(True)["result"], "inconclusiveOrFailed")

    def test_held_key_or_live_worker_cannot_pass(self):
        evidence = self.complete()
        self.assertEqual(evidence.result(False)["result"], "inconclusiveOrFailed")
        evidence.held_empty = False
        self.assertEqual(evidence.result(True)["result"], "inconclusiveOrFailed")

    def test_duplicate_delivery_cannot_pass(self):
        evidence = self.complete()
        evidence.observe("target", {"event": "keyDown", "tag": 101, "ns": "1200000000"})
        self.assertEqual(evidence.result(True)["result"], "inconclusiveOrFailed")

    def test_target_loss_cannot_pass(self):
        evidence = self.complete()
        evidence.observe("target", {"event": "closed", "ns": "1200000000"})
        self.assertEqual(evidence.result(True)["result"], "inconclusiveOrFailed")

    def test_receipts_without_insertion_cannot_pass(self):
        evidence = self.complete()
        evidence.valid_text.clear()
        self.assertEqual(evidence.result(True)["result"], "inconclusiveOrFailed")
        self.assertTrue(evidence.result(True)["drainVerified"])

    def test_missing_target_origin_cannot_pass(self):
        evidence = self.complete()
        evidence.verified_origin.clear()
        self.assertEqual(evidence.result(True)["result"], "inconclusiveOrFailed")

    def test_process_directed_input_does_not_require_global_tap_receipt(self):
        evidence = self.complete()
        evidence.observed.clear()
        self.assertEqual(evidence.result(True)["result"], "measured")

    def test_no_input_is_not_a_successful_stop_test(self):
        self.assertEqual(Evidence().result(True)["result"], "inconclusiveOrFailed")

    def test_permission_failure_does_not_report_zero_millisecond_drain(self):
        evidence = Evidence()
        evidence.stop_ns = 1_000_000_000
        self.assertIsNone(evidence.result(True)["drainMs"])


class ParserTests(unittest.TestCase):
    def test_actual_client_sample_fits_the_request_boundary(self):
        self.assertEqual(request_text({"v": 1, "op": "typeText", "text": SAMPLE}), SAMPLE)
        self.assertEqual(len(SAMPLE), 110)

    def test_minimal_typed_request(self):
        row = decode_frame(b'{"v":1,"op":"typeText","text":"STOP SPIKE 0"}')
        self.assertEqual(request_text(row), "STOP SPIKE 0")

    def test_ambiguous_or_unbounded_frames_reject(self):
        for data in (b'{"op":"stop","op":"typeText"}', b'{"n":NaN}', b'[]',
                     b'\xff', b' ' * 1025):
            with self.subTest(data=data[:30]), self.assertRaises(ValueError):
                decode_frame(data)

    def test_scope_and_type_changes_reject(self):
        base = {"v": 1, "op": "typeText", "text": "STOP SPIKE 0"}
        for changes in ({"v": True}, {"op": "approve"}, {"text": "a" * 129},
                        {"text": "STOP\nSPIKE 0"}, {"pid": 1234}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                request_text({**base, **changes})


if __name__ == "__main__":
    unittest.main()
