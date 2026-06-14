## Deploy Ops — One-SFTP-user multi-site `lftp` deploy with `~/.netrc` (no secrets in git)

**Source:** App-Websites monorepo, 2026-06-14. Consolidated three sites (apps.lucesumbrarum.com portal + Penumbra + Aloft) onto **one** Strato SFTP user, with a unified deploy that keeps zero credentials in the repo. Replaced per-site `deploy.sh` scripts that each embedded a plaintext password.

**Use case:** You deploy several static/PHP sites from one monorepo to shared hosting (Strato/IONOS/OVH) over **SFTP**, want **one credential** for all of them, and want **no secret in any committed file** — while still being able to run `./deploy-all.sh` or a single site's `deploy.sh`. Multi-Mac via Syncthing makes "where does the password live" a real question.

**When to reach for it:** migrating away from `lftp -u user,PLAINTEXT_PASS` scripts; setting up a fresh deploy where the same SFTP account serves multiple document roots; any time you're about to hardcode an SFTP password "just for now."

---

### The headline gotcha: `lftp` + `sftp` shells out to `ssh`, which needs the user in the URL

`lftp`'s sftp backend runs an external `ssh` (`ssh -a -x -s <host> sftp`). **`ssh` gets the username only from the connection URL**, not from `~/.netrc`. So:

