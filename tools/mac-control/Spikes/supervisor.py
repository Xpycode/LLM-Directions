#!/usr/bin/env python3
"""Single supervised experiment; not the production broker or a bootstrap proof."""
import argparse
import ctypes
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

from focus_evidence import focus_result
from recovery_admission import Admission, AdmissionError, RecoverySetup
from recovery_evidence import OwnedEvidence, check_recovery
from recovery_snapshot import MarkerLock
from recovery_verifier import Verdict
from recovery_probe import capture_bounded_context

MAX_FRAME = 1024


def valid_checkpoint(row, run_id, sequence, tag, previous):
    """Only explicit current-boundary state from the owned worker pipe counts."""
    return (set(row) in ({"event", "ns", "run", "sequence", "tag", "heldKeysEmpty"},
                        {"source", "event", "ns", "run", "sequence", "tag", "heldKeysEmpty"})
            and row.get("source", "worker") == "worker" and row.get("event") == "checkpoint"
            and row.get("run") == run_id and type(row.get("sequence")) is int
            and row["sequence"] == sequence and sequence > previous and sequence % 2 == 0
            and type(row.get("tag")) is int and row["tag"] == tag
            and row.get("heldKeysEmpty") is True)


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
        self.received_kind = {}
        self.posted = set()
        self.posted_kind = {}
        self.invalid_receipt = False
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
                kind = "down" if event == "keyDown" else "up"
                self.received_kind[tag] = kind
                self.invalid_receipt |= kind != ("down" if tag in self.down_counts else "up")
                if self.worker_pid is not None and row.get("sourcePID") == self.worker_pid:
                    self.verified_origin.add(tag)
                if (event == "keyDown" and row.get("matchesSamplePrefix") is True
                        and row.get("count") == self.down_counts.get(tag)):
                    self.valid_text.add(tag)
        if source == "worker" and event == "posted":
            self.duplicate |= row["tag"] in self.posted
            self.posted.add(row["tag"])
            self.posted_kind[row["tag"]] = ("down" if row.get("down") is True else
                                            "up" if row.get("down") is False else None)
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
                  and not self.invalid_receipt
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


def verified_artifacts(directory, focus_loss=False):
    root = Path(directory).resolve(strict=True)
    manifest = json.loads((root / "artifacts.json").read_text())
    paths = {}
    artifacts = {"worker": "StopSpikeWorker",
                 "target": "StopSpikeTarget.app/Contents/MacOS/StopSpikeTarget"}
    if focus_loss:
        artifacts["focusSink"] = "StopSpikeFocusSink.app/Contents/MacOS/StopSpikeFocusSink"
    for name, relative in artifacts.items():
        path = root / relative
        if path.is_symlink() or path.resolve(strict=True) != path or not path.is_file():
            raise ValueError("invalid artifact")
        if hashlib.sha256(path.read_bytes()).hexdigest() != manifest[name]:
            raise ValueError("artifact changed since build")
        paths[name] = path
    return paths, {name: manifest[name] for name in paths}


def experiment_lock(run_id=None, *, activation=None):
    """Exclude concurrent spike runs; a dirty marker blocks automatic crash retries."""
    # Python's name table omits this Darwin extension. unistd.h defines its ABI value.
    root = Path(os.confstr(65537)) / "directions-stop-spike" # _CS_DARWIN_USER_TEMP_DIR
    if activation is None:
        try:
            root.mkdir(mode=0o700)
        except FileExistsError:
            pass
    info = root.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.geteuid() or stat.S_IMODE(info.st_mode) != 0o700:
        raise ValueError("unsafe experiment directory")
    owner = MarkerLock.acquire(root.resolve(strict=True), create=activation is None)
    try:
        from recovery_activation import FENCES, consume
        if activation is not None:
            # Explicit trusted integration only: the CLI never loads a receipt
            # as authority. Consumption fully flushes this identified admission.
            consume(owner, activation, run_id)
            return owner
        # Ordinary startup rejects orphaned activation names as well as all
        # initialization evidence; a clean marker cannot erase consumption.
        for name in FENCES:
            try:
                os.stat(Path(owner.directory) / name, follow_symlinks=False)
            except FileNotFoundError:
                continue
            raise ValueError('bootstrap remains fenced; activation requires separate verification')
        owner.recheck()
        marker = owner.read_marker(139)
        if marker not in (b"", b"clean"):
            raise ValueError("unresolved previous spike; review its trace and recovery before retry")
        if run_id is not None and (type(run_id) is not str or len(run_id) != 32
                                   or any(char not in "0123456789abcdef" for char in run_id)):
            raise ValueError("invalid recovery run identity")
        unresolved = b"unresolved" if run_id is None else b"unresolved:" + run_id.encode("ascii")
        owner.write_marker(unresolved)
        return owner
    except BaseException:
        owner.close()
        raise


