"""Offline subprocess topology experiment; cannot launch native artifacts or input.

Observer owns all three Python children. Only the disposable supervisor retains
the worker command writer. This models EOF, not the native worker's parent PID.
"""
import argparse
import json
import os
from pathlib import Path
import selectors
import subprocess
import sys
import time

from supervisor import decode_frame

FAULTS = ("supervisor-crash", "hung-worker", "missing-fence", "late-receipt",
          "retained-writer", "recorder-exit-failure")
PEER = Path(__file__).resolve().with_name("recovery_peer.py")


class Observer:
    def __init__(self):
        self.selector = selectors.DefaultSelector()
        self.children = {}
        self.trace = []
        self.buffers = {}
        self.eof = set()
        self.forced = []
        self.exits = {}

    def record(self, source, **row):
        if len(self.trace) >= 1000:
            raise ValueError("trace limit")
        self.trace.append(dict(source=source, receivedNs=time.monotonic_ns(), **row))

    def launch(self, role, fault, fd, stdin=subprocess.PIPE):
        child = subprocess.Popen([sys.executable, "-B", str(PEER), role, fault, str(fd)],
                                 stdin=stdin, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                 pass_fds=(fd,), close_fds=True)
        self.children[role] = child
        os.set_blocking(child.stdout.fileno(), False)
        self.selector.register(child.stdout, selectors.EVENT_READ, role)
        self.buffers[role] = bytearray()
        return child

    def send(self, role, op):
        child = self.children[role]
        if child.poll() is not None:
            raise ValueError(role + " exited before " + op)
        # At most three tiny commands per peer; never a streaming writer.
        child.stdin.write((json.dumps(dict(op=op)) + "\n").encode())
        child.stdin.flush()

    def rows(self, source, event):
        return [r for r in self.trace if r["source"] == source and r["event"] == event]

    def pump(self, timeout):
        for key, _ in self.selector.select(timeout):
            source = key.data
            data = os.read(key.fileobj.fileno(), 4096)
            if not data:
                self.selector.unregister(key.fileobj)
                self.eof.add(source)
                if self.buffers[source]:
                    raise ValueError("partial frame at EOF")
                self.record(source, event="streamEOF", ns=time.monotonic_ns())
                continue
            buf = self.buffers[source]
            for byte in data:
                if byte != 10:
                    if len(buf) >= 1024:
                        raise ValueError("frame limit")
                    buf.append(byte)
                    continue
                row = decode_frame(bytes(buf))
                buf.clear()
                if (type(row.get("event")) is not str or type(row.get("ns")) is not int
                        or not 0 < row["ns"] <= time.monotonic_ns()
                        or set(row) - {"event", "ns", "tag", "heldKeysEmpty"}):
                    raise ValueError("invalid peer evidence")
                self.record(source, **row)

    def until(self, predicate, seconds=2):
        deadline = time.monotonic() + seconds
        while not predicate():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("observation deadline")
            self.pump(min(remaining, 0.02))

    def cleanup(self):
        # All children here are disposable Python fixtures retained by Popen.
        # Native target kill policy is deliberately not implemented by this tool.
        for child in self.children.values():
            if child.stdin is not None:
                try:
                    child.stdin.close()
                except (BrokenPipeError, OSError):
                    pass
        # Reap the writer before waiting for its reader. Otherwise a recorder
        # waiting for source EOF can be killed merely because the worker hung.
        for role in ("supervisor", "worker", "recorder"):
            child = self.children.get(role)
            if child is None:
                continue
            try:
                child.wait(timeout=0.5)
            except subprocess.TimeoutExpired:
                child.kill()
                self.forced.append(role)
        for role, child in self.children.items():
            try:
                self.exits[role] = child.wait(timeout=1)
            except subprocess.TimeoutExpired:
                self.exits[role] = None
            child.stdout.close()
        self.selector.close()


