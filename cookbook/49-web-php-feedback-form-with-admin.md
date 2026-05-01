## Web Feedback Form — PHP + Flat-File JSON + Admin UI, No Backend

**Source:** `apps.lucesumbrarum.com/public/feedback.*`, `public/feedback-submit.php`, `public/admin/*`, `public/js/feedback.js`. Added 2026-04-21.

**Use case:** A marketing / portfolio / small-product site that wants in-app "Report a bug" / "Feature request" / "Question" submissions — persisted, emailed to the operator, and **publicly listed** on the site so future visitors can see a live ticker of what's been reported and how it was resolved. No GitHub Issues account required from the reporter. No database, no SaaS, no cookies, no third-party requests. Builds directly on cookbook #46's PHP + flat-file JSON pattern but adds: public/private data separation with PII handling, an admin triage UI gated by Basic-Auth, and a CSRF layer that correctly addresses Basic-Auth's "credentials auto-attached on every request" trap.

**When to reach for it:**
- You already have the cookbook #46 toolbox (Apache + PHP shared hosting, `flock`, `.htaccess`).
- Submission volume forecast < 1000/year. Past that, JSON-file contention and linear scan on submit will start to matter.
- One operator (you) triaging submissions. Multi-admin needs a real session/role layer.
- The reporter's expectation is "send it and get a reply" — not "track it in a ticket dashboard."
- You want the listed-publicly social signal: new visitors seeing past resolved items is reassurance that the operator actually reads feedback.

**When *not* to use it:**
- Reports must be private (security disclosures, HR, healthcare). Use a separate private channel or a real ticketing system.
- You need threaded conversations, attachments, assignees, due dates. That's ticketing. Use GitHub Issues, Linear, or Plane.
- High-volume consumer product (>100 submissions/day). Append-only log scan on every submit becomes a bottleneck; move to SQLite + full-text-search or Redis.
- Platform without PHP (Cloudflare Pages, Netlify, Vercel). Port the backend to a Worker + KV; the frontend patterns still apply.

---

### Anatomy

```
public/
├── feedback.html                    ← form + public list page
├── feedback-submit.php              ← POST handler (validate, write, email, redirect)
├── feedback/
│   ├── public.json                  ← web-readable, no PII
│   ├── .htaccess                    ← explicit Require all granted for public.json
│   └── private/
│       ├── .htaccess                ← Require all denied
│       └── submissions.log          ← append-only, one JSON per line, with email + ip_hash + ua
├── admin/
│   ├── index.html                   ← triage UI
│   ├── admin.js                     ← fetch + edit-in-place + save/delete
│   ├── data.php                     ← GET: public.json ∪ private-log emails (auth'd)
│   ├── update.php                   ← POST: status/resolution/delete (auth'd + CSRF)
│   ├── .htaccess                    ← AuthType Basic + Require valid-user
│   └── .htpasswd                    ← uploaded separately (never in git)
├── _whereami.php                    ← one-time helper to discover AuthUserFile path
└── js/
    └── feedback.js                  ← list render + filter + prefill + toast

deploy.sh                            ← must --exclude server-managed files
```

---

### The two-file storage split (why it matters)

`public.json` is web-readable and rendered as the public list. It **must not contain** email, IP, or user agent. `private/submissions.log` is `.htaccess`-denied at the HTTP layer and contains the same `id` joined with email + a salted SHA-256 of the IP + truncated UA. Rationale: if `.htaccess` ever misconfigures (e.g., a hosting provider upgrade wipes custom rules), there's **nothing sensitive in the web-readable file to leak**. Defense in depth — the data model itself is a barrier, not just the access-control rule.

```php
// feedback-submit.php — the two parallel writes
$public_entry = [
  'id' => $id, 'app' => $app, 'type' => $type,
  'title' => $title, 'body' => $body,
  'reporter' => $reporter,                         // "Anonymous" if blank
  'app_version' => $app_version, 'os_version' => $os_version,
  'status' => 'open', 'submitted_at' => $submitted_at, 'updated_at' => $submitted_at,
  'resolution' => null, 'github_url' => null,
];
$private_entry = [
  'id' => $id,
  'email' => $email,                               // only here
  'ip_hash' => hash('sha256', $_SERVER['REMOTE_ADDR'] . IP_SALT),
  'ua' => substr($_SERVER['HTTP_USER_AGENT'] ?? '', 0, 500),
  'submitted_at' => $submitted_at,
];
```

Both writes use the same `flock(LOCK_EX)` discipline as cookbook #46. Public.json is `c+` (read-modify-write); private log is `a` (append-only). If the private log write fails, the public entry is still recorded — email notification is best-effort.

---

### The honeypot + salted-IP rate limit

