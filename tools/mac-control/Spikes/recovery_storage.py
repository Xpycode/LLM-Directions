"""Experimental single-writer storage, exercised only in fresh private test namespaces.

Connected through recovery_admission in the supervisor's worker-crash case.
The caller supplies a trusted, empty directory;
this is not live bootstrap/recovery authorization or a path from an evidence report.
Public methods belong to one controlling thread. Disk I/O belongs to one dedicated
thread, which retains its directory/lock descriptors until the last write finishes.
"""
from dataclasses import dataclass
import fcntl
import os
import queue
import stat
import sys
import threading

import recovery_record as model


def flush_file(fd):
    os.fsync(fd)
    if sys.platform == "darwin":
        # Fail closed if the platform cannot flush the device write cache.
        fcntl.fcntl(fd, fcntl.F_FULLFSYNC)


def flush_directory(fd):
    os.fsync(fd)


@dataclass(frozen=True)
class WriteResult:
    data: bytes | None
    error: str | None


class RecordWriter:
    """submit/poll/close never wait for disk or join the writer.

    Creation is pre-input setup and may perform filesystem I/O. close cancels
    delivery of all acknowledgements, including already queued results. In-flight
    writes may finish; finished marks resource release, not verified input recovery.
    Keep the separate unresolved runtime marker until proper reconciliation exists.
    """

    def __init__(self, directory):
        self._directory = self._lock = None
        self._cancel = threading.Event()
        self.finished = threading.Event()
        self._requests = queue.Queue(maxsize=1)
        self._results = queue.SimpleQueue()
        self._outstanding = False
        self._last = None
        try:
            self._directory = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            info = os.fstat(self._directory)
            model.require(stat.S_ISDIR(info.st_mode) and info.st_uid == os.geteuid()
                          and stat.S_IMODE(info.st_mode) == 0o700)
            # No resume/migration path yet. Even an empty prior lock is evidence
            # of a previous attempt, not permission to initialize another run.
            model.require(not os.listdir(self._directory))
            self._lock = os.open("record.lock", os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                                 0o600, dir_fd=self._directory)
            fcntl.flock(self._lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self._thread = threading.Thread(target=self._run, name="spike-record-writer", daemon=True)
            self._thread.start()
        except BaseException:
            self._release()
            raise

    def submit(self, data):
        try:
            model.require(not self._cancel.is_set() and not self.finished.is_set()
                          and not self._outstanding)
            record = model.parse(data)
            model.require(model.encode(record) == data)
            if self._last is None:
                model.require(record["state"] == "prepared")
            else:
                # Validate same-run, next-revision transition; no permit is
                # restored by constructing this validation-only gate.
                model.WriteGate(self._last).stage(record)
            self._outstanding = True
            self._requests.put_nowait(data)
        except (ValueError, queue.Full):
            self.close()
            raise ValueError("record write rejected") from None

    def poll(self):
        if self._cancel.is_set():
            return None
        try:
            result = self._results.get_nowait()
        except queue.Empty:
            return None
        self._outstanding = False
        if result.error is not None:
            self.close()
        else:
            self._last = model.parse(result.data)
        return result

    def close(self):
        self._cancel.set()

    def _write(self, data):
        fd = None
        created = False
        try:
            fd = os.open("pending.json", os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                         0o600, dir_fd=self._directory)
            created = True
            offset = 0
            while offset < len(data):
                count = os.write(fd, data[offset:])
                if count <= 0:
                    raise OSError("incomplete record write")
                offset += count
            flush_file(fd)
            os.close(fd)
            fd = None
            os.replace("pending.json", "record.json", src_dir_fd=self._directory,
                       dst_dir_fd=self._directory)
            created = False
            flush_directory(self._directory)
        finally:
            if fd is not None:
                os.close(fd)
            if created:
                # Only remove a pending entry this writer created; never repair
                # a pre-existing path or follow one supplied by another source.
                os.unlink("pending.json", dir_fd=self._directory)

    def _run(self):
        try:
            while not self._cancel.is_set():
                try:
                    data = self._requests.get(timeout=0.01)
                except queue.Empty:
                    continue
                if self._cancel.is_set():
                    break
                try:
                    self._write(data)
                except Exception:
                    self._results.put(WriteResult(None, "durableWriteFailed"))
                    return
                self._results.put(WriteResult(data, None))
        finally:
            self._release()
            self.finished.set()

    def _release(self):
        for fd in (self._lock, self._directory):
            if fd is not None:
                os.close(fd)
