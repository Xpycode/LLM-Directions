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
- **Focus:** Cross-project Directions audit (2026-05-13 → -15) **fully closed**. All 6 quick-wins + M1 (50/52/58 → canonical `52_context-management.md`) + M2 (`29_`/`38_`/`39_`) + post-M1 polish (`13_folder-structure.md` web parity, Pattern A/B + deploy artifacts + setup scripts + migration recipes) + AutoRedact orphan split + 4 consumer-index backfills (MousePlus, SFTPmount, KinoBerlin local-only, Group Alarms script-side fix) + `sync-session-index.sh` `(./)` link-form patch. Audit reports `✓ in sync` across master + 10 consumer projects. **2026-05-16 follow-up:** real-product session on SFTPmount produced the 26.5 re-validation rev-3 input + canonized `37_multi-mac-discipline.md` (3 recurring cross-Mac incidents codified). 30s discipline range now contiguous 30–39. **1 housekeeping item remaining**: dogfood `/session-close` on a real session (can't be done retroactively).
- **Status:** ready
- **Last updated:** 2026-05-16

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
- 2026-05-16 (later): **Canonized `37_multi-mac-discipline.md`** (279L, slot 37 — closes the only open 30s slot). Three recurrences in two weeks pushed the cross-Mac pattern past the "interesting incident" threshold: `.claude/settings.local.json` union-merge (2026-05-14), SFTPmount duplicate spike commit detected at push (2026-05-15), M1-vs-M4 spike-context discovery (2026-05-16). Doc structure mirrors `39_libsql-turso-sync.md`: mental model + Rule 1 (`git fetch` first when crossing Macs) + Rule 2 (verify machine-specific OS state on the actual machine; record host identity in spike journals) + Rule 3 (union-merge for accumulating non-tracked files; `.stignore` to prevent recurrence) + Rule 4 (pivot-when-blocked-by-physical-machine pattern, productive substitute for redoing setup) + 30-second pre-flight template + 8-row cheatsheet. Inbound refs wired in `00_base.md` and `01_quick-reference.md`. Master commit `b372d58` pushed.
- 2026-05-16: **Real-product session on SFTPmount.** Attempted Wave 0 Step 3 from M1 Max; pre-flight surfaced spike-context-on-other-machine (no `FSKitExp.app` here, no `~/scratch/sftpmount-spikes/`, no `fskitd` activity 2026-05-09 in retained log — confirmed via three diagnostic methods that the spike actually ran on M4 Pro per journal header). Pivoted to read-only re-validation of rev-3 plan corrections against macOS 26.5: three parallel checks (Info.plist+entitlements diff, log archaeology, FSKit framework surface). Result: 5/6 rev-3 corrections still hold; correction #5 needs `LSMinimumSystemVersion` 26.4 → 26.5; surfaced 6 additional Info.plist keys to mirror Apple's stock + 1 entitlement decision (drop `com.apple.security.network.server` for SFTP). Findings written into `01_Project/spike-r2-fskitd/NOTES.md` as a 5-item rev-3 punch list. SFTPmount commit `f146c66` pushed. **Cross-Mac collision pattern recurred a 3rd time** (the initial M1-vs-M4 confusion); now warrants its own Directions doc. **Pivot-when-blocked-by-physical-machine pattern proven**: when primary task needs other hardware, read-only validation that informs the next attempt is a productive substitute.
- 2026-05-15: **Audit punch list fully closed.** AutoRedact 4-way split (filesystem only; `2026-04-05.md` 177L → 4 per-session files 43/57/44/34L; `.pre-split-backup` retained). Consumer-index backfills shipped: MousePlus `2026-05-01-a` (local), SFTPmount `2026-05-09-spike` (`Xpycode/SFTPmount 1eaf000`), KinoBerlin `2026-01-16-tmdb-ratings-plan` artifact (local-only repo `089137f`). Group Alarms was a false positive — entries already indexed in bullet list via `(./file.md)` form the audit regex rejected. Patched `sync-session-index.sh` (master `5c1ca10`) to accept `(./)` prefix; verified `✓ in sync` across 11 audits (4 backfilled + 6 regression + master self). Side-incident: SFTPmount remote had near-identical spike commits pushed from another Mac (cross-Mac collision pattern recurring); resolved via `git reset --hard` + redo of the unique `_index.md` row.
- 2026-05-14: **M1 + post-M1 polish.** Consolidated `50_progressive-context.md` + `52_context-management.md` + `58_context-engineering.md` (1042L overlap) into canonical three-part `52_context-management.md` (Architecture + Runtime + Information Design), 1001L; 50/58 became 30-line breadcrumb stubs. Then expanded `13_folder-structure.md` 353L → 711L with Pattern A (no-build/Strato) + Pattern B (framework/Vercel), deploy-artifact tables, setup scripts, migration recipes — closes the web-target gap surfaced in the post-M1 audit.
- 2026-05-14: **M2 COMPLETE — wrote `38_ios-swiftui-state.md`** (247 lines). Five iOS state patterns from Group Alarms incidents, all rooted in "SwiftUI property wrappers are View-only": `@AppStorage` on non-View classes silently fails; `SettingsResetService` over duplicate declarations; pessimistic disk + optimistic memory; two-gate guard for implicit actions; UUID Equatable trap. Bonus: Xcode 16 synced folders auto-track filesystem. M2 fully shipped (29_, 38_, 39_).
- 2026-05-14: **M2 partial — wrote `39_libsql-turso-sync.md`** (198 lines). LEARNING's two libSQL/Turso CDC gotchas: DDL never replicates; raw sqlite3 DML bypasses CDC.
- 2026-05-14: **M2 partial — wrote `29_web-strato-hosting.md`** (230 lines). Codifies Strato hosting gotchas rediscovered across 4 web projects. 20s gotchas range contiguous 20–29.
- 2026-05-14: **Sync-conflict audit closed.** Resolved final 3 sync-conflicts in AspectRatioUnifier (base = newer Wave-7 version in all 3). Cleaned 2 `.git/refs/.DS_Store` files. **Zero sync-conflicts remain anywhere under `/ProgrammingProjects/`.**
- 2026-05-14: Merged both `.claude/settings.local.json` conflict pairs via python union (MenuBarPLUS 11 → 24 entries; SFTPmount 7 → 40 entries; both gained 5 MCP servers from the other Mac).
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
