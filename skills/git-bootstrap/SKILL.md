---
name: git-bootstrap
description: Reconcile a project that has source on disk but NO .git repo onto its canonical GitHub origin, WITHOUT overwriting local work. Invoke when a project directory has files but `git status` says "not a git repository" — a freshly-set-up or erased-and-restored Mac where Syncthing carried the working tree but .git is excluded from sync. Safe init → fetch → --mixed reset → verify (HTTPS via gh, never blind --hard). Do this BEFORE any edit or commit.
---

# git-bootstrap

**When:** a project has **source on disk but no `.git`** — `git status` → *"not a git repository."*
Canonical history lives **only on GitHub `origin`**. This is the fresh/reset-Mac case
(Syncthing carries the working tree; `.git` is globally excluded from sync).

**The trap this skill prevents:** treating the on-disk files as authoritative and either
(a) editing/committing on top of them, or (b) blindly `git init` + commit — which forks a
**new root history disconnected from origin**. Reconcile to origin **first**, revealing any
drift *before* anything is overwritten.

**Precondition:** run only when there is genuinely no repo. If `git rev-parse --is-inside-work-tree`
succeeds, you have a repo — this is Rule 1a (behind-with-local-changes), **not** bootstrap; use the
per-file hash reconciliation instead (`37_multi-mac-discipline.md` Rule 1a).

---

## Procedure

### 0. Confirm the situation

```bash
git rev-parse --is-inside-work-tree 2>/dev/null && echo "HAS REPO — stop, use Rule 1a" || echo "no repo — bootstrap"
```

Only proceed if it prints `no repo`.

### 1. Find the canonical origin URL

The URL is **not** guessable — get it from the project itself:

```bash
grep -riE 'github\.com|origin|repo' docs/PROJECT_STATE.md PROJECT_STATE.md CLAUDE.md 2>/dev/null | head
gh repo list --limit 200 | grep -i '<project-name>'   # fallback: list your GitHub repos
```

If you cannot determine the URL with confidence, **stop and ask** — the wrong origin is worse
than no origin.

### 2. Auth: GitHub over HTTPS via gh (these Macs have no SSH key)

```bash
gh auth status           # confirm logged in; if not: gh auth login  (HTTPS, browser)
gh auth setup-git        # makes git use the gh credential helper for github.com
```

### 3. Init, wire origin, fetch (nothing destructive yet)

```bash
git init -b main
git remote add origin <canonical-URL-from-step-1>
git fetch origin
```

### 4. THE reconcile — `--mixed`, never `--hard`

```bash
git reset --mixed origin/main            # HEAD + index → origin; WORKING TREE LEFT UNTOUCHED
git status --short --untracked-files=no   # ← THE CHECK
```

`--mixed` is the whole point: it advances HEAD and the index to origin while leaving every
on-disk byte alone, so the next command shows you **exactly** how the disk differs from origin.
A `--hard` here would silently destroy any Mac-local work before you ever saw it.

### 5. Read the check

- **0 tracked changes** → on-disk == origin. **Done — adopt as-is.**
  Do **not** `reset --hard`: nothing to gain, only risk. The repo is now correctly attached to origin.

- **Any tracked diff** → Syncthing carried Mac-local work origin lacks, *or* the local copy is
  **stale** and origin is newer. **STOP.** For each path:
  ```bash
  git diff origin/main -- <file>
  ```
  Reconcile by hand — re-apply your genuinely-unique edits *onto* origin's current version.
  **Never blind-`--hard` in either direction.** (Real counter-case: bootstrapping the Directions
  master itself once found the local copy *stale* vs origin — the check caught it, so the doc edit
  was re-applied onto origin's version instead of clobbering it.)

### 6. Verify commit identity is set (before you commit anything)

A fresh `git init` inherits identity from `~/.gitconfig`. Confirm it's populated — do **not**
hardcode a name/email in this skill (it's shared/versioned); read from the machine:

```bash
git config user.name; git config user.email      # both must be non-empty
# if empty, the user sets them once per Mac: git config --global user.name / user.email
```

---

## Expected-clean untracked noise

After bootstrap, `git status` (with untracked shown) may list files that are **fine** and should
stay untracked / gitignored — not evidence of drift:

- `DerivedData/`, `build/`, `.build/` — Xcode/SwiftPM build output
- `*.sync-conflict-*` — Syncthing conflict copies (inspect, then delete; never commit)
- `.DS_Store`, `~/.claude/settings.local.json` — per-Mac, never travels
- tool scratch dirs the project's `.gitignore` already covers

The check in step 4 uses `--untracked-files=no` deliberately so this noise doesn't mask the
signal (tracked drift). Handle untracked items separately, after the tracked reconcile is clean.

---

## Why this exists (one line each)

- **Blind `git init` + commit** forks a disconnected root history — the single worst outcome.
- **Blind `reset --hard`** destroys Syncthing-carried local work before you can see it.
- **`--mixed` + `git status`** is the "verify byte-identity before overwriting" discipline from
  Rule 1a, applied to a from-scratch repo.

Full context, per-Mac constants, and the source incidents: `37_multi-mac-discipline.md` Rule 1b.
Deployed to `~/.claude/skills/` by `redeploy.sh`; travels between Macs via the Directions git repo.
