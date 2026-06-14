# 100 — Web centralized donation / tip-jar page (one hub, `?app=`-aware, many free apps)

**Best for:** a multi-app site (marketing portal + per-app pages) where the apps are **free** and you
want an **optional donation / "buy me a coffee"** path — *especially* when many future apps will live
only on a portal grid with **no page of their own**, and where one or two apps have a **paid tier and
must be excluded**. Hosted-provider link (Ko-fi / PayPal / Stripe / GitHub Sponsors), **no payment
backend, no PII**. Composes with #46 (download counter) and #49 (feedback form) — same flat-file,
no-DB philosophy; deployed via #99.

---

## The idea: link to ONE page, never to the provider

The mistake is sprinkling `https://ko-fi.com/you` across 12 HTML files. Then changing provider, fixing
a typo'd handle, or A/B-testing a label means editing every file — and a half-built handle ships
half-fixed. Instead:

> **One canonical `donate.html` on the hub domain is the single source of the provider URL. Every
> other site/page/menu links to `/donate.html?app=<slug>` — never to the provider directly.**

This mirrors the `dl.php?app=<name>` convention (#46): the *app identity travels in the query string*,
and the destination page does the work. New page-less apps inherit the tip jar for free — just append
`?app=newslug` to a link.

```
portal index ───┐
app page  ?app=x ─┤
                  ├──►  /donate.html?app=<slug>  ──►  (the ONE provider URL)
sibling-site footer (absolute URL) ─┘            self-personalizes from ?app=
in-app Help menu  ?app=x ───────────┘
```

## `donate.html` — self-personalizing hub (the only file with the provider link)

```html
<!-- ════ KOFI_URL — the ONE place the provider link lives. Everything links to
     /donate.html, never here, so replace just this href to change provider. ════ -->
<a class="kofi-btn" id="kofiBtn" href="https://ko-fi.com/lucesumbrarum"
   target="_blank" rel="noopener">☕ Buy me a coffee</a>
<p class="lede" id="lede">Every app here is free — no ads, no tracking… optional tip.</p>

<script>
  // Per-app personalization via ?app= (same convention as dl.php?app=).
  // PAID apps are intentionally absent from this map → they fall through to generic.
  const APPS = { conjoyn:'Conjoyn', cropbatch:'CropBatch', /* …free apps only… */ };
  const slug = new URLSearchParams(location.search).get('app');
  const name = slug && APPS[slug.toLowerCase()];
  if (name) {
    document.title = `Support ${name} — Luces Umbrarum`;
    document.getElementById('lede')
      .insertAdjacentHTML('afterbegin', `Enjoying <strong>${name}</strong>? `);
    // Tag the outbound link so analytics/Ko-fi show which app drove the visit.
    const b = document.getElementById('kofiBtn');
    try { const u = new URL(b.href); u.searchParams.set('ref', slug.toLowerCase()); b.href = u.toString(); }
    catch (_) {}
  }
</script>
```

Graceful by design: unknown/missing `?app=` → generic page (no error). The `?ref=` tag is free
attribution — you learn which apps actually move people to give without any backend.

## Linking it in — reuse existing classes, watch for nested anchors

**Per-app pages (same domain):** add a quiet button using a class you already have (e.g. a ghost
button) plus a footer link — no new CSS, so copied stylesheets across sites don't drift:

```html
<a class="btn-ghost" href="/donate.html?app=cropbatch">☕ Donate</a>      <!-- in hero actions -->
<a href="/donate.html?app=cropbatch">Donate</a> &nbsp;·&nbsp; <a href="/imprint.html">Imprint</a>
```

**Sibling marketing sites on other subdomains** must use an **absolute** URL to the hub:

```html
<a href="https://apps.lucesumbrarum.com/donate.html?app=conjoyn">Donate</a>
```

**⚠ Nested-anchor trap (the portal card grid):** app cards are often a whole `<a class="card">…</a>`.
You **cannot** put a `<a href="/donate.html">` *inside* it — nested anchors are invalid HTML and
browsers silently split/drop them. Put the donate link in the app's **detail page** (hero/footer),
**not** in the grid card. Verify after scripted edits:

```python
import re, glob
for p in glob.glob('**/*.html', recursive=True):
    h = open(p).read()
    for m in re.finditer(r'<a\b[^>]*>(.*?)</a>', h, re.S):
        if '<a ' in m.group(1): print('⚠ nested anchor in', p); break
```

## Scripted, idempotent insertion across N pages

Editing 11 app pages by hand drifts. Script it against a **stable anchor** present on every page —
the `dl.php?app=` href doubles as the slug source:

```python
import re, glob
for path in glob.glob('apps/*.html'):
    html = open(path).read()
    slug = re.search(r'/dl\.php\?app=([a-z0-9]+)', html).group(1)
    # idempotency: bail if a donate link is already in the actions block / footer
    m = re.search(r'(<a class="btn-download"[^>]*>.*?</a>)', html, re.S)
    if 'donate.html' not in html[m.end():m.end()+400]:
        btn = f'\n  <a class="btn-ghost" href="/donate.html?app={slug}">☕ Donate</a>'
        html = html[:m.end()] + btn + html[m.end():]
    if 'Donate</a>' not in html.split('<footer')[1]:
        html = html.replace('<a href="/imprint.html">Imprint</a>',
                            f'<a href="/donate.html?app={slug}">Donate</a> &nbsp;·&nbsp; '
                            '<a href="/imprint.html">Imprint</a>', 1)
    open(path, 'w').write(html)
```

## Decisions / gotchas

- **Selective scope.** Keep paid-tier apps **out** of the `APPS` map *and* don't add their links — a
  tip jar next to a "$14.99 Pro" muddies the message. The exclusion is a one-line absence, not a flag.
- **Single source of URL.** Everything links to `/donate.html`; only that file names the provider.
  Provider swap = one edit. Use a loud `KOFI_URL`/`PROVIDER_URL` comment so it's greppable.
- **No new shared CSS.** Reuse `btn-ghost`/footer-link styles. If you must style the provider button,
  scope it in a `<style>` inside `donate.html` only (don't touch the copied `site.css` — see #62/#39).
- **Hub is usually light-only.** If per-app dark mode lives in each app's own CSS (not the shared
  `site.css`), the hub page stays light — expected, not a bug.
- **Placeholder handle.** Before the real account exists, ship a clearly-marked placeholder
  (`ko-fi.com/<you>`) and track "replace handle + deploy" as a task — same discipline as #49's
  `POLAR_CHECKOUT_URL`.
- **Provider choice (free apps):** Ko-fi = best tip-jar fit (0% donation fee, no donor account,
  one-time + monthly). PayPal = universal but feels less indie. Stripe Payment Link = own branding,
  low EU fee, slightly more setup. GitHub Sponsors = 0% but donor needs a GitHub account.

Source: App-Websites monorepo (`apps.lucesumbrarum.com/public/donate.html` + 11 app pages + Conjoyn).
Pairs with #46 (`dl.php?app=` convention reused), #49 (flat-file/no-backend sibling), #99 (deploy),
#39/#62 (don't diverge the shared token stylesheet).
