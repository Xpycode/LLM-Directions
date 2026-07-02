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
- **Next:** *(framework)* **Wave 2 fully DONE + redeployed + CLAUDE.md modernized (2026-07-02 (f)).**
  Live `commands/` 38→15 (13 Directions + independent `mcp-profile`/`preview`); and `~/.claude/CLAUDE.md`
  is now the full read-on-demand shape — grep-first cookbook router (was a 52-ref inline dump),
  generated 45-row Directions Index, PROJECT_STATE sentinel, new MCP-hygiene section (411 lines).
  **Two `CLAUDE-GLOBAL-TEMPLATE.md` bugs found during the merge — fix the template before next redeploy
  or they'll regress:** (1) template's Git Discipline still says "never commit to main / feature
  branches" but the live/preferred policy is "small changes → commit straight to main"; (2) template's
  Multi-Mac pre-flight dropped the `NO .git → git-bootstrap skill` case. The deployed file has both
  correct (I merged live-wins). Backups: `~/.claude/commands.bak-*`, `~/.claude/CLAUDE.md.bak-*`. Then
  optionally **Wave 3** (per-file trims). *(product)* **roll `AppCitizenshipKit` to the first
  wave** of apps — DiskVerdict
  next (additive: it has FeedbackKit already, ACK adds Tip Jar + About), then the rest. Use the per-app
  rollout checklist in ACK's README + the `#108` pattern. Separate sweep: fix 19/30 missing/empty
  AppIcons (cookbook #76).
  *(Naming decision baked into ACK: tip-jar framing — "Leave a Tip" / "Tip Jar" — over "Donate"
  (charity) and "Support" (collides with the web help-desk page #105).)*

## Recent
<!-- Last ~5 changes, one line each, plain language. Full detail → sessions/_index.md -->
- **2026-07-02 (f)** — **Redeployed to live `~/.claude/` AND modernized the global CLAUDE.md.** Commands
  38→15 (retired 25 obsolete Directions-owned files via `git log --diff-filter=D` provenance, installed
  the 13 incl. new `/check`+`/make-plan`, left `mcp-profile`/`preview` untouched). Then adopted the
  read-on-demand `CLAUDE-GLOBAL-TEMPLATE.md` as `~/.claude/CLAUDE.md` (411 lines): grep-first cookbook
  router replacing the 52-ref inline dump, generated 45-row Directions Index, PROJECT_STATE sentinel,
  new MCP-hygiene section. **Merged live-wins on two stale-template spots:** kept the "commit straight
  to main" Git Discipline and the `NO .git → git-bootstrap` case (both dropped in the template). Both
  live files backed up (`~/.claude/commands.bak-*`, `CLAUDE.md.bak-*`).
- **2026-07-02 (e)** — Executed OPTIMIZATION-PLAN **Wave 2.2: 36 commands → 13.** `/log` absorbs 7
  end-of-session commands; new `/check` (code|ship|security) absorbs 5 + security-audit→63_ doc;
  `/status`←context/arrive; `/spec`←interview/example-map; `/execute`←next (gate softened to nudge);
  `/directions`←update-directions with a generated catalog; deleted tdd/build-fix/checkpoint/reorg.
  Swept ~50 cross-refs across 22 files + hooks. 8 commits; Wave 2 now fully done. **Redeploy pending.**
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
- **Wave 2 FULLY done** — 2.1–2.4 (5 commits, pushed earlier) + **2.2 commands 36→13** (8 commits
  this session). Backpressure met: `ls commands | wc -l` = **13**; `PATTERNS-COOKBOOK.md` = 41.6 KB;
  no live dead command refs. Only `.claude/settings.local.json` stays uncommitted (per-Mac).
- **Redeploy + CLAUDE.md modernization DONE (2026-07-02 (f)).** Live `~/.claude/commands/` = 15;
  `~/.claude/CLAUDE.md` = 411 lines, full read-on-demand shape (grep-first cookbook router, generated
  45-row Directions Index via `gen-directions-index.sh`, PROJECT_STATE sentinel, MCP-hygiene section).
  Nothing on-machine is pending. Backups: `~/.claude/commands.bak-20260702-203924`,
  `~/.claude/CLAUDE.md.bak-20260702-204226`. **Not yet done (repo hygiene, optional):** patch the two
  stale spots in `CLAUDE-GLOBAL-TEMPLATE.md` (Git Discipline → "commit straight to main"; re-add the
  `NO .git → git-bootstrap` case) so a future redeploy doesn't reintroduce them; note the template is
  the *public* LLM-Directions repo so keep the personal bootstrap identity out of it. Then optionally
  **Wave 3** (per-file trims, `OPTIMIZATION-PLAN §3`).
- **First-real-use watch:** the 13 commands + the new CLAUDE.md shape haven't been exercised live yet
  — `/check`, `/log`'s absorbed modes, and the grep-first cookbook lookup are the most-changed.
- **Not yet verified by real use:** the 13 commands passed static checks (grep/counts/bash-n/py_compile)
  but no live dry-run in a scratch project (plan's Wave 2 backpressure) — first real invocations
  post-redeploy are the true test. `/check` and `/log`'s new modes are the most-changed; watch those.
- **The 13 commands:** setup · status (+full/arrive) · log (end-of-session: close/depart/handoff/
  phase/compound/blockers) · decide · learned · spec (+deep/examples) · make-plan · execute (+next) ·
  check (code|ship|security) · cookbook · directions (+update) · worktree · test-app.
- **Per-Mac wiring (does NOT travel via git):** both Macs are wired — M1 Max erased+restored
  2026-06-13 and `bash hooks/install.sh` was re-run there (symlinks verified); M4-Pro long since done.
  Reminder only if a Mac is restored again: after `git pull`, run `bash hooks/install.sh` once — it
  symlinks the hooks (incl. `session-guard.sh`) + statusline into `~/.claude/` and registers them in
  `settings.json` (idempotent).
- **Carried-over TODO:** cookbook **#92** for the hook↔statusline handshake pattern (#91 is now the
  process-inspection session detector). *(The "tune `model-advisor.sh` keyword lists" TODO is
  superseded — 2026-06-19 replaced keyword-guessing with phase-aware gating in `/spec`/`/make-plan`/`/execute`
  + a `/log` next-model reminder; the keyword hook stays only as a weak backstop.)*

---
*Lean digest. Source of truth for current position; history lives in the linked files.*
*Last updated: 2026-07-02 (f).*
