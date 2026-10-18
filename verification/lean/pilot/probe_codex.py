#!/usr/bin/env python3
"""Inspect actual Codex request tools against a loopback rejection server; no model.

Uses an empty temporary home with no credentials or inherited provider environment.
The server returns a terminal HTTP 400, never model output or tool instructions.
This is a capability probe, not an adapter, pilot, or provider acceptance test.
"""
import argparse
import hashlib
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
from pathlib import Path
import queue
import re
import shutil
import subprocess
import tempfile
import threading
import time

import runner
import host_policy


def tool_names(tools, namespace=""):
    names = []
    if not isinstance(tools, list):
        return [namespace + "<invalid-tools>"]
    for tool in tools:
        if not isinstance(tool, dict):
            names.append(namespace + "<invalid-tool>")
            continue
        name = tool.get("name", tool.get("type", "unknown"))
        if not isinstance(name, str):
            name = "<invalid-name>"
        if tool.get("type") == "namespace":
            names.extend(tool_names(tool.get("tools", []), namespace + name + "."))
        else:
            names.append(namespace + name)
    return names


def inventory(body):
    policy_errors = host_policy.check_surface(body)
    body = body if isinstance(body, dict) else {}
    tools = body.get("tools", [])
    tools = list(tools) if isinstance(tools, list) else []
    inputs = body.get("input", [])
    for item in inputs if isinstance(inputs, list) else []:
        if isinstance(item, dict) and item.get("type") == "additional_tools":
            extra = item.get("tools", [])
            if isinstance(extra, list):
                tools.extend(extra)
    names = tool_names(tools)
    allowed = {t["name"] for t in runner.TOOLS}
    # Code Mode exposes nested functions in text; an exec wrapper is itself
    # unexpected and must never be mistaken for an empty/broker-only inventory.
    declarations = sorted(set(re.findall(r"declare const tools: \{ (\w+)\(", json.dumps(tools))))
    return {"tool_names": names, "nested_text_declarations": declarations,
            "unexpected_tools": sorted(set(names) - allowed),
            "missing_direct_broker_tools": sorted(allowed - set(names)),
            "policy_id": host_policy.POLICY_ID,
            "policy_errors": policy_errors}


def assess(captured, messages):
    inventories = [inventory(row["body"]) for row in captured]
    received = [row["received"] for row in messages if "received" in row]
    completions = [v for v in received if v.get("method") == "turn/completed"]
    errors = [v for v in received if v.get("method") == "error"]
    expected = (len(captured) == 1 and captured[0]["path"] == "/v1/responses"
                and captured[0]["body"].get("model") == "gpt-6.1-sol"
                and captured[0]["body"].get("reasoning", {}).get("effort") == "medium"
                and len(completions) == 1
                and completions[0]["params"]["turn"]["status"] == "failed"
                and len(errors) == 1 and errors[0]["params"].get("willRetry") is False
                and "probe_stop" in errors[0]["params"]["error"]["message"])
    return {"status": "blocked" if not expected or any(
        i["policy_errors"] for i in inventories) else "inspection-only",
        "expected_terminal_rejection": expected, "request_count": len(captured),
        "inventories": inventories, "warnings": [v["params"]["message"] for v in received
                                                 if v.get("method") == "warning"]}


