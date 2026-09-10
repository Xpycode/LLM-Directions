"""Opt-in, bounded kernel-name inventory adapter; never a recovery authority.

Use only under the shared, pinned launcher exclusion and marker/storage locks,
held through consumption. Absence is conditional on conforming fixed native
worker names and UIDs across sessions (see kernel-inventory-review.md). It says
nothing about earlier workers or queued events. Candidates always reject.

The caller explicitly supplies trusted compiled library bytes and the supervisor
continuous clock. No compilation, discovery, environment fallback or process-path
scan occurs here. OS reads/loading can block: use recovery_probe's external
deadline and bounded cleanup. Artifact stability assumes cooperating local code;
hashing disk bytes does not authenticate mapped code against hostile replacement.
"""
import ctypes as C
import hashlib
import json
import os
import re
import stat
import uuid

from recovery_context import ContextFailure
from recovery_identity import _Kernel, _stamp
from recovery_record import require
from recovery_verifier import context_snapshot

MAX_LIBRARY_BYTES = 16 * 1024 * 1024
_STATUS_STAGES = {
    1: 'kernelInventoryCandidate',
    -1: 'kernelInventoryArgument',
    -2: 'kernelInventoryAlloc',
    -3: 'kernelInventoryQueryError',
    -4: 'kernelInventoryMalformed',
    -5: 'kernelInventoryCallerMissing',
}


def _load_library(path, expected_sha256):
    path = os.fspath(path)
    require(type(path) is str and os.path.isabs(path)
            and '\x00' not in path and os.path.realpath(path) == path)
    require(type(expected_sha256) is str
            and re.fullmatch('[0-9a-f]{64}', expected_sha256) is not None)
    before = os.stat(path, follow_symlinks=False)
    require(stat.S_ISREG(before.st_mode) and 0 < before.st_size <= MAX_LIBRARY_BYTES)
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
        require(digest.hexdigest() == expected_sha256)

        def stable():
            require(_stamp(os.fstat(fd)) == _stamp(before)
                    and _stamp(os.stat(path, follow_symlinks=False)) == _stamp(before)
                    and os.path.realpath(path) == path)

        stable()
        library = C.CDLL(path)
        stable()
        library.mc_inventory.argtypes = [C.c_uint32, C.c_int]
        library.mc_inventory.restype = C.c_int
        return library
    finally:
        os.close(fd)


def _boot(kernel):
    value = kernel.boot()
    require(type(value) is str and str(uuid.UUID(value)) == value
            and uuid.UUID(value).int != 0)
    return value


def _session(kernel):
    value = kernel.session()
    require(type(value) is tuple and len(value) == 2
            and all(type(item) is int for item in value))
    actual, attributes = value
    require(0 < actual < 0xfffffffe and 0 <= attributes <= 0xffffffff
            and attributes & 0x10 and not attributes & 0x1001)
    return value


def capture_context(clock, library_path, library_sha256):
    """Return a validated empty context or fixed ContextFailure; one query only."""
    stage = 'caller'
    try:
        uid, caller, real_uid = os.geteuid(), os.getpid(), os.getuid()
        require(type(uid) is int and 0 < uid <= 0x7fffffff
                and type(caller) is int and 0 < caller <= 0x7fffffff
                and type(real_uid) is int and real_uid == uid)
        stage = 'kernelLibrary'
        library = _load_library(library_path, library_sha256)
        stage = 'kernel'
        kernel = _Kernel()
        stage = 'boot'
        boot = _boot(kernel)
        stage = 'session'
        session = _session(kernel)
        stage = 'kernelInventoryQuery'
        status = library.mc_inventory(uid, caller)
        stage = 'kernelInventoryStatus'
        require(type(status) is int)
        if status != 0:
            stage = _STATUS_STAGES.get(status, stage)
            raise ValueError('rejected inventory')
        stage = 'contextRecheck'
        require(_boot(kernel) == boot and _session(kernel) == session)
        current = (os.getuid(), os.geteuid(), os.getpid())
        require(all(type(value) is int for value in current)
                and current == (uid, uid, caller))
        stage = 'timestamp'
        result = dict(boot=boot, session=str(session[0]), checked_ns=clock(),
                      inventory_complete=True, executors=[])
        context_snapshot(result)
        return result
    except (OSError, ValueError, TypeError, KeyError, AttributeError, OverflowError,
            C.ArgumentError):
        raise ContextFailure(stage) from None


def probe_main(clock, library_path, library_sha256):
    """Emit one bounded JSON context or fixed contextFailure/v1 diagnostic."""
    try:
        result = capture_context(clock, library_path, library_sha256)
    except ContextFailure as error:
        print(json.dumps(dict(schema='contextFailure/v1', stage=error.stage)), flush=True)
        return 1
    print(json.dumps(result, separators=(',', ':')), flush=True)
    return 0
