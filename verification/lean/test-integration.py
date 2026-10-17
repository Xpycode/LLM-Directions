#!/usr/bin/env python3
"""Check routing/references and baseline or explicitly reviewed source bytes."""
import hashlib
import json
import re
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parents[2]
records = json.loads((root / 'verification/lean/baseline/manifest.json').read_text())['files']
reviewed = json.loads((root / 'verification/guidance-review-2026-10-17/receipts.json').read_text())['sources']
for name in ('IMPLEMENTATION_PLAN.md', '20_swiftui-gotchas.md', '22_macos-platform.md',
             '29_web-strato-hosting.md', '44_my-glossary.md', 'MACHINES.md'):
    # Later intentional guidance edits have their own receipts; never rewrite the frozen baseline.
    expected = reviewed[name] if name in reviewed else records[name]
    assert hashlib.sha256((root / name).read_bytes()).hexdigest() == expected['sha256'], name
generated = subprocess.check_output(['bash', str(root / 'scripts/gen-directions-index.sh')], text=True)
routes = re.findall(r'^- .*`([0-9][0-9]_[a-z0-9-]+\.md)`$', generated, re.M)
assert len(routes) == len(set(routes)) == 47
for route in routes:
    assert (root / route).is_file(), route
for name in ('CODEX-GLOBAL-TEMPLATE.md', 'CLAUDE-GLOBAL-TEMPLATE.md'):
    source = (root / name).read_text()
    body = re.search(r'<!-- DIRECTIONS-INDEX:START[^\n]*\n(.*?)<!-- DIRECTIONS-INDEX:END -->', source, re.S)[1]
    assert set(re.findall(r'`([0-9][0-9]_[a-z0-9-]+\.md)`', body)) == set(routes), name
paths = set()
for name in ('commands/log.md', 'commands/execute.md', 'commands/status.md', 'commands/setup.md',
             'commands/make-plan.md', 'reference/log/app-handoff.md'):
    source = (root / name).read_text()
    for path in re.findall(r'(?:<master>/)?(reference/[a-z/-]+\.md)', source):
        assert (root / path).is_file(), (name, path)
        paths.add(path)
assert {'reference/task-state.md', 'reference/log/app-handoff.md',
        'reference/log/mac-handoff.md', 'reference/log/claude-integration.md'} <= paths
print('PASS: 47 final routes, shared task/log references, unchanged Mac plan and reviewed guide bytes')
