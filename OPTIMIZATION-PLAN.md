# Directions Optimization Plan

**Date:** 2026-07-02 · **Scope:** full repo audit (60 docs, 36 commands, hooks, scripts, cookbook)
**Goal:** leaner docs, fewer tokens per session, more concise answers, less ceremony — without losing the hard-won knowledge that makes this system valuable.

This plan was produced by a full-corpus audit (five parallel deep reads covering every file). It is written so a future Claude session can execute it wave by wave, using this repo's own funnel discipline. Each wave has its own backpressure (validation) step.

---

## The headline numbers

| What | Today | After plan | Saving |
|---|---|---|---|
| Cookbook index load (`PATTERNS-COOKBOOK.md`) | ~67K tokens, loaded **wholesale** on every cookbook trigger | ~10K token router (grep-first, load one pattern file) | **~85%** on the hottest path |
| Always-loaded global file (`CLAUDE-GLOBAL-TEMPLATE.md`) | ~5K tokens every session | ~3.5K | ~800 words/session |
| Numbered docs (00–62) | ~146K tokens | ~100K | ~30% via dedup + trims |
| Commands | 36 commands, ~28K tokens | ~14 commands, ~11K tokens | ~60% |
| Setup/template docs | ~20K words | ~12.5K words | ~37% |
| Files a solo user must maintain per project | ~14 kinds | 5 kinds | most of the ceremony |

The verdict on the system itself: **the architecture is right** (read-on-demand, trigger router, pattern cookbook, lean state file). What's wrong is that (a) several seams between generations of the system are broken, (b) content that should live in exactly one place lives in 2–4, and (c) fast-decaying facts (model IDs, CLI flags, pricing) were written down as if permanent and have rotted.

---

## Wave 1 — Fix what is broken (correctness, small diffs, do first)

These are bugs, not style. Each is a small edit.

### 1.1 The core pipeline is broken
- `commands/plan.md:80` writes `IMPLEMENTATION_PLAN.md`; `commands/execute.md:29,64,73,88,95,99-100` looks for `PLAN.md` and re-interviews the user when it's missing. `52_context-management.md:428,637,966` also says `PLAN.md`.
- **Fix:** standardize on `IMPLEMENTATION_PLAN.md` everywhere (execute.md, 52_, SKILL references).

### 1.2 Hooks detect Directions via a file that no longer exists
- `scripts/session-start.py:150-153` and `scripts/doc-suggester.py:89` check for `docs/00_base.md` — but the read-on-demand migration (`commands/update-directions.md:57`) deletes numbered docs from projects. The declared sentinel is `docs/PROJECT_STATE.md` (`commands/setup.md:20`). `00_base.md:18` still teaches the old sentinel.
- **Fix:** gate both scripts and 00_base's detection rule on `docs/PROJECT_STATE.md`. One sentinel, stated once.

### 1.3 Both Python hooks emit output Claude Code ignores
- `session-start.py:136-138`, `doc-suggester.py:138-141` print `{"message": ...}` — not a valid hook output key. `doc-suggester.py:115-120` also reads raw JSON payload as if it were the prompt and falls back to an env var Claude Code doesn't set.
- **Fix:** parse the JSON payload, read `.prompt`, emit `hookSpecificOutput.additionalContext` (or plain stdout for SessionStart). Mirror what the shell hooks already do correctly.

### 1.4 The skill never registers
- `skills/directions-workflow/SKILL.md` has no YAML frontmatter, so it is inert; its content is 90% duplicate of 00_base/52_/directions.md anyway.
- **Fix:** delete it (or reduce to a 15-line frontmattered pointer at 00_base.md).

### 1.5 README teaches the forbidden install
- `README.md:44-56` says to rsync the whole repo into `project/docs/` — exactly what `commands/setup.md:12-16` prohibits ("Do not copy them into the project. Copies drift"). `README.md:192-193` copies the global template without mentioning the `[LOCAL_DIRECTIONS_PATH]` placeholders must be filled in.
- **Fix:** rewrite Quick Start around the read-on-demand model (install script + scaffold-only project files).

