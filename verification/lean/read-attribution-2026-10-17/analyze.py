#!/usr/bin/env python3
"""Read retained E1 evidence and emit deterministic accounting; never run a host.

Usage: python3 -B verification/lean/read-attribution-2026-10-17/analyze.py
Output is JSON on stdout. Inputs, including the ignored raw archive, are read-only.
Repeat annotations describe evidence, not whether a read was necessary.
"""
import hashlib
import json
import statistics
import zipfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
REPLAY = ROOT / 'verification/lean/host-replay-2026-10-16'


def receipt(data):
    return {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def analyze():
    if not __debug__:
        raise RuntimeError('Python optimization disables evidence assertions; run without -O/PYTHONOPTIMIZE.')
    inputs = {}

    def load(name):
        data = (REPLAY / name).read_bytes()
        inputs[str((REPLAY / name).relative_to(ROOT))] = receipt(data)
        return json.loads(data)

    runs = load('runs.json')
    metrics = load('representative-metrics.json')
    manifest = load('evidence-manifest.json')
    archive_info = load('archive-info.json')
    archive = Path(archive_info['archive_path'])
    archive_receipt = receipt(archive.read_bytes())
    assert archive_receipt == {k: archive_info[k] for k in ('bytes', 'sha256')}
    selected = [r for r in runs if r['host'] == 'codex' and r.get('layout') == 'root'
                and r.get('scenario') in ('S01', 'S04', 'S05')
                and r.get('validity') == 'active']
    assert len(selected) == 18
    output, artifacts, status_sections = [], {}, {}
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None

        def read_member(name):
            data = z.read(name)
            actual = receipt(data)
            assert actual == manifest[name], name
            artifacts[name] = actual
            return data

        for source in ('baseline', 'final'):
            name = f'rendered/{source}/commands/status.md'
            data = z.read(name)
            lines = data.decode('utf-8').splitlines(keepends=True)
            boundaries = [0] + [i for i, line in enumerate(lines) if line.startswith('## ')]
            boundaries.append(len(lines))
            sections = {lines[a].strip(): len(''.join(lines[a:b]).encode('utf-8'))
                        for a, b in zip(boundaries, boundaries[1:])}
            assert sum(sections.values()) == len(data)
            status_sections[source] = dict(archive_member=name, **receipt(data), sections=sections)

        for run in sorted(selected, key=lambda r: r['run']):
            prefix = 'runs/' + run['run']
            audit = [json.loads(line) for line in
                     read_member(prefix + '/evidence/audit.jsonl').splitlines()]
            for name in ('fixture.json', 'initial.json', 'evidence/prompt.txt',
                         'evidence/answer.txt'):
                read_member(prefix + '/' + name)
            assert len(audit) == run['tool_calls'], run['run']
            assert sum(e['returned_bytes'] for e in audit) == run['all_returned_bytes']
            assert sum(f['bytes'] for f in run['initial_files']) == run['initial_configured_bytes']
            reads, buckets, seen, writes = [], Counter(), {}, Counter()
            for ordinal, event in enumerate(audit, 1):
                response = event['response'].encode('utf-8')
                assert len(response) == event['returned_bytes']
                assert hashlib.sha256(response).hexdigest() == event['response_sha256']
                path = event.get('path', '')
                if event['tool'] == 'write_file' and event['ok']:
                    writes[path] += 1
                if event['tool'] != 'read_file' or not event['ok']:
                    continue
                assert event['bytes'] == len(response)
                if '/rendered/' in path:
                    short = 'rendered/' + path.split('/rendered/', 1)[1]
                    category = 'master_procedure'
                else:
                    short = path.split('/' + prefix + '/project/', 1)[1]
                    category = ('project_entry' if short == 'AGENTS.md' else
                                'fixture_source' if short in ('sample.txt', 'other.txt') else
                                'fixture_instructions' if short == 'FIXTURE.md' else
                                'fixture_records')
                previous = seen.get(path)
                unchanged = bool(previous and previous['sha256'] == event['response_sha256'])
                intervening_write = bool(previous and previous['writes'] != writes[path])
                reads.append(dict(ordinal=ordinal, path=short, category=category,
                                  bytes=event['bytes'], sha256=event['response_sha256'],
                                  same_as_previous_read=unchanged,
                                  write_since_previous_read=intervening_write,
                                  previous_read_ordinal=previous['ordinal'] if previous else None))
                seen[path] = dict(sha256=event['response_sha256'], writes=writes[path],
                                  ordinal=ordinal)
                buckets[category] += event['bytes']
            assert sum(buckets.values()) == run['retrieved_bytes'], run['run']
            output.append(dict(run=run['run'], scenario=run['scenario'], source=run['source'],
                               repetition=run['repetition'], tool_calls=len(audit),
                               initial_configured_bytes=run['initial_configured_bytes'],
                               retrieved_bytes=run['retrieved_bytes'],
                               configured_plus_retrieval_bytes=(run['initial_configured_bytes']
                                                               + run['retrieved_bytes']),
                               categories=dict(buckets), reads=reads))
    groups = []
    for scenario in ('S01', 'S04', 'S05'):
        for source in ('baseline', 'final'):
            rows = [r for r in output if r['scenario'] == scenario and r['source'] == source]
            historical = next(m for m in metrics if m['host'] == 'codex'
                              and m['scenario'] == scenario and m['source'] == source)
            assert len(rows) == historical['n'] == 3
            computed = {}
            for key in ('retrieved_bytes', 'tool_calls', 'initial_configured_bytes'):
                computed[key] = statistics.median(r[key] for r in rows)
                assert computed[key] == historical[key]['median'], (scenario, source, key)
            computed['configured_plus_retrieval_bytes'] = statistics.median(
                r['configured_plus_retrieval_bytes'] for r in rows)
            groups.append(dict(scenario=scenario, source=source, n=3, medians=computed))
    return dict(scope='Historical Codex S01/S04/S05 root runs only; no host execution or acceptance.',
                method='Successful read_file UTF-8 responses only; ordinal is 1-based broker audit order. '
                       'Categories describe provenance, not necessity. Medians computed per complete run.',
                archive=dict(path=str(archive), **archive_receipt, crc_pass=True),
                inputs=inputs, verified_artifacts=artifacts, status_sections=status_sections,
                groups=groups, runs=output)


if __name__ == '__main__':
    print(json.dumps(analyze(), indent=2, ensure_ascii=False))
