# Session History

## Active Project
LLM-Directions - Documentation system for AI-assisted development

## Current Status
→ See [PROJECT_STATE.md](../PROJECT_STATE.md)

## Sessions

| Date | Focus | Outcome | Log |
|------|-------|---------|-----|
| 2026-05-15 | Audit punch-list cleanup: AutoRedact orphans + consumer-index backfill + script regex fix | **AutoRedact** (not git-tracked): split inline 4-session file `2026-04-05.md` into per-session files `.md`/`-b.md`/`-c.md`/`-d.md` (43/57/44/34 lines). Backup retained `.pre-split-backup`. **Consumer indexes:** added rows in MousePlus (`2026-05-01-a`, local), SFTPmount (`2026-05-09-spike`, pushed as `1eaf000`), KinoBerlin (`2026-01-16-tmdb-ratings-plan` with `(artifact)` label, local-only repo, `089137f`). **Group Alarms** false-positive — entries were already indexed via `(./<file>.md)` bullet-list links the audit regex didn't accept. **Script patch** (`5c1ca10`): `sync-session-index.sh` regex now accepts both `(<file>.md)` and `(./<file>.md)` link forms; verified `✓ in sync` across 11 projects (4 backfilled + 6 regression-test + master self-audit). **SFTPmount duplicate-commit recovery:** another Mac had pushed near-identical spike work; `git reset --hard origin/main` dropped my duplicate, re-added the unique `_index.md` row. **3 commits on `origin/main`** (`5c1ca10`, `246fbd4` allowlist chore, plus SFTPmount's `1eaf000` on a different remote). Audit punch list now 1 item remaining (`/session-close` dogfooding — can't be done retroactively) | [log](2026-05-15.md) |
| 2026-05-13 → -14 | Cross-project Directions audit: six quick-wins + master backfill + 10-consumer sweep + full sync-conflict cleanup + M2 complete | 4 parallel Explore agents scanned 30 projects / 434 logs; web cross-check (AGENTS.md standard, Kiro SDD, 2026 CLAUDE.md guides). **Q2:** rename `55_→36_`. **Q5+Q5b:** archived `/0-DIRECTIONS/` monolith + parallel `docs/`; umbrella dir 30 → 6 entries. **Q4:** `28_xcode-signing-and-sourcekit.md`. **Q1:** `sync-session-index.sh` + `/check-index`. **Q3:** `/session-close` 6-step checklist. **Master backfill:** 9 missing rows. **Consumer cleanup:** 29 bootstrap-contamination files removed across 4 consumers. **Sync-conflict cleanup:** all 12 conflicts under `/ProgrammingProjects/` resolved. **Syncthing prevention:** `.stignore` ignores `.git`, `.DS_Store`, `.claude/settings.local.json`, signing xcconfigs, build/cache dirs. **M2 complete:** `29_web-strato-hosting.md` (230L, 4 web projects); `39_libsql-turso-sync.md` (198L, LEARNING libSQL CDC); `38_ios-swiftui-state.md` (247L, 5 iOS state patterns from Group Alarms). 20s gotchas contiguous 20–29; 30s discipline now 30–36 + 38–39. **M1 complete** (`b5b1d19`): consolidated `50_progressive-context.md` + `52_context-management.md` + `58_context-engineering.md` (1042L of overlap) into canonical three-part `52_context-management.md` (Architecture + Runtime + Information Design); 50 and 58 become breadcrumb stubs; inbound refs updated in 3 files. Audit punch list **fully closed**. **13 commits on `origin/main`** | [audit-day](2026-05-13.md) · [exec-day](2026-05-14.md) |
| 2026-05-10 | Admin: commit pending settings, push | Committed `f098483` (Claude Code permission allowlist additions from 2026-05-01 cleanup), pushed `6e42766..f098483` to `origin/main` | [log](2026-05-10.md) |
| 2026-05-01 | Flatten master structure to fix consumer-bootstrap friction | Moved `docs/cookbook/` → `cookbook/` (62 entries, links rewritten); consolidated drifted `sessions/` folders; replaced `git clone … docs` bootstrap with rsync-with-excludes (no embedded `.git`, no tool-cache bloat); shipped `mcp-templates/`; added cookbook entries 40–61; 2 commits `8b495e5` + `57f2e9a` pushed to `origin/main`; patched BatchTextExtractorPlus inline | [log](2026-05-01.md) |
| 2026-04-28 | Diagnose & prevent codebase-memory-mcp CPU runaway | Killed PID 22328 (837% CPU, 21 GB RAM), freed 5.6 GB by deleting 3 umbrella DBs; wrote PreToolUse guard hook (concrete + templated); shipped `27_mcp-gotchas.md`, `hooks/mcp-guards/`, ecosystem entry, `CLAUDE-GLOBAL-TEMPLATE.md` MCP Hygiene subsection — committed `bf99e2f`, unpushed | [log](2026-04-28.md) |
| 2026-04-21 | Add design-tokens cookbook + correct Penumbra reference model | Created `39-design-tokens.md` (typography/spacing/icons/radii grounded in live Penumbra); added canonical-path + SwiftUI-not-AppKit note to `00-app-shell.md`; promoted Sigil's Theme extensions to sanctioned policy; restructured memory into per-file index | [log](2026-04-21.md) |
| 2026-04-19 | Persist Apple identity + signing conventions | Saved Team ID FDMSRXXN73 + canonical bundle pattern `com.lucesumbrarum.<AppName>` to memory; scanned 8 macOS pbxprojs; added `14_project-identity.md` | [log](2026-04-19.md) |
| 2026-04-14 | Rename root folder XcodeProjects → CodingProjects | Scoped refs, wrote idempotent rename script with backup+rollback; awaiting execution | [log](2026-04-14.md) |
| 2026-04-03 | Install Stream Deck MCP integration for Claude Code | Installed official `@elgato/mcp-server` v0.1.1 globally; native MCP support shipped in Stream Deck 7.4 (April 2026); chose official over 4 community alternatives (verygoodplugins, jxxh204, sohumsuthar, AgentDeck); verified `elgato: Connected` in Claude Code MCP config at both project and user scope | [log](2026-04-03.md) |
| 2026-03-31 | Evaluate Phantom (ghostwright/phantom) autonomous co-worker agent | Not adopting now — flagged as a Mac mini project for a dedicated future session. Key fit: background delegation + persistent cross-project memory via Qdrant-backed MCP (Tailscale + Ollama + Slack channel); less useful for active coding work | [log](2026-03-31.md) |
| 2026-03-24 | Design per-project static website generator for Directions | Bottom-up architecture: each project generates `docs/site/index.html` + `project.json` (data contract); master aggregator at `__DIRECTIONS/site/` discovers all `project.json` files; auto-triggers on `/setup` and `/log`. Complements existing ProjectOverview (top-down). Open questions on schema + LOC/git activity | [log](2026-03-24.md) |
| 2026-03-10 | Install codebase-memory-mcp + persist Apple developer credentials | Installed CMM v0.4.6 to `~/.local/bin/`; auto-registered with 7 editors (Claude Code, Codex CLI, Cursor, Windsurf, Gemini CLI, VS Code, Zed); 4 skills installed (exploring, tracing, quality, reference); complemented Serena (Serena = editing, CMM = exploration/tracing). Created `~/.claude/apple-developer.md` with Team ID FDMSRXXN73 + bundle prefix `com.lucesumbrarum` + signing identity | [log](2026-03-10.md) |
| 2026-02-27 | Wire folder structure into setup flow | Updated template, base, setup command; synced live CLAUDE.md | [log](2026-02-27.md) |
| 2026-02-21 | Improve Claude Code approval-prompt UX | Added rule to global `~/.claude/CLAUDE.md` Communication Style: "always explain the command's purpose in your message before executing it" — workaround until native Claude Code support for command-explanation prompts | [log](2026-02-21.md) |
| 2026-02-18 | Install XcodePreviews globally | Cloned, installed `/preview` command, updated ecosystem docs, tested on Group Alarms | [log](2026-02-18.md) |
| 2026-02-12 | Install codemoot (Claude Code ↔ Codex CLI bridge for cross-model review) | Built from source at `/Users/sim/Tools/codemoot` (npm `@codemoot/cli` had a `workspace:*` protocol bug); `pnpm link --global`; `codemoot doctor` passes in __DIRECTIONS + Penumbra; added global CLAUDE.md note instructing Claude Code to run `codemoot` via Bash, not the built-in `/code-review` skill | [log](2026-02-12.md) |
| 2026-02-11 | Multi-Mac skills sync + deploy pending Directions updates | Pushed pending commit (skills.sh integration); gitignored `.claude/skills/` and `.agents/` (managed externally by `npx skills`); created `scripts/install-skills.sh` for multi-Mac deployment; kept `settings.local.json` in repo as setup reference | [log](2026-02-11.md) |
| 2026-02-10 | Research pointfreeco/sqlite-data + audit projects with persistence | Reviewed sqlite-data (GRDB-backed, SwiftData-like API `@Table`/`@FetchAll`/`@FetchOne`, CloudKit sync, ~6× faster than GRDB+Codable); audited 1-macOS + 2-iOS — found 6 projects with persistence (MusicServer/GRDB best migration candidate; Nexus/CardGamesTutorials/LangDisp/PhotoInventory on SwiftData; Meeting Recording on Core Data); no adoption yet — bookmarked | [log](2026-02-10.md) |
| 2026-02-02 | Deploy cookbook + sync commands | Vestige patterns stored, 7 commands added to global CLAUDE.md | [log](2026-02-02.md) |
| 2026-01-29 | Installed Vestige memory MCP server | MCP configured for Claude | [log](2026-01-29.md) |
| 2026-01-24 | LLM failure modes reference | Added 53_llm-failure-modes.md from WFGY analysis | [log](2026-01-24.md) |
| 2026-01-23 | System improvement analysis | Simplified onboarding, consolidated docs, added testing guide | [log](2026-01-23.md) |
| 2025-02-07 | Install agent skills marketplace (skills.sh) globally | Installed **261 skills** across SwiftUI/Swift (avdlee), UI/UX (vercel-labs, anthropics, nextlevelbuilder, wshobson, giuseppe-trisciuoglio), web (React/Tailwind/shadcn), workflow patterns (obra/superpowers — TDD, systematic-debugging, verification, planning, git-worktrees), docs generation (PDF/DOCX/XLSX/PPTX), architecture, AWS/DevOps; established `npx skills` as the deployment/update mechanism. (*Filename year is 2025 — may be a typo for 2026; content fits the broader 2026 ecosystem timeline.*) | [log](2025-02-07.md) |

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
