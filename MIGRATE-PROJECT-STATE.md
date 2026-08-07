# Migrating an old-shape PROJECT_STATE to the lean digest

Shared procedure invoked by `/status` and `/log` when they detect an old-shape
`PROJECT_STATE.md`. **Opt-in. Nothing breaks if skipped** — the new `/status` reads the old shape
fine, just heavier. Migrate a project the next time you're already working in it.

## Detect "old shape"
A project's `PROJECT_STATE.md` is old-shape if **any** of:
- it has a `## Active Decisions` section, **or**
- it is missing **either** a `## Now` **or** a `## Recent` section (not just both — a file with a
  `Recent` but no `Now` is not the lean shape, and a `Now`-only budget can never catch it), **or**
- its `## Now` exceeds ~30 lines, **or**
- the whole file exceeds **~250 lines** — a loose backstop for bloat *outside* `Now`/`Recent`, which
  the `Now` budget cannot see. Set far above any healthy digest so it cannot fire on correct output:
  the largest clearly-healthy file in the 87-file audit was 147 lines with a 23-line `Now`.

**Measure `Now`, not the file.** `Infrastructure`, `Backlog`, `Risks` and `Detail` are legitimately
long and hold content that exists nowhere else — a healthy digest can run past 100 lines. The old
raw-line-count trigger (~70) fired on correctly-migrated files, so it was ignored. Audited across 87
real `PROJECT_STATE.md` files: 11 healthy digests were being nagged permanently by it.

**A bloated `## Recent` is NOT a reason to migrate.** If `Recent` holds more than ~5 entries, prune it
in `/log` step 2 and stop there — the same audit found 7 files of 41–66 lines whose only fault was
6–12 `Recent` entries, and restructuring those would be a remedy that does not match the disease.

## ⚠️ This is recurring, not one-time
Expect to run this again. A project that needed it twice has a **`Now` that is not being pruned at
close-out**, which is the actual defect — `/log` step 2's "completed work is transient" rule is the
fix, and this migration only clears the backlog it left. Measured in one project: 86 lines after the
first migration, 241 lines 46 days later, ~90% of the growth retired-wave bullets that were prepended
to `Now` and never removed. If you are migrating a second time, re-read `/log` step 2 before assuming
the file is just verbose.

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
- [ ] `## Now` is ≤ ~30 lines and holds **no** completed-wave/phase bullets; `## Recent` is ≤ 5
      entries. (Not "the file got shorter" — a digest with a long `Infrastructure` section is fine.)
- [ ] `decisions.md` grew, or there were genuinely no orphans.

Then commit `chore(directions): slim PROJECT_STATE to lean digest`, merge to `main` locally
(solo dev — no PR).