- `lftp sftp://HOST` (no user) → ssh connects as your **local** user → server drops you → `Connection closed by <ip> port 22` (looks exactly like a fail2ban ban — see #88, but here it's just a missing username).
- `lftp sftp://USER@HOST` → ssh gets `-l USER`; **`lftp` then reads the *password* from `~/.netrc`** by matching `(machine, login)`. ✓

> The fix is one character of insight: **user in the URL, password in netrc.** Nothing on the command line, nothing in the script.

```bash
# debug tell — run with -d and watch the connect program:
lftp -d -e "cls -la; quit" sftp://HOST
#   ---- Running connect program (ssh -a -x -s HOST sftp)   ← NO -l user → it will fail
# add the user:
lftp -d -e "cls -la; quit" sftp://USER@HOST                  # ssh now gets -l USER ✓
```

---

### Split the credential by sensitivity

| Piece | Where | Synced? | Why |
|---|---|---|---|
| **password** | `~/.netrc` (chmod 600) | **No** (lives in `$HOME`, outside the repo) | The secret never enters the Syncthing tree or git; recreated per-Mac. |
| **host + user** | repo `.env` (gitignored) | Yes (in the repo folder) | Identifiers, not secrets — convenient to sync; one place to read. |

`~/.netrc` (note: write with a **single-quoted heredoc** so `$`, `?`, `^` in the password aren't shell-expanded; whitespace-delimited, so a password with no spaces is one token):

```bash
( umask 077; cat > ~/.netrc <<'EOF'
machine 53958841.ssh.w1.strato.hosting
  login  stuXXXXXXXXX
  password p@ss?with$pecials^
EOF
)
chmod 600 ~/.netrc
# verify WITHOUT printing the secret:
awk '/password/{print length($2)}' ~/.netrc   # expect the known length
```

`.env` (gitignored) + committed `.env.example` (placeholders, **no** password — the example documents that the password goes in `~/.netrc`).

---

### Shared plumbing + thin per-site scripts

`_deploy-common.sh` (SOURCE it, don't run it) centralizes the security-sensitive bits so there's one place to get auth right:

```bash
#!/usr/bin/env bash
set -euo pipefail
COMMON_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"   # = repo ROOT
source "${COMMON_DIR}/.env"
: "${SFTP_HOST:?}"; : "${SFTP_USER:?}"
command -v lftp >/dev/null || { echo "brew install lftp" >&2; exit 1; }

normalize_perms() {            # macOS editors reset files to 0600 → Apache 403s; force web-readable
  find "$1" -type f -exec chmod 644 {} +
  find "$1" -type d -exec chmod 755 {} +
}

deploy_mirror() {              # <local_src> <remote_dir> [extra lftp mirror args…]
  local src="$1" remote="$2"; shift 2
  [ -d "$src" ] || { echo "no src: $src" >&2; exit 1; }
  local dry=""
  if [ -n "${DRY_RUN:-}" ]; then dry="--dry-run"; else normalize_perms "$src"; fi
  lftp "sftp://${SFTP_USER}@${SFTP_HOST}" -e "
    set sftp:auto-confirm yes
    mirror -R --verbose ${dry} --exclude .DS_Store --exclude-glob _backup_* $* ${src} ${remote}
    bye"
}
```

Each site is a thin script that self-locates and calls `deploy_mirror SRC REMOTE`:

```bash
#!/usr/bin/env bash
set -euo pipefail
SITE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$(cd "${SITE_DIR}/../.." && pwd)/_deploy-common.sh"
deploy_mirror "${SITE_DIR}/01_Source" "ALOFT"      # site's web root → its server folder
```

`deploy-all.sh` loops the sites; per-site stays the default for single pushes.

---

### Safety rails that matter

- **`DRY_RUN=1 ./deploy-all.sh`** → `--dry-run` AND skips the local mutations (perms `chmod`, any CSS cache-stamp `sed -i`). A preview must touch *nothing*, local or remote.
- **No `--delete`.** Mirror only adds/updates; it never prunes remote files. This is what protects **server-managed state** (PHP-written JSON, logs) from being wiped by a deploy.
- **Exclude server-managed files, then seed once.** Files the server writes (`feedback/public.json`, `submissions.log`) are `--exclude`d so deploys don't clobber live data — but that means a **first deploy to an empty server omits them**. Seed the initial empty `public.json` with a one-off `put`. Access-control files (`feedback/.htaccess`, `private/.htaccess`) are **not** excluded, so they ride up on the first deploy and the `private/` dir gets created.
- **Web-readable perms (644/755)** before every upload — macOS's stray 0600 → Apache 403.

---

### Un-ignoring the now-sanitized `deploy.sh`

Old `.gitignore` blanket-ignored `deploy.sh` *because it held a password*. Once sanitized, the scripts should be **committed** (they're useful and secret-free):

```gitignore
# Secrets live in ~/.netrc (password) + .env (host/user). deploy.sh scripts are sanitized → committed.
.env
.netrc
```

**Order matters:** overwrite the old plaintext script *first*, then un-ignore, then **prove it's clean before committing**:

```bash
git add -A
git grep -I -n -e '<the-password>' -e '<sftp-user>' --cached && echo "⚠️ SECRET — do not commit" \
  || echo "✓ clean"
git diff --cached --name-only | grep -x '.env' && echo "⚠️ .env staged" || echo "✓ .env not staged"
```

(Watch for **other** pre-existing per-site deploy scripts un-ignoring at the same time — a sibling site may have its own `deploy.sh` + `.deploy.env` that was relying on the blanket ignore.)

---

### Pitfalls

- **`Connection closed … port 22`** with a correct password is ambiguous: could be the user-missing-from-URL bug *here*, or a real fail2ban ban (#88). Check the connect program (`lftp -d`) for a missing `-l` before assuming a ban.
- **Multi-line `lftp -e "…"`** strings parse unreliably; prefer one line of `;`-separated commands, or a clean heredoc-style `-e` with each command on its own line and `bye`/`quit` last (not trailing on another command).
- **`~/.netrc` is per-Mac and not synced** — a fresh Mac has the repo (`.env`) but no password; recreate `~/.netrc` once (document it in `.env.example`).
- **Special chars in the password** break naive shell writes — single-quote everything; verify by **length**, never by printing.

Pairs with **#88** (is it a ban or a real auth failure?), **#46/#49** (the PHP download-counter / feedback backends being deployed — the server-managed files you must exclude), **#29** (Strato hosting specifics).
