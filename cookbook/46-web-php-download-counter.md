## Web Download Counter — PHP + Flat-File JSON, No Backend

**Source:** `apps.lucesumbrarum.com/public/dl.php` + `public/downloads/counts.json` + `public/js/download-stats.js`. Added 2026-04-21.

**Use case:** A static (or static-ish) marketing/portfolio site that hosts downloadable assets — DMGs, ZIPs, installers, PDFs — and wants per-asset download counts shown on the page, without standing up a backend, database, or third-party analytics. The whole apparatus is ~50 lines of PHP + ~20 lines of JS + a `{}` JSON file. Apache serves the actual bytes; PHP just tallies and 302-redirects.

**When to reach for it:**
- Apache + PHP shared hosting (most cheap web hosts: Strato, IONOS, OVH, DreamHost, SiteGround, etc.).
- 1-50 downloadable assets. Past that, JSON-file contention may matter — see "scaling" below.
- You're OK with the counts being **public-by-design** (anyone can fetch `counts.json`). For most marketing sites this is a feature, not a bug — it's the same transparency model GitHub uses for its own download badges.
- You explicitly do **not** want third-party analytics (Plausible, Umami, GA, etc.) — the counter is first-party, no cookies, no fingerprinting, no external requests.

**When *not* to use it:**
- Counts must be private or auditable. JSON is world-readable; logs/database give you privacy and audit trails.
- High concurrency (hundreds of simultaneous downloads). `flock` serializes writes; under heavy load the lock becomes the bottleneck. Consider Redis INCR or a real DB.
- You need per-user / per-IP analytics (unique downloaders, geo, repeat-rate, conversion). This is an *aggregate counter*, not analytics.
- You're on Cloudflare Pages / Netlify / Vercel where PHP isn't an option. Use a Cloudflare Worker (~30 lines of JS + KV) instead.

---

### Anatomy

```
public/
├── dl.php                 ← validate + count + 302 redirect
├── downloads/
│   ├── counts.json        ← flat tally: {"appname": N, ...}
│   ├── cropbatch.dmg      ← actual asset bytes (Apache serves)
│   ├── sigil.dmg
│   ├── …
└── js/
    └── download-stats.js  ← reads counts.json, populates UI
```

Flow per click:
1. User clicks `<a href="/dl.php?app=cropbatch">` on a detail page.
2. `dl.php` validates the app name (regex), finds the file, checks UA against bot list, **only on GET requests** opens `counts.json` under `LOCK_EX`, increments, releases.
3. PHP issues a `302 Location: /downloads/cropbatch.dmg`. Browser follows.
4. Apache serves the DMG bytes directly — `Range:` requests for resumable downloads, correct MIME, no PHP overhead during the megabyte-pumping part.

UI flow:
1. Each detail page has `<div class="download-stats" data-app="cropbatch">latest v1.4 · 10 MB</div>` — the version + size text is *baked into the HTML* so the line reads correctly even if JS fails or the count is 0.
2. `download-stats.js` fetches `/downloads/counts.json` once on page load.
3. When count > 0, JS prepends `"N downloads · "` to the static text.

---

### `dl.php` (the whole thing)

