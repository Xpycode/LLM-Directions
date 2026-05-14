# Close Session

End-of-session hygiene. Run this BEFORE walking away from a session, especially if work will resume later (today, tomorrow, or in two weeks). Prevents the four drift patterns surfaced by the 2026-05-13 audit: missing "Next Session" handoffs, stale PROJECT_STATE, decisions buried in session prose, and `_index.md` falling out of sync.

This is a checklist Claude runs WITH the user, not a silent automation. Each step prompts before changing files.

## Step 1 — Identify the active session log

Pick the file to close:

1. Look in `docs/sessions/` for files matching today's date: `YYYY-MM-DD*.md`.
2. If one exists, use it. If several, pick the latest (alphabetical suffix `a`, `b`, `c`, or a descriptor like `-night`, `-build-1`).
3. If none exists for today, ask the user: "There's no session log for today — did we work on something? Should I create one with `/log`, or are we closing the most recent log (`<filename>`)?"

Report the file path being closed.

## Step 2 — Verify required sections

Open the log and confirm these four sections are present and non-empty:

| Section | Required content |
|---|---|
| `## Goal` | One sentence on what this session was trying to accomplish. |
| `## Progress` (or `### Completed`) | What got done. Bullet list, file/PR/commit refs welcome. |
| `## Decisions Made` (or `### Decisions Made`) | Any architectural choices. May be empty — but the header should exist as a prompt. |
| `## Next Session` | Forward pointer. May say "TBD" or "blocked on X" or "continue Y" — but it must exist. |

For any missing section, **insert a stub at the right position** (don't auto-fill content):

```markdown
## Next Session
- TBD — leaving session here, pick up next time
```

Then prompt the user: "I added a stub `## Next Session` — what should it actually say?" Edit in their answer before continuing.

**Why this matters:** The audit found 46/306 recent logs (15%) lacked a Next Session pointer — heavily concentrated in interrupted or build-step sessions. The next person opening the project has to reverse-engineer intent from the Progress section. One sentence prevents that.

## Step 3 — Extract decisions to `decisions.md`

Scan the session log's `## Decisions Made` bullets. For each one:

1. Read `docs/decisions.md`. Check if a corresponding entry exists.
2. If not, ask the user: "We decided X in this session. Should I add it to `decisions.md`?"
3. If yes, ask:
   - **Context** (what prompted it)
   - **Alternatives** (what else was considered)
   - **Rationale** (why this won)
   - **Consequences** (what it locks in)
4. Append to `decisions.md` using the template at the top of that file.

**Why this matters:** Audit found decisions like LUCESUMBRARUM's "re-pull-and-migrate recipe", YTdl's `Window` vs `WindowGroup` swap, and Group Alarms' model-invariant fixes all stayed buried in session prose. Three months later nobody can find them.

Don't auto-copy the session bullet verbatim — a one-line "decided X" in a session log is a summary, not an architectural-decision record. The `decisions.md` entry needs the context to be useful in isolation.

## Step 4 — Sync `PROJECT_STATE.md`

Open `docs/PROJECT_STATE.md`. Check three things:

| Field | Action |
|---|---|
| `Last updated:` | Bump to today's date. Always. |
| `Focus:` | Does it still describe what we're actually working on? If the session shifted focus, propose new text. |
| `Active Decisions` list | If a new decision was added in Step 3, prepend it (one-liner referencing `decisions.md`). Keep the list to 3–5 entries — drop the oldest to make room. |

Also check **Status** and **Blockers** sections — if anything changed during the session, update them.

Don't blindly bump everything; only change fields the session evidence supports.

**Why this matters:** Audit found PROJECT_STATE.md timestamps lagging session activity by days or weeks (Penumbra was 3 weeks behind). Future-you grepping for "what's the current state?" gets stale answers.

## Step 5 — Sync `_index.md`

Run the index-drift check:

```bash
docs/scripts/sync-session-index.sh
```

(Or `scripts/sync-session-index.sh` if you're in the master Directions repo.)

Interpret the output:

- **`✓ index in sync`** — done, move on.
- **`MISSING from _index.md`** including today's log — add a row at the top of the table in `_index.md`. Use the session's Goal as the Focus column and the Progress + Next Session as the Outcome column. Don't run `--fix` for this — the auto-stubs aren't as good as a hand-crafted row that summarises the work.
- **`MISSING`** including older logs — surface them to the user: "Your index is missing N entries from prior sessions. Want me to backfill them, or just today's?"
- **`ORPHAN entries`** — flag and ask. Could be a typo, a moved file, or a deleted log. Never auto-remove.

## Step 6 — Suggest a commit (don't run it)

After Steps 1–5, summarise:

> Session closed. Changes:
> - `docs/sessions/<file>` — N lines added/modified
> - `docs/decisions.md` — N decisions added
> - `docs/PROJECT_STATE.md` — timestamp + N fields updated
> - `docs/sessions/_index.md` — N rows added/modified
>
> Suggested commit message:
> ```
> session: close <date> + sync state
> ```
>
> Run `git add` + `git commit` when ready.

**Never auto-commit.** The user may have other in-flight work that shouldn't ride along.

## When to invoke

- At the end of a working session, before closing the terminal / IDE.
- Before walking away for >2 hours mid-session.
- Before switching projects (closing the current one cleanly so future-you can resume).
- If `/status` reports drift between recent log and PROJECT_STATE.

## What this command intentionally does NOT do

- Write the `## Next Session` content for you — that requires human judgment about what's actually next.
- Auto-extract decisions verbatim into `decisions.md` — full ADR-style entries need context the session log doesn't always provide.
- Remove orphan `_index.md` rows — they may represent real work in flight.
- Commit or push — that's a separate, deliberate action.

Source: `scripts/sync-session-index.sh`, `decisions.md` (template), audit findings 2026-05-13.
