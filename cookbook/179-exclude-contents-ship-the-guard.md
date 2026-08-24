# 179 — Excluding a directory from the deploy also excludes the `.htaccess` guarding it

**Tags:** lftp, mirror, exclude, .htaccess, Require all denied, Deny from all, server-canonical, uploads, auth bypass, direct URL, session auth, Strato, deploy, PHP

**Extracted from:** PRIVAT (2026-08-24), designing per-event password-protected photo galleries

## The problem

Two rules that are individually correct combine into an auth bypass.

**Rule 1** (#169): a directory the server writes to must be excluded from the mirror, or every
deploy overwrites live data with local seeds.

**Rule 2**: when auth is enforced in application code — a PHP session check, a signed cookie, a
framework middleware — the files themselves must be unreachable by Apache, or a guessed direct URL
serves them and the login is decorative:

```apache
# storage/.htaccess
Require all denied
```

So you write the obvious deploy line:

```bash
lftp ... -e "mirror -R --exclude storage/ 01_Project /"
```

`storage/` holds server-canonical uploads → excluded. Correct per Rule 1.

**And `storage/.htaccess` is inside `storage/`.** It never ships. On a fresh server it never existed
to begin with, so there is nothing to notice: the site works, the login page works, the gallery
works — and `https://site/storage/events/wedding/original/DSC_0042.jpg` returns the photo to anyone
who guesses it. The password is real, the session check is real, and neither protects anything.

Nothing fails. The deploy reports success. The login still prompts.

## Why it hides

Every signal points the wrong way:

- The **feature works** — visitors log in, browse, and download exactly as designed.
- `lftp` **hides dotfiles** in its verbose listing, so the transfer log never shows the absence.
- The guard is a *negative* control: its correct behaviour is a 403 nobody requests on the happy path.
- Testing while logged in proves nothing — you'd get the photo either way.
- On a fresh deploy there is no "it used to work" moment. It was never protected.

## The rule

> Exclude the **contents**, not the container. A directory's access-control file is code, not state —
> it must ship on every deploy, even when everything beside it must not.

```bash
# storage/ holds server-canonical uploads: photos and metadata created by the live
# admin page. Local copies are stale by definition, so its CONTENT dirs are excluded.
#
# But NOT storage/ itself — storage/.htaccess (Require all denied) is the only thing
# stopping a direct image URL from bypassing the PHP session check. Exclude the
# container and the guard never reaches the server, silently, on a site that works.
mirror -R --parallel=4 \
  --exclude storage/events/ \
  --exclude storage/tmp/ \
  "$STAGE" "$REMOTE_DIR"
```

Layout so this is expressible: keep the guard at the *root* of the excluded area and the mutable
data one level down, so a per-subdirectory exclusion is possible at all.

```
storage/
  .htaccess          ← code. ships every deploy.
  events/            ← server-canonical. never pushed.
  tmp/               ← server-canonical. never pushed.
```

If the layout forces guard and data into the same directory, ship the deny rule from the parent
instead — `RedirectMatch 404 ^/storage/` in the root `.htaccess` — so it lives outside the exclusion.

## Verify it, because success looks identical to failure

Both checks are negative controls: **prove they can fail** before trusting a pass
([[negative-checks-pass-vacuously]]).

```bash
# 1. The guard actually arrived (lftp's listing won't tell you — dotfiles are hidden)
lftp -u "$U","$P" -e "cd $REMOTE/storage; ls -a; bye" "sftp://$HOST" | grep -q '\.htaccess' \
  || echo "FAIL: storage/.htaccess missing on server"

# 2. A direct URL is refused. Run it LOGGED OUT (-b: no cookie jar).
#    Confirm the check works by first pointing it at a file that SHOULD be served.
curl -sb /dev/null -o /dev/null -w '%{http_code}\n' \
  "https://$SITE/storage/events/$EVENT/original/$KNOWN_FILE"   # expect 403, NOT 200
```

Add both to the post-deploy step. A deploy that ships the app but drops the guard is worse than a
deploy that fails, because only one of them tells you.

## Related

- **#169** — the upstream rule this collides with: `mirror -R` clobbers server-written state, so
  exclude it. This pattern is the security-shaped exception to how you write that exclusion.
- **#180** — the credential half of the same deploy script.
