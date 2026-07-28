# 170 — Auditing what you actually published (secrets, PII, repos)

**Tags:** security audit, secret scanning, git history, gh cli, public repo, sparkle private key, leaked credentials, blobless clone, rev-list, filter=blob:none, PII

**Extracted from:** ProgrammingProjects portfolio audit (2026-07-27)

## Three traps that make a "clean" result meaningless

### 1. Enumerate from the API, never the filesystem

The instinct is to grep the projects folder. But a local clone is not the unit of publication —
a **repo on the host** is. In a real portfolio audit only **9 of 28** public repos had a local
clone. Grepping the tree would have declared the other 19 clean without ever opening them, and
would also have missed a public repo whose name nobody remembered.

```bash
gh repo list <owner> --limit 200 --json name,visibility \
  --jq '.[] | select(.visibility=="PUBLIC") | .name' | sort > public.txt

# what's actually on disk, keyed by ORIGIN not folder name (they differ!)
find . -name .git -maxdepth 5 -type d | sed 's|/.git$||' | while read -r d; do
  git -C "$d" remote get-url origin 2>/dev/null | sed 's|.*/||; s|\.git$||'
done | sort -u > local.txt

comm -23 public.txt local.txt      # ← published but never audited locally
```

Folder name ≠ repo name is common (`AvidMXFPeek` → `MXF-Peek`), so mapping by directory name
silently mis-pairs repos. Always map by `remote get-url origin`.

### 2. Match secrets by VALUE, not by pattern

Pattern-matching (`grep -E '[A-Za-z0-9+/]{40,}='`) drowns in false positives and misses the real
thing. For **asymmetric** secrets it is actively misleading: a Sparkle `SUPublicEDKey` and its
private seed are both 44-char base64 and visually identical — but the public key is *supposed* to
ship. Only value-comparison distinguishes them.

```bash
# take distinctive substrings of the REAL secrets, then hunt for those
for f in "$VAULT"/*.key "$VAULT"/*private*.txt; do
  python3 -c "
import re,sys
d=open(sys.argv[1],errors='ignore').read()
for m in re.findall(r'[A-Za-z0-9+/]{40,}={0,2}', d): print(m[:24])" "$f"
done | sort -u > frags.txt

grep -rFf frags.txt <clones>/ --exclude-dir=.git   # current trees
git -C <repo> log --all -S"$frag" --oneline        # history, per fragment
```

`log -S` is the right history tool: it searches *changes* and is indexed-ish, unlike the naive
approach below.

### 3. Never `git grep <pat> $(git rev-list --all)`

This is the command everyone reaches for, and it will take down your session. It expands to every
commit in history and forces git to materialize **every blob in the repo** — gigabytes of I/O and
an argument list that blows past `ARG_MAX` on any repo with real history. Four parallel audit
agents all died to exactly this.

Cheap alternatives that cover the same ground:

```bash
# every filename ever added — eyeball for .p8/.p12/.pem/.env/id_rsa/*secret*
git -C "$d" log --all --diff-filter=A --name-only --pretty=format: | sort -u

# a specific known value, across all history
git -C "$d" log --all -S'<literal>' --oneline

# leaked author identity
git -C "$d" log --all --format='%ae' | sort | uniq -c
```

## Auditing repos you have no clone of

Don't full-clone. A **blobless** clone gives complete commit history (so every filename ever
committed is visible) while downloading blobs only for the checkout:

```bash
git clone --quiet --filter=blob:none "https://github.com/<owner>/<repo>.git" "$dst"
```

Fast enough to do 19 repos in one pass. Blobs for older revisions are fetched on demand if a
`log -S` later needs them.

## Distinguish "published" from "on disk"

The severities are completely different, and conflating them produces a scary report about
non-problems. Sort every finding into:

- **Published** — in a public repo (tree *or* history), or inside a web-upload root. History
  counts: a secret deleted in a later commit is still one `git log -p` away.
- **Tracked but private** — committed to a private repo. Rotate at leisure; treat as public if the
  value also ships compiled into a distributed binary.
- **On disk only** — plaintext in an untracked/gitignored file. Not published. Guard against the
  *future* leak (add a `.gitignore` even to a non-repo directory) rather than panicking.

Also check what the *deploy* publishes, not just what git does: an `lftp mirror -R` of a directory
containing `.git/`, `docs/`, or `CLAUDE.md` publishes all of it to the web host.

## Don't over-report

Two framings that produce false alarms:

- **"Plaintext on disk"** is not the same as unencrypted at rest. With FileVault on, files are
  encrypted at rest; file-mode `600` is what protects against other processes/users. State which
  threat you actually mean.
- **Sync tools** (Syncthing et al.) use pinned-cert TLS — transit is not the exposure. The
  exposure is at-rest on the peer, and whether the peer is trusted.

## Rotation ordering gotcha (Sparkle specifically)

Rotating a Sparkle EdDSA key requires shipping one update **signed with the OLD key** that carries
the NEW `SUPublicEDKey`; only afterwards do you sign with the new key. **If the old private key is
lost, that path is closed** — existing users can never be auto-updated again and need a manual
re-download. Audit key *backups* with the same seriousness as key *secrecy*.