```php
// Honeypot — silent accept so bots get no signal
if (trim($_POST['website'] ?? '') !== '') {
  header('Location: /feedback.html?submitted=1');
  exit;
}

// Rate limit — never store raw IP
const IP_SALT = 'lu-feedback-v1';           // rotate to invalidate all tallies
$ip_hash = hash('sha256', ($_SERVER['REMOTE_ADDR'] ?? '') . IP_SALT);

$recent = [];
$h = @fopen(PRIVATE_LOG, 'r');
if ($h) {
  while (($line = fgets($h)) !== false) {
    $e = json_decode(trim($line), true);
    if (!is_array($e) || ($e['ip_hash'] ?? '') !== $ip_hash) continue;
    $t = strtotime($e['submitted_at'] ?? '') ?: 0;
    if ($t > 0 && (time() - $t) < 86400) $recent[] = $t;
  }
  fclose($h);
}
$in_hour = count(array_filter($recent, fn($t) => (time() - $t) < 3600));
if ($in_hour >= 3 || count($recent) >= 10) {
  http_response_code(429);
  echo "You've sent several recently…"; exit;
}
```

The honeypot field is a hidden input named `website`. Real users never see it; scripted form-fillers blindly populate every field. Key nuance: **silently succeed** on honeypot match (302 redirect, no error). Returning a visible "rejected" message would teach the bot which field was the trap. The IP hash is salted so the private log can't be cross-referenced to expose IPs even if leaked.

---

### XSS safety via rendering discipline, not input sanitisation

Store raw user input in JSON; escape at the render boundary. `feedback.js` uses `textContent` and `createElement` exclusively — no `innerHTML` anywhere, not even for "trusted" template strings. This makes XSS structurally impossible, not merely "unlikely":

```js
// feedback.js — the render path (abbreviated)
function renderItem(item) {
  const article = document.createElement('article');
  article.className = 'fb-item';
  if (typeof item.id === 'string') article.id = item.id;   // id is validated shape

  // Whitelist the class modifier so attacker-controlled status
  // can't target arbitrary CSS rules.
  const statusKey = ALLOWED_STATUS.includes(item.status) ? item.status : 'open';

  const title = document.createElement('h3');
  title.textContent = item.title || '';         // ← cannot parse HTML, ever
  const body = document.createElement('p');
  body.textContent = item.body || '';           // ← same
  // …
}
```

