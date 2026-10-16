#!/usr/bin/env bash
# gen-directions-index.sh — generate the "Directions Index" table from each doc's TRIGGERS header.
#
# The Index maps topic → master doc so a running project reads the *current* doc on demand
# (see the "Directions Index" section in the tool's global instructions). Generating it from the docs'
# own TRIGGERS: headers means the table can never drift from the docs.
#
# Usage:
#   gen-directions-index.sh                      # print compact inline routing (preview)
#   gen-directions-index.sh --format detailed    # preview the full trigger table
#   gen-directions-index.sh --base '[LOCAL_DIRECTIONS_PATH]'   # use a placeholder base path
#   gen-directions-index.sh --write FILE         # splice the body between the markers in FILE
#   gen-directions-index.sh --write FILE --base '[LOCAL_DIRECTIONS_PATH]'
#
# --write requires FILE to already contain the two marker lines:
#   <!-- DIRECTIONS-INDEX:START ... -->
#   <!-- DIRECTIONS-INDEX:END -->
# Everything between them is replaced; the markers themselves are kept. A single existing
# Directions Index heading can bootstrap absent markers. Invalid/duplicate markers exit 2.
# Requires Python 3 for byte-preserving, validated atomic destination replacement.
# Eligible filenames: NN_lowercase-words.md (ASCII lowercase letters/digits, hyphen-separated).
# Reserved artifact words backup, bak, copy, conflict, orig, old, tmp, temp, swp, swo and
# sync-conflict are excluded, as are LOAD: redirect stubs. Excluded files are never modified.
#
# Each row's "When the task involves…" cell = the first few TRIGGERS keywords (falls back to the
# doc's H1 title when a doc has no TRIGGERS line). Tune MAX_KW below.
#
# Exit codes: 0 ok · 2 validation error (arguments, eligible docs or destination).

set -euo pipefail
export LC_ALL=C

REPO="$(cd "$(dirname "$0")/.." && pwd)"
BASE="$REPO"
MAX_KW=6
FORMAT=inline
SEEN_FORMAT=0
WRITE=""
SEEN_BASE=0
SEEN_WRITE=0
HELP=0
fail() { echo "gen-directions-index.sh: $*" >&2; exit 2; }

while [ $# -gt 0 ]; do
  case "$1" in
    --base|--write|--format)
      [ "$#" -ge 2 ] && [ -n "$2" ] && [[ "$2" != -* ]] || fail "$1 requires a nonempty value"
      [[ "$2" != *$'\n'* && "$2" != *$'\r'* ]] || fail "$1 value must be one line"
      if [ "$1" = --format ]; then
        [ "$SEEN_FORMAT" -eq 0 ] || fail "duplicate --format"
        case "$2" in inline|detailed) FORMAT="$2" ;; *) fail "unknown format: $2" ;; esac
        SEEN_FORMAT=1
      elif [ "$1" = --base ]; then
        [ "$SEEN_BASE" -eq 0 ] || fail "duplicate --base"
        BASE="$2"; SEEN_BASE=1
      else
        [ "$SEEN_WRITE" -eq 0 ] || fail "duplicate --write"
        WRITE="$2"; SEEN_WRITE=1
      fi
      shift 2 ;;
    -h|--help) HELP=1; shift ;;
    *) echo "gen-directions-index.sh: unknown arg '$1'" >&2; exit 2 ;;
  esac
done
[ "$HELP" -eq 0 ] || { sed -n '2,/^set -/p' "$0" | sed '$d'; exit 0; }
[ "$FORMAT" != inline ] || MAX_KW=3

