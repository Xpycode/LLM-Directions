<!--
TRIGGERS: strato, strato.hosting, lftp, mirror, chmod, .htaccess, .htpasswd, htpasswd, basic auth, "401 Unauthorized", "Domain reserved", subdomain binding, DocumentRoot, AuthUserFile, FastCGI PHP, "served as download", DirectoryIndex, Umleitung, Directory Protection, cache-buster, ?v=, filemtime, no-build, deploy script, re-pull-and-migrate, prod canonical
PHASE: implementation, deploy
LOAD: when bootstrapping a new Strato site, debugging deploys, or shipping changes to existing PHP/static sites
-->

# Strato Shared Hosting Gotchas

*Strato shared hosting is one of the cheapest live-PHP+SQLite hosts; it's also one of the most quirky. This doc captures the gotchas that have eaten time across at least 4 sites (LUCESUMBRARUM, apps.lucesumbrarum.com, LEARNING/INGEST, Bookmarks). The common rule: **half the configuration lives in the control panel, not in the files you can SFTP.***

---

## What you can fix via SFTP vs. what needs the control panel

Get this wrong and you'll waste a session editing files that have no effect on the live response. The diagnostic question to ask first when something's off:

| Problem | Fix-where |
|---|---|
| Wrong content served (HTML, PHP, CSS, images) | SFTP |
| `.htaccess` rewrite/auth/handlers | SFTP |
| **Domain → docroot mapping** (e.g. `lucesumbrarum.com` serves wrong site) | **Control panel** (Domains → target folder) |
| **Subdomain not yet bound** (serves `"Domain reserved"` placeholder) | **Control panel** (subdomain → bind to docroot) |
| **Directory Protection** (HTTP Basic Auth dialog you didn't configure in `.htaccess`) | **Control panel** (Domains → Directory Protection) |
| **Umleitung Intern** (silently invalidates root-level targets) | **Control panel** (Domains → redirects) |
| `Require all denied` blocking a subdir from inheritance | SFTP (add allow override) |
| TLS / HTTPS termination | Strato handles upstream; sets `X-Forwarded-Proto: https` |

**Diagnostic clue for "the right SFTP file isn't fixing the live behaviour":** look at the `WWW-Authenticate` header's `realm=…` value. If it doesn't match the realm of any `.htaccess` you've put in place (e.g. `.com` returns realm `"LEARNING"` but your only `.htaccess` says `realm "Luces Umbrarum Admin"`), the auth is coming from a **different docroot** the panel has the domain mapped to.

Source: LUCESUMBRARUM `2026-05-12` (`.com` returning 401 with mismatched realm — fix required portal access, not SFTP).

---

## First-deploy bootstrap

Things that bite specifically on the first deploy of a new site or subdomain.

### Bind the subdomain *before* uploading

The `stuNNNNNNN` SFTP account exists immediately. The subdomain you want to serve from it does not. Until you bind `<subdomain>.<your-domain>` to that docroot in the control panel, every request gets the **"Domain reserved"** placeholder regardless of what you've uploaded.

Check first:

```bash
curl -I https://<subdomain>.<your-domain>
# Expect: HTTP/2 200, Content-Length matching what you uploaded
# Got "Domain reserved" or similar Strato page → not bound yet
```

### Strato chroots SFTP users — `pwd` lies

Inside SFTP, `pwd` returns `/`, hiding the actual filesystem path. Apache directives like `AuthUserFile` require the **absolute** path, and Strato won't tell you what that is from the SFTP shell.

Workaround: upload a one-line PHP probe and curl it:

```php
<?php echo __DIR__;
```

Then:

```bash
curl https://<your-subdomain>/_path-probe.php
# → /mnt/web408/e0/41/53958841/htdocs/INGEST  (or similar)
```

Use that path verbatim in `AuthUserFile /mnt/web408/.../htdocs/INGEST/.htpasswd`. **Delete the probe file after use** — it leaks server topology.

Source: LEARNING `2026-05-01`.

### `DirectoryIndex` may not include `index.html`

Strato's default `DirectoryIndex` for some hosting tiers includes `index.php` but **not** `index.html`. Symptom: `/` returns 404 even though `/index.html` returns 200.

Fix: add to your top-level `.htaccess`:

```apache
DirectoryIndex index.html index.php
```

Source: LEARNING `2026-05-01` (Next.js static export hit this — `out/index.html` was uploaded but `/` 404'd until DirectoryIndex was set).

### **Don't** add a PHP handler — Strato runs FastCGI

The most expensive first-deploy mistake: adding `SetHandler application/x-httpd-php` (or `AddHandler` variants) to `.htaccess` to "make sure PHP runs." On Strato's current FastCGI tier, this **breaks PHP execution** — the browser downloads `index.php` as a file instead of executing it.

The correct `.htaccess` for PHP on Strato has **no PHP-handler directive**. Compare against any working PHP site already on Strato — none of them have one.

```apache
# ✓ correct — no SetHandler / AddHandler for PHP
DirectoryIndex index.php index.html
RewriteEngine On
RewriteRule ^.*$ index.php [L]
```

Source: Bookmarks `2026-05-06a` (first deploy "succeeded" but served `index.php` as a download; diagnosed by diffing against three working PHP sites).

---

## Deploy script patterns

These have evolved across LEARNING, LUCESUMBRARUM, and Bookmarks. The combined recipe:

### `lftp mirror -R` — without `--delete`, with `chmod` normalize

```bash
#!/usr/bin/env bash
set -euo pipefail

# Normalize permissions before pushing — macOS editors sometimes set 0600 on files
# they touch, lftp preserves permissions, and Apache then 403s on world-unreadable files.
find "$STAGE_DIR" -type f -exec chmod 644 {} \;
find "$STAGE_DIR" -type d -exec chmod 755 {} \;

lftp -u "$STRATO_USER","$STRATO_PASS" -e "
  set sftp:auto-confirm yes;
  mirror -R --verbose --parallel=4 \
    $STAGE_DIR /htdocs/$SITE_NAME/;
  bye
" sftp://$STRATO_HOST
```

Three things to know:

- **No `--delete`** — protects server-only data (SQLite DBs, uploads, generated favicon caches). The cost is that removed source files stay on the server until cleaned up by hand. Worth it.
- **`$STAGE_DIR` is `01_Project/`, the live DB lives in `04_Data/`** — for a no-build site, `01_Project/` is both the code home and what lftp mirrors (see `13_folder-structure.md` → Pattern A). The SQLite live DB sits in `04_Data/` (gitignored, *outside* `01_Project/`), so it's *physically unreachable* from the upload step — there's no path that could cause it to be overwritten. (If you build into a stage, point `$STAGE_DIR` at the emit dir; the DB-in-`04_Data/` separation is what guarantees safety, not a separate stage.)
- **lftp uploads dotfiles by default** — `.htaccess`, `.htpasswd` land on the server even though the verbose listing hides them. Confirm via SFTP `ls -a`.

### Idempotent: lftp checksums skip unchanged files

`lftp mirror` compares file size + mtime and skips matches. So a redeploy after one `.htaccess` edit transfers exactly that one file. The pattern fits well with cache-busters keyed on `filemtime` (next section).

### Bcrypt `.htpasswd` works on current Strato Apache 2.4

The widely-cited Strato FAQ that mentions MD5-only `.htpasswd` is for the older "BasicWeb XL" tier. Current shared hosting is Apache 2.4 and accepts `$2y$`, `$2a$`, `$2b$` bcrypt hashes from `htpasswd -nbB`.

Source: LEARNING `2026-05-01`, Bookmarks `2026-05-09a`.

---

## Cache-busting on no-build sites

Static + PHP sites without a bundler have no automatic asset hashing. Browsers cache JS/CSS aggressively; users see stale code after a deploy and report bugs that don't exist.

Two patterns, both proven across LUCESUMBRARUM and Bookmarks:

### Automatic: `?v=<filemtime>` (recommended)

Cheap helper, recompiles automatically:

```php
// lib/assets.php
function asset(string $name): string {
    static $cache = [];
    if (!isset($cache[$name])) {
        $cache[$name] = "public/{$name}?v=" . filemtime(__DIR__ . "/../public/{$name}");
    }
    return $cache[$name];
}
```

```php
<link rel="stylesheet" href="<?= asset('app.css') ?>">
<script src="<?= asset('app.js') ?>"></script>
```

Renders as `public/app.css?v=1778249624`. The `?v=…` advances **only when the file's mtime changes**, which means lftp's mirror only re-uploads files whose content changed — perfectly aligned. Source: Bookmarks `2026-05-08c`.

### Manual: `?v=<date-rev>` (when there's no PHP at the reference point)

For static HTML (`index.html`), where PHP doesn't run:

```html
<link rel="stylesheet" href="admin.css?v=20260509-r3.5b">
<script src="admin.js?v=20260509-r3.5b"></script>
```

Bump the date-rev string by hand on every ship. Source: LUCESUMBRARUM repeatedly across `2026-05-04`, `2026-05-08`, `2026-05-09` waves.

**Key gotcha:** check **every** HTML/PHP file references the cache-busted version. The audit found `index.html` had no cache-buster at all on `admin.css`/`admin.js` while `gallery.html` did — the previous wave's bump skipped one file. Easy way to miss: site looks fine in the browser you tested but breaks in any other browser/profile that has the old cache.

---

## Server-state-canonical sync (when prod has data your local doesn't)

If your local development mutates server-state files (JSON manifests, SQLite DBs, etc.) — e.g. via local e2e tests against admin endpoints — your local copies *will* drift from prod. Shipping local-as-canonical will then silently overwrite real production state with test mutations.

The recipe (proven on LUCESUMBRARUM `2026-05-12` — caught a `dias.json` photo-array reorder caused by 3-day-old e2e tests that would have overwritten real prod state):

```
1. Pull prod files first (SFTP get; treat prod as canonical for state)
2. Diff against local
3. If drift detected:
   a. Backup the local-mutated copy (file.PRE-RE-MIGRATE.bak)
   b. Copy prod over local
   c. Re-run any idempotent migration on the prod-canonical files
   d. Re-run the canary / smoke test → expect 0-diff
4. Push only after canary passes
```

When to apply: any file whose source-of-truth lives on the server (manifests written by mutating endpoints, the SQLite DB, generated thumbnails, uploaded user content). When NOT to apply: source code, config — those flow local → prod, not the other way.

---

## Quick-reference cheatsheet

| Symptom | First check |
|---|---|
| Subdomain returns "Domain reserved" placeholder | Bind subdomain → docroot in control panel |
| Site returns 401 with realm name you don't recognize | Domain mapping in control panel points to a different docroot |
| `index.php` downloads as a file instead of executing | Remove `SetHandler`/`AddHandler` for PHP from `.htaccess` |
| `/` returns 404 but `/index.html` returns 200 | Add `DirectoryIndex index.html` to `.htaccess` |
| Apache `AuthUserFile` needs absolute path you don't know | Upload `<?php echo __DIR__;` probe, curl it, then delete |
| Site looks broken after deploy in some browsers, not others | Cache-buster: `?v=<filemtime>` on JS/CSS, check **every** referencing HTML |
| Files on server have wrong perms (403 after mirror) | `chmod 644/755` normalize before `lftp mirror` |
| Removed source files reappear on server after deploy | Expected — `lftp mirror` without `--delete` doesn't remove. Clean by hand if needed. |
| Local copy of a server-state file overwrites real prod data | Re-pull-and-migrate recipe — never ship local-canonical for server-mutated files |
| "FAQ says I need MD5 .htpasswd" | False on current tier; bcrypt (`$2y$`/`$2a$`/`$2b$`) works on Apache 2.4 |

---

## The cross-cutting rule

> **If editing files via SFTP doesn't change the live response, the configuration is in the control panel — not in your repo.**

Strato keeps half the config (domain mapping, subdomain binding, directory protection, redirects, TLS) in a panel that you can't script and can't grep. When the symptom doesn't match what your `.htaccess` says, that's the tell.

---

*Related: `24_web-gotchas.md` (browser/cache patterns more broadly), `32_git-workflow.md` (deploy hygiene), `54_security-rules.md` (auth + secrets).*
