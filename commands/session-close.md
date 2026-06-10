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

**Old-shape check first:** if this `PROJECT_STATE.md` is still old-shape — has a `## Active Decisions`
section, or lacks both `## Now` and `## Recent`, or exceeds ~70 lines — offer to migrate it now:
*"PROJECT_STATE is the old verbose shape — migrate to the lean digest while we're here?"* If yes,
follow `<directions-master>/MIGRATE-PROJECT-STATE.md` (it preserves decisions into `decisions.md`
first, then slims the file), then continue Step 4 against the new shape.

`PROJECT_STATE.md` is a **lean digest** (Now / Recent / index). Don't paste detail into it — detail
lives in `decisions.md` and `sessions/_index.md`. Update only these:

| Field | Action |
|---|---|
| `Last updated:` | Bump to today's date. Always. |
| `Now → Focus` | Still describe what we're actually working on? If the session shifted focus, propose new one-sentence text. |
| `Now → Next` / `Blockers` | If the session changed what's next or surfaced/cleared a blocker, update the one-liner. |
| `Recent` list | Prepend a **one-line, plain-language** entry for this session (no commit SHAs, no jargon). Keep the list to ~5 — drop the oldest. The full version is the `sessions/_index.md` row. |

If a real architectural decision was made (Step 3), it goes in `decisions.md` — **not** expanded into PROJECT_STATE.

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

## Step 6 — Offer to commit AND push (confirmed, not silent)

After Steps 1–5, summarise, then **offer to commit and push** — don't just print a message and stop.

> Session closed. Changes:
> - `docs/sessions/<file>` — N lines added/modified
> - `docs/decisions.md` — N decisions added
> - `docs/PROJECT_STATE.md` — timestamp + N fields updated
> - `docs/sessions/_index.md` — N rows added/modified
>
> Commit + push now? (recommended before switching Macs)
> ```
> session: close <date> + sync state
> ```

If the user says yes:

1. **Check for in-flight work that shouldn't ride along.** Run `git status`. If there are unrelated
   modified files (code mid-change, an experiment), name them and ask whether to stage only the
   docs/session files or everything. Default to staging only what this close touched.
2. `git add` the chosen files, `git commit` with the message above.
3. **Push** — `git push`. In a multi-Mac repo an *unpushed* commit is as invisible to the other Mac
   as an uncommitted file; closing the session without pushing leaves the duplicate-work window open
   (see `37_multi-mac-discipline.md`). If the branch isn't `main`/`master`, push the feature branch;
   never push directly to `main` if the user's git rules forbid it — merge locally first, then push.
4. If `git push` is rejected ("fetch first"), STOP — origin moved under you (another Mac). Do **not**
   force. Run the Rule 1 reconcile from `37_multi-mac-discipline.md`.

**Still confirmed, never silent.** Ask before committing; ask before pushing if anything unrelated is
staged. The change from older guidance is that the *offer now includes the push* — because stopping at
a local commit defeats the whole point of closing cleanly when you work across machines.

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
