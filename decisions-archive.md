# Decisions Log — Archive

Older full ADRs moved out of [`decisions.md`](decisions.md) (2026-07-02) to cap that file's size.
This file is append-only history — not read by any command in the normal flow. A one-paragraph
summary of each entry below still lives in the **Condensed Log** section of the live file.

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

---
*Archive only — not read by `/status`, `/log`, or `/decide`. Condensed one-paragraph summaries of
each entry above still live in the Condensed Log section of [`decisions.md`](decisions.md).*
