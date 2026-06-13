# Arrive

Run when you **sit down at a Mac** to work on a project — especially after switching from the other
Mac and letting Syncthing settle. Answers the handover questions in plain English: *what did the
other Mac do, am I behind, is it safe to start, and where did I leave off?*

This is the per-project, human-readable version of the session-start git pre-flight. **Read-only** —
it fetches and reports; it never pulls, commits, or switches a branch without asking.

Pairs with `/depart` (run that when you leave). The "which Mac" labels come from `/depart` stamping
each commit — see Step 3.

**Detect mode:**
- `docs/PROJECT_STATE.md` exists → use `docs/` paths (installed project)
- else `./PROJECT_STATE.md` → root paths (master repo)

## Step 1 — Who am I?

```bash
MAC=$(cat ~/.claude/this-mac 2>/dev/null || scutil --get LocalHostName 2>/dev/null || hostname -s)
echo "This Mac: $MAC"
```

`~/.claude/this-mac` is a one-line label you set per machine (e.g. `M1 Max`). It lives **outside** the
Syncthing folder, so it never travels — that's the whole point: same path on every Mac, different
content. If it's missing, the Mac's own name is used. (Don't put this file inside `~/ProgrammingProjects`
or Syncthing will overwrite it with the other Mac's copy.)

## Step 2 — Is this a git project with a remote?

```bash
git rev-parse --is-inside-work-tree >/dev/null 2>&1 && echo "git:yes" || echo "git:NO"
git remote get-url origin >/dev/null 2>&1 && echo "remote:yes" || echo "remote:NO"
```

- **No git** → "This project isn't under git, so there's nothing to compare across Macs — its files
  travel by Syncthing only." Skip to Step 5.
- **git but no remote** → "This project has git history but no GitHub remote, so I can't see what the
  other Mac did — git history doesn't travel between your Macs without one. Want to add a remote? That's
  the only way `/arrive` can compare Macs here." Skip to Step 5.
- **git + remote** → continue.

## Step 3 — Fetch and read the other Mac's last work (read-only)

```bash
git fetch --quiet 2>/dev/null
git status -sb | head -1
# last commit on your upstream branch: how-long-ago, author, subject, and the Mac that pushed it
git log -1 @{u} --format='%cr%n%an%n%s' 2>/dev/null
git log -1 @{u} --format='%(trailers:key=Handoff-from,valueonly)' 2>/dev/null
```

The `Handoff-from:` value is the machine `/depart` stamped into that commit (immutable, never
conflicts). If empty, the commit predates `/depart` — just report the author/date.

## Step 4 — Plain verdict (no SHAs — say what it means)

Translate `git status -sb` into one line:

- **up to date** → "✓ Up to date. Last work: <other Mac>, <when> — \"<subject>\". Good to start."
- **behind N** → "⚠ <other Mac> pushed <when> (\"<subject>\") — you're N commits behind. Pull before you
  start?" Offer `git pull --ff-only`; pull only on **yes**.
- **ahead M** → "You have M commits here not pushed yet (from a previous session on this Mac). Fine to
  keep working — remember `/depart` when you leave."
- **diverged (ahead M + behind N)** → "⚠ Both Macs have unpushed work — these have diverged. Don't pull
  blindly." Point to `37_multi-mac-discipline.md` Rule 1. Do **not** auto-pull or reset.

## Step 5 — Where did I leave off?

Read `PROJECT_STATE.md` and show just the **Now → Focus** and **Now → Next** lines (one each). That's
the "what was I doing" reminder. Don't dump the whole file.

## Step 6 — Same-folder session collision check (light)

```bash
bash ~/.claude/hooks/session-guard.sh 2>/dev/null \
  || bash /Users/sim/ProgrammingProjects/0-DIRECTIONS/__DIRECTIONS/hooks/session-guard.sh 2>/dev/null
```

No output → say nothing. A warning block → show it plainly: another Claude session shares this
checkout; coordinate git in one, or split with `/worktree`.

## When to invoke

- First thing when you start work on a Mac, especially after switching machines.
- After Syncthing shows the folder "Up to Date".

## What it intentionally does NOT do

- Pull, reset, commit, or switch branches on its own — it reports and *offers*. You confirm.
- Touch any file — it's read-only except for a pull you explicitly approve.

Source: `37_multi-mac-discipline.md`, `commands/depart.md`, `hooks/session-start.sh` (same fetch logic).
