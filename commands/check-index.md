# Check Session Index

Verify `docs/sessions/_index.md` matches the session-log files on disk. Flags missing entries (file exists, no index row) and orphan entries (index row, no file).

## What to do

Run the sync script:

```bash
docs/scripts/sync-session-index.sh
```

If you are running this inside the master Directions repo (not a consumer project), the script lives at `scripts/sync-session-index.sh` instead.

## Interpreting output

The script reports three counts and up to two lists:

- **on disk** — number of `2*.md` session files in `docs/sessions/`.
- **in index** — number of entries referenced in `_index.md` (either via markdown link form like `[2026-05-13](2026-05-13.md)` or via bare-date table rows like `| 2026-05-13 |`).
- **MISSING** — session files that exist but have no row in `_index.md`. These are usually safe to auto-add.
- **ORPHAN** — rows in `_index.md` that point at files which no longer exist. These are **never** auto-removed; they may be typos, moved files, or work-in-progress. Investigate manually.

Exit codes: `0` = in sync; `1` = drift; `2` = error (no sessions dir, etc.).

## Optional: auto-fix missing entries

If MISSING rows are present and you want stub rows added, re-run with `--fix`:

```bash
docs/scripts/sync-session-index.sh --fix
```

`--fix`:

- Adds placeholder rows for each missing file: `| YYYY-MM-DD | (auto-added — fill in) | (unknown — see log) | [log](YYYY-MM-DD.md) |`
- Inserts them at the top of the table (reverse-chronological convention).
- Does **not** touch orphan rows.
- After adding, edit each stub to fill in the real Focus and Outcome from reading the corresponding log file.

## When to run

- After a session where you may have created multiple session-log files without updating `_index.md`.
- When `/status` or `/log` complain about index mismatches.
- Periodically — e.g. once a week or before a release — to catch drift before it accumulates.
- After `git pull` if collaborating: someone else may have added sessions but not regenerated the index.

## Background

Index drift is the single most common Directions-hygiene leak in long-running projects. Out of 29 projects audited on 2026-05-13, 16 had some level of drift, with the worst at ±9 entries. The script + slash command pair are the prevent-at-source remedy.

Source: `scripts/sync-session-index.sh`.
