# Project State

> **Lean digest — target <50 lines.** Current state + a short changelog, then pointers to detail
> files. History lives in `decisions.md` and `sessions/_index.md`, not here.

## Identity
- **Project:** Directions — LLM-assisted development framework (specs, plans, verification)
- **Tags:** meta, framework, documentation, workflow, Claude · **Started:** 2024

## Now
- **Phase:** build / implementation (~80%) — mature framework, ongoing refinement.
- **Focus:** multi-Mac / multi-session safety hardening — git-collision guards, worktree workflow.
- **Blockers:** none.
- **Next:** (1) run `bash hooks/install.sh` on the **other Mac** to wire the new session-collision
  guard. (2) Parked decision — cross-project status view: throwaway gitignored `dashboard.html` vs the
  committed `project.json` site generator (2026-03-24). **Build one, not both.**

## Recent
<!-- Last ~5 changes, one line each, plain language. Full detail → sessions/_index.md -->
- **2026-06-11** — built a guard that warns when two Claude sessions are open in the same folder (they share one git checkout, so a branch switch in one hits both); added a `/worktree` helper to split them safely, and wrote it up as Rule 5 in the multi-Mac doc.
- **2026-06-10** — statusline: removed the broken weekly-limit readout, color-coded model names by tier, and built a model-switch reminder system (UserPromptSubmit keyword hook + persistent statusline hint).
- **2026-06-09** — added cookbook #85/#86; caught + dropped duplicate work another Mac had pushed; slimmed this file and `/status`.
- **2026-06-08** — shared guidance docs are now read on demand from one master copy instead of copied into each project (kills silent drift); added a session-start git-fetch check for cross-Mac collisions.
- **2026-05-16** — wrote the multi-Mac discipline doc after 3 cross-Mac mix-ups in two weeks; re-validated the SFTPmount spike plan against macOS 26.5.
- **2026-05-14** — cross-project cleanup: merged 3 overlapping context docs into one, added iOS/web/sync gotcha docs, fixed session-index drift across 10 projects.

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
- **Per-Mac wiring (does NOT travel via git):** on the **other Mac**, after `git pull`, run
  `bash hooks/install.sh` once — it symlinks the hooks (now including `session-guard.sh`) and the
  statusline into `~/.claude/` and registers them in `settings.json` (idempotent).
- **Carried-over TODO:** cookbook **#92** for the hook↔statusline handshake pattern (#91 is now the
  process-inspection session detector); tune `model-advisor.sh` keyword lists.

---
*Lean digest. Source of truth for current position; history lives in the linked files.*
*Last updated: 2026-06-11.*