# --- extract a one-line description for a doc -------------------------------------------------
describe() {
  local f="$1" raw kw title out t n i
  # First TRIGGERS-style header line, in any of: "TRIGGERS:", "**Triggers:**", "> Triggers:"
  raw=$(grep -iE -m1 '^[>* ]*triggers?[:* ]' "$f" 2>/dev/null || true)
  if [ -n "$raw" ]; then
    kw=${raw#*:}                                   # drop label up to first colon
    kw=$(printf '%s' "$kw" | sed -E 's/^[* ]+//; s/[* ]+$//')
    local IFS=','
    local arr
    read -r -a arr <<< "$kw"
    n=${#arr[@]}
    out=""
    for ((i=0; i<n && i<MAX_KW; i++)); do
      t=$(printf '%s' "${arr[i]}" | sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//')
      [ -z "$t" ] && continue
      out="$out${out:+, }$t"
    done
    if [ "$FORMAT" = detailed ] && [ "$n" -gt "$MAX_KW" ]; then out="$out …"; fi
    printf '%s' "$out"
  else
    title=$(grep -m1 '^# ' "$f" | sed -E 's/^#+[[:space:]]*//' || true)
    [ -n "$title" ] || title=$(basename "$f" .md)
    printf '%s' "$title"
  fi
}

# --- build the body (intro + table + why) ----------------------------------------------------
build_body() {
  local f desc count=0
  if [ "$FORMAT" = inline ]; then
    printf 'Read relevant master guidance on demand; match the task\047s intent, not incidental quoted keywords. Resolve paths under `%s`; never use copied consumer guides. If routing is ambiguous, inspect the master\047s canonical numbered filenames and TRIGGERS headers before acting. Preserve dirty work; never expose secrets. Before multi-Mac recovery read `37_multi-mac-discipline.md`; before UI changes read `36_ui-changes-protocol.md` and `47_project-ui-conventions.md`; for credentials read `54_security-rules.md`. Current user limits, including no desktop control, prevail.\n' "$BASE"
    printf 'Directions commands, with or without a slash, read `commands/<name>.md` completely. Plan continuation and “next wave” read `commands/execute.md`; preserve no-agent/no-commit and other explicit limits.\n\n'
  else
  printf 'The Directions guidance docs are the **single source of truth** in the master repo. Do **not**\n'
  printf 'rely on a copy inside the current project — copies drift and never receive new house-style. When a\n'
  printf 'task matches a trigger below, **read the master doc on demand** from `%s/`:\n\n' "$BASE"
  printf '| When the task involves… | Read |\n'
  printf '|---|---|\n'
  fi
  for f in "$REPO"/[0-9][0-9]_*.md; do
    [ -f "$f" ] && [ ! -L "$f" ] || continue
    local name="${f##*/}"
    [[ "$name" =~ ^[0-9][0-9]_[a-z0-9]+(-[a-z0-9]+)*\.md$ ]] || continue
    [[ "$name" =~ (^|_|-)(backup|bak|copy|conflict|orig|old|tmp|temp|swp|swo)(-|\.) ]] && continue
    # Skip redirect stubs (consolidated docs that just point elsewhere) — their triggers live on
    # the canonical doc, so they shouldn't be double-listed.
    grep -qiE '^[[:space:]]*LOAD:[[:space:]]*redirect' "$f" && continue
    desc=$(describe "$f")
    desc=${desc//|/\/}                              # never let a pipe break the table
    if [ "$FORMAT" = inline ]; then
      printf -- '- %s: `%s`\n' "$desc" "$(basename "$f")"
    else
      printf '| %s | `%s` |\n' "$desc" "$(basename "$f")"
    fi
    count=$((count+1))
  done
  if [ "$count" -eq 0 ]; then
    echo "gen-directions-index.sh: no numbered docs found in $REPO" >&2
    exit 2
  fi
  [ "$FORMAT" = detailed ] || return 0
  printf '\n**Why read-on-demand:** Universal docs used to be copied into each project at `/setup`, so updates\n'
  printf 'never reached already-set-up projects (N copies silently drift). This Index lets a running project —\n'
  printf 'which reads global + project instructions — pull the *current* master doc instead.\n'
}

BODY=$(build_body)

if [ -z "$WRITE" ]; then
  # preview: full section
  printf '## Directions Index (Read-on-Demand, Not Copied)\n\n'
  printf '<!-- DIRECTIONS-INDEX:START — generated by scripts/gen-directions-index.sh; do not edit by hand -->\n'
  printf '%s\n' "$BODY"
  printf '<!-- DIRECTIONS-INDEX:END -->\n'
  exit 0
fi

# Validate the complete destination in memory before creating any output file. Preserve bytes
# outside the managed body (including CRLF and an absent final newline), and preserve file mode.
python3 - "$WRITE" "$BODY" <<'PY'
import os
from pathlib import Path
import re
import stat
import sys
import tempfile

path = Path(sys.argv[1])
temporary = None
try:
    if path.is_symlink() or not path.is_file():
        raise ValueError("destination must be an existing regular file, not a symlink")
    original = path.read_bytes()
    lines = original.splitlines(keepends=True)
    starts = [i for i, line in enumerate(lines) if b'DIRECTIONS-INDEX:START' in line]
    ends = [i for i, line in enumerate(lines) if b'DIRECTIONS-INDEX:END' in line]
    newline = b'\r\n' if b'\r\n' in original else b'\n'
    body = sys.argv[2].encode() + b'\n'
    body = body.replace(b'\n', newline)
    if starts or ends:
        if len(starts) != 1 or len(ends) != 1 or starts[0] >= ends[0]:
            raise ValueError("expected exactly one ordered START/END marker pair")
        start, end = starts[0], ends[0]
        if not re.fullmatch(rb'<!-- DIRECTIONS-INDEX:START(?: [^\r\n]*)? -->\r?\n', lines[start]):
            raise ValueError("invalid START marker line")
        if not re.fullmatch(rb'<!-- DIRECTIONS-INDEX:END -->\r?\n?', lines[end]):
            raise ValueError("invalid END marker line")
        result = b''.join(lines[:start + 1]) + body + b''.join(lines[end:])
    else:
        headings = [i for i, line in enumerate(lines) if re.match(rb'^## Directions Index(?:[ \r\n]|$)', line)]
        if len(headings) != 1:
            raise ValueError("expected markers or exactly one Directions Index heading")
        start = headings[0]
        end = next((i for i in range(start + 1, len(lines))
                    if lines[i].startswith(b'## ') or lines[i].rstrip(b'\r\n') == b'---'), len(lines))
        prefix = b''.join(lines[:start + 1])
        if not prefix.endswith(b'\n'):
            prefix += newline
        result = (prefix + newline + b'<!-- DIRECTIONS-INDEX:START -->' + newline
                  + body + b'<!-- DIRECTIONS-INDEX:END -->' + newline + b''.join(lines[end:]))
    if result != original:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix='.directions-index-', delete=False) as output:
            temporary = output.name
            output.write(result)
            os.fchmod(output.fileno(), stat.S_IMODE(path.stat().st_mode))
        os.replace(temporary, path)
        temporary = None
except (OSError, ValueError) as error:
    print(f'gen-directions-index.sh: {path}: {error}', file=sys.stderr)
    sys.exit(2)
finally:
    if temporary is not None:
        os.unlink(temporary)
PY
echo "✓ regenerated Directions Index in $WRITE"
