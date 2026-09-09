"""Read-only Darwin context probe for the isolated reconciliation adapter.

Call only under the cooperating broker/storage locks, outside active input/Stop
handling, with an external deadline. OS reads can block. No marker access, process
signalling, launch, repair, or admission authority is provided here.

Completeness is scoped to conforming, fixed-name workers: MacControlExecutor
(Protocol.md) and the standalone StopSpikeWorker, across all paths and sessions
of the effective UID. Renamed/exec-replaced workers and hostile same-UID code are
outside that contract. Two scans detect observed races, not arbitrary activity
between samples; cooperating launchers must honor the caller's lock throughout.
"""
import ctypes as C
import os
import time

from recovery_identity import _Kernel as IdentityKernel, _session
from recovery_record import require

MAX_PIDS = 65536
EXECUTOR_NAMES = frozenset(('MacControlExecutor', 'StopSpikeWorker'))
FAILURE_STAGES = frozenset(('caller', 'kernel', 'boot', 'session', 'inventoryInitial',
    'processIdentity', 'processPath', 'processRecheck', 'inventoryAfterFirstScan',
    'scanComparison', 'inventoryAfterSecondScan', 'contextRecheck', 'timestamp',
    'inventoryInitialQuery', 'inventoryInitialMalformed',
    'inventoryAfterFirstScanQuery', 'inventoryAfterFirstScanMalformed',
    'inventoryAfterFirstScanChanged', 'inventoryAfterSecondScanQuery',
    'inventoryAfterSecondScanMalformed', 'inventoryAfterSecondScanChanged'))


class ContextFailure(ValueError):
    def __init__(self, stage):
        self.stage = stage if type(stage) is str and stage in FAILURE_STAGES else 'kernel'
        super().__init__('Darwin context unresolved: ' + self.stage)


class _InventoryFailure(ValueError):
    def __init__(self, kind):
        self.kind = kind if kind in ('Query', 'Malformed') else 'Malformed'
        super().__init__('Darwin inventory unresolved: ' + self.kind)


class _Kernel(IdentityKernel):
    def __init__(self):
        super().__init__()
        # Installed Darwin libproc.h / sys/proc_info.h: PROC_UID_ONLY=4;
        # return value and capacity are BYTES, not numbers of PIDs.
        self.lib.proc_listpids.argtypes = [C.c_uint32, C.c_uint32, C.c_void_p, C.c_int]
        self.lib.proc_listpids.restype = C.c_int

    def pids(self, uid):
        require(type(uid) is int and 0 < uid < 0xffffffff)
        buffer = (C.c_int * MAX_PIDS)()
        capacity = C.sizeof(buffer)
        try:
            count = self.lib.proc_listpids(4, uid, buffer, capacity)
        except (OSError, ValueError, TypeError, AttributeError, OverflowError,
                C.ArgumentError):
            raise _InventoryFailure('Query') from None
        try:
            # A full buffer might have silently omitted processes. No retry or
            # guessed sizing; any ambiguity makes this observation unusable.
            require(0 < count < capacity and count % C.sizeof(C.c_int) == 0)
            return _pids(tuple(buffer[:count // C.sizeof(C.c_int)]))
        except (ValueError, TypeError, OverflowError):
            raise _InventoryFailure('Malformed') from None


def _pids(values):
    require(type(values) is tuple and 0 < len(values) < MAX_PIDS)
    require(all(type(pid) is int and 0 < pid <= 0x7fffffff for pid in values))
    require(len(set(values)) == len(values))
    return tuple(sorted(values))


def capture_context(clock=time.monotonic_ns):
    """Return verifier context, or raise ValueError if the scan is unresolved.

No report/configurable name filter can exclude a known worker. Every UID process
must have a readable stable path and kernel incarnation, including non-candidates.
Any candidate blocks the verifier regardless of code identity; a name/PID never
grants authority. Candidate rows are diagnostic only and intentionally omit paths.
The existing adapter accepts this callable explicitly; it is not installed as a
runtime default. Caller security-session identity is not a login-freshness proof.
"""
    stage = 'caller'
    try:
        uid, caller = os.geteuid(), os.getpid()
        require(0 < uid < 0xffffffff and os.getuid() == uid)
        stage = 'kernel'
        kernel = _Kernel()
        stage = 'boot'
        boot = kernel.boot()
        stage = 'session'
        session = _session(kernel)
        def inventory(boundary):
            nonlocal stage
            stage = boundary + 'Query'
            try:
                values = kernel.pids(uid)
            except _InventoryFailure as error:
                stage = boundary + error.kind
                raise
            stage = boundary + 'Malformed'
            return _pids(values)

        pids = inventory('inventoryInitial')
        stage = 'inventoryInitialMalformed'
        require(caller in pids)

        def scan():
            nonlocal stage
            rows = {}
            for pid in pids:
                stage = 'processIdentity'
                row = kernel.process(pid)
                require(type(row) is tuple and len(row) == 7
                        and all(type(value) is int for value in row))
                require(row[0] == pid and row[2] == uid and row[1] >= 0
                        and 0 <= row[3] < 0xffffffff and 0 <= row[4] < 0xffffffff
                        and row[5] > 0 and 0 <= row[6] < 1000000)
                stage = 'processPath'
                path = kernel.path(pid)
                require(type(path) is str and os.path.isabs(path)
                        and '\x00' not in path and os.path.normpath(path) == path)
                stage = 'processRecheck'
                require(kernel.process(pid) == row)
                rows[pid] = row, path
            return rows

        first = scan()
        after_first = inventory('inventoryAfterFirstScan')
        stage = 'inventoryAfterFirstScanChanged'
        require(after_first == pids)
        second = scan()
        stage = 'scanComparison'
        require(second == first)
        after_second = inventory('inventoryAfterSecondScan')
        stage = 'inventoryAfterSecondScanChanged'
        require(after_second == pids)
        stage = 'contextRecheck'
        require(kernel.boot() == boot and _session(kernel) == session
                and os.getuid() == os.geteuid() == uid and os.getpid() == caller)
        candidates = [dict(pid=pid, start=f'{row[5]}-{row[6]}')
                      for pid, (row, path) in first.items()
                      if os.path.basename(path) in EXECUTOR_NAMES]
        stage = 'timestamp'
        return dict(boot=boot, session=str(session[0]), checked_ns=clock(),
                    inventory_complete=True, executors=candidates)
    except (OSError, ValueError, TypeError, KeyError, AttributeError, OverflowError):
        raise ContextFailure(stage) from None


def probe_main(clock):
    """Bounded helper wire output: fixed error stages, never native error text."""
    import json
    try:
        result = capture_context(clock=clock)
    except ContextFailure as error:
        print(json.dumps(dict(schema='contextFailure/v1', stage=error.stage)), flush=True)
        return 1
    print(json.dumps(result, separators=(',', ':')), flush=True)
    return 0
