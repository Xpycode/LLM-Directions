"""Read-only locked snapshots of explicitly trusted, isolated spike directories.

No default runtime path, report-derived path, repair, marker clearing, process
operation or restart authority. The caller must keep evidence collection and its
decision inside the context; successful exit rechecks all opened names and bytes.
Advisory locks exclude cooperating writers, not a malicious same-UID process.
"""
from contextlib import contextmanager
import fcntl
import os
import stat

import recovery_record as model


class SnapshotError(ValueError):
    pass


def require(condition, reason="unsafeSnapshot"):
    if not condition:
        raise SnapshotError(reason)


def identity(info):
    return info.st_dev, info.st_ino


def fingerprint(info):
    return (identity(info), info.st_mode, info.st_uid, info.st_gid, info.st_nlink,
            info.st_size, info.st_mtime_ns, info.st_ctime_ns)


class _Snapshot:
    def __init__(self):
        self._fds = []
        self._edges = []
        self._directories = []
        self._files = []
        self._active = True

    def _open(self, name, flags, parent=None):
        fd = os.open(name, flags | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
        self._fds.append(fd)
        if parent is not None:
            self._edges.append((parent, name, fd))
        return fd

    def _trusted_directory(self, path):
        path = os.fspath(path)
        require(type(path) is str and path.startswith("/") and path != "/"
                and os.path.normpath(path) == path and not path.startswith("//"),
                "untrustedSnapshotPath")
        # Walk every component without following links, including ancestors.
        fd = self._open("/", os.O_RDONLY | os.O_DIRECTORY)
        for component in path.split("/")[1:]:
            fd = self._open(component, os.O_RDONLY | os.O_DIRECTORY, fd)
        self._private_directory(fd)
        self._directories.append((fd, fingerprint(os.fstat(fd))))
        return fd

    @staticmethod
    def _private_directory(fd):
        info = os.fstat(fd)
        require(stat.S_ISDIR(info.st_mode) and info.st_uid == os.geteuid()
                and stat.S_IMODE(info.st_mode) == 0o700)

    @staticmethod
    def _regular(fd):
        info = os.fstat(fd)
        require(stat.S_ISREG(info.st_mode) and info.st_uid == os.geteuid()
                and stat.S_IMODE(info.st_mode) == 0o600 and info.st_nlink == 1)
        return info

    def _read(self, fd, limit):
        before = self._regular(fd)
        require(before.st_size <= limit, "snapshotTooLarge")
        data = os.pread(fd, limit + 1, 0)
        require(len(data) <= limit and len(data) == before.st_size
                and fingerprint(before) == fingerprint(self._regular(fd)),
                "snapshotChanged")
        return data, fingerprint(before)

    def _file(self, parent, name, limit, lock=False):
        fd = self._open(name, os.O_RDONLY, parent)
        self._regular(fd)
        if lock:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise SnapshotError("snapshotBusy") from None
        data, stamp = self._read(fd, limit)
        self._files.append((fd, limit, data, stamp))
        return data

    def _storage_entries(self):
        # Stop immediately at an unexpected name; no unbounded directory list.
        names = set()
        with os.scandir(self._storage) as entries:
            for index, entry in enumerate(entries):
                require(index < 2 and entry.name in {"record.lock", "record.json"},
                        "incompleteStorage")
                names.add(entry.name)
        require(names == {"record.lock", "record.json"}, "incompleteStorage")

    def _load(self, marker_directory, run_directory, held_lock=None):
        marker_root = self._trusted_directory(marker_directory)
        self._held_lock = held_lock
        if held_lock is None:
            self._marker = self._file(marker_root, "lock", 139, lock=True)
        else:
            require(type(held_lock) is MarkerLock, "untrustedMarkerLock")
            held_lock.recheck()
            require(os.fspath(marker_directory) == held_lock.directory,
                    "markerLockPathMismatch")
            # Borrow the owner's actual locked description. Never add it to
            # _fds: closing a snapshot must not close or unlock the owner.
            fd = held_lock._fd
            self._edges.append((marker_root, "lock", fd))
            self._marker, stamp = self._read(fd, 139)
            self._files.append((fd, 139, self._marker, stamp))
        runtime = self._trusted_directory(run_directory)
        self._storage = self._open("recovery", os.O_RDONLY | os.O_DIRECTORY, runtime)
        self._private_directory(self._storage)
        self._directories.append((self._storage, fingerprint(os.fstat(self._storage))))
        require(self._file(self._storage, "record.lock", 0, lock=True) == b"")
        self._storage_entries()
        self._record = self._file(self._storage, "record.json", model.MAX_BYTES)
        try:
            record = model.parse(self._record)
        except (ValueError, TypeError, OverflowError, RecursionError):
            raise SnapshotError("invalidSnapshotRecord") from None
        require(self._marker == b"unresolved:" + record["identity"]["run"].encode("ascii"),
                "markerRunMismatch")
        self.recheck()

    @property
    def marker(self):
        return self._marker

    @property
    def record(self):
        return self._record

    def recheck(self):
        require(self._active, "snapshotClosed")
        try:
            if self._held_lock is not None:
                self._held_lock.recheck()
            for parent, name, fd in self._edges:
                named = os.stat(name, dir_fd=parent, follow_symlinks=False)
                require(identity(named) == identity(os.fstat(fd)), "snapshotChanged")
            for fd, stamp in self._directories:
                self._private_directory(fd)
                require(fingerprint(os.fstat(fd)) == stamp, "snapshotChanged")
            self._storage_entries()
            for fd, limit, expected, stamp in self._files:
                data, current = self._read(fd, limit)
                require(data == expected and current == stamp, "snapshotChanged")
        except OSError:
            raise SnapshotError("snapshotUnavailable") from None

    def _close(self):
        self._active = False
        for fd in reversed(self._fds):
            os.close(fd)
        self._fds.clear()


class MarkerLock:
    """Exclusive marker ownership acquired here, never asserted by a raw fd.

    The owner must outlive every borrowed snapshot. Its descriptor is private:
    callers use read_marker/write_marker and must not close, duplicate or unlock
    it. This is a trusted in-process capability, not a Python security boundary.
    Marker writes may change bytes while the owner lives; a snapshot separately
    pins those bytes for its entire reconciliation transaction.
    """

    def __init__(self):
        raise TypeError("use MarkerLock.acquire")

    @classmethod
    def acquire(cls, marker_directory, *, create=False):
        require(cls is MarkerLock, "untrustedMarkerLock")
        owner = object.__new__(cls)
        owner._active = False
        owner._tree = _Snapshot()
        owner.directory = os.fspath(marker_directory)
        try:
            parent = owner._tree._trusted_directory(marker_directory)
            flags = os.O_RDWR | (os.O_CREAT if create else 0)
            # _open intentionally has no creation mode; new markers must be 600.
            fd = os.open("lock", flags | os.O_NOFOLLOW | os.O_NONBLOCK,
                         0o600, dir_fd=parent)
            owner._tree._fds.append(fd)
            owner._tree._edges.append((parent, "lock", fd))
            owner._fd = fd
            owner._identity = identity(os.fstat(fd))
            owner._tree._regular(fd)
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise SnapshotError("snapshotBusy") from None
            owner._active = True
            owner.recheck()
            return owner
        except BaseException:
            owner.close()
            raise

    def recheck(self):
        require(self._active, "markerLockClosed")
        try:
            require(identity(self._tree._regular(self._fd)) == self._identity,
                    "markerLockChanged")
            for parent, name, fd in self._tree._edges:
                require(identity(os.stat(name, dir_fd=parent, follow_symlinks=False))
                        == identity(os.fstat(fd)), "markerLockChanged")
            for fd, _ in self._tree._directories:
                self._tree._private_directory(fd)
        except OSError:
            raise SnapshotError("markerLockUnavailable") from None

    def read_marker(self, limit):
        self.recheck()
        return os.pread(self._fd, limit, 0)

    def write_marker(self, data):
        self.recheck()
        require(type(data) is bytes, "invalidMarkerBytes")
        if os.pwrite(self._fd, data, 0) != len(data):
            raise OSError("partial marker write")
        os.ftruncate(self._fd, len(data))
        os.fsync(self._fd)
        self.recheck()

    def close(self):
        self._active = False
        # Do not close an unrelated descriptor after accidental external close
        # and reuse. Normal callers cannot access the private descriptor.
        fd = getattr(self, "_fd", None)
        if fd in self._tree._fds:
            try:
                retained = identity(os.fstat(fd)) == self._identity
            except (OSError, AttributeError):
                retained = False
            if not retained:
                self._tree._fds.remove(fd)
        self._tree._close()


@contextmanager
def locked_snapshot(marker_directory, run_directory, *, held_lock=None):
    """Lock marker then storage, yield immutable bytes, and recheck before release.

    Both arguments must be canonical absolute private directories selected by a
    trusted caller, never a trace/report. The marker directory contains ``lock``;
    the separate per-run directory contains ``recovery/record.lock`` and record.
    Missing, legacy, partial, contended or changed state raises SnapshotError.
    With held_lock, borrow a live MarkerLock acquired before evidence collection;
    no marker flock, unlock, duplicate or close occurs in this context.
    """
    snapshot = _Snapshot()
    try:
        try:
            snapshot._load(marker_directory, run_directory, held_lock)
            yield snapshot
            snapshot.recheck()
        except OSError:
            raise SnapshotError("snapshotUnavailable") from None
    finally:
        snapshot._close()
