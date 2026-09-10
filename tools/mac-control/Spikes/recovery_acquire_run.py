"""Capture/reload wrapper reporting; explicit commands, no native configuration.

The prepared report is exclusively created by the location-checking wrapper.
Append-only JSON lines preserve earlier records on an interrupted later write.
A partial final line means unresolved; nothing here repairs or retries a journal.
Only capture success permits reload. Reports never grant recovery authority.
"""
import json
import os
import re
import subprocess

from recovery_probe import _parse
from recovery_snapshot import _Snapshot, require
from recovery_storage import flush_file

MAX_RETAINED_OUTPUT = 16384


class AcquisitionRunFailure(ValueError):
    pass


def _output(value):
    raw = value if isinstance(value, bytes) else (value or '').encode('utf-8')
    return raw[:MAX_RETAINED_OUTPUT].decode('utf-8', errors='replace'), len(raw) > MAX_RETAINED_OUTPUT


def _append(fd, record):
    raw = (json.dumps(record, sort_keys=True, allow_nan=False) + '\n').encode('utf-8')
    while raw:
        count = os.write(fd, raw)
        require(count > 0, 'partialReportWrite')
        raw = raw[count:]
    flush_file(fd)


def run_operations(operations, *, report_path, configuration, cwd, timeout=45):
    """Append outcomes to a fresh prepared report; stop on any failure.

    subprocess.run kills/waits for its owned child on timeout. Preserve the
    exception's available stdout/stderr (up to 16 KiB each), never retry or reload
    after failure. This limits retained output, not subprocess.run's buffering.
    The trusted wrapper supplies the report path and exact capture/reload argv.
    """
    require([name for name, _ in operations] == ['capture', 'reload'], 'invalidOperations')
    fd = os.open(report_path, os.O_RDWR | os.O_APPEND | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        info = _Snapshot._regular(fd)
        require(0 < info.st_size <= 65536, 'invalidPreparedReport')
        prepared = _parse(os.pread(fd, 65537, 0))
        require(prepared == dict(configuration=configuration, stage='prepared'), 'reportAlreadyAttempted')
        # Any following record permanently consumes this report, including a
        # started record whose child outcome was lost to wrapper termination.
        parsed = {}
        for operation, command in operations:
            _append(fd, dict(operation=operation, stage='started', command=command))
            try:
                completed = subprocess.run(command, capture_output=True, timeout=timeout, cwd=cwd)
                code, out, err = completed.returncode, completed.stdout, completed.stderr
                failure = None if code == 0 else 'childExit'
            except subprocess.TimeoutExpired as error:
                code, out, err, failure = None, error.stdout, error.stderr, 'timeout'
            except OSError:
                code, out, err, failure = None, None, None, 'launch'
            stdout, stdout_truncated = _output(out)
            stderr, stderr_truncated = _output(err)
            if failure is None and (stdout_truncated or stderr_truncated):
                failure = 'outputLimit'
            _append(fd, dict(operation=operation, stage='finished', exit_code=code,
                stdout=stdout, stderr=stderr, stdout_truncated=stdout_truncated,
                stderr_truncated=stderr_truncated, failure=failure))
            if failure is not None:
                raise AcquisitionRunFailure(failure)
            try:
                result = _parse(stdout.encode('utf-8'))
                require(type(result) is dict and result.get('schema') == 'prospectiveAcquisitionReport/v1'
                    and result.get('operation') == operation
                    and result.get('launch_eligible') is False
                    and result.get('native_recovery_verified') is False
                    and result.get('result') == {'capture': 'prospectiveBaselineRetained',
                                                'reload': 'acquiredEvidenceReloaded'}[operation], 'invalidChildReport')
                require(type(result.get('baseline_sha256')) is str and
                        re.fullmatch('[0-9a-f]{64}', result['baseline_sha256']) is not None
                        and type(result.get('acquisition')) is dict, 'invalidChildReport')
                if operation == 'capture':
                    require(result.get('marker_unchanged') is True, 'invalidChildReport')
                else:
                    require(result.get('marker_unchanged') is None and
                            result['baseline_sha256'] == parsed['capture']['baseline_sha256'] and
                            result['acquisition'] == parsed['capture']['acquisition'], 'reloadMismatch')
            except (ValueError, TypeError, KeyError, RecursionError):
                _append(fd, dict(operation=operation, stage='rejected', failure='invalidChildReport'))
                raise AcquisitionRunFailure('invalidChildReport') from None
            parsed[operation] = result
        _append(fd, dict(stage='verified', launch_eligible=False, native_recovery_verified=False))
        return parsed
    finally:
        os.close(fd)