```php
<?php
// Download redirect + counter. Matches /dl.php?app=<name>, increments
// /downloads/counts.json, then 302s to the actual DMG/ZIP/saver file.
// Apache serves the bytes — PHP just tallies and redirects.

$app = isset($_GET['app']) ? $_GET['app'] : '';

// Only allow alphanumerics, underscore, dash. Blocks path traversal.
if (!preg_match('/^[a-zA-Z0-9_-]{1,64}$/', $app)) {
  http_response_code(400);
  header('Content-Type: text/plain; charset=utf-8');
  echo "Invalid app name.\n";
  exit;
}

$dir = __DIR__ . '/downloads';

// Find the distributable — first match wins among known extensions.
$ext_used = null;
foreach (['dmg', 'zip', 'saver', 'pkg'] as $ext) {
  if (is_file("$dir/$app.$ext")) {
    $ext_used = $ext;
    break;
  }
}
if ($ext_used === null) {
  http_response_code(404);
  header('Content-Type: text/plain; charset=utf-8');
  echo "Download not found.\n";
  exit;
}

// Only count GET requests — browser speculative-prefetch and curl -I (HEAD)
// would otherwise inflate the tally even when no real download happens.
$method = isset($_SERVER['REQUEST_METHOD']) ? $_SERVER['REQUEST_METHOD'] : 'GET';
$is_get = ($method === 'GET');

// Bot filter — skip the count increment but still allow the download.
$ua = isset($_SERVER['HTTP_USER_AGENT']) ? $_SERVER['HTTP_USER_AGENT'] : '';
$is_bot = preg_match('/bot|crawl|spider|slurp|curl|wget|python-requests|go-http/i', $ua);

if ($is_get && !$is_bot) {
  // Increment the counter under an exclusive lock so concurrent downloads
  // from the same app can't clobber each other.
  $counts_file = "$dir/counts.json";
  $fp = @fopen($counts_file, 'c+');
  if ($fp !== false) {
    if (flock($fp, LOCK_EX)) {
      rewind($fp);
      $raw = stream_get_contents($fp);
      $counts = ($raw !== false && $raw !== '') ? json_decode($raw, true) : [];
      if (!is_array($counts)) $counts = [];
      $counts[$app] = (isset($counts[$app]) ? (int)$counts[$app] : 0) + 1;
      ftruncate($fp, 0);
      rewind($fp);
      fwrite($fp, json_encode($counts, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES));
      fflush($fp);
      flock($fp, LOCK_UN);
    }
    fclose($fp);
  }
  // Failing to open/lock the counter file is non-fatal — the download
  // still proceeds. Apache permissions can be fixed without breaking users.
}

// 302 to the real asset; Apache handles byte ranges and Content-Type.
header("Location: /downloads/$app.$ext_used");
exit;
```

---

### `counts.json` (initial state)

```json
{}
```

Just an empty JSON object. `dl.php` creates entries on first hit.

---

### `download-stats.js` (the whole thing)

```js
// Populate each .download-stats[data-app] with the current count from
// /downloads/counts.json. The version string is already in the HTML, so
// the page still reads correctly if this fetch fails.

(function () {
  const nodes = document.querySelectorAll('.download-stats[data-app]');
  if (!nodes.length) return;

  fetch('/downloads/counts.json', { cache: 'no-store' })
    .then((r) => r.ok ? r.json() : {})
    .then((counts) => {
      nodes.forEach((el) => {
        const app = el.dataset.app;
        const n = (counts && typeof counts[app] === 'number') ? counts[app] : 0;
        const countEl = el.querySelector('.dl-count');
        if (n > 0 && countEl) {
          const label = n === 1 ? 'download' : 'downloads';
          countEl.textContent = n.toLocaleString() + ' ' + label + ' · ';
          countEl.hidden = false;
        }
      });
    })
    .catch(() => { /* offline / file missing — leave the static version text */ });
})();
```

---

### HTML wiring

Each download UI block:

```html
<div class="actions">
  <a class="btn-download" href="/dl.php?app=cropbatch">
    Download for Mac ↓
  </a>
  <a class="btn-ghost" href="https://github.com/Xpycode/CropBatch" target="_blank" rel="noopener">
    View on GitHub
  </a>
</div>
<div class="download-stats" data-app="cropbatch">
  <span class="dl-count" hidden></span>latest v1.4 · 10 MB
</div>
```

Plus once per page:
```html
<script src="/js/download-stats.js" defer></script>
```

CSS:
```css
.download-stats {
  margin-top: 14px;
  font-size: 13px;
  color: var(--ink-soft);
  min-height: 1.2em;          /* prevent layout shift when count loads in */
}
.download-stats .dl-count[hidden] { display: none; }
```

---

### Why these specific choices

