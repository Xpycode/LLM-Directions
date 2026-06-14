# 105 — Single-source JS-injected nav / footer partials for a static multi-page site

**Best for:** a static multi-page site (plain `.html`, maybe one `.php` index) whose **header and
footer are hand-copied into every page** and have therefore **drifted** — the nav shows different
links depending where you are, a label means the wrong thing, the footer's copyright/link-set varies.
There's no template engine and no build step, so each copy is edited by hand and they fall out of
sync. This entry makes the **header and footer markup live in ONE JS file**; every page carries only
an empty placeholder. Sibling of **#103** (one JSON roster as single source) — same disease (a thing
duplicated across pages drifts), but the cure differs because here the duplicated thing is **markup**,
not shared data. Pairs with #100 (the donate hub the footer links to), #99 (deploy), #62/#39 (don't
diverge the shared stylesheet), #49 (the imprint/legal page the footer must reach).

---

## The smell: the same header in N pages, now in 5 versions

A 16-page portal's `<header>` was pasted into every file. Over time the nav drifted into five
variants: `Apps·Support·GitHub` / `Apps·Feedback·GitHub` / `Apps·Coming soon·GitHub` / `Apps·GitHub`
/ … — no two pages agreed, and "Support" ambiguously linked to the **donate** page (support *me*, not
help for the *user*). The footer had the same problem with extra per-page wrinkles. **The fix is not
"go fix all 16" — it's to delete the copies so there's only one place to be wrong.**

> **One JS file builds the partial. Every page carries only `<header id="site-nav"></header>` (resp.
> `<footer id="site-footer"></footer>`) + a `<script>` tag. The markup exists once.**

```
nav.js     (one LINKS array) ──▶ every page's <header id="site-nav">   ← change a link once, here
footer.js  (one builder)     ──▶ every page's <footer id="site-footer"> ← + per-page data-* params
```

Changing the global nav afterwards = **one line in one array**, reflected on all pages — the whole
payoff. Test it by editing the array and confirming every page updated with no other edit.

## Build the DOM, don't string-concat

Mirror whatever XSS-safe discipline the site already uses (`createElement` / `textContent`, never
`innerHTML`) even though the nav has no user data — consistency means no page ever hand-builds markup
from strings. Each page decides **for itself** which item is "current" from `location.pathname`, so
there's zero per-page config:

```js
// nav.js — the ONE definition of the primary nav.
const LINKS = [
  { label: 'Apps',     href: '/#apps' },
  { label: 'Support',  href: '/support.html' },
  { label: 'Feedback', href: '/feedback.html' },
  { label: 'Donate',   href: '/donate.html' },
  // GitHub deliberately omitted: each app page links its own repo + footer carries it site-wide.
];
const mount = document.getElementById('site-nav');
if (!mount) return;
mount.classList.add('site-header');
const here = location.pathname.replace(/\/index\.(php|html)$/, '/') || '/';  // "/index.php" -> "/"
// …build brand + <nav>; for each link, aria-current="page" when href path === here…
function samePage(href){ return (href.split('#')[0].split('?')[0] || '/') === here; }
```

`/#apps` → path `/` → highlights "Apps" on the home page; sub-pages match their own slug; everything
else gets no current marker. **Absorb per-page inline glue too:** the scroll-shadow handler
(`header.classList.toggle('scrolled', scrollY>8)`) was an identical inline `<script>` on every page —
fold it into the injector so it lives once as well.

## Per-page data ≠ drift — the key distinction (vs #103)

The **footer** legitimately varies per page: the home page wants a *generic* Donate link, each **app
page** wants `donate.html?app=<slug>` **and** a link to *that app's* GitHub repo, and the
feedback/donate/imprint pages want **no** Donate link at all. That is **not drift** — drift is
duplicated markup that *should be identical but isn't*. A per-page value that's *supposed* to differ
is a **parameter**, not a copy.

> **Single-source the markup (in the JS); keep per-page values as `data-*` attributes on the
> placeholder.** Don't force them into a central roster — an app's repo name is *that page's* datum.

```html
<!-- home -->        <footer class="site-footer" id="site-footer" data-donate></footer>
<!-- an app page --> <footer class="site-footer" id="site-footer" data-app="sigil" data-repo="Sigil"></footer>
<!-- plain page -->  <footer class="site-footer" id="site-footer"></footer>
```
```js
// footer.js
const app  = mount.dataset.app;            // slug or undefined
const repo = mount.dataset.repo;           // repo name or undefined
const showDonate = 'donate' in mount.dataset || !!app;
//  Donate href = app ? `/donate.html?app=${app}` : '/donate.html'   (only if showDonate)
//  GitHub href = repo ? `${ORG}/${repo}` : ORG
```

**Pick the single-source mechanism by the data's nature** — three of them, don't confuse:

