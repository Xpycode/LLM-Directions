# Version a Release

Tag `main` with a `release/vX.Y.Z` tag so you can always jump back to a known-good state after merging.

**Use this every time you merge a feature branch into `main`** — once the branch is deleted, the tag is your only way to revisit that state by name.

See `57_checkpoint-discipline.md` (`release/` category) and `32_git-workflow.md` (Tags for Releases) for full context.

---

## Step 1: Pre-flight

Run in parallel:

```bash
git rev-parse --abbrev-ref HEAD       # must be: main
git status --porcelain                # must be: empty
git tag -l "release/v*" --sort=-v:refname | head -5   # see recent versions
```

If not on `main` or working tree dirty:
> "You're on `[branch]` with [N] uncommitted changes. Switch to `main` and clean up first, or tag the current HEAD anyway?"

---

## Step 2: Determine Next Version

Look at the most recent `release/vX.Y.Z` tag and ask:

> "Last release: `release/vX.Y.Z`. What kind of bump?
> 1. **patch** → `vX.Y.(Z+1)` — fixes, small additions
> 2. **minor** → `vX.(Y+1).0` — new feature, backward-compatible
> 3. **major** → `v(X+1).0.0` — breaking change
> 4. **custom** — specify a version"

If no `release/v*` tags exist yet, propose `v0.1.0` as the starting point.

---

## Step 3: Get Summary

Ask:
> "One-line summary of what this version contains?"

(This becomes the tag annotation — keep it terse, like a commit subject.)

---

## Step 4: Create the Tag

```bash
git tag -a release/vX.Y.Z -m "[summary]"
```

---

## Step 5: Push the Tag

```bash
git push origin release/vX.Y.Z
```

(Tags don't go to the remote with a normal `git push`. Push them explicitly.)

---

## Step 6: Confirm

Display:

```
Tagged: release/vX.Y.Z — [summary]

Jump back later with:
  git checkout release/vX.Y.Z              # detached HEAD, look around
  git checkout -b restore release/vX.Y.Z   # branch from this version

See what changed since:
  git diff release/vX.Y.Z..main

List all releases:
  git tag -l "release/v*" --sort=-v:refname
```

---

## Quick Mode

| Command | Behavior |
|---------|----------|
| `/version patch` | Auto-bump patch, prompt only for summary |
| `/version minor` | Auto-bump minor, prompt only for summary |
| `/version major` | Auto-bump major, prompt only for summary |
| `/version vX.Y.Z` | Use that exact version, prompt only for summary |

---

## When to Run This

- Right after merging a feature branch into `main` (before deleting the branch)
- Before any significant refactor on `main`
- When you ship something — even just to yourself

If in doubt, tag. Tags are cheap; lost states aren't.
