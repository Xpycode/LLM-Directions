# Project State

> **Lean digest — target <50 lines.** Current state + a short changelog, then pointers to detail
> files. History lives in `decisions.md` and `sessions/_index.md`, not here.

## Identity
- **Project:** Directions — LLM-assisted development framework (specs, plans, verification)
- **Tags:** meta, framework, documentation, workflow, Claude · **Started:** 2024

## Now
- **Phase:** build / implementation (~80%) — mature framework, ongoing refinement.
- **Focus:** portfolio **"app citizenship" rollout** — shared Feedback/Tip-Jar/About across all macOS
  apps. Audited 30 apps + built `AppCitizenshipKit` (2026-06-14); **first reference app (Conjoyn) now
  migrated to it end-to-end** — package hardened `Xpycode/AppCitizenshipKit` 0.1.0→**0.1.2**, Conjoyn
  consumes the tag and builds green; cookbook **#108** captures the migration + proving-ground pattern.
- **Blockers:** none.
- **Next:** **roll `AppCitizenshipKit` to the first wave** of apps — DiskVerdict next (additive: it has
  FeedbackKit already, ACK adds Tip Jar + About), then the rest. Use the per-app rollout checklist in
  ACK's README + the `#108` pattern. Separate sweep: fix 19/30 missing/empty AppIcons (cookbook #76).
  *(Naming decision baked into ACK: tip-jar framing — "Leave a Tip" / "Tip Jar" — over "Donate"
  (charity) and "Support" (collides with the web help-desk page #105).)*

## Recent
<!-- Last ~5 changes, one line each, plain language. Full detail → sessions/_index.md -->
- **2026-06-16** — sat down on the M1 Max, pulled M4-Pro's 9 commits cleanly (no code, handover only). Confirmed Directions is fully wired into Claude on this Mac (the post-restore `install.sh` took — hooks + statusline symlinks all resolve). Cleared two stale "run install.sh on the *other* Mac" reminders from PROJECT_STATE: the Mac restored on 2026-06-13 was *this* one, and the script was already run — so both Macs are now wired and the reminder is gone. Also clarified that the ACK→DiskVerdict rollout happens *in the DiskVerdict repo*, not here; this repo just tracks it.
- **2026-06-15** — sat down at the M4-Pro and found the usual "switched Macs" mess: 8 commits behind *and* a dirty tree, because Syncthing copies loose files while the other Mac actually commits them. Sorted every changed file by hashing it against origin — most were already-identical duplicates (safe to drop), a few were genuinely new local work. Set the new work aside, pulled cleanly, put it back. Shipped one new pattern, cookbook **#110**: deep-linking straight to a macOS System Settings pane and *proving* the pane id is right by reading the OS's own extension registry (the ids drift every macOS release and a quick click-test can't tell "opened the right pane" from "opened the wrong one"). Kept the per-Mac settings file out of the commit so it stops causing cross-Mac conflicts. Then turned the lens on the framework itself: mined how `/log` is actually used (69 invocations — the "what are we working on?" question was asked literally zero times because it's always inferable) and **rewrote `/log` as a session-close** that reads the wrap-up mode from its argument instead of asking. Surveyed 10 apps for what they ship beyond the baseline and **grew `/minimums`** — standard shortcuts (Command-Comma = Settings, Command-Shift-? = Help), drag-drop, security-scoped bookmarks, and a separate HUD/agent tier. Extracted **cookbook #112** (security-scoped bookmarks, from 4 apps); the other Mac had shipped #111 (a hotkey-recorder field) in parallel, so mine took #112 — caught by checking the index before committing.
- **2026-06-14 (b)** — took the new `AppCitizenshipKit` from "built but unused" to "proven in a real app." Migrated Conjoyn — the app the patterns came from — off its hand-wired Feedback/Donate menus onto the package's one-liner, and used that migration to catch three things the package had wrong (an ellipsis its own rulebook forbids, a missing separator, and a bad word) and fix them *in the package* so every future app inherits the fix. Renamed the money item from "Donate"/"Support" to **"Leave a Tip"** (less beggary; "Support" clashed with the website's help page). Published the fixes as 0.1.1→0.1.2, wrote it up as cookbook **#108**. Along the way caught a cross-Mac duplicate cookbook number (two #106s) and reconciled it. Next: roll it to the other apps.
- **2026-06-14** — surveyed all 30 macOS apps for the "every app should have this" features (Help, Settings, Feedback, Donate, About, updates, onboarding, app icon) and found donate missing from every single app, feedback and a proper About almost everywhere, and 19 apps shipping a blank icon. Then built `AppCitizenshipKit` — one small package an app adds in a single line to get Send-Feedback + Support/Donate + a links-rich About in its menus. It reuses the existing FeedbackKit and adds the first reusable "Donate" link (pointing at the shared donate web page). Builds and tests pass; not yet published or wired into an app.
- **2026-06-13** — added two "switching Macs" commands. `/arrive` (sit down) fetches and tells you in plain words what the other Mac did, whether you're behind, and where you left off; `/depart` (leaving) syncs the log + state, commits, and pushes — stamping each commit with which Mac it came from so the other side can read it back. The clever bit: the Mac name lives in git's own commit data (never conflicts), not in a synced file. Machine identity comes from a tiny per-Mac file `~/.claude/this-mac` (outside Syncthing) with the Mac's own name as fallback.
- **2026-06-13** — resolved the long-parked "see all my projects at a glance" question. Two old designs competed: a heavyweight one that commits a data file into every project and stitches them together (auto-runs on every log), versus a throwaway single page generated on demand. Picked the throwaway: a small gitignored script reads each project's PROJECT_STATE.md + last commit and writes one self-contained `dashboard.html` (search, phase filters, stale-project dimming) — nothing committed, nothing touches other projects. The scan itself doubled as a health check: 6 projects have a drifted PROJECT_STATE worth tidying, and only zPackages is truly blocked.
- **2026-06-13** — the other Mac was erased and restored; Syncthing copied the current files back here but not git's history, so this Mac looked "10 commits behind with uncommitted changes" even though every file already matched origin. Confirmed it was harmless (a "phantom"), fixed it with one `git reset --hard`, then taught the session-start hook to detect this exact case and say "safe to reset" instead of guessing — and wrote up the `diff -q` gotcha that briefly faked a disagreement.
- **2026-06-11** — built a guard that warns when two Claude sessions are open in the same folder (they share one git checkout, so a branch switch in one hits both); added a `/worktree` helper to split them safely, and wrote it up as Rule 5 in the multi-Mac doc.

## Progress
| Funnel | Status | Gate |
|--------|--------|------|
| Define | ✅ done | Framework documented |
| Plan   | ✅ done | Commands + templates defined |
| Build  | 🔶 active | Iterating on improvements |

| Dimension | Features | UI/Polish | Testing | Docs | Distribution |
|-----------|----------|-----------|---------|------|--------------|
| Status    | ✅ | 🔶 | ⚪ | ✅ | ✅ |

## Detail (read only if needed)
- **Why we decided things** → `decisions.md`
- **Full session history** → `sessions/_index.md`
- **Backlog / what's ahead** → `TASKS.md` (+ `tasks-archive.md`)
- **Global config mirror** → `CLAUDE-GLOBAL-TEMPLATE.md` (the live `~/.claude/CLAUDE.md` is not in this repo)

## Infrastructure
- 261 global skills at `~/.claude/skills/` (update: `npx skills update`)
- XcodePreviews `/preview` at `/Users/sim/ProgrammingProjects/0-DIRECTIONS/XcodePreviews/`

## Resume
<!-- If RESUME.md exists, note it here. Otherwise blank. -->
- **Per-Mac wiring (does NOT travel via git):** both Macs are wired — M1 Max erased+restored
  2026-06-13 and `bash hooks/install.sh` was re-run there (symlinks verified); M4-Pro long since done.
  Reminder only if a Mac is restored again: after `git pull`, run `bash hooks/install.sh` once — it
  symlinks the hooks (incl. `session-guard.sh`) + statusline into `~/.claude/` and registers them in
  `settings.json` (idempotent).
- **Carried-over TODO:** cookbook **#92** for the hook↔statusline handshake pattern (#91 is now the
  process-inspection session detector); tune `model-advisor.sh` keyword lists.

---
*Lean digest. Source of truth for current position; history lives in the linked files.*
*Last updated: 2026-06-16.*
