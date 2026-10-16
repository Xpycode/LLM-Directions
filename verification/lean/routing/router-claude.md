# Global Claude Instructions

<!-- SOURCE: CLAUDE-GLOBAL-TEMPLATE.md in the Directions master repo, installed to
     ~/.claude/CLAUDE.md by redeploy.sh (which renders [LOCAL_DIRECTIONS_PATH]).
     Edit the TEMPLATE and redeploy — hand-editing the live file is how the template
     and live copy drifted 200+ lines apart by 2026-07-29. -->

**These instructions apply to all sessions.**

`CLAUDE.md` is the Claude Code entry point; `AGENTS.md` is the Codex entry point. Keep stable
project facts aligned between them, but keep tool-specific behavior separate. Shared workflow
procedures live only in the Directions `commands/*.md` files; do not create a translated Codex
command library.

In Directions projects, requests to execute/resume an approved plan (including “continue
implementation” or “next wave”) use the master `commands/execute.md` procedure. Follow its
dependency, fresh-context delegation and validation rules; continue ready work within the user's
authorized scope without renewed task/wave permission. Explicit user limits prevail.

---

## Session Start: Auto-Detect and Resume

At the start of every session, **automatically run Project Detection (below)** to determine project state.

### Multi-Mac pre-flight (run FIRST, before any work)

This codebase is edited from more than one Mac (see `37_multi-mac-discipline.md`, Rule 1).
`~/ProgrammingProjects` is **one Syncthing folder** and **`.git` is excluded from sync**, so a
fresh/reset Mac has the source on disk but **no repo** — history lives only on GitHub `origin`.

```bash
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git fetch --quiet 2>/dev/null
  git status -sb | head -1; git status --porcelain | head -1
  # …and the question `git status` structurally cannot answer: has the DEFAULT branch moved past me?
  B=$(git branch --show-current); D=$(git symbolic-ref -q --short refs/remotes/origin/HEAD || echo origin/main)
  if [ -n "$B" ] && [ "origin/$B" != "$D" ] && git rev-parse -q --verify "$D" >/dev/null; then
    echo "vs $D: behind $(git rev-list --count HEAD..$D) · already-merged=$(git merge-base --is-ancestor HEAD $D && echo YES || echo no)"
  fi
else
  echo "NO .git — Syncthing-stripped; bootstrap needed"
fi
```

*(Keep this an `if/else`, not the old `&&`/`||` one-liner. A `{ …; }` block exits with the status of
its **last** command, so appending a conditional makes the block return non-zero whenever that
conditional is false — firing the "NO `.git`" branch inside a perfectly healthy repo. Verified
2026-07-28.)*

Read **three** things — the ahead/behind counts, whether the tree is dirty, **and the `vs origin/main`
line** — then act (these are *confirmed* actions — offer, don't silently mutate the tree):

- **behind > 0, tree clean** → safe fast-forward. Offer to `git pull` *before* editing — it's lossless,
  and another Mac may have already done the work you're about to start (the copy-vs-drift duplicate-
  commit incident, 2026-06-08).
- **behind > 0, tree dirty** → the local edits may be the *same* work origin already shipped, carried
  over by Syncthing but never committed here (the recurring duplicate pattern). Compare local changes
  against origin before discarding; once confirmed redundant, drop them and fast-forward.
- **ahead and behind** (diverged) → do **not** push; surface it and reconcile first (Rule 1).
- **ahead only** → unpushed commits the other Mac can't see; remind the user to push before switching.
- **in sync but tree dirty** → uncommitted leftovers from a prior session. Offer to commit + push or
  discard before new work — stray uncommitted edits are the seed of cross-Mac duplicates.
- **`already-merged=YES`** → ⚠️ **the branch is finished; `git status`'s green is a lie.** Every commit
  here is already in `origin/main`, which has since moved on. The branch is genuinely in sync with
  *its own* upstream, so the ahead/behind line above reads clean — it is answering a question you
  did not ask. Combined with Syncthing (which carries `main`'s **files** onto a checkout whose `.git`
  still points here), every file `main` has and this branch lacks appears as `M`/`??`, indistinguishable
  from real work. **Do not commit the working tree.** Rebranch from `origin/main` and cherry-pick only
  what is genuinely new: `git diff origin/main HEAD -- '*.swift'` empty ⇒ *nothing* here is new.
  Penumbra hit this five times (2026-06-10 / 06-14 / 07-02 / 07-12 / 07-27); the fifth pushed six
  commits of already-shipped work before anyone noticed.
- **`behind N` on the `vs origin/main` line, `already-merged=no`** → real branch work, but stale base.
  Rebase or merge `origin/main` in before trusting a test run — a clean cherry-pick onto a moved base
  is not the same as a correct one. Re-run the suite and compare the count to the last known-good.
- **in sync, clean** → proceed normally.
- **NO `.git`** (Syncthing stripped it) → **invoke the `git-bootstrap` skill** before any edit/commit.
  It does the safe init → fetch → **mixed**-reset → verify (HTTPS-via-`gh`, no SSH; identity
  `Luces Umbrarum <87826179+Xpycode@users.noreply.github.com>`). **Never `reset --hard` blind** —
  the skill's `--mixed`+`git status` check reveals on-disk drift *before* anything is overwritten;
  only escalate to `--hard` once the tree is proven clean.

