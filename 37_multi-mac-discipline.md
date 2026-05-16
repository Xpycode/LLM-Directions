<!--
TRIGGERS: cross-mac, multi-mac, M1 Max, M4 Pro, multiple Macs, working from two Macs,
          Syncthing sync-conflict, git push rejected "fetch first", divergent commits,
          duplicate commits across machines, "we did this on the other Mac",
          machine-specific state, per-machine spike context, fixture missing on this Mac,
          settings.local.json conflict, .stignore, log archaeology
PHASE: any (especially when state surfaces drift)
LOAD: when working from more than one Mac on the same project, debugging "this worked yesterday on the other Mac" issues, recovering from a sync-conflict / push-rejection, or designing where to put state that needs to follow you between machines
-->

# Multi-Mac Discipline

*State on disk is per-machine by default. Cross-machine sync (git, Syncthing) is opt-in, partial, and surfaces divergence at integration moments — push, pull, "is this still here?" Three sessions in two weeks yielded three distinct collision patterns, all rooted in the same blind spot: **assuming the machine you're on is the machine where the work was done**.*

---

## The mental model

Two systems sync state across your Macs, at different cadences and with different semantics:

| Layer | Cadence | What it sees | What it misses |
|---|---|---|---|
| **Git (per repo)** | Manual: `push` / `pull` / `fetch` | Commits in tracked files | Untracked files, build outputs, OS state (system extensions, fixtures, DerivedData) |
| **Syncthing (per folder)** | Continuous, eventually-consistent | All files in tracked folders | Whatever `.stignore` excludes (`.git`, `.DS_Store`, `.claude/settings.local.json`, build/cache dirs) |

The blind spots compose. Three categories of state behave very differently:

- **Per-machine OS state** (registered system extensions, Xcode DerivedData, signing certs, fixtures dropped on the Desktop, scratch dirs like `~/scratch/...`): neither git nor Syncthing touches it. Lives only on the machine where it was created.
- **Git-tracked but independently edited** on two Macs (`docs/sessions/_index.md` rows, code, plans): produces divergent commits at the next push.
- **Syncthing-tracked but allowed to accumulate** (`.claude/settings.local.json` allowlists, MCP server lists): produces `*.sync-conflict-*.<ext>` files at the next sync.

All three patterns this period stemmed from one of these three categories.

---

## Rule 1: Defend at integration moments — `git fetch` first when crossing machines

The most expensive class of mistake is **pushing a duplicate commit**. You build local work; another Mac pushed near-identical work in the meantime; your push gets rejected; `git pull --rebase` produces conflicts on every file (both edits touch the same content); resolving them feels like real work but yields a noisy history with two commits doing the same thing.

### Symptom

```
$ git push origin main
 ! [rejected]        main -> main (fetch first)
error: failed to push some refs to '...'
hint: Updates were rejected because the remote contains work that you do not
hint: have locally.
```

When you fetch and inspect, you see commits with similar subjects (e.g. `Wave 0 R2 spike: register + activate FSKit extension on macOS 26.4.1` vs your local `Wave 0.0 spike progress: R2 registration+activation retired on 26.4.1`).

### The fix

```bash
git fetch origin main
git rev-list --left-right --count HEAD...origin/main   # how far apart?
git diff --stat HEAD~1 origin/main                     # what's the file overlap?
```

Then choose based on overlap:

| Their work vs yours | Action |
|---|---|
| Effectively identical | `git reset --hard origin/main` (drops your duplicate; recoverable via reflog) → re-apply only the genuinely-unique parts as a new focused commit |
| Unrelated | `git pull --rebase` |
| Your commit is a strict superset (their work + more) | `git pull --rebase` then push |
| Both diverged with real conflicts | Inspect file by file; resolve manually |

**Don't merge** unless histories genuinely diverge. A merge commit on top of two near-identical sets of work is permanent noise.

### The discipline

Before any non-trivial commit on a multi-Mac repo: `git fetch origin main` first. It's free (read-only), and the output answers the question that prevents the duplicate-commit class.

| `git rev-list --left-right --count HEAD...origin/main` | Means | Action |
|---|---|---|
| `0 0` | in sync | proceed |
| `N 0` | you ahead | proceed (push when ready) |
| `0 N` | other ahead | `git pull --rebase` then proceed |
| `N M` | both ahead | inspect diff first |

Source: SFTPmount 2026-05-15 (committed local spike work; push rejected because the M4 Pro had pushed near-identical commits earlier; resolved via `git reset --hard origin/main` + a focused single-row `_index.md` commit, total 1 unique commit instead of 2 duplicates).

---

