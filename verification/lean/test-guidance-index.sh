#!/usr/bin/env bash
# All writes occur in a disposable master containing a copied generator.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
python3 - "$ROOT/scripts/gen-directions-index.sh" <<'PY'
import hashlib
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

checks = 0
with tempfile.TemporaryDirectory(prefix='directions-guidance-') as scratch:
    master = Path(scratch) / 'master with spaces'
    (master / 'scripts').mkdir(parents=True)
    generator = master / 'scripts/gen-directions-index.sh'
    shutil.copy2(sys.argv[1], generator)
    docs = {
        '00_base.md': '# Base\nTRIGGERS: alpha, beta, gamma, delta, epsilon, zeta, eta\n',
        '01_title.md': '# Title fallback\n',
        '02_bold.md': '# Bold\n**Triggers:** literal *, a|b\n',
        '03_quote.md': '# Quote\n> Triggers: quote\n',
        '04_no-title.md': 'plain content\n',
        '05_redirect.md': '# Redirect\n LOAD: redirect elsewhere\n',
        '06_other.md': '# Other\nLOAD: ReDiReCt\n',
    }
    artifacts = [
        '00_base.sync-conflict-20261016-123456-DEVICE.md',
        '00_base (copy).md', '00_base.backup.md', '00_base.bak.md',
        '00_base.md~', '00_base.md.bak', '.00_base.md.swp', '#00_base.md#',
        '00_base-backup.md', '00_base-copy.md', '00_base-old.md',
        '00_base-sync-conflict-20261016.md', '00_base_orig.md',
        '00_base-tmp.md', '00_base-swp.md', '09_Uppercase.md',
    ]
    docs.update({name: '# Must never appear\nTRIGGERS: contaminated\n' for name in artifacts})
    for name, contents in docs.items():
        (master / name).write_text(contents)
    (master / '07_link.md').symlink_to(master / '00_base.md')
    (master / '08_directory.md').mkdir()
    def hashes():
        return {name: hashlib.sha256((master / name).read_bytes()).hexdigest() for name in docs}
    before = hashes()
    destination = master / 'template.md'
    start = b'<!-- DIRECTIONS-INDEX:START custom annotation -->\n'
    end = b'<!-- DIRECTIONS-INDEX:END -->\n'
    def run(*args, expected=0):
        global checks
        previous = destination.read_bytes() if destination.exists() else None
        result = subprocess.run(['bash', str(generator), *args], capture_output=True)
        assert result.returncode == expected, (args, result.returncode, result.stderr)
        if expected:
            assert (destination.read_bytes() if destination.exists() else None) == previous, args
            assert not list(master.glob('.directions-index-*')), args
        checks += 1
        return result.stdout
    preview = run()
    for name in list(docs)[:5]:
        assert preview.count(f'`{name}`'.encode()) == 1, name
    assert b'alpha, beta, gamma, delta, epsilon, zeta \xe2\x80\xa6' in preview, preview
    assert b'literal *, a/b' in preview, preview
    assert b'Title fallback' in preview and b'04_no-title' in preview
    for name in list(docs)[5:]:
        assert name.encode() not in preview, name
    assert b'07_link.md' not in preview and b'08_directory.md' not in preview
    assert run() == preview
    # A different rendered base must not change discovery or accept docs from that path.
    other = Path(scratch) / 'other'
    other.mkdir()
    (other / '99_wrong-source.md').write_text('# Wrong source\n')
    rendered = run('--base', str(other))
    assert f'`{other}/`'.encode() in rendered and b'99_wrong-source.md' not in rendered
    assert b'00_base.md' in rendered
    for newline in [b'\n', b'\r\n']:
        prefix = b'prefix\x00\n' + start
        suffix = end + b'unchanged suffix without newline'
        prefix, suffix = prefix.replace(b'\n', newline), suffix.replace(b'\n', newline)
        destination.write_bytes(prefix + b'old body' + newline + suffix)
        destination.chmod(0o640)
        run('--write', str(destination), '--base', '[LOCAL_DIRECTIONS_PATH]')
        actual = destination.read_bytes()
        assert actual.startswith(prefix) and actual.endswith(suffix)
        assert destination.stat().st_mode & 0o777 == 0o640
        run('--base', '[LOCAL_DIRECTIONS_PATH]', '--write', str(destination))
        assert destination.read_bytes() == actual
    # Preserve supported heading bootstrap, then prove repeat output is identical.
    for boundary in [b'## Next\nkeep', b'---\nkeep', b'']:
        destination.write_bytes(b'before\n## Directions Index\nold\n' + boundary)
        run('--write', str(destination))
        actual = destination.read_bytes()
        assert actual.startswith(b'before\n## Directions Index\n') and actual.endswith(boundary)
        run('--write', str(destination))
        assert destination.read_bytes() == actual
    malformed = [
        start, end, end + start, start + start + end, start + end + end,
        start + end + start + end, b'prefix ' + start + end,
        start + b'prefix ' + end, b'<!-- DIRECTIONS-INDEX:START broken\n' + end,
        b'## Directions Index\n' + end, b'no heading or markers',
        b'## Directions Index\none\n## Directions Index\ntwo\n',
    ]
    for contents in malformed:
        destination.write_bytes(contents)
        run('--write', str(destination), expected=2)
    destination.write_bytes(start + b'original\n' + end)
    bad_args = [
        ['--base'], ['--write'], ['--base', ''], ['--write', ''],
        ['--base', '--write'], ['--write', '--base'], ['--unknown'],
        ['--base', 'a', '--base', 'b'], ['--write', str(destination), '--write', str(destination)],
        ['--base', 'a\nb'], ['--write', 'a\rb'], ['--help', '--unknown'],
    ]
    for args in bad_args:
        run(*args, expected=2)
    run('--write', str(destination), '--unknown', expected=2)
    run('--write', str(master / 'missing.md'), expected=2)
    assert not (master / 'missing.md').exists()
    link = master / 'destination-link.md'
    link.symlink_to(destination)
    run('--write', str(link), expected=2)
    assert link.is_symlink()
    run('--help')
    assert hashes() == before, 'source or excluded artifacts changed'
    # Keep only artifacts/redirects: no eligible docs must fail before destination changes.
    for name in list(docs)[:5]:
        (master / name).unlink()
    assert run(expected=2) == b''
    run('--write', str(destination), expected=2)
    for path in master.glob('[0-9][0-9]_*.md'):
        if path.is_file() or path.is_symlink():
            path.unlink()
    run('--write', str(destination), expected=2)
print(f'PASS: {checks} generator invocations; canonical eligibility, contamination preservation, arguments, markers, bootstrap, byte/mode preservation, empty sets and idempotence')
PY
