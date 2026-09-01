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
  rest gradually — **awaiting: human picks a Sanzo Wada combination for Magpie** (2026-07-19), then
  derive ramps + `DESIGN.md`. *(framework)* optional Wave 3 per-file trims (`OPTIMIZATION-PLAN §3`);
  carried-over TODO: cookbook #92 (hook↔statusline handshake pattern).

## Recent
<!-- Last ~5 changes, one line each, plain language. Full detail → sessions/_index.md -->
- **2026-09-01** — Made `AGENTS.md` the first-class Codex project entry point, added a reusable
  template and dual-tool setup guidance, and kept the live Directions commands as the shared source.
- **2026-08-30** — Added a Codex adapter that runs the same live Directions command files as Claude
  Code, plus a persistent Codex context/token status line; the two tools now share one workflow
  source instead of maintaining translated copies.
- **2026-08-25** — Two patterns out of a consumer project's deploy design: excluding a
  server-canonical directory from the mirror also excludes the `.htaccess` guarding it (auth
  silently bypassable on a site that works), and netrc's host-keying is *why* a sibling project's
  password ended up inline — Keychain keys by service and holds the username too. Also masked the
  Strato account number this repo had been publishing in two examples.
- **2026-08-20** — Credential audit: **none committed** (only deliberate bad-examples). Fixed the
  status-line context gauge, which escalated at 70%/95% while the canonical zone table defines five
  bands at 50/70/85/95 — it stayed blue through the whole "start compacting" zone. Gave this
  **public** repo the secret patterns its `.gitignore` never had; security rules gained the missing
  "secret already committed" step.
- **2026-07-29** — Usage-report follow-ups: per-Mac capability registry (`MACHINES.md` — this M1 Max
  has **no dev cert and no AppProbe**), house permission allowlist union-merged by `redeploy.sh` 2c
  (fixture copies + read-only commands stop hitting the classifier), PreToolUse guard blocking
  `git add -A`/`.` sweeps, cookbook #173 (crash-tolerant agent fan-out). En route, found and healed
  **200+ lines of template↔live CLAUDE.md drift** (live had newer pre-flight, template had newer
  index); migration flow now actually lives in `/setup` as the slim CLAUDE.md long claimed.
## Progress
- **Funnel:** Define ✅ · Plan ✅ · **Build 🔶** — iterating on improvements.
- **Readiness:** Features ✅ · UI/Polish 🔶 · Testing ⚪ · Docs ✅ · Distribution ✅

## Detail (read only if needed)
- **Why** → `decisions.md` · **history** → `sessions/_index.md` · **backlog** → `TASKS.md` (+ archive)
- **Global config mirror** → `CLAUDE-GLOBAL-TEMPLATE.md` (live `~/.claude/CLAUDE.md` is not in this repo)
  + `CLAUDE-SETTINGS-TEMPLATE.json` / `.md` (house-preference half of `~/.claude/settings.json`)

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
*Last updated: 2026-09-01.*
