# Project Status

Fast, plain-language status. Keep it short. **No commit SHAs, no internal codenames or jargon** —
say what something *means*, not what it's called.

**Detect mode:**
- `docs/PROJECT_STATE.md` exists → use `docs/` paths (installed project)
- else `./PROJECT_STATE.md` exists → use root paths (master repo)

**Read only what you need (stop early):**
1. `PROJECT_STATE.md` — this is the digest; it's almost always all you need.
2. The **first data row** of `sessions/_index.md` (most recent session). Do **not** read the whole file.
3. `TASKS.md` top section — only if it exists.

Do **not** read full session logs or `tasks-archive.md` unless the user asks to dig deeper.

**Report — aim for ≤8 lines, plain English. Skip any line with nothing to say.**
- **Phase / focus** — one sentence: where we are + what's active.
- **Tasks** — one line `N/M sprint · X% overall`, only if `TASKS.md` exists.
- **Blockers** — name them, or `none`.
- **Last session** — one sentence on what got done, translated out of jargon (no SHAs).
- **Next** — one concrete suggested action.

**Style rules:**
- Translate technobabble. "Moved the sentinel" → "changed which file marks a project as set up."
- No commit hashes, file-path soup, or codenames unless the user used them first.
- Empty/clean field → two words (`Blockers: none`). Don't pad.

## Phase-Specific Reminder

If phase is **polish** or **shipping**, add one line:

> Run `/minimums` to check baseline features before release.
