#!/usr/bin/env python3
"""Read-only consumer inventory; analyze disposable copies, retain hashes and entry points."""
import difflib
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

DEST = Path(__file__).resolve().parent
MASTER = DEST.parents[2]
PROJECTS = {
    'Magpie': Path('/Users/sim/ProgrammingProjects/1-macOS/Magpie'),
    'App-Websites': Path('/Users/sim/ProgrammingProjects/3-Websites/App-Websites'),
}
sha = lambda data: hashlib.sha256(data).hexdigest()
report = {'method': 'Read-only source capture; comparisons on disposable snapshots. Differing lines are preservation candidates, not proven project customizations.', 'projects': {}}
for name, root in PROJECTS.items():
    env = dict(os.environ, GIT_OPTIONAL_LOCKS='0')
    status = subprocess.run(['git', '-C', str(root), 'status', '--porcelain=v1', '--untracked-files=all'],
                            env=env, capture_output=True, text=True)
    records = []
    with tempfile.TemporaryDirectory(prefix='lean consumer snapshot ') as temporary:
        snapshot = Path(temporary)
        paths = sorted(p for p in root.rglob('*') if p.is_file() and not p.is_symlink()
                       and not any(part in ('.git', 'node_modules', '.build') for part in p.relative_to(root).parts)
                       and (p.name in ('AGENTS.md', 'CLAUDE.md', 'sync-session-index.sh')
                            or re.fullmatch(r'\d\d_.*\.md', p.name)))
        for path in paths:
            relative = path.relative_to(root)
            target = snapshot / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
            data = target.read_bytes()
            canonical = MASTER / ('scripts/sync-session-index.sh' if path.name == 'sync-session-index.sh' else path.name)
            master_data = canonical.read_bytes() if canonical.is_file() else None
            record = {'path': str(relative), 'sha256': sha(data), 'bytes': len(data),
                      'master_path': str(canonical) if master_data is not None else None,
                      'master_sha256': sha(master_data) if master_data is not None else None,
                      'exact_duplicate': data == master_data,
                      'disposition': 'preserve pending contextual comparison'}
            if master_data is not None and data != master_data:
                record['consumer_only_lines'] = sum(1 for line in difflib.ndiff(
                    master_data.decode().splitlines(), data.decode().splitlines()) if line.startswith('+ '))
            if path.name in ('AGENTS.md', 'CLAUDE.md', 'sync-session-index.sh'):
                retained = DEST / 'snapshots' / name / relative
                retained.parent.mkdir(parents=True, exist_ok=True)
                retained.write_bytes(data)
                record['retained_snapshot'] = str(retained.relative_to(DEST))
            assert sha(path.read_bytes()) == sha(data), f'source changed during capture: {path}'
            records.append(record)
    report['projects'][name] = {'root': str(root), 'git_status_returncode': status.returncode,
                              'git_status': status.stdout.splitlines(), 'git_status_error': status.stderr,
                              'files': records}
(DEST / 'inventory.json').write_text(json.dumps(report, indent=2) + '\n')
for name, project in report['projects'].items():
    records = project['files']
    print(name, len(records), 'files;', sum(r['exact_duplicate'] for r in records),
          'exact duplicates;', len(project['git_status']), 'dirty/untracked status entries')
