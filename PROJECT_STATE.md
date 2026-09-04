# Project State

> **Lean digest — target <50 lines.** Current state + a short changelog, then pointers to detail
> files. History lives in `decisions.md` and `sessions/_index.md`, not here.

## Identity
- **Project:** Directions — LLM-assisted development framework (specs, plans, verification)
- **Tags:** meta, framework, documentation, workflow, Codex, Claude Code · **Started:** 2024

## Now
- **Phase:** build / implementation (~80%) — mature framework, ongoing refinement.
- **Focus:** make Directions first-class for a Codex-primary period: provider-neutral model/context
  guidance, current Codex controls, generated read-on-demand routing, and project `AGENTS.md`.
- **Blockers:** none.
- **Next:** start a fresh Codex session; exercise `status arrive`, `execute`, `check ship`, and `log`
  in consumer projects; refine the ten new entry points from real use; then decide whether concrete
  missing automation justifies a Codex hooks port.

## Recent
<!-- Last ~5 changes, one line each, plain language. Full detail → sessions/_index.md -->
- **2026-09-04** — Made model/context guidance provider-neutral, documented current Codex controls
  and provider mappings, refreshed global routing, and added tailored `AGENTS.md` files to the ten
  recently active projects after their logs and existing instructions were audited.
- **2026-09-02** — Stopped Codex from reading Claude-only model markers or recommending Claude
  `/model` commands; model guidance now uses Codex model strength and reasoning effort when useful.
- **2026-09-01** — Made bare Directions requests such as `/status arrive` and `log clear` the
  primary Codex convention; the longer `$directions` form is now only a compatibility fallback.
- **2026-09-01** — Made `AGENTS.md` the first-class Codex project entry point, added a reusable
  template and dual-tool setup guidance, and kept the live Directions commands as the shared source.
- **2026-08-30** — Added a Codex adapter that runs the same live Directions command files as Claude
  Code, plus a persistent Codex context/token status line; the two tools now share one workflow
  source instead of maintaining translated copies.
## Progress
- **Funnel:** Define ✅ · Plan ✅ · **Build 🔶** — iterating on improvements.
- **Readiness:** Features ✅ · UI/Polish 🔶 · Testing ⚪ · Docs ✅ · Distribution ✅

## Detail (read only if needed)
- **Why** → `decisions.md` · **history** → `sessions/_index.md` · **backlog** → `TASKS.md` (+ archive)
- **Global config mirrors** → `CODEX-GLOBAL-TEMPLATE.md` + `deploy-codex.sh`; Claude Code remains in
  `CLAUDE-GLOBAL-TEMPLATE.md`, `CLAUDE-SETTINGS-TEMPLATE.json` / `.md`, and `redeploy.sh`.

## Infrastructure
- Codex Directions skill source: `codex/skills/directions/`; deploy to `CODEX_HOME/skills/directions`.
- XcodePreviews `/preview` at `/Users/sim/ProgrammingProjects/0-DIRECTIONS/XcodePreviews/`
- **Mac restore:** `git pull --ff-only`, then `bash deploy-codex.sh --dry-run && bash deploy-codex.sh`.
  If Claude Code is also used, run its separate `redeploy.sh` flow.

## Resume
<!-- If RESUME.md exists, note it here. Otherwise blank. -->

---
*Lean digest. Source of truth for current position; history lives in the linked files.*
*Last updated: 2026-09-04.*