## Rule 2: Verify machine-specific state on the actual machine before acting on it

OS-level state — registered system extensions, installed apps, mounted filesystems, captured fixtures, scratch dirs, DerivedData — is **per-machine by default**. The journal entry "we built FSKitSample on the M4 Pro and toggled the extension on" is a claim about the M4 Pro. If you're on M1 Max, none of that state exists here regardless of what the journal says.

### Symptom

You read a session journal, switch context to that project, start running commands assuming the documented state — and they fail in confusing ways. `mount -t MyFS ...` returns "filesystem type not recognized." A fixture file referenced in the doc isn't on disk. A scratch dir doesn't exist.

### The fix

Before resuming machine-dependent work, run a pre-flight that's specific to what the work needs. Examples by domain:

```bash
# FSKit / system extensions
systemextensionsctl list                         # what system extensions are active?
pluginkit -m -v | grep -i <bundle-id>            # is your appex registered?

# App installation
ls /Applications/<App>.app
find ~/Library/Developer/Xcode/DerivedData -name "<App>.app" 2>/dev/null

# HID device fixtures, scratch dirs
ls ~/Desktop/<expected-fixture>.json
ls ~/scratch/<project>-spikes/

# Apple log archaeology — was this work ever attempted on this Mac?
log show --predicate 'process == "<daemon>"' --last 7d --style compact | grep <signal>
```

Negative results are informative: **no log evidence + no on-disk residue + no system registration ≈ this work happened on the other Mac**. Don't redo the setup blindly; pivot (Rule 4 below).

### The discipline

When you record machine-specific work in a doc (spike journals, fixture captures, signing setup), put the **host machine identity** at the top:

```markdown
## Environment

- **Host macOS:** 26.4.1 (build 25E253), arm64 (M4 Pro)
- **Apple ID team:** FDMSRXXN73 (Luces Umbrarum)
- **Sample-source location (NOT in this repo):** `~/scratch/sftpmount-spikes/FSKitSample`
```

That block is what saves the next session 15 minutes of "wait, where did we do this?" investigation. The `(NOT in this repo)` annotation is the explicit signal that the state isn't synced.

Sources:
- SFTPmount 2026-05-16 (started Step 3 on M1 Max; pre-flight revealed no FSKitExp residue; log archaeology showed zero `fskitd` events for the spike date; confirmed work was on M4 Pro per journal header — pivoted to 26.5 re-validation).
- MousePlus 2026-05-01-a (post-Mac-restart resume; PROJECT_STATE flagged `#19` open but the inspector follow-ups were already in code; HID++ snapshot fixture `~/Desktop/hid-046d-b034-1x2-2026-04-29.json` referenced in session-e was missing on this machine — likely on M1 Max only).

---

## Rule 3: For accumulating files outside git, expect divergence; reconcile with union-merge

