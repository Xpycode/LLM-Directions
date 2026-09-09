"""Serialized admission controller; disk work and identity setup run elsewhere."""
from pathlib import Path
import queue
import threading
import time

import recovery_record as model
from recovery_storage import RecordWriter


class AdmissionError(ValueError):
    pass


class Admission:
    WRITE_NS = 400_000_000

    def __init__(self, writer, identity, now):
        self.writer = writer
        self.gate = model.WriteGate(model.new_record(identity))
        self.closed = False
        self.initialized = False
        self.next_sequence = 1
        self.pending = None
        self.deadline = None
        self._submit(model.encode(self.gate.record), now)

    @property
    def record(self):
        return self.gate.record

    @property
    def resolved(self):
        return (not self.closed and self.pending is None and self.initialized
                and self.record["state"] == "resolved")

    @property
    def can_reserve(self):
        return (not self.closed and self.initialized and self.pending is None
                and self.record["state"] in ("prepared", "resolved"))

    def _fail(self, reason):
        self.stop()
        raise AdmissionError(reason)

    def _submit(self, data, now):
        self.pending = data
        self.deadline = now + self.WRITE_NS
        try:
            self.writer.submit(data)
        except (ValueError, OSError):
            self._fail("recordWriteFailed")

    def poll(self, now):
        """Return exact accepted writer bytes once; never reconstruct from disk.

        A caller may bind the final resolved acknowledgement to its independently
        collected owned evidence before injecting a controlled worker crash.
        Existing callers may ignore the return value; this grants no new permit.
        """
        if self.closed:
            return
        if self.pending is not None and now >= self.deadline:
            self._fail("recordWriteTimeout")
        result = self.writer.poll()
        if result is None:
            return
        if result.error is not None or self.pending is None or result.data != self.pending:
            self._fail("recordWriteFailed")
        if self.initialized:
            try:
                self.gate.acknowledge(result.data)
            except ValueError:
                self._fail("recordWriteFailed")
        self.initialized = True
        self.pending = self.deadline = None
        return result.data

    def reserve(self, down_tag, now):
        if not self.can_reserve:
            self._fail("recordAdmissionMismatch")
        self._submit(self.gate.stage(model.reserve_pair(self.record, down_tag)), now)

    def permits(self, sequence, tag):
        record = self.record
        return (not self.closed and self.initialized and self.pending is None
                and record["state"] == "uncertain" and sequence == self.next_sequence
                and sequence <= record["sequence"] and record["events"][sequence - 1]["tag"] == tag)

    def consume(self, sequence, tag):
        if not self.permits(sequence, tag):
            self._fail("recordAdmissionMismatch")
        if sequence % 2 == 1:
            self.gate.consume_dispatch()
        self.next_sequence += 1

    def resolve(self, sequence, evidence, now):
        record = self.record
        expected = {event["tag"] for event in record["events"]}
        kinds = {event["tag"]: event["kind"] for event in record["events"]}
        if (self.closed or self.pending is not None or sequence != record["sequence"]
                or self.next_sequence != sequence + 1 or evidence.duplicate
                or expected != evidence.admitted or expected != evidence.posted
                or expected != set(evidence.received) or expected != evidence.verified_origin
                or evidence.received_kind != kinds or evidence.posted_kind != kinds
                or evidence.valid_text != set(evidence.down_counts)):
            self._fail("recordCheckpointMismatch")
        receipts = [dict(sequence=event["sequence"], tag=event["tag"],
                         kind=evidence.received_kind[event["tag"]]) for event in record["events"]]
        proof = dict(identity=record["identity"], sequence=sequence,
                     tag=record["events"][-1]["tag"], held=[], receipts=receipts)
        self._submit(self.gate.stage(model.checkpoint(record, proof)), now)

    def stop(self):
        self.closed = True
        self.gate.stop()
        self.writer.close()


class RecoverySetup:
    """One owned setup thread; no I/O or join in poll/close. Never signals a PID."""
    def __init__(self, runtime, run_id, children, paths, artifact_codes):
        self._cancel = threading.Event()
        self._results = queue.SimpleQueue()
        self.finished = threading.Event()
        self._writer = None
        self._thread = threading.Thread(target=self._run,
                                       args=(runtime, run_id, dict(children), dict(paths), dict(artifact_codes)),
                                       name="spike-recovery-setup", daemon=True)
        self._thread.start()

    def _run(self, runtime, run_id, children, paths, artifact_codes):
        try:
            from recovery_identity import capture_identity
            identity = capture_identity(run_id, children, paths)
            model.require(all(identity[role]["code"] == artifact_codes[role]
                              for role in ("worker", "target")))
            if self._cancel.is_set():
                return
            directory = Path(runtime) / "recovery"
            directory.mkdir(mode=0o700)
            self._writer = RecordWriter(directory)
            self._results.put((identity, self._writer))
        except Exception:
            self._results.put(None)
        finally:
            if self._cancel.is_set() and self._writer is not None:
                self._writer.close()
            self.finished.set()

    def poll(self):
        if self._cancel.is_set():
            return None
        try:
            result = self._results.get_nowait()
        except queue.Empty:
            return None
        if result is None:
            raise AdmissionError("recoveryIdentityUnavailable")
        return result

    def close(self):
        self._cancel.set()
        if self._writer is not None:
            self._writer.close()

    def wait_released(self, timeout):
        """Post-input only: bound setup completion and writer resource release.

        close() must precede this call. Setup can still be creating a writer when
        cancelled; waiting for its finally block closes that publication race.
        A timeout is unresolved and never permits a snapshot or another run.
        """
        model.require(self._cancel.is_set() and 0 <= timeout <= 2)
        deadline = time.monotonic() + timeout
        if not self.finished.wait(timeout):
            return False
        return (self._writer is None or
                self._writer.finished.wait(max(0, deadline - time.monotonic())))
