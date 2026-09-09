"""Exercise the real supervisor loop with synthetic peers, never native processes.

The clock, selector and child pipe endpoints are deterministic substitutes. This
covers transport sequencing and verdict integration, not AppKit or input APIs.
"""
from collections import deque
from contextlib import ExitStack
import json
import os
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import supervisor
from test_recovery_admission import FakeWriter
from test_recovery_record import identity
from client import SAMPLE


class Stream:
    def __init__(self, fd, on_close=lambda: None):
        self.fd, self.on_close, self.closed = fd, on_close, False

    def fileno(self):
        return self.fd

    def close(self):
        self.closed = True
        self.on_close()


class Peer:
    def __init__(self, rig, name, pid):
        self.rig, self.name, self.pid = rig, name, pid
        self.returncode = None
        self.stdin = Stream(pid * 2, self.finish)
        self.stdout = Stream(pid * 2 + 1)
        self.killed = False

    def poll(self):
        return self.returncode

    def finish(self):
        if self.returncode is not None:
            return
        if self.name != "focusSink" or self.rig.sink_exit != "timeout":
            self.returncode = self.rig.sink_exit if self.name == "focusSink" else 0

    def wait(self, timeout):
        if self.returncode is None:
            raise subprocess.TimeoutExpired(self.name, timeout)
        return self.returncode

    def kill(self):
        self.killed = True
        self.returncode = -9


