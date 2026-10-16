#!/usr/bin/env python3
"""Verify frozen source bytes; comparisons are static, never token/latency estimates."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = Path(__file__).parent / 'baseline'

def check_baseline():
    records = json.loads((BASE / 'manifest.json').read_text())['files']
    for name, expected in records.items():
        data = (BASE / 'source' / name).read_bytes()
        assert len(data) == expected['bytes'], name
        assert hashlib.sha256(data).hexdigest() == expected['sha256'], name
    print(f'PASS: {len(records)} frozen files; hashes and bytes match')

def compare():
    records = json.loads((BASE / 'manifest.json').read_text())['files']
    for name in ['CODEX-GLOBAL-TEMPLATE.md', 'CLAUDE-GLOBAL-TEMPLATE.md', 'AGENTS.md',
                 'commands/log.md', 'commands/execute.md', '52_context-management.md']:
        print(f"{name}: {records[name]['bytes']} -> {len((ROOT / name).read_bytes())} bytes")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--check-baseline', action='store_true')
    parser.add_argument('--compare', action='store_true')
    args = parser.parse_args()
    if args.check_baseline:
        check_baseline()
    if args.compare:
        compare()
    if not (args.check_baseline or args.compare):
        parser.error('choose --check-baseline or --compare')
