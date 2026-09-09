"""Bounded, read-only context capture after teardown under the caller's locks.

The owned helper receives no lock descriptors and grants no recovery authority.
Only that helper may be killed; no discovered process is ever signalled.
"""
import json
import math
import os
from pathlib import Path
import selectors
import subprocess
import sys
import time

from recovery_verifier import context_snapshot
from recovery_context import FAILURE_STAGES

MAX_OUTPUT = 16384
REAP_TIMEOUT = 0.5


class ProbeFailure(ValueError):
    def __init__(self, stage):
        allowed = FAILURE_STAGES | {'launch', 'readOutput', 'waitExit', 'helperExit',
                                    'deadline', 'outputLimit', 'decode', 'reap'}
        self.stage = stage if type(stage) is str and stage in allowed else 'helperExit'
        super().__init__('bounded context unresolved: ' + self.stage)


def _probe_command():
    # Isolated interpreter ignores PYTHONPATH and user site configuration. Import
    # the exact supervisor clock, so capture timestamps share its continuous-time
    # domain, including time spent asleep. Never use capture_context's default.
    source = (f'import sys; sys.path.insert(0, {str(Path(__file__).resolve().parent)!r}); '
              'from recovery_context import probe_main; '
              'from supervisor import mac_clock; '
              'raise SystemExit(probe_main(clock=mac_clock()))')
    return [sys.executable, '-B', '-I', '-c', source]


def _parse(data):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('duplicate context field')
            result[key] = value
        return result

    def nonfinite(_):
        raise ValueError('nonfinite context value')

    return json.loads(data.decode('utf-8'), object_pairs_hook=unique,
                      parse_constant=nonfinite)


def _decode(data):
    result = _parse(data)
    context_snapshot(result)
    return result


def capture_bounded_context(timeout=2.0, clock=time.monotonic_ns):
    """Return a strict empty-inventory snapshot or raise ValueError.

    Supply the supervisor's continuous nanosecond clock to count system sleep.
    The deadline starts before launch, but Popen creation itself cannot be
    interrupted; an overrun is rejected once it returns. Output and exit waits
    recheck the clock at most every 50 ms while scheduled. Cleanup has a separate
    half-second reap allowance. Native kernel reads occur only in the helper;
    inherited marker/storage locks remain exclusively owned by the caller.
    """
    if (type(timeout) not in (int, float) or not 0 < timeout <= 30
            or not math.isfinite(timeout)):
        raise ValueError('invalid context deadline')
    child = None
    selector = selectors.DefaultSelector()
    stage = 'launch'
    try:
        deadline = clock() + int(timeout * 1_000_000_000)

        def remaining_seconds():
            remaining = (deadline - clock()) / 1_000_000_000
            if remaining <= 0:
                raise ProbeFailure('deadline')
            return remaining

        child = subprocess.Popen(_probe_command(), stdin=subprocess.DEVNULL,
                                 stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                 close_fds=True, bufsize=0)
        os.set_blocking(child.stdout.fileno(), False)
        selector.register(child.stdout, selectors.EVENT_READ)
        output = bytearray()
        eof = False
        stage = 'readOutput'
        while not eof:
            for key, _ in selector.select(min(remaining_seconds(), 0.05)):
                try:
                    chunk = os.read(key.fd, min(4096, MAX_OUTPUT + 1 - len(output)))
                except BlockingIOError:
                    continue
                if not chunk:
                    eof = True
                    break
                output.extend(chunk)
                if len(output) > MAX_OUTPUT:
                    raise ProbeFailure('outputLimit')
        stage = 'waitExit'
        while child.poll() is None:
            try:
                child.wait(timeout=min(remaining_seconds(), 0.05))
            except subprocess.TimeoutExpired:
                continue
        remaining_seconds()
        if child.returncode != 0:
            failure = 'helperExit'
            try:
                diagnostic = _parse(bytes(output))
                if (type(diagnostic) is dict and set(diagnostic) == {'schema', 'stage'}
                        and diagnostic['schema'] == 'contextFailure/v1'
                        and type(diagnostic['stage']) is str
                        and diagnostic['stage'] in FAILURE_STAGES):
                    failure = diagnostic['stage']
            except (ValueError, TypeError, RecursionError):
                pass
            raise ProbeFailure(failure)
        stage = 'decode'
        return _decode(bytes(output))
    except ProbeFailure:
        raise
    except (OSError, ValueError, TypeError, KeyError, OverflowError,
            RecursionError, subprocess.TimeoutExpired):
        raise ProbeFailure(stage) from None
    finally:
        selector.close()
        if child is not None:
            if child.stdout is not None:
                child.stdout.close()
            if child.poll() is None:
                try:
                    child.kill()
                    child.wait(timeout=REAP_TIMEOUT)
                except (OSError, subprocess.TimeoutExpired):
                    raise ProbeFailure('reap') from None
