# Session History

## Active Project
LLM-Directions - Documentation system for AI-assisted development

## Current Status
→ See [PROJECT_STATE.md](../PROJECT_STATE.md)

## Sessions

> Outcome cells are capped at ~300 chars. Older rows (pre-2026-05-15) → [_index-archive.md](_index-archive.md).

| Date | Focus | Outcome | Log |
|------|-------|---------|-----|
| 2026-09-02 | Make Claude-specific model-tier guidance behave correctly when Directions commands run in Codex | Updated the Codex adapter to skip Claude-only model markers and `/model` nudges, translating useful guidance into model strength and reasoning effort without guessing active settings. Next: exercise more shared commands and adapt proven incompatibilities. | [log](2026-09-02.md) |
| 2026-09-01 | Make Directions first-class and easy to invoke in Codex without duplicating its command library | Added the Codex entry point and template, aligned setup docs, and made bare requests such as `/status arrive` and `log clear` the primary convention while retaining `$directions` compatibility. Next: exercise the short forms in consumer projects. | [log](2026-09-01.md) |
| 2026-08-30 | Make the Claude Code Directions workflow usable from Codex without creating a drifting copy | Added a validated `$directions` adapter backed by the live command files and enabled Codex's model/folder/branch/context/token status line. Next: exercise status, checks, and a real project close; adapt only proven incompatibilities. | [log](2026-08-30.md) |
| 2026-08-25 | Extract two deploy patterns from a consumer project (PRIVAT) and clear the identifiers they exposed in this public repo | **#179** — excluding a server-canonical dir from `mirror` (#169's fix) also excludes the `.htaccess` denying it, so session auth is bypassable by direct URL on a site that works. **#180** — `~/.netrc` keys by host so it can't hold two SFTP accounts on one hostname, which is *why* a sibling project's password went inline; Keychain keys by service and carries the username. Both cross-referenced from #169/#99 (`c8d6450`). Masked the Strato account number in `99` + `29_` at HEAD only — history left alone deliberately (`d6dfcea`). Pushed. | [log](2026-08-25.md) |
| 2026-08-20 | Credential audit of the repo + locate where the status-line token gauge's colour thresholds are defined | No credentials found (only deliberate bad-examples). Gauge escalated at 70/95 while `52_`'s canonical table defines 50/70/85/95 — widened to five bands (`b3a9142`); added secret patterns to the public repo's empty `.gitignore` (`c9a5118`); gave `54_` the purge step it lacked (`31d5d88`). All pushed. Index drift (24 missing, 1 orphan) surfaced. | [log](2026-08-20.md) |
| 2026-07-19 | Evaluate Sanzo Wada's colour dictionary as a palette source; pick a trial app | Wada fits the per-app `DESIGN.md` §1 slot, **not** house tokens — it gives harmonies, §2 needs ramps. Four caveats (WCAG, dark-mode inversion, cross-app sameness, plates-vs-values licensing) each with a fix. Trial app = **Magpie**: its neutrals are pure grey + a uniform +4 blue nudge (the §0 "no temperature" diagnosis), `Theme.swift` documents the banned luminance-flip in its own docblock, status colors are Apple's verbatim. Teal accent left alone. Reframe: the *bird* is the source, Wada the vocabulary. **Nothing locked, no files changed** — blocked on the human picking a combination (§10). | [log](2026-07-19.md) |
| 2026-07-18 | Trim PROJECT_STATE + adopt the Claude-Desktop UI critique as the house design system | PROJECT_STATE 151→54 (tip-jar decision rescued to decisions.md first). New `42_design-system.md` (token roles, per-app briefs, banned LLM-tells) + `/check design`; shell-check updated + versioned into repo `skills/` (was live-only); 3-way appearance drift aligned → **dark default + user-selectable light** (#113 picker). Deployed sha-verified; stray #61 ditto-vs-unzip gotcha committed. | [log](2026-07-18.md) |
| 2026-07-13 | M1 Max catch-up: `/status arrive` → reconcile git to origin | Repo was **5-behind + dirty**; per-file hashed all 7 changed files (incl. untracked `skills/`) vs origin → **100% byte-identical** — Syncthing had carried the M4-Pro's committed work over as uncommitted edits. Discarded dups (`restore`×6 + `clean skills/`), guarded on clean tree, `merge --ff-only` `087ec4a..24fd710`. In sync, clean, no `reset --hard`. | [log](2026-07-13.md) |
| 2026-07-13 | A prior session couldn't find the `git-bootstrap` skill — verify, and if missing author + deploy to both Macs | It was a **phantom**: referenced in 5 docs (37_multi-mac, redeploy.sh, PROJECT_STATE, template, decisions) but never authored anywhere. Authored `skills/git-bootstrap/SKILL.md` + wired a **copy-only** Skills section into `redeploy.sh` (never prunes — beside ~263 third-party skills). Mid-task found the **M1 Max had a richer un-versioned copy** (Jul 8, never committed → never propagated) with a "no-origin re-founding" path mine lacked. Repo is PUBLIC → merged to one public-safe version (identity verified-not-hardcoded, no secret paths), deployed **byte-identical** to both Macs (sha e120769). Also reconciled a 2-behind dirty tree (2 dup files discarded + ff, 1 real signing gotcha committed), gitignored WORKING_NOTES. 4 commits pushed. | [log](2026-07-13.md) |
| 2026-07-11 | Evaluate `claude-octopus` for the Directions framework; extract anything reusable without bloat | Cloned + subagent-analyzed it (348 md / 429 sh, v9.52.0): `/octo:` commands are thin shells coercing Claude into a ~2,900-line multi-vendor `orchestrate.sh` (codex/gemini/qwen), consensus inseparable from paid CLIs; its own `debate.sh` concedes agreement≠correctness → **rejected wholesale**. Extracted the one transferable idea (`config/blind-spots/`): a keyword→prompt library injecting the perspectives an LLM structurally forgets. Reimplemented lean as **cookbook #159** — 9-entry seed from OUR OWN gotcha docs (20_/21_/22_/38_/61_/32_/29_/36_ + #62/#147/#153/#158) + a ~15-line jq matcher. Verified: JSON parses, all cross-refs resolve, matcher tested across 6 cases (caught+fixed a jq scoping bug; tightened `actor`→`\bactor\b`). Gitignored `.claude/logs/`. Committed `8a8cb91`, pushed with pending `ac08ab5`; in sync. | [log](2026-07-11.md) |
| 2026-07-02 | M4 Pro: reconcile diverged git + run `redeploy.sh` (execute the M1 Max handoff) | Copy-vs-drift recurred, this time **diverged** (1 ahead / 31 behind): a stale duplicate commit (`fcc801f`, old copy of #152) + a full *uncommitted* copy of work already on origin. Proved the entire working tree byte-identical to `origin/main` except the per-Mac `settings.local.json` — via throwaway-index → `write-tree` → `diff-tree` (one-shot, not per-file) — so origin was a complete superset. `reset --hard origin/main` (dropped commit safe in reflog), settings preserved → `0/0` clean. Then `redeploy.sh` after dry-run: commands **38→15** (pruned 25 retired by git-deletion provenance, kept `mcp-profile`/`preview`), CLAUDE.md → template, hooks wired, all backed up. **Both Macs now on the 15-command set + read-on-demand CLAUDE.md.** Committed + pushed from M4-Pro; effective on restart. | [log](2026-07-02.md) |
| 2026-07-02 | Reproducible cross-Mac redeploy — make the M4 Pro's command/CLAUDE.md deploy one safe command | Wrote `redeploy.sh` (repo root): installs the 13 canonical commands, **prunes the 25 retired ones via git-deletion provenance** (`--diff-filter=D` → removes only files this repo once tracked; keeps independent `mcp-profile`/`preview`), overwrites `~/.claude/CLAUDE.md` from `CLAUDE-GLOBAL-TEMPLATE.md`, delegates hooks to `hooks/install.sh`; backs up commands + CLAUDE.md, `--dry-run`/`--skip-claude-md` flags, idempotent. Fixes the trap that plain `install-directions.sh` copies-without-pruning and won't overwrite an existing CLAUDE.md. Verified by dry-run on M1 Max (kept 2 independents, CLAUDE.md/hooks correct). Updated PROJECT_STATE Resume with the M4 Pro steps. Committed + pushed. | [log](2026-07-02.md) |
| 2026-07-02 | `/execute` OPTIMIZATION-PLAN **Wave 2.2 — commands 36→13** (done directly on Opus, per-target batches) | Consolidated the command system, one atomic commit per merge. **/log**←session-close/depart/handoff/check-index/phase/compound/blockers (imports their content but keeps /log's infer-don't-interrogate style; 8 files→1). **/check** (new; code\|ship\|security)←code-review/quality/reflect/review/minimums; security-audit's 290-line body→`63_security-audit.md` via git mv. **/status**←context(full)/arrive. **/spec**←interview(deep)/example-map(examples); new-feature retired. **/execute**←next + hard gate softened to nudge. **/directions**←update-directions + catalog now generated live from `commands/`. Deleted tdd/build-fix (nuggets→34_/25_)/checkpoint/reorg. Updated executable hooks (session-start/stop.sh, session-start.py) + global template. **Cross-ref sweep:** ~50 `/old-command` refs across 22 files repointed (agent) + README rebuilt to 13 commands. Backpressure: `ls commands`=13, no live dead refs, bash-n/py_compile clean. 8 commits; Wave 2 fully done. **`~/.claude/` redeploy still pending** (staged in repo only). | [log](2026-07-02.md) | Ran 2.1/2.3/2.4 concurrently (disjoint file sets), deferred risky 2.2 (commands). **2.1:** index 50,360→41,603 B (≤45K ✓), split 00-app-shell→#156 (canonical Info.plist home), #00/#16/#89 now cross-ref. **2.3:** deleted/merged 5 docs (03/11/31/41apple/42web) into one-home-per-fact + new 41_ui-vocabulary & 47_project-ui-conventions; trimmed CLAUDE-GLOBAL-TEMPLATE; regenerated router (docs 27–39 reachable). **2.4:** sessions/_index 42K→9.7K & decisions 42K→20.6K into archives; /decide + /log read-rule/budget edits. Fixed all resulting dead links; **repaired an origin dead link** (#155 row shipped in `8c89213` without its file) + backfilled #117 variant. 5 local commits, **not yet pushed**. | [log](2026-07-02.md) |
| 2026-07-02 | `/arrive` on M1 Max: reconcile `behind 14` + dirty tree (copy-vs-drift) losslessly via fast-forward | Reconciled 14-behind dirty tree: per-file hashing found 26 dupes (dropped), 1 unique file kept (#152), fast-forwarded clean. Merged efficiency branch + ran OPTIMIZATION-PLAN Wave 1 (10 fixes, `0081238`). Backfilled missing cookbook-index rows #141/#145/#151/#153 — 154/154 reconciled. Pushed `129d730..cf21478`. | [log](2026-07-02.md) |
| 2026-06-19 | `/status`+`/arrive` token-cost diagnosis → louder model warnings → phase-aware model gating | Root-caused /status token bloat to an undeployed command fix; deployed it. Made model-mismatch warnings loud (red statusline bar, CAPS message). Built phase-aware model gating: /execute gates to Sonnet, /spec+/plan nudge Opus, /session-close reminds next session's model. Synced 10 stale commands. Pushed `9a83888`. | [log](2026-06-19.md) |
| 2026-06-18 | Reconcile a cross-Mac `ahead 4 / behind 4` divergence (duplicate-commit signature) while shipping SearchAway Wave-5 cookbooks | Reconciled a cross-Mac ahead-4/behind-4 divergence: per-file diff proved 3 local commits were byte-identical duplicates already on origin (dropped); kept 2 unique commits (#124 benchmark, #73 HUD gotchas) + untracked #123 via reset --hard + cherry-pick. Pushed `f53058b..9bc9373`. SearchAway 5.3 logged separately. | [log](2026-06-18.md) |
| 2026-06-17 (b) | `/arrive` on M1 Max: reconcile parked cookbooks, then roll Directions out to live config + 3 projects | `/arrive` flagged behind-7 as a "byte-identical phantom" but file hashing found 3 genuine uncommitted cookbooks (#118-120) a prior session left; reconciled with `reset --mixed` (not --hard) to preserve them, pushed `ba70cae`. Rolled Directions out to live `~/.claude/commands/` + synced 3 of 44 vestigial project copies (DiskVerdict, Conjoyn, App-Websites). | [log](2026-06-17-b.md) |
| 2026-06-16 | `/arrive` on M1 Max + clear stale per-Mac wiring reminders | Fast-forwarded `4bad1d9..b49d038` on M1 Max. Corrected stale PROJECT_STATE reminders that still described the M1 Max restore as belonging to "the other Mac" — it was this Mac; removed the stale Next item, rewrote Resume to reflect both Macs wired. | [log](2026-06-16.md) |
| 2026-06-15 | `/arrive` on M4-Pro: reconcile a copy-vs-drift tangle, then commit/push cookbook #110 | Reconciled a copy-vs-drift tangle via per-file hashing, pushed cookbook #110 (deep-link System Settings + prove bundle id against .appex registry) + gotcha updates to #65/#71 (`a740b73`). Rewrote /log as session-close (arg-driven modes). Grew /minimums with an HUD/agent tier. Added cookbook #112 (security-scoped bookmarks). Yielded a numbering collision to #111. | [log](2026-06-15.md) |
| 2026-06-14 (b) | First `AppCitizenshipKit` integration (Conjoyn) + harden the package + cookbook #108 + Directions | First AppCitizenshipKit integration (Conjoyn), used as differential test. Fixed 3 package defects up-stream (stray ellipsis, missing divider, Support/Donate naming collision → "Leave a Tip" framing), published ACK 0.1.1→0.1.2. Verified live Help/App menus via AppleScript. Reconciled a duplicate #106 (renumbered to #107). | [log](2026-06-14-b.md) |

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
