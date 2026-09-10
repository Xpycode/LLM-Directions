"""One read-only observation after the inventory-contract review; never retry.

Reuse the reviewed caller with a fresh exclusive journal. The original consumed
journal and all failed acquisition transactions remain untouched.
"""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    'identity_observation', ROOT / 'identity-read-observation.py')
caller = importlib.util.module_from_spec(spec)
spec.loader.exec_module(caller)
caller.REPORT = ROOT / 'inventory-contract-observation-2026-09-10.jsonl'

if __name__ == '__main__':
    raise SystemExit(caller.main())
