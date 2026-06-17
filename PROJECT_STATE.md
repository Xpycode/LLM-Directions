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
- **2026-06-17 (b)** — sat down on the M1 Max. `/arrive` flagged `behind 7` and the start-up banner said "byte-identical phantom, safe to `reset --hard`" — but a file-by-file hash check caught it under-counting: three cookbooks (**#118/#119/#120**) were genuine uncommitted local work a prior session never `/depart`-ed, and a blind `--hard` would have lost the index edits. Reconciled with **`reset --mixed`** instead (catches HEAD up but treats the working tree as sacred), then committed + pushed #118–120. Then **rolled the new Directions out** where it actually runs: refreshed the live `~/.claude/commands` copies (the #62-routing `/review` + `/minimums`, plus 4 commands that were missing globally). Surveyed all 44 projects that carry a Directions copy — every one is "behind" — but **decided NOT to mass-sync**: the live cookbook/command lookup reads from the *master repo*, so those per-project copies are vestigial snapshots nothing on the hot path reads. Synced + pushed only the 3 asked for (DiskVerdict, Conjoyn, App-Websites), docs-only so App-Websites' in-flight `apps.json` stayed untouched.
- **2026-06-17 (a)** — sat down on the M4-Pro; `/arrive` caught a parked working tree (cookbook #117 + index, uncommitted from a prior session) and reconciled it cleanly. Then captured a new framework doc, **`62_final-stretch-triage.md`** — discipline for the last 10% of shipping (capture-don't-fix, three honest buckets, define "done for v1" in writing). Wired it into both routing tables (`00_base` + `CLAUDE-GLOBAL-TEMPLATE`) and **into the ship-phase commands**: `/review` now completes the full pass before fixing, triages flagged items into the three buckets, and prompts for a written done-line; `/minimums` buckets gaps so a cosmetic miss isn't treated as a blocker. Synced the live `~/.claude/commands` copies (diffed first — were unmodified). *Note: already-set-up projects need `/update-directions` before the new `docs/62_…` path resolves.*
- **2026-06-16** — sat down on the M1 Max, pulled M4-Pro's 9 commits cleanly (no code, handover only). Confirmed Directions is fully wired into Claude on this Mac (the post-restore `install.sh` took — hooks + statusline symlinks all resolve). Cleared two stale "run install.sh on the *other* Mac" reminders from PROJECT_STATE: the Mac restored on 2026-06-13 was *this* one, and the script was already run — so both Macs are now wired and the reminder is gone. Also clarified that the ACK→DiskVerdict rollout happens *in the DiskVerdict repo*, not here; this repo just tracks it.
- **2026-06-15** — sat down at the M4-Pro and found the usual "switched Macs" mess: 8 commits behind *and* a dirty tree, because Syncthing copies loose files while the other Mac actually commits them. Sorted every changed file by hashing it against origin — most were already-identical duplicates (safe to drop), a few were genuinely new local work. Set the new work aside, pulled cleanly, put it back. Shipped one new pattern, cookbook **#110**: deep-linking straight to a macOS System Settings pane and *proving* the pane id is right by reading the OS's own extension registry (the ids drift every macOS release and a quick click-test can't tell "opened the right pane" from "opened the wrong one"). Kept the per-Mac settings file out of the commit so it stops causing cross-Mac conflicts. Then turned the lens on the framework itself: mined how `/log` is actually used (69 invocations — the "what are we working on?" question was asked literally zero times because it's always inferable) and **rewrote `/log` as a session-close** that reads the wrap-up mode from its argument instead of asking. Surveyed 10 apps for what they ship beyond the baseline and **grew `/minimums`** — standard shortcuts (Command-Comma = Settings, Command-Shift-? = Help), drag-drop, security-scoped bookmarks, and a separate HUD/agent tier. Extracted **cookbook #112** (security-scoped bookmarks, from 4 apps); the other Mac had shipped #111 (a hotkey-recorder field) in parallel, so mine took #112 — caught by checking the index before committing.
- **2026-06-14 (b)** — took the new `AppCitizenshipKit` from "built but unused" to "proven in a real app." Migrated Conjoyn — the app the patterns came from — off its hand-wired Feedback/Donate menus onto the package's one-liner, and used that migration to catch three things the package had wrong (an ellipsis its own rulebook forbids, a missing separator, and a bad word) and fix them *in the package* so every future app inherits the fix. Renamed the money item from "Donate"/"Support" to **"Leave a Tip"** (less beggary; "Support" clashed with the website's help page). Published the fixes as 0.1.1→0.1.2, wrote it up as cookbook **#108**. Along the way caught a cross-Mac duplicate cookbook number (two #106s) and reconciled it. Next: roll it to the other apps.
<!-- older entries → sessions/_index.md -->

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
*Last updated: 2026-06-17.*
