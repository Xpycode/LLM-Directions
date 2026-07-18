# Project State

> **Lean digest — target <50 lines.** Current state + a short changelog, then pointers to detail
> files. History lives in `decisions.md` and `sessions/_index.md`, not here.

## Identity
- **Project:** Directions — LLM-assisted development framework (specs, plans, verification)
- **Tags:** meta, framework, documentation, workflow, Claude · **Started:** 2024

## Now
- **Phase:** build / implementation (~80%) — mature framework, ongoing refinement.
- **Focus:** portfolio **"app citizenship" rollout** — shared Feedback/Tip-Jar/About
  (`AppCitizenshipKit` 0.1.2) across all macOS apps; reference app Conjoyn migrated end-to-end
  (migration + proving-ground pattern: cookbook #108).
- **Blockers:** none.
- **Next:** *(product)* roll ACK to **DiskVerdict** (additive — has FeedbackKit, gains Tip Jar +
  About), then the rest of the wave (per-app checklist: ACK README + #108); separate sweep — fix
  19/30 missing/empty AppIcons (#76). *(design)* per-app `DESIGN.md` briefs + accents (orange stays
  Penumbra's; Conjoyn needs its own); appearance wave 1 = DiskVerdict/Conjoyn/TimeCodeEditor/Magpie,
  rest gradually. *(framework)* optional Wave 3 per-file trims (`OPTIMIZATION-PLAN §3`);
  carried-over TODO: cookbook #92 (hook↔statusline handshake pattern).

## Recent
<!-- Last ~5 changes, one line each, plain language. Full detail → sessions/_index.md -->
- **2026-07-18** — Adopted the **house design system**: Claude-Desktop's screenshot critique distilled
  into `42_design-system.md` (tokens + banned LLM-tells + per-app briefs), new `/check design` mode,
  shell-check updated + versioned into repo; appearance standard now **dark default + user light**.
- **2026-07-16→18** — Drive-by gotchas from app work: ScrollView centers narrower content, macOS 26
  popover-after-NSOpenPanel crash, Strato Python-on-CGI, cookbook #163 (SwiftTerm env) + #164.
- **2026-07-13** — M1 Max caught up: 5-behind + dirty tree proved pure Syncthing duplicates of
  origin — discarded and fast-forwarded, nothing lost; both Macs in sync.
- **2026-07-13** — Authored the previously-phantom **`git-bootstrap` skill** (merged with the M1
  Max's richer live copy), deployed identically to both Macs; `redeploy.sh` now installs skills.
- **2026-07-11** — Evaluated **claude-octopus**, rejected wholesale; its one good idea became
  cookbook **#159** (keyword→prompt "blind-spot" library seeded from our own gotcha docs).

## Progress
- **Funnel:** Define ✅ · Plan ✅ · **Build 🔶** — iterating on improvements.
- **Readiness:** Features ✅ · UI/Polish 🔶 · Testing ⚪ · Docs ✅ · Distribution ✅

## Detail (read only if needed)
- **Why** → `decisions.md` · **history** → `sessions/_index.md` · **backlog** → `TASKS.md` (+ archive)
- **Global config mirror** → `CLAUDE-GLOBAL-TEMPLATE.md` (live `~/.claude/CLAUDE.md` is not in this repo)

## Infrastructure
- 261 global skills at `~/.claude/skills/` (update: `npx skills update`)
- XcodePreviews `/preview` at `/Users/sim/ProgrammingProjects/0-DIRECTIONS/XcodePreviews/`
- **Mac restore:** `git pull --ff-only && bash redeploy.sh --dry-run && bash redeploy.sh`, then
  `bash hooks/install.sh` once. (`install-directions.sh` alone copies without pruning and won't
  overwrite CLAUDE.md — not enough.)

## Resume
<!-- If RESUME.md exists, note it here. Otherwise blank. -->

---
*Lean digest. Source of truth for current position; history lives in the linked files.*
*Last updated: 2026-07-18.*
