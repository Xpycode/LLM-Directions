# Session History

## Active Project
LLM-Directions - Documentation system for AI-assisted development

## Current Status
→ See [PROJECT_STATE.md](../PROJECT_STATE.md)

## Sessions

| Date | Focus | Outcome | Log |
|------|-------|---------|-----|
| 2026-05-13 → -14 | Audit consumer session logs across all `/ProgrammingProjects/` + execute six quick-wins | 4 parallel Explore agents scanned 30 projects / 434 logs; verified claims via shell stats; web cross-check (AGENTS.md standard, Kiro SDD, 2026 CLAUDE.md guides). **Q2:** `git mv 55_ui-changes-protocol.md 36_ui-changes-protocol.md` + 4 master ref updates. **Q5:** archived dormant `/0-DIRECTIONS/` monolith (~600 files, 12 MB) → `__archive/2026-01-07-pre-flatten-monolith/`. **Q5 follow-on:** archived `/0-DIRECTIONS/docs/` (~452 KB) → `__archive/2026-02-06-pre-final-flatten-docs/`; umbrella dir 30 → 6 entries. **Q4:** wrote `28_xcode-signing-and-sourcekit.md` (187 lines). **Q1:** wrote `scripts/sync-session-index.sh` (154 lines, bash 3.2-compat) + `commands/check-index.md` slash command; discovered 3 consumer projects share the same 6-entry bootstrap-contamination pattern AND the master itself has 9-entry index drift. **Q3:** wrote `commands/session-close.md` (122-line slash command, 6-step end-of-session checklist) — prevent-at-source mechanism for the four drift patterns. Audit findings logged: `_index.md` drift in 16/29 projects, 50/52/58 context-doc fragmentation, missing gotchas for web/iOS still pending | [log](2026-05-13.md) |
| 2026-05-10 | Admin: commit pending settings, push | Committed `f098483` (Claude Code permission allowlist additions from 2026-05-01 cleanup), pushed `6e42766..f098483` to `origin/main` | [log](2026-05-10.md) |
| 2026-05-01 | Flatten master structure to fix consumer-bootstrap friction | Moved `docs/cookbook/` → `cookbook/` (62 entries, links rewritten); consolidated drifted `sessions/` folders; replaced `git clone … docs` bootstrap with rsync-with-excludes (no embedded `.git`, no tool-cache bloat); shipped `mcp-templates/`; added cookbook entries 40–61; 2 commits `8b495e5` + `57f2e9a` pushed to `origin/main`; patched BatchTextExtractorPlus inline | [log](2026-05-01.md) |
| 2026-04-28 | Diagnose & prevent codebase-memory-mcp CPU runaway | Killed PID 22328 (837% CPU, 21 GB RAM), freed 5.6 GB by deleting 3 umbrella DBs; wrote PreToolUse guard hook (concrete + templated); shipped `27_mcp-gotchas.md`, `hooks/mcp-guards/`, ecosystem entry, `CLAUDE-GLOBAL-TEMPLATE.md` MCP Hygiene subsection — committed `bf99e2f`, unpushed | [log](2026-04-28.md) |
| 2026-04-21 | Add design-tokens cookbook + correct Penumbra reference model | Created `39-design-tokens.md` (typography/spacing/icons/radii grounded in live Penumbra); added canonical-path + SwiftUI-not-AppKit note to `00-app-shell.md`; promoted Sigil's Theme extensions to sanctioned policy; restructured memory into per-file index | [log](2026-04-21.md) |
| 2026-04-19 | Persist Apple identity + signing conventions | Saved Team ID FDMSRXXN73 + canonical bundle pattern `com.lucesumbrarum.<AppName>` to memory; scanned 8 macOS pbxprojs; added `14_project-identity.md` | [log](2026-04-19.md) |
| 2026-04-14 | Rename root folder XcodeProjects → CodingProjects | Scoped refs, wrote idempotent rename script with backup+rollback; awaiting execution | [log](2026-04-14.md) |
| 2026-02-27 | Wire folder structure into setup flow | Updated template, base, setup command; synced live CLAUDE.md | [log](2026-02-27.md) |
| 2026-02-18 | Install XcodePreviews globally | Cloned, installed `/preview` command, updated ecosystem docs, tested on Group Alarms | [log](2026-02-18.md) |
| 2026-02-02 | Deploy cookbook + sync commands | Vestige patterns stored, 7 commands added to global CLAUDE.md | [log](2026-02-02.md) |
| 2026-01-29 | Installed Vestige memory MCP server | MCP configured for Claude | [log](2026-01-29.md) |
| 2026-01-24 | LLM failure modes reference | Added 53_llm-failure-modes.md from WFGY analysis | [log](2026-01-24.md) |
| 2026-01-23 | System improvement analysis | Simplified onboarding, consolidated docs, added testing guide | [log](2026-01-23.md) |

---

## Session Log Template

When starting a new session, create a file: `sessions/YYYY-MM-DD-[a|b|c].md`

```markdown
# Session: [Date] [a/b/c]

## Goal
[What we're trying to accomplish]

## Context
- Previous session: [link or summary]
- Current phase: [discovery|planning|implementation|polish|shipping]

## Progress

### Completed
- [x] [What got done]

### In Progress
- [ ] [What's being worked on]

### Discovered
- [New things learned]

### Decisions Made
- [Decision] → logged in decisions.md

### Blockers
- [Anything blocking progress]

## Next Session
- [What to do next]

## Notes
[Anything else worth remembering]
```

---
*One log per session. Link from here.*
