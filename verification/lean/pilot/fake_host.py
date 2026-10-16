#!/usr/bin/env python3
"""Inert local NDJSON transcript replay. Never executes transcript commands/code."""
import json
import signal
import sys
import time


def main():
    events = json.loads(open(sys.argv[1]).read())["events"]
    for event in events:
        if "ignore_term" in event:
            signal.signal(signal.SIGTERM, signal.SIG_IGN)
        elif "sleep" in event:
            time.sleep(float(event["sleep"]))
        elif "exit" in event:
            return int(event["exit"])
        elif "raw" in event:
            sys.stdout.write(event["raw"]); sys.stdout.flush()
        else:
            print(json.dumps(event), flush=True)
            if "final" not in event:
                for _ in event.get("calls", [event]):
                    if not sys.stdin.readline():
                        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