def probe(output):
    output = Path(output).absolute()
    if output.exists() or output.parent.resolve() != output.parent:
        raise ValueError("fresh output with canonical existing parent required")
    output.mkdir()
    executable = Path(shutil.which("codex") or "").resolve(strict=True)
    captured = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            body = self.rfile.read(int(self.headers.get("Content-Length", "0")))
            captured.append({"path": self.path, "body": json.loads(body)})
            data = b'{"error":{"message":"local transport probe: intentional rejection","type":"invalid_request_error","code":"probe_stop"}}'
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, *args):
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    messages = []
    pending = queue.Queue()
    process = None
    verdict = {"status": "incomplete", "live_transport_gate": "open"}
    started = time.monotonic()
    try:
        with tempfile.TemporaryDirectory(prefix="directions-codex-probe-") as temp:
            root = Path(temp)
            home = root / "home"
            cwd = root / "work"
            home.mkdir()
            cwd.mkdir()
            config = '''model = "gpt-6.1-sol"
model_provider = "local_probe"
model_reasoning_effort = "medium"
approval_policy = "never"
sandbox_mode = "read-only"
web_search = "disabled"
[model_providers.local_probe]
name = "Loopback rejection only"
wire_api = "responses"
requires_openai_auth = false
request_max_retries = 0
stream_max_retries = 0
base_url = "http://127.0.0.1:PORT/v1"
[features]
shell_tool = false
shell_snapshot = false
apps = false
hooks = false
multi_agent = false
computer_use = false
browser_use = false
in_app_browser = false
image_generation = false
view_image = false
code_mode = false
code_mode_host = false
skill_search = false
api_key_model_discovery = false
unbounded_connection_retries = false
[analytics]
enabled = false
[feedback]
enabled = false
'''.replace("PORT", str(server.server_port))
            (home / "config.toml").write_text(config)
            (output / "config.toml").write_text(config)
            env = {"HOME": str(home), "CODEX_HOME": str(home), "PATH": "/usr/bin:/bin", "TMPDIR": temp}
            version = subprocess.run([str(executable), "--version"], env=env, cwd=cwd,
                                     capture_output=True, timeout=10, check=True).stdout.decode().strip()
            with (output / "stderr.txt").open("wb") as stderr:
                process = subprocess.Popen([str(executable), "app-server", "--stdio", "--strict-config"],
                                           stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=stderr,
                                           env=env, cwd=cwd)

                def read():
                    for line in process.stdout:
                        pending.put(line)
                    pending.put(None)

                reader = threading.Thread(target=read, daemon=True)
                reader.start()
                deadline = time.monotonic() + 25

                def send(value):
                    messages.append({"sent": value})
                    process.stdin.write(runner.wire(value))
                    process.stdin.flush()

                def receive_until(predicate):
                    while True:
                        line = pending.get(timeout=max(0.001, deadline - time.monotonic()))
                        if line is None:
                            raise RuntimeError("app-server EOF")
                        value = json.loads(line)
                        messages.append({"received": value})
                        if predicate(value):
                            return value

                send({"id": 1, "method": "initialize", "params": {
                    "clientInfo": {"name": "directions_transport_probe", "version": "1"},
                    "capabilities": {"experimentalApi": True}}})
                initialized = receive_until(lambda v: v.get("id") == 1)
                if "error" in initialized:
                    raise RuntimeError(initialized["error"])
                send({"method": "initialized", "params": {}})
                send({"id": 2, "method": "thread/start", "params": {
                    "model": "gpt-6.1-sol", "modelProvider": "local_probe", "cwd": str(cwd),
                    "ephemeral": True, "approvalPolicy": "never", "sandbox": "read-only",
                    "allowProviderModelFallback": False, "environments": [],
                    "baseInstructions": "Local protocol probe. No model output is supplied.",
                    "dynamicTools": [dict(t, description="Confined local broker probe tool") for t in runner.TOOLS]}})
                thread = receive_until(lambda v: v.get("id") == 2)
                if "error" in thread:
                    raise RuntimeError(thread["error"])
                send({"id": 3, "method": "turn/start", "params": {
                    "threadId": thread["result"]["thread"]["id"],
                    "input": [{"type": "text", "text": "Local rejection probe; no model is running."}]}})
                completed = receive_until(lambda v: v.get("method") == "turn/completed")
                verdict.update(**assess(captured, messages),
                               executable=str(executable), version=version,
                               executable_sha256=hashlib.sha256(executable.read_bytes()).hexdigest(),
                               completion=completed, configured_endpoint_loopback=True,
                               outbound_network_independently_monitored=False, model_outputs=0)
    except Exception as error:
        verdict["error"] = f"{type(error).__name__}: {error}"
    finally:
        if process is not None:
            # Only this directly owned process; never a name-based app/process selection.
            if process.poll() is None:
                process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=2)
            verdict["owned_process_exit"] = process.returncode
            process.stdin.close()
            reader.join(timeout=2)
            process.stdout.close()
        server.shutdown()
        server.server_close()
        worker.join(timeout=2)
        verdict["elapsed_seconds"] = time.monotonic() - started
        for name, value in [("rpc.json", messages), ("requests.json", captured), ("result.json", verdict)]:
            (output / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    return verdict


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(probe(args.output), indent=2))
