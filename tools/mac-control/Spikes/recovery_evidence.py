"""Independent owned-pipe evidence collector for offline recovery integration.

Attach before dispatch to Popen handles and a trusted launch-time identity (the
native producer is recovery_identity.capture_identity). No report file or PID
lookup supplies exit/EOF proof. This normalized transport is exercised with Python
peers; optional native_tag_base adapts the Swift wire schema with an explicit
continuous clock. Standalone mode owns pipe reads; external_reader consumes exact
bytes from the supervisor's sole reader without registering a second reader.
The caller owns process lifetime; this collector never launches/signals a process.
"""
import copy
import hashlib
import json
import os
import selectors
import time

import recovery_record as model

MAX_FRAME = 1024
MAX_ROWS = 1024


def decode(data):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            model.require(key not in result)
            result[key] = value
        return result
    model.require(0 < len(data) <= MAX_FRAME)
    return json.loads(data, object_pairs_hook=unique)


class OwnedEvidence:
    def __init__(self, identity, children, clock=None, *, native_tag_base=None,
                 external_reader=False):
        model.check_identity(identity)
        model.require(type(children) is dict and set(children) == {"worker", "target"})
        # An explicit continuous clock is mandatory for native streams. Python's
        # default monotonic clock cannot silently stand in for the native domain.
        model.require(native_tag_base is None or callable(clock))
        self.native = None
        if native_tag_base is not None:
            from recovery_native import NativeFrames
            self.native = NativeFrames(identity, native_tag_base)
        self.identity = copy.deepcopy(identity)
        self.children = dict(children)
        self.clock = clock or time.monotonic_ns
        self.external_reader = external_reader
        self.selector = None if external_reader else selectors.DefaultSelector()
        self.buffers = {role: bytearray() for role in children}
        self.rows = {"posts": [], "receipts": [], "checkpoints": []}
        self.exits, self.streams = {}, {}
        self.fence = self.digest = None
        self.failed = self.closed = False
        self.count = 0
        try:
            for role, child in children.items():
                model.require(child.pid == identity[role]["pid"] and child.poll() is None
                              and child.stdout is not None)
                if not external_reader:
                    os.set_blocking(child.stdout.fileno(), False)
                    self.selector.register(child.stdout, selectors.EVENT_READ, role)
        except BaseException:
            self.close()
            raise

    def bind_durable_record(self, acknowledged_bytes):
        """Bind once to independently delivered final writer acknowledgement.

        Never compute this binding from the restart snapshot being evaluated.
        Missing/lost acknowledgement stays blocked, even if record bytes look valid.
        """
        try:
            model.require(not self.closed and not self.failed and self.digest is None)
            record = model.parse(acknowledged_bytes)
            model.require(record["identity"] == self.identity and record["state"] == "resolved")
            from recovery_verifier import completed_boundary
            completed_boundary(record, self.rows, self.clock())
            # Receipt collection must precede an independently observed live
            # worker. A later wait timestamp is only an exit upper bound and
            # cannot by itself rule out delivery after the actual process exit.
            model.require(not self.exits and not self.streams and
                          all(child.poll() is None for child in self.children.values()))
            self.digest = hashlib.sha256(acknowledged_bytes).hexdigest()
        except (ValueError, TypeError):
            self.failed = True
            raise ValueError("durable evidence binding rejected") from None

    def _frame(self, role, raw):
        row = decode(raw)
        model.require(type(row) is dict)
        self.count += 1
        model.require(self.count <= MAX_ROWS)
        if self.native is not None:
            normalized = self.native.normalize(role, row)
            # Diagnostics also need the same clock and row-count bounds.
            model.require(int(row["ns"]) <= self.clock())
            if normalized is None:
                return
            row = normalized
        event = row.get("event")
        fields = {
            ("worker", "posted"): "event run sequence tag kind ns",
            ("worker", "checkpoint"): "event run sequence tag held ns",
            ("target", "receipt"): "event run sequence tag kind origin_pid ns",
            ("target", "observationComplete"): "event run ns",
        }.get((role, event))
        model.require(fields is not None)
        model.keys(row, fields)
        model.require(row["run"] == self.identity["run"])
        model.number(row["ns"], 1)
        model.require(row["ns"] <= self.clock())
        if event == "observationComplete":
            model.require(self.fence is not None and "acknowledged_ns" not in self.fence)
            self.fence["acknowledged_ns"] = row["ns"]
        else:
            normalized = {key: value for key, value in row.items() if key != "event"}
            if event != "checkpoint":
                normalized.pop("run")
            target = {"posted": "posts", "receipt": "receipts", "checkpoint": "checkpoints"}[event]
            # Preserve ordering, actual kinds, duplicates and late rows verbatim.
            self.rows[target].append(normalized)

    def pump(self, timeout=0):
        """Bounded select/read; call until both streams reach actual EOF and reaping completes."""
        try:
            model.require(not self.external_reader and not self.closed and not self.failed
                          and 0 <= timeout <= 0.1)
            for key, _ in self.selector.select(timeout):
                role = key.data
                data = os.read(key.fileobj.fileno(), 4096)
                if not data:
                    model.require(not self.buffers[role])
                    self.selector.unregister(key.fileobj)
                    self.streams[role] = dict(eof_ns=self.clock(), complete=True)
                    continue
                for byte in data:
                    if byte == 10:
                        self._frame(role, bytes(self.buffers[role]))
                        self.buffers[role].clear()
                    else:
                        model.require(len(self.buffers[role]) < MAX_FRAME)
                        self.buffers[role].append(byte)
            self.observe_exits()
        except (OSError, ValueError, TypeError, KeyError, RecursionError):
            self.failed = True
            raise ValueError("owned stream evidence incomplete or invalid") from None

    def ingest(self, role, data):
        """Consume exact bytes/EOF from the sole trusted supervisor pipe reader.

        Not a report-ingestion API. Call at the actual read boundary before the
        safety parser. This mode never registers or reads a second copy of a pipe.
        """
        try:
            model.require(self.external_reader and not self.closed and not self.failed
                          and role in self.children and role not in self.streams
                          and type(data) is bytes and len(data) <= 4096)
            if not data:
                model.require(not self.buffers[role])
                self.streams[role] = dict(eof_ns=self.clock(), complete=True)
                return
            for byte in data:
                if byte == 10:
                    self._frame(role, bytes(self.buffers[role]))
                    self.buffers[role].clear()
                else:
                    model.require(len(self.buffers[role]) < MAX_FRAME)
                    self.buffers[role].append(byte)
        except (OSError, ValueError, TypeError, KeyError, RecursionError):
            self.failed = True
            raise ValueError('owned reader evidence invalid') from None

    def observe_exits(self):
        model.require(not self.closed and not self.failed)
        for role, child in self.children.items():
            if role not in self.exits:
                status = child.poll()
                if status is not None:
                    self.exits[role] = dict(identity=copy.deepcopy(self.identity[role]),
                                            status=status, ns=self.clock(), method='ownedWait')

    def request_observation(self):
        """Send one fixed, input-free fence request to the retained target pipe.

        Caller must wait the verifier's observation interval before calling. No
        retry: short writes, early requests and missing acknowledgements block.
        """
        try:
            model.require(not self.failed and not self.closed and self.fence is None
                          and "worker" in self.exits and "worker" in self.streams
                          and self.children["target"].poll() is None)
            from recovery_verifier import OBSERVATION_NS
            now = self.clock()
            model.require(now >= max(self.exits["worker"]["ns"], self.streams["worker"]["eof_ns"])
                          + OBSERVATION_NS)
            self.fence = dict(run=self.identity["run"], target=copy.deepcopy(self.identity["target"]),
                              requested_ns=now)
            pipe = self.children["target"].stdin
            model.require(pipe is not None)
            fd = pipe.fileno()
            os.set_blocking(fd, False)
            data = b'{"op":"observeEnd"}\n'
            model.require(os.write(fd, data) == len(data))
        except (OSError, ValueError, TypeError, AttributeError):
            self.failed = True
            raise ValueError("observation request rejected") from None

    def evidence(self):
        model.require(not self.failed and not self.closed and self.digest is not None
                      and set(self.exits) == set(self.streams) == {"worker", "target"}
                      and self.fence is not None and "acknowledged_ns" in self.fence)
        return copy.deepcopy(dict(identity=self.identity, record_sha256=self.digest,
                                  **self.rows, exits=self.exits, streams=self.streams,
                                  fence=self.fence, end_ns=self.clock()))

    def finish_target(self):
        """Close the owned target's input only after its acknowledged fence.

        Native targets keep recording after observeEnd. The caller must continue
        pumping through stdout EOF and owned wait; closing stdin is not exit proof.
        No signal or process lookup is used. Repeated/early close rejects.
        """
        try:
            model.require(not self.failed and not self.closed and self.fence is not None
                          and "acknowledged_ns" in self.fence)
            pipe = self.children['target'].stdin
            model.require(pipe is not None and not pipe.closed)
            pipe.close()
        except (OSError, ValueError, TypeError, AttributeError):
            self.failed = True
            raise ValueError('target completion rejected') from None

    def close(self):
        self.closed = True
        if self.selector is not None:
            self.selector.close()


