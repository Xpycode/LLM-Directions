# 103 — One JSON roster as the single source of truth across PHP, JS & server-rendered HTML

**Best for:** a list that the same multi-page site repeats in several languages — the classic case is
a **roster of apps / products / tabs / categories** that shows up as a PHP allow-list, an HTML
`<select>` or card grid, one or more JS name-maps, and a JSON-LD `hasPart` block. Because PHP, JS and
static HTML **can't share a literal**, each copy gets hand-edited and they **drift** (an item missing
from one map, a casing mismatch, an allow-list that 400s a real item). This entry makes the roster a
**single `apps.json`** that every consumer reads. Direct sequel to the "keep `ALLOWED_APPS`(.php) +
dropdown(.html) + maps(.js) balanced by hand" footnote in **#102** — this is how you stop balancing
by hand. Composes with #49 (the PHP allow-list), #100 (the donate `APPS` map), #99 (deploy), #46.

---

## The smell: the same list in N places

`feedback-submit.php` `ALLOWED_APPS`, `feedback.html` `<select>`, `feedback.js` `APP_NAMES` +
`TITLE_EXAMPLES`, `admin.js` `APP_NAMES`, `index.html` JSON-LD, `donate.html` `APPS` — six copies of
one list. Adding an app = six edits; miss one and that surface silently breaks (the admin board shows
raw slugs, the homepage schema omits the app, the allow-list rejects it). **The fix is not "be more
careful" — it's to delete five of the six.**

> **One canonical JSON file. PHP reads it on the server; JS pages `fetch()` it; SEO/no-JS surfaces are
> server-rendered from it. Nothing else lists the items.**

```
                       ┌─ feedback-submit.php  → read on server  → $ALLOWED_APPS (fail-safe)
apps.json (the list) ──┼─ index.php (was .html) → echo JSON-LD   (crawler-facing → server-render)
                       ├─ feedback.js / admin.js → fetch()        → name map + <select> + pills
                       └─ donate.html            → fetch()        → ?app= personalization
```

## The canonical file — self-documenting, richer than a bare list

Put **everything keyed by the item's slug** here, not just the name — title hints, category, and
flags that decide which surfaces show it. A bare `["a","b"]` just moves the drift to the metadata.
JSON has no comments, so carry docs in an ignored `_` key:

```json
{
  "_": "SINGLE SOURCE OF TRUTH. Edit here only. Consumers: feedback-submit.php (ALLOWED_APPS),
        index.php (JSON-LD), feedback.js, admin.js, donate.html. portalPage=false => not listed
        on this site (own site elsewhere) so it's omitted from the homepage schema.",
  "apps": [
    { "slug": "cropbatch", "name": "CropBatch", "category": "MultimediaApplication",
      "portalPage": true,  "titleExample": "e.g. 'Export fails on 10k+ images'" },
    { "slug": "conjoyn",   "name": "Conjoyn",   "category": "MultimediaApplication",
      "portalPage": false, "titleExample": "e.g. 'Split clips not grouped'" }
  ]
}
```

A **per-item flag** (`portalPage`) is what lets one file serve surfaces with *different* membership —
e.g. an item that has its own separate site appears in the feedback roster + donate map but **not** in
this site's homepage schema. Exclusion = a flag, not a second list.

## Consumer A — PHP, server-side, with a fail-safe (the security-critical read)

A PHP `const` can't be assigned from a function, so the allow-list becomes a runtime variable. If the
roster can't load, **reject** rather than fall open — validation that silently accepts anything is
worse than a 500:

```php
$allowed = [];
$raw = @file_get_contents(__DIR__ . '/apps.json');
if ($raw !== false) {
  $d = json_decode($raw, true);
  if (is_array($d['apps'] ?? null))
    $allowed = array_values(array_filter(array_map(fn($a) => (string)($a['slug'] ?? ''), $d['apps'])));
}
if (!$allowed) { http_response_code(500); error_log('roster unreadable'); exit('Server misconfigured'); }
// …later: if (!in_array($app, $allowed, true)) $errors[] = 'Please choose an app from the list.';
```

## Consumer B — server-render the crawler-facing surface (decide .html vs .php)

The criterion for *server-render vs client-fetch* is **who reads it**:

