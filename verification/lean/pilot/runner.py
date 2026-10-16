#!/usr/bin/env python3
"""Local transcript transport exerciser; NOT a provider/CLI sandbox or live host adapter.

Only the bundled inert fake_host.py is launched. Responses are compact UTF-8 JSON
lines; returned-byte accounting includes the complete response line and its newline.
Each calls[] member is dispatched and counted separately, serially. No retries.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import selectors
import select
import signal
import stat
import subprocess
import sys
import time

CAPS = {"S19": (24, 96000), "S17": (24, 64000), "routing": (8, 32000)}
# This local-only runner is also frozen into scratch snapshots. Keep the actual
# live master protected even when __file__ points into that snapshot's tools/.
MASTER = Path("/Users/sim/ProgrammingProjects/0-DIRECTIONS/__DIRECTIONS").resolve()
TOOLS = [
    {"name": name, "inputSchema": {"type": "object", "properties": props,
     "required": list(props), "additionalProperties": False}}
    for name, props in [("discover", {}), ("list_files", {"path": {"type": "string"}}),
                        ("read_file", {"path": {"type": "string"}}),
                        ("sha256", {"path": {"type": "string"}})]
]


def wire(value):
    return (json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")


class Breach(Exception):
    pass


class Confined:
    """Descriptor-relative opens reject all symlinks and multiply linked files."""
    def __init__(self, root, deadline, allowed_read_paths=None):
        self.fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        self.deadline = deadline
        self.allowed = allowed_read_paths

    def close(self):
        os.close(self.fd)

    def check_time(self):
        if time.monotonic() >= self.deadline:
            raise TimeoutError("session watchdog")

    def open(self, path):
        if not isinstance(path, str) or path.startswith("/") or "\x00" in path:
            raise Breach("relative fixture path required")
        parts = path.split("/")
        if any(p in ("..", "") for p in parts) or ("." in parts and path != "."):
            raise Breach("noncanonical path")
        fd = os.dup(self.fd)
        try:
            for i, part in enumerate(parts):
                self.check_time()
                info = os.stat(part, dir_fd=fd, follow_symlinks=False)
                if stat.S_ISLNK(info.st_mode):
                    raise Breach("symlink refused")
                flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
                if i < len(parts) - 1:
                    flags |= os.O_DIRECTORY
                new = os.open(part, flags, dir_fd=fd)
                os.close(fd)
                fd = new
            info = os.fstat(fd)
            if not (stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode)):
                raise Breach("special file refused")
            if stat.S_ISREG(info.st_mode) and info.st_nlink != 1:
                raise Breach("hardlink refused")
            return fd
        except BaseException:
            os.close(fd)
            raise

    def call(self, tool, args, max_bytes):
        self.check_time()
        if tool not in {t["name"] for t in TOOLS}:
            raise Breach("tool unavailable: writes, shell, apps, web and delegation forbidden")
        if not isinstance(args, dict) or set(args) != (set() if tool == "discover" else {"path"}):
            raise ValueError("invalid arguments")
        if tool == "discover":
            return {"tools": TOOLS}
        path = args["path"]
        if tool != "list_files" and self.allowed is not None and path not in self.allowed:
            raise Breach("body read outside session allowlist")
        fd = self.open(path)
        try:
            info = os.fstat(fd)
            if tool == "list_files":
                if not stat.S_ISDIR(info.st_mode):
                    raise ValueError("directory required")
                # One directory per call: enumeration itself never follows links.
                entries = []
                for name in sorted(os.listdir(fd)):
                    self.check_time()
                    item = os.stat(name, dir_fd=fd, follow_symlinks=False)
                    if stat.S_ISLNK(item.st_mode) or (stat.S_ISREG(item.st_mode) and item.st_nlink != 1):
                        raise Breach("linked directory entry refused")
                    entries.append({"name": name, "directory": stat.S_ISDIR(item.st_mode)})
                    if len(wire(entries)) > max_bytes:
                        raise OverflowError("response byte cap")
                return {"entries": entries}
            if not stat.S_ISREG(info.st_mode):
                raise ValueError("regular file required")
            digest = hashlib.sha256()
            data = bytearray()
            count = 0
            while True:
                self.check_time()
                chunk = os.read(fd, 65536)
                if not chunk:
                    break
                count += len(chunk)
                if tool == "read_file":
                    if count > max_bytes:
                        raise OverflowError("response byte cap")
                    data.extend(chunk)
                digest.update(chunk)
            after = os.fstat(fd)
            if (info.st_size, info.st_mtime_ns, info.st_ctime_ns, info.st_nlink) != (after.st_size, after.st_mtime_ns, after.st_ctime_ns, after.st_nlink):
                raise Breach("fixture changed during read")
            if tool == "sha256":
                return {"path": path, "bytes": count, "sha256": digest.hexdigest()}
            return {"path": path, "text": bytes(data).decode("utf-8")}
        finally:
            os.close(fd)


def positive(value, ceiling):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 < value <= ceiling:
        raise ValueError("invalid limit")
    return value


def run_batch(config_path, evidence_dir):
    config = json.loads(Path(config_path).read_text())
    sessions = config["sessions"]
    if not 1 <= len(sessions) <= 3 or len({s["id"] for s in sessions}) != len(sessions):
        raise ValueError("one to three unique sessions required")
    evidence = Path(evidence_dir).resolve()
    if evidence.is_relative_to(MASTER):
        raise ValueError("evidence must be outside master")
    for s in sessions:
        if s["id"] not in CAPS:
            raise ValueError("unknown session")
        s["root"] = str(Path(s["root"]).resolve(strict=True))
        root = Path(s["root"])
        if root.is_relative_to(MASTER) or MASTER.is_relative_to(root) or evidence.is_relative_to(root) or root.is_relative_to(evidence):
            raise ValueError("fixture/evidence/master separation required")
        if "host_command" in s or "host_script" in s:
            raise ValueError("only bundled fake transport is supported")
        transcript = Path(s["transcript"]).resolve(strict=True)
        s["transcript"] = str(transcript)
        limits = s.get("limits", {})
        calls, size = CAPS[s["id"]]
        for key in ("tool_calls", "returned_bytes"):
            if key in limits and type(limits[key]) is not int:
                raise ValueError("integer call/byte limits required")
        s["caps"] = (int(positive(limits.get("tool_calls", calls), calls)),
                     int(positive(limits.get("returned_bytes", size), size)))
        s["timeout"] = positive(limits.get("timeout_seconds", 180), 180)
        s["grace"] = positive(limits.get("termination_grace_seconds", 1), 5)
    evidence.mkdir(parents=True, exist_ok=False)
    summary = {"transport": "local-fake-only; no live host parity", "status": "complete",
               "calls": 0, "requested_calls": 0, "returned_bytes": 0, "sessions": []}
    audit = (evidence / "audit.ndjson").open("wb", buffering=0)

    def log(event):
        audit.write(wire(event))
        os.fsync(audit.fileno())

    def save():
        temp = evidence / "summary.tmp"
        with temp.open("wb") as out:
            out.write(wire(summary)); out.flush(); os.fsync(out.fileno())
        temp.replace(evidence / "summary.json")

    try:
        save()
        for session in sessions:
            started = time.monotonic()
            item = {"id": session["id"], "calls": 0, "requested_calls": 0, "returned_bytes": 0,
                    "status": "incomplete", "process_launched": False, "exit_code": None,
                    "termination_grace_seconds": session["grace"]}
            summary["sessions"].append(item)
            save()
            deadline = started + session["timeout"]
            confined = None
            proc = None
            reason = None
            final = None
            raw = (evidence / (session["id"] + "-stdout.raw")).open("wb", buffering=0)
            err = (evidence / (session["id"] + "-stderr.raw")).open("wb", buffering=0)
            delivered = (evidence / (session["id"] + "-responses.ndjson")).open("wb", buffering=0)
            selector = selectors.DefaultSelector()
            try:
                confined = Confined(session["root"], deadline, session.get("allowed_read_paths"))
                proc = subprocess.Popen([sys.executable, str(Path(__file__).with_name("fake_host.py")),
                                         session["transcript"]], stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                        start_new_session=True)
                item["process_launched"] = True
                os.set_blocking(proc.stdin.fileno(), False)
                selector.register(proc.stdout, selectors.EVENT_READ, "stdout")
                selector.register(proc.stderr, selectors.EVENT_READ, "stderr")
                buf = bytearray()
                while selector.get_map():
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        raise TimeoutError("session watchdog")
                    for key, _ in selector.select(min(remaining, .1)):
                        chunk = os.read(key.fileobj.fileno(), 65536)
                        if not chunk:
                            selector.unregister(key.fileobj)
                            continue
                        (raw if key.data == "stdout" else err).write(chunk)
                        if key.data != "stdout":
                            continue
                        buf.extend(chunk)
                        if len(buf) > 1048576:
                            raise Breach("host protocol line exceeds 1 MiB")
                        while b"\n" in buf:
                            line, _, rest = buf.partition(b"\n"); buf = bytearray(rest)
                            request = json.loads(line)
                            log({"session": item["id"], "request": request})
                            if not isinstance(request, dict):
                                raise Breach("request object required")
                            calls = request.get("calls", [request] if "tool" in request else [])
                            if not isinstance(calls, list):
                                raise Breach("invalid calls batch")
                            item["requested_calls"] += len(calls)
                            summary["requested_calls"] += len(calls)
                            if "final" in request:
                                if set(request) != {"final"}:
                                    raise Breach("final cannot contain calls or extra fields")
                                if final is not None:
                                    raise Breach("duplicate final")
                                final = request["final"]
                                continue
                            if final is not None:
                                raise Breach("request after final")
                            if not calls:
                                raise Breach("invalid calls batch")
                            for call in calls:
                                if item["calls"] >= session["caps"][0] or summary["calls"] >= 56:
                                    raise OverflowError("call cap before dispatch")
                                item["calls"] += 1; summary["calls"] += 1
                                if not isinstance(call, dict):
                                    raise Breach("call object required")
                                budget = min(session["caps"][1] - item["returned_bytes"], 192000 - summary["returned_bytes"])
                                breach = None
                                try:
                                    result = confined.call(call["tool"], call.get("arguments", {}), budget)
                                    response = {"id": call.get("id"), "result": result}
                                except (Breach, TimeoutError, OverflowError) as exc:
                                    breach = exc
                                    response = {"id": call.get("id"), "error": str(exc)}
                                except (OSError, ValueError, KeyError, TypeError) as exc:
                                    response = {"id": call.get("id"), "error": type(exc).__name__ + ": " + str(exc)}
                                payload = wire(response)
                                if len(payload) > budget:
                                    log({"session": item["id"], "response": response,
                                         "response_bytes": len(payload), "delivered": False, "delivered_bytes": 0})
                                    raise OverflowError("response byte cap before delivery")
                                sent = 0
                                try:
                                    while sent < len(payload):
                                        confined.check_time()
                                        _, writable, _ = select.select([], [proc.stdin], [], max(0, deadline - time.monotonic()))
                                        if not writable:
                                            raise TimeoutError("session watchdog during response")
                                        try:
                                            n = os.write(proc.stdin.fileno(), payload[sent:])
                                        except BlockingIOError:
                                            continue
                                        delivered.write(payload[sent:sent + n])
                                        sent += n
                                        item["returned_bytes"] += n; summary["returned_bytes"] += n
                                finally:
                                    log({"session": item["id"], "response": response,
                                         "response_bytes": len(payload), "delivered": sent == len(payload),
                                         "delivered_bytes": sent})
                                save()
                                if breach:
                                    raise breach
                if buf:
                    raise Breach("truncated host protocol")
                proc.wait(timeout=max(.001, deadline - time.monotonic()))
                if proc.returncode != 0 or final is None:
                    raise RuntimeError("fake host failure or missing final")
                item.update(status="complete", final=final)
            except Exception as exc:
                reason = type(exc).__name__ + ": " + str(exc)
                item["reason"] = reason
                summary["status"] = "stopped"
                log({"session": item["id"], "stop": reason})
            finally:
                if proc is not None:
                    item["termination_requested"] = proc.poll() is None
                    if proc.poll() is None:
                        try:
                            os.killpg(proc.pid, signal.SIGTERM)
                        except ProcessLookupError:
                            pass  # The owned process exited between poll and signal.
                        try:
                            proc.wait(timeout=session["grace"])
                        except subprocess.TimeoutExpired:
                            item["kill_required"] = True
                            try:
                                os.killpg(proc.pid, signal.SIGKILL)
                            except ProcessLookupError:
                                pass
                            proc.wait()
                    item["exit_code"] = proc.returncode
                    # Preserve bytes emitted during teardown, after the host exits.
                    for pipe, output in [(proc.stdout, raw), (proc.stderr, err)]:
                        output.write(pipe.read())
                        pipe.close()
                    proc.stdin.close()
                selector.close()
                if confined is not None:
                    confined.close()
                raw.close(); err.close(); delivered.close()
                item["elapsed_seconds"] = time.monotonic() - started
                save()
            if reason:
                break
        summary["unstarted_sessions"] = [s["id"] for s in sessions[len(summary["sessions"]):]]
        save()
        return summary
    finally:
        audit.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--evidence-dir", required=True)
    args = parser.parse_args()
    result = run_batch(args.config, args.evidence_dir)
    print(json.dumps(result))
    sys.exit(0 if result["status"] == "complete" else 1)
