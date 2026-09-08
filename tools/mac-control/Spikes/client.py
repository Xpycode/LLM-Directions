#!/usr/bin/env python3
"""Minimal real-session transport client. Run only in the agreed foreground window."""
import argparse
import json
import os
from pathlib import Path
import selectors
import signal
import subprocess
import sys
import tempfile
import time

from loss_timing import LOSS_REASONS, loss_timing
from supervisor import mac_clock

SAMPLE = "STOP SPIKE 0123456789 " * 5


def run_case(artifacts, case):
    now = mac_clock() # Same boot clock as worker/supervisor; evidence only, never sent as authority.
    runtime = Path(tempfile.mkdtemp(prefix="directions-stop-client-"))
    os.chmod(runtime, 0o700)
    audit = {"version": 1, "case": case, "clock": "mach_continuous_time_ns",
             "startedNs": str(now()), "lastHeartbeatSend": None, "fault": None,
             "stop": None, "supervisorResult": None, "supervisorExitCode": None,
             "supervisorTraceDirectory": None, "errors": []}
    # No trace writes on heartbeat, fault injection, or active Stop paths.
    child = subprocess.Popen([sys.executable, str(Path(__file__).with_name("supervisor.py")),
                              "--artifacts", artifacts], stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE, bufsize=0)
    selector = selectors.DefaultSelector()
    selector.register(child.stdout, selectors.EVENT_READ)
    os.set_blocking(child.stdin.fileno(), False)
    stopping = False
    interrupted = False
    heartbeat = time.monotonic()
    deadline = heartbeat + 40
    buffer = bytearray()
    expected_reasons = {
        "stop-mid-entry": {"clientStop"}, "disconnect": {"clientEOF"},
        "heartbeat-loss": {"clientHeartbeatLost"}, "escape": {"escape"},
        "wrong-focus": {"wrongFocus", "readinessLost"}, "physical-key": {"unownedInput"},
        "stop-button": {"stopClicked", "unownedInput"},
    }

    def send(op, **fields):
        frame = (json.dumps({"v": 1, "op": op, **fields}) + "\n").encode()
        if os.write(child.stdin.fileno(), frame) != len(frame):
            raise OSError("partial client frame")

    def on_signal(_number, _frame):
        nonlocal interrupted
        interrupted = True

    previous_signals = {sig: signal.signal(sig, on_signal) for sig in (signal.SIGINT, signal.SIGTERM)}
    try:
        # Fixed disposable payload; no user content or configurable target.
        send("typeText", text=SAMPLE)
        while selector.get_map():
            if time.monotonic() >= deadline:
                audit["errors"].append("clientDeadline")
                break
            if interrupted and not stopping and child.poll() is None:
                send("stop")
                stopping = True
            if not stopping and child.poll() is None and time.monotonic() - heartbeat >= 0.5:
                sent_before = now()
                send("heartbeat")
                audit["lastHeartbeatSend"] = {"beforeNs": str(sent_before), "afterNs": str(now())}
                heartbeat = time.monotonic()
            for key, _ in selector.select(0.05):
                chunk = key.fileobj.read(4096)
                if not chunk:
                    selector.unregister(key.fileobj)
                    continue
                buffer.extend(chunk)
                if len(buffer) > 65536:
                    raise ValueError("oversized supervisor output")
                while b"\n" in buffer:
                    frame, _, rest = buffer.partition(b"\n")
                    buffer = bytearray(rest)
                    row = json.loads(frame)
                    if type(row) is not dict:
                        raise ValueError("invalid supervisor frame")
                    print(json.dumps(row), flush=True)
                    if row.get("event") == "trace":
                        audit["supervisorTraceDirectory"] = row.get("directory")
                    if row.get("event") == "stopping":
                        if audit["stop"] is not None:
                            raise ValueError("duplicate stop evidence")
                        audit["stop"] = {**row, "clientReceivedNs": str(now())}
                    if row.get("event") in ("targetStillOpen", "targetExitFailed", "workerExitFailed"):
                        audit["errors"].append(row["event"])
                    if row.get("event") == "result":
                        if audit["supervisorResult"] is not None:
                            raise ValueError("duplicate result evidence")
                        audit["supervisorResult"] = row
                    # Receipt count 11 is the sixth down; each previous down/up was acknowledged.
                    if row.get("event") == "receipt" and row.get("count", 0) >= 11 and not stopping:
                        if case == "stop-mid-entry":
                            send("stop")
                            stopping = True
                        elif case in LOSS_REASONS:
                            audit["fault"] = {"case": case, "beforeNs": str(now())}
                            stopping = True # Heartbeat case keeps its pipe open.
                            if case == "disconnect":
                                child.stdin.close()
                            audit["fault"]["afterNs"] = str(now())
        if buffer:
            audit["errors"].append("partialSupervisorOutput")
    except (OSError, ValueError, KeyboardInterrupt) as error:
        audit["errors"].append(type(error).__name__)
    finally:
        if not child.stdin.closed:
            child.stdin.close() # EOF revokes. Never kill the agent or the test target.
        try:
            audit["supervisorExitCode"] = child.wait(timeout=6)
        except subprocess.TimeoutExpired:
            audit["errors"].append("supervisorTeardownTimeout")
            print("Supervisor has not exited; inspect the experiment before another run.", file=sys.stderr)
        selector.close()
        child.stdout.close()
        for sig, previous in previous_signals.items():
            signal.signal(sig, previous)
    audit["finishedNs"] = str(now())
    audit["liveness"] = loss_timing(case, audit["fault"], audit["lastHeartbeatSend"], audit["stop"])
    result = audit["supervisorResult"] or {}
    matched = (result.get("reason") in expected_reasons[case]
               and (audit["stop"] or {}).get("reason") == result.get("reason"))
    audit["casePassed"] = (not audit["errors"] and audit["supervisorExitCode"] == 0 and matched
                           and result.get("result") == "measured"
                           and result.get("drainVerified") is True
                           and audit["liveness"]["result"] in ("measured", "notApplicable"))
    evidence_path = runtime / "client-evidence.json"
    try:
        with evidence_path.open("x", encoding="utf-8") as output:
            os.chmod(evidence_path, 0o600)
            json.dump(audit, output, indent=2)
            output.write("\n")
            output.flush()
            os.fsync(output.fileno())
    except OSError:
        print("Client evidence could not be saved; this case cannot pass.", file=sys.stderr)
        return 2
    print(json.dumps({"event": "caseResult", "case": case, "casePassed": audit["casePassed"],
                      "liveness": audit["liveness"], "evidence": str(evidence_path)}), flush=True)
    return 0 if audit["casePassed"] else 2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts", required=True)
    parser.add_argument("--case", choices=("stop-mid-entry", "disconnect", "heartbeat-loss",
                                          "escape", "wrong-focus", "physical-key", "stop-button"),
                        default="stop-mid-entry")
    args = parser.parse_args()
    return run_case(args.artifacts, args.case)


if __name__ == "__main__":
    raise SystemExit(main())
