#!/usr/bin/env bash
# deploy-codex.sh — install or refresh the Codex side of Directions on this Mac.
#
# Installs the Directions skill in this Codex build's user-skill location and merges a generated,
# marked Directions block into the user's global AGENTS.md without replacing unrelated guidance.
# The skill is symlinked to this repo, so a git pull updates the live workflow adapter immediately.
#
# Usage:
#   bash deploy-codex.sh
#   bash deploy-codex.sh --dry-run
#   bash deploy-codex.sh --skip-agents-md

set -euo pipefail

dry_run=0
skip_agents=0
for arg in "$@"; do
  case "$arg" in
    --dry-run) dry_run=1 ;;
    --skip-agents-md) skip_agents=1 ;;
    -h|--help) sed -n '2,13p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) printf 'deploy-codex.sh: unknown flag: %s\n' "$arg" >&2; exit 2 ;;
  esac
done

repo=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
skill_src="$repo/codex/skills/directions"
deploy_home="${DIRECTIONS_DEPLOY_HOME:-$HOME}"
codex_dir="${DIRECTIONS_CODEX_HOME:-${CODEX_HOME:-$deploy_home/.codex}}"
skill_root="$codex_dir/skills"
skill_dest="$skill_root/directions"
agents_file="$codex_dir/AGENTS.md"
template="$repo/CODEX-GLOBAL-TEMPLATE.md"
stamp=$(date +%Y%m%d-%H%M%S)

say() { printf '%s\n' "$*"; }

[ -f "$skill_src/SKILL.md" ] || { say "✗ Directions skill missing: $skill_src/SKILL.md"; exit 1; }
[ -f "$template" ] || { say "✗ Codex template missing: $template"; exit 1; }
[ -x "$repo/scripts/gen-directions-index.sh" ] || {
  say "✗ Index generator is missing or not executable: $repo/scripts/gen-directions-index.sh"
  exit 1
}

rendered=""
merged=""
cleanup() {
  [ -z "$rendered" ] || rm -f "$rendered"
  [ -z "$merged" ] || rm -f "$merged"
}
trap cleanup EXIT

# Prepare and validate the complete AGENTS.md result before changing either live artifact.
{
  [ ! -L "$agents_file" ] || [ -e "$agents_file" ] || {
    say "✗ $agents_file is a broken symlink; fix it before deployment"
    exit 1
  }
  rendered=$(mktemp)
  merged=$(mktemp)
  python3 -I - "$template" "$repo" "$rendered" <<'PY'
from pathlib import Path
import sys
Path(sys.argv[3]).write_text(Path(sys.argv[1]).read_text().replace('[LOCAL_DIRECTIONS_PATH]', sys.argv[2]))
PY
  "$repo/scripts/gen-directions-index.sh" --format inline --write "$rendered" --base "$repo" >/dev/null
  python3 -I - "$rendered" "$repo" <<'PY'
from pathlib import Path
import re, sys
text = Path(sys.argv[1]).read_text()
root = Path(sys.argv[2])
assert root.is_absolute() and (root / 'commands/execute.md').is_file()
for name in re.findall(r'`((?:commands/)?[0-9a-z][0-9a-z_-]*\.md)`', text):
    assert (root / name).is_file(), f'unresolved master reference: {name}'
assert len(re.findall(r'^<!-- DIRECTIONS-CODEX:START .* -->$', text, re.M)) == 1
assert text.count('DIRECTIONS-CODEX:START') == text.count('DIRECTIONS-CODEX:END') == 1
assert text.endswith('<!-- DIRECTIONS-CODEX:END -->\n')
PY
  if grep -q '\[LOCAL_DIRECTIONS_PATH\]' "$rendered"; then
    say "  ✗ unresolved [LOCAL_DIRECTIONS_PATH]; refusing to install"
    exit 1
  fi

  if [ -f "$agents_file" ]; then
    python3 -I - "$agents_file" <<'PY'
from pathlib import Path
import re, sys
text = Path(sys.argv[1]).read_text()
starts = [m.start() for m in re.finditer('DIRECTIONS-CODEX:START', text)]
ends = [m.start() for m in re.finditer('DIRECTIONS-CODEX:END', text)]
assert (not starts and not ends) or (len(starts) == len(ends) == 1 and starts[0] < ends[0]), 'invalid managed markers'
if starts:
    assert len(re.findall(r'^<!-- DIRECTIONS-CODEX:START .* -->$', text, re.M)) == 1, 'invalid START line'
    assert len(re.findall(r'^<!-- DIRECTIONS-CODEX:END -->$', text, re.M)) == 1, 'invalid END line'
PY
    start_count=$(grep -c 'DIRECTIONS-CODEX:START' "$agents_file" || true)
    end_count=$(grep -c 'DIRECTIONS-CODEX:END' "$agents_file" || true)
    if [ "$start_count" -ne "$end_count" ]; then
      say "  ✗ managed block markers are unbalanced in $agents_file; fix them manually"
      exit 1
    fi
    if [ "$start_count" -gt 1 ]; then
      say "  ✗ multiple managed Directions blocks found in $agents_file; fix them manually"
      exit 1
    fi

    if [ "$start_count" -eq 1 ]; then
      python3 -I - "$agents_file" "$rendered" "$merged" <<'PY'
from pathlib import Path
import sys
original, replacement = [Path(p).read_bytes() for p in sys.argv[1:3]]
start = original.rfind(b'\n', 0, original.index(b'DIRECTIONS-CODEX:START')) + 1
end = original.find(b'\n', original.index(b'DIRECTIONS-CODEX:END'))
end = len(original) if end < 0 else end + 1
Path(sys.argv[3]).write_bytes(original[:start] + replacement + original[end:])
PY
    else
      cp "$agents_file" "$merged"
      [ ! -s "$merged" ] || printf '\n' >> "$merged"
      cat "$rendered" >> "$merged"
    fi
  else
    cp "$rendered" "$merged"
  fi
}

