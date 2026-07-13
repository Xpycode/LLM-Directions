---
name: git-bootstrap
description: Reconcile a project that has source on disk but NO .git repo onto its canonical GitHub origin, WITHOUT losing local work. Invoke when a project directory has files but `git status` says "not a git repository" — a fresh or erased-and-restored Mac where Syncthing carried the working tree but .git is excluded from sync, or when history clearly exists on GitHub but the local repo is gone. Safe init → fetch → --mixed reset → verify (HTTPS via gh, never blind --hard). Also covers the local-only case where NO origin exists (re-founding, not bootstrap). Do this BEFORE any edit or commit.
---

# git-bootstrap

## The situation
The projects folder is **one Syncthing folder**: Syncthing replicates the working tree but
**`.git` is excluded** (via `.stignore`). So on a fresh or reset Mac every project has its
**source on disk but no repo** — and canonical history lives **only on GitHub `origin`**.
Reconcile to origin **first**; editing or committing before you do forks history (the
duplicate-commit incident). This is the same for every project in the folder, not just one.

## Precondition — is it actually a bootstrap?
```bash
git rev-parse --is-inside-work-tree 2>/dev/null \
  && { git fetch && git status -sb | head -1; echo "already a repo — use the Multi-Mac pre-flight (Rule 1a), NOT this skill"; } \
  || echo "no repo — bootstrap"
```
If it prints `already a repo`, this is the behind-with-local-changes case (`37_multi-mac-discipline.md`
Rule 1a) — per-file hash reconciliation, not bootstrap. Only continue on `no repo`.

## Find the canonical origin URL FIRST
The URL is not guessable — the remote name is **not guaranteed** to equal the folder name (a repo
may have been renamed since the folder was created). Source of truth, in order:
```bash
grep -riE 'repo|github\.com|origin' docs/PROJECT_STATE.md PROJECT_STATE.md CLAUDE.md 2>/dev/null | head
gh repo list --limit 200 | grep -i '<project-name>'   # fallback: your GitHub repos (gh auth's account)
```
If you cannot determine the URL with confidence, **stop and ask** — the wrong origin is worse than none.

## If NO origin exists (repo was local-only) — re-founding, not bootstrap
`gh repo list` has no match and/or the project's session logs say "local-only, no remote": there is
**nothing to fetch** and the procedure below does not apply. The only history is a `.git` on some
Mac's disk (a local-only project has permanently lost its history this way before).
1. **Find which Mac did the work** — session logs, Claude transcripts in `~/.claude/projects/<project>/`,
   DerivedData. If that Mac's `.git` survives, push from **there**:
   `gh repo create <owner>/<REPO> --private --source . --push`, then bootstrap the other Mac normally.
   **Never `git init` a fresh history on the non-authoring Mac** — a new root history can never merge
   with the real one.
2. **If `.git` is gone everywhere** (confirm with the user first): re-found — `git init -b main`,
   snapshot-commit the tree (state the history loss in the commit message — it's the only archaeology
   future readers get), then `gh repo create <owner>/<REPO> --private --source . --push`.
3. Afterwards add a **`Repo/git:` line to the project's CLAUDE.md** so the next bootstrap can confirm
   the URL, and check `.gitignore` patterns before the snapshot commit (an over-broad `*PLAN*.md` has
   eaten an `IMPLEMENTATION_PLAN.md` before).

## Auth — GitHub over HTTPS via gh (these Macs have no SSH key)
```bash
gh auth status            # confirm logged in; if not: gh auth login  (HTTPS, browser)
gh auth setup-git         # make git use the gh credential helper for github.com — never git@github.com: URLs
```

## Procedure (in the project root)
```bash
git init -b main
git remote add origin <canonical-URL-from-above>
git fetch origin

# Mixed reset: point HEAD+index at origin, LEAVE the working tree untouched.
# This is the safety move — it reveals how on-disk differs WITHOUT overwriting anything.
git reset --mixed origin/main
git branch --set-upstream-to=origin/main main

git status --short --untracked-files=no    # ← THE CHECK
```

## Identity — verify, don't hardcode
A fresh `git init` inherits identity from `~/.gitconfig`, which is often empty on a restored Mac.
Confirm it's populated; if empty, set it (globally, or repo-local) to match your usual identity —
do **not** copy a literal email into this shared/public skill:
```bash
git config user.name; git config user.email      # both must be non-empty before you commit
# if empty: git config --global user.name "…" ; git config --global user.email "…"
```

## Read THE CHECK — this is the whole point
- **0 tracked changes** → on-disk == canonical history. **Done — adopt as-is.**
  Do **not** `git reset --hard`: nothing to gain, only risk of clobbering.
- **Tracked files modified/deleted** → Syncthing carried work this Mac has but origin lacks (or the
  local copy is *stale* and origin is newer). **STOP.** `git diff origin/main -- <file>` each path and
  reconcile by hand — re-apply genuinely-unique edits *onto* origin's current version. **Never
  blind-`--hard`** in either direction; it silently destroys whatever is only on this Mac.
- Using `--mixed` (not `--hard`) is precisely what lets you *see the truth before* deciding.

> ⚠️ Older project docs saying `remote add && fetch && reset --hard origin/main` skip the verify step.
> Prefer this mixed-reset+check discipline; only escalate to `--hard` after the check proves a clean
> tree and you've decided origin should win.

## Expected-clean untracked noise (ignore, not drift)
Local tool/build dirs that are fine to leave untracked / gitignored — not evidence of drift:
`DerivedData/`, `build/`, `.build/`, `.claude/` (esp. `settings.local.json`), `.serena/`,
`.fastembed_cache/`, `.DS_Store`, `*.sync-conflict-*` (Syncthing copies — inspect then delete, never
commit). The check above uses `--untracked-files=no` deliberately so this noise doesn't mask the
signal. If `.claude/settings.local.json` shows as untracked, gitignoring it (then commit+push) is the
right cleanup — it's per-machine state, never canonical.

## After reconcile
- **Xcode projects:** `.xcodeproj` is gitignored + generated → `cd 01_Project && xcodegen generate`
  before building.
- **Any commit you make → push immediately** (`git push origin main`) so origin stays canonical for the
  other Macs. Solo dev, no PRs: small/config/docs → straight to `main`.
- **Per-Mac secrets don't sync** — Keychain items, notarization profiles, and Sparkle signing keys are
  machine-local. Recreate them per-Mac from your secure secrets store; they will not arrive via git.

---
Full context, the source incidents, and per-Mac constants: `37_multi-mac-discipline.md` Rule 1b.
Deployed to `~/.claude/skills/` by `redeploy.sh` (copy-only); travels between Macs via this git repo.