def reconcile_after_teardown(owner, runtime, setup, observer, now):
    """Informational verdict with uninterrupted marker ownership; no repair."""
    try:
        if setup is None or type(owner) is not MarkerLock:
            return Verdict('blocked', 'recoveryOwnershipUnavailable')
        owner.recheck()
        setup.close()
        if not setup.wait_released(2.0):
            return Verdict('blocked', 'recoveryResourcesPending')
        if observer is None:
            return Verdict('blocked', 'recoveryOwnershipUnavailable')
        return check_recovery(owner.directory, runtime,
                              lambda: capture_bounded_context(clock=now),
                              observer, now, held_lock=owner)
    except (OSError, ValueError, TypeError, AttributeError):
        return Verdict('blocked', 'recoveryReconciliationUnavailable')


def run(directory, focus_loss=False, worker_crash=False, *, activation=None):
    if focus_loss and worker_crash:
        raise ValueError("one fault per experiment")
    now = mac_clock()
    paths, artifact_codes = verified_artifacts(directory, focus_loss)
    run_id = secrets.token_hex(16)
    if activation is not None:
        lock_owner = experiment_lock(run_id, activation=activation)
    else:
        lock_owner = experiment_lock(run_id) if worker_crash else experiment_lock()
    try:
        return _run_owned(paths, artifact_codes, run_id, lock_owner, now,
                          focus_loss, worker_crash)
    finally:
        # Also release after setup, teardown or trace-write exceptions. A crash
        # marker is never cleared by this resource-lifetime guard.
        lock_owner.close()


