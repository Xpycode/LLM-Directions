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
- **Next:** *(framework, in flight)* **Wave 2 is ¾ done** — 2.1 (cookbook router), 2.3 (doc dedup),
  2.4 (growth-file caps) landed 2026-07-02 (d). **Remaining: 2.2 — consolidate 36 commands → ~14**
  (`/log` absorbs session-close/depart/handoff/check-index/phase/compound; `/status` absorbs
  context/arrive; `/spec` absorbs interview/example-map; new `/check` absorbs code-review/quality/
  reflect/review/minimums; generate the `/directions` catalog from `commands/`). Do 2.2 as its own
  focused run (Medium risk — rewrites the command system). **Then** deploy the finalized template +
  commands to `~/.claude/` (that's when `/make-plan` goes live and the `/plan` shadow is removed
  on-machine). *(product)* **roll `AppCitizenshipKit` to the first wave** of apps — DiskVerdict
  next (additive: it has FeedbackKit already, ACK adds Tip Jar + About), then the rest. Use the per-app
  rollout checklist in ACK's README + the `#108` pattern. Separate sweep: fix 19/30 missing/empty
  AppIcons (cookbook #76).
  *(Naming decision baked into ACK: tip-jar framing — "Leave a Tip" / "Tip Jar" — over "Donate"
  (charity) and "Support" (collides with the web help-desk page #105).)*

## Recent
<!-- Last ~5 changes, one line each, plain language. Full detail → sessions/_index.md -->
- **2026-07-02 (d)** — Executed OPTIMIZATION-PLAN **Wave 2 (¾: 2.1+2.3+2.4)** via 3 parallel agents:
  cookbook index 50K→41.6K + split app-shell into #156; deleted/merged 5 numbered docs (03/11/31/
  41apple/42web) into one-home-per-fact + new 41_ui-vocabulary/47_project-ui-conventions; capped
  sessions/_index 42K→9.7K & decisions 42K→20.6K into archives. Fixed all resulting dead links;
  backfilled 2 prior-session orphans (#155 file, #117 variant). 2.2 (commands) deferred.
- **2026-07-02 (c)** — Landed dangling cookbook #153 + backfilled missing index rows #141/#145/#151;
  index now 154/154, no gaps. Pushed.
- **2026-07-02 (b)** — Merged the efficiency branch and executed OPTIMIZATION-PLAN Wave 1 (10
  correctness fixes across ~39 files, incl. `/plan`→`/make-plan`). Global config migration deferred
  to post-Wave-2. Pushed.
- **2026-07-02 (a)** — Reconciled a 14-behind dirty tree via per-file hashing: 26 files were
  duplicates already on origin, only cookbook #152 was genuinely new. Fast-forwarded cleanly.
- **2026-06-19** — Fixed `/status` token bloat (a leaner version existed but was never deployed
  live). Made model-mismatch warnings loud and added phase-aware model gating (`/execute`, `/spec`,
  `/plan`, `/session-close`). Pushed `9a83888`.
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
- **Wave 2 (¾) committed locally, NOT yet pushed** — 5 commits this session (orphan backfill +
  2.1 + 2.3 + 2.4 + this state sync). `main` is ahead of origin; **push before leaving this Mac.**
  Only `.claude/settings.local.json` stays uncommitted (per-Mac). Backpressure met:
  `PATTERNS-COOKBOOK.md` = 41.6 KB (≤45 ✓); cookbook now **157 files** (added #155/#156).
- **Cold-start pickup:** the one Wave 2 piece left is **2.2 — commands 36 → ~14** (see `## Next` and
  `OPTIMIZATION-PLAN.md §2.2`). Target `ls commands | wc -l` ≈ 14. Run it as its own focused session.
- **Live-vs-repo caveat:** all Wave-1 + Wave-2 doc changes + the `/make-plan` rename are in the
  **repo**, NOT yet on this Mac's `~/.claude/` — `/plan` still hits the old custom command live until
  the post-Wave-2 redeploy (deferred deliberately; don't deploy a template 2.2 still rewrites).
- **Fixed this session:** origin had a **dead link** — #155's index row (in `8c89213`) shipped
  without its file; backfilled. Also folded away 5 duplicate docs; `gen-directions-index.sh` now
  reaches docs 27–39.
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
*Last updated: 2026-07-02 (d).*
