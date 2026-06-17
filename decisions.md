# Decisions Log

This file tracks the WHY behind technical and design decisions.

---

## Template

### [Date] - [Decision Title]
**Context:** [What situation prompted this decision?]
**Options Considered:**
1. [Option A] - [pros/cons]
2. [Option B] - [pros/cons]

**Decision:** [What we chose]
**Rationale:** [Why we chose it]
**Consequences:** [What this means going forward]

---

## Decisions

### 2026-06-13 - Cross-project status view: disposable `dashboard.html`, not a committed `project.json` generator

**Context:** A "current state of all my work" view had been parked through two sessions with two competing designs. **2026-03-24** designed a bottom-up *committed generator*: every project emits `docs/site/index.html` + a `project.json` data contract, a master aggregator at `__DIRECTIONS/site/` scans all the `project.json` files, with auto-triggers wired into `/setup` and `/log`. **2026-06-06** (after reading Thariq Shihipar's "Unreasonable Effectiveness of HTML") proposed the opposite: a top-down, on-demand, *disposable* `dashboard.html` — one agent/script reads every project's `PROJECT_STATE.md` + git and emits a single static page; gitignored, no per-project files, no triggers. The standing instruction was "build one, not both." This session resolved it and built the proof-of-concept.

**Options Considered:**
1. **Committed `project.json` generator (2026-03-24)** — per-project committed artifacts + master aggregator + `/setup`/`/log` triggers.
   - Pros: always-fresh (regenerates on every log); structured data contract reusable by other tools.
   - Cons: reintroduces exactly what sank every prior web-dashboard attempt — standing maintenance surface (N committed `project.json` files that drift, two trigger integrations to keep working, an aggregator to maintain). Also violates its own motivating principle: the HTML-effectiveness decision rule says *markdown stays for anything git-tracked or iterated weekly* — committed, weekly-regenerated state files are precisely that case wearing an HTML hat.
2. **Disposable gitignored `dashboard.html` (2026-06-06)** — one top-down script, scans `PROJECT_STATE.md` across the fleet, emits one self-contained page. Gitignored script + output. No per-project files, no triggers.
   - Pros: zero standing surface; reversible; the scan itself measures whether a dashboard is even worth keeping (how many projects have fresh vs. drifted state); faithful to the essay's HTML-for-human-facing-dashboards rule.
   - Cons: snapshot only (accurate at generation time); must be re-run manually.

**Decision:** Option 2. Built `dashboard.py` (stdlib-only, ~Python 3.9) + its `dashboard.html` output, both **gitignored** alongside the existing local-tool precedent (`docs-browser.html`, `docs.sh`). Top-down: scans `~/ProgrammingProjects/<category>/<project>/docs/PROJECT_STATE.md` (+ the master at repo root), parses Phase/Focus/Blockers/one-liner, adds last-session date (from `sessions/*.md` filenames) and last git commit, emits one dark self-contained page with client-side search + phase/blocked filter chips, sorted by most-recent activity so stale projects sink. Option 1 (the 2026-03-24 committed generator) is **retired** — not building it.

**Rationale:** Past web dashboards failed because they were *web apps* (server/build/committed artifacts to maintain), and Option 1 is the same shape. Option 2 has no standing surface, is reversible, and respects the principle that motivated the whole idea. Starting cheap and graduating only if it earns its keep is the correct risk order; starting heavy and discovering it wasn't worth it is the expensive mistake. If it proves repeatedly useful it can graduate to a `/dashboard` command or `voidful/claude-html-report-skill` later.

**Consequences:**
- The scan is itself a **drift detector**: on first run, 39/47 projects exposed a parseable `**Phase:**`, 34/47 a `**Focus:**`; the 6 with neither (ScreenshotFromVideos, PhoneticAlphabet, MousePlus, AutoRedact, LiveInterviewTool, GPSvideo) have `PROJECT_STATE.md` drifted from the lean template. The dashboard surfaces these for cleanup. Genuinely blocked at build time: zPackages.
- Parser must tolerate format variance: `**Project:**` is often `Name — one-liner` / `Name → New (note)` (split on the first ` — `/` · `/` (`); `**Blockers:**` is usually omitted when empty and, when present, frequently reads `none for v1 …` / `none for dev …` (treat any "none…" prefix as no blocker). Both were real bugs caught on first run.
- Nothing is committed and nothing touches consumer repos — no `project.json` written anywhere, no `/setup`/`/log` changes. Re-run with `python3 dashboard.py && open dashboard.html`.
- Decision rule reaffirmed: **HTML for human-facing dashboards/comparisons; markdown stays in git repos and for agent-consumed docs.** Do NOT HTML-ify cookbook or Directions docs.

---

### 2026-05-14 - `/session-close` is a six-step checklist, not silent automation

**Context:** Audit found four recurring drift patterns: 15% of recent logs lack a Next Session pointer, PROJECT_STATE.md timestamps lag by weeks (Penumbra 3 weeks), decisions stay buried in session prose (LUCESUMBRARUM's re-pull-and-migrate, YTdl's `Window` swap, Group Alarms model invariants), `_index.md` falls out of sync (16/29 projects). All four are end-of-session hygiene failures. Q1's script catches `_index.md` drift retroactively; Q3 needs to prevent all four at source.

**Options Considered:**
1. **Silent automation** — `/session-close` rewrites everything automatically (auto-add a Next Session stub, auto-extract every "decision" bullet from the session log into `decisions.md`, auto-bump timestamps, auto-fix index).
   - Pros: zero user effort; can't be forgotten.
   - Cons: Next Session content can't be auto-generated meaningfully ("TBD" is worse than nothing); auto-copying one-line session bullets into `decisions.md` creates poor ADRs lacking Context / Alternatives / Rationale; silent auto-edits surprise the user.
2. **Pure read-only audit** — report what's wrong, fix nothing.
   - Pros: maximum safety; mirrors `/check-index`.
   - Cons: doesn't actually close the loop. User has to do the work anyway.
3. **Six-step interactive checklist** — Claude walks each step, makes minimal stub edits where unambiguous (e.g. bump Last-Updated), but PROMPTS for content that needs human judgment (Next Session text, decisions.md entries, Focus rewrites).
   - Pros: prevents all four drift patterns at source. The friction is a feature: it makes hygiene visible.
   - Cons: not invocable on every session-end (user will skip when in a hurry). Mitigation: ship `/check-index` separately as the lightweight version.

**Decision:** Option 3. Commands lives at `commands/session-close.md` (122 lines, six steps).

**Rationale:** The audit's evidence is unambiguous about why decisions are missing from `decisions.md` — they're summarised in session prose because writing a proper ADR is more work than typing one bullet. Silent automation would copy those summaries verbatim and make `decisions.md` *worse*. The right intervention is to **make ADR-shaped entries the path of least resistance at the moment the human is most likely to remember the Context** (immediately after the decision, while closing the session). Same logic for Next Session: a stub `"TBD"` is worthless; a prompt that says "what's actually next?" while the work is still fresh is when the answer is cheap.

**Consequences:**
- `/session-close` does NOT replace `/log` (which is for mid-session updates). They're complementary: `/log` records progress; `/session-close` enforces handoff hygiene.
- `/check-index` becomes the lightweight version: read-only, runnable anytime, no decisions/state work.
- Six-step structure becomes a template — if future audits surface additional drift patterns, they can be added as Step 7/8 without restructuring.
- The audit's finding that 15% of logs miss Next Session is the baseline; if it doesn't drop after a few weeks of `/session-close` adoption, the command is failing to be invoked. That's the success metric.

---

### 2026-05-14 - Ship `sync-session-index.sh` + `/check-index` to fight `_index.md` drift

**Context:** Cross-project audit (2026-05-13) found that 16 of 29 consumer projects had `_index.md` drift — either session logs on disk with no index row (the common case: LUCESUMBRARUM +9, AvidMXFPeek +8, ePubReader +6) or index rows pointing at files that no longer exist (the dangerous case: DownKeyCounter had 11 stale rows at audit time, though it's since been rebuilt). The master Directions repo itself has 9 missing entries in its own `_index.md`. Drift was the single most pervasive hygiene leak surfaced by the audit, and the only sustainable fix is automated detection.

**Options Considered:**
1. **Manual hygiene reminders only** — update `00_base.md` to say "always update _index.md when you create a session log".
   - Pros: zero code.
   - Cons: doesn't catch existing drift; relies on human discipline that has demonstrably failed across 16 projects.
2. **A git pre-commit hook** in every consumer project — refuse commits with drift.
   - Pros: forces hygiene at source.
   - Cons: high friction; users can `--no-verify` past it; doesn't help projects without git.
3. **A standalone audit script + slash command** users invoke when they remember (or periodically).
   - Pros: low friction; reversible (`--fix` is opt-in); catches existing drift; works without git.
   - Cons: requires the user to run it.
4. **A scheduled `/loop` job** that runs the check weekly.
   - Pros: zero friction.
   - Cons: requires `/loop` adoption per project; overkill for most projects.

**Decision:** Option 3 first, with the door open to Option 4 layering on top later.

Implementation:
- `scripts/sync-session-index.sh` (bash 3.2-compatible, 154 lines). Exit 0 = clean, 1 = drift, 2 = error.
- Supports both index formats observed in consumer projects: markdown-link form (`[2026-05-13](2026-05-13.md)`) AND bare-date row form (`| 2026-05-13 | …`). The audit's claim of 100% link-form consistency was wrong; DownKeyCounter and LUCESUMBRARUM use bare-date rows.
- `--fix` mode: adds placeholder rows for missing files only. Never auto-removes orphans (they could be typos, moved files, or work in progress).
- `commands/check-index.md` (52 lines) — `/check-index` slash command wrapping the script with usage docs.

**Rationale:** Detect first, fix-with-consent second. Removing orphan rows is dangerous because they may represent real work the user is mid-flight on; an auto-remover would destroy that information. Adding placeholder rows for missing files is safe because the source-of-truth (the file) still exists; the row is just a pointer that fell behind.

The bash-3.2 constraint matters: macOS ships with bash 3.2 and many users won't have a newer one. The script uses POSIX-style arrays and avoids `mapfile`, associative arrays, and `${var^^}` for that reason.

**Consequences:**
- Consumer projects can run `docs/scripts/sync-session-index.sh` to verify their index. Next rsync from master will deliver the script.
- The master's own 9 missing entries are now diagnosed and can be backfilled (added to next-session queue).
- A new pattern surfaced during testing: 3 consumer projects share the **same 6-entry missing set** (`2026-01-{23,24,29}`, `2026-02-{02,18,27}`). These are master Directions session-log dates that appear to have been seeded into consumer `docs/sessions/` during early bootstrap. The current rsync-with-excludes (2026-05-01) addresses future bootstrap but doesn't clean up the historical contamination. A separate cleanup pass may be warranted, but is **not** what `--fix` is for — those rows would document the master's framework history inside consumer projects, which is misleading. Recommend: delete the spurious files from consumer `docs/sessions/`, then re-run the index check.

**Addendum (2026-05-14, same day):** Performed the contamination cleanup on the 3 named consumers (LUCESUMBRARUM, AvidMXFPeek, ePubReader). Used `cmp -s master/<date>.md consumer/<date>.md` to confirm bit-identity before each `rm` — no local work risked. Total: **23 files removed** (not 18 as initially scoped). The cleanup happened in 2 rounds because round-1's re-audit surfaced additional `2026-04-*` dates that were ALSO identical to master. The revised understanding: bootstrap contamination is "every master session that existed at the consumer's last sync time," not just the 6 dates the original audit flagged. All 3 consumers now `✓ in sync`. The ~7 other consumers with drift in the original audit likely have the same pattern at smaller scale and can be cleaned with the same `cmp -s` + `rm` recipe.

**Addendum 2 (2026-05-14):** Swept the other 7 candidate consumers (AutoRedact, MenuBarPLUS, MousePlus, SFTPmount, Group Alarms, KinoBerlin, apps.lucesumbrarum.com). Result: only AutoRedact had real contamination (6 files removed, same 6-date initial-audit set). The other 6 had drift but NOT contamination — their "missing" entries are legit local suffix-variant sessions (`2026-04-05-s3`, `2026-05-03-followup`, `2026-05-01-a`, `2026-05-09-spike`, `2026-01-16-tmdb-ratings-plan`, etc.) that simply aren't indexed yet — work for `/session-close` or `/check-index`, not `rm`. So the "every-master-session" theory from Addendum 1 turns out to be only partially true: the contamination is concentrated in consumers that bootstrapped between Jan-Feb 2026 (LUCESUMBRARUM, AvidMXFPeek, ePubReader, AutoRedact); consumers bootstrapped later picked up little or none.

**Side-discoveries from the sweep:**
1. **Whitespace bug in `sync-session-index.sh`** — `find … | xargs -n1 basename` whitespace-splits paths, so `"Group Alarms"` produced 24 false-positive `"Group"` entries. Fixed via `find … -execdir basename {} .md \;` which keeps each path intact. Bash 3.2-compatible; tested on all paths (with and without spaces).
2. **4 Syncthing sync-conflict files** across MenuBarPLUS, SFTPmount, AspectRatioUnifier (`.sync-conflict-YYYYMMDD-HHMMSS-XXXXXXX.md` and `_index.sync-conflict-…`). Each one contains *divergent* content from its base, so they're real work needing manual merge (not auto-deletion). Pattern: while one Mac was editing `2026-05-09.md`, another was editing the same file; Syncthing kept both versions. Not bootstrap contamination but worth noting.
3. **AutoRedact orphan rows** — after removing 6 contaminated files, AutoRedact's `_index.md` still references 3 rows (`2026-04-05b/c/d`) whose files don't exist on disk. These predate this session; either the files were never created or were cleaned up earlier. By Q1's design, orphans are NOT auto-removed (they may be work-in-progress); flagged for separate user decision.

**Addendum 3 (2026-05-14):** Merged the 4 surfaced sync-conflict files. Structural analysis (base vs conflict size, mtime, unique-line counts) revealed all 4 were the same pattern: **the base file was a strict superset, the conflict was an obsolete earlier snapshot**. Specifically: in 3 of 4 cases the conflict had 0 lines of unique content (just stopped at line N while the base continued to line M); in the 4th case (`MenuBarPLUS/_index.md`) the conflict's 1 unique line was the same logical row with a stale metric — `(562 + 370 lines)` — that the base subsequently updated to `(562 + 444 lines)` along with substantial additional row content. Merge outcome: **keep base as-is, delete conflict** — zero information loss. All 4 conflict files deleted. The Syncthing pattern is now understood: when two Macs edit the same file and one keeps writing past where the other paused, Syncthing keeps both copies even though one is a strict subset of the other. The cleanup recipe is: `diff base conflict | grep -c '^>'` — if 0, safe to delete conflict.

**Out-of-scope discovery (2026-05-14):** `find` for `*.sync-conflict-*` revealed 8 more files outside `docs/sessions/` that were missed by the audit's session-log-focused scope: 3 in `.git/` directories (KinoBerlin, PDF2Calendar — DANGEROUS to auto-touch; Syncthing arguably shouldn't be syncing `.git/` at all), 2 in `.claude/settings.local.sync-conflict.json` (MenuBarPLUS, SFTPmount — significantly diverged), 1 in `AspectRatioUnifier/docs/PROJECT_STATE.sync-conflict.md` (both sides have unique content), 2 Swift source files in AspectRatioUnifier's project tree (`ContentView`, `AppState`). These are intentionally NOT handled in this session — they need per-file user judgment and `.git/` modifications should never be automated.

---

### 2026-05-14 - Archive `/0-DIRECTIONS/docs/` (second-generation parallel master)

**Context:** After archiving the 2026-01-07 monolith yesterday, `/0-DIRECTIONS/docs/` was the only remaining ambiguous artifact at the umbrella-dir level. It carried the same numbered-doc shape as the live `__DIRECTIONS/` (`00_base.md`, `01_quick-reference.md`, …, `commands/`, `sessions/`, `skills/`, `decisions.md`, `PROJECT_STATE.md`) but was a smaller, older snapshot — 28 numbered files vs ~45 in `__DIRECTIONS/`, missing all material added after 2026-02-06 (`27_mcp-gotchas.md`, `33_app-minimums.md`, `34_testing.md`, `35_ai-code-quality.md`, `52_context-management.md`, `53_llm-failure-modes.md`, `54_security-rules.md`, `60_model-selection.md`, plus the cookbook). Notably it still carried the duplicate `55_` prefix that was fixed in `__DIRECTIONS/` on 2026-05-13 — a useful tell that this was a snapshot before the rename.

The naming collision (`/0-DIRECTIONS/docs/00_base.md` vs `/0-DIRECTIONS/__DIRECTIONS/00_base.md`) was the highest-leverage cognitive-load source remaining: any future Claude session looking for canonical content could land on the older copy and use stale guidance.

**Options Considered:**
1. **Leave it** — It's small (452 KB), been there for months without confusion.
   - Pros: Zero work.
   - Cons: Naming ambiguity persists. Predictably the source of "which one is canonical?" confusion.
2. **Diff against `__DIRECTIONS/`, port any unique content forward, then delete**
   - Pros: Salvages anything unique.
   - Cons: An hour of careful diffing. Likely outcome: nothing unique survives, since `__DIRECTIONS/` is the strict superset.
3. **Archive in place alongside the monolith**
   - Pros: Same low-risk pattern as yesterday. Reversible. Indexed via ARCHIVE.md. No content loss.
   - Cons: 452 KB more in `__archive/` (negligible).

**Decision:** Option 3. Confirmed via grep that no master refs into `/0-DIRECTIONS/docs/` exist (only refs were in yesterday's session log + decisions.md, both meta-references about the archive itself). Moved to `__archive/2026-02-06-pre-final-flatten-docs/`. Updated `ARCHIVE.md` with a top-of-list entry describing what it was and why it was retired.

**Rationale:** The bar to keep something live in the umbrella dir should be "actively used by current sessions." This wasn't (last touched 2026-02-06; nothing referenced it). Archiving with an indexed restore path is strictly better than deleting.

**Consequences:**
- `/0-DIRECTIONS/` top level now: `__DIRECTIONS/`, `XcodePreviews/`, `__archive/`, `HANDOFF-TO-OTHER-MAC-2026-04-26.md`, `claude-code-for-the-rest-of-us.pdf` — 5 functional entries (plus `.DS_Store`). Maximum signal, minimum noise.
- `__archive/ARCHIVE.md` is now the single source of truth for "where did the old docs go" — useful for any future archeology.
- `__archive/` total: ~12.5 MB, two dated subfolders.

---

### 2026-05-13 - Archive dormant `/0-DIRECTIONS/` doc monolith

**Context:** The umbrella directory `/Users/sim/ProgrammingProjects/0-DIRECTIONS/` contained 19 topical doc directories (`AI-LLM/`, `ARCHITECTURE/`, `CHANGELOGS/`, `CODE-REVIEWS/`, `CONTRIBUTING/`, `DEBUGGING/`, `ENGINEERING-GUIDES/`, `GUIDES/`, `LICENSES/`, `PORTFOLIO/`, `READMES/`, `RESEARCH/`, `SECURITY/`, `SESSION-LOGS/`, `TECHNICAL-REFERENCES/`, `TEMPLATES/`, `TODO-PLANS/`, `_Analysis/`, `_reddit-wisdom/`) plus a `txt/` source dump (476 files) and 3 loose Jan-7 session files — ~600 files, ~12 MB total, all frozen on 2026-01-07 (except `_Analysis/` at 2026-03-13). Audit revealed this material had been consolidated into the numbered `__DIRECTIONS/*.md` docs (00–60) during the 2026-01-23 "system improvement analysis" session, but the original monolith was never archived. Sitting next to the live `__DIRECTIONS/` it created cognitive load and discoverability friction: 30 top-level entries when only 4 mattered.

**Options Considered:**
1. **Delete outright** — Reclaim 12 MB.
   - Pros: Cleanest. Maximum signal-to-noise at root.
   - Cons: Irreversible. Some material may not be fully absorbed; risk of losing context history.
2. **`tar czf` + delete** — Compress into one tarball.
   - Pros: Reduces noise to one file.
   - Cons: Requires extracting to look at anything; harder to grep across when researching history.
3. **Move to `__archive/<date>-<reason>/` with a summary `ARCHIVE.md`** — Keep accessible but out of the way.
   - Pros: Reversible (`mv` back). Greppable. Self-documenting via ARCHIVE.md mapping each item to its current location.
   - Cons: Still uses ~12 MB. Two extra directories at root (`__archive/` and the dated subdir).

**Decision:** Option 3. Moved everything to `/0-DIRECTIONS/__archive/2026-01-07-pre-flatten-monolith/` and wrote `/0-DIRECTIONS/__archive/ARCHIVE.md` documenting each item, its file count, what superseded it in `__DIRECTIONS/`, and how to restore.

**Rationale:** Reversibility matters more than reclaiming 12 MB. Future sessions may need to grep the old material when answering "where did X come from"; archived-with-index is far better for that than archived-as-tarball. The dated subfolder name (`2026-01-07-pre-flatten-monolith`) makes it obvious why these files exist together and when they were retired.

**Consequences:**
- `/0-DIRECTIONS/` top level: 30 entries → 7. The live trees (`__DIRECTIONS/`, `XcodePreviews/`) are now visually unambiguous.
- `__archive/ARCHIVE.md` becomes the canonical map between old paths and new (e.g. "old `DEBUGGING/` content lives in `__DIRECTIONS/{25_troubleshooting, 31_debugging}.md` now").
- **Open follow-up:** `/0-DIRECTIONS/docs/` is also a pre-flatten artifact (same numbered structure as `__DIRECTIONS/`, last modified 2026-02-06) but was left in place pending a separate decision — its position relative to `__DIRECTIONS/docs/` (which doesn't exist) is less risky but still creates a naming ambiguity.
- `HANDOFF-TO-OTHER-MAC-2026-04-26.md` and `claude-code-for-the-rest-of-us.pdf` left at root as recent / reference material.

---

### 2026-05-13 - Rename `55_ui-changes-protocol.md` → `36_ui-changes-protocol.md`

**Context:** Master Directions had two files sharing the `55_` prefix (`55_spec-template.md` and `55_ui-changes-protocol.md`). Discovered during a cross-project audit that surfaced framework structural issues. Duplicate numeric prefixes hurt discoverability and break the implicit "numbered docs map" mental model.

**Options Considered:**
1. **Shift `55_spec-template.md` to `56_` and renumber 56–60 forward**
   - Pros: Keeps `ui-changes-protocol` in the 50s near other planning/spec docs.
   - Cons: Breaks 5 file names + every incoming reference in commands, skills, and consumer copies. High blast radius.
2. **Rename `55_ui-changes-protocol.md` to an open number in a fitting range**
   - Pros: Single rename. The 30s range is for process discipline (`30_production-checklist`, `31_debugging`, `32_git-workflow`, `33_app-minimums`, `34_testing`, `35_ai-code-quality`); `ui-changes-protocol` is a process doc (Explore → Propose → Confirm → Implement). 36 is the lowest open slot — semantic fit + low blast radius.
   - Cons: Consumer projects retain old `55_…md` copies until next `install-directions.sh` resync.

**Decision:** Option 2 — `git mv 55_ui-changes-protocol.md 36_ui-changes-protocol.md`.

**Rationale:** One rename + four reference updates (`CLAUDE-GLOBAL-TEMPLATE.md:234`, `commands/new-feature.md:69`, `commands/plan.md:35`, self-ref in `36_ui-changes-protocol.md:114`) — entirely contained in master. Consumer command files reference filenames as plain strings, so they still resolve locally against their local `55_…md` copy. No consumer breakage. Next time a consumer runs the install/sync script they will pick up the renamed file; the old file can then be cleaned up by that script.

**Consequences:**
- Master is now clean (`grep -r "55_ui-changes-protocol"` returns zero hits).
- Numbered-doc semantic ranges become slightly more legible: 30s = process discipline.
- A future TODO: rsync/install script should `--delete` outdated numbered files in consumer `docs/` so stale `55_ui-changes-protocol.md` copies don't accumulate alongside the new `36_…md` after sync.

---

### 2026-01-25 - Integrate everything-claude-code Features

**Context:** Discovered affaan-m/everything-claude-code repository - a battle-tested Claude Code configuration with agents, commands, and workflows. Evaluated for complementary features to add to Directions.

**Options Considered:**
1. **Full adoption** - Replace Directions with everything-claude-code
   - Pros: More comprehensive command set, hooks system
   - Cons: Different philosophy (TypeScript/web-focused), loses Directions' strengths

2. **Selective integration** - Cherry-pick complementary features
   - Pros: Best of both worlds, no breaking changes
   - Cons: Maintenance of adapted code

3. **No integration** - Keep systems separate
   - Pros: Simpler, no merge work
   - Cons: Miss valuable workflow improvements

**Decision:** Selective integration (Option 2)

**Rationale:**
- Directions is stronger at: discovery interviews, architecture mapping, Swift/macOS gotchas, progressive context
- everything-claude-code is stronger at: code review automation, TDD workflow, build error handling
- The features complement rather than compete

**What was integrated:**
- `/code-review` command - Automated quality checklist before commits
- `/tdd` command - Test-driven development workflow
- `/build-fix` command - Xcode/Swift error resolution
- `54_security-rules.md` - Security checklist reference

**What was NOT integrated:**
- Hooks system (Directions uses session logs instead)
- Memory persistence (Directions uses PROJECT_STATE.md)
- MCP configs (too specific to their web stack)
- Package manager setup (Directions is Swift-focused)

**Consequences:**
- Three new commands available for quality workflows
- Attribution to source repo in adapted files
- May adopt more features in future if valuable

## Condensed Log (summaries — migrated from PROJECT_STATE.md, 2026-06-09)

> One-paragraph decision/outcome summaries, newest first. Lighter than the full ADRs above; kept
> verbatim here so PROJECT_STATE.md can stay a lean digest. Some overlap with ADRs above is intentional.

- 2026-06-17: **Per-project `docs/` Directions are vestigial — rely on the master path, sync on demand only.** Surveyed all 44 projects carrying a `docs/00_base.md` Directions copy: every one is "behind" master (none had ref doc #62; cookbook tops scattered 40→109 vs master 120; 16 have no `cookbook/` dir at all). **Decided NOT to mass-sync.** Rationale: the live lookup paths don't read the project copy — the global `CLAUDE.md` cookbook lookup resolves the index + sub-files from the **master repo** (`…/__DIRECTIONS/`), and slash commands run from `~/.claude/commands/` (or a project's own `.claude/`), never from `docs/commands/`. So the per-project `docs/` Directions are reference snapshots nothing on the hot path consults — the 16 cookbook-less projects working fine prove it. Mass-running `/update-directions` across 44 repos = pure git churn. Sync a project's `docs/` only when it must be self-contained; otherwise let master be the single source (same read-on-demand principle as the 2026-06-08 copy-vs-drift fix). Synced only 3 active projects this session (DiskVerdict/Conjoyn/App-Websites) on explicit request, docs-only.
- 2026-06-17: **`reset --mixed` over `reset --hard` when the session-start "phantom" banner under-counts.** The start-up oracle hashes dirty *tracked* paths against origin and, finding them byte-identical (Syncthing-carried), advised `git reset --hard origin/main` as "lossless." It missed two things a `--hard` would have destroyed: an index edit to a tracked file (`PATTERNS-COOKBOOK.md`) that *differed* from origin, and genuine *untracked* work (cookbooks #118–120) from a prior session that never `/depart`-ed. **Rule: when `/arrive` says behind-N with local changes, verify file-by-file (`git hash-object <f>` vs `git rev-parse origin/main:<f>`) before any `--hard`; if anything differs, reconcile with `git reset --mixed origin/main`** — it advances HEAD + index to origin while leaving the working tree sacred, collapsing the phantoms to "clean" and surfacing exactly the real delta to commit. Never blind-`--hard` while any path differs from origin. (Mirrors the git-bootstrap skill's `--mixed`-then-`git status` discipline.)
- 2026-06-13: **Added `/arrive` + `/depart` — the cross-Mac handover pair.** `/arrive` = per-project, plain-language version of the session-start git pre-flight (fetch → behind/ahead → read the other Mac's last commit + where you left off; read-only, offers a pull). `/depart` = `/session-close` hygiene + commit + push, framed for switching machines. **Key decision: machine identity lives in git, not in a tracked file.** `/depart` stamps each commit with a `Handoff-from: <Mac>` trailer (immutable, conflict-free); `/arrive` reads it back via `git log --format='%(trailers:key=Handoff-from,valueonly)'`. Rejected the user's first instinct (write "pushed at HH:MM on MacN" into PROJECT_STATE/state `.md`) as redundant with git metadata *and* a sync-conflict footgun (two Macs editing one line — the exact pattern Rule 1 fights). Machine name resolves from `~/.claude/this-mac` (one-line label, **outside** the Syncthing folder so it never travels) with `scutil --get LocalHostName` as fallback — so it works with zero setup. Commands live in `commands/`, copied to `~/.claude/commands/` by `/update-directions` (the other Mac picks them up that way). Verified end-to-end on this Mac (git 2.50; trailer round-trip proven).
- 2026-06-08: **Killed the copy-vs-drift flaw with a read-on-demand model.** Universal Directions docs (`00–61`) are now the single source of truth in the master repo, surfaced to every running project via a topic→doc **Directions Index** in global `~/.claude/CLAUDE.md` (+ tracked mirror in `CLAUDE-GLOBAL-TEMPLATE.md`). `/setup` stops copying them and scaffolds only project-specific files; the "is Directions set up?" sentinel moved `00_base.md` → `PROJECT_STATE.md`. Rationale: copied docs in N projects silently drift and never get new house-style — same problem packages solved with path-deps (single source of truth). Discovered live proof mid-task: the template and live global config had themselves drifted apart. Also reconciled a cross-Mac branch divergence (origin had duplicate cookbook #80/#81 from another Mac; local was a clean superset → `-s ours` merge, pushed `effe3f2`).
- 2026-06-06: **Evaluated Thariq's "Unreasonable Effectiveness of HTML" for a cross-project status dashboard.** Thesis (Anthropic, 2026-05-09): human-facing agent output → self-contained `.html` beats markdown. Decision rule kept: HTML for human-facing/comparisons/dashboards; **markdown stays for short outputs, chained agents, anything git-tracked or iterated weekly.** Surveyed implementing skills (`dogum/html-artifacts`, `voidful/claude-html-report-skill` = reports→GitHub Pages, most relevant). **Diagnosis:** past web-dashboard attempts failed because they were *web apps* (server/build to maintain); the artifact pattern has none — agent reads filesystem, emits one static html. Cautions: keep dashboard disposable/gitignored, don't HTML-ify cookbook/Directions docs, usefulness gated by PROJECT_STATE quality. No code built; PoC `dashboard.html` pending go-ahead. See open question above + connects to 2026-03-24.
- 2026-05-31: **Performer-voice "mood lightener" system made global.** Imported the user's `VOICES.md` (21 comedian/character voices) and promoted it from project-scoped to global: full roster + rules at `~/.claude/VOICES.md`, loaded via a new "Performer Voices (Mood Lightener)" section in `~/.claude/CLAUDE.md` (applies in every project). TARS-style dial, default **40%** (user adjusts: "go to 80% voices" / "drop to 20%"); voiced text wrapped in a `🎭 *(VoiceName, NN%)*` blockquote marker so the user can see when it's a joke; plain text = serious. Hard rule: never voice genuinely bad news (data loss / security / destructive ops). Project memory `feedback_voice-level-dial.md` keeps a pointer to the global home.
- 2026-05-28: **Corrected Apple Developer team IDs in `~/.claude/apple-developer.md`.** `FDMSRXXN73` = paid Individual Developer Program (renewal 2026-09-27); `H56HM4MMZS` = free Personal Team. Docs had these swapped since 2026-03-10; all published apps were always on the correct team. Credentials file rebuilt with full cert inventory + New Project Checklist. **Watch date: renew membership before 2026-09-27.**
- 2026-05-16 (later): **Canonized `37_multi-mac-discipline.md`** (279L, slot 37 — closes the only open 30s slot). Three recurrences in two weeks pushed the cross-Mac pattern past the "interesting incident" threshold: `.claude/settings.local.json` union-merge (2026-05-14), SFTPmount duplicate spike commit detected at push (2026-05-15), M1-vs-M4 spike-context discovery (2026-05-16). Doc structure mirrors `39_libsql-turso-sync.md`: mental model + Rule 1 (`git fetch` first when crossing Macs) + Rule 2 (verify machine-specific OS state on the actual machine; record host identity in spike journals) + Rule 3 (union-merge for accumulating non-tracked files; `.stignore` to prevent recurrence) + Rule 4 (pivot-when-blocked-by-physical-machine pattern, productive substitute for redoing setup) + 30-second pre-flight template + 8-row cheatsheet. Inbound refs wired in `00_base.md` and `01_quick-reference.md`. Master commit `b372d58` pushed.
- 2026-05-16: **Real-product session on SFTPmount.** Attempted Wave 0 Step 3 from M1 Max; pre-flight surfaced spike-context-on-other-machine (no `FSKitExp.app` here, no `~/scratch/sftpmount-spikes/`, no `fskitd` activity 2026-05-09 in retained log — confirmed via three diagnostic methods that the spike actually ran on M4 Pro per journal header). Pivoted to read-only re-validation of rev-3 plan corrections against macOS 26.5: three parallel checks (Info.plist+entitlements diff, log archaeology, FSKit framework surface). Result: 5/6 rev-3 corrections still hold; correction #5 needs `LSMinimumSystemVersion` 26.4 → 26.5; surfaced 6 additional Info.plist keys to mirror Apple's stock + 1 entitlement decision (drop `com.apple.security.network.server` for SFTP). Findings written into `01_Project/spike-r2-fskitd/NOTES.md` as a 5-item rev-3 punch list. SFTPmount commit `f146c66` pushed. **Cross-Mac collision pattern recurred a 3rd time** (the initial M1-vs-M4 confusion); now warrants its own Directions doc. **Pivot-when-blocked-by-physical-machine pattern proven**: when primary task needs other hardware, read-only validation that informs the next attempt is a productive substitute.
- 2026-05-15: **Audit punch list fully closed.** AutoRedact 4-way split (filesystem only; `2026-04-05.md` 177L → 4 per-session files 43/57/44/34L; `.pre-split-backup` retained). Consumer-index backfills shipped: MousePlus `2026-05-01-a` (local), SFTPmount `2026-05-09-spike` (`Xpycode/SFTPmount 1eaf000`), KinoBerlin `2026-01-16-tmdb-ratings-plan` artifact (local-only repo `089137f`). Group Alarms was a false positive — entries already indexed in bullet list via `(./file.md)` form the audit regex rejected. Patched `sync-session-index.sh` (master `5c1ca10`) to accept `(./)` prefix; verified `✓ in sync` across 11 audits (4 backfilled + 6 regression + master self). Side-incident: SFTPmount remote had near-identical spike commits pushed from another Mac (cross-Mac collision pattern recurring); resolved via `git reset --hard` + redo of the unique `_index.md` row.
- 2026-05-14: **M1 + post-M1 polish.** Consolidated `50_progressive-context.md` + `52_context-management.md` + `58_context-engineering.md` (1042L overlap) into canonical three-part `52_context-management.md` (Architecture + Runtime + Information Design), 1001L; 50/58 became 30-line breadcrumb stubs. Then expanded `13_folder-structure.md` 353L → 711L with Pattern A (no-build/Strato) + Pattern B (framework/Vercel), deploy-artifact tables, setup scripts, migration recipes — closes the web-target gap surfaced in the post-M1 audit.
- 2026-05-14: **M2 COMPLETE — wrote `38_ios-swiftui-state.md`** (247 lines). Five iOS state patterns from Group Alarms incidents, all rooted in "SwiftUI property wrappers are View-only": `@AppStorage` on non-View classes silently fails; `SettingsResetService` over duplicate declarations; pessimistic disk + optimistic memory; two-gate guard for implicit actions; UUID Equatable trap. Bonus: Xcode 16 synced folders auto-track filesystem. M2 fully shipped (29_, 38_, 39_).
- 2026-05-14: **M2 partial — wrote `39_libsql-turso-sync.md`** (198 lines). LEARNING's two libSQL/Turso CDC gotchas: DDL never replicates; raw sqlite3 DML bypasses CDC.
- 2026-05-14: **M2 partial — wrote `29_web-strato-hosting.md`** (230 lines). Codifies Strato hosting gotchas rediscovered across 4 web projects. 20s gotchas range contiguous 20–29.
- 2026-05-14: **Sync-conflict audit closed.** Resolved all sync-conflicts under `/ProgrammingProjects/` (AspectRatioUnifier Wave-7 bases, `.claude/settings.local.json` union-merges for MenuBarPLUS/SFTPmount, 4 `docs/sessions/` superset-dedupes). **Zero sync-conflicts remain.** Bootstrap-contamination sweep: **29 bit-identical session-log files removed across 4 consumers** (LUCESUMBRARUM, AvidMXFPeek, ePubReader, AutoRedact); all `✓ in sync`. *(detail in session logs)*
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

---
*Add decisions as they are made. Future-you will thank present-you.*
