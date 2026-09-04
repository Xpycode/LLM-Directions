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

> Full ADRs older than the one below live in [`decisions-archive.md`](decisions-archive.md) — a
> one-paragraph summary of each still lives in the Condensed Log further down this file.

### 2026-08-30 - Codex uses a thin adapter over the live Claude Directions commands

**Context:** Directions already has a mature Claude Code command library under `commands/`, and the
same session/state discipline is wanted while evaluating Codex. Translating every command into a
second Codex-owned copy would make fixes to `/log`, `/status`, and related workflows drift between
tools. Codex also reserves some slash commands, including `/status`.

**Options Considered:**
1. **Copy and translate every command for Codex** — direct per-command invocation, but two large
   instruction sets to reconcile after every Directions change.
2. **Use a thin Codex skill that routes to the live command files** — one small compatibility layer;
   Codex reads the selected shared command before acting.
3. **Rely on ad-hoc prompts in Codex** — no setup cost, but session logging and state updates lose
   the deterministic Directions contract.

**Decision:** Option 2. Version `codex/skills/directions/` in this repository and link it into the
local Codex skills directory. Invoke it explicitly as `$directions /status`, `$directions /log`, and
so on; natural-language requests may select it implicitly.

**Rationale:** The existing command files remain the only procedural source of truth, so both tools
receive future fixes immediately. The adapter contains only tool-specific routing, permission, and
fallback rules. Explicit `$directions` invocation also avoids collisions with Codex's built-in slash
commands while making the selected workflow visible.

**Consequences:** Claude Code remains unchanged. Codex must be able to read this repository path,
and genuinely Claude-only hooks or state files need evidence-based fallbacks rather than invented
equivalence. Cross-Mac restore must install or link the Codex skill separately; that deployment step
is not yet folded into `redeploy.sh`. Real-project use should drive any further adapter rules.

**2026-09-01 refinement:** Real use showed that requiring `$directions` makes routine commands
needlessly cumbersome. Bare workflow requests (`/status arrive` or `status arrive`) are now the
primary Codex convention; `$directions /status` remains a compatibility fallback. Slashless forms
also handle cases where the interface reserves a slash command before the model can see it. This
changes invocation ergonomics only—the thin adapter and live `commands/*.md` source remain intact.

**2026-09-04 refinement:** Make Codex deployment first-class rather than relying on a one-off link in
the legacy `~/.codex/skills` directory. The versioned skill remains the adapter, but
`deploy-codex.sh` now links it into the active build's user-skill location (`CODEX_HOME/skills`) and
merges a generated, marked Directions block into global `$CODEX_HOME/AGENTS.md` (default
`~/.codex/AGENTS.md`). The block carries the
master path and live topic index while preserving unrelated personal instructions. Shared commands
mark Claude-only model integration explicitly; `/directions update` selects the active tool's
deployer. A standalone skill remains the right first deployment because this is one personal
workflow still being exercised; a plugin and Codex hooks are deferred until their extra packaging,
trust, payload, and noise behavior is proven in real sessions.

**2026-09-04 model/context refinement:** Keep capability tiers and escalation order provider-neutral
in `60_model-selection.md`; put volatile current model mappings in `23_claude-code-cli.md` and
`64_codex.md`. Model capability, reasoning effort, context quality, and parallelism are separate
controls. Diagnose missing or polluted context before escalating. The Codex reference owns current
CLI controls such as `/usage`, `/status`, `/permissions`, and `/statusline`, while `AGENTS.md` stays
lean. After an explicit fleet-backfill request, the ten recently active projects received tailored
root `AGENTS.md` files containing only stable project facts, validation, safety constraints, and live
Directions routing—no copied universal docs or mutable state.

### 2026-07-18 - House design system (`42_`) + appearance standard: dark default, user-selectable light

