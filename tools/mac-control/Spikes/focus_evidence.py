"""Offline focus-specific oracle; generic input drain is evaluated separately."""


def focus_result(trace, sink_pid):
    failed = {"result": "inconclusiveOrFailed"}
    try:
        if type(sink_pid) is not int or sink_pid <= 1:
            return {**failed, "reason": "missingSinkIdentity"}

        def rows(source, event):
            return [row for row in trace if row.get("source") == source and row.get("event") == event]

        def ns(row):
            value = row["ns"]
            if not isinstance(value, str) or not value.isascii() or not value.isdigit() or not 0 < int(value) < 2**64:
                raise ValueError("invalid timestamp")
            return int(value)

        def one(source, event):
            matches = rows(source, event)
            if len(matches) != 1:
                raise ValueError("missing or repeated event")
            return matches[0]

        launched = [row for row in rows("supervisor", "launched") if row.get("child") == "focusSink"]
        if len(launched) != 1 or launched[0].get("pid") != sink_pid:
            raise ValueError("sink launch identity")
        ready = one("focusSink", "ready")
        injection = one("supervisor", "focusInjection")
        requested = one("focusSink", "activationRequested")
        active = one("focusSink", "becameActive")
        stopped = one("worker", "stopping")
        closed = one("worker", "stopped")
        supervisor_stop = one("supervisor", "stopping")
        end = one("supervisor", "observationEnded")
        fence_request = one("supervisor", "observationFenceRequested")
        sink_fence = one("focusSink", "observationComplete")
        target_fence = one("target", "observationComplete")
        if (ready.get("pid") != sink_pid or ready.get("active") is not False
                or injection.get("pid") != sink_pid):
            raise ValueError("sink identity or initial focus")
        if not (ns(launched[0]) <= ns(injection) and ns(ready) <= ns(injection) <= ns(requested)
                <= ns(stopped) <= ns(closed) <= ns(end)
                and ns(requested) <= ns(active) <= ns(end)
                and ns(stopped) <= ns(supervisor_stop) <= ns(end)):
            raise ValueError("invalid transition order")
        if any(ns(row) > ns(end) for row in trace):
            raise ValueError("future evidence")
        for fence in (sink_fence, target_fence):
            if not ns(supervisor_stop) <= ns(fence_request) <= ns(fence) <= ns(end):
                raise ValueError("invalid observation fence order")
        if (sink_fence.get("frontmostPID") != sink_pid or sink_fence.get("isActive") is not True
                or target_fence.get("frontmostPID") != sink_pid or target_fence.get("isActive") is not False
                or active.get("frontmostPID") != sink_pid or active.get("isActive") is not True):
            raise ValueError("foreground identity missing")
        if (stopped.get("reason") not in ("wrongFocus", "readinessLost")
                or stopped.get("focusCheck") != "frontmost"
                or supervisor_stop.get("reason") != stopped.get("reason")):
            return {**failed, "reason": "notIndependentFrontmostLoss"}
        if min(ns(sink_fence), ns(target_fence)) - ns(supervisor_stop) < 2_000_000_000:
            raise ValueError("short observation")
        if ns(stopped) - ns(requested) > 1_000_000_000:
            return {**failed, "reason": "focusDetectionDeadlineExceeded"}
        # All sink input invalidates this isolated experiment, including untagged input.
        if any(rows("focusSink", event) for event in ("inputReceived", "resignedActive", "closed", "error")):
            return {**failed, "reason": "sinkInterferenceOrLoss"}
        if any(ns(row) >= ns(requested) for row in rows("target", "becameActive")):
            return {**failed, "reason": "targetReactivated"}
        if not any(ns(row) < ns(injection) for row in rows("target", "becameActive")):
            raise ValueError("missing initial target activation")
        if not any(ns(requested) <= ns(row) <= ns(end) for row in rows("target", "resignedActive")):
            raise ValueError("missing target focus loss")
        samples = rows("focusSink", "focusSample")
        after_active = [row for row in samples if ns(row) >= ns(active)]
        checkpoints = sorted([ns(active), *map(ns, after_active), ns(sink_fence)])
        if (not after_active or any(row.get("frontmostPID") != sink_pid or row.get("isActive") is not True
                                    for row in after_active)
                or any(right - left > 200_000_000 for left, right in zip(checkpoints, checkpoints[1:]))
                or ns(end) - ns(sink_fence) > 500_000_000):
            raise ValueError("missing sustained sink focus")
        if len([row for row in rows("target", "keyDown") if ns(row) < ns(injection)
                and row.get("matchesSamplePrefix") is True]) < 6:
            raise ValueError("missing pre-fault text")
        if any(ns(row) >= ns(stopped) for row in rows("supervisor", "admittedPair")):
            return {**failed, "reason": "admissionAfterStop"}
        for row in rows("worker", "posted"):
            if ns(row) >= ns(closed) or (ns(row) >= ns(stopped) and row.get("down") is not False):
                return {**failed, "reason": "postingAfterClosure"}
        return {"result": "measured", "sinkPID": sink_pid, "sinkInputEvents": 0,
                "requestToDetectionUpperBoundMs": (ns(stopped) - ns(requested)) / 1_000_000,
                "observationMs": (ns(end) - ns(supervisor_stop)) / 1_000_000}
    except (KeyError, TypeError, ValueError, OverflowError):
        return {**failed, "reason": "missingOrInvalidFocusEvidence"}
