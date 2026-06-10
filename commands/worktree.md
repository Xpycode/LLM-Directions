# Worktree (Parallel Session Isolation)

Set up a **git worktree** so a second Claude session can work on a different branch **without
sharing a checkout** with this one.

## Why this exists

Two Claude sessions open in the *same folder* share one git checkout — git keeps a single HEAD per
working directory. The moment one session runs `git checkout other-branch`, it switches the branch
for **both**, and a commit from one can land on the branch the other just moved to (the theme-editor
cross-commit incident). A worktree gives the second session its **own directory with its own HEAD**,
so the two can sit on different branches at the same time, sharing the same repo history underneath.

`/status` and the session-start hook detect the collision; **`/worktree` is the fix.**

## What this command does (confirmed, never silent)

Run this *with* the user — confirm before creating anything.

### Step 1 — Establish context

```bash
git rev-parse --show-toplevel        # repo root (must be inside a git repo)
git rev-parse --abbrev-ref HEAD      # current branch
git worktree list                    # existing worktrees (don't duplicate)
```

If not inside a git repo, stop and say so. If `git worktree list` already shows a worktree that
fits what the user wants, point them at it instead of making another.

### Step 2 — Decide the branch and location

- **Branch name:** use the argument if the user gave one (`/worktree theme-editor`). Otherwise ask:
  *"New branch for the parallel work, or an existing one? What name?"*
  - New branch → `-b <name>` (created off current HEAD unless they name a base).
  - Existing branch → no `-b`. **Note:** a branch already checked out in another worktree can't be
    checked out again — pick a new name or detach.
- **Location:** default to a **sibling** of the repo, named `../<repo>-<name>` (kept *outside* the
  repo so it isn't nested inside the tracked tree). Confirm the path doesn't already exist.

Show the user the exact command before running it:

```bash
git worktree add ../<repo>-<name> -b <name>      # new branch
# or
git worktree add ../<repo>-<name> <existing>     # existing branch
```

### Step 3 — Create it and hand off

After `git worktree add` succeeds:

```bash
git worktree list                    # confirm it registered
```

Then tell the user, in plain language:

> Created an isolated worktree at `../<repo>-<name>` on branch `<name>`.
> **Open your second Claude session there** (`cd ../<repo>-<name>` and start `claude`). It now has
> its own HEAD — the two sessions won't fight over the branch.

This session's working tree is untouched — `git worktree add` never changes the current checkout.

### Step 4 — Cleanup (tell them how, don't do it now)

When the parallel work is merged/finished:

```bash
git worktree remove ../<repo>-<name>     # remove the dir (must be clean)
git branch -d <name>                     # delete the branch if fully merged
git worktree prune                       # tidy stale admin entries
```

## Multi-Mac caution (37_multi-mac-discipline.md)

A worktree is a **single-Mac, short-lived** device — create it, use it, remove it in the same
sitting. Its internal `.git` link is an **absolute path** valid only on the Mac that made it, so a
worktree dir that rides Syncthing to the other Mac will be a broken reference there. Don't rely on a
worktree surviving a Mac switch: before switching Macs, either `remove` it or merge its branch and
let the *commits* (which do travel via git) carry the work. Keep worktrees out of any path you sync
file-by-file.

## When to invoke

- `/status` or the session-start hook warned that two sessions share this folder.
- You knowingly want two sessions on two branches at once (e.g. one building a feature, one fixing a
  bug) without the checkout tug-of-war.

## What this command intentionally does NOT do

- Touch the current checkout (worktree add is non-destructive by design).
- Remove worktrees or delete branches — cleanup is a separate, deliberate step.
- Push anything — the new branch is local until you push it.