Verified: a submission with `"title": "<script>alert(1)</script> & \"quotes\""` is stored verbatim in JSON (correct — JSON doesn't care about HTML) and rendered as visible literal text (correct — `textContent` never parses). No escape function needed on the server. No escape function needed on the client. The API shape itself prevents the vulnerability.

---

### Admin gate — Basic-Auth + CSRF (the subtle part)

Basic-Auth is convenient: one `.htaccess` stanza and Apache handles everything. But it carries a trap: **the browser attaches credentials automatically on every request to the realm**, including cross-origin POSTs. An attacker's page can submit `<form action="https://yoursite/admin/update.php">` and the victim's browser will obligingly include the admin's credentials.

The mitigation is a same-origin check inside the PHP handler itself — but **the obvious implementation is wrong**, and the wrong version was the original recipe in this cookbook entry. The corrected pattern:

```php
// admin/update.php — CSRF guard under Basic-Auth
// Compare hostnames *exactly* via parse_url(). A substring match
// (stripos / str_contains) is the textbook anti-pattern below.
$raw_host      = (string)($_SERVER['HTTP_HOST']    ?? '');
$expected_host = strtolower(explode(':', $raw_host, 2)[0]);   // strip :port

$origin  = (string)($_SERVER['HTTP_ORIGIN']  ?? '');
$referer = (string)($_SERVER['HTTP_REFERER'] ?? '');

$origin_host  = $origin  !== '' ? strtolower((string)parse_url($origin,  PHP_URL_HOST)) : '';
$referer_host = $referer !== '' ? strtolower((string)parse_url($referer, PHP_URL_HOST)) : '';

$ok = false;
if ($expected_host !== '') {
  if ($origin_host !== '') {
    $ok = ($origin_host === $expected_host);          // prefer Origin
  } elseif ($referer_host !== '') {
    $ok = ($referer_host === $expected_host);         // fallback for browsers that strip Origin
  }
}
if (!$ok) { http_response_code(403); echo "Cross-site POST refused."; exit; }
```

#### Anti-pattern: `stripos($origin, $host)` substring match

The seductive version that *looks* right and ships in plenty of "same-origin guard" snippets online:

```php
// ❌ BROKEN — substring match, bypassable
if (stripos($origin, $host) !== false) $ok = true;
```

Three concrete bypasses, all of which slip through:

| Attacker page | `Origin` header | Substring contains `apps.lucesumbrarum.com`? | Verdict |
|---|---|---|---|
| `https://evil.com/apps.lucesumbrarum.com/x` | *(only the Origin matters — path isn't sent)* | — | (irrelevant; path-based bypass needs Referer instead, see below) |
| `https://apps.lucesumbrarum.com.evil.com` | `https://apps.lucesumbrarum.com.evil.com` | yes | **passes — admin compromised** |
| `https://evil.apps.lucesumbrarum.com.attacker.example` | same | yes | **passes** |

When `stripos` is applied to the `Referer` (the fallback path), even the path-based bypass works:

```
Referer: https://evil.com/apps.lucesumbrarum.com/forge.html
                          ^^^^^^^^^^^^^^^^^^^^^^^^^
                          substring of HTTP_HOST → "matches" → forged POST allowed
```

Combined with cached Basic-Auth credentials, that's functionally leaked admin access — the browser auto-attaches credentials and the substring guard waves the request through.

#### Why `parse_url(..., PHP_URL_HOST)` fixes it

`parse_url` parses an absolute URL and returns just the hostname segment — port stripped, path discarded, scheme discarded. Comparing those segments with `===` means there's no substring left to game:

| Origin sent | `parse_url(..., PHP_URL_HOST)` | Equals expected `apps.lucesumbrarum.com`? |
|---|---|---|
| `https://apps.lucesumbrarum.com` | `apps.lucesumbrarum.com` | ✅ |
| `https://apps.lucesumbrarum.com:8080` | `apps.lucesumbrarum.com` | ✅ (port lives in `PHP_URL_PORT`) |
| `https://apps.lucesumbrarum.com.evil.com` | `apps.lucesumbrarum.com.evil.com` | ❌ |
| `https://evil.com/apps.lucesumbrarum.com/x` | `evil.com` | ❌ |

Lowercasing both sides handles the rare case where a client sends mixed-case host headers.

#### Threat-model footnote

This pattern aligns with the OWASP CSRF Prevention Cheat Sheet's "Verifying Origin with Standard Headers" approach. It's a solid floor for a single-admin Basic-Auth tool. If the threat model escalates (multi-admin, untrusted networks, mTLS not in play), layer in a session-bound CSRF token rather than relying on `Origin`/`Referer` alone — both can be elided by determined network attackers.

---

### `.htaccess` + `.htpasswd` — the setup dance

The tricky part is `AuthUserFile` needing an **absolute server path** — which varies by host and isn't easy to discover. Ship a one-time helper:

```php
<?php
// public/_whereami.php — DELETE AFTER USE
header('Content-Type: text/plain; charset=utf-8');
echo "AuthUserFile \"" . __DIR__ . "/admin/.htpasswd\"\n";
echo "(Copy that line into admin/.htaccess, then delete this file.)\n";
```

Flow:
1. Deploy `_whereami.php` + `admin/.htaccess` (with a placeholder path).
2. Visit `https://yoursite/_whereami.php` once — copy the printed `AuthUserFile` line.
3. Generate the password file locally: `htpasswd -c -B admin/.htpasswd <username>` (bcrypt, not MD5).
4. Upload `admin/.htpasswd` via SFTP. Edit `admin/.htaccess` on the server — replace the placeholder with the real path.
5. **Delete `_whereami.php`** from the server. Leaving it live leaks filesystem layout.
6. Test — browser prompts for the password.

Alternative: most shared hosts (Strato, IONOS, etc.) have a "Directory protection" GUI in their control panel that generates both files for you. Skip steps 2-5 entirely.

The `admin/.htaccess`:
```apache
AuthType Basic
AuthName "Admin"
AuthUserFile "/REPLACE/WITH/ABSOLUTE/PATH/admin/.htpasswd"
Require valid-user

# Belt-and-braces: deny .htpasswd itself even to authed users.
<Files ".htpasswd">
  Require all denied
</Files>
```

---

### `deploy.sh` excludes — critical for server-managed files

The moment the server starts writing to `public.json` (i.e., the moment real users submit), your local copy is stale. A naive `lftp mirror -R` from local → server is then **destructive** — it overwrites real user data with your empty seed. This is the single most dangerous failure mode in the whole setup:

```bash
# deploy.sh — exclude server-written files
lftp -u "$USER","$PASS" "sftp://$HOST" -e "
  mirror -R \
    --exclude feedback/public.json \
    --exclude feedback/private/submissions.log \
    --verbose ${PUBLIC_DIR} .
  bye
"
```

Gotcha: on **first deploy**, the excluded files don't upload, so the server has no seed. Fix: temporarily comment out the two `--exclude` lines for the first deploy only, run, then restore. Or manually SFTP the seeds once.

The same principle applies to any shared-hosting pattern where the server mutates a file the local repo also tracks. Cookbook #46's `counts.json` has the same problem and needs the same `--exclude` treatment.

---

### Admin data read — joining public + private at read time

```php
// admin/data.php — join-at-read, not join-at-write
$public = json_decode(file_get_contents(PUBLIC_JSON), true);
$emails = [];                                   // id → email map from log
$h = fopen(PRIVATE_LOG, 'r');
while (($line = fgets($h)) !== false) {
  $e = json_decode(trim($line), true);
  if (is_array($e) && !empty($e['id'])) $emails[$e['id']] = $e['email'] ?? '';
}
fclose($h);

$out = [];
foreach ($public['items'] as $item) {
  $item['_email'] = $emails[$item['id']] ?? '';
  $out[] = $item;
}
echo json_encode(['items' => $out]);
```

Deliberately doing the join at **read time** (behind auth) rather than write time means public.json stays PII-free on disk, not just "PII-free as served." If an operator sshes in and `cat public.json`, they also see no email. The only place email lives is the `.htaccess`-denied log. One source of truth for each concern.

---

### Per-app placeholder polish (small JS pattern)

```js
// feedback.js — swap the title placeholder per selected app
const TITLE_EXAMPLES = {
  cropbatch: "e.g. 'Export fails when folder has 10k+ images'",
  sigil:     "e.g. 'Icon disappears after APFS remount'",
  // … one per app
};
function applyTitlePlaceholder(slug) {
  titleInput.placeholder = TITLE_EXAMPLES[slug] || 'Short, descriptive';
}
appSelect.addEventListener('change', (e) => applyTitlePlaceholder(e.target.value));
applyTitlePlaceholder(appSelect.value);          // run once on load for ?app=... prefill
```

Tiny UX lever, disproportionate payoff: someone reporting a syncthingStatus bug sees a syncthingStatus example, not a CropBatch one. Pairs with in-app Help-menu deep-linking (`?app=<slug>&v=<Bundle.main.version>`) so the page lands with the dropdown + placeholder already contextual.

---

### Gotchas

- **`<fieldset>/<legend>` for radio groups fights grid layouts.** `<legend>` renders outside normal flow and its baseline doesn't align with sibling form controls. Use `<div role="radiogroup" aria-label="Type">` with a separate label span — same accessibility, predictable layout.
- **`accent-color: var(--brand)` on radio inputs** — one line replaces the "custom div + `appearance: none` + JS" workaround for branded radios/checkboxes. Modern Safari 15.4+, all evergreen browsers.
- **PHP built-in server ignores `.htaccess`.** Local dev via `php -S` leaves `/admin/` and `/feedback/private/` wide open. Apache-side tests must happen on a real Apache host (staging or prod). The PHP-level CSRF check still works locally because it's enforced in application code.
- **`mail()` doesn't work from dev Macs.** No local MTA. Test the 302 + file-write path locally; wait until deploy to confirm email delivery. Strato and most shared hosts handle outbound SMTP transparently.
- **HEAD requests hit all your PHP logic even though they return no body.** Cookbook #46 taught this lesson; same applies here. Honeypot/rate-limit paths should all short-circuit with early `exit` before any heavy work.
- **ID format validation is path-traversal defence.** `admin/update.php` validates `id` against `^fb_\d{4}-\d{2}-\d{2}_[a-f0-9]+$` — same principle as `dl.php`'s regex on `app`. Attacker-controlled `id` must never reach `fopen()` or `file_get_contents()` unfiltered.
- **Bcrypt (`-B` flag to `htpasswd`)**, not MD5. MD5 is fast enough that a modern GPU cracks a weak password in seconds. Bcrypt is intentionally slow and tunable. Apache has supported bcrypt for years — there's no reason to use MD5 for new files.

---

### Scaling

- **~1000 submissions/year:** zero concern. JSON scan on every submit is O(n) but n is small.
- **~10,000 submissions/year:** the rate-limit scan through `submissions.log` becomes the first bottleneck (scanning the whole file per submit to count recent entries). Fix: rotate the log daily (`submissions-2026-04.log`) and only scan the current month's file.
- **~100,000 submissions/year:** move to SQLite. The patterns transfer 1:1 — same validation, same flock-equivalent via transactions, same public/private column split.
- **Multi-admin:** replace Basic-Auth with a session cookie + CSRF token. The data model can stay flat-file; only the gate changes.

---

### Composes with

- Cookbook **#46** (download counter) — same `flock` + flat-file JSON + PHP + static-site shape. If you have one, you have the toolbox for the other.
- Cookbook **#41** / **#42** (web hero / lightbox) — the public feedback page feels consistent with the rest of the portfolio when it uses the same token system and `<dialog>` modal patterns.

---

### Reference implementation

`apps.lucesumbrarum.com/public/feedback-submit.php` + `public/admin/update.php` + `public/js/feedback.js`. See session log `docs/sessions/2026-04-21.md` ("Evening: bug-reporting feature built end-to-end") for the build narrative and every validation check performed.
