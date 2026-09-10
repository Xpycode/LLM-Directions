"""Read-only Darwin identities for already owned children and verified artifacts.

No report-derived authority, PID signalling, runtime marker access, or spawning.
Call in a setup thread with an external deadline: OS calls can block. Hashing is
size-bounded. A digest identifies stable disk bytes, not mapped code or signing.
The login identity is the caller's security session (inherited at fork/exec);
this does not attest children that deliberately change security sessions.
"""
import ctypes as C
import errno
import hashlib
import os
import stat
import sys
import uuid

from recovery_record import check_identity, require, token

MAX_ARTIFACT_BYTES = 128 * 1024 * 1024
PROCESS_IDENTITY_FAILURE_KINDS = frozenset((
    'Query', 'Missing', 'Denied', 'NativeError', 'Zero', 'Negative', 'Short',
    'Oversize'))


class ProcessIdentityFailure(ValueError):
    """Fixed diagnostic for a rejected proc_pidinfo observation."""
    def __init__(self, kind):
        self.kind = (kind if type(kind) is str and
                     kind in PROCESS_IDENTITY_FAILURE_KINDS else 'Query')
        super().__init__('Darwin process identity unresolved: ' + self.kind)


# Darwin SDK sys/proc_info.h and sys/param.h: MAXCOMLEN=16,
# PROC_PIDTBSDINFO=3, PROC_PIDPATHINFO_MAXSIZE=4*MAXPATHLEN (PATH_MAX=1024).
class _BSDInfo(C.Structure):
    _fields_ = [(name, C.c_uint32) for name in (
        'flags', 'status', 'xstatus', 'pid', 'ppid', 'uid', 'gid',
        'ruid', 'rgid', 'svuid', 'svgid', 'reserved')]
    _fields_ += [('comm', C.c_char * 16), ('name', C.c_char * 32)]
    _fields_ += [(name, C.c_uint32) for name in ('nfiles', 'pgid', 'jobc', 'tdev', 'tpgid')]
    _fields_ += [('nice', C.c_int32), ('seconds', C.c_uint64), ('micros', C.c_uint64)]


class _Kernel:
    def __init__(self):
        require(sys.platform == 'darwin' and C.sizeof(_BSDInfo) == 136)
        self.lib = C.CDLL('/usr/lib/libSystem.B.dylib', use_errno=True)
        self.security = C.CDLL('/System/Library/Frameworks/Security.framework/Security')
        self.lib.proc_pidinfo.argtypes = [C.c_int, C.c_int, C.c_uint64, C.c_void_p, C.c_int]
        self.lib.proc_pidinfo.restype = C.c_int
        self.lib.proc_pidpath.argtypes = [C.c_int, C.c_void_p, C.c_uint32]
        self.lib.proc_pidpath.restype = C.c_int
        self.lib.sysctlbyname.argtypes = [C.c_char_p, C.c_void_p, C.POINTER(C.c_size_t), C.c_void_p, C.c_size_t]
        self.lib.sysctlbyname.restype = C.c_int
        # AuthSession.h: UInt32 input, UInt32* outputs, OSStatus (SInt32).
        self.security.SessionGetInfo.argtypes = [C.c_uint32, C.POINTER(C.c_uint32), C.POINTER(C.c_uint32)]
        self.security.SessionGetInfo.restype = C.c_int32

    def boot(self):
        buffer = C.create_string_buffer(128)
        size = C.c_size_t(len(buffer))
        if self.lib.sysctlbyname(b'kern.bootsessionuuid', buffer, C.byref(size), None, 0) != 0:
            raise OSError(C.get_errno(), 'boot identity unavailable')
        require(size.value == 37 and buffer.raw[36] == 0)
        result = buffer.raw[:36].decode('ascii')
        require(str(uuid.UUID(result)) == result.lower() and uuid.UUID(result).int != 0)
        return result.lower()

    def session(self):
        actual, attributes = C.c_uint32(), C.c_uint32()
        require(self.security.SessionGetInfo(0xffffffff, C.byref(actual), C.byref(attributes)) == 0)
        return actual.value, attributes.value

    def process(self, pid):
        info = _BSDInfo()
        size = C.sizeof(info)
        try:
            # Apple libproc converts an underlying __proc_info -1 to zero while
            # preserving errno. Clear it first so an unclassified zero cannot
            # inherit unrelated thread-local state. A full read ignores errno.
            C.set_errno(0)
            count = self.lib.proc_pidinfo(pid, 3, 0, C.byref(info), size)
            native_errno = C.get_errno()
        except (OSError, ValueError, TypeError, AttributeError, OverflowError,
                C.ArgumentError):
            raise ProcessIdentityFailure('Query') from None
        if type(count) is not int:
            raise ProcessIdentityFailure('Query')
        if count != size:
            if count < 0:
                kind = 'Negative'
            elif count == 0 and native_errno == errno.ESRCH:
                kind = 'Missing'
            elif count == 0 and native_errno in (errno.EPERM, errno.EACCES):
                kind = 'Denied'
            elif count == 0 and native_errno:
                kind = 'NativeError'
            elif count == 0:
                kind = 'Zero'
            elif count < size:
                kind = 'Short'
            else:
                kind = 'Oversize'
            raise ProcessIdentityFailure(kind)
        return (info.pid, info.ppid, info.uid, info.ruid, info.svuid, info.seconds, info.micros)

    def path(self, pid):
        buffer = C.create_string_buffer(4096)
        count = self.lib.proc_pidpath(pid, buffer, len(buffer))
        require(0 < count < len(buffer) and buffer.raw[count] == 0)
        require(len(buffer.value) == count)
        result = os.fsdecode(buffer.value)
        require(os.path.isabs(result) and os.path.realpath(result) == result)
        return result


