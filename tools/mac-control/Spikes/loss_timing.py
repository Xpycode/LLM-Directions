"""Offline loss-timing oracle. Client timestamps are evidence, never control authority."""

LOSS_LIMIT_NS = 3_000_000_000
LOSS_REASONS = {"disconnect": "clientEOF", "heartbeat-loss": "clientHeartbeatLost"}


def timestamp(value):
    if (type(value) is not str or not value.isascii() or not value.isdecimal()
            or len(value) > 20 or not 0 < int(value) < 2**64):
        raise ValueError("invalid continuous-clock timestamp")
    return int(value)


def loss_timing(case, fault, heartbeat, stop):
    """Conservative upper bound from before fault injection; no scheduling tolerance."""
    if case not in LOSS_REASONS:
        return {"result": "notApplicable"}
    result = {"result": "inconclusiveOrFailed", "reason": "missingOrInvalidTiming",
              "lossToDetectionUpperBoundMs": None, "lossToDetectionLowerBoundMs": None,
              "heartbeatAgeAtDetectionMs": None, "heartbeatThresholdOvershootMs": None,
              "detectionLimitMs": LOSS_LIMIT_NS / 1_000_000}
    try:
        if fault["case"] != case or stop["reason"] != LOSS_REASONS[case]:
            return {**result, "reason": "wrongCaseOrStopReason"}
        before, after = timestamp(fault["beforeNs"]), timestamp(fault["afterNs"])
        sent_before = timestamp(heartbeat["beforeNs"])
        sent_after = timestamp(heartbeat["afterNs"])
        detected = timestamp(stop["detectionNs"])
        observed = timestamp(stop["clientReceivedNs"])
        last_received = timestamp(stop["lastClientLivenessNs"])
        # Detection can occur during close(); receive can occur during a write().
        # A sent heartbeat can still be queued, so do not equate send and receive.
        if not sent_before <= sent_after <= before <= after or detected < before:
            return result
        if last_received > detected or detected > observed or after > observed:
            return result
        age = detected - last_received
        if case == "heartbeat-loss" and age < LOSS_LIMIT_NS:
            return {**result, "reason": "watchdogBeforeLossThreshold"}
        upper = detected - before
        result.update(lossToDetectionUpperBoundMs=upper / 1_000_000,
                      lossToDetectionLowerBoundMs=max(0, detected - after) / 1_000_000,
                      heartbeatAgeAtDetectionMs=age / 1_000_000,
                      heartbeatThresholdOvershootMs=max(0, age - LOSS_LIMIT_NS) / 1_000_000)
        result.update(result="measured" if upper <= LOSS_LIMIT_NS else "inconclusiveOrFailed",
                      reason="withinLossDeadline" if upper <= LOSS_LIMIT_NS else "lossDeadlineExceeded")
        return result
    except (KeyError, TypeError, ValueError):
        return result
