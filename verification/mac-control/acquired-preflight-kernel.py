"""Prepared one-shot later-boot inspection; no initialization or launch.

`inspect` checks configured locations/artifact without loading native code.
`run` consumes a fresh journal and loads existing retained evidence (including
flush calls); marker access is read-only. A failure is never retried.
"""
import hashlib
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys

REPO = Path(__file__).resolve().parents[2]
# Reuse the exact reviewed acquisition configuration, never its consumed main().
CONFIG = runpy.run_path(str(REPO / 'verification/mac-control/prospective-acquisition-kernel.py'))
PIN = CONFIG['LIBRARY_SHA256']
LIBRARY = CONFIG['EVIDENCE_PARENT'] / ('inventory-' + PIN) / 'recovery_inventory.dylib'
REPORT = REPO / 'verification/mac-control/acquired-preflight-c6448ce2f81c44f78af0752199fdae2b.jsonl'


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv not in (['inspect'], ['run']):
        raise ValueError('choose inspect or run')
    if os.path.lexists(REPORT):
        raise ValueError('journal consumed; no retry')
    CONFIG['trusted_runtime_root'](CONFIG['MARKER'])
    for key in ('MARKER', 'SLOTS', 'ARCHIVE', 'ANCHOR'):
        CONFIG['checked'](CONFIG[key], private=True)
    CONFIG['checked'](LIBRARY.parent, private=True)
    if (LIBRARY.resolve(strict=True) != LIBRARY or not LIBRARY.is_file()
            or hashlib.sha256(LIBRARY.read_bytes()).hexdigest() != PIN):
        raise ValueError('inventory library changed')
    command = [sys.executable, '-B', str(REPO / 'tools/mac-control/Spikes/recovery_preflight.py'),
        'inspect-acquired', '--marker-directory', str(CONFIG['MARKER']),
        '--evidence-directory', str(CONFIG['SLOTS']), '--anchor-directory', str(CONFIG['ANCHOR']),
        '--archive-directory', str(CONFIG['ARCHIVE']),
        '--inventory-library', str(LIBRARY), '--inventory-sha256', PIN]
    if argv == ['inspect']:
        print(json.dumps(dict(command=command, report=str(REPORT), native_query_run=False), indent=2))
        return 0
    os.umask(0o077)
    with REPORT.open('x') as output:
        def append(record):
            output.write(json.dumps(record, sort_keys=True, allow_nan=False) + '\n')
            output.flush()
            os.fsync(output.fileno())
        append(dict(stage='started', command=command, launch_eligible=False,
                    native_recovery_verified=False))
        CONFIG['flush'](REPORT.parent)
        try:
            result = subprocess.run(command, capture_output=True, timeout=45, cwd=REPO)
            if len(result.stdout) > 16384 or len(result.stderr) > 16384:
                raise ValueError('outputLimit')
            append(dict(stage='finished', exit_code=result.returncode,
                        stdout=result.stdout.decode('utf-8', errors='replace'),
                        stderr=result.stderr.decode('utf-8', errors='replace')))
            parsed = json.loads(result.stdout)
            if (result.returncode != 0 or parsed.get('schema') != 'recoveryPreflight/v1'
                    or parsed.get('operation') != 'inspect-acquired'
                    or parsed.get('result') != 'acquiredPreflightObserved'
                    or parsed.get('marker_unchanged') is not True
                    or parsed.get('launch_eligible') is not False
                    or parsed.get('native_recovery_verified') is not False):
                raise ValueError('preflightUnresolved')
        except (OSError, ValueError, TypeError, AttributeError, subprocess.TimeoutExpired) as error:
            append(dict(stage='unresolved', reason=type(error).__name__,
                        launch_eligible=False, native_recovery_verified=False))
            return 1
        append(dict(stage='verified', launch_eligible=False, native_recovery_verified=False))
    print('Later-boot inspection passed; marker unchanged; no launch authority.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
