# Project State

> **Size limit: <100 lines.** This is a digest, not an archive. Details go in session logs.

## Identity
- **Project:** Directions
- **One-liner:** LLM-assisted development framework with structured specs, plans, and verification
- **Tags:** meta, framework, documentation, workflow, Claude
- **Started:** 2024

## Current Position
- **Funnel:** build
- **Phase:** implementation
- **Focus:** Acting on cross-project audit findings — Q2, Q5, Q5 follow-on, Q4, Q1, and Q3 shipped. The four drift patterns surfaced by the audit now have either a doc, a detection tool, or a prevention command. Remaining: backfill master's own 9 missing index entries, eat our own dogfood on `/session-close`, consolidate 50/52/58 context docs, add web/iOS gotchas docs, commit the lot.
- **Status:** ready
- **Last updated:** 2026-05-14

## Funnel Progress (Ralph-style)
<!-- The 3-phase funnel that ships software -->

| Funnel | Status | Gate |
|--------|--------|------|
| **Define** | done | Framework documented, patterns established |
| **Plan** | done | Slash commands, templates, workflows defined |
| **Build** | active | Iterating on improvements |

## Phase Progress
```
[################....] 80% - Mature framework
```

| Phase | Status | Tasks |
|-------|--------|-------|
| Discovery | done | ✓ |
| Planning | done | ✓ |
| Implementation | **active** | ongoing |
| Polish | ongoing | docs refinement |

## Readiness
<!-- Status per dimension: ⚪ not started | 🔶 WIP | ✅ done -->

| Dimension | Status | Notes |
|-----------|--------|-------|
| Features | ✅ done | Core framework complete |
| UI/Polish | 🔶 WIP | Slash commands, templates |
| Testing | ⚪ — | Manual verification |
| Docs | ✅ done | Full documentation suite |
| Distribution | ✅ done | GitHub repo, local master |

## Validation Gates
<!-- Backpressure checks before phase transitions -->
- [x] **Define → Plan**: Framework spec complete
- [x] **Plan → Build**: Commands and templates documented
- [ ] **Build → Ship**: Ongoing refinement

## Active Decisions
<!-- Last 3-5 decisions only. Full history in decisions.md -->
- 2026-05-14: Verified `.git` is already in Syncthing's `.stignore` (`**/.git`, present since Apr 29 — predates known conflicts by 3 days). Cleaned 3 residual `.git/*.sync-conflict-*` files (~13 KB). Both KinoBerlin + PDF2Calendar repos remain healthy after delete. 5 non-`.git` sync-conflicts still remain (`.claude/settings.local.*`, `PROJECT_STATE`, two `.swift` source files) — out of scope for this pass.
- 2026-05-14: Merged the 4 `docs/sessions/` sync-conflict files. All 4 turned out to be the same pattern: base = strict superset; deleted the conflicts with zero information loss. MenuBarPLUS + AspectRatioUnifier now `✓ in sync`.
- 2026-05-14: Swept other 7 candidate consumers. Only AutoRedact had real contamination (**6 more files removed**); the other 6 had drift but no contamination. Grand total: **29 contamination files cleaned across 4 consumers**. Side-fixed a whitespace bug in `sync-session-index.sh`.
- 2026-05-14: Cleaned bootstrap contamination from 3 consumers (LUCESUMBRARUM, AvidMXFPeek, ePubReader) — 23 bit-identical-to-master session-log files removed via `cmp -s` + `rm` after dogfooding `sync-session-index.sh` on each. All 3 now `✓ in sync`.
- 2026-05-14: Shipped `commands/session-close.md` (122 lines) — six-step end-of-session checklist (NOT silent automation). Prevents all four audit-surfaced drift patterns at source: missing Next Session, stale PROJECT_STATE, decisions buried in prose, `_index.md` drift. Friction is intentional: human judgment beats auto-stubs for Next Session text and ADR entries.
- 2026-05-14: Shipped `scripts/sync-session-index.sh` (154 lines, bash 3.2-compat) + `commands/check-index.md`. Detects + optionally fixes `_index.md` drift against files on disk. Supports both link-form and bare-date row formats. Surfaced 9-entry drift in master's own index + a shared 6-entry bootstrap-contamination pattern across 3 consumer projects.
- 2026-05-14: Wrote `28_xcode-signing-and-sourcekit.md` (187 lines) — codifies the `Debug.local.xcconfig` per-machine signing pattern and SourceKit false-positive discipline that had been independently rediscovered in 6+ projects. Fills the open `28_` slot in the 20s gotchas range.
- 2026-05-14: Archived `/0-DIRECTIONS/docs/` (second-gen parallel master, 452 KB, 2026-02-06) to `__archive/2026-02-06-pre-final-flatten-docs/`. Umbrella dir: 7 → 6 entries. Naming-ambiguity risk eliminated.
- 2026-05-13: Archived dormant `/0-DIRECTIONS/` doc monolith (19 dirs + txt + 3 loose sessions, ~600 files, 12 MB, frozen 2026-01-07) to `__archive/2026-01-07-pre-flatten-monolith/` with summary ARCHIVE.md. Umbrella dir: 30 → 7 entries.
- 2026-05-13: Renamed `55_ui-changes-protocol.md` → `36_ui-changes-protocol.md` (fixes duplicate `55_` prefix with `55_spec-template.md`; semantic fit in the 30s process-discipline range). Master refs updated; consumers update on next sync.
- 2026-05-01: Flattened master — cookbook moved to root (`cookbook/` not `docs/cookbook/`); bootstrap is now rsync-with-excludes (no embedded `.git`, no tool-cache bloat). Eliminates `docs/docs/cookbook/` nesting in consumer projects. Cookbook at 62 entries (added 40–61).
- 2026-04-28: Adopted MCP-hygiene pattern — PreToolUse guard on `index_repository` + new `hooks/mcp-guards/` dir; first instance documents codebase-memory-mcp's umbrella-cwd footgun in `27_mcp-gotchas.md`
- 2026-03-24: Designing per-project static site generator — bottom-up complement to ProjectOverview aggregator
- 2026-02-27: Wired `13_folder-structure.md` into setup flow — template, base, and setup command now auto-create numbered folders
- 2026-02-18: Added XcodePreviews (Iron-Ham/XcodePreviews) to ecosystem — global `/preview` command, documented in 26_ecosystem.md and global CLAUDE.md

## Blockers
<!-- Empty = good. If blocked, include workaround attempts. -->


## Infrastructure
- **Global skills:** 261 installed at `~/.claude/skills/`
- **Key skill sets:** SwiftUI, Swift concurrency, UI/UX, workflow patterns, debugging, TDD
- **Update command:** `npx skills update`
- **XcodePreviews:** `/Users/sim/ProgrammingProjects/0-DIRECTIONS/XcodePreviews/` — `/preview` command for SwiftUI visual capture

## Resume
<!-- If RESUME.md exists, note it here. Otherwise blank. -->


---
*Updated by Claude. Source of truth for project position.*
