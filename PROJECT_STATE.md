# Project State

> **Lean digest — target <50 lines.** Current state + a short changelog, then pointers to detail
> files. History lives in `decisions.md` and `sessions/_index.md`, not here.

## Identity
- **Project:** Directions — LLM-assisted development framework (specs, plans, verification)
- **Tags:** meta, framework, documentation, workflow, Claude · **Started:** 2024

## Now
- **Phase:** build / implementation (~80%) — mature framework, ongoing refinement.
- **Focus:** portfolio **"app citizenship" rollout** — shared Feedback/Tip-Jar/About across all macOS
  apps. Audited 30 apps + built `AppCitizenshipKit` (2026-06-14); **first reference app (Conjoyn) now
  migrated to it end-to-end** — package hardened `Xpycode/AppCitizenshipKit` 0.1.0→**0.1.2**, Conjoyn
  consumes the tag and builds green; cookbook **#108** captures the migration + proving-ground pattern.
- **Blockers:** none.
- **Next:** *(framework, in flight)* execute **Wave 2** of `OPTIMIZATION-PLAN.md` — lean cookbook
  router, command consolidation, template trim (biggest token wins); **then** deploy the finalized
  template + commands to `~/.claude/` (that's when `/make-plan` goes live and the `/plan` shadow is
  removed on-machine). *(product)* **roll `AppCitizenshipKit` to the first wave** of apps — DiskVerdict
  next (additive: it has FeedbackKit already, ACK adds Tip Jar + About), then the rest. Use the per-app
  rollout checklist in ACK's README + the `#108` pattern. Separate sweep: fix 19/30 missing/empty
  AppIcons (cookbook #76).
  *(Naming decision baked into ACK: tip-jar framing — "Leave a Tip" / "Tip Jar" — over "Donate"
  (charity) and "Support" (collides with the web help-desk page #105).)*

## Recent
<!-- Last ~5 changes, one line each, plain language. Full detail → sessions/_index.md -->
- **2026-07-02 (b)** — committed #152 (`6689a62`), merged the iOS `optimize-directions-efficiency`
  branch (`c8924be` — brings `OPTIMIZATION-PLAN.md` + read-on-demand setup-seam/hook fixes), then
  **executed Wave 1** of that plan (`0081238`): 10 correctness fixes across ~39 files — broken
  plan→execute pipeline, stale model/CLI facts, wrong Swift snippets, and 8 doc contradictions
  (incl. `/plan`→`/make-plan`, split-pane decision tree, adaptive-theme default). `/update-directions`
  found this Mac runs the **shell** hooks (not the plugin's Python) and the live `~/.claude/CLAUDE.md`
  predates the template → **global migration deferred to post-Wave-2**. All pushed; `main` in sync.
- **2026-07-02 (a)** — sat down on the M1 Max; `/arrive` flagged the alarming "14 behind *and* a dirty
  tree," but it was the familiar Syncthing copy-vs-drift, not a real divergence: no competing local
  commits, so all 14 fast-forward. Hashed every dirty file against origin — **26 of 27 were
  byte-identical duplicates** the other Mac already committed (24 cookbooks #125/#128–#151 + #89 + most
  of the index table), safe to drop. Only **one file was genuinely mine**: cookbook **#152**
  (detecting when a root-only CLI like `fs_usage` fails to get privileges instead of showing a false
  "live"), plus its one index row. Deleted the duplicates, pulled cleanly, re-added the #152 row onto
  origin's newer index — a plain fast-forward, no cherry-pick, because #152's filename doesn't exist on
  origin. Left #152 + its row uncommitted for `/depart`. (Also spotted the other Mac left a #151 file
  with no matching index row.)
- **2026-06-19** — chased down why `/status` had started costing 40–70k tokens (it was ~20k): the leaner `/status` I wrote 9 days ago was committed to the master repo but never *copied* into the live `~/.claude/commands/`, so the old version that reads the entire 37 KB session index + a full log was still running. Deployed the fix (and confirmed the 5×→20× plan upgrade has nothing to do with it — that's rate limits, not cost-per-message). Then made the "you're on the wrong model" warning impossible to miss — a bold white-on-red bar in the statusline — and, following the user's own insight, turned it into a **phase-aware gate**: `/execute` stops you if you're not on Sonnet, `/spec` and `/plan` nudge you to Opus, and `/session-close` now reminds you which model to switch to for the *next* session (switch right after `/clear`, when it's cheapest). Also synced 10 live commands that had fallen behind the master. Pushed `9a83888`.
- **2026-06-17 (b)** — sat down on the M1 Max. `/arrive` flagged `behind 7` and the start-up banner said "byte-identical phantom, safe to `reset --hard`" — but a file-by-file hash check caught it under-counting: three cookbooks (**#118/#119/#120**) were genuine uncommitted local work a prior session never `/depart`-ed, and a blind `--hard` would have lost the index edits. Reconciled with **`reset --mixed`** instead (catches HEAD up but treats the working tree as sacred), then committed + pushed #118–120. Then **rolled the new Directions out** where it actually runs: refreshed the live `~/.claude/commands` copies (the #62-routing `/review` + `/minimums`, plus 4 commands that were missing globally). Surveyed all 44 projects that carry a Directions copy — every one is "behind" — but **decided NOT to mass-sync**: the live cookbook/command lookup reads from the *master repo*, so those per-project copies are vestigial snapshots nothing on the hot path reads. Synced + pushed only the 3 asked for (DiskVerdict, Conjoyn, App-Websites), docs-only so App-Websites' in-flight `apps.json` stayed untouched.
- **2026-06-17 (a)** — sat down on the M4-Pro; `/arrive` caught a parked working tree (cookbook #117 + index, uncommitted from a prior session) and reconciled it cleanly. Then captured a new framework doc, **`62_final-stretch-triage.md`** — discipline for the last 10% of shipping (capture-don't-fix, three honest buckets, define "done for v1" in writing). Wired it into both routing tables (`00_base` + `CLAUDE-GLOBAL-TEMPLATE`) and **into the ship-phase commands**: `/review` now completes the full pass before fixing, triages flagged items into the three buckets, and prompts for a written done-line; `/minimums` buckets gaps so a cosmetic miss isn't treated as a blocker. Synced the live `~/.claude/commands` copies (diffed first — were unmodified). *Note: already-set-up projects need `/update-directions` before the new `docs/62_…` path resolves.*
<!-- older entries → sessions/_index.md -->

## Progress
| Funnel | Status | Gate |
|--------|--------|------|
| Define | ✅ done | Framework documented |
| Plan   | ✅ done | Commands + templates defined |
| Build  | 🔶 active | Iterating on improvements |

| Dimension | Features | UI/Polish | Testing | Docs | Distribution |
|-----------|----------|-----------|---------|------|--------------|
| Status    | ✅ | 🔶 | ⚪ | ✅ | ✅ |

## Detail (read only if needed)
- **Why we decided things** → `decisions.md`
- **Full session history** → `sessions/_index.md`
- **Backlog / what's ahead** → `TASKS.md` (+ `tasks-archive.md`)
- **Global config mirror** → `CLAUDE-GLOBAL-TEMPLATE.md` (the live `~/.claude/CLAUDE.md` is not in this repo)

## Infrastructure
- 261 global skills at `~/.claude/skills/` (update: `npx skills update`)
- XcodePreviews `/preview` at `/Users/sim/ProgrammingProjects/0-DIRECTIONS/XcodePreviews/`

## Resume
<!-- If RESUME.md exists, note it here. Otherwise blank. -->
- **All committed + pushed; `main` in sync, tree clean** (only `.claude/settings.local.json` shows
  modified — per-Mac, intentionally never committed). This session: `6689a62` (#152) → `c8924be`
  (merge optimize branch) → `0081238` (Wave 1).
- **Cold-start pickup:** open `OPTIMIZATION-PLAN.md` → execute **Wave 2** (backpressure targets:
  `PATTERNS-COOKBOOK.md` ≤ 45 KB, `ls commands | wc -l` ≈ 14).
- **Live-vs-repo caveat:** Wave-1 fixes + the `/make-plan` rename are in the **repo**, NOT yet on this
  Mac's `~/.claude/` — `/plan` still hits the old custom command live until the post-Wave-2 redeploy
  (intentional; the global-config migration was deferred to avoid deploying a template Wave 2 rewrites).
- **Still-open small gap:** origin has a `cookbook/151` file but no `#151` index row in
  `PATTERNS-COOKBOOK.md` — add when convenient.
- **Per-Mac wiring (does NOT travel via git):** both Macs are wired — M1 Max erased+restored
  2026-06-13 and `bash hooks/install.sh` was re-run there (symlinks verified); M4-Pro long since done.
  Reminder only if a Mac is restored again: after `git pull`, run `bash hooks/install.sh` once — it
  symlinks the hooks (incl. `session-guard.sh`) + statusline into `~/.claude/` and registers them in
  `settings.json` (idempotent).
- **Carried-over TODO:** cookbook **#92** for the hook↔statusline handshake pattern (#91 is now the
  process-inspection session detector). *(The "tune `model-advisor.sh` keyword lists" TODO is
  superseded — 2026-06-19 replaced keyword-guessing with phase-aware gating in `/spec`/`/plan`/`/execute`
  + a `/session-close` next-model reminder; the keyword hook stays only as a weak backstop.)*

---
*Lean digest. Source of truth for current position; history lives in the linked files.*
*Last updated: 2026-07-02.*
