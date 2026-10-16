#!/usr/bin/env bash
set -euo pipefail
LEAN_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
python3 - "$LEAN_ROOT/install-directions.sh" <<'PY'
import os,pathlib,subprocess,sys,tempfile
script=sys.argv[1]
def inventory(root):
 return {str(p.relative_to(root)):('link',os.readlink(p)) if p.is_symlink() else ('file',p.read_bytes()) if p.is_file() else ('dir',None) for p in root.rglob('*')}
with tempfile.TemporaryDirectory(prefix='lean installer ') as temp:
 root=pathlib.Path(temp); env=os.environ.copy(); env['HOME']=str(root); env['CODEX_HOME']=str(root/'codex')
 for populated in [False,True]:
  if populated:
   (root/'.claude').mkdir(); (root/'.claude/CLAUDE.md').write_text('personal instructions\n')
   (root/'sentinel').symlink_to('.claude/CLAUDE.md')
  before=inventory(root)
  for args,code in [([],1),([],1),(['--help'],0),(['-h'],0),(['--bad'],2),(['--help','extra'],2)]:
   result=subprocess.run(['bash',script,*args],env=env,cwd=root,capture_output=True,text=True)
   assert result.returncode==code,(args,result)
   assert inventory(root)==before,args
   if code in (0,1): assert 'replaces CLAUDE.md' in result.stdout and '--dry-run' in result.stdout
print('PASS: 12 retirement cases; absent/existing home inventories unchanged')
PY
