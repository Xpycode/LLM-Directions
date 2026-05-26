<!--
TRIGGERS: git, commit, branch, merge, main, version control, undo, reset, tag, release
PHASE: any
LOAD: full
-->

# Git Workflow for Solo Developers

**Simple but disciplined version control.**

*You work alone, but future-you is your teammate.*

---

## The Golden Rule

**Never commit directly to `main`.**

Main should always be deployable. Work on branches, merge when stable.

---

## Branch Strategy

### Creating Branches

```bash
# Feature work
git checkout -b feature/dark-mode
git checkout -b feature/export-pdf

# Bug fixes
git checkout -b fix/crash-on-launch
git checkout -b fix/save-not-working

# Experiments (might throw away)
git checkout -b experiment/new-ui-approach
git checkout -b spike/test-library
```

### Naming Convention

| Prefix | Use For | Example |
|--------|---------|---------|
| `feature/` | New functionality | `feature/settings-screen` |
| `fix/` | Bug fixes | `fix/memory-leak` |
| `experiment/` | Trying something | `experiment/swiftui-charts` |
| `refactor/` | Code cleanup | `refactor/extract-service` |

---

## Commit Messages

### Format

```
[What changed]: [Why it changed]

[Optional: More details]
```

### Good Examples

```bash
git commit -m "Add dark mode toggle: users requested theme options"

git commit -m "Fix crash on empty file: guard against nil array"

git commit -m "Refactor settings: extract to dedicated ViewModel for testability"
```

### Bad Examples

```bash
# Too vague
git commit -m "Fixed bug"
git commit -m "Updates"
git commit -m "WIP"

# No why
git commit -m "Changed color to blue"  # Why blue?
```

### When to Commit

- **Do commit:** Working increments, completed thoughts
- **Don't commit:** Broken code, debug prints left in, "WIP" without context

---

## Merging to Main

### When to Merge

✅ Feature works as intended
✅ No debug prints or commented code
✅ Tested the actual user flow
✅ No known bugs introduced

### How to Merge

```bash
# Switch to main
git checkout main

# Merge your branch
git merge feature/dark-mode

# Delete the branch (it's merged)
git branch -d feature/dark-mode
```

### After Merging

**Tag the merge before deleting the branch** (see next section). Once `feature/dark-mode` is gone, the tag is your only named way back to that state.

---

## Tags for Releases

**Tag every merge to `main`.** Branches get deleted; tags stay forever and cost nothing.

### The Rule

```
merge feature → main
    └── git tag -a release/vX.Y.Z -m "summary"
    └── git push origin release/vX.Y.Z
    └── git branch -d feature/...   ← only AFTER tagging
```

Use `/version` to do all of this with prompts (see `commands/version.md`).

### Version Numbering (semver-ish)

| Bump | When | Example |
|------|------|---------|
| **patch** `vX.Y.Z+1` | Small fix, doc update, tiny addition | `v0.1.0 → v0.1.1` |
| **minor** `vX.Y+1.0` | New feature, backward-compatible | `v0.1.1 → v0.2.0` |
| **major** `vX+1.0.0` | Breaking change | `v0.9.0 → v1.0.0` |

Stay in `v0.x` until the project is genuinely stable.

### Creating Tags Manually

```bash
# Annotated tag (preferred — carries a message + author + date)
git tag -a release/v0.2.0 -m "Add export feature and dark mode"

# Push it (normal git push does NOT include tags)
git push origin release/v0.2.0

# Tag a past commit retroactively
git tag -a release/v0.1.0 abc1234 -m "Baseline"
```

### Jumping Back

```bash
# Look around (detached HEAD — read-only)
git checkout release/v0.2.0

# Branch off a release to fix or restore something
git checkout -b restore/something release/v0.2.0

# See what's changed since
git diff release/v0.2.0..main
```

### Listing Tags

```bash
git tag -l "release/v*" --sort=-v:refname   # newest first
git show release/v0.2.0                     # tag details + diff
```

### Other Tag Categories

This repo also uses `phase/`, `safe/`, `wave/`, `decision/` for in-progress checkpoints — see `57_checkpoint-discipline.md`. `release/` is reserved for "this is what main looked like after that merge."

---

## The "Oh Shit" Commands

### Undo Last Commit (Keep Changes)

```bash
# Uncommit but keep files changed
git reset --soft HEAD~1
```

### Undo Last Commit (Discard Changes)

```bash
# Uncommit AND discard changes (CAREFUL)
git reset --hard HEAD~1
```

### Discard All Uncommitted Changes

```bash
# Throw away everything not committed (CAREFUL)
git checkout .
# Or for newer git:
git restore .
```

### Recover Deleted Branch

```bash
# Find the commit
git reflog

# Recreate branch from that commit
git checkout -b recovered-branch abc1234
```

### Undo a Merge

```bash
# If you haven't committed after merge
git merge --abort

# If you already committed the merge
git revert -m 1 HEAD
```

### See What Changed

```bash
# What files changed
git status

# What lines changed (not staged)
git diff

# What lines changed (staged)
git diff --staged

# History
git log --oneline -10
```

---

## Quick Reference

| Task | Command |
|------|---------|
| New branch | `git checkout -b feature/name` |
| Switch branch | `git checkout branch-name` |
| See branches | `git branch` |
| Stage all | `git add .` |
| Commit | `git commit -m "message"` |
| Merge to main | `git checkout main && git merge branch` |
| Tag release (after merge) | `/version` or `git tag -a release/vX.Y.Z -m "msg" && git push origin release/vX.Y.Z` |
| Delete branch | `git branch -d branch-name` |
| Jump back to a release | `git checkout release/vX.Y.Z` |
| List releases | `git tag -l "release/v*" --sort=-v:refname` |
| Undo last commit | `git reset --soft HEAD~1` |

---

## Claude Integration

Tell Claude about your git workflow:

```
Before implementing, create a feature branch.
After changes are working, commit with a message explaining WHY.
Don't commit to main directly.
```

Add to your CLAUDE.md:
```markdown
## Git Rules
- Never commit directly to main
- Branch names: feature/, fix/, experiment/
- Commit messages: what + why
- Merge only when tested and working
- Tag every merge to main as `release/vX.Y.Z` BEFORE deleting the branch
  (use the `/version` slash command)
```

---

*Simple discipline now prevents "what happened to my code?" later.*