[ "$dry_run" = 1 ] && say "— DRY RUN: no files will change —"
say "Repo:   $repo"
say "Skill:  $skill_dest"
say "Global: $agents_file"
say ""

skill_changed=0
skill_backup=""
agents_changed=0
agents_existed=0
agents_backup=""
restore_live() {
  if [ "$agents_changed" = 1 ]; then
    if [ "$agents_existed" = 1 ]; then
      cp "$agents_backup" "$agents_file" || true
    else
      rm -f "$agents_file"
    fi
  fi
  if [ "$skill_changed" = 1 ]; then
    rm -f "$skill_dest"
    [ -z "$skill_backup" ] || mv "$skill_backup" "$skill_dest"
  fi
}

say "Directions skill:"
if [ -L "$skill_dest" ] && [ "$skill_dest" -ef "$skill_src" ]; then
  say "  ✓ already linked"
elif [ "$dry_run" = 1 ]; then
  if [ -e "$skill_dest" ] || [ -L "$skill_dest" ]; then
    say "  [dry-run] would back up existing skill"
  fi
  say "  [dry-run] would link $skill_dest → $skill_src"
else
  mkdir -p "$skill_root"
  if [ -e "$skill_dest" ] || [ -L "$skill_dest" ]; then
    skill_backup="$skill_dest.bak-$stamp"
    mv "$skill_dest" "$skill_backup"
    say "  • backed up existing skill → directions.bak-$stamp"
  fi
  if ! ln -s "$skill_src" "$skill_dest"; then
    [ -z "$skill_backup" ] || mv "$skill_backup" "$skill_dest"
    say "  ✗ could not link the Directions skill"
    exit 1
  fi
  skill_changed=1
  say "  → linked $skill_dest"
fi
say ""

if [ "$skip_agents" = 1 ]; then
  say "Global AGENTS.md: skipped (--skip-agents-md)"
else
  say "Global AGENTS.md:"

  if [ -f "$agents_file" ] && cmp -s "$merged" "$agents_file"; then
    say "  ✓ managed Directions block is current"
  elif [ "$dry_run" = 1 ]; then
    if [ -f "$agents_file" ]; then
      say "  [dry-run] would back up AGENTS.md and refresh only the managed Directions block"
    else
      say "  [dry-run] would create $agents_file"
    fi
  else
    mkdir -p "$codex_dir"
    agents_backup="$agents_file.bak-$stamp"
    if [ -f "$agents_file" ]; then
      agents_existed=1
      cp -p "$agents_file" "$agents_backup"
      say "  • backed up existing file → AGENTS.md.bak-$stamp"
    fi
    # cp follows an existing destination symlink, preserving dotfiles-managed AGENTS.md links.
    if ! cp "$merged" "$agents_file"; then
      agents_changed=1
      restore_live
      say "  ✗ AGENTS.md install failed; restored prior live artifacts"
      exit 1
    fi
    agents_changed=1
    say "  → installed generated Directions guidance"
  fi
fi

say ""
say "Verification:"
if [ "$dry_run" = 1 ]; then
  say "  [dry-run] skipped live-file verification"
else
  verify_error=""
  if [ ! -L "$skill_dest" ] || [ ! -f "$skill_dest/SKILL.md" ]; then
    verify_error="skill link verification failed"
  elif [ "$skip_agents" = 0 ] && ! grep -q 'DIRECTIONS-CODEX:START' "$agents_file"; then
    verify_error="AGENTS.md verification failed"
  fi
  if [ -n "$verify_error" ]; then
    restore_live
    say "  ✗ $verify_error; restored prior live artifacts"
    exit 1
  fi
  say "  ✓ skill and global guidance installed"
fi
say "Start a new Codex session so global guidance and skill discovery are rebuilt."
