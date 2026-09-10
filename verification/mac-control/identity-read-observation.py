"""One read-only identity diagnostic for the Wave 1 continuation; never retry.

No acquisition, marker mutation, discovered-process signalling, activation or desktop input.
Timeout cleanup may terminate only the owned observation helper.
The exclusive append-only report is consumed even if this invocation fails.
"""
import json
import os
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / 'tools/mac-control/Spikes'))
from recovery_probe import capture_bounded_context, ProbeFailure
from recovery_snapshot import MarkerLock
from recovery_bootstrap import _stamps
from supervisor import mac_clock
from runtime_root import trusted_runtime_root

MARKER = Path('/private/var/folders/ly/b2sk443n0hq1_z9mgf4q8f4w0000gn/T/directions-stop-spike')
REPORT = REPO / 'verification/mac-control/identity-read-observation-2026-09-10.jsonl'


def main(*, inventory_library=None, report_path=None):
    report_path = REPORT if report_path is None else report_path
    report = dict(schema=('identityReadObservation/v1' if inventory_library is None
                          else 'kernelInventoryObservation/v1'), launch_eligible=False,
                  native_recovery_verified=False, observation_count=0,
                  marker_unchanged=False, result='prepared')
    if inventory_library is not None:
        report['inventory_library_sha256'] = inventory_library[1]
    owner = None
    code = 1
    try:
        trusted_runtime_root(MARKER)
        with report_path.open('x') as output:
            def append():
                output.write(json.dumps(report, sort_keys=True, allow_nan=False) + '\n')
                output.flush()
                os.fsync(output.fileno())
            append()
            try:
                owner = MarkerLock.acquire(MARKER, create=False)
                before = owner.read_marker(139)
                stamps = _stamps(owner)
                if before != b'unresolved':
                    raise ValueError('unexpected marker state')
                clock = mac_clock()
                report.update(result='started', observation_count=1, started_ns=clock())
                append()
                try:
                    options = {} if inventory_library is None else dict(inventory_library=inventory_library)
                    report['sample'] = capture_bounded_context(clock=clock, **options)
                    report['result'] = 'observed'
                    code = 0
                except ProbeFailure as error:
                    report.update(result='unresolved', failure_stage=error.stage)
                finally:
                    report['ended_ns'] = clock()
                    owner.recheck()
                    report['marker_unchanged'] = (owner.read_marker(139) == before
                                                 and _stamps(owner) == stamps)
                    if not report['marker_unchanged']:
                        raise ValueError('marker changed')
            except (OSError, ValueError, TypeError, RuntimeError) as error:
                report.update(result='unresolved', reason=type(error).__name__)
                code = 1
            finally:
                if owner is not None:
                    try:
                        owner.close()
                    except (OSError, ValueError, TypeError, RuntimeError) as error:
                        report.update(result='unresolved', teardown_failure=type(error).__name__)
                        code = 1
                append()
    except (OSError, ValueError, TypeError, RuntimeError) as error:
        print(json.dumps(dict(result='unresolved', reason=type(error).__name__)))
        return 1
    print(json.dumps(report, sort_keys=True))
    return code


if __name__ == '__main__':
    raise SystemExit(main())
