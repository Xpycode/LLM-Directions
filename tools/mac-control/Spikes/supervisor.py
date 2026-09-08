#!/usr/bin/env python3
"""Single supervised experiment; not the production broker or a bootstrap proof."""
import argparse
import ctypes
import fcntl
import hashlib
import json
import os
from pathlib import Path
import secrets
import selectors
import signal
import stat
import subprocess
import sys
import tempfile

MAX_FRAME = 1024


def decode_frame(data):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate field")
            result[key] = value
        return result
    if len(data) > MAX_FRAME:
        raise ValueError("oversized frame")
    value = json.loads(data.decode("utf-8"), object_pairs_hook=unique,
                       parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite")))
    if type(value) is not dict:
        raise ValueError("object required")
    return value


def request_text(row):
    if set(row) != {"v", "op", "text"} or type(row["v"]) is not int or row["v"] != 1:
        raise ValueError("invalid request")
    text = row["text"]
    if row["op"] != "typeText" or type(text) is not str or not 12 <= len(text) <= 128:
        raise ValueError("invalid text request")
    if any(not 32 <= ord(char) <= 126 for char in text):
        raise ValueError("only printable ASCII in this experiment")
    return text


class Evidence:
    """Actual target receipts and worker closure are both required; exit is insufficient."""
    def __init__(self):
        self.admitted = set()
        self.received = {}
        self.posted = set()
        self.observed = set()
        self.worker_pid = None
        self.verified_origin = set()
        self.down_counts = {}
        self.valid_text = set()
        self.stop_ns = None
        self.closed_ns = None
        self.held_empty = False
        self.duplicate = False
        self.target_lost = False

    def reserve_pair(self, down_tag):
        self.down_counts[down_tag] = len(self.down_counts) + 1
        self.admitted.update((down_tag, down_tag + 1))

    def observe(self, source, row):
        event, ns = row["event"], int(row["ns"])
        if source == "target" and event in ("keyDown", "keyUp"):
            tag = row.get("tag")
            if tag in self.admitted:
                self.duplicate |= tag in self.received
                self.received[tag] = ns
                if self.worker_pid is not None and row.get("sourcePID") == self.worker_pid:
                    self.verified_origin.add(tag)
                if (event == "keyDown" and row.get("matchesSamplePrefix") is True
                        and row.get("count") == self.down_counts.get(tag)):
                    self.valid_text.add(tag)
        if source == "worker" and event == "posted":
            self.posted.add(row["tag"])
        if source == "worker" and event == "ownedObserved":
            self.observed.add(row["tag"])
        if source == "worker" and event == "stopped":
            self.closed_ns = ns
            self.held_empty = row.get("heldKeysEmpty") is True
        if source == "target" and event == "closed":
            self.target_lost = True

    def result(self, worker_exited):
        end = max([self.closed_ns or 0, *self.received.values()])
        complete = bool(self.admitted) and self.admitted == set(self.received) == self.posted
        latency = (max(0, end - self.stop_ns) / 1_000_000
                   if complete and self.stop_ns is not None and self.closed_ns is not None else None)
        drained = (complete and worker_exited and self.held_empty and self.closed_ns is not None
                  and self.stop_ns is not None and not self.duplicate and not self.target_lost
                  and latency is not None and latency <= 1000 and self.verified_origin == self.posted)
        passed = drained and self.valid_text == set(self.down_counts)
        return {"result": "measured" if passed else "inconclusiveOrFailed",
                "drainVerified": drained,
                "drainMs": latency, "admittedEvents": len(self.admitted),
                "receivedEvents": len(self.received), "duplicateReceipt": self.duplicate,
                "workerExited": worker_exited, "targetLost": self.target_lost,
                "ownedEventsObserved": len(self.observed), "textPrefixesVerified": len(self.valid_text),
                "targetOriginsVerified": len(self.verified_origin),
                "gateA": "closed"}


def mac_clock():
    class Timebase(ctypes.Structure):
        _fields_ = [("numer", ctypes.c_uint32), ("denom", ctypes.c_uint32)]
    lib = ctypes.CDLL("/usr/lib/libSystem.B.dylib")
    lib.mach_continuous_time.restype = ctypes.c_uint64
    info = Timebase()
    if lib.mach_timebase_info(ctypes.byref(info)) != 0 or info.denom == 0:
        raise RuntimeError("continuous clock unavailable")
    return lambda: lib.mach_continuous_time() * info.numer // info.denom


def verified_artifacts(directory):
    root = Path(directory).resolve(strict=True)
    manifest = json.loads((root / "artifacts.json").read_text())
    paths = {}
    for name, relative in {"worker": "StopSpikeWorker",
                           "target": "StopSpikeTarget.app/Contents/MacOS/StopSpikeTarget"}.items():
        path = root / relative
        if path.is_symlink() or path.resolve(strict=True) != path or not path.is_file():
            raise ValueError("invalid artifact")
        if hashlib.sha256(path.read_bytes()).hexdigest() != manifest[name]:
            raise ValueError("artifact changed since build")
        paths[name] = path
    return paths


def experiment_lock():
    """Exclude concurrent spike runs; a dirty marker blocks automatic crash retries."""
    # Python's name table omits this Darwin extension. unistd.h defines its ABI value.
    root = Path(os.confstr(65537)) / "directions-stop-spike" # _CS_DARWIN_USER_TEMP_DIR
    try:
        root.mkdir(mode=0o700)
    except FileExistsError:
        pass
    info = root.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.geteuid() or stat.S_IMODE(info.st_mode) != 0o700:
        raise ValueError("unsafe experiment directory")
    fd = os.open(root / "lock", os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        info = os.fstat(fd)
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.geteuid()
                or stat.S_IMODE(info.st_mode) != 0o600 or info.st_nlink != 1):
            raise ValueError("unsafe experiment lock")
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        marker = os.read(fd, 64)
        if marker not in (b"", b"clean"):
            raise ValueError("unresolved previous spike; review its trace and recovery before retry")
        os.lseek(fd, 0, os.SEEK_SET)
        os.write(fd, b"unresolved")
        os.ftruncate(fd, len(b"unresolved"))
        os.fsync(fd)
        return fd
    except BaseException:
        os.close(fd)
        raise


def run(directory):
    now = mac_clock()
    paths = verified_artifacts(directory)
    lock_fd = experiment_lock()
    # Exclusive experiment directory. This is a trace, not a production recovery ledger.
    runtime = Path(tempfile.mkdtemp(prefix="directions-stop-spike-"))
    os.chmod(runtime, 0o700)
    journal = (runtime / "events.jsonl").open("x", encoding="utf-8")
    os.chmod(journal.name, 0o600)
    selector = selectors.DefaultSelector()
    buffers, partials, children = {}, {}, {}
    evidence = Evidence()
    base = secrets.randbelow(1 << 48) * 1024 + 1024
    state, payload, sequence = "request", "", 1
    last_client = last_worker = last_send = now()
    start = now()
    countdown_end = None
    awaiting = None
    awaiting_since = None
    stop_at = None
    stop_reason = None
    bound = False
    worker_ready = False
    interrupted = False
    next_dispatch = 0
    clean = False
    trace = []
    os.set_blocking(sys.stdout.fileno(), False)

    def report(row):
        nonlocal interrupted
        frame = (json.dumps(row) + "\n").encode()
        try:
            if os.write(sys.stdout.fileno(), frame) != len(frame):
                interrupted = True
        except (BlockingIOError, BrokenPipeError):
            interrupted = True # Output pressure closes admission on the next loop.

    def record(row):
        # Dirty marker was fsynced before launching any child. A crash leaves that
        # marker unresolved; do not block stop/watchdogs on per-event disk writes.
        if len(trace) >= 10000:
            raise ValueError("trace limit")
        trace.append(row)

    def log(source, event, **fields):
        row = {"source": source, "event": event, "ns": str(now()), **fields}
        record(row)
        if source == "supervisor" and event in ("countdown", "active", "stopping"):
            report(row)
        return row

    def watch(stream, source):
        os.set_blocking(stream.fileno(), False)
        selector.register(stream, selectors.EVENT_READ, source)
        buffers[source] = bytearray()

    def launch(name):
        # Popen objects retain owned-child identity; never discover or signal a PID from a file.
        child = subprocess.Popen([str(paths[name])], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                 stderr=subprocess.DEVNULL, close_fds=True)
        children[name] = child
        if name == "worker":
            evidence.worker_pid = child.pid
        os.set_blocking(child.stdin.fileno(), False)
        watch(child.stdout, name)
        log("supervisor", "launched", child=name, pid=child.pid)
        return child

    def send(row):
        child = children.get("worker")
        if child is None or child.poll() is not None:
            return False
        frame = json.dumps(row, separators=(",", ":")).encode() + b"\n"
        try:
            return os.write(child.stdin.fileno(), frame) == len(frame)
        except (BrokenPipeError, BlockingIOError, OSError):
            return False

    def stop(reason, origin_ns=None):
        nonlocal state, stop_at, stop_reason
        if stop_at is not None:
            return
        state, stop_at, stop_reason = "stopping", now(), reason
        evidence.stop_ns = min(stop_at, origin_ns) if origin_ns is not None else stop_at
        send({"op": "stop"})
        log("supervisor", "stopping", reason=reason, originNs=str(evidence.stop_ns),
            detectionNs=str(stop_at), lastClientLivenessNs=str(last_client),
            clientHeartbeatAgeMs=(stop_at - last_client) / 1_000_000)

    def interrupt(_signal, _frame):
        nonlocal interrupted
        interrupted = True

    signal.signal(signal.SIGINT, interrupt)
    signal.signal(signal.SIGTERM, interrupt)
    watch(sys.stdin.buffer, "client")
    report({"event": "trace", "directory": str(runtime)})
    try:
        while True:
            instant = now()
            if interrupted:
                stop("signal")
            if instant - start >= 30_000_000_000:
                stop("experimentDeadline")
            if instant - last_client >= 3_000_000_000:
                stop("clientHeartbeatLost")
            if "worker" in children and instant - last_worker >= 3_000_000_000:
                stop("workerHeartbeatLost")
            if "worker" in children and instant - last_send >= 500_000_000 and stop_at is None:
                if not send({"op": "heartbeat"}):
                    stop("workerWriteFailed")
                last_send = instant
            if awaiting is not None and instant - awaiting_since >= 400_000_000:
                stop("eventReceiptTimeout")
            for source, since in list(partials.items()):
                if instant - since >= 3_000_000_000:
                    stop(source + "PartialFrameTimeout")
            if state == "countdown" and instant >= countdown_end:
                state = "active"
                log("supervisor", "active")
            if state == "active" and awaiting is None and instant >= next_dispatch:
                index = (sequence - 1) // 2
                if index == len(payload):
                    stop("completed")
                else:
                    down = sequence % 2 == 1
                    tag = base + sequence
                    if down:
                        evidence.reserve_pair(tag)
                        # Both down and its possible cleanup up are uncertain before posting.
                        log("supervisor", "admittedPair", downTag=tag, upTag=tag + 1)
                    if send({"op": "event", "sequence": sequence,
                             "unit": ord(payload[index]), "down": down}):
                        awaiting, awaiting_since = tag, instant
                        sequence += 1
                        next_dispatch = instant + 100_000_000
                    else:
                        stop("workerWriteFailed")
            worker = children.get("worker")
            if stop_at is not None:
                elapsed = instant - stop_at
                # Reserve 500 ms to reap only this still-owned child. Killing cannot pass evidence.
                if worker is not None and worker.poll() is None and elapsed >= 500_000_000:
                    worker.kill()
                    log("supervisor", "ownedWorkerKilled")
                # Keep target recording at least one second beyond the stop budget.
                if elapsed >= 2_000_000_000:
                    break
            for key, _ in selector.select(0.01):
                source = key.data
                try:
                    data = os.read(key.fileobj.fileno(), 4096)
                except BlockingIOError:
                    continue
                if not data:
                    selector.unregister(key.fileobj)
                    if source != "worker" or stop_at is None:
                        stop(source + "EOF")
                    if source == "target":
                        evidence.target_lost = True
                    continue
                for byte in data:
                    if byte != 10:
                        if not buffers[source]:
                            partials[source] = now()
                        if len(buffers[source]) >= MAX_FRAME:
                            stop(source + "OversizedFrame")
                            raise ValueError("oversized frame")
                        buffers[source].append(byte)
                        continue
                    frame = decode_frame(bytes(buffers[source]))
                    buffers[source].clear()
                    partials.pop(source, None)
                    if source == "client":
                        if state == "request":
                            payload = request_text(frame)
                            last_client = now()
                            state = "preflight"
                            launch("worker")
                            last_worker = now()
                        elif frame == {"v": 1, "op": "heartbeat"}:
                            last_client = now()
                        elif frame == {"v": 1, "op": "stop"}:
                            stop("clientStop")
                        else:
                            stop("invalidClientMessage")
                        continue
                    # Owned children emit sanitized diagnostics only; never journal client text.
                    event = frame.get("event")
                    if type(event) is not str or not str(frame.get("ns", "")).isdigit():
                        raise ValueError("invalid child event")
                    record({**frame, "source": source})
                    evidence.observe(source, frame)
                    if source == "worker":
                        last_worker = now()
                        if event == "ready" and not worker_ready and stop_at is None:
                            worker_ready = True
                            launch("target")
                        if event in ("unavailable", "stopping"):
                            stop(frame.get("reason", event), int(frame["ns"]))
                        if event == "bound" and not bound and stop_at is None:
                            bound = True
                            state = "countdown"
                            countdown_end = now() + 5_000_000_000
                            log("supervisor", "countdown", seconds=5)
                    if source == "target":
                        if event == "ready" and not bound and stop_at is None:
                            if frame.get("pid") != children["target"].pid:
                                stop("targetIdentityMismatch")
                            elif not send({"op": "bind", "pid": children["target"].pid,
                                           "path": str(paths["target"]), "tagBase": base}):
                                stop("workerWriteFailed")
                        if event in ("stopClicked", "closed"):
                            stop(event, int(frame["ns"]))
                        if event == "keyDown" and frame.get("tag") in evidence.admitted:
                            report({"event": "receipt", "count": len(evidence.received)})
                    # Wait for posting AND receipt, regardless of pipe-delivery ordering.
                    if awaiting in evidence.received and awaiting in evidence.posted:
                        awaiting = awaiting_since = None
            # Child loss without pipe EOF must also close admission.
            for name, child in children.items():
                if child.poll() is not None and stop_at is None:
                    stop(name + "Exited")
        result = evidence.result(worker is None or worker.poll() is not None)
        clean = (result["drainVerified"] or
                 (not evidence.admitted and result["workerExited"]))
        log("supervisor", "result", **result, reason=stop_reason)
        report({"event": "result", **result, "reason": stop_reason})
        return 0 if result["result"] == "measured" else 2
    except (ValueError, OSError, KeyError, TypeError):
        stop("harnessError")
        report({"event": "result", "result": "inconclusiveOrFailed",
                "reason": "harnessError", "gateA": "closed"})
        return 2
    finally:
        # Teardown is distinct from proof of stop. Only owned worker may be force-killed.
        worker = children.get("worker")
        if worker is not None:
            if worker.poll() is None:
                send({"op": "stop"})
                try:
                    worker.wait(timeout=0.5)
                except subprocess.TimeoutExpired:
                    worker.kill()
                    worker.wait(timeout=0.5)
            worker.stdin.close()
            log("supervisor", "workerExited", pid=worker.pid, exitCode=worker.returncode)
            if worker.returncode != 0:
                clean = False
                report({"event": "workerExitFailed", "exitCode": worker.returncode})
        target = children.get("target")
        if target is not None:
            target.stdin.close() # Target handles EOF by graceful close, after observation ends.
            try:
                target.wait(timeout=2)
                log("supervisor", "targetExited", pid=target.pid, exitCode=target.returncode)
                if target.returncode != 0:
                    clean = False
                    report({"event": "targetExitFailed", "exitCode": target.returncode})
            except subprocess.TimeoutExpired:
                clean = False
                report({"event": "targetStillOpen", "pid": target.pid})
        selector.close()
        for row in trace:
            journal.write(json.dumps(row, separators=(",", ":")) + "\n")
        journal.flush()
        os.fsync(journal.fileno())
        journal.close()
        if clean:
            os.lseek(lock_fd, 0, os.SEEK_SET)
            os.write(lock_fd, b"clean")
            os.ftruncate(lock_fd, len(b"clean"))
            os.fsync(lock_fd)
        os.close(lock_fd)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts", required=True)
    args = parser.parse_args()
    raise SystemExit(run(args.artifacts))