class SyntheticTransport:
    def __init__(self, sink_exit=0, focus_check="frontmost", missing_fence=None):
        self.ns = 1_000_000_000
        self.sink_exit, self.focus_check = sink_exit, focus_check
        self.missing_fence = missing_fence
        self.streams, self.queues, self.peers = {}, {}, {}
        self.outputs, self.delivered, self.launches, self.activations = [], [], [], []
        self.client, self.output = Stream(90000), Stream(90001)
        self.queue(self.client, {"v": 1, "op": "typeText", "text": SAMPLE})
        self.active = False
        self.real_read, self.real_write = os.read, os.write
        self.record_writer = FakeWriter()

    def recovery_setup(self, runtime, run_id, children, paths, artifact_codes):
        bound_identity = identity()
        bound_identity["run"] = run_id
        for role in ("worker", "target"):
            bound_identity[role]["pid"] = children[role].pid
        return SimpleNamespace(poll=lambda: (bound_identity, self.record_writer),
                               close=self.record_writer.close)

    def queue(self, stream, row):
        self.queues.setdefault(stream.fileno(), deque()).append(row)

    def emit(self, name, event, **fields):
        self.queue(self.peers[name].stdout, dict(source=name, event=event, ns=str(self.ns), **fields))

    def popen(self, args, **kwargs):
        name = Path(args[0]).name
        self.launches.append((name, list(self.delivered)))
        peer = Peer(self, name, 10000 + len(self.peers))
        self.peers[name] = peer
        if name == "focusSink":
            self.emit(name, "ready", pid=peer.pid, active=False)
        else:
            self.emit(name, "ready", pid=peer.pid)
            if name == "target":
                self.emit(name, "becameActive")
        return peer

    def register(self, stream, events, source):
        self.streams[stream.fileno()] = SimpleNamespace(fileobj=stream, data=source)

    def unregister(self, stream):
        del self.streams[stream.fileno()]

    def select(self, timeout):
        self.ns += 10_000_000
        self.queue(self.client, {"v": 1, "op": "heartbeat"})
        worker = self.peers.get("worker")
        if worker and worker.poll() is None and self.ns % 500_000_000 == 0:
            self.emit("worker", "heartbeat")
        if self.active and self.ns % 50_000_000 == 0:
            self.emit("focusSink", "focusSample", frontmostPID=self.peers["focusSink"].pid,
                      isActive=True)
        ready = [(key, 1) for fd, key in list(self.streams.items()) if self.queues.get(fd)]
        for peer in self.peers.values():
            fd = peer.stdout.fileno()
            if peer.poll() is not None and fd in self.streams and not self.queues.get(fd):
                ready.append((self.streams[fd], 1))
        return sorted(ready, key=lambda item: item[0].data == "worker")

    def close(self):
        pass

    def read(self, fd, size):
        if fd not in self.streams:
            return self.real_read(fd, size)
        if not self.queues.get(fd):
            return b''
        row = self.queues[fd].popleft()
        self.delivered.append((self.streams[fd].data, row))
        return (json.dumps(row) + "\n").encode()

    def write(self, fd, data):
        if fd == self.output.fileno():
            self.outputs.append(json.loads(data))
            return len(data)
        peer = next((peer for peer in self.peers.values() if peer.stdin.fileno() == fd), None)
        if peer is None:
            return self.real_write(fd, data)
        row = json.loads(data)
        if row["op"] == "bind":
            self.base = row["tagBase"]
            self.run_id = row.get("run")
            self.emit("worker", "bound")
        elif row["op"] == "event":
            tag = self.base + row["sequence"]
            # Receipt deliberately precedes posting. Twelve receipts alone must
            # not trigger activation while the last worker post is outstanding.
            fields = dict(count=(row['sequence'] + 1) // 2, matchesSamplePrefix=True) if row['down'] else {}
            self.emit("target", "keyDown" if row["down"] else "keyUp", tag=tag,
                      sourcePID=self.peers["worker"].pid, **fields)
            self.emit("worker", "posted", tag=tag, down=row["down"])
            if not row["down"]:
                self.emit("worker", "checkpoint", run=self.run_id, sequence=row["sequence"],
                          tag=tag, heldKeysEmpty=True)
        elif row["op"] == "activate":
            self.activations.append(list(self.delivered))
            self.active = True
            self.emit("focusSink", "activationRequested")
            self.emit("focusSink", "becameActive", frontmostPID=self.peers["focusSink"].pid, isActive=True)
            self.emit("target", "resignedActive")
            self.emit("worker", "stopping", reason="wrongFocus", focusCheck=self.focus_check)
        elif row["op"] == "stop":
            self.emit("worker", "stopped", heldKeysEmpty=True, clipboard='untouched')
            peer.returncode = 0
        elif row["op"] == "observeEnd":
            if peer.name != self.missing_fence:
                self.emit(peer.name, "observationComplete", isActive=peer.name == "focusSink",
                          frontmostPID=self.peers["focusSink"].pid)
        return len(data)


class FocusSupervisorTests(unittest.TestCase):
    def run_transport(self, rig=None, focus_loss=True, worker_crash=False, **options):
        rig = rig if rig is not None else SyntheticTransport(**options)
        with tempfile.TemporaryDirectory(prefix="focus-supervisor-test-") as directory:
            root = Path(directory).resolve()
            runtime = root / "trace"
            runtime.mkdir()
            lock = root / "lock"
            lock.write_bytes(b"unresolved")
            lock.chmod(0o600)
            def acquire(run_id=None):
                owner = supervisor.MarkerLock.acquire(root)
                if getattr(rig, 'locked_reconciliation', False):
                    owner.write_marker(b'unresolved:' + run_id.encode())
                return owner
            with ExitStack() as stack:
                replacements = {
                    "mac_clock": lambda: lambda: rig.ns,
                    "verified_artifacts": lambda *_: (
                        {name: Path("/synthetic") / name for name in ("worker", "focusSink", "target")},
                        {"worker": "a" * 64, "target": "b" * 64}),
                    "experiment_lock": acquire,
                    "capture_bounded_context": lambda **_: dict(
                        boot=identity()['boot'], session=identity()['session'],
                        checked_ns=rig.ns, inventory_complete=True, executors=[]),
                    "RecoverySetup": rig.recovery_setup,
                    "tempfile.mkdtemp": lambda **_: str(runtime),
                    "subprocess.Popen": rig.popen,
                    "selectors.DefaultSelector": lambda: rig,
                    "os.read": rig.read, "os.write": rig.write,
                    "os.set_blocking": lambda *_: None,
                    "signal.signal": lambda *_: None,
                    "sys.stdin": SimpleNamespace(buffer=rig.client), "sys.stdout": rig.output,
                }
                for name, replacement in replacements.items():
                    stack.enter_context(patch("supervisor." + name, replacement))
                code = supervisor.run("/synthetic", focus_loss=focus_loss, worker_crash=worker_crash)
            trace = [json.loads(line) for line in (runtime / "events.jsonl").read_text().splitlines()]
            marker = lock.read_bytes()
        return rig, code, trace, marker

    def test_full_loop_launches_ready_sink_before_target_and_injects_after_complete_pairs(self):
        rig, code, trace, marker = self.run_transport()
        self.assertEqual(code, 0)
        self.assertEqual([name for name, _ in rig.launches], ["worker", "focusSink", "target"])
        before_target = rig.launches[2][1]
        self.assertTrue(any(source == "focusSink" and row["event"] == "ready"
                            for source, row in before_target))
        self.assertEqual(len(rig.activations), 1)
        before_activation = rig.activations[0]
        receipts = {row["tag"] for source, row in before_activation
                    if source == "target" and row["event"] in ("keyDown", "keyUp")}
        posts = {row["tag"] for source, row in before_activation
                 if source == "worker" and row["event"] == "posted"}
        self.assertEqual(len(receipts), 12)
        self.assertEqual(receipts, posts)
        result = [row for row in rig.outputs if row["event"] == "result"]
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["focus"]["result"], "measured")
        self.assertTrue(result[0]["drainVerified"])
        self.assertEqual(marker, b"clean")
        self.assertTrue(all(peer.stdin.closed and not peer.killed for peer in rig.peers.values()))

    def test_valid_drain_does_not_hide_missing_frontmost_cause(self):
        rig, code, _, _ = self.run_transport(focus_check="windowUnavailable")
        self.assertEqual(code, 2)
        result = [row for row in rig.outputs if row["event"] == "result"][-1]
        self.assertTrue(result["drainVerified"])
        self.assertEqual(result["result"], "inconclusiveOrFailed")
        self.assertEqual(result["focus"]["reason"], "notIndependentFrontmostLoss")

    def test_sink_teardown_failure_cannot_leave_successful_exit(self):
        for failure, event in ((7, "focusSinkExitFailed"), ("timeout", "focusSinkStillOpen")):
            with self.subTest(failure=failure):
                rig, code, _, marker = self.run_transport(sink_exit=failure)
                self.assertEqual(code, 2)
                results = [row for row in rig.outputs if row["event"] == "result"]
                self.assertEqual(len(results), 1)
                # The measurement is reported before teardown; the exit code and
                # teardown error must revoke the caller's overall success.
                self.assertEqual(results[0]["result"], "measured")
                self.assertIn(event, [row["event"] for row in rig.outputs])
                self.assertEqual(marker, b"unresolved")
                self.assertTrue(rig.peers["focusSink"].stdin.closed)
                self.assertFalse(rig.peers["focusSink"].killed)

    def test_missing_either_observation_fence_cannot_pass(self):
        for name in ("target", "focusSink"):
            with self.subTest(child=name):
                rig, code, trace, _ = self.run_transport(missing_fence=name)
                self.assertEqual(code, 2)
                result = [row for row in rig.outputs if row["event"] == "result"][-1]
                self.assertEqual(result["result"], "inconclusiveOrFailed")
                self.assertIn("observationFenceTimeout", [row["event"] for row in trace])


if __name__ == "__main__":
    unittest.main()