**Machine profile:** before machine-dependent work (builds that need signing, UI automation,
fixture capture), read this Mac's section in `[LOCAL_DIRECTIONS_PATH]/MACHINES.md` (keyed by
`~/.claude/this-mac`) — it records signing identities, tooling presence, and known permission
blocks with workarounds, so they aren't rediscovered mid-build. Discovered a new machine fact the
hard way? Append it there in the same session.

**At session end** (or before walking away / switching Macs): run `/log`, which writes the session log,
syncs state, and — in Mac-handoff mode — offers to commit **and push** in one confirmed step. A local
commit that never reaches origin is as invisible to the other Mac as an uncommitted file. See
`37_multi-mac-discipline.md`.

After detection:
- If Directions exists → show current status and ask what to work on
- If no Directions → offer to set it up, then show commands menu

**Available commands:** run `/directions` for the full, current list — don't maintain a second
copy of it here; command sets change and a hardcoded table drifts (four hand-maintained catalogs
already drifted — that's why the list is generated on demand).

---

## Pattern Cookbook (Auto-Trigger)

When implementing a Swift/SwiftUI/web/macOS pattern, treat the cookbook as a **grep-first router** —
never read the whole index. It's 155 patterns, one one-line summary each. Two-step lookup:

1. **Grep the index**, then read only the matching pattern file (the row's link is the file):
   `grep -i '<keyword>' [LOCAL_DIRECTIONS_PATH]/PATTERNS-COOKBOOK.md`
2. Or **grep the pattern files directly** by their `**Tags:**` line, skipping the index entirely:
   `grep -ril '<keyword>' [LOCAL_DIRECTIONS_PATH]/cookbook/`

Read **only** the one matching `cookbook/NNN-*.md`. Do **not** load `PATTERNS-COOKBOOK.md` wholesale
— that's the anti-pattern this router exists to prevent.

**App Shell Standard (enforced):** All macOS apps use HSplitView (not NavigationSplitView),
FCPToolbarButtonStyle (not round buttons), `.windowStyle(.hiddenTitleBar)`, `.preferredColorScheme(.dark)`,
`.toolbarRole(.editor)`, and the `Theme` struct. Apps not following this should be migrated —
grep `cookbook/00-app-shell.md` (MANDATORY for all apps) and `47_project-ui-conventions.md`.

**Also search Vestige** for semantic matches — patterns are stored there too.

---

## Directions Index (Read-on-Demand, Not Copied)

<!-- DIRECTIONS-INDEX:START — generated by scripts/gen-directions-index.sh; do not edit by hand -->
Read relevant master guidance on demand; match the task's intent, not incidental quoted keywords. Resolve paths under `[LOCAL_DIRECTIONS_PATH]`; never use copied consumer guides. If routing is ambiguous, inspect the master's canonical numbered filenames and TRIGGERS headers before acting. Preserve dirty work; never expose secrets. Before multi-Mac recovery read `37_multi-mac-discipline.md`; before UI changes read `36_ui-changes-protocol.md` and `47_project-ui-conventions.md`; for credentials read `54_security-rules.md`. Current user limits, including no desktop control, prevail.
Directions commands, with or without a slash, read `commands/<name>.md` completely. Plan continuation and “next wave” read `commands/execute.md`; preserve no-agent/no-commit and other explicit limits.

For guidance about Directions/workflow, architecture/setup/docs, SwiftUI/macOS/iOS, web/data, tools/MCP/plugins, Git/multi-Mac, testing/security/release, design/UI, planning/context/models: read `[LOCAL_DIRECTIONS_PATH]/DIRECTIONS-INDEX.md`, then only the relevant listed guides. A routine command with no guidance question goes directly to its command file.
<!-- DIRECTIONS-INDEX:END -->

---

## Project Detection (Run automatically on session start)

Check the project state and act accordingly:

```
Does docs/PROJECT_STATE.md exist?
```

(Sentinel is `PROJECT_STATE.md`, not `00_base.md` — the universal docs are no longer copied into
projects; see the Directions Index above.)

**YES → Directions is set up.** Follow "Existing Projects with Directions" below.

**NO → Directions is not set up.** Offer to set it up. If the user accepts, run **`/setup`** — the
full detection flow (existing-docs migration, new-project scaffolding, folder structure, and the
migration extraction table) lives in `~/.claude/commands/setup.md` and loads on demand, so it does
not sit in context in every project.

---

## Existing Projects with Directions

If `docs/PROJECT_STATE.md` exists:

1. Read `docs/PROJECT_STATE.md` for current phase/focus/blockers
2. Show: "Phase: [X] | Focus: [Y] | Last session: [date]"
3. Ask: "Continue with [current focus], or work on something else?"

Only read additional files (session logs, decisions.md) if specifically needed for the task.

---

## General Preferences

### Git Discipline (solo dev)
- Small, low-risk changes (cleanup, docs, config, single-file fixes) → commit straight to `main`.
- Branch (`feature/`, `fix/`, `experiment/`) only for risky or multi-step work where bailing out is plausible.
- No PRs required — fast-forward merge or commit directly. PRs are team-review ceremony; skip them.
- One repo per project, **`.git` at the project root** (never inside `01_Project/` or `frontend/`).
- Commit messages: what + why. (See `[LOCAL_DIRECTIONS_PATH]/32_git-workflow.md`.)

### Communication Style
- Be direct, skip unnecessary preamble
- Ask clarifying questions when unsure
- Offer relevant docs from Directions when keywords match triggers
- Remind me about terminology references when I'm searching for words

### Quality
- Test the actual user flow, not just "build succeeded"
- Log decisions to `docs/decisions.md` when architectural choices are made
- Update session logs after significant progress

### UI Changes
When adding UI elements (views, controls, toggles, buttons, menus):
1. **Find similar first** — Locate an existing comparable control
2. **Trace wiring** — Show where it's defined, how state flows
3. **Propose location** — State exact file/line for new element
4. **Wait for confirmation** — Do not implement until approved

See `[LOCAL_DIRECTIONS_PATH]/36_ui-changes-protocol.md` for full protocol and examples.

### Xcode Build Behavior
Before building any app, ALWAYS do a clean build cycle:

1. **Kill the running app** (if any)
   ```bash
   # macOS app
   killall "AppName" 2>/dev/null || true

   # iOS Simulator
   xcrun simctl terminate booted <bundle-id> 2>/dev/null || true
   ```

2. **Clean the build folder**
   ```bash
   xcodebuild clean -scheme "SchemeName" -destination "..."
   # Or: rm -rf ~/Library/Developer/Xcode/DerivedData/ProjectName-*
   ```

3. **Build the app**
   ```bash
   xcodebuild -scheme "SchemeName" -destination "..." build
   ```

4. **Launch the app**
   ```bash
   # macOS
   open /path/to/Build/Products/Debug/AppName.app

   # iOS Simulator
   xcrun simctl install booted /path/to/app
   xcrun simctl launch booted <bundle-id>
   ```

This ensures a fresh state every time - no stale caches or zombie processes.

### Context Management

**CLAUDE.md Size:** Keep this file under 500 lines. If it's growing beyond that, move workflow-specific instructions into skills (`.claude/skills/<name>/SKILL.md`). Skills load on-demand, saving context.

**Compaction instructions:**
When compacting conversation context, always preserve:
- Full list of modified files in this session
- Test commands used and their results
- Key architectural decisions made
- Current task state and next steps

**Session hygiene:**
- `/clear` between unrelated tasks — a clean session outperforms a cluttered one
- `/compact` proactively at 65-70% context, not when forced at 95%
- `/rename` sessions before clearing so you can `/resume` later
- Use subagents for research to keep main context light

**MCP server awareness:** Disable unused MCP servers via `/mcp` — they consume context just by existing (tool definitions always loaded). CLI tools (`gh`, `aws`) have no context overhead.

### Skills Strategy

Use skills (`.claude/skills/<name>/SKILL.md`) instead of long CLAUDE.md sections for:
- Process workflows (commit, review, deploy)
- Domain-specific checklists
- Interview/discovery flows
- Repeatable multi-step procedures

Skills load on-demand only when invoked. CLAUDE.md loads every session.

**The Three-Times Rule:** If you've typed the same prompt three times, create a skill.

See `[LOCAL_DIRECTIONS_PATH]/23_claude-code-cli.md` for full skills documentation.

### MCP Hygiene

Never launch Claude Code from `$HOME` or umbrella project dirs (e.g. `~/Code/`, `~/Code/group/`)
while `codebase-memory-mcp` is installed — its auto-index skills will walk the entire tree
into a multi-GB SQLite DB and burn hundreds of % CPU. A PreToolUse guard at
`~/.claude/hooks/codebase-memory-guard.sh` blocks this; see `[LOCAL_DIRECTIONS_PATH]/27_mcp-gotchas.md`
and `hooks/mcp-guards/` for the templated guard. Same caution applies to Serena's
`--project-from-cwd`.

### Troubleshooting Quick Reference

When something goes wrong:
1. `Escape` — stop current action immediately
2. `Esc+Esc` — rewind file changes (doesn't track bash command changes)
3. `git restore` — rollback to last commit (tracks everything)
4. `/clear` — fresh session with better prompt

Run `/doctor` first for configuration issues. See `[LOCAL_DIRECTIONS_PATH]/25_troubleshooting.md` for full guide.

---

## Directions Location

- **GitHub:** https://github.com/Xpycode/LLM-Directions (`origin`, public)
- **Local master:** `[LOCAL_DIRECTIONS_PATH]`

Note the directory is named `__DIRECTIONS`, not `LLM-Directions` — searching for the repo by its
GitHub name will not find it on disk.

`git fetch` this repo before relying on it; it is edited from more than one Mac
(see `37_multi-mac-discipline.md`).
