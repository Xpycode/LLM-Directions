<!--
TRIGGERS: git, commit, branch, merge, main, version control, undo, reset, tag, release,
          git init, git clone, where does the repo live, .git location, repo root,
          re-root repo, nested .git, untracked docs, clone into subfolder
PHASE: any
LOAD: full
-->

# Git Workflow for Solo Developers

**Simple but disciplined version control.**

*You work alone, but future-you is your teammate.*

> **No pull requests.** This is a solo workflow — there's no reviewer and no remote review step. Never suggest opening a PR, "pushing for review," or a fork/PR flow. You branch, commit, and **merge to `main` locally** (see "Merging to Main" below). Pushing to GitHub, when a remote exists, is just a backup/mirror — not a review gate.

---

## The Golden Rule

**Never commit directly to `main`.**

Main should always be deployable. Work on branches, merge when stable.

---

## Where the Repo Lives

**The repository lives at the app root — one repo per app, wrapping everything.**

```
MyApp/                    ← git init HERE.  .git/ lives at this level.
├── 01_Project/           ← Xcode project + source (tracked)
│   └── MyApp/
├── 02_Design/            ← tracked
├── 03_Screenshots/       ← tracked
├── 04_Exports/           ← gitignored, but inside the repo
├── docs/                 ← Directions docs — MUST be tracked
├── .git/                 ← ← ← right here, at the root
├── .gitignore
└── CLAUDE.md
```

One repo at the root tracks the source **and** the Directions docs, design files, and screenshots together. That's the point — your session logs, decisions, and `PROJECT_STATE.md` are versioned alongside the code that they describe.

### ⚠️ The clone-into-subfolder trap

The #1 way this goes wrong: you `git clone` an existing GitHub repo, and the clone drops `.git/` **inside** the cloned folder — typically `01_Project/MyApp/.git`. Now git only tracks the Xcode source. `docs/`, `02_Design/`, `03_Screenshots/`, and the `01_Project/` wrapper itself are all **outside the repo and silently untracked.**

```bash
# ❌ WRONG — produces 01_Project/MyApp/.git
cd MyApp/01_Project
git clone https://github.com/you/MyApp.git    # .git ends up nested

# ✅ RIGHT — clone into a temp dir, then lift the source into 01_Project,
#    and init the repo at the app root instead.
```

### Verify where your `.git` actually is

```bash
# From the app root — should print ".git" (root) , NOT "01_Project/MyApp/.git"
git rev-parse --show-toplevel
# or, to find every repo boundary in the tree:
find . -name .git -maxdepth 4
```

If `--show-toplevel` points anywhere below the app root, the repo is misplaced.

### Recovery — re-rooting a misplaced repo

If `.git` is stuck in `01_Project/MyApp/`, move it up to the app root **without losing history**:

```bash
cd MyApp                                  # the app root
mv 01_Project/MyApp/.git .                # lift the repo boundary up
mv 01_Project/MyApp/.gitignore . 2>/dev/null || true
git status                                # now sees 02_Design, docs/, etc. as untracked
# Add a root .gitignore (see 13_folder-structure.md) BEFORE staging,
# so 04_Exports/, DerivedData/, .DS_Store don't get committed.
git add -A
git commit -m "Re-root repo at app level: track docs, design, screenshots"
```

Do this with **no other session/agent active in that app** and a clean working tree (commit or stash first). If there's a remote, the remote URL is preserved by the move — verify with `git remote -v`.

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

Your main branch now has the new work. The feature branch is deleted (its history is preserved in main).

---

## Tags for Releases

### When to Tag

- App is ready for distribution
- Major milestone reached
- Before significant changes (so you can go back)

### Creating Tags

```bash
# Simple version tag
git tag v1.0

# Version with message
git tag -a v1.1 -m "Added export feature and dark mode"

# Tag a specific commit (retroactively)
git tag -a v0.9 abc1234 -m "Last stable before refactor"
```

### Listing Tags

```bash
git tag           # List all tags
git show v1.0     # Show tag details
```

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
| Delete branch | `git branch -d branch-name` |
| Tag release | `git tag -a v1.0 -m "message"` |
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
```

---

*Simple discipline now prevents "what happened to my code?" later.*
