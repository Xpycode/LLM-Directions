#!/usr/bin/env bash
# sync-session-index.sh — verify session indexes match files on disk.
#
# Usage:
#   sync-session-index.sh                    # check the project at cwd (read-only)
#   sync-session-index.sh path/to/sessions   # check a specific sessions dir
#   sync-session-index.sh --fix              # add placeholder rows for missing entries
#
# Exit codes:
#   0  — index is in sync
#   1  — drift detected (missing or orphan entries)
#   2  — error (no sessions dir, no _index.md, etc.)
#   3  — --fix cannot locate a table separator; index left unchanged
#
# Behavior:
#   - Coverage is the union of _index.md and optional _index-archive.md.
#   - "Missing" = file on disk has no row in either index → can be auto-added to _index.md with --fix.
#   - "Orphan"  = row in either index points to a file that doesn't exist → never auto-removed
#                 (could be a typo, a moved file, or work-in-progress; investigate manually).

set -euo pipefail

fix_mode=false
sessions_dir=""

for arg in "$@"; do
  case "$arg" in
    --fix) fix_mode=true ;;
    -h|--help)
      sed -n '2,/^$/p' "$0" | sed 's/^# \{0,1\}//'
      exit 0
      ;;
    *)
      if [ -d "$arg" ]; then
        sessions_dir="$arg"
      fi
      ;;
  esac
done

# Auto-detect sessions dir if not passed
if [ -z "$sessions_dir" ]; then
  if [ -d "docs/sessions" ]; then
    sessions_dir="docs/sessions"
  elif [ -d "sessions" ]; then
    sessions_dir="sessions"
  else
    echo "error: no docs/sessions/ or sessions/ at cwd; pass a path as arg" >&2
    exit 2
  fi
fi

index="$sessions_dir/_index.md"
if [ ! -f "$index" ]; then
  echo "error: $index does not exist" >&2
  exit 2
fi

index_files=("$index")
archive_index="$sessions_dir/_index-archive.md"
if [ -f "$archive_index" ]; then
  index_files+=("$archive_index")
fi

# --- collect files on disk (basename without .md, sorted) ---
# Match anything starting with a 4-digit year. Excludes _index.md.
# NOTE: must handle paths with spaces (e.g. "Group Alarms") — avoid `xargs basename`
# which whitespace-splits the input. `find -execdir` keeps each path intact.
files=$(
  find "$sessions_dir" -maxdepth 1 -type f -name "20*.md" -execdir basename {} .md \; 2>/dev/null \
    | sort \
    || true
)

# --- collect entries from the live + optional archive indexes ---
# Two formats are common across consumer projects:
#   (a) markdown link form:  `[2026-05-13](2026-05-13.md)` or `[2026-05-13](./2026-05-13.md)`
#                            (the `./` prefix is canonical in some consumers, e.g. Group Alarms)
#   (b) bare-date row form without a log link: `| 2026-05-13 | Focus | Outcome |`
# We accept either. (`grep -oE` exits 1 on no matches → guard with `|| true`.)
entries=$(
  {
    grep -h -oE '\((\./)?20[0-9]{2}-[0-9]{2}-[0-9]{2}[A-Za-z0-9_.-]*\.md\)' "${index_files[@]}" \
      | sed -E 's|^\((\./)?||;s|\.md\)$||' \
      || true
    # A linked row's target is authoritative. Its display date may carry a
    # section suffix such as "(b)" or "-b" while several sections share one
    # daily log, so do not also interpret that display value as a filename.
    grep -h -E '^\| *20[0-9]{2}-[0-9]{2}-[0-9]{2}' "${index_files[@]}" \
      | grep -vE '\((\./)?20[0-9]{2}-[0-9]{2}-[0-9]{2}[A-Za-z0-9_.-]*\.md\)' \
      | grep -oE '^\| *20[0-9]{2}-[0-9]{2}-[0-9]{2}[A-Za-z0-9_.-]*' \
      | sed 's/^| *//;s/ *$//' \
      || true
  } | sort -u | grep -v '^$' || true
)

# --- diffs ---
missing_entries=$(comm -23 <(printf '%s\n' "$files") <(printf '%s\n' "$entries") | grep -v '^$' || true)
orphan_entries=$(comm -13 <(printf '%s\n' "$files") <(printf '%s\n' "$entries") | grep -v '^$' || true)

n_files=$(printf '%s\n' "$files" | grep -c . || true)
n_entries=$(printf '%s\n' "$entries" | grep -c . || true)
n_missing=$(printf '%s\n' "$missing_entries" | grep -c . || true)
n_orphan=$(printf '%s\n' "$orphan_entries" | grep -c . || true)

# --- report ---
echo "== sync-session-index =="
echo "  dir:       $sessions_dir"
echo "  on disk:   $n_files"
echo "  in index:  $n_entries"
if [ -f "$archive_index" ]; then
  echo "  coverage:  _index.md + _index-archive.md"
fi

if [ "$n_missing" -gt 0 ]; then
  echo
  echo "MISSING from session indexes (file exists, no row):"
  printf '%s\n' "$missing_entries" | sed 's/^/  + /'
fi

if [ "$n_orphan" -gt 0 ]; then
  echo
  echo "ORPHAN entries in session indexes (row exists, file missing):"
  printf '%s\n' "$orphan_entries" | sed 's/^/  - /'
  echo "  (targets unavailable locally; may be on another Mac; never auto-removed)"
fi

# --- apply --fix ---
if $fix_mode && [ "$n_missing" -gt 0 ]; then
  echo
  echo "applying --fix: adding $n_missing placeholder row(s)..."

  # Find the table-separator line `|---|...`
  header_line=$(grep -nE '^\|[ -]*\|' "$index" | head -1 | cut -d: -f1 || true)
  if [ -z "$header_line" ]; then
    echo "error: cannot find table separator line in $index — fix manually" >&2
    exit 3
  fi

  # Build new rows newest-first (so they sit at top of reverse-chronological table)
  new_rows=$(
    printf '%s\n' "$missing_entries" | sort -r | while read -r entry; do
      [ -z "$entry" ] && continue
      date_part=$(printf '%s' "$entry" | grep -oE '^20[0-9]{2}-[0-9]{2}-[0-9]{2}')
      printf '| %s | (auto-added — fill in) | (unknown — see log) | [log](%s.md) |\n' "$date_part" "$entry"
    done
  )

  # Splice: keep lines 1..header_line, insert new_rows, keep the rest
  tmp=$(mktemp)
  {
    head -n "$header_line" "$index"
    printf '%s\n' "$new_rows"
    tail -n "+$((header_line + 1))" "$index"
  } > "$tmp"
  mv "$tmp" "$index"

  echo "  done — review and edit the new rows in $index"
fi

# --- exit code ---
if [ "$n_missing" -gt 0 ] || [ "$n_orphan" -gt 0 ]; then
  if $fix_mode && [ "$n_missing" -gt 0 ] && [ "$n_orphan" -eq 0 ]; then
    exit 0
  fi
  exit 1
fi

echo
echo "✓ index in sync"
exit 0
