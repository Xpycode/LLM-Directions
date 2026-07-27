<!--
TRIGGERS: cross-mac, multi-mac, M1 Max, M4 Pro, multiple Macs, working from two Macs,
          Syncthing sync-conflict, git push rejected "fetch first", divergent commits,
          duplicate commits across machines, "we did this on the other Mac",
          machine-specific state, per-machine spike context, fixture missing on this Mac,
          settings.local.json conflict, .stignore, log archaeology,
          two Claude sessions same folder, shared checkout, commit on wrong branch,
          git worktree, parallel sessions, session collision, /worktree
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
| Effectively identical | verify `git diff origin/main` shows no genuinely-unique local work, **then** `git reset --hard origin/main` (drops your duplicate; reflog-recoverable) → re-apply only the unique parts as a new focused commit |
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

### Rule 1a: The dual-carry trap — git AND Syncthing over the same working tree

The duplicate-commit class has a quieter, more confusing variant when **the repo lives inside a
Syncthing folder** (e.g. anything under `~/ProgrammingProjects`, which is a Syncthing root). Now every
file is carried by *two* systems with different notions of "synced," and they race:

1. **This Mac** edits tracked files (code, docs) and leaves them **uncommitted**.
2. **Syncthing** silently copies those working-tree bytes to the other Mac — uncommitted edits and all.
3. **Other Mac** commits them and pushes to origin.
4. **This Mac** reopens: `git fetch` says "behind N," yet `git status` *still* shows the same files as
   modified/untracked. They are **byte-identical to origin** (Syncthing kept them current) but git here
   never recorded the commit. Result: a phantom "uncommitted duplicate of work that's already shipped."

This is not a discipline failure — it's structural. **Git carries commits; Syncthing carries file-bytes
including the *uncommitted* ones git can't see as done.** The tell: you're `behind` *and* dirty, and the
dirty files diff clean against `origin` (`git diff origin/main -- <file>` shows zero lines).

**Recovery** (when local dirty == origin, confirmed): the whole thing is one move —
`git reset --hard origin/main`. It overwrites the modified *tracked* files **and** checks out the
untracked-but-already-on-origin files (they exist in the target commit, so reset writes them and they
become tracked & clean) — no separate `git restore`/`rm`/`clean` step. `git clean -nd` afterward should
come back empty.

If a risk-guard hook blocks `reset --hard` (Claude Code's fable5 `pre-tool-guard` does, by design — the
verb is irreversible and the guard can't see that you've *proved* the discard lossless), take the route
that destroys nothing and lands identically:

```bash
git stash push --include-untracked -m "phantom: Syncthing-carried, identical to origin"
git merge --ff-only origin/main    # fast-forwards; checks out the untracked-in-target files
```

Leave the stash as the undo net. To confirm afterwards that it holds nothing new, compare each entry to
what landed. Two traps make the naive loop lie:

1. **Untracked entries aren't at `stash@{0}:<path>`.** A stash is a merge commit; the untracked files
   live on its *third parent*, `stash@{0}^3:<path>`.
2. **`git rev-parse` echoes the unresolved argument to stdout when it fails.** So the obvious
   `a || b` fallback captures *the error text plus the real hash*, and every untracked file reports
   DIFFERS even when the hashes match. Same failure family as the `diff -q` SIGPIPE inversion above:
   the tool's non-silent failure poisons the comparison, not the data. Use **`-q --verify`**, which
   stays quiet and returns nothing on failure.

```bash
for f in $(git stash show --include-untracked --name-only stash@{0}); do
  s=$(git rev-parse -q --verify "stash@{0}:$f" || git rev-parse -q --verify "stash@{0}^3:$f")
  h=$(git rev-parse -q --verify "HEAD:$f")
  [ -n "$s" ] && [ "$s" = "$h" ] && echo "IDENTICAL $f" || echo "DIFFERS $f"
done
```

All IDENTICAL = the stash is redundant and safe to `git stash drop` (and the dropped commit still sits
in the reflog for the usual ~2 weeks if you want it back).

**Verify byte-identity first — and use the right oracle.** Confirm each dirty path is identical to origin
before discarding, so you never drop genuinely-unique local work. Two trustworthy tests:

- `git hash-object <file>` **==** `git rev-parse origin/main:<file>` — compares the content SHA to origin's
  blob; exact, fast, and immune to EOL/whitespace/trailing-newline noise. This is what `session-start.sh`
  now runs automatically (≤200 dirty files) to print a *confirmed* "byte-identical phantom, lossless to
  `reset --hard`" verdict instead of a guess.
