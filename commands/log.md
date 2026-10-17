# Session Log

Read this core completely. `/log` is the single session-close workflow: save evidence, state,
index and next action once. It replaces `/session-close`, `/depart`, `/handoff`, `/check-index`,
`/phase`, `/compound` and `/blockers`. Infer from session evidence; do not invent work.

## Resolve canonical procedures

`<master>` means the **absolute Directions master directory**, never the project or installed
command directory. Use the invoking Directions adapter's resolved master, otherwise the `Local
master:` value in the host's managed global instructions. For a repository-only invocation, the
real command source's repository root (the parent of `commands/`) is a candidate only if it contains `commands/log.md` and
`reference/log/`. Validate the chosen root contains both. If unresolved, ask for the master location;
do not guess relative to an installed `~/.claude/commands/log.md` or copy references into projects.
Expand every `<master>/…` path to that absolute root before reading. Load conditional references
only at their actual trigger below, not during initial core loading.

Read each required procedure completely on first use. Within the same task/context, reuse its
retained complete content while its canonical identity and contents are unchanged. Reread if either
changes or retained context is incomplete, compacted or uncertain; fresh agents perform their own
required reads. Reuse does not carry forward authorization: apply current scope and recovery triggers.

## Golden rule — infer and report, don't interrogate

Run applicable steps below within the user's current authorization and **report the result**.
Do **not** ask permission per step. Logging itself does not authorize app or desktop control;
apply §7 before any lifecycle or recovery action. Honor an explicit no-log or immediate-stop
request; preserve no-commit/no-push independently. If control is unavailable, save the obligation
and provide a user-operated handoff while completing the authorized logging work.
Ask **at most one** question, and only when the session had no coherent thread (several unrelated
tasks) *and* the arg gives no framing (e.g. "Frame the log around X, or list them separately?").
This is the deliberate reversal of the old checklist-style close — silent defaults, not prompts.

## Wrap-up mode — read the argument FIRST

The argument is the **wrap-up mode**, not a goal. Detect it; don't ask which mode when the arg says:

| Arg contains… | Mode | The log MUST… |
|---|---|---|
| "clear", "next session", "for next time" | **pre-clear** | end with a **Resume block**: uncommitted work, exact next pickup point, deferred-item counts, recommended model fit, and any half-done edit. The next session starts cold. (Replaces the old `/handoff` doc — no separate handoff file.) |
| "switch Macs", "handoff", "other Mac", "depart" | **Mac-handoff** | use **§7 Mac handoff** within Git authorization; record branch/unpushed work, verify actual sync and recovery limits. |
| (none, "log it", "just log") | **plain** | a normal log; no resume/sync ceremony, no commit. |

Default to **plain** — don't ask. Detect path mode once: `docs/sessions/` exists → `docs/` paths;
else `./sessions/` (master repo).

**Automatic execution close:** when `commands/execute.md` calls this workflow at the end of a run,
use **pre-clear** mode even without an explicit `/log clear` message. Preserve the execution outcome
(whole plan complete, selected scope complete, or blocked/incomplete) and the next pickup point.
Refresh today's existing entry rather than duplicating the execution history. Do not restart
execution from the Resume instructions. Local execution-commit permission does not authorize a push;
apply §7 Mac handoff only within the user's actual Git/handoff authorization. Respect explicit instructions to
leave a fresh app running for user acceptance. This close saves context; it does not clear the session.

Batch known closeout record updates, reusing record content only under the same retained-content
conditions above. Then read back the final changed records and verify their links before
claiming the handoff is ready. Preserve archive/link verification before retiring active records
(§5). Required post-edit source acceptance still runs; later documentation-only edits do not require
repeating still-valid source checks. If a record changes again, verify that changed record again.

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
## Resume        ← pre-clear: uncommitted work + pickup + deferred counts + model fit; plain: update pickup here only if it changed
## Sync          ← Mac-handoff mode only: unpushed commits, branch, what the other Mac pulls
```

## 2 · Sync PROJECT_STATE.md  (always)

A stale snapshot is the failure case, especially before a clear/switch. `PROJECT_STATE.md` is a
**lean digest** (Now / Recent / index) — don't paste detail into it; detail lives in `decisions.md`
and `sessions/_index.md`. Update only what the session evidence supports:

- **`Last updated:`** — bump to today. Always.
- **Now → Focus / Next** — if the session shifted them, propose new one-liners.
- **Now → Execution** — when a plan is active, keep one concise line with its link, current wave/task
  IDs and ready/blocked/awaiting-acceptance status. Preserve unresolved gates. Once the whole plan is
  verified and archived, remove the active execution line and set Next to the actual follow-up.
- **Current handoff** — link one specific current session-log Resume anchor. Superseded blocks
  remain historical evidence; preserve their bytes and outstanding recovery. Refresh this pointer
  when new facts change the pickup. In plain mode, add/update a uniquely identified Resume with
  the changed pickup and obligations; this does not trigger pre-clear-only model/sync ceremony.
- **Blockers** — if one surfaced or cleared, update the one-liner. For a real blocker worth detail,
  use: `**What:** … · **Tried:** … · **Unblock:** …` (mark `✅ RESOLVED` + `**Resolution:**` when cleared).