def run(output, fault="supervisor-crash"):
    if fault not in FAULTS:
        raise ValueError("unsupported synthetic fault")
    # Exclusive creation prevents overwriting earlier evidence, even on failure.
    output = Path(output)
    with output.open("x", encoding="utf-8") as evidence_file:
        os.chmod(output, 0o600)
        observer = Observer()
        fds = set()
        before = after = None
        error = None
        recorder_survived = False
        try:
            read_commands, write_commands = os.pipe()
            fds.update((read_commands, write_commands))
            read_events, write_events = os.pipe()
            fds.update((read_events, write_events))
            observer.launch("recorder", fault, read_events)
            os.close(read_events)
            fds.remove(read_events)
            observer.launch("worker", fault, write_events, stdin=read_commands)
            for fd in (read_commands, write_events):
                os.close(fd)
                fds.remove(fd)
            observer.launch("supervisor", fault, write_commands)
            if fault != "retained-writer":
                os.close(write_commands)
                fds.remove(write_commands)
            observer.until(lambda: all(observer.rows(role, "ready") for role in observer.children))
            observer.send("supervisor", "pair")
            observer.until(lambda: len(observer.rows("worker", "posted")) == 2
                           and len(observer.rows("recorder", "receipt")) == 2)
            # Crash is requested only after the complete pair reached the recorder.
            before = time.monotonic_ns()
            observer.send("supervisor", "crash")
            observer.until(lambda: observer.children["supervisor"].poll() is not None)
            after = time.monotonic_ns()
            observer.until(lambda: "worker" in observer.eof
                           and bool(observer.rows("recorder", "sourceEOF")), seconds=0.5)
            recorder_survived = observer.children["recorder"].poll() is None
            observer.record("observer", event="fenceRequested", ns=time.monotonic_ns())
            observer.send("recorder", "observeEnd")
            observer.until(lambda: bool(observer.rows("recorder", "observationComplete")), seconds=0.5)
        except (OSError, ValueError, TimeoutError) as exc:
            error = type(exc).__name__ + ": " + str(exc)
        finally:
            for fd in fds:
                os.close(fd)
            observer.cleanup()

        posts = observer.rows("worker", "posted")
        receipts = observer.rows("recorder", "receipt")
        stopped = observer.rows("worker", "stopped")
        command_eof = observer.rows("worker", "commandEOF")
        fault_rows = observer.rows("supervisor", "crashing")
        bracket_valid = (before is not None and after is not None and len(fault_rows) == 1
                         and before <= fault_rows[0]["ns"] <= after)
        contained = (bracket_valid and len(command_eof) == 1
                     and before <= command_eof[0]["ns"] <= before + 500_000_000
                     and observer.exits == {"recorder": 0, "worker": 0, "supervisor": 17}
                     and not observer.forced)
        synthetic_drain = (contained and recorder_survived and error is None
                           and [r.get("tag") for r in posts] == [1, 2]
                           and [r.get("tag") for r in receipts] == [1, 2]
                           and len(stopped) == 1 and stopped[0].get("heldKeysEmpty") is True
                           and len(observer.rows("worker", "observationComplete")) == 1
                           and len(observer.rows("recorder", "observationComplete")) == 1)
        result = dict(result="passed" if synthetic_drain else "inconclusiveOrFailed",
                      scope="syntheticProcessesOnly", fault=fault, error=error,
                      faultBracketNs=dict(before=before, after=after),
                      transportContained=contained, syntheticDrainComplete=synthetic_drain,
                      nativeDrainVerified=False, restartEligible=False,
                      recorderSurvivedSupervisor=recorder_survived,
                      forcedChildren=observer.forced, exits=observer.exits, trace=observer.trace)
        json.dump(result, evidence_file, indent=2)
        evidence_file.write("\n")
        evidence_file.flush()
        os.fsync(evidence_file.fileno())
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    parser.add_argument("--fault", choices=FAULTS, default="supervisor-crash")
    args = parser.parse_args()
    result = run(args.output, args.fault)
    print(json.dumps({key: value for key, value in result.items() if key != "trace"}))
    raise SystemExit(0 if result["result"] == "passed" else 2)