**Context:** A Claude-Desktop screenshot critique of DiskVerdict/Conjoyn/Penumbra/CropBatch/Magpie
diagnosed the "LLM-generated look": system semantic colors (no temperature), accent sprayed on
everything, one global corner radius, centered big-SF-Symbol empty states, default-weight SF
headings — and, collectively, five apps sharing one visual center. It proposed a per-app DESIGN.md
token system (light-first). Meanwhile the repo's own appearance story had drifted three ways:
cookbook §0 blurb + the shell-check skill still mandated forced dark, while `00-app-shell.md` §2
had already moved to adaptive-by-default. User direction: dark stays standard, light must be available.

**Options Considered:**
1. **Drop DESIGN.md into each app repo as-is** — recreates copy-vs-drift (5 drifting foundations);
   keeps its light-first default, contradicting the house aesthetic.
2. **Adopt as master doc, keep forced-dark** — resolves drift but rejects the wanted light mode.
3. **Split shared-vs-per-app + dark-default/user-switchable** — foundation in master
   `42_design-system.md` (read on demand); app repos carry only the filled §1 brief + Theme;
   appearance = dark first launch + Light/Dark/Match-System picker via
   `NSApplication.shared.appearance` (#113); critique pass folded into `/check design`.

**Decision:** Option 3.

**Rationale:** The banned-patterns list is the real value — negative constraints beat aspirational
prose for steering a model off its statistical center. Per-app briefs (unique accent + distinctive
element, human-picked) attack the sameness. Master-homed foundation is this framework's own
copy-vs-drift lesson applied to design. Dark-default + picker honors both the existing aesthetic
and the new direction, using the mechanism #113 already proved. The semantic-colors ban is adopted
*with its cost stated* (Theme must carry adaptation + Increase Contrast) so a future session
doesn't "fix" it back.

**Consequences:** shell-check checks #2/#7 now audit for the picker + an appearance-aware Theme
(hardcoded forced dark = pass-with-note; keeping forced dark stays a legitimate per-app opt-in,
`00-app-shell.md` §2.1 — e.g. Penumbra). The skill is now versioned in repo `skills/` (was
live-only on the M4-Pro — the git-bootstrap lesson). `/check` gains a `design` mode; cookbook §0 +
`00-app-shell.md` §2 aligned; Directions Index regenerated. Appearance wave 1: DiskVerdict,
Conjoyn, TimeCodeEditor, Magpie; rest gradually. ACK shared screens must consume the host app's
Theme tokens. Per-app accents pending (orange stays Penumbra's; Conjoyn needs its own).

### 2026-07-11 - Reject `claude-octopus` wholesale; adopt only its blind-spot-injection idea, Claude-only

**Context:** Considered whether `claude-octopus` (nyldn) — a multi-provider AI-orchestration plugin
(52 commands, 55 skills, 58 hooks, 32 personas, v9.52.0; 348 md + 429 shell) — could strengthen the
Directions framework, whose whole thrust is a *lean, curated, solo, Claude-Code-only* toolset (we'd
just pruned commands 38→15 to fight bloat). Its headline feature is a "council/consensus" that runs
multiple vendor CLIs (Codex/Gemini/Qwen) adversarially and gates on agreement.

**Options Considered:**
1. **Install it wholesale** — instant multi-model review. Cons: the value is inseparable from *paid*
   external CLIs we don't run; adds per-Mac wiring (the exact cross-Mac tax `37_` warns about); a
   ~2,900-line `orchestrate.sh` + ~2,500-line `council.sh` maintenance surface riddled with
   bug-number patches; re-inflates the command/hook count we just cut. Its own `debate.sh` concedes
   *"convergent agreement between models may indicate shared blind spots, not correctness."*
2. **Borrow personas / freeze-guard hooks** — decent but overlap our existing `fable5` agents +
   integrity guardrails; marginal.
3. **Extract only the `config/blind-spots/` idea, reimplemented Claude-only** — a keyword→prompt
   library that injects the perspectives an LLM structurally forgets. Provider-free, ~40 lines.

**Decision:** Option 3. Skip the whole orchestration/vendor layer; reimplement just the blind-spot
injection as **cookbook #159**, with a seed library sourced from *our own* numbered gotcha docs
(20_/21_/22_/38_/61_/32_/29_/36_ + prior cookbook entries) rather than octopus's B2B-SaaS entries,
plus a ~15-line jq matcher.

**Rationale:** It captures the actual mechanism of value behind "council" (surface what one model
reliably misses) with zero external dependencies, zero API cost, negligible context, and one owned
file — while *inverting* octopus's premise: encode our own hard-won blind spots instead of renting a
stranger's. Multi-Claude "consensus" would share Claude's blind spots anyway, so the vendor diversity
(the only thing we can't reproduce) is also the part with the worst cost/maintenance profile.

**Consequences:** #159 is a manual pattern first (skim/paste before `/check`/spec/hand-off); a
`UserPromptSubmit` hook to auto-inject is deliberately deferred until the manual form proves it fires
more usefully than it nags. The seed grows by one row whenever Claude is caught skipping the same
category twice. We do **not** take on octopus as a dependency; re-evaluate only if we ever routinely
run multiple vendor CLIs locally.

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

> Six older full ADRs (2026-05-14 ×3, 2026-05-13 ×2, 2026-01-25) archived to
> [`decisions-archive.md`](decisions-archive.md) on 2026-07-02 — condensed one-paragraph summaries
> of each remain in the Condensed Log immediately below.

---

## Condensed Log (summaries — migrated from PROJECT_STATE.md, 2026-06-09)

> One-paragraph decision/outcome summaries, newest first. Lighter than the full ADRs above; kept
> verbatim here so PROJECT_STATE.md can stay a lean digest. Some overlap with ADRs above is intentional.

- 2026-07-13: **Skills deploy is COPY-ONLY; commands deploy PRUNES.** `redeploy.sh` gained a Skills section that installs the repo's `skills/` into `~/.claude/skills/` but **never removes** anything — the deliberate inverse of the commands policy (which prunes retired Directions commands via git-deletion provenance). Reason: `~/.claude/skills/` holds ~263 mostly third-party skills (npx/plugin-managed) we don't own; a prune keyed on "not in the repo" would nuke them. Same script, opposite reconciliation rule per artifact type — because commands are a closed canonical set and skills are a shared namespace.
- 2026-07-13: **A skill must be versioned in the repo, not left live-only on one Mac.** The `git-bootstrap` skill was a "phantom": five docs referenced it, but it had only ever been authored as a *live* `~/.claude/skills/` file on the M1 Max — never committed. An un-versioned live skill is invisible to origin and to every other machine, so it silently never propagates (this Mac and the session skill-list both showed it "missing"). Fix: repo now carries a `skills/` source dir + `redeploy.sh` installs from it. Corollary to the 2026-06-08 copy-vs-drift decision: the cure for drift is a single versioned source, and that applies to skills too, not just docs/commands.
- 2026-06-19: **Model-tier signal = session type (command), not prompt keywords.** A regex matches *form* not *meaning* — "implement" can be trivial or subtle. A `/spec`/`/plan`/`/execute` invocation is an explicit declaration of intent → near-zero false positives. Replaced keyword-guessing with phase-aware gating: `/execute` **gates** to Sonnet, `/spec`+`/plan` **nudge** to Opus, `/session-close` reminds the next session's model. Keyword hook stays only as a weak backstop.
- 2026-06-19: **Switch models at the `/clear` boundary, not mid-session.** Switching model is a prompt-cache miss (per-model cache) — the new model re-reads the whole context at full input price. Cheapest when context is empty, right after `/clear`. Pattern: end-of-session reminder → clear → switch → start. Mid-session switch at 180k+ context buys little for the cost.
- 2026-06-19: **Loudness is channel-specific.** Statusline = true ANSI red (terminal line, renders ANSI). Chat / `systemMessage` = CAPS + emoji (plain-text channels — ANSI leaks as literal escape codes). Match the technique to the channel, not the desired emphasis.
- 2026-06-14: **ACK monetization naming: tip-jar framing.** "Leave a Tip" / "Tip Jar" chosen over "Donate" (reads as charity) and "Support" (collides with the website's help-desk page, cookbook #105). Baked into `AppCitizenshipKit`, so every app in the citizenship rollout inherits it. *(Moved here from PROJECT_STATE.md, 2026-07-18.)*
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
