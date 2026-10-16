#!/usr/bin/env python3
"""Verify frozen source bytes; comparisons are static, never token/latency estimates."""
import argparse
import hashlib
import json
import re
import subprocess
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

def routing(full=False):
    """Account for explicit oracle paths; this does not simulate an LLM's routing."""
    fixture = Path(__file__).parent / 'routing'
    cases = json.loads((fixture.parent / 'routing-cases.json').read_text())['cases']
    manifest = json.loads((BASE / 'manifest.json').read_text())['files']
    def rendered(path):
        return path.read_text().replace('[LOCAL_DIRECTIONS_PATH]', str(ROOT)).encode()
    def paths(text):
        return set(re.findall(r'`([0-9][0-9]_[a-z0-9-]+\.md)`', text))
    current = subprocess.check_output(['bash', str(ROOT / 'scripts/gen-directions-index.sh')], text=True)
    eligible = paths(current)
    domain = {c['expected'][0] for c in cases if c['kind'] == 'domain'}
    assert len(eligible) == 47 and domain == eligible, 'canonical domain coverage changed'
    assert paths((fixture / 'inline.md').read_text()) == eligible
    assert paths((fixture / 'DIRECTIONS-INDEX.md').read_text()) == eligible
    results = []
    index_bytes = len(rendered(fixture / 'DIRECTIONS-INDEX.md'))
    for host in ('codex', 'claude'):
        repo_bytes = len(rendered(fixture / ('repository.md' if host == 'codex' else 'repository-claude.md')))
        # No repository CLAUDE.md existed in LE01; baseline Claude repo contribution is zero.
        baseline_repo = manifest['AGENTS.md']['bytes'] if host == 'codex' else 0
        baseline_global = len(rendered(BASE / 'source' / f'{host.upper()}-GLOBAL-TEMPLATE.md'))
        baseline_initial = baseline_global + baseline_repo
        for candidate in ('inline', 'router'):
            global_bytes = len(rendered(fixture / f'{candidate}-{host}.md'))
            initial = global_bytes + repo_bytes
            assert initial < baseline_initial, (host, candidate, 'initial bytes regression')
            for case in cases:
                expected = case['expected']
                for name in expected:
                    assert name in manifest and (ROOT / name).is_file(), name
                # Hold guide/command contents constant at LE01, isolating routing cost.
                retrieved = sum(manifest[name]['bytes'] for name in expected)
                command = all(name.startswith('commands/') for name in expected)
                index_reads = int(candidate == 'router' and bool(expected) and not command)
                for globals_present in (True, False):
                    fallback_reads = int(not globals_present and bool(expected) and not command)
                    entry = initial if globals_present else repo_bytes
                    extra_bytes = index_reads * index_bytes + fallback_reads * global_bytes
                    baseline_total = baseline_initial + retrieved if globals_present else None
                    results.append(dict(host=host, candidate=candidate, case=case['id'],
                        globals_present=globals_present, initial_bytes=entry,
                        retrieval_paths=expected, retrieval_bytes=retrieved + extra_bytes,
                        retrieval_calls=len(expected) + index_reads + fallback_reads,
                        extra_index_reads=index_reads, fallback_template_reads=fallback_reads,
                        total_bytes=entry + retrieved + extra_bytes,
                        baseline_initial_bytes=baseline_initial if globals_present else baseline_repo,
                        baseline_total_bytes=baseline_total,
                        delta_bytes=entry + retrieved + extra_bytes - baseline_total if globals_present else None,
                        disposition=case['disposition']))
    report = dict(evidence='static oracle accounting; E1 host runs unavailable',
        canonical_domains=len(eligible), cases=len(cases),
        source_hashes={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                       for p in sorted(fixture.glob('*.md'))}, rows=results)
    if full:
        print(json.dumps(report, indent=2))
    else:
        print(f"PASS: {len(eligible)} canonical domains, {len(cases)} cases, {len(results)} static accounting rows; E1 pending")
        for host in ('codex', 'claude'):
            for candidate in ('inline', 'router'):
                rows = [r for r in results if r['host'] == host and r['candidate'] == candidate and r['globals_present']]
                deltas = [r['delta_bytes'] for r in rows]
                print(f"{host}/{candidate}: global+repo {rows[0]['baseline_initial_bytes']} -> {rows[0]['initial_bytes']} bytes; total deltas {min(deltas)}..{max(deltas)} bytes")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--check-baseline', action='store_true')
    parser.add_argument('--compare', action='store_true')
    parser.add_argument('--routing', action='store_true')
    parser.add_argument('--routing-json', action='store_true')
    args = parser.parse_args()
    if args.check_baseline:
        check_baseline()
    if args.compare:
        compare()
    if args.routing or args.routing_json:
        routing(full=args.routing_json)
    if not (args.check_baseline or args.compare or args.routing or args.routing_json):
        parser.error('choose --check-baseline, --compare or --routing')