| Decision | Why |
|---|---|
| **PHP redirects, doesn't serve bytes** | Apache serves files faster than PHP can stream them, handles `Range:` requests for resumable downloads natively, and gets the right `Content-Type` from `mime.types` automatically. PHP serving large files via `readfile()` blocks a worker for the whole download — terrible under load. The 302 hands off to Apache. |
| **Strict regex on the `app` parameter** (`[a-zA-Z0-9_-]{1,64}`) | Blocks path traversal (`../etc/passwd`), null bytes, URL-encoded shenanigans. The whitelist is more robust than blacklisting unsafe characters. Length cap prevents resource exhaustion via 10MB query strings. |
| **First-match across known extensions** | `dmg`, `zip`, `saver`, `pkg` covered — order matters (DMG preferred, then ZIP). Means the URL stays clean (`?app=cropbatch` not `?app=cropbatch&ext=dmg`) and clients don't need to know what flavor each app ships in. |
| **`fopen('c+')` not `fopen('a+')`** | `c+` opens for read/write without truncating, creates if missing. `a+` always seeks to end on write, which clobbers the JSON parse-modify-write flow. `c+` lets us `rewind()`, read existing JSON, modify in memory, `ftruncate(0)`, write back. |
| **`flock(LOCK_EX)` for the whole read-modify-write** | Without it, two concurrent downloads of the same file race: both read `{cropbatch: 5}`, both write `{cropbatch: 6}`, count loses one. With `LOCK_EX`, the second request blocks until the first releases. Slow under heavy contention but bulletproof for typical traffic. |
| **`@fopen` (suppress warnings)** | If counter file is unwritable (perms, disk full), we don't want a PHP warning leaking into the response body — that would corrupt the 302 redirect. The `@` swallows the warning; we check the return value explicitly. |
| **Counter failure is non-fatal** | If the lock fails, the file is unwritable, or the JSON is corrupt — the download *still proceeds*. The user gets their DMG; the operator gets to fix permissions on their schedule without breaking users. |
| **GET-only counting** | Browsers may issue speculative HEAD requests on hover-anticipated links (Chrome's "preload on hover" features, Safari's prefetch). `curl -I` does the same. Without the GET guard, those inflate counts even though no real download happens. The HEAD still returns the correct 302; it just doesn't tally. |
| **Bot UA filter is best-effort** | Sophisticated bots spoof browser UAs. The filter catches naive crawlers (Googlebot, etc.) and accidental scripted hits (curl, wget, python-requests). Real-world counts will still be inflated by some bot traffic — accept this. The `flock` matters more (prevents *data corruption*) than perfect bot detection (which only affects *number accuracy*). |
| **JSON, not SQLite/MySQL/Redis** | A flat 1KB JSON file beats spinning up a database for an aggregate counter. `json_encode` + `json_decode` are in core PHP. Backups are `git add counts.json`. Migrations don't exist — schema is "object of string→int". |
| **Counts public at `/downloads/counts.json`** | Anyone can fetch the whole tally. This is intentional: the JS already does it on every page load (it's how the UI populates), so there's no point pretending the data is private. Treat it like GitHub's public download badges — transparency by default. |
| **Static version text in HTML** | `latest v1.4 · 10 MB` is in the HTML, not added by JS. The line reads correctly even if `download-stats.js` fails (offline, blocked by an extension, server is down). The count is purely additive — when present, it prepends to the static text; when absent, the static text still says something useful. |
| **`min-height: 1.2em` on `.download-stats`** | Prevents layout shift when the count loads in async. Without it, the page jumps down by ~16px when JS runs. CLS metric improves; user doesn't see content jumping. |
| **`cache: 'no-store'` on the fetch** | We want the freshest count on every page load, not a stale browser cache. `no-store` is more aggressive than `no-cache` — doesn't even check `If-None-Match`. Counts.json is small (under 1 KB at any reasonable scale), so the bandwidth cost is negligible. |

---

### Variations

**Per-version counts.** If you ship multiple major versions and want to track them separately, change the URL to `/dl.php?app=cropbatch&v=1.4` and the JSON shape to `{"cropbatch": {"1.4": 12, "1.3": 5}}`. Total per app = sum of values.

**Per-day counts.** Track time series by keying on `YYYY-MM-DD` instead of (or alongside) the app name: `{"cropbatch": {"2026-04-21": 3, "2026-04-22": 11}}`. Generates a sparkline-able dataset for free. Watch the JSON file size — a year of daily counts × 9 apps is ~3 KB still, fine.

**Counter reset endpoint.** Add `/dl.php?reset=1&token=...` that requires a long random token (stored in an env var or include) to clear the JSON. Useful after a flood of bot traffic. Don't omit the token check — public reset is a denial-of-counts attack.

**Stats page.** A `/stats.html` showing all counts in a table — fetches `counts.json`, renders a sorted table client-side. Adds nothing the per-app inline count doesn't show, but useful for the operator at a glance. Consider whether public-stats fits the brand voice.

**Cloudflare Worker version (no PHP).** If you're on Cloudflare Pages, swap PHP for a Worker reading/writing a KV namespace. Same shape, different runtime. Worker code is ~30 lines of JS, reads/writes are eventually consistent (acceptable for a counter), and you keep the static-site posture.

**SQLite for medium scale.** When `flock` contention starts mattering (say, a launch-day spike of ~10 downloads/sec), swap the JSON for a SQLite file with `BEGIN IMMEDIATE; UPDATE counts SET n = n + 1 WHERE app = ?; COMMIT;`. SQLite handles writer serialization natively and is still single-file. PHP has SQLite3 in core. ~15-line change.

---

### Pitfalls

- **Don't serve files via PHP `readfile()`.** Serving 100 MB through PHP blocks a worker for the entire download time — under any kind of concurrency, you'll exhaust the PHP worker pool. Always 302 to an Apache-served static file.
- **Don't skip `flock`.** Without it, concurrent counter increments race and you silently lose counts. The bug only shows up under load — looks "fine" in dev, then your launch-day numbers are mysteriously low.
- **Don't use `fopen('a+')` for the counter.** `a+` always seeks to end on write. You'd append a new JSON object each time instead of replacing the existing one. The file grows linearly and `json_decode` fails on the second hit.
- **Don't rely on `__DIR__` resolving the way you expect.** `__DIR__` is the directory of the PHP file, not the document root. If you symlink `dl.php` from elsewhere or move it later, the `downloads/` path breaks. For portability, consider `$_SERVER['DOCUMENT_ROOT'] . '/downloads'` if your hosting honors it correctly.
- **Don't forget the GET guard.** Without it, `curl -I` (HEAD) and browser speculative-prefetch increment counts. The user notices "the count was already 2 before I clicked" the moment the site goes live. Saw this exact bug in production on day one of `apps.lucesumbrarum.com`.
- **Don't store IPs or User-Agents in `counts.json`.** That converts a *counter* into *analytics* and pulls you into GDPR scope. If you need uniqueness, hash IP + day with a server-side secret and never write the IP itself.
- **Don't expose `dl.php` as the canonical asset URL.** Users will bookmark the URL they see in their downloads folder. The 302 means the canonical URL is `/downloads/cropbatch.dmg` (clean, versionless, friendly). If you instead serve via `dl.php`, every bookmarked link goes through the counter again — inflating numbers and creating PHP load for re-downloads.
- **Don't use BSD `flock` semantics if your hosting is on NFS.** `flock()` over NFS is unreliable on some setups. If your hosting is shared/clustered and uses NFS-mounted document roots, test the lock behavior or switch to `fopen` with exclusive create + rename atomics.
- **Don't trust the JSON file's existence.** `fopen('c+')` creates if missing — but only if the directory is writable. Test by deleting `counts.json` and hitting the endpoint; it should recreate cleanly.

---

### Reference implementation

`apps.lucesumbrarum.com` — every per-app detail page. View source at `public/apps/cropbatch.html` (or any sibling) — search for `class="download-stats"`. PHP at `public/dl.php`, JS at `public/js/download-stats.js`, counter data at `public/downloads/counts.json` (publicly fetchable on the live site).

Brand context: warm-neutral palette, single inline count line below the action buttons, no separate stats page. The download counter is integrated into each app's detail page where the context is — not a centralized analytics dashboard.

Session log with the implementation rationale + the day-one HEAD-counts-too bug: `apps.lucesumbrarum.com/docs/sessions/2026-04-21.md` ("Afternoon: card meta polish, then Strato-hosted DMGs + PHP download counter").