Some files accumulate independently on each Mac without being meaningful targets for git tracking. The canonical example: `.claude/settings.local.json` (Claude Code's per-project allowlist) — each Mac adds entries as the user approves new commands; both Macs end up with overlapping-but-different sets. Same pattern hits `.vscode/settings.json` user-side keys, MCP server lists, editor histories.

If the file is git-tracked: divergent commits at the next push. If it's Syncthing-tracked but not git-tracked: `*.sync-conflict-<date>-<id>.<ext>` on whichever Mac saw the second-arriving version.

### Symptom

Two flavors:

```
# Git tracking:
$ git push
 ! [rejected]        main -> main (fetch first)

# Syncthing tracking:
$ ls .claude/
settings.local.json
settings.local.json.sync-conflict-20260509-232258-7R66K7G.json
```

### The fix — Syncthing flavor (union-merge)

```python
# read both files, take the set-union of keyed entries, write the merged file
import json

with open("settings.local.json") as f:           local = json.load(f)
with open("settings.local.json.sync-conflict-...json") as f: remote = json.load(f)

allow = sorted(set(local["permissions"]["allow"] + remote["permissions"]["allow"]))
local["permissions"]["allow"] = allow

# back up the original first
import shutil; shutil.copy("settings.local.json", "settings.local.json.pre-merge-backup")

with open("settings.local.json", "w") as f: json.dump(local, f, indent=2)
# then delete the .sync-conflict file
```

After verifying the merged file works for a few days, delete the `.pre-merge-backup`.

Source: 2026-05-14 (`.claude/settings.local.json` union-merge — MenuBarPLUS 11 → 24 entries; SFTPmount 7 → 40 entries; both gained 5 MCP servers from the other Mac).

### The fix — git flavor

When two Macs both edited a tracked file independently:

```bash
git fetch origin main
git diff HEAD origin/main -- <file>          # see what's diverged
# Either accept theirs and re-add your unique edits as a new commit:
git checkout origin/main -- <file>
# (re-edit to add your unique changes)
# Or hand-merge by editing the file:
git pull --rebase                            # produces conflict markers; resolve and `git rebase --continue`
```

### The prevention

Add to root `.stignore` so Syncthing stops trying to sync these files at all:

```
**/.claude/settings.local.json
**/.git
**/.DS_Store
```

Each Mac then keeps its own copy locally; commit periodically to git via the existing `chore: add Claude Code permission allowlist entries` pattern. After enough commits both Macs converge naturally.

---

## Rule 4: Pivot when blocked by physical-machine access

When the primary task needs the other Mac, **don't redo setup blindly**. Find work that the current Mac CAN do and that informs the next attempt on the other Mac. Examples:

- Re-validate a documented plan against current OS/SDK state on this machine
- Inspect Apple framework headers / vendor SDK changes that may have shifted
- Update planning docs with discoveries
- Audit / log archaeology for negative-evidence questions ("did this even happen here?")
- Review code that doesn't need the missing state

Output: the next session on the other Mac is faster because the current session produced a rev-N+1 punch list.

Source: SFTPmount 2026-05-16 (Step 3 blocked on M4 Pro; ran 3 parallel read-only checks on M1 Max + 26.5; produced rev-3 punch list with 1 plan correction + 6 additional Info.plist keys + 1 entitlement decision — all without the registered extension. ~30 min of read-only work that closes a real chunk of the next M4 Pro session.)

---

## Detection: pre-flight before machine-sensitive work

Before resuming work that depends on machine-specific state, a 30-second pre-flight:

```bash
#!/usr/bin/env bash
# Pre-flight for any cross-Mac project resume

echo "=== identity ==="
hostname
sw_vers
uname -m

echo "=== git state (run from project root) ==="
git fetch origin main 2>/dev/null
git rev-list --left-right --count HEAD...origin/main

echo "=== machine-specific deps (customize per project) ==="
# e.g. for SFTPmount:
# pluginkit -m -v | grep -i fskit
# ls ~/scratch/sftpmount-spikes/ 2>/dev/null

# e.g. for MousePlus:
# ls ~/Desktop/hid-*-*.json
# xcrun --find xcodebuild
```

If `git rev-list` shows `0 N`, pull before doing anything. If it shows `N M`, stop and inspect (Rule 1). If machine-specific deps are missing, you're on the wrong Mac (or the OS update wiped them) — pivot to read-only validation rather than redoing setup (Rule 4).

---

## Quick-reference cheatsheet

| Symptom | Class | First move |
|---|---|---|
| `git push` rejected with "fetch first" | Rule 1 (divergent commits) | `git fetch && git rev-list --left-right --count HEAD...origin/main` to size the gap |
| Duplicate-looking commits in `git log --left-right HEAD...origin/main` | Rule 1 | reset + redo only the unique parts (don't merge) |
| `mount -t <YourFS>` returns "not recognized" | Rule 2 (machine-specific state) | `pluginkit -m -v` / `systemextensionsctl list` to verify registration on *this* Mac |
| Fixture / scratch dir referenced in journal isn't on disk | Rule 2 | check the journal's "Host machine" line; you may be on the wrong Mac |
| `.sync-conflict-*` file in `.claude/` or similar accumulating dir | Rule 3 | union-merge with python; backup; add to `.stignore` |
| `_index.md` reports drift between two Macs | Rule 1 + 3 | pre-flight `git fetch` first, then `sync-session-index.sh` after pull |
| Need the other Mac for the next step | Rule 4 | pivot to read-only re-validation that produces rev-N+1 input |
| "It worked yesterday on the other Mac" | Any | run pre-flight; verify state on this Mac before assuming continuity |

---

## The cross-cutting rule

> **Cross-machine state is opt-in. Git syncs commits. Syncthing syncs file-bytes. Nothing syncs the OS-level state your work depends on. Verify the machine before assuming the work.**

When your future self sits down at a different Mac and tries to resume, the friction is *always* in one of three places: divergent commits at integration time (Rule 1), missing per-machine OS state (Rule 2), or accumulated config drift in non-tracked files (Rule 3). The 30-second pre-flight catches all three before they cost 30 minutes.

---

*Related: `27_mcp-gotchas.md` (MCP / Syncthing umbrella-cwd pattern — same per-machine-state class), `28_xcode-signing-and-sourcekit.md` (per-machine `Debug.local.xcconfig` pattern — Rule 2 in concrete form), `32_git-workflow.md` (git baseline conventions).*