| Situation | Mechanism | Example |
|---|---|---|
| Identical markup everywhere | **Pure injection**, no per-page data | nav.js |
| Shared markup **+ per-page params** | **Injection + `data-*`** | footer.js |
| Shared **data** across surfaces (PHP/JS/SEO) | **Central JSON** (read/fetch/server-render) | #103 `apps.json` |

## The two costs of JS-injecting structural chrome — and the fixes

**(1) Layout shift (CLS).** An empty `<header>`/`<footer>` is ~0px tall until JS fills it → content
jumps. **Reserve the height in CSS** so the placeholder occupies the final size from first paint:

```css
.site-header { min-height: 63px; }                 /* == rendered nav height */
@media (max-width: 640px){ .site-header { min-height: 52px; } }
```
Load the injector with `defer` (runs after parse → placeholder exists, but ASAP).

**(2) No-JS = no chrome.** With JS off there's no nav and no footer. Acceptable for JS-heavy
utility/marketing pages (the nav already needs JS) — **but flag legally-required links.** A German
imprint (**§5 TMG/DDG**, "ständig verfügbar") lives only in the footer; if the footer needs JS it's
arguably non-compliant. Give *that* a `<noscript>` fallback (the nav had no legal content → none):

```html
<footer class="site-footer" id="site-footer" data-app="sigil" data-repo="Sigil">
  <noscript><div class="inner"><span>
    <a href="/imprint.html">Imprint</a> · <a href="mailto:you@example.com">Contact</a>
  </span></div></noscript>
</footer>
```
The injector does `mount.replaceChildren(inner)` → the `<noscript>` is removed when JS runs (and
`<noscript>` only renders with JS off anyway), so it never double-shows. It's the **one** place the
no-JS gap actually matters; verify it by grepping the **served HTML** (it won't be in the live DOM).

## Mechanics & gotchas

- **Exclude the private/admin page.** It usually has its OWN header/footer (different brand/links) →
  leave it alone. ⚠️ **`grep -rl` / `ugrep` may emit paths *without* `./`**, so a `grep -v '^\./admin/'`
  filter silently fails and your bulk `perl` rewrites admin too. **Verify the exclude excluded**; if it
  didn't, `git checkout -- admin/index.html` to restore (it was clean).
- **Harvest per-page values before deleting the old markup.** Scrape the 11 footers' GitHub URLs first
  — caught an irregular `Xpycode/syncthingStatus` (lowercase `s`) → **you can't derive the repo from
  the slug or display name; it must be explicit** (that's exactly why it rides as `data-repo`).
- **Encoding.** Footer markup carries a literal middot `·` (U+00B7) and `&nbsp;` — the Edit tool and
  `perl`-through-shell mangle the byte. Do the bulk placeholder swaps with a **Python script (explicit
  UTF-8, `·`/` `)**; in the injector build the separator as an **escape**,
  `const SEP = ' · '` (non-breaking, never a literal).
- **Pure-refactor discipline.** The injected output must be **byte-same** as the old footer (copyright
  text, "Built with…", link set, nbsp separators) — it's a refactor, not a redesign.
- **Cache-bust only if you touched the shared CSS.** Reserving `min-height` edits `site.css` → bump the
  `?v=<hash>` across all pages (the deploy script may already stamp this). The injector JS gets no
  `?v=` (consistent with sibling JS; new file on first deploy = no stale-cache risk).
- **Deploy is additive** (new `nav.js`/`footer.js`/`support.html` + in-place edits, **no renames**) →
  the no-`--delete` `lftp mirror` (#99) needs no manual prune — contrast #103's `index.html`→`.php`
  rename that left a shadowing orphan.

## Verify in a real browser (not just the linter)

`node --check nav.js footer.js`, then a **headless Chrome** pass asserting the rendered DOM per
page-type — because `php -l` + JSON-validate all pass while the page is visibly wrong (#103's
double-fill lesson):

- home: nav highlights **Apps**; footer Donate → `/donate.html`, GitHub → org
- app page: footer Donate → `?app=<slug>`, GitHub → `org/<Repo>` (check the irregular one)
- plain page: footer has **no** Donate
- header `offsetHeight` == the reserved `min-height` (no shift); **no console errors**
- served HTML (curl, not DOM) contains the `<noscript>` imprint fallback

Source: App-Websites (`apps.lucesumbrarum.com/public/js/nav.js` + `js/footer.js`, the empty
`#site-nav`/`#site-footer` placeholders across 16 pages, new `support.html`). Pairs with #103
(central-JSON sibling — different cure for the same disease), #100 (donate hub the footer targets),
#99 (additive deploy / no-`--delete`), #62/#39 (shared-stylesheet/token drift), #49 (the imprint page
the `<noscript>` keeps reachable).