- **Crawler-facing or must-work-without-JS (JSON-LD, `<noscript>` content) → server-render** (PHP).
- **Already JS-dependent → `fetch()`** (don't pay a rename for a page that needs JS anyway).

Converting `index.html` → `index.php` to server-render JSON-LD is **free when the page is the directory
index** — `https://site/` serves `index.php` once `index.html` is gone, so the public URL doesn't
change (no redirect, no sitemap edit). Renaming a *named* page (`feedback.html` → `.php`) is **not**
free — it changes an indexed URL and needs a 301 + sitemap/canonical updates; if that page already
requires JS, prefer client-fetch and leave the URL alone.

```php
<?php $apps = json_decode(file_get_contents(__DIR__.'/apps.json'), true)['apps'] ?? [];
$hasPart = [];
foreach ($apps as $a) { if (empty($a['portalPage'])) continue;
  $hasPart[] = ['@type'=>'SoftwareApplication','name'=>$a['name'],
                'applicationCategory'=>$a['category'],
                'url'=>'https://site/apps/'.rawurlencode($a['slug']).'.html']; } ?>
<script type="application/ld+json">
<?= json_encode(['@context'=>'https://schema.org','@type'=>'WebSite','hasPart'=>$hasPart],
                JSON_PRETTY_PRINT|JSON_UNESCAPED_SLASHES|JSON_UNESCAPED_UNICODE) ?>
</script>
```

## Consumer C — JS pages fetch, then sequence everything roster-dependent

The map was built **synchronously** before; now it's a `fetch`, so prefill, the `<select>`, filter
pills and list rendering must run **after** it resolves. Use `.finally()` so the page still degrades
if the roster 404s:

```js
const NAMES = {}, ORDER = [], EXAMPLES = {};
fetch('/apps.json', { cache: 'no-store' })
  .then(r => r.ok ? r.json() : Promise.reject(r.status))
  .then(d => (d.apps || []).forEach(a => { if (!a.slug) return;
      NAMES[a.slug] = a.name; ORDER.push(a.slug); if (a.titleExample) EXAMPLES[a.slug] = a.titleExample; }))
  .catch(() => { /* roster gone: <select> keeps its placeholder, list still tries */ })
  .finally(() => { populateSelect(); applyPrefill(); loadTheActualData(); });
```

## ⚠️ Gotchas that bite

- **Double-fill when JS injects a `<select>`/list:** if you switch a `<select>` from static `<option>`s
  to JS injection, you **must delete the static markup** (keep only the placeholder). Leaving it makes
  JS *append* a second set → 13 + 12 = 25 options. **`php -l` and JSON validation both pass while the
  form is broken** — test the **rendered DOM** (headless browser: assert `select.options.length`), not
  just the lint.
- **Deploy that never prunes (renamed file shadows the new one):** an `lftp mirror` without `--delete`
  (#99) leaves the old `index.html` on the server, and Apache's `DirectoryIndex` serves `.html`
  **before** `.php` → `/` keeps serving the stale page while `/index.php` works. Remove the obsolete
  file by hand (`lftp … rm index.html`); expect auto-mode to flag the prod delete.
- **Cache-buster blind to the new extension:** a deploy step that stamps `?v=` only on `*.html` will
  skip your new `index.php` → its stylesheet never busts on a future CSS change. Add `--include='*.php'`.
- **Not every list needs this.** A download redirect that validates by **regex + file-existence**
  (`dl.php`, #46) self-heals and is *not* a roster consumer — don't wire it to the JSON. Centralize the
  lists that **enumerate**, not the ones that **probe**.
- **Don't centralize bespoke prose.** The visible card grid (per-item screenshots, descriptions,
  version strings) is hand-curated marketing copy — leave it literal. Centralize the **machine roster**
  (allow-list, schema, name maps), not the editorial content; forcing rich HTML into JSON is a net loss.

## Payoff (and how to prove it)

Adding an item becomes **one line in one file**. Prove it end-to-end: append a new slug to `apps.json`
only, deploy, and confirm it appears on every surface (form options, validation accepts it, JSON-LD if
flagged) with **no other edit** — that round-trip is the regression test for the whole pattern.

Source: App-Websites monorepo (`apps.lucesumbrarum.com/public/apps.json` + `feedback-submit.php` /
`index.php` / `js/feedback.js` / `admin/admin.js` / `donate.html`). Pairs with #102 (replaces its
manual-balance footnote), #49 (`ALLOWED_APPS` becomes a reader), #100 (donate map becomes a reader),
#99 (deploy + the no-`--delete` shadowing trap), #46 (the `?app=` convention / the self-healing list
that is *not* a consumer).
