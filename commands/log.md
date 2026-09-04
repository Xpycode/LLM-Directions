# Session Log

Wrap up the session: write the log, sync state, extract anything reusable, and — when you're
clearing or switching Macs — commit + push. **`/log` is the single end-of-session command.** It
replaces the old `/session-close`, `/depart`, `/handoff`, `/check-index`, `/phase`, `/compound`,
and `/blockers`: run it once at the end and it does all of that, **inferring from context instead
of interrogating you**.

> Measured: 69/69 `/log` invocations were session-enders, and the "what were we working on?"
> question was inferred — never asked — every time. Treat it as a session close, not a mid-session note.

## Golden rule — infer and report, don't interrogate

Run every step below automatically and **report the result**. Do **not** ask permission per step.
Ask **at most one** question, and only when the session had no coherent thread (several unrelated
tasks) *and* the arg gives no framing (e.g. "Frame the log around X, or list them separately?").
This is the deliberate reversal of the old checklist-style close — silent defaults, not prompts.

## Wrap-up mode — read the argument FIRST

The argument is the **wrap-up mode**, not a goal. Detect it; don't ask which mode when the arg says:

| Arg contains… | Mode | The log MUST… |
|---|---|---|
| "clear", "next session", "for next time" | **pre-clear** | end with a **Resume block**: uncommitted work, exact next pickup point, deferred-item counts, recommended model fit, and any half-done edit. The next session starts cold. (Replaces the old `/handoff` doc — no separate handoff file.) |
| "switch Macs", "handoff", "other Mac", "depart" | **Mac-handoff** | run **§8 Leaving a Mac** — commit + push, stamped with this Mac; verify tree clean / pushed before declaring done. |
| (none, "log it", "just log") | **plain** | a normal log; no resume/sync ceremony, no commit. |

Default to **plain** — don't ask. Detect path mode once: `docs/sessions/` exists → `docs/` paths;
else `./sessions/` (master repo).

## 1 · Write the log

Create today's `sessions/YYYY-MM-DD.md` (actual date). If it exists, **append/refresh** rather than
duplicating — and if it's already comprehensive, say so instead of redoing it.

```markdown
# Session: [DATE]
## Goal
[INFER from the work just done — the log is written after the fact, the goal is already in context.
Do NOT ask (see Golden rule).]
## Progress
- [What actually happened, plain language, file/commit refs welcome]
## Decisions
- [Any architectural/design choices — significant ones also go to decisions.md, see §4]
## Next
- [What to do next time]
## Resume        ← pre-clear mode only: uncommitted work + exact pickup point + deferred counts + model fit
## Sync          ← Mac-handoff mode only: unpushed commits, branch, what the other Mac pulls
```

## 2 · Sync PROJECT_STATE.md  (always)

A stale snapshot is the failure case, especially before a clear/switch. `PROJECT_STATE.md` is a
**lean digest** (Now / Recent / index) — don't paste detail into it; detail lives in `decisions.md`
and `sessions/_index.md`. Update only what the session evidence supports:

- **`Last updated:`** — bump to today. Always.
- **Now → Focus / Next** — if the session shifted them, propose new one-liners.
- **Blockers** — if one surfaced or cleared, update the one-liner. For a real blocker worth detail,
  use: `**What:** … · **Tried:** … · **Unblock:** …` (mark `✅ RESOLVED` + `**Resolution:**` when cleared).
- **Recent** — prepend a **one-line, plain-language** entry (no SHAs, no jargon). Keep ~5; drop the oldest.
- **Now → completed work is transient.** `## Now` is **present tense only**. When a wave or phase
  closes, **replace** its bullet with the next one — never prepend and leave the old one behind. A
  `**Wave X — DONE**` bullet belongs in `Recent` as one line and in `decisions.md` in full; if it is
  still sitting in `Now` next session, it is rot. This is the section that actually grows: `Recent`
  has a cap and holds, everything uncapped climbs. Measured in one project — 86 → 241 lines over 46
  days, roughly 90% of it retired-wave bullets, across *two* migrations that each landed above target
  and were each undone within weeks.

Report "Synced PROJECT_STATE." — don't ask "should I sync?".

*Old-shape check:* if this file has a `## Active Decisions` section, or is **missing either `## Now`
or `## Recent`**, or its **`## Now` exceeds ~30 lines**, or the whole file exceeds **~250 lines**
(a loose backstop for bloat outside those sections), offer once to migrate it via
`<directions-master>/MIGRATE-PROJECT-STATE.md`.

**Measure `Now`, not the file.** `Infrastructure`, `Backlog`, `Risks` and `Detail` are legitimately
long and are not rot, so raw file length is the wrong signal: it fires on a correctly-migrated file,
and a check that fires on correct output gets ignored — which is how the 46-day regrowth above went
unnoticed. (Audited across 87 real `PROJECT_STATE.md` files: 11 healthy digests, `Now` ≤ 26 and
`Recent` ≤ 5, were being nagged permanently by the old ~70-line trigger.)