def _stamp(info):
    return (info.st_dev, info.st_ino, info.st_mode, info.st_uid, info.st_gid,
            info.st_size, info.st_mtime_ns, info.st_ctime_ns, info.st_nlink)


def _digest(path):
    path = os.fspath(path)
    require(type(path) is str and os.path.isabs(path) and os.path.realpath(path) == path)
    before = os.stat(path, follow_symlinks=False)
    require(stat.S_ISREG(before.st_mode) and 0 < before.st_size <= MAX_ARTIFACT_BYTES)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
    try:
        require(_stamp(os.fstat(fd)) == _stamp(before))
        digest = hashlib.sha256()
        remaining = before.st_size
        while remaining:
            chunk = os.read(fd, min(1024 * 1024, remaining))
            require(bool(chunk))
            digest.update(chunk)
            remaining -= len(chunk)
        require(os.read(fd, 1) == b'')
        require(_stamp(os.fstat(fd)) == _stamp(before))
        require(_stamp(os.stat(path, follow_symlinks=False)) == _stamp(before))
        require(os.path.realpath(path) == path)
        return digest.hexdigest()
    finally:
        os.close(fd)


def _session(kernel):
    actual, attributes = kernel.session()
    # AuthSession.h: 0 invalid, -1 caller sentinel, -2 reserved;
    # root=0x1, graphics=0x10, remote=0x1000.
    require(0 < actual < 0xfffffffe and attributes & 0x10 and not attributes & 0x1001)
    return actual, attributes


def capture_identity(run_id, children, paths):
    """Return recovery_record identity; raise ValueError on unresolved evidence.

    children and paths are mappings with exactly worker and target. The former
    contains this supervisor's Popen objects, the latter canonical launch paths
    verified before spawning. Never call using a saved record's PID or path.
    """
    try:
        token(run_id)
        require(set(children) == set(paths) == {'worker', 'target'})
        require(os.getuid() == os.geteuid() and os.geteuid() != 0)
        uid, parent = os.geteuid(), os.getpid()
        kernel = _Kernel()
        boot, session = kernel.boot(), _session(kernel)
        result = dict(boot=boot, session=str(session[0]), run=run_id)
        snapshots = {}

        def snapshot(role):
            child = children[role]
            require(type(child.pid) is int and 0 < child.pid <= 0x7fffffff and child.poll() is None)
            row = kernel.process(child.pid)
            require(row[:5] == (child.pid, parent, uid, uid, uid))
            require(row[5] > 0 and 0 <= row[6] < 1000000)
            path = os.fspath(paths[role])
            require(type(path) is str and os.path.isabs(path) and os.path.realpath(path) == path)
            require(kernel.path(child.pid) == path)
            return row

        for role in ('worker', 'target'):
            snapshots[role] = snapshot(role)
            code = _digest(paths[role])
            require(snapshot(role) == snapshots[role])
            row = snapshots[role]
            result[role] = dict(pid=row[0], start=f'{row[5]}-{row[6]}', code=code)
        # Recheck the first child after hashing the second, and context drift.
        require(all(snapshot(role) == snapshots[role] for role in ('worker', 'target')))
        require(kernel.boot() == boot and _session(kernel) == session)
        check_identity(result)
        return result
    except (OSError, ValueError, TypeError, KeyError, AttributeError, OverflowError):
        raise ValueError('owned process identity unresolved') from None