- **Recent** — prepend a **one-line, plain-language** entry (no SHAs, no jargon). Keep ~5; drop the oldest.
- **Now → completed work is transient.** `## Now` is **present tense only**. When a wave or phase
  closes, **replace** its bullet with the next one — never prepend and leave the old one behind. A
  `**Wave X — DONE**` bullet belongs in `Recent` as one line and in `decisions.md` in full; if it is
  still sitting in `Now` next session, replace it with current work.

Report "Synced PROJECT_STATE." — don't ask "should I sync?".

*Old-shape check:* if this file has a `## Active Decisions` section, or is **missing either `## Now`
or `## Recent`**, or its **`## Now` exceeds ~30 lines**, or the whole file exceeds **~250 lines**
(a loose backstop for bloat outside those sections), offer once to migrate it via
`<master>/MIGRATE-PROJECT-STATE.md`.

**Measure `Now`, not the file.** Long Infrastructure/Backlog/Risks/Detail sections alone are not
rot. An over-long `Recent` needs pruning to ~5 entries in this step, not a migration offer.

## 3 · Sync the session index

Add a row for this session to `sessions/_index.md`: read only the table header + first data row to
confirm the column format — **never the whole file**. Insert below the header; Focus = the session
Goal, Outcome = Progress + Next (cap at ~300 chars, condense — don't ask). If the live file already
holds ~20 rows, move its oldest into `sessions/_index-archive.md` (create with a one-line header if
absent) to keep it capped.

Then run the master's `scripts/sync-session-index.sh` with the actual session directory. If a consumer
invokes an older local checker, record its exact path/version before attributing drift to the master:
- The checker compares files against the **union** of the capped live `_index.md` and optional
  `_index-archive.md`; archived rows must not be reported as missing merely because they left the
  live table.
- **`✓ in sync`** — done. **`MISSING`** (absent from both indexes) — surface: "index missing N prior
  entries — backfill, or just today's?". **`ORPHAN`** (row → no file) — flag, never auto-remove
  (typo / moved / work-in-flight). Don't `--fix` today's row — a hand-written row beats the auto-stub.

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

## 5 · Record progress without mirroring task history

When task status/progress needs updating, read `<master>/reference/task-state.md`. The selected plan
owns task status/evidence; TASKS holds backlog/inbox and an Active plan link. Report completed/total
plan tasks and separate open external gates. Never recompute a combined backlog/archive percentage.
Keep incomplete plans active. On full acceptance, archive plan/evidence and update incoming links
before retiring the active copy. Standalone completed TASKS items may move to tasks-archive, dated;
their archive count is separate. Preserve legacy mirrors until scoped reconciliation validates
their replacement; logging does not authorize a bulk migration or close a manual gate.

## 6 · Change phase  (only if the session actually shifted it)

If the work moved the project between phases (discovery → planning → implementation → polish →
shipping), update the **Phase:** line in PROJECT_STATE and add `<!-- Phase changed: YYYY-MM-DD -->`.
Re-check the Readiness table (Features/UI/Testing/Docs/Distribution). For a move to **polish/shipping**,
require Features to be at least 🔶, and remind: "run `/check ship` before release." Skip this section
entirely if the phase didn't change — don't prompt for it.

## 7 · Conditional app and Mac handoff

Read only the applicable reference, completely, using the master resolution above:

| Actual trigger | Procedure |
|---|---|
| Session produced a runnable build, launched an app, or retains unresolved app/test recovery (including from another session/Mac) | `<master>/reference/log/app-handoff.md` |
| Mac-handoff mode or explicit request for a logging commit | `<master>/reference/log/mac-handoff.md` |

Load both if both triggers apply; app/recovery status must inform the Mac handoff. A project being
an app project alone is not a trigger. No-control or keep-running restrictions remain binding;
record unresolved recovery even in plain mode. A timer, log or switch request cannot authorize
control. Ordinary plain/pre-clear mode does not commit or push. No-commit and no-push always win.

## 8 · Next-session model-fit reminder  (pre-clear or Mac-handoff only)

Read the recorded next action and apply `60_model-selection.md` → **User-Facing Model-Fit Notice**.
Add one line to the Resume/next-session block:

```text
Model fit: deep capability + high reasoning — next action is a concurrency diagnosis.
```

If the host exposes the active setting reliably, say whether to stay or switch and name the host's
control. Otherwise say that the current setting is not reliably visible. This is a single boundary
reminder, not a gate and not a recurring prompt. The actual next action wins over a mechanical
phase mapping.

Only in **Claude Code**, and only in pre-clear/Mac-handoff mode, read
`<master>/reference/log/claude-integration.md` for the optional phase marker. Codex does not load
it or touch Claude markers. Missing/unreliable markers do not block logging or replace the actual
next action.

## What `/log` intentionally does NOT do

- **Clear or exit** the session — it prepares the log; you run `/clear` / switch Macs.
- **Force-push or auto-resolve a diverged branch** — it stops and points at the reconcile rule.
- **Write the `## Next` / Resume content for you** past what the session evidence supports — the
  forward pointer is a judgment call; infer what you can, flag what you can't.

Source: `scripts/sync-session-index.sh`, `decisions.md` template, `37_multi-mac-discipline.md`,
audit findings 2026-05-13.