**An over-long `Recent` is a prune, not a migration.** If `Recent` holds more than ~5 entries, just
drop the oldest here in step 2 — that is this step's own job, and it is what went un-run. Do **not**
escalate it to a migration offer: the same audit found 7 files of 41–66 lines whose only fault was
6–12 `Recent` entries, and proposing a full restructure for those is a remedy that does not match the
disease. Only structural rot — retired waves piling up in `Now` — warrants the migration.

## 3 · Sync the session index

Add a row for this session to `sessions/_index.md`: read only the table header + first data row to
confirm the column format — **never the whole file**. Insert below the header; Focus = the session
Goal, Outcome = Progress + Next (cap at ~300 chars, condense — don't ask). If the live file already
holds ~20 rows, move its oldest into `sessions/_index-archive.md` (create with a one-line header if
absent) to keep it capped.

Then run the drift check (`scripts/sync-session-index.sh`, or `docs/scripts/…` in a consumer project):
- **`✓ in sync`** — done. **`MISSING`** (older logs) — surface: "index missing N prior entries —
  backfill, or just today's?". **`ORPHAN`** (row → no file) — flag, never auto-remove (typo / moved /
  work-in-flight). Don't `--fix` today's row — a hand-written row beats the auto-stub.

## 4 · Extract anything reusable  (silent-surface — only if something emerged)

Route learnings to their **one home**; skip silently if nothing emerged (don't ask the open-ended
"did this produce a pattern?"):

| Emerged this session | Home |
|---|---|
| Reusable UI/window/export/lifecycle **pattern** ("finally got X working", "copied from [project]") | offer `/cookbook add` |
| A **term** the user learned | `44_my-glossary.md` (or `/learned`) |
| A real **architectural decision** | `decisions.md` — full entry (context/alternatives/rationale/consequences). Don't verbatim-copy the one-line session bullet; an ADR needs standalone context. |
| A **gotcha** | the relevant shared guidance doc; use `AGENTS.md` only for Codex-specific operating constraints |
| A **workflow improvement** to Directions itself | this master repo |

Report "Extracted: …" only if you routed something.

Also reconcile issues captured during the session: confirmed non-blockers belong in `TASKS.md`
Backlog; unconfirmed observations belong in its Inbox; current blockers belong in the active plan.
Do not leave an actionable deferred issue only in prose. In pre-clear/Mac-handoff mode, report the
deferred counts in the Resume/next-session summary so the user knows they were not forgotten.

## 5 · Archive completed tasks  (skip if no `TASKS.md` or nothing checked)

Move `- [x]` items from `TASKS.md` Current Sprint → `tasks-archive.md` Completed (top), dated
`(YYYY-MM-DD)`; bump "Total archived" + "Last updated"; remove them from Current Sprint. Recompute the
PROJECT_STATE progress bar: `(archived + current_checked) / (backlog + current + archived) × 100`.
Report "Archived N tasks. Progress: X%" only if something moved.

## 6 · Change phase  (only if the session actually shifted it)

If the work moved the project between phases (discovery → planning → implementation → polish →
shipping), update the **Phase:** line in PROJECT_STATE and add `<!-- Phase changed: YYYY-MM-DD -->`.
Re-check the Readiness table (Features/UI/Testing/Docs/Distribution). For a move to **polish/shipping**,
require Features to be at least 🔶, and remind: "run `/check ship` before release." Skip this section
entirely if the phase didn't change — don't prompt for it.

## 7 · Retire stray test builds  (app projects only — skip if none were launched)

If this session **built and launched** a local copy of the project's app (Xcode `DerivedData`, a
`.build` product, a staged bundle), **quit it now** — a test build left running keeps answering the
installed app's global hotkeys and sharing its data store, but is signed with a *different* identity,
so macOS treats it as a different app and its TCC grants (Accessibility, Screen Recording, Automation)
silently do not apply. The result looks like the shipped app misbehaving, not like a stale process.

```bash
# Match the EXECUTABLE path (ps comm), never the command line.
ps -Ao pid,comm | grep -E "(DerivedData|\.build)/.*\.app/Contents/MacOS/"
```

⚠️ **Do not use `ps -Ao pid,command` here.** It matches any process whose *command line* merely
mentions those paths — including the grep itself and the shell wrapper running it — so it reports a
stray build on a clean machine. That false positive fired the first time this step ran (2026-08-06);
`comm` is the executable path, so wrappers can't match it. And since this check normally passes,
**prove it can fail** before trusting a clean result — pipe a fake DerivedData path through the same
grep and confirm it fires ([[negative-checks-pass-vacuously]]).

Kill any match, then relaunch the installed one (`open -a /Applications/AppName.app`) if the user
uses it daily. Report "Quit N test build(s); installed app relaunched" — or say nothing if there
were none. Matches from **other** projects: name them, don't kill them silently.

*Why this step exists:* an Aloft Debug build outlived its session by nine days, kept the
Command+Shift+V hotkey, and broke auto-paste system-wide while reporting every paste as successful
(2026-08-06). Nothing in git or the working tree can show you this — only `ps` can.

## 8 · Leaving a Mac  (Mac-handoff mode, or pre-clear when you want it committed)

