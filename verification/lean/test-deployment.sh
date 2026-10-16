#!/usr/bin/env bash
# All installations and fixture Git metadata are confined to a disposable directory.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
python3 - "$ROOT" <<'PY'
import hashlib, json, os, re, shutil, subprocess, sys, tempfile
from pathlib import Path
source = Path(sys.argv[1])
checks = 0
legacy = source / 'verification/lean/deployment/snapshots/App-Websites/docs/scripts/sync-session-index.sh'
def inventory(root):
    return {str(p.relative_to(root)): ('link', os.readlink(p)) if p.is_symlink()
            else ('file', hashlib.sha256(p.read_bytes()).hexdigest()) if p.is_file()
            else ('dir', '') for p in root.rglob('*')}
with tempfile.TemporaryDirectory(prefix='directions deployment ') as temporary:
    scratch = Path(temporary)
    master, home, outside = [scratch / n for n in ('master with spaces', 'home with spaces', 'outside')]
    for directory in (master, home, outside): directory.mkdir()
    (outside / 'sentinel').write_text('must remain unchanged\n')
    outside_before = inventory(outside)
    # Frozen old consumer checker versus master: archive-only entries expose the old defect.
    sessions = scratch / 'sessions'; sessions.mkdir()
    (sessions / '_index.md').write_text('| Date | Log |\n|---|---|\n')
    (sessions / '_index-archive.md').write_text('| 2026-01-01 | [log](2026-01-01.md) |\n')
    (sessions / '2026-01-01.md').write_text('preserved historical evidence\n')
    retained = inventory(sessions)
    old = subprocess.run(['bash', str(legacy), str(sessions)], capture_output=True)
    current = subprocess.run(['bash', str(source / 'scripts/sync-session-index.sh'), str(sessions)], capture_output=True)
    assert old.returncode == 1 and current.returncode == 0, (old, current)
    assert inventory(sessions) == retained
    for name in ('scripts', 'codex', 'commands', 'reference', 'hooks', 'claude-statusline', 'skills'):
        if (source / name).exists(): shutil.copytree(source / name, master / name)
    for path in source.glob('*.md'): shutil.copy2(path, master / path.name)
    for name in ('deploy-codex.sh', 'redeploy.sh', 'CLAUDE-SETTINGS-TEMPLATE.json', 'CLAUDE-SETTINGS-PERMISSIONS.json'):
        shutil.copy2(source / name, master / name)
    subprocess.run(['git', 'init', '-q', str(master)], check=True)
    # Independent master-relative reference: consumer has a contradictory same-name file.
    (master / 'reference').mkdir(exist_ok=True)
    (master / 'reference/fixture.md').write_text('canonical reference\n')
    (master / 'commands/fixture.md').write_text('Read [fixture](reference/fixture.md).\n')
    (outside / 'reference').mkdir()
    (outside / 'reference/fixture.md').write_text('stale consumer reference\n')
    outside_before = inventory(outside)
    reference = re.search(r'\]\((reference/[^)]+)\)', (master / 'commands/fixture.md').read_text())[1]
    assert (master / reference).read_text() == 'canonical reference\n'
    assert (outside / reference).read_text() == 'stale consumer reference\n'
    assert 'resolved master root' in (master / 'codex/skills/directions/SKILL.md').read_text()
    for entry in ('AGENTS.md', 'CLAUDE.md'):
        text = (master / entry).read_text()
        assert 'Without global' in text and 'commands/<name>.md' in text
        assert 'routing section only' in text or 'only the routing section' in text
    env = os.environ.copy()
    env.update(HOME=str(home), CODEX_HOME=str(home / '.codex'),
               DIRECTIONS_DEPLOY_HOME=str(home), DIRECTIONS_CODEX_HOME=str(home / '.codex'),
               TMPDIR=str(scratch))
    def run(host, *args, ok=True):
        global checks
        before = inventory(home)
        result = subprocess.run(['bash', str(master / host), *args], env=env, cwd=outside,
                                capture_output=True, text=True)
        assert (result.returncode == 0) == ok, (host, args, result.stdout, result.stderr)
        if not ok: assert inventory(home) == before, 'failed validation mutated installation'
        assert inventory(outside) == outside_before, 'outside fixture path changed'
        checks += 1
    # Contaminated numbered files are excluded and preserved, never installed as routes.
    artifact = master / '00_base-sync-conflict-20261016.md'
    artifact.write_text('# contaminated\nTRIGGERS: secret artifact\n')
    artifact_before = artifact.read_bytes()
    before = inventory(home)
    run('deploy-codex.sh', '--dry-run'); run('redeploy.sh', '--dry-run')
    assert inventory(home) == before
    # Missing globals: complete install of both hosts, including real settings and hook installer.
    run('deploy-codex.sh')
    run('redeploy.sh')
    codex, claude = home / '.codex/AGENTS.md', home / '.claude/CLAUDE.md'
    def body(path):
        return re.search(r'<!-- DIRECTIONS-INDEX:START[^\n]*\n(.*?)<!-- DIRECTIONS-INDEX:END -->', path.read_text(), re.S)[1]
    assert body(codex) == body(claude)
    assert str(master) in body(codex) and 'sync-conflict' not in body(codex)
    assert artifact.read_bytes() == artifact_before
    web = source / 'verification/lean/deployment/snapshots/App-Websites'
    assert './check-invariants.sh' in (web / 'CLAUDE.md').read_text()
    assert 'swift build' not in (web / 'CLAUDE.md').read_text()
    assert '[build command]' in (web / 'docs/AGENTS.md').read_text()
    assert 'web, website, HTML: `24_web-gotchas.md`' in body(claude)
    # Personal byte preservation, including CRLF and absent final newline.
    prefix, suffix = b'personal prefix\r\n', b'personal suffix without newline'
    codex.write_bytes(prefix + codex.read_bytes() + suffix)
    run('deploy-codex.sh')
    assert codex.read_bytes().startswith(prefix) and codex.read_bytes().endswith(suffix)
    personal = b'Claude personal whole-file replacement fixture\n'
    claude.write_bytes(personal)
    run('redeploy.sh')
    assert any(p.read_bytes() == personal for p in claude.parent.glob('CLAUDE.md.bak-*'))
    assert personal not in claude.read_bytes()
    stable = (codex.read_bytes(), claude.read_bytes(), (home / '.claude/settings.json').read_bytes())
    run('deploy-codex.sh'); run('redeploy.sh')
    assert stable == (codex.read_bytes(), claude.read_bytes(), (home / '.claude/settings.json').read_bytes())
    # Failed render/marker validation precedes commands/settings/skill writes, also when skipped.
    for host, template, skip in [('deploy-codex.sh', 'CODEX-GLOBAL-TEMPLATE.md', '--skip-agents-md'),
                                 ('redeploy.sh', 'CLAUDE-GLOBAL-TEMPLATE.md', '--skip-claude-md')]:
        path = master / template
        saved = path.read_bytes()
        path.write_bytes(saved.replace(b'DIRECTIONS-INDEX:END', b'BROKEN:END'))
        run(host, ok=False); run(host, skip, ok=False)
        path.write_bytes(saved)
    saved = codex.read_bytes()
    codex.write_text('<!-- DIRECTIONS-CODEX:END -->\n<!-- DIRECTIONS-CODEX:START bad -->\n')
    run('deploy-codex.sh', ok=False)
    codex.write_bytes(saved)
    settings = home / '.claude/settings.json'
    saved = settings.read_bytes(); settings.write_text('{bad json')
    run('redeploy.sh', ok=False); settings.write_bytes(saved)
    prefs = master / 'CLAUDE-SETTINGS-TEMPLATE.json'
    saved_settings, saved_prefs = settings.read_bytes(), prefs.read_bytes()
    malformed = [
        {'hooks': {event: 42}} for event in ('SessionStart', 'Stop', 'UserPromptSubmit', 'PreToolUse', 'IndependentEvent')
    ] + [
        {'hooks': {'SessionStart': [42]}},
        {'hooks': {'Stop': [{'hooks': 42}]}},
        {'hooks': {'PreToolUse': [{'hooks': [42]}]}},
        {'statusLine': 42},
    ]
    for value in malformed:
        # Live settings corruption and template-introduced corruption both fail before writes.
        settings.write_text(json.dumps(value))
        run('redeploy.sh', ok=False)
        settings.write_bytes(saved_settings)
        prefs.write_text(json.dumps(value))
        run('redeploy.sh', ok=False)
        prefs.write_bytes(saved_prefs)
    # Even with preference merging disabled the hook installer still runs and must preflight.
    settings.write_text('{"hooks":{"SessionStart":42}}')
    run('redeploy.sh', '--skip-settings', ok=False)
    settings.write_bytes(saved_settings)
    # A template can repair an invalid event with an empty array. Structural changes have
    # no scalar leaf paths, but the real merge must still match its validated preview.
    repaired = json.loads(saved_settings)
    repaired['hooks']['SessionStart'] = 42
    repaired['hooks']['IndependentEvent'] = [{'hooks': [{'type': 'command', 'command': 'personal-hook'}]}]
    settings.write_text(json.dumps(repaired))
    template_repair = json.loads(saved_prefs)
    template_repair['hooks'] = {'SessionStart': []}
    prefs.write_text(json.dumps(template_repair))
    run('redeploy.sh')
    installed = json.loads(settings.read_text())
    assert isinstance(installed['hooks']['SessionStart'], list)
    assert installed['hooks']['IndependentEvent'] == repaired['hooks']['IndependentEvent']
    settings.write_bytes(saved_settings); prefs.write_bytes(saved_prefs)
    saved = prefs.read_bytes(); prefs.write_text('{bad json')
    run('redeploy.sh', ok=False); prefs.write_bytes(saved)
    perms = master / 'CLAUDE-SETTINGS-PERMISSIONS.json'
    saved = perms.read_bytes(); perms.write_text('{}')
    run('redeploy.sh', ok=False); perms.write_bytes(saved)
    command = master / 'commands/execute.md'
    saved = command.read_bytes(); command.unlink()
    run('deploy-codex.sh', ok=False); run('redeploy.sh', ok=False)
    command.write_bytes(saved)
    before = inventory(home)
    run('deploy-codex.sh', '--dry-run'); run('redeploy.sh', '--dry-run')
    assert inventory(home) == before
print(f'PASS: {checks} deployment invocations; both hosts, missing globals, spaces, shared routes, references, contamination, preservation, backups, idempotence, pre-write failure, dry-run and outside sentinel checks')
PY
