#!/usr/bin/env python3
"""Exercise a verified freeze with the inert host only; never score model behavior."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import prepare


def validate(frozen, output):
    frozen, output = Path(frozen).resolve(), Path(output).absolute()
    prepare.verify_manifest(frozen)
    initial_manifest = prepare.receipt((frozen / "manifest.json").read_bytes())
    if output.parent.resolve() != output.parent or output.is_symlink():
        raise ValueError("validation output parent must be a real absolute directory")
    if output.is_relative_to(frozen) or frozen.is_relative_to(output):
        raise ValueError("validation output must be separate from frozen inputs")
    spec = importlib.util.spec_from_file_location("frozen_pilot_runner", frozen / "tools/runner.py")
    runner = importlib.util.module_from_spec(spec)
    previous_bytecode_setting = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(runner)
    finally:
        sys.dont_write_bytecode = previous_bytecode_setting
    if output.is_relative_to(runner.MASTER) or runner.MASTER.is_relative_to(output):
        raise ValueError("validation output must be separate from live master")
    output.mkdir(exist_ok=False)
    config = json.loads((frozen / "config.json").read_bytes())
    pairs = json.loads((frozen / "sessions/S19/fixture.json").read_bytes())["pairs"]
    requests = {
        "S19": [("sha256", row[key]) for row in pairs for key in ("original", "copy")]
               + [("read_file", "project/migration/inventory.md")],
        "S17": [("read_file", p) for p in ("project/IMPLEMENTED.md", "project/TEST-EVIDENCE.md", "prompt.txt")],
        "routing": [("read_file", p) for p in ("globals/AGENTS.md", "master/AGENTS.md", "fixture.json")],
    }
    for session in config["sessions"]:
        events = [{"id": 0, "tool": "discover", "arguments": {}}]
        events += [{"id": i, "tool": tool, "arguments": {"path": path}}
                   for i, (tool, path) in enumerate(requests[session["id"]], 1)]
        events.append({"final": "Inert local replay complete; no model or oracle observation."})
        transcript = output / (session["id"] + "-transcript.json")
        transcript.write_bytes(prepare.json_bytes({"events": events}))
        session["transcript"] = str(transcript)
    config_path = output / "smoke-config.json"
    config_path.write_bytes(prepare.json_bytes(config))
    result = runner.run_batch(config_path, output / "evidence")
    # These assertions exercise real tools, not planned receipts or model claims.
    if result["status"] != "complete":
        raise ValueError("local replay incomplete; inspect retained evidence")
    receipts = [json.loads(line)["result"] for line in
                (output / "evidence/S19-responses.ndjson").read_bytes().splitlines()][1:15]
    for index, row in enumerate(pairs):
        computed = []
        for offset, key in enumerate(("original", "copy")):
            data = (frozen / "sessions/S19" / row[key]).read_bytes()
            expected = {"path": row[key], "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
            if receipts[index * 2 + offset] != expected:
                raise ValueError("checksum tool receipt differs from independent actual-byte computation")
            computed.append(expected)
        if computed[0]["sha256"] != computed[1]["sha256"]:
            raise ValueError("preserved original/copy differ")
    for session in result["sessions"]:
        response = output / "evidence" / (session["id"] + "-responses.ndjson")
        if response.stat().st_size != session["returned_bytes"]:
            raise ValueError("delivered byte accounting mismatch")
    prepare.verify_manifest(frozen)
    if prepare.receipt((frozen / "manifest.json").read_bytes()) != initial_manifest:
        raise ValueError("manifest changed during replay")
    report = {
        "scope": "local fake-host integration only; E1 open; no model oracle scoring",
        "frozen_path": str(frozen),
        "manifest": initial_manifest,
        "snapshot_unchanged_before_and_after": True,
        "independent_checksum_receipts": 14,
        "original_copy_pairs_equal": 7,
        "result": result,
        "configured_sizes": json.loads((frozen / "sizes.json").read_bytes()),
    }
    (output / "validation.json").write_bytes(prepare.json_bytes(report))
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frozen", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    report = validate(args.frozen, args.output)
    print(json.dumps({"report": str(args.output / "validation.json"),
                      "status": report["result"]["status"],
                      "calls": report["result"]["calls"],
                      "returned_bytes": report["result"]["returned_bytes"]}, indent=2))