def check_recovery(marker_directory, run_directory, context_probe, observer=None,
                   clock=time.monotonic_ns, *, held_lock=None):
    """Read-only transaction over two locked namespaces and an owned observer.

    Directories and context_probe are trusted application configuration, never
    report fields. Probe must independently enumerate all managed executors and
    OS boot/login identity. Pass the independently tested recovery_context probe
    explicitly; no native default is installed. Native streams also require a
    probe and transaction clock in the same continuous-time domain. Two fresh
    context samples bracket evidence capture under locks.
    A verdict expires when locks release and never enables admission.
    """
    from recovery_snapshot import locked_snapshot
    from recovery_verifier import Verdict, context_snapshot, verify
    try:
        with locked_snapshot(marker_directory, run_directory, held_lock=held_lock) as snapshot:
            start = clock()
            before = copy.deepcopy(context_probe())
            context_snapshot(before)
            model.require(start <= before["checked_ns"] <= clock())
            evidence = None
            if observer is not None:
                model.require(type(observer) is OwnedEvidence)
                evidence = observer.evidence()
            after = copy.deepcopy(context_probe())
            context_snapshot(after)
            model.require(before["checked_ns"] <= after["checked_ns"] <= clock())
            model.require((before["boot"], before["session"]) == (after["boot"], after["session"]))
            result = verify(snapshot.marker, snapshot.record, after, evidence)
            snapshot.recheck()
        return result
    except (OSError, ValueError, TypeError, KeyError, AttributeError, RecursionError):
        return Verdict("blocked", "snapshotOrIndependentEvidenceUnresolved")