Only in Mac-handoff mode (or when the user asks to commit). Plain mode does **not** commit.

```bash
MAC=$(cat ~/.config/directions/this-mac 2>/dev/null \
  || cat ~/.claude/this-mac 2>/dev/null \
  || scutil --get LocalHostName 2>/dev/null \
  || hostname -s)
```

1. **Stage only what this session touched.** If `git status` shows unrelated in-flight code, name it
   and ask whether to include it (default: only the docs/session files).
2. **Commit, stamped with this Mac** — a `Handoff-from:` trailer lives in git history (immutable,
   conflict-free); never write "pushed at HH:MM on MacN" into a tracked `.md` (that invites the
   two-Macs-edit-the-same-line conflict). `/status arrive` reads the trailer back.
   ```bash
   git commit -m "session: $(date +%F) + sync state

   Handoff-from: $MAC"
   ```
   ⚠️ **Keep every trailer in ONE final paragraph — no blank line between them.** Git parses only
   the *last* paragraph as trailers, so a `Co-Authored-By:` (or any second trailer) separated by a
   blank line silently demotes `Handoff-from:` to ordinary body text. It still *looks* right in
   `git log`, but `%(trailers:key=Handoff-from,valueonly)` — what `/status arrive` actually reads —
   returns empty, and the other Mac falls back to author/date with no Mac name. Correct shape:
   ```
   session: 2026-08-20 + sync state

   <body…>

   Handoff-from: M4-Pro
   Co-Authored-By: …
   ```
   Verify before moving on — a stamp that doesn't parse is worse than none, because it reads as
   present:
   ```bash
   git log -1 --format='%(trailers:key=Handoff-from,valueonly)'   # must print the Mac, not empty
   ```
   *(Recorded 2026-08-20, after `ed7eaec` shipped with exactly this defect — unfixable without
   force-pushing already-pushed history, so it stands as the example.)*
3. **Push** — an *unpushed* commit is as invisible to the other Mac as an uncommitted file.
   - **No remote** → say so: the commit stays on this Mac; offer to add a remote.
   - **Rejected ("fetch first")** → origin moved (other Mac pushed). **STOP, don't force.** Reconcile
     via `37_multi-mac-discipline.md` Rule 1, then push.
   - **Feature branch + git rules forbid pushing `main`** → push the branch; don't auto-merge.
   - **Nothing to commit** → still push any unpushed local commits.
4. **Confirm honestly.** On full success:
   `✓ <Project> wrapped on <MAC> · log + state synced · committed · pushed — safe to switch; run /status arrive on the other Mac after Syncthing settles.`
   If something didn't happen (no remote, nothing to push), **say that** — never claim "pushed" if it wasn't.

## 9 · Next-session model-fit reminder  (pre-clear or Mac-handoff only)

Read the recorded next action and apply `60_model-selection.md` → **User-Facing Model-Fit Notice**.
Add one line to the Resume/next-session block:

```text
Model fit: deep capability + high reasoning — next action is a concurrency diagnosis.
```

If the host exposes the active setting reliably, say whether to stay or switch and name the host's
control. Otherwise say that the current setting is not reliably visible. This is a single boundary
reminder, not a gate and not a recurring prompt. The actual next action wins over a mechanical
phase mapping.

<!-- CLAUDE-ONLY:START — Codex skips this model-marker integration -->

### Claude Code phase-marker integration

Switching models re-reads the whole context (a cache miss); doing it right after `/clear` at an empty
context is nearly free, mid-session at full context is the expensive moment. So the ritual is
**clear → switch → start**, and this reminder makes the next session begin on the right tier:

```bash
SID=$(ls -t "$HOME"/.claude/.current-model-* 2>/dev/null | head -1 | sed "s:.*/.current-model-::")
PHASE=$(cat "$HOME/.claude/.session-phase-$SID" 2>/dev/null)
echo "this session phase: ${PHASE:-unknown}"
rm -f "$HOME/.claude/.session-phase-$SID" 2>/dev/null   # consume it — fresh phase set next session
```

When it agrees with the actual next action, use the phase marker to add the exact Claude Code model
command to the shared reminder (do not emit a second notice):

| This session was | Show |
|---|---|
| `spec` | 🔴 **NEXT: PLANNING → `/model opus`** |
| `plan` | 🔴 **NEXT: EXECUTING → `/model sonnet`** |
| `execute` | 🔴 **More execution? STAY ON SONNET. Planning next? → `/model opus`** |
| unknown / empty | skip — no phase recorded |

Append: **"Clear FIRST, then `/model <X>`, then start."** This is a reminder, not an action.
<!-- CLAUDE-ONLY:END -->

## What `/log` intentionally does NOT do

- **Clear or exit** the session — it prepares the log; you run `/clear` / switch Macs.
- **Force-push or auto-resolve a diverged branch** — it stops and points at the reconcile rule.
- **Write the `## Next` / Resume content for you** past what the session evidence supports — the
  forward pointer is a judgment call; infer what you can, flag what you can't.

Source: `scripts/sync-session-index.sh`, `decisions.md` template, `37_multi-mac-discipline.md`,
audit findings 2026-05-13.