### 1.6 Fictional commands and packages
- `ideas.md:80-88` documents `/ideas`, `/ideas add|promote|start|done` — none exist. Delete ideas.md; fold an Ideas section into `TASKS.md`.
- `23_claude-code-cli.md:136,236` and `Directions-CURRICULUM.md:598-612` recommend npm packages `@anthropic-ai/mcp-filesystem`, `@anthropic-ai/mcp-github`, `@anthropic-ai/mcp-memory` — **these packages do not exist**. `23_:632` invents `claude mcp test`. `03_workflow-phases.md:151` references `/zen` (never introduced). `Directions-CURRICULUM.md:637` uses a `$FILE` hook variable that doesn't exist.
- **Fix:** correct or delete each; mark CURRICULUM "human reading only — do not load into sessions."

### 1.7 Stale model/CLI facts (highest user-facing blast radius)
- `60_model-selection.md:25-36`: compares Sonnet 4.5/Opus 4.6 (current: Sonnet 5, Opus 4.8); says context is "200K (1M beta)" (current Opus/Sonnet: **1M standard**); says adaptive thinking is "Opus exclusive" (it's standard across current tiers); lists extended `budget_tokens` thinking as available (removed on current models).
- `23_claude-code-cli.md`: `/continue` as slash command (it's `claude -c`; in-session is `/resume`); stale model ID in config example; `think/think hard/ultrathink` ladder (obsolete — thinking is adaptive now, also taught at `01_quick-reference.md:137-146`); outdated GitHub Action inputs; wrong system requirements; incomplete hook-event list; broken link to `Directions-PROGRESSIVE-CONTEXT.md`.
- `52_context-management.md:313`: `claude --headless` does not exist (headless is `claude -p`), and shell-spawned Claude instances are obsolete vs native subagents; `52_:505` shows a deprecated model with a 200K window.
- **Fix:** rewrite 60_ as tier-level guidance (Haiku = cheap/fast/200K; Sonnet = default/1M; Opus = hard problems/1M) with **no version-pinned benchmarks or prices**; halve 23_ and re-source from official docs; fix 52_'s two spots. Add a durability rule (Wave 5).

### 1.8 Wrong code snippets (they teach Claude to write bugs)
- `21_coordinate-systems.md:55-56` scale-factor snippet has an operator-precedence bug (never divides); `21_:149-157` "The Solution" for EXIF orientation is a no-op labeled CORRECT.
- `33_app-minimums.md:470-475` deprecated `SKStoreReviewController` API; `33_:441-444` claims `.handlesExternalEvents` does window restoration (it doesn't).
- `57_checkpoint-discipline.md:211-214` bash aliases use `$1` (aliases can't; needs functions).
- `20_swiftui-gotchas.md:41-58` UUID refresh-trigger hack — the modern fix is `@Observable`.
- **Fix:** correct each snippet.

### 1.9 Contradictions between docs (pick one answer each)
| Topic | Conflict | Decision needed |
|---|---|---|
| Split panes | `00-app-shell.md` mandates `HSplitView`; `21-anti-patterns`, `20_`, `41_` say use `HStack+Divider` | Pick one; update the MANDATORY standard |
| Sidebar nav | `41_apple-ui.md:335` bans `NavigationSplitView`; `cookbook/01` leads with it | Pick one |
| Dark mode | `00-app-shell` mandates `.preferredColorScheme(.dark)`; `cookbook/113` says remove it (and cites #00 content that doesn't exist) | Reconcile; write the missing adaptive-theme section or fix the citation |
| `/plan` | Custom command (writes plan file) vs built-in plan mode — same trigger, two meanings (`00:87` vs `01:92`, `23_:62`) | Rename custom command (e.g. `/make-plan`) |
| Context threshold | 53_ says 60%; 52_ says 70% zones; 01_ says 70–85% | Single source: 52_'s zone table |
| Committing to main | `32_:21` "never"; 37_'s whole workflow commits docs on main | Scope the rule: app code = branches; docs repos exempt |
| State stack | 33_ says `@Published + ObservableObject`; 38_ says `@Observable` | Standardize on `@Observable` (matches 20_ gotcha #1) |
| Swift version | 10_/11_/12_ say Swift 5.9/macOS 14; 14_ says Swift 6, per-app targets | 14_ wins; others defer |

### 1.10 Destructive-suggestion hook bug
- `hooks/session-start.sh:49,60` compares against hardcoded `origin/main` and can suggest `git reset --hard origin/main` on a branch whose upstream is elsewhere.
- **Fix:** use `@{u}` for both the comparison and the suggestion.

**Wave 1 backpressure:** grep-verify no remaining references to `PLAN.md` (as artifact name), `docs/00_base.md` (as sentinel), dead packages, `/ideas`, `--headless`, `ultrathink`; run `bash -n` on edited shell scripts and `python3 -m py_compile` on edited hooks.

---

## Wave 2 — Structural token wins (biggest savings)

> **STATUS (2026-07-02 d):** ✅ 2.1 done (index 50K→41.6K, app-shell split → #156) · ✅ 2.3 done
> (5 docs merged/deleted, new 41_ui-vocabulary + 47_project-ui-conventions, template trimmed, router
> regenerated) · ✅ 2.4 done (sessions/_index & decisions capped + archived) · ⏳ **2.2 NOT started**
> (commands 36→14 — deferred to its own focused run; Medium risk, rewrites the command system).

### 2.1 Rebuild the cookbook index as a lean router
`PATTERNS-COOKBOOK.md` is 264KB and loads wholesale on every cookbook auto-trigger (`CLAUDE-GLOBAL-TEMPLATE.md:84-95`).
1. Replace line 4's 28KB changelog line with `**Last updated:** <date> (#NNN)`. History lives in git.
2. One row per pattern: `#NNN | filename | ≤200-char summary | keywords`. Move verbose row bodies into their pattern files. Target: ≤40KB total.
3. Delete the stale Quick Reference Table (lines 183–268).
4. Add a `tags:` header line to each `cookbook/NNN-*.md` so a Grep over `cookbook/` can often skip the index entirely.
5. Update the two routers to say: *grep the index or cookbook filenames, then read only the matching pattern file — never read the whole index.* Rewrite `commands/cookbook.md` for the split structure (it currently instructs appending full patterns to sections that no longer exist, re-bloating the monolith) and drop the Vestige references.
6. Soft cap ~10KB per pattern file; split `00-app-shell.md` (29KB) into shell standard + Info.plist machinery; consolidate the Info.plist allowlist gotcha (currently in #00, #16, #89) into one file with cross-references.

### 2.2 Consolidate 36 commands → ~14
The newest commands (log, status, decide, worktree) show the right low-ceremony design; the older generation was layered under them instead of replaced.

Keep/merge map:
- `/setup` (trim) · `/decide` · `/learned` · `/worktree` · `/test-app` · `/cookbook` (fixed) — keep.
- `/status` absorbs `context`, `arrive` (as git-preflight variant).
- `/log` absorbs `session-close`, `depart`, `handoff`, `check-index`, `phase`, `compound` — **one end-of-session command, one turn** (its own telemetry says 69/69 invocations were session-enders).
- `/spec` absorbs `interview` (deep mode), `example-map` (examples mode), `new-feature` (delete).
- `/plan` (renamed per 1.9; fix artifact name) keeps TASKS.md sync.
- `/execute` absorbs `next`; model gate becomes a one-line nudge (drop the fragile `.current-model-*` newest-file dance — wrong under the repo's own two-session workflow).
- `/check` absorbs `code-review`, `quality`, `reflect`, `review`, `minimums` (modes: code | ship | security); `security-audit` body moves to a `5x_` doc.
- `/directions` merges with `update-directions`; the catalog table is **generated from the commands/ dir** so it can't drift (today four catalogs exist and all four are wrong).
- Delete: `tdd`, `build-fix` (content → 34_/25_ docs), `checkpoint`, `reorg`, `blockers` (fold into `/log`), SKILL.md.

### 2.3 De-duplicate the always-loaded and near-always-loaded docs
- Merge `03_workflow-phases.md` into `00_base.md` (funnel diagram, quick start, regeneration philosophy are verbatim duplicates; keep only per-phase detail).
- Stub `51_planning-patterns.md` into 52_ (move error-log pattern + planning-level table; soften the "2-Action Rule" to milestone updates).
- Merge `31_debugging.md` into 25_/35_ (it's a book extract with orphaned "Part 6/8" headers).
- Delete `11_ai-context-template.md` (AI-CONTEXT.md/SESSION-LOG.md are orphaned parallel systems no command reads or writes); `12_` becomes the sole template home; 10_ links instead of copying.
- Keep the bug-category and red-flag tables only in `01_quick-reference.md`; 02_/03_/60_ get one-line pointers (multi-model validation is currently stated three times).
- Merge `41_apple-ui.md` + `42_web-ui.md` vocabulary into one table-driven doc (~25 duplicated entries, some ASCII art verbatim in both); extract the load-bearing "Project UI Conventions" (41_:329-617) into its own doc so `/spec` and `/plan` stop paying a 330-line terminology tax.
- Trim `CLAUDE-GLOBAL-TEMPLATE.md`: drop the 31-row command table (point at `/directions`), keep only the generated Directions Index as router, replace dead `docs/NN_*.md` references with `[LOCAL_DIRECTIONS_PATH]` (six spots: lines 235, 247, 309, 335, 403, 422), remove the hardcoded Vestige line.
- 00_base's Document Router: **generate it from the TRIGGERS headers** (script exists: `scripts/gen-directions-index.sh`) — today 10 of 20 platform docs are unreachable from it (27, 28, 29, 31, 33, 34, 35, 36, 38, 39). Add the missing TRIGGERS header to 36_; normalize 54_'s format; disambiguate 25_ vs 31_ trigger keywords.

### 2.4 Growth-file policies (stop unbounded context creep)
- `sessions/_index.md` (38KB): cap Outcome cells at ~300 chars; keep ~20 recent rows, roll the rest to `_index-archive.md`; codify the "first row only" read rule in every command that touches it.
- `decisions.md` (44KB): keep recent ADRs + condensed log in the live file; archive older ADRs to `decisions-archive.md`; give `/decide` a length budget and push addenda to session logs; fix its path handling for master-repo mode.
- `PROJECT_STATE.md`: rewrite Recent entries to actual one-liners (currently 150–230-word narratives with SHAs and codenames, violating its own spec — and it's the template every new project copies).

**Wave 2 backpressure:** `wc -c PATTERNS-COOKBOOK.md` ≤ 45KB; `ls commands | wc -l` ≈ 14; regenerate index and diff routers; run `/status`, `/log`, `/spec`, `/plan`, `/execute`, `/check` dry runs in a scratch project.

---

## Wave 3 — Trim the long tail (per-file cuts)

Apply the per-file cut targets from the audit. Editing standard: the best files in the repo (62_, 54_, 27_, 28_, 29_, 39_, `log.md`, `decide.md`) — incident-derived, one-line sources, cheatsheet tables, no repeated restatement. Every other file gets edited toward that bar.

| File | Cut | Main move |
|---|---|---|
| 13_folder-structure (25K) | ~50% | Same placement facts stated 4–5×; keep tree + one placement table per pattern + one .gitignore |
| 37_multi-mac (26K) | ~40% | Keep Rules 1–5 + cheatsheet; compress incident chronicles to one-line sources; hook detail → hooks/README |
| 34_testing (14K) | ~40% | Delete XCTest/Swift-Testing syntax tutorials (training data); keep strategy, 5 gotchas, AppProbe |
| 33_app-minimums (24K) | ~30% | Checklist appears 3–4×; keep one canonical pass |
| 26_ecosystem (14K) | ~40% | Move per-machine MCP inventory out of the shared doc; fix config-path errors (`.mcp.json` vs `~/.claude.json`) |
| 52_context-mgmt (30K) | ~35% | 3 near-identical router examples → 1; cut blog-stat table; fix stale examples |
| 57_checkpoint (6K) | ~40% | Git-tag mechanics ×3 → 1; lead with built-in `/rewind`, tags for cross-session rollback |
| 53_llm-failure-modes | ~50% | Delete RAG category (inapplicable), ΔS pseudo-metric, credits; align threshold with 52_ |
| 56_, 59_, 30_, 22_, 24_, 20_, 21_, 01_, 02_, 10_, 12_ | 15–40% | Per audit: dedupe, shrink code samples, cut restatements |
| `.claude/settings.local.json` | — | Prune dead entries (`Bash(then)`, `Bash(fi)`…), fix `git *` → `git:*` patterns, drop over-broad `Read(//Users/sim/**)` and sudo rules |

Also: replace hardcoded `/Users/sim/...` paths in shareable files (45_, 34_, arrive/status/test-app commands) with the `[LOCAL_DIRECTIONS_PATH]`-style placeholder discipline used elsewhere.

**Wave 3 backpressure:** total numbered-doc bytes reduced ≥25%; every doc has exactly one TRIGGERS header; regenerated index has no degraded rows.

---

## Wave 4 — Interaction quality (better answers, fewer turns)

1. **One end-of-session turn.** `/log` owns all end-of-session writes (state, session log, index, tasks, learnings). No stacked nags: keep ONE Stop hook (delete the duplicate between `hooks.json` and `hooks/install.sh` — running both installers today double-fires menus and nags).
2. **Question budgets.** Commands infer from context and ask at most one question. Codify `log.md`'s pattern ("run automatically and report; don't ask permission for each") as a repo-wide command style rule. Rewrite the worst offenders if they survive consolidation: blockers (3 questions to append a paragraph), checkpoint (2 questions + menu for one git tag), review/minimums (40+ interactive checklist turns → Claude audits, presents one bucketed findings table, asks one question).
3. **Nudge, don't gate.** `/execute`'s hard STOP over model choice becomes plan.md-style "nudge once, continue."
4. **Kill the PostToolUse LLM check on every Bash call** (`hooks.json:38-47`) — replace with a cheap grep for `git commit`, or drop it.
5. **Bookkeeping budget.** One statement in 00_base: for tasks under ~30 min, only PROJECT_STATE gets updated at the end. Downgrade the four scattered "always write X" rules that currently mandate ~6 file writes per session.
6. **Maintained file set, stated explicitly:** `CLAUDE.md` + `docs/PROJECT_STATE.md` + `docs/decisions.md` + `docs/TASKS.md` + `docs/sessions/` (+ IMPLEMENTATION_PLAN.md and AGENTS.md during builds only). Everything else (AI-CONTEXT, SESSION-LOG, ideas.md, handoff files, tasks-archive as separate concern) is deleted or folded in.

---

## Wave 5 — Durability rules (so it doesn't rot again)

Add a short "Doc Rules" section to 00_base and enforce in `/compound` and `/cookbook add`:

1. **No fast-decaying facts.** Model names/prices/context windows, CLI flags, npm package names, GitHub Action inputs: never hardcode. Write tier-level guidance and "verify against official docs (code.claude.com/docs / platform.claude.com) before trusting specifics."
2. **One home per fact.** Cheatsheet = 01_; canonical context = 52_; templates = 12_; conventions = the new UI-conventions doc. Everything else points.
3. **Generated, never hand-maintained:** the Document Router, the Directions Index, the `/directions` catalog — all from TRIGGERS headers and the commands/ dir via the existing script.
4. **Size caps as policy:** pattern files ≤10KB; index row ≤200 chars; session-index Outcome ≤300 chars; ADR ≤ one screen; PROJECT_STATE Recent = one line each.
5. **The quality bar:** new docs must look like 62_/28_/29_ — incident-derived, one statement per fact, cheatsheet table, no narrative padding.
6. **Periodic check:** a `/check docs` mode (or quarterly manual pass) that greps for model IDs, dead paths, and duplicate headings.

---

## Suggested execution order

| Wave | Effort | Payoff | Risk |
|---|---|---|---|
| 1 Correctness | ~1 session | Broken pipeline + dead hooks fixed; no more wrong facts taught | Low — small diffs |
| 2 Structural | 1–2 sessions | ~85% off the cookbook hot path; 60% off commands; routers can't drift | Medium — touch hot paths; test in scratch project |
| 3 Trims | 1–2 sessions | ~30% off the doc corpus | Low — content-preserving edits |
| 4 Interaction | ~½ session | Fewer turns, fewer nags, one-question commands | Low |
| 5 Durability | ~½ session | Stops the rot recurring | Low |

Full per-file findings (with line references) live in the five audit reports summarized here; the top items are all cited inline above.
