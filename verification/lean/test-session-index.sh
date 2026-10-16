#!/usr/bin/env bash
set -euo pipefail
LEAN_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
python3 - "$LEAN_ROOT/scripts/sync-session-index.sh" <<'PY'
import hashlib, pathlib, subprocess, sys, tempfile
script=pathlib.Path(sys.argv[1])
count=0
def case(name, files, rows='', archive=None, expected=0, fix=False, diagnostic=None):
 global count
 with tempfile.TemporaryDirectory(prefix='lean sessions ') as tmp:
  d=pathlib.Path(tmp)
  index=d/'_index.md'; index.write_text('| Date | Log |\n|---|---|\n'+rows)
  original_index=index.read_bytes()
  for file in files: (d/file).write_text('retained evidence\n')
  if archive is not None: (d/'_index-archive.md').write_text(archive)
  retained={p.name:p.read_bytes() for p in d.iterdir() if p != index}
  args=['bash',str(script),str(d)]+(['--fix'] if fix else [])
  result=subprocess.run(args,capture_output=True,text=True)
  assert result.returncode==expected,(name,result.returncode,result.stdout,result.stderr)
  if diagnostic: assert diagnostic in result.stdout,(name,result.stdout)
  for file,data in retained.items(): assert (d/file).read_bytes()==data,name
  if not fix:
   assert index.read_bytes()==original_index,(name,'read-only index changed')
  else:
   # Existing rows, order and text must survive insertion, including orphan rows.
   remaining=iter(index.read_bytes().splitlines(keepends=True))
   assert all(any(line==candidate for candidate in remaining) for line in original_index.splitlines(keepends=True)),(name,'old rows changed')
  if fix and expected in (0,1):
   first=index.read_bytes(); again=subprocess.run(args,capture_output=True,text=True)
   assert again.returncode==expected and index.read_bytes()==first,(name,again.stdout)
  count+=1
case('empty',[])
case('no archive',['2026-01-01.md'],'| 2026-01-01 | x |\n')
case('union',['2026-01-01.md','2026-01-02.md'],'| 2026-01-02 | [log](2026-01-02.md) |\n','| 2026-01-01 | [log](2026-01-01.md) |\n')
case('dot link',['2026-01-01.md'],'| 2026-01-01 | [log](./2026-01-01.md) |\n')
case('suffix wins',['2026-01-01-extra.md'],'| 2026-01-01 | [log](2026-01-01-extra.md) |\n')
case('display suffix',['2026-01-01.md'],'| 2026-01-01-b | [log](2026-01-01.md) |\n')
case('duplicate',['2026-01-01.md'],'| 2026-01-01 | x |\n','| 2026-01-01 | x |\n')
case('missing',['2026-01-01.md'],expected=1,diagnostic='MISSING')
case('orphan',[],'| 2026-01-01 | x |\n',expected=1,diagnostic='ORPHAN')
case('fix',['2026-01-01.md'],fix=True)
case('fix preserves archive',['2026-01-01.md','2026-01-02.md'],archive='| 2026-01-01 | x |\n',fix=True)
case('fix cannot erase orphan',['2026-01-02.md'],'| 2026-01-01 | x |\n',expected=1,fix=True)
case('conflict surfaced',['2026-01-01.sync-conflict-abc.md'],expected=1,diagnostic='2026-01-01.sync-conflict-abc')
case('conflict fix retains target',['2026-01-01.sync-conflict-abc.md'],fix=True)
with tempfile.TemporaryDirectory() as tmp:
 d=pathlib.Path(tmp)
 assert subprocess.run(['bash',str(script),str(d)],capture_output=True).returncode==2
 (d/'_index.md').write_text('no table\n'); (d/'2026-01-01.md').write_text('evidence')
 before=(d/'_index.md').read_bytes()
 result=subprocess.run(['bash',str(script),str(d),'--fix'],capture_output=True,text=True)
 assert result.returncode==3,(result.returncode,result.stderr)
 assert (d/'_index.md').read_bytes()==before
 count+=2
print(f'PASS: {count} session-index cases; source sha256={hashlib.sha256(script.read_bytes()).hexdigest()}')
PY
