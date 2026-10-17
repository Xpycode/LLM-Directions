# Status arrival procedure

Run when you **sit down at a Mac**, especially after switching from the other one and letting
Syncthing settle. The per-project, human-readable version of the session-start git pre-flight.
**Read-only** — it fetches and reports; never pulls/commits/switches without asking. Pairs with
`/log` Mac-handoff mode (which stamps each commit with the Mac that pushed it).

1. **Who am I?**
   ```bash
   MAC=$(cat ~/.config/directions/this-mac 2>/dev/null \
     || cat ~/.claude/this-mac 2>/dev/null \
     || scutil --get LocalHostName 2>/dev/null \
     || hostname -s)
   ```
   `~/.config/directions/this-mac` is the tool-neutral one-line per-machine label (e.g. `M1 Max`),
   kept **outside** Syncthing so it never travels — same path, different content per Mac. The old
   Claude path remains a compatibility fallback. Missing → the Mac's own name is used.
2. **Verify the intended repository, then git + remote.** Confirm the absolute working directory
   and `git rev-parse --show-toplevel` match the requested checkout before inspecting its remote.
   After a failed `cd`, stop: the previous directory is not evidence about the intended project.
   Do not fetch or make remote-state claims until identity is established. Then run
   `git rev-parse --is-inside-work-tree` and `git remote get-url origin`.
   - No git → "files travel by Syncthing only; nothing to compare." Skip to 4.
   - git but no remote → "history has no GitHub remote, so I can't see the other Mac's work — add one?" Skip to 4.
3. **Fetch and read the other Mac's last work (read-only):**
   ```bash
   git fetch --quiet 2>/dev/null; git status -sb | head -1
   git log -1 @{u} --format='%cr%n%an%n%s' 2>/dev/null
   git log -1 @{u} --format='%(trailers:key=Handoff-from,valueonly)' 2>/dev/null
   ```
   `Handoff-from:` is the Mac `/log` stamped in (immutable, conflict-free). Empty → predates it; report author/date.
   **Plain verdict (no SHAs):**
   - **up to date** → "✓ Up to date. Last: <Mac>, <when> — \"<subject>\". Good to start."
   - **behind N** → "⚠ <Mac> pushed <when> — you're N behind. Pull first?" Offer `git pull --ff-only`; pull only on **yes**, after the Rule 5 mutation preflight in `37_multi-mac-discipline.md`.
   - **ahead M** → "M commits here not pushed (prior session on this Mac). Fine to keep working — `/log` before you leave."
   - **diverged (ahead+behind)** → "⚠ Both Macs have unpushed work — diverged. Don't pull blindly." → `37_multi-mac-discipline.md` Rule 1. No auto-pull/reset.
4. **Where did I leave off?** Read `PROJECT_STATE.md`; show **Now → Focus** and **Next** (one line
   each), applying the execution reminder in `<master>/commands/status.md` when a plan is active.
5. **Collision check** (light) — read `<master>/reference/status/collision.md` completely.
