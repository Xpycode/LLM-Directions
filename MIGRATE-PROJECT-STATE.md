# Migrating an old-shape PROJECT_STATE to the lean digest

Shared procedure invoked by `/status` and `/session-close` when they detect an old-shape
`PROJECT_STATE.md`. **Opt-in. Nothing breaks if skipped** — the new `/status` reads the old shape
fine, just heavier. Migrate a project the next time you're already working in it.

## Detect "old shape"
A project's `PROJECT_STATE.md` is old-shape if **any** of:
- it has a `## Active Decisions` section, **or**
- it has **no** `## Now` and no `## Recent` section, **or**
- it exceeds ~70 lines.

## Target shape (the lean digest)
`Identity` · `Now` (phase / focus-one-sentence / blockers / next) · `Recent` (≤5 changes, one
plain-language line each, newest first) · `Progress` (compact funnel + readiness, only if the
project uses them) · `Detail` (index → `decisions.md`, `sessions/_index.md`, `TASKS.md`) ·
optional `Infrastructure` · `Resume`.

## ⚠️ First rule
`PROJECT_STATE.md` is **this project's own content** — never copy the master's file over it. This is
an **in-place transform**, not a replace.

## Steps
1. **Branch** (reversible): `git checkout -b chore/lean-project-state`. (If the project isn't git, just proceed carefully.)
2. **Preserve decisions FIRST — this is the step that prevents data loss.** A project's `decisions.md`
   is often stale, so PROJECT_STATE's `## Active Decisions` list may hold entries that exist nowhere
   else. Compare the two. For every Active-Decisions entry **not** already in `decisions.md`, append it
   **verbatim** to `decisions.md` under a `## Condensed Log (migrated from PROJECT_STATE.md, <today>)`
   section (create it if absent). **Do not fabricate ADR fields** (Context/Options/Rationale) you don't
   have — keep the one-paragraph summary as-is.
3. **Now:** condense the verbose `Focus` paragraph to **one sentence**; pull `Blockers` and the next
   action into `## Now` as one-liners.
4. **Recent:** take the top ~5 rows of the project's `sessions/_index.md`, rewrite each as **one
   plain-language line** (no commit SHAs, no codenames/jargon), newest first.
5. **Progress:** keep the project's real Funnel/Readiness **values** in a compact block; drop the
   redundant ASCII progress-bar, the separate Phase-Progress table, and the Validation-Gates checklist
   if present (their info already lives in the funnel/readiness rows).
6. **Detail:** add `## Detail (read only if needed)` pointing to `decisions.md`, `sessions/_index.md`,
   `TASKS.md`.

## Before committing — safety checklist
- [ ] Every `Active Decisions` entry is now in `decisions.md` (verbatim) **or** was already there.
- [ ] `Focus` / `Blockers` / next-action preserved inside `## Now`.
- [ ] No project-specific content silently dropped (read the full diff).
- [ ] You transformed the project's **own** file — you did not paste the master's.
- [ ] Line count dropped and `decisions.md` grew (or there were genuinely no orphans).

Then commit `chore(directions): slim PROJECT_STATE to lean digest`, merge to `main` locally
(solo dev — no PR).