def _run_owned(paths, artifact_codes, run_id, lock_owner, now, focus_loss, worker_crash):
    # Exclusive experiment directory. This is a trace, not a production recovery ledger.
    runtime = Path(tempfile.mkdtemp(prefix="directions-stop-spike-"))
    os.chmod(runtime, 0o700)
    journal = (runtime / "events.jsonl").open("x", encoding="utf-8")
    os.chmod(journal.name, 0o600)
    selector = selectors.DefaultSelector()
    buffers, partials, children = {}, {}, {}
    evidence = Evidence()
    base = secrets.randbelow(1 << 48) * 1024 + 1024
    checkpoint_sequence = 0
    recovery_setup = None
    setup_started = None
    admission = None
    recovery_evidence = None
    binding_sent = False
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
    focus_requested = False
    sink_ready = False
    fence_requested_at = None
    fences = set()
    required_fences = {"target", "focusSink"} if focus_loss else {"target"}
    crash_injected = False
    exit_code = 2
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
        if worker_crash:
            # The client independently retains these sanitized rows in memory.
            # Nonblocking report failure interrupts control; never wait for disk.
            report({"event": "recoveryTrace", "row": row})

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

    def send(row, name="worker"):
        child = children.get(name)
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
        if admission is not None:
            admission.stop()
        if recovery_setup is not None:
            recovery_setup.close()
        evidence.stop_ns = min(stop_at, origin_ns) if origin_ns is not None else stop_at
        send({"op": "stop"})
        log("supervisor", "stopping", reason=reason, originNs=str(evidence.stop_ns),
            detectionNs=str(stop_at), lastClientLivenessNs=str(last_client),
            clientHeartbeatAgeMs=(stop_at - last_client) / 1_000_000)

    def interrupt(_signal, _frame):
        nonlocal interrupted
        interrupted = True

    def maybe_crash():
        nonlocal crash_injected
        if (worker_crash and not crash_injected and not interrupted and stop_at is None
                and state == "active" and awaiting is None and sequence == 13
                and checkpoint_sequence == 12 and admission is not None and admission.resolved
                and recovery_evidence is not None and recovery_evidence.digest is not None
                and admission.record["sequence"] == 12 and len(evidence.admitted) == 12
                and evidence.admitted == evidence.posted == set(evidence.received)
                and evidence.verified_origin == evidence.posted
                and evidence.valid_text == set(evidence.down_counts) and not evidence.duplicate):
            owned_worker = children["worker"]
            if owned_worker.poll() is None:
                crash_injected = True
                # kill() is asynchronous: poll may still report alive below.
                # Freeze dispatch/storage before the fault so no next uncertain
                # record can overwrite the independently bound final boundary.
                admission.stop()
                before = now()
                owned_worker.kill()
                after = now()
                log("supervisor", "workerCrashInjected", pid=owned_worker.pid,
                    beforeNs=str(before), afterNs=str(after))

    signal.signal(signal.SIGINT, interrupt)
    signal.signal(signal.SIGTERM, interrupt)
    watch(sys.stdin.buffer, "client")
    log("supervisor", "runIdentity", run=run_id)
    report({"event": "trace", "directory": str(runtime)})
    try:
        while True:
            instant = now()
            if recovery_evidence is not None:
                recovery_evidence.observe_exits()
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
            if stop_at is None:
                try:
                    if recovery_setup is not None and admission is None:
                        if instant - setup_started >= 3_000_000_000:
                            raise AdmissionError("recoverySetupTimeout")
                        ready = recovery_setup.poll()
                        if ready is not None:
                            identity, writer = ready
                            recovery_evidence = OwnedEvidence(identity, children, now,
                                                              native_tag_base=base, external_reader=True)
                            admission = Admission(writer, identity, instant)
                    if admission is not None:
                        was_pending = admission.pending is not None
                        acknowledged = admission.poll(instant)
                        if was_pending and admission.pending is None:
                            snapshot = admission.record
                            log("supervisor", "recordDurable", revision=snapshot["revision"],
                                sequence=snapshot["sequence"], disposition=snapshot["state"], run=run_id)
                            if snapshot['state'] == 'resolved' and snapshot['sequence'] == 12:
                                recovery_evidence.bind_durable_record(acknowledged)
                                log('supervisor', 'recoveryEvidenceBound', sequence=12,
                                    recordSHA256=recovery_evidence.digest)
                        if admission.initialized and not binding_sent:
                            binding_sent = True
                            if not send({"op": "bind", "pid": children["target"].pid,
                                         "path": str(paths["target"]), "tagBase": base, "run": run_id}):
                                stop("workerWriteFailed")
                        if (awaiting is None and admission.pending is None
                                and admission.record["state"] == "uncertain"
                                and checkpoint_sequence == admission.record["sequence"]):
                            admission.resolve(checkpoint_sequence, evidence, instant)
                        maybe_crash()
                except AdmissionError as error:
                    stop(str(error))
            # Loss must close admission before consuming a completed durable write.
            for name, child in children.items():
                if child.poll() is not None and stop_at is None:
                    stop(name + "Exited")
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
                    dispatch_ready = not worker_crash or admission is not None
                    if admission is not None:
                        if down and admission.can_reserve:
                            try:
                                admission.reserve(tag, instant)
                                log("supervisor", "recordPending", sequence=sequence, run=run_id)
                            except AdmissionError as error:
                                stop(str(error))
                        dispatch_ready = admission.permits(sequence, tag)
                    if down and dispatch_ready:
                        evidence.reserve_pair(tag)
                        # Both down and its possible cleanup up are uncertain before posting.
                        log("supervisor", "admittedPair", downTag=tag, upTag=tag + 1)
                    if not dispatch_ready:
                        pass  # Keep servicing Stop, heartbeats and write deadlines.
                    elif send({"op": "event", "sequence": sequence,
                             "unit": ord(payload[index]), "down": down}):
                        if admission is not None:
                            admission.consume(sequence, tag)
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
                observation_ready = elapsed >= 2_000_000_000
                if worker_crash and recovery_evidence is not None:
                    observation_ready = ('worker' in recovery_evidence.exits
                                         and 'worker' in recovery_evidence.streams
                                         and instant >= max(recovery_evidence.exits['worker']['ns'],
                                                            recovery_evidence.streams['worker']['eof_ns'])
                                         + 2_000_000_000)
                if observation_ready:
                    if not (focus_loss or worker_crash):
                        break
                    if fence_requested_at is None:
                        fence_requested_at = instant
                        log("supervisor", "observationFenceRequested")
                        if worker_crash and recovery_evidence is not None:
                            recovery_evidence.request_observation()
                        else:
                            for name in sorted(required_fences):
                                if not send({"op": "observeEnd"}, name):
                                    log("supervisor", "observationFenceFailed", child=name)
                    elif instant - fence_requested_at >= (2_000_000_000 if worker_crash else 500_000_000):
                        log("supervisor", "observationFenceTimeout")
                        break
                    if fences == required_fences:
                        if worker_crash and recovery_evidence is not None:
                            if not children['target'].stdin.closed:
                                recovery_evidence.finish_target()
                            if set(recovery_evidence.exits) == set(recovery_evidence.streams) == {'worker', 'target'}:
                                break
                        else:
                            break
                if worker_crash and elapsed >= 5_000_000_000:
                    log('supervisor', 'recoveryObservationTimeout')
                    break
            for key, _ in selector.select(0.01):
                source = key.data
                try:
                    data = os.read(key.fileobj.fileno(), 4096)
                except BlockingIOError:
                    continue
                if recovery_evidence is not None and source in ('worker', 'target'):
                    recovery_evidence.ingest(source, data)
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
                    if source in ("target", "focusSink") and event == "observationComplete":
                        if fence_requested_at is None or source in fences:
                            raise ValueError("unexpected observation fence")
                        fences.add(source)
                    if source == "worker":
                        if event == "checkpoint" and worker_crash and stop_at is None:
                            if not valid_checkpoint(frame, run_id, sequence - 1,
                                                    base + sequence - 1, checkpoint_sequence):
                                stop("invalidWorkerCheckpoint")
                            else:
                                checkpoint_sequence = frame["sequence"]
                        last_worker = now()
                        if event == "ready" and not worker_ready and stop_at is None:
                            worker_ready = True
                            launch("focusSink" if focus_loss else "target")
                        if event in ("unavailable", "stopping"):
                            stop(frame.get("reason", event), int(frame["ns"]))
                        if event == "bound" and not bound and stop_at is None:
                            if worker_crash and (not binding_sent or admission is None
                                                 or not admission.initialized or admission.closed):
                                stop("unexpectedWorkerBound")
                                continue
                            bound = True
                            state = "countdown"
                            countdown_end = now() + 5_000_000_000
                            log("supervisor", "countdown", seconds=5)
                    if source == "focusSink":
                        if event == "ready" and not sink_ready and stop_at is None:
                            if frame.get("pid") != children["focusSink"].pid or frame.get("active") is not False:
                                stop("focusSinkIdentityOrActivationMismatch")
                            else:
                                sink_ready = True
                                launch("target")
                        if event in ("inputReceived", "resignedActive", "closed", "error"):
                            stop("focusSinkInterference", int(frame["ns"]))
                    if source == "target":
                        if event == "ready" and not bound and stop_at is None:
                            if frame.get("pid") != children["target"].pid:
                                stop("targetIdentityMismatch")
                            elif worker_crash:
                                if recovery_setup is not None:
                                    stop("duplicateTargetReady")
                                else:
                                    setup_started = now()
                                    recovery_setup = RecoverySetup(runtime, run_id, children, paths, artifact_codes)
                            elif not send({"op": "bind", "pid": children["target"].pid,
                                           "path": str(paths["target"]), "tagBase": base, "run": run_id}):
                                stop("workerWriteFailed")
                        if event in ("stopClicked", "closed"):
                            stop(event, int(frame["ns"]))
                        if event == "keyDown" and frame.get("tag") in evidence.admitted:
                            report({"event": "receipt", "count": len(evidence.received)})
                    # Wait for posting AND receipt, regardless of pipe-delivery ordering.
                    checkpoint_ready = (not worker_crash or (sequence - 1) % 2 == 1
                                        or checkpoint_sequence == sequence - 1)
                    if awaiting in evidence.received and awaiting in evidence.posted and checkpoint_ready:
                        awaiting = awaiting_since = None
                    # Inject only after six complete pairs, with the input monitor still enabled.
                    # Never pause dispatch to manufacture successful cancellation.
                    if (focus_loss and sink_ready and not focus_requested and stop_at is None
                            and state == "active" and len(evidence.received) >= 12
                            and awaiting is None):
                        focus_requested = True
                        log("supervisor", "focusInjection", pid=children["focusSink"].pid)
                        if not send({"op": "activate"}, "focusSink"):
                            stop("focusSinkWriteFailed")
            # Child loss without pipe EOF must also close admission.
            for name, child in children.items():
                if child.poll() is not None and stop_at is None:
                    stop(name + "Exited")
        log("supervisor", "observationEnded")
        result = evidence.result(worker is None or worker.poll() is not None)
        if focus_loss:
            result["focus"] = focus_result(trace, children.get("focusSink").pid
                                            if "focusSink" in children else None)
            if result["focus"]["result"] != "measured":
                result["result"] = "inconclusiveOrFailed"
        clean = (result["drainVerified"] or
                 (not evidence.admitted and result["workerExited"]))
        if worker_crash:
            # This fault intentionally lacks worker closure. Evidence collection
            # is not a verified drain or authorization to clear the crash marker.
            clean = False
            result.update(result="inconclusiveOrFailed", drainVerified=False,
                          crashInjected=crash_injected, restartEligible=False)
            result['recoveryEvidenceComplete'] = False
            if recovery_evidence is not None:
                try:
                    collected = recovery_evidence.evidence()
                    result['recoveryEvidenceComplete'] = True
                    log('supervisor', 'recoveryEvidenceCollected',
                        evidence=collected)
                except ValueError:
                    pass
        log("supervisor", "result", **result, reason=stop_reason)
        report({"event": "result", **result, "reason": stop_reason})
        exit_code = 0 if result["result"] == "measured" else 2
    except (ValueError, OSError, KeyError, TypeError):
        stop("harnessError")
        report({"event": "result", "result": "inconclusiveOrFailed",
                "reason": "harnessError", "gateA": "closed"})
        exit_code = 2
    finally:
        if admission is not None:
            admission.stop()
        if recovery_setup is not None:
            recovery_setup.close()
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
                exit_code = 2
                report({"event": "workerExitFailed", "exitCode": worker.returncode})
        for name in ("target", "focusSink"):
            target = children.get(name)
            if target is None:
                continue
            target.stdin.close() # Target handles EOF by graceful close, after observation ends.
            try:
                target.wait(timeout=2)
                log("supervisor", name + "Exited", pid=target.pid, exitCode=target.returncode)
                if target.returncode != 0:
                    clean = False
                    exit_code = 2
                    report({"event": name + "ExitFailed", "exitCode": target.returncode})
            except subprocess.TimeoutExpired:
                clean = False
                exit_code = 2
                report({"event": name + "StillOpen", "pid": target.pid})
        selector.close()
        if worker_crash:
            verdict = reconcile_after_teardown(lock_owner, runtime, recovery_setup,
                                               recovery_evidence, now)
            fields = dict(result=verdict.result, reason=verdict.reason,
                          restartEligible=verdict.restart_eligible,
                          nativeRecoveryVerified=verdict.native_recovery_verified)
            log('supervisor', 'recoveryReconciliation', **fields)
            report(dict(event='recoveryReconciliation', **fields))
        if recovery_evidence is not None:
            recovery_evidence.close()
        for row in trace:
            journal.write(json.dumps(row, separators=(",", ":")) + "\n")
        journal.flush()
        os.fsync(journal.fileno())
        journal.close()
        if worker_crash:
            report({"event": "recoveryTraceSaved", "rows": len(trace)})
        if clean:
            lock_owner.write_marker(b"clean")
    return exit_code


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts", required=True)
    fault = parser.add_mutually_exclusive_group()
    fault.add_argument("--focus-loss", action="store_true")
    fault.add_argument("--worker-crash", action="store_true")
    args = parser.parse_args()
    raise SystemExit(run(args.artifacts, args.focus_loss, args.worker_crash))
