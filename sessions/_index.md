# Session History

## Active Project
LLM-Directions - Documentation system for AI-assisted development

## Current Status
→ See [PROJECT_STATE.md](../PROJECT_STATE.md)

## Sessions

> Outcome cells are capped at ~300 chars. Older rows (pre-2026-05-15) → [_index-archive.md](_index-archive.md).

| Date | Focus | Outcome | Log |
|------|-------|---------|-----|
| 2026-10-28 | Guidance refinements and Codex-primary handoff | Shortcut, interview, testing/debugging and architecture/review/planning guidance refined; local installation verified. Codex is primary. Integration/index/whitespace pass. Next: observe on a real Codex task; E1/recovery remain open. | [log](2026-10-28.md) |
| 2026-10-27 | Research, interview, completion, diagnostics and build handoff | Interview/completion/bounded-debugging guidance implemented and statically reviewed; uncommitted, not deployed. Next preference routing. Earlier research and fresh-build deployment retained. E1/recovery open. | [log](2026-10-27.md) |
| 2026-10-17 | Lean cleanup, size acceptance and local rollout | Listed size increases accepted; both tools deployed and 110 consumer roots migrated to master routing. Verified backups; guides/state/history preserved. E1 open. Next: fresh tool sessions; no host batch scheduled. | [log](2026-10-17.md) |
| 2026-10-16 | Directions review, lean execution and local runner | Local runner committed; 31 tests and frozen fake-host replay pass. E1 open; live transport, corrected host behavior and byte tradeoffs unverified. Claude and Mac-control deferred; no pilot or rollout. Next: local live-transport validation before pilot proposal. | [log](2026-10-16.md) |
| 2026-09-17 | Project status, MultiVibe evaluation and session-history cleanup | Kept model setup unchanged. Indexed February variant; integrated September 8/9 conflict details and archived originals. Mac-control recovery gate remains open; coordinate restart timing when resuming. | [log](2026-09-17.md) |
| 2026-09-10 | Native acquisition and later-boot preparation; M1 Max arrival | Capture/reload passed; marker unchanged. Persistent library and reviewed inspection ready; 478 tests passed/one skip. User deferred restart to a new session; coordinate timing then. Preserve successful acquisition and prior failures. Gate A open. | [log](2026-09-10.md) |
| 2026-09-09 | Native diagnostics; M4-Pro/workflow updates; lean-efficiency spec | Recovery checkpoint preserved; M4-Pro reconciled; wave/status/logging fixes deployed to Codex. Sol/Luna + web review captured as a draft spec with 11 findings/criteria. Next: resolve spec policy choices; consumer trial and native inventory diagnosis remain open. | [log](2026-09-09.md) |
| 2026-09-08 | Record intervention results; reconcile Git and install Codex Directions on M4-Pro | Prior Escape/key cases passed; focus-loss proof remains pending. Fast-forwarded six commits with a recovery stash retained; installed and verified global Codex guidance and the skill link. Next: fresh-session `status arrive`, then the focus-loss fixture. | [log](2026-09-08.md) |
| 2026-09-07 | Prepare and run the live loss-timing recheck | Disconnect and heartbeat loss met detection/drain limits; all test processes closed and evidence saved. Gate A remains incomplete. Next: prepare intervention/focus-loss testing and agree its window. | [log](2026-09-07.md) |
| 2026-09-06 | Verify disconnect/heartbeat-loss stops and add loss-timing evidence | Both drains passed (11.11/10.57 ms); all test processes closed. Added fault timestamps, deadline assertions and teardown-failure checks; 32 offline tests passed. Next: agree a live timing recheck. Gate A remains closed. | [log](2026-09-06.md) |
| 2026-09-05 | Plan shared Mac control and verify the first disposable Stop case | Inventory/protocol complete; built the harness and passed six-character Stop with 12 matching events and 11.72 ms drain. Both processes closed; 16 offline tests passed. Gate A remains closed. Next: schedule disconnect/watchdog tests. | [log](2026-09-05.md) |
| 2026-09-04 | Make Directions first-class for a Codex-primary period using evidence from the ten most recently active projects | Added the Codex deployer and global routing, provider-neutral model/context guidance, current Codex controls and mappings, artifact-freshness gates, and tailored AGENTS.md files for all ten audited projects. Hooks remain an evidence-gated follow-up. | [log](2026-09-04.md) |
| 2026-09-02 | Make Claude-specific model-tier guidance behave correctly when Directions commands run in Codex | Updated the Codex adapter to skip Claude-only model markers and `/model` nudges, translating useful guidance into model strength and reasoning effort without guessing active settings. Next: exercise more shared commands and adapt proven incompatibilities. | [log](2026-09-02.md) |
| 2026-09-01 | Make Directions first-class and easy to invoke in Codex without duplicating its command library | Added the Codex entry point and template, aligned setup docs, and made bare requests such as `/status arrive` and `log clear` the primary convention while retaining `$directions` compatibility. Next: exercise the short forms in consumer projects. | [log](2026-09-01.md) |
| 2026-08-30 | Make the Claude Code Directions workflow usable from Codex without creating a drifting copy | Added a validated `$directions` adapter backed by the live command files and enabled Codex's model/folder/branch/context/token status line. Next: exercise status, checks, and a real project close; adapt only proven incompatibilities. | [log](2026-08-30.md) |
| 2026-08-25 | Extract two deploy patterns from a consumer project (PRIVAT) and clear the identifiers they exposed in this public repo | **#179** — excluding a server-canonical dir from `mirror` (#169's fix) also excludes the `.htaccess` denying it, so session auth is bypassable by direct URL on a site that works. **#180** — `~/.netrc` keys by host so it can't hold two SFTP accounts on one hostname, which is *why* a sibling project's password went inline; Keychain keys by service and carries the username. Both cross-referenced from #169/#99 (`c8d6450`). Masked the Strato account number in `99` + `29_` at HEAD only — history left alone deliberately (`d6dfcea`). Pushed. | [log](2026-08-25.md) |
| 2026-08-20 | Credential audit of the repo + locate where the status-line token gauge's colour thresholds are defined | No credentials found (only deliberate bad-examples). Gauge escalated at 70/95 while `52_`'s canonical table defines 50/70/85/95 — widened to five bands (`b3a9142`); added secret patterns to the public repo's empty `.gitignore` (`c9a5118`); gave `54_` the purge step it lacked (`31d5d88`). All pushed. Index drift (24 missing, 1 orphan) surfaced. | [log](2026-08-20.md) |
| 2026-07-19 | Evaluate Sanzo Wada's colour dictionary as a palette source; pick a trial app | Wada fits the per-app `DESIGN.md` §1 slot, **not** house tokens — it gives harmonies, §2 needs ramps. Four caveats (WCAG, dark-mode inversion, cross-app sameness, plates-vs-values licensing) each with a fix. Trial app = **Magpie**: its neutrals are pure grey + a uniform +4 blue nudge (the §0 "no temperature" diagnosis), `Theme.swift` documents the banned luminance-flip in its own docblock, status colors are Apple's verbatim. Teal accent left alone. Reframe: the *bird* is the source, Wada the vocabulary. **Nothing locked, no files changed** — blocked on the human picking a combination (§10). | [log](2026-07-19.md) |
| 2026-07-18 | Trim PROJECT_STATE + adopt the Claude-Desktop UI critique as the house design system | PROJECT_STATE 151→54 (tip-jar decision rescued to decisions.md first). New `42_design-system.md` (token roles, per-app briefs, banned LLM-tells) + `/check design`; shell-check updated + versioned into repo `skills/` (was live-only); 3-way appearance drift aligned → **dark default + user-selectable light** (#113 picker). Deployed sha-verified; stray #61 ditto-vs-unzip gotcha committed. | [log](2026-07-18.md) |
| 2026-07-13 | M1 Max catch-up: `/status arrive` → reconcile git to origin | Repo was **5-behind + dirty**; per-file hashed all 7 changed files (incl. untracked `skills/`) vs origin → **100% byte-identical** — Syncthing had carried the M4-Pro's committed work over as uncommitted edits. Discarded dups (`restore`×6 + `clean skills/`), guarded on clean tree, `merge --ff-only` `087ec4a..24fd710`. In sync, clean, no `reset --hard`. | [log](2026-07-13.md) |

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
