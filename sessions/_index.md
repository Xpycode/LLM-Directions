# Session History

## Active Project
LLM-Directions - Documentation system for AI-assisted development

## Current Status
→ See [PROJECT_STATE.md](../PROJECT_STATE.md)

## Sessions

> Outcome cells are capped at ~300 chars. Older rows (pre-2026-05-15) → [_index-archive.md](_index-archive.md).

| Date | Focus | Outcome | Log |
|------|-------|---------|-----|
| 2026-07-02 | `/execute` OPTIMIZATION-PLAN **Wave 2 (¾)** — cookbook router + doc dedup + growth-file caps via 3 parallel agents | Ran 2.1/2.3/2.4 concurrently (disjoint file sets), deferred risky 2.2 (commands). **2.1:** index 50,360→41,603 B (≤45K ✓), split 00-app-shell→#156 (canonical Info.plist home), #00/#16/#89 now cross-ref. **2.3:** deleted/merged 5 docs (03/11/31/41apple/42web) into one-home-per-fact + new 41_ui-vocabulary & 47_project-ui-conventions; trimmed CLAUDE-GLOBAL-TEMPLATE; regenerated router (docs 27–39 reachable). **2.4:** sessions/_index 42K→9.7K & decisions 42K→20.6K into archives; /decide + /log read-rule/budget edits. Fixed all resulting dead links; **repaired an origin dead link** (#155 row shipped in `8c89213` without its file) + backfilled #117 variant. 5 local commits, **not yet pushed**. | [log](2026-07-02.md) |
| 2026-07-02 | `/arrive` on M1 Max: reconcile `behind 14` + dirty tree (copy-vs-drift) losslessly via fast-forward | Reconciled 14-behind dirty tree: per-file hashing found 26 dupes (dropped), 1 unique file kept (#152), fast-forwarded clean. Merged efficiency branch + ran OPTIMIZATION-PLAN Wave 1 (10 fixes, `0081238`). Backfilled missing cookbook-index rows #141/#145/#151/#153 — 154/154 reconciled. Pushed `129d730..cf21478`. | [log](2026-07-02.md) |
| 2026-06-19 | `/status`+`/arrive` token-cost diagnosis → louder model warnings → phase-aware model gating | Root-caused /status token bloat to an undeployed command fix; deployed it. Made model-mismatch warnings loud (red statusline bar, CAPS message). Built phase-aware model gating: /execute gates to Sonnet, /spec+/plan nudge Opus, /session-close reminds next session's model. Synced 10 stale commands. Pushed `9a83888`. | [log](2026-06-19.md) |
| 2026-06-18 | Reconcile a cross-Mac `ahead 4 / behind 4` divergence (duplicate-commit signature) while shipping SearchAway Wave-5 cookbooks | Reconciled a cross-Mac ahead-4/behind-4 divergence: per-file diff proved 3 local commits were byte-identical duplicates already on origin (dropped); kept 2 unique commits (#124 benchmark, #73 HUD gotchas) + untracked #123 via reset --hard + cherry-pick. Pushed `f53058b..9bc9373`. SearchAway 5.3 logged separately. | [log](2026-06-18.md) |
| 2026-06-17 (b) | `/arrive` on M1 Max: reconcile parked cookbooks, then roll Directions out to live config + 3 projects | `/arrive` flagged behind-7 as a "byte-identical phantom" but file hashing found 3 genuine uncommitted cookbooks (#118-120) a prior session left; reconciled with `reset --mixed` (not --hard) to preserve them, pushed `ba70cae`. Rolled Directions out to live `~/.claude/commands/` + synced 3 of 44 vestigial project copies (DiskVerdict, Conjoyn, App-Websites). | [log](2026-06-17-b.md) |
| 2026-06-16 | `/arrive` on M1 Max + clear stale per-Mac wiring reminders | Fast-forwarded `4bad1d9..b49d038` on M1 Max. Corrected stale PROJECT_STATE reminders that still described the M1 Max restore as belonging to "the other Mac" — it was this Mac; removed the stale Next item, rewrote Resume to reflect both Macs wired. | [log](2026-06-16.md) |
| 2026-06-15 | `/arrive` on M4-Pro: reconcile a copy-vs-drift tangle, then commit/push cookbook #110 | Reconciled a copy-vs-drift tangle via per-file hashing, pushed cookbook #110 (deep-link System Settings + prove bundle id against .appex registry) + gotcha updates to #65/#71 (`a740b73`). Rewrote /log as session-close (arg-driven modes). Grew /minimums with an HUD/agent tier. Added cookbook #112 (security-scoped bookmarks). Yielded a numbering collision to #111. | [log](2026-06-15.md) |
| 2026-06-14 (b) | First `AppCitizenshipKit` integration (Conjoyn) + harden the package + cookbook #108 + Directions | First AppCitizenshipKit integration (Conjoyn), used as differential test. Fixed 3 package defects up-stream (stray ellipsis, missing divider, Support/Donate naming collision → "Leave a Tip" framing), published ACK 0.1.1→0.1.2. Verified live Help/App menus via AppleScript. Reconciled a duplicate #106 (renumbered to #107). | [log](2026-06-14-b.md) |
| 2026-06-14 | Portfolio-wide "app citizenship" audit (Help/Feedback/Donate/About/Updates/etc.) + build `AppCitizenshipKit` | Portfolio-wide app-citizenship audit (7 agents, 30 apps): Donate 0/30, Feedback 2/30, custom About 1/30, AppIcon broken 19/30. Corrected infra assumptions (AppUpdater not reusable, PaymentOptions docs-only). Built `AppCitizenshipKit` package (Feedback+Donate+About), `swift build`/`test` clean. Not yet published or integrated. | [log](2026-06-14.md) |
| 2026-06-13 (b) | Resolve cross-project status view + multi-Mac sync architecture + build `/arrive`+`/depart` | Chose a disposable gitignored dashboard.py/.html (top-down PROJECT_STATE scan) over a committed project.json generator for cross-project status. Clarified Syncthing vs GitHub sync roles (private GitHub for code). Built /arrive+/depart, machine identity via git commit trailer `Handoff-from:`, not a tracked file. | [log](2026-06-13-b.md) |
| 2026-06-13 | Reconcile a behind-10 + dirty tree (erased-Mac Syncthing phantom) + harden hook/doctrine | Diagnosed behind-10 dirty tree as a Rule-1a "erased-Mac" phantom (other Mac restored, Syncthing carried current files onto stale .git) — proved byte-identical, `reset --hard origin/main` reconciled losslessly. Hardened session-start.sh to compute a confirmed verdict via hash-object; documented the SIGPIPE gotcha in `37_multi-mac-discipline.md`. | [log](2026-06-13.md) |
| 2026-06-11 | Same-folder Claude session collision guard + `/worktree` | Diagnosed that two Claude sessions sharing one folder share one git checkout — a checkout in either moves the branch for both. Built `hooks/session-guard.sh` (process-inspection collision detector, worktree-aware), wired into session-start + /status, and a new `/worktree` command. Added Rule 5 to multi-mac doc. Pushed `da7fb6d`+`1670755`. | [log](2026-06-11.md) |
| 2026-06-10 | Statusline cleanup + build the model-switch reminder system | Removed the broken weekly-usage statusline readout. Color-coded model names by tier. Built the model-switch enforcement: `hooks/model-advisor.sh` keyword-matches prompts and nudges via statusline handshake + systemMessage. Reconciled a 5th cross-Mac duplicate commit. Pushed `93c3632`. | [log](sessions/2026-06-10.md) |
| 2026-06-08 | Ship the copy-vs-drift fix + reconcile cross-Mac divergence | Shipped the copy-vs-drift fix: added a Directions Index to global CLAUDE.md, made /setup scaffold only project-specific files, moved the sentinel `00_base.md`→`PROJECT_STATE.md`. Reconciled a duplicate cookbook #80/#81 from another Mac. Same-day follow-up: another Mac had shipped the identical fix in parallel — reset --hard dropped the dupes, pushed `0897333`+`499b314`. | [log](sessions/2026-06-08.md) |
| 2026-06-07 | Main-menu house-style + Directions copy-vs-drift fix (spilled from zPackages) | Drafted `46_main-menu.md` house-style doc. Diagnosed the copy-vs-drift flaw that 2026-06-08 fixed. | [log](sessions/2026-06-07.md) |
| 2026-06-06 | Evaluate "Unreasonable Effectiveness of HTML" for a cross-project status dashboard | Evaluated Thariq's "Unreasonable Effectiveness of HTML" essay for a cross-project dashboard. Decision rule: HTML for human-facing dashboards/comparisons, markdown stays for git-tracked/chained/weekly-iterated content. Surveyed implementing skills (voidful's html-report-skill most relevant). No code built yet. | [log](2026-06-06.md) |
| 2026-05-31 (b) | Standing preference: proactive model switching | Reviewed the current Claude Code model lineup (Opus/Sonnet/Haiku + Plan Mode + /fast) and established the switch heuristic: reasoning-bound→Opus, spec-bound→Sonnet, grind→Haiku. Saved as a standing preference — Claude flags the cheaper tier at task start and reminds to verify via /model at plan↔execute boundaries. | [log](2026-05-31-b.md) |
| 2026-05-31 | Make performer-voice "mood lightener" system global | Promoted the performer-voice "mood lightener" system from project-scoped to global (`~/.claude/VOICES.md`, 21 voices). Established a TARS-style dial (default 40%) and a 🎭 blockquote marker so joking is visually distinct from serious text. Hard rule: never voice bad news. | [log](2026-05-31.md) |
| 2026-05-28 | Apple developer credentials audit + correction | Discovered Apple developer team IDs were swapped in docs (FDMSRXXN73 = paid, not free); rebuilt credentials file with full cert inventory + a New Project Checklist, renewal deadline 2026-09-27. Verified all 4 published apps already used the correct team — code was right, docs were wrong. | [log](2026-05-28.md) |
| 2026-05-16 | SFTPmount Wave 0 Step 3 attempt → pivot to 26.5 re-validation → canonized `37_multi-mac-discipline.md` | SFTPmount Wave 0 Step 3 was blocked (spike context was on the other Mac, not this one) — pivoted to re-validating rev-3 plan corrections against macOS 26.5 (5/6 held, 1 needs an update). Pushed `f146c66`. Canonized `37_multi-mac-discipline.md` (279L, 4 rules) after a 3rd cross-Mac recurrence. Pushed `b372d58`. | [log](2026-05-16.md) |
| 2026-05-15 | Audit punch-list cleanup: AutoRedact orphans + consumer-index backfill + script regex fix | Cleaned up audit punch-list items: split an AutoRedact session file into 4, backfilled 3 consumer-index entries, fixed a whitespace bug in `sync-session-index.sh` (paths with spaces). Reconciled an SFTPmount duplicate-commit collision via `reset --hard`. Audit punch list now 1 item remaining. | [log](2026-05-15.md) |

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
