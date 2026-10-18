#!/usr/bin/env python3
"""One-time, preservation-first instruction routing migration. No Git mutations or app control."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

MASTER = Path('/Users/sim/ProgrammingProjects/0-DIRECTIONS/__DIRECTIONS')
BASE = Path('/Users/sim/ProgrammingProjects')
START = '<!-- DIRECTIONS-PROJECT:START -->'
END = '<!-- DIRECTIONS-PROJECT:END -->'
BACKUP = Path('/Users/sim/.local/state/directions-migrations/2026-10-17')
PLAN = Path('/tmp/directions-consumer-migration-plan.json')
RECEIPT = MASTER / 'verification/lean/rollout-2026-10-17/receipts.json'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def block():
    return f'''{START}
## Shared Directions workflow

- **Local master:** `{MASTER}`.
- For Directions commands, use the installed Directions skill in Codex or read the master's
  `commands/<name>.md` completely. Slashless forms work too. Approved-plan continuation uses
  `commands/execute.md`; status alone does not authorize execution.
- Resolve shared `reference/...` from that master. Read universal guidance there on demand;
  use the relevant host global template's routing section if global guidance is unavailable.
  Report a missing master instead of using copied universal guides.
- This section supersedes older generic Directions workflow, copied-guide loading, automatic
  app-control and PR-ceremony instructions in this file. Preserve project-specific architecture,
  build commands, security constraints and product requirements above.
- Retained numbered guides in `docs/` are legacy references, not workflow authority. Preserve
  their project-specific additions; consult them only for relevant historical/project evidence.
- Preserve existing state, selected plans, open gates and session history. Legacy task/state
  reconciliation is separate work; never mark a manual gate complete from an old checkbox.
- Before builds/tests, read the master's `34_testing.md` and inspect startup effects. Desktop/app
  control requires explicit user permission; older automatic quit/launch instructions do not grant it.
  Give full absolute paths for user-operated file/app steps. Preserve dirty work and user limits.
{END}
'''


def run_git(root, *args):
    return subprocess.run(['git', '-C', str(root), *args], capture_output=True,
                          env=dict(os.environ, GIT_OPTIONAL_LOCKS='0'))


def make_plan():
    records = json.loads(Path('/tmp/directions-migration-inventory.json').read_text())
    roots = [Path(r['root']) for r in records]
    entries = {Path(p) for r in records for p in r['entries']}
    extras = [Path(p) for p in json.loads(Path('/tmp/directions-migration-extra.json').read_text())]
    entries.update(extras)
    entries.update(p.with_name('AGENTS.md') for p in extras if p.name == 'CLAUDE.md')
    for root in roots:
        entries.update([root / 'AGENTS.md', root / 'CLAUDE.md'])
    placeholder = (BASE / '1-macOS/AspectRatioUnifier/docs/AGENTS.md').read_bytes()
    changes = []
    for p in sorted(entries):
        if p.is_symlink():
            raise RuntimeError(f'review symlink before editing: {p}')
        before = p.read_bytes() if p.exists() else None
        if before and START.encode() in before:
            raise RuntimeError(f'already migrated; inspect receipts: {p}')
        owner = max((r for r in roots if p.is_relative_to(r)), key=lambda r: len(r.parts))
        action = 'append'
        if before == placeholder:
            action = 'replace-placeholder'
            prefix = f'# Documentation instructions\n\nFollow `{owner / "AGENTS.md"}` for project facts and verified validation commands.\n\n'.encode()
        elif before is None:
            action = 'create'
            other = p.with_name('CLAUDE.md' if p.name == 'AGENTS.md' else 'AGENTS.md')
            if other.is_file():
                facts = f'Read `{other}` for project facts, build commands and safety constraints;\nits host-specific tool mechanics apply only to that host.\n'
            else:
                facts = 'Read `README.md` when present for project facts; inspect actual tooling before proposing checks.\n'
            prefix = (f'# {p.parent.name} — {"Codex" if p.name == "AGENTS.md" else "Claude Code"} instructions\n\n'
                      + facts + f'\nCurrent state: `{owner / "docs/PROJECT_STATE.md"}`. Preserve its plans, gates and handoff pointers.\n\n').encode()
        else:
            prefix = before + b'\n\n'
        after = prefix + block().encode()
        changes.append({'path': str(p), 'owner': str(owner), 'action': action,
                        'before_sha256': digest(before) if before is not None else None,
                        'after_sha256': digest(after), 'after': after.decode(),
                        'mode': p.stat().st_mode & 0o777 if before is not None else 0o644})
    guides = [{'path': p, 'sha256': digest(Path(p).read_bytes())}
              for r in records for p in r['copies']]
    protected = set()
    for root in roots:
        for name in ('PROJECT_STATE.md', 'TASKS.md', 'decisions.md', 'glossary.md'):
            protected.update(p for p in (root / name, root / 'docs' / name) if p.is_file())
        protected.update(p for p in (root / 'IMPLEMENTATION_PLAN.md', root / 'docs/IMPLEMENTATION_PLAN.md') if p.is_file())
        for folder in (root / 'docs/sessions', root / 'specs', root / 'docs/specs'):
            if folder.is_dir():
                protected.update(p for p in folder.rglob('*.md') if p.is_file() and not p.is_symlink())
    protected_records = [{'path': str(p), 'sha256': digest(p.read_bytes())} for p in sorted(protected)]
    projects = []
    for r in records:
        root = Path(r['root'])
        top = run_git(root, 'rev-parse', '--show-toplevel')
        status = run_git(root, 'status', '--porcelain=v1', '--untracked-files=all')
        projects.append({'root': str(root), 'git_ok': top.returncode == 0,
                         'git_toplevel': top.stdout.decode().strip() if top.returncode == 0 else None,
                         'status_sha256': digest(status.stdout),
                         'dirty': bool(status.stdout) if status.returncode == 0 else None})
    # Keep all copied guides: no deletion from a dirty or metadata-missing checkout, no
    # automatic loss of contextual additions, and no broken legacy links.
    plan = {'projects': projects, 'changes': changes, 'retained_guides': guides,
            'protected_records': protected_records,
            'backup_root': str(BACKUP), 'scope': 'instruction routing only; legacy state and guide bytes preserved'}
    PLAN.write_text(json.dumps(plan, indent=2) + '\n')
    print(json.dumps({'projects': len(projects), 'changes': len(changes),
                      'create': sum(c['action'] == 'create' for c in changes),
                      'replace_placeholder': sum(c['action'] == 'replace-placeholder' for c in changes),
                      'retained_guides': len(guides), 'protected_records': len(protected_records),
                      'plan': str(PLAN)}, indent=2))


def apply_plan():
    plan = json.loads(PLAN.read_text())
    if RECEIPT.exists():
        raise RuntimeError('receipt already exists; verify instead of overwriting')
    for c in plan['changes']:
        p = Path(c['path'])
        if not p.is_relative_to(BASE) or p.is_relative_to(MASTER) or p.is_symlink():
            raise RuntimeError(f'unsafe target: {p}')
        actual = digest(p.read_bytes()) if p.exists() else None
        if actual != c['before_sha256']:
            raise RuntimeError(f'changed since preview: {p}')
        if digest(c['after'].encode()) != c['after_sha256']:
            raise RuntimeError(f'bad planned digest: {p}')
    for g in plan['retained_guides'] + plan['protected_records']:
        if digest(Path(g['path']).read_bytes()) != g['sha256']:
            raise RuntimeError(f'guide changed since preview: {g["path"]}')
    BACKUP.mkdir(parents=True, exist_ok=True, mode=0o700)
    # Save and verify every original before the first consumer write.
    for c in plan['changes']:
        if c['before_sha256'] is not None:
            p = Path(c['path'])
            target = BACKUP / p.relative_to(BASE)
            target.parent.mkdir(parents=True, exist_ok=True)
            data = p.read_bytes()
            if target.exists() and target.read_bytes() != data:
                raise RuntimeError(f'backup collision: {target}')
            if not target.exists():
                with target.open('xb') as f:
                    f.write(data)
                target.chmod(0o600)
            if digest(target.read_bytes()) != c['before_sha256']:
                raise RuntimeError(f'backup verification failed: {target}')
            c['backup'] = str(target)
    private_plan = BACKUP / 'plan.json'
    with private_plan.open('x') as f:
        json.dump(plan, f, indent=2)
    private_plan.chmod(0o600)
    for c in plan['changes']:
        p = Path(c['path'])
        actual = digest(p.read_bytes()) if p.exists() else None
        if actual != c['before_sha256']:
            raise RuntimeError(f'concurrent change; earlier writes retained in private plan: {p}')
        p.write_bytes(c['after'].encode())
        p.chmod(c['mode'])
    receipt = {**plan, 'changes': [{k: v for k, v in c.items() if k != 'after'} for c in plan['changes']]}
    RECEIPT.write_text(json.dumps(receipt, indent=2) + '\n')
    verify()


def verify():
    receipt = json.loads(RECEIPT.read_text())
    for c in receipt['changes']:
        p = Path(c['path'])
        data = p.read_bytes()
        if digest(data) != c['after_sha256'] or data.count(START.encode()) != 1 or data.count(END.encode()) != 1:
            raise RuntimeError(f'installed content mismatch: {p}')
        if c['before_sha256'] is not None:
            old = Path(c['backup']).read_bytes()
            if digest(old) != c['before_sha256']:
                raise RuntimeError(f'backup content mismatch: {p}')
            if c['action'] == 'append' and not data.startswith(old):
                raise RuntimeError(f'original prefix lost: {p}')
    for g in receipt['retained_guides'] + receipt['protected_records']:
        if digest(Path(g['path']).read_bytes()) != g['sha256']:
            raise RuntimeError(f'legacy guide was modified: {g["path"]}')
    print(f'PASS: {len(receipt["projects"])} projects; {len(receipt["changes"])} entries; '
          f'{len(receipt["retained_guides"])} guide hashes and {len(receipt["protected_records"])} '
          'state/spec/history hashes unchanged; all original backups verified')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['plan', 'apply', 'verify'])
    args = parser.parse_args()
    {'plan': make_plan, 'apply': apply_plan, 'verify': verify}[args.mode]()
