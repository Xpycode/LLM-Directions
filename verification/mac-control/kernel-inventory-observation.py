"""Prepared one-shot read-only observation; execution requires agreed native scope.

Uses the existing locked/reporting caller and a separately built, explicitly
pinned library. No capture, initialization, activation, reboot or desktop input.
The report is exclusive/append-only and a failed attempt is never retried.
"""
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIBRARY = ('/private/tmp/directions-inventory.1aT0KH/recovery_inventory.dylib',
           'b0d46b7fb180e1e04d29b538f18d19211fd90f6342106d917c7dcfa51c6eedfc')
REPORT = HERE / 'kernel-inventory-observation-2026-09-10.jsonl'


def main():
    spec = importlib.util.spec_from_file_location('locked_observation', HERE / 'identity-read-observation.py')
    caller = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(caller)
    return caller.main(inventory_library=LIBRARY, report_path=REPORT)


if __name__ == '__main__':
    raise SystemExit(main())