- `git diff --quiet origin/main -- <file>` — normalization-aware; exit 0 = identical.

**Do NOT** trust `git show origin/main:<file> | diff -q - <file>` for this. `diff -q` exits at the first
difference, killing the upstream `git show` with SIGPIPE; under `set -o pipefail` the pipeline then reports
non-zero and can **invert** the verdict (flagging identical files as different, or vice-versa). A content
oracle (hash-object) or a full `diff -` that reads both streams is the safe choice. (Burned by this
2026-06-13 — three checks disagreed; the hash/`git diff --quiet` pair was right.)

**Variant: the untracked-file collision — a `… 2` copy is NOT reliably the throwaway.**

Everything above is the *tracked*-file face of dual-carry. Untracked files show a different one, because
Syncthing resolves the two cases differently:

- **Tracked file** — Syncthing overwrites it in place. Git reports a plain `modified`. No duplicate.
- **Untracked file** — an incoming file colliding with a local copy of the same name cannot be silently
  overwritten, so Syncthing parks one of them beside the other with a ` 2` suffix.

The trap is what the suffix means. **` 2` marks the file that arrived and lost the name race — not the
redundant one.** When the local copy is the *stale* one (this Mac never got the update, or got it as an
untracked file git couldn't reconcile), the newcomer — the **canonical** version — is what gets suffixed.
Deleting "the duplicate" on sight throws away the current work and reinstates the old.

Worse, one single upstream change can surface **two different ways at once**: a content diff on the
tracked artifact *and* a phantom duplicate beside its untracked sibling. Reading either symptom alone
tells you the wrong story.

**Resolve by content, never by name.** Anchor on something that provably shipped — a tracked artifact, or
the commit that built the release — and ask which copy matches it:

```bash
# Which loose folder matches the tracked zip that actually shipped?
unzip -l "Icon set.zip"                       # working-tree (Syncthing-updated) — sizes + mtimes
git show HEAD:"Icon set.zip" > /tmp/head.zip  # the previous, committed version
unzip -l /tmp/head.zip
# then md5 each candidate folder's files against both extractions
```

Identity by *name* is a guess; identity by *content* is a verdict. In the case that produced this rule the
verdict inverted the intuition: `… 2` was the final artwork, the un-suffixed folder was a discarded
earlier concept.

**Before deleting the loser, prove it's recoverable.** `rm -rf` on an *untracked* folder is unrecoverable —
git cannot restore what it never held. Make it reversible first by confirming every file is byte-identical
to something already in history (`md5 -q` against the extracted `HEAD` blob), which turns the delete into
a `git show HEAD:<path>` away from undo. Then delete.

**Prevention:** track the loose files, not just the archive. A zip is one opaque blob to git — every
re-export reads as `Bin 5000 -> 4717 bytes` and nothing more, which is precisely why the drift was
unreadable. Tracking the unpacked files *alongside* the zip gives git something diffable, and — because
tracked files sync in place — removes the untracked-name collision that creates `… 2` copies at all.

**Two structural defenses:**

- **Close the uncommitted-work window (lifecycle).** The race only opens while tracked work sits
  *uncommitted* for Syncthing to carry. If every session **commits + pushes before you walk away**, the
  other Mac gets a clean fast-forward and this Mac's tree is clean — no phantom dups. The Directions
  hooks enforce this as *confirmed* (never silent) actions:
  - `hooks/session-start.sh` (`SessionStart`) — fetches, reports ahead/behind **and** whether the tree
    is dirty. In the `behind + dirty` case it hashes each dirty path against origin's blob and prints a
    *computed* verdict: a confirmed "byte-identical Syncthing phantom — lossless to `reset --hard`" when
    all match, or a per-file "compare before discarding" caution when any differs.
  - `hooks/session-stop.sh` (`Stop`) — debounced (~20 min) `systemMessage` nudge when work is
    uncommitted or unpushed. Never blocks.
  - `/log` Step 6 — offers to commit **and push** in one confirmed step (an unpushed commit is
    as invisible to the other Mac as an uncommitted file).
  - **The hook scripts travel via git; the wiring does not.** Run `bash hooks/install.sh` once per Mac
    after cloning/pulling — it symlinks the hooks + statusline into `~/.claude/` and registers them in
    `settings.json` (idempotent, preserves existing non-Directions hooks). `--dry-run` previews. The
    forgotten-wiring-on-the-second-Mac gap was itself a recurring source of these collisions.
- **Stop the dual-carry (boundary).** Let git own tracked files and Syncthing carry only the gitignored
  files that genuinely need it (session logs). In the Syncthing root's `.stignore`:

  ```gitignore
  // Directions master: git owns tracked files; Syncthing carries only the gitignored
  // session logs. Kills the git+Syncthing dual-carry race. !include precedes the ignore.
  !/0-DIRECTIONS/__DIRECTIONS/sessions/**
  /0-DIRECTIONS/__DIRECTIONS/**
  ```

  `.git` is already excluded globally (syncing it makes branch checkouts look like mass deletions —
  02_Design incident 2026-06-03). `.stignore` itself rides Syncthing, so the rule propagates; watch the
  other Mac's sync status briefly after adding it, since a wrong pattern fails *silently*.

Source: Directions master repo, 6 cross-Mac collisions Apr–Jun 2026; the dual-carry mechanism isolated
2026-06-10 (behind-2 + dirty tree whose files diffed clean against origin). Recurred 2026-06-13 at
behind-10 after the *other* Mac was erased-and-restored: Syncthing had carried the current files onto
this (stale-`.git`) Mac, so 9 modified + 12 untracked files all showed as local changes yet hashed
byte-identical to origin — the textbook phantom. `git reset --hard origin/main` reconciled it in one move
(the 12 untracked files were in the target commit, so they checked out clean; `git clean -nd` empty
after). This is what hardened the hook into a computed verdict and added the `diff -q` SIGPIPE caveat.
The untracked-collision variant came from MediaIngest 2026-07-24/26: the other Mac replaced the app-icon
concept and re-exported its handoff bundle; the tracked zip synced in place (`modified`) while the loose
folder landed as `design_handoff_mediaingest_icon 2`. Content beat naming — the `… 2` copy was byte-identical
to the updated zip and to the palette compiled into the shipped icon generator, so the *un-suffixed* folder
was the stale one. Cost a full session to diagnose from symptoms alone.

### Rule 1b: The fresh/reset Mac — no `.git` at all (the bootstrap case)

Rule 1a assumes a repo exists. A freshly-set-up or erased-and-restored Mac has the stronger version:
Syncthing carried the **working tree**, but `.git` is globally excluded (above), so the project has
**source on disk and no repo**. `git status` → "not a git repository." Canonical history lives **only on
`origin`**.

The trap: treating the on-disk files as authoritative and starting to edit/commit — or, worse, blindly
`git init` + commit, forking a brand-new root history disconnected from origin's. Reconcile to origin
**first**, without overwriting anything:

```bash
gh auth setup-git                        # GitHub here is HTTPS-via-gh (no SSH key on these Macs)
git init -b main
git remote add origin <project's canonical URL>   # from the project's PROJECT_STATE / `gh repo list`
git fetch origin
git reset --mixed origin/main            # HEAD+index → origin; WORKING TREE LEFT UNTOUCHED
git status --short --untracked-files=no   # ← THE CHECK
```

Read the check:
- **0 tracked changes** → on-disk == origin. Done; adopt as-is. **Do not `reset --hard`** — nothing to
  gain, only risk.
- **Any tracked diff** → Syncthing carried Mac-local work origin lacks (or the local copy is *stale* and
  origin is newer). **Stop**, `git diff origin/main -- <file>` each path, and reconcile by hand — re-apply
  your genuinely-unique edits *onto* origin's current version. Never blind-`--hard` either direction.

`--mixed` (not `--hard`) is the whole point: it reveals the truth *before* anything is overwritten — the
same "verify byte-identity first" discipline as Rule 1a's recovery, applied to a from-scratch repo.

Full generalized procedure + per-Mac constants (commit identity, gh auth, expected-clean untracked tool
dirs): the global **`git-bootstrap` skill**.

Source: Conjoyn 2026-06-13 (fresh Mac, no `.git`; mixed-reset proved 0 tracked drift → clean adopt, no
`--hard` needed). Counter-case same day: bootstrapping *this* master found the local copy **stale vs
origin** (missing Rule 5 + `/worktree`) — the check caught it, so the doc edit was re-applied onto
origin's version instead of clobbering it.

### Rule 1c: The merged-branch blind spot — when the pre-flight's green is *wrong*

Rule 1a's tell is "you're `behind` **and** dirty." This variant is worse, because **the pre-flight
reports fully green** and there is no tell at all.

#### Symptom

You are on a feature branch that was merged into `main` weeks ago and then abandoned. `main` has since
moved far ahead. The session-start check prints:

```
✓ 'fix/whatever' in sync with origin/fix/whatever, working tree clean.
```

Both halves are **true**. The branch really is in sync with `origin/<branch>` — that upstream is equally
frozen. The tree really is clean *by that branch's reckoning*. `git status -sb` compares HEAD to **its own
upstream** and nothing else; "has the default branch moved past me?" is a question it structurally never
asks. So the guard that exists to catch cross-Mac drift waves through the worst case of it.

Then Syncthing supplies the payload: it carries `main`'s **files** onto a checkout whose `.git` still
points at the stale branch. Every file `main` has and the branch lacks shows as `M` or `??` —
indistinguishable from real uncommitted work. A session that trusts the green pre-flight, sees "dirty
tree," and helpfully commits it will **re-commit and push work that shipped weeks ago**.

#### The fix — ask the second question, always

```bash
D=$(git symbolic-ref -q --short refs/remotes/origin/HEAD || echo origin/main)
git rev-list --count HEAD..$D                    # has the default branch moved past me?
git merge-base --is-ancestor HEAD $D && echo "ALREADY MERGED — this branch is finished"
```

`--is-ancestor` is the decisive one: true means every commit on this branch is already in `main`, so
**nothing here is new** no matter what `git status` shows. Confirm with the content check before acting:

```bash
git diff $D HEAD -- '*.swift'    # empty ⇒ literally nothing unique on this branch
```

**Recovery:** do **not** commit the working tree, and do not merge the branch. Rebranch from the default
branch and cherry-pick only what is genuinely new:

```bash
git switch -c <fresh-branch> origin/main
git cherry-pick <the one or two real commits>
```

Then verify the replay actually *works* on the new base — a clean cherry-pick onto a base that moved is
not the same as a correct one. Run the suite and compare the count against the last known-good number.

#### The discipline

- **Never let "in sync, tree clean" authorize a commit on a non-default branch.** It is a statement about
  a frozen upstream, not about your work.
- **A dirty tree on a stale branch is evidence of Rule 1a, not of unsaved work** — until proven otherwise
  by diff, not by inspection.
- **Prefer deleting merged branches immediately.** `git branch -d` refuses unless every commit is
  reachable elsewhere, so it doubles as the check — and a branch that no longer exists cannot be
  accidentally resumed on the other Mac.
- Distrust in-repo "NOT committed yet" notes; verify with `git cat-file -t <sha>`. Such a note is true
  when written and stale hours later, and it compounds this trap by lending the phantom work credibility.

Source: Penumbra 2026-07-27 — `fix/code-review-2026-07`, merged 2026-07-18, `origin/main` 32 ahead; the
pre-flight printed green and six commits of already-shipped work were re-committed and pushed. Fifth
occurrence of the family (2026-06-10 / 06-14 / 07-02 / 07-12 / 07-27), first where the guard actively
said go. Reconciled 2026-07-28 by the rebranch+cherry-pick recipe above; replay verified by a clean-build
suite run matching the pre-reconcile count exactly (503/1/0). The global pre-flight in `~/.claude/CLAUDE.md`
now emits the `vs origin/main: behind N · already-merged=YES|no` line.

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

## Rule 5: Two sessions, one checkout — the same-Mac collision

Rules 1–4 are about *two Macs*. This one is the opposite axis: **one Mac, two Claude sessions open in
the same project folder.** It bites even when you never leave your desk.

Two `claude` CLI sessions in the same directory share **one git checkout** — git keeps a single HEAD
per working tree. The moment one session runs `git checkout other-branch`, it switches the branch for
**both** sessions, and a commit from one can land on the branch the other just moved to. (Mirror of the
Rule 1 duplicate-commit cost, but the "other worker" is *you, in the other window*, not the other Mac.)

### Symptom

You commit work in session A; it lands on a branch you didn't expect — because session B ran a
`checkout` that silently moved HEAD under A. Or a commit you intended for `main` shows up on
`feature/x`. The tell is that *nobody* on the other Mac was involved; the divergence is local and
within the same minute.

### The fix

Don't try to share one checkout between two sessions — give the second its own. A **git worktree** is a
second working directory with its **own HEAD**, backed by the same repo history:

```bash
git worktree add ../<repo>-<name> -b <branch>   # isolated dir + new branch
cd ../<repo>-<name>                             # point the 2nd session here
# ... when done:
git worktree remove ../<repo>-<name>
```

Two sessions in **different worktrees** are safe — they don't share a HEAD. The `/worktree` command
automates this; `/status` and the session-start hook both surface the collision so you catch it before
a stray checkout.

### The discipline

- **Detection is wired.** `hooks/session-guard.sh` (run from `SessionStart` and `/status`) lists running
  `claude` sessions, resolves each to its worktree toplevel, and warns — warn-only — when 2+ share one.
  It's worktree-aware, so the safe split-across-worktrees pattern never false-positives. Pure local
  process inspection (no lock files), so nothing goes stale and it never touches git.
- **One git driver.** If you *do* keep two sessions in one folder, run all `git checkout` / branch ops in
  exactly **one** of them; let the other only read or edit files.
- **Worktrees are single-Mac, short-lived (don't cross Rule 1a with this).** A worktree's internal `.git`
  link is an **absolute path** valid only on the Mac that made it — a worktree dir that rides Syncthing to
  the other Mac is a broken reference there. Create it, use it, remove it in the same sitting; before
  switching Macs, `remove` it and let the *commits* (which travel via git) carry the work. Keep worktree
  dirs out of any file-by-file synced path.

Source: Directions master repo, 2026-06-10 — the theme-editor incident (a second session ran `checkout
feature/theme-editor`, moving HEAD for both, so the first session's docs commit landed on the wrong
branch). Fixed with `hooks/session-guard.sh` + the `/worktree` helper.

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
| `behind N` **and** dirty tree, but dirty files diff clean vs `origin` | Rule 1a (dual-carry) | confirm byte-identity via `git hash-object` vs `git rev-parse origin/main:<file>` (not `diff -q` in a pipe), then `git reset --hard origin/main` (one move; handles tracked + untracked-in-target); close the window with commit-on-end |
| A `<name> 2` / `… 2` copy appeared beside an untracked file | Rule 1a (dual-carry, untracked variant) | **don't assume `… 2` is the throwaway** — it marks the file that *arrived*. Identify by content against a tracked artifact (`unzip -l` the working-tree vs `HEAD` archive; `md5 -q` each candidate), then prove the loser is byte-identical to something in history before `rm -rf` |
| `reset --hard` blocked by a risk-guard hook | Rule 1a | same end state, nothing destroyed: `git stash push -u -m "phantom"` → `git merge --ff-only origin/main`; the stash stays as the undo net |
| `mount -t <YourFS>` returns "not recognized" | Rule 2 (machine-specific state) | `pluginkit -m -v` / `systemextensionsctl list` to verify registration on *this* Mac |
| Fixture / scratch dir referenced in journal isn't on disk | Rule 2 | check the journal's "Host machine" line; you may be on the wrong Mac |
| `.sync-conflict-*` file in `.claude/` or similar accumulating dir | Rule 3 | union-merge with python; backup; add to `.stignore` |
| `_index.md` reports drift between two Macs | Rule 1 + 3 | pre-flight `git fetch` first, then `sync-session-index.sh` after pull |
| Commit landed on a branch you didn't expect, no other Mac involved | Rule 5 (same-folder collision) | check for a 2nd `claude` session in this folder; split it into a `/worktree` |
| Two Claude sessions open in the same project folder | Rule 5 | one git driver, or isolate the 2nd with `git worktree add` |
| Need the other Mac for the next step | Rule 4 | pivot to read-only re-validation that produces rev-N+1 input |
| "It worked yesterday on the other Mac" | Any | run pre-flight; verify state on this Mac before assuming continuity |

---

## The cross-cutting rule

> **Cross-machine state is opt-in. Git syncs commits. Syncthing syncs file-bytes. Nothing syncs the OS-level state your work depends on. Verify the machine before assuming the work.**

When your future self sits down at a different Mac and tries to resume, the friction is *always* in one of three places: divergent commits at integration time (Rule 1), missing per-machine OS state (Rule 2), or accumulated config drift in non-tracked files (Rule 3). The 30-second pre-flight catches all three before they cost 30 minutes.

And on a *single* Mac there's a fourth, orthogonal trap (Rule 5): two Claude sessions in one folder sharing one checkout, where a `checkout` in one moves HEAD for both. Different axis, same root reflex — **know which working tree you're actually in before you act on git.**

---

*Related: `27_mcp-gotchas.md` (MCP / Syncthing umbrella-cwd pattern — same per-machine-state class), `28_xcode-signing-and-sourcekit.md` (per-machine `Debug.local.xcconfig` pattern — Rule 2 in concrete form), `32_git-workflow.md` (git baseline conventions — its "never commit to main" rule is scoped to application code; docs repos, including this one, commit straight to `main` as their normal workflow, which is what Rule 1's commit-before-you-walk-away discipline above assumes).*
