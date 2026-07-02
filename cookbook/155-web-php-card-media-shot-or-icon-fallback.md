# 155 — Card media that self-upgrades: real screenshot if the file exists, else icon fallback

**Tags:** is_file, graceful degradation, data-driven card, object-fit contain, 16:10 tile, portal grid, Featured strip, no-code-change screenshot, loading=lazy screenshot gotcha

**Best for:** an app/product **card grid** (or a "featured" strip) where *some* items have a real
main-window **screenshot** and others don't yet. You want each card to show the screenshot when one
exists and quietly fall back to the **app icon on a tint tile** when it doesn't — **without editing
code** each time a capture lands. The naïve version hardcodes `shot--icon` per card (so every new
screenshot is a manual markup edit) or hardcodes an `<img src>` that 404s until the file shows up.
This makes the media **file-driven**: drop `<slug>-hero.webp` into the screenshots dir and the card
upgrades itself on the next request. Composes with **#103** (the `apps.json` roster the cards loop
over) and **#41** (hero) / **#46** (`dl.php`); verify with **#148**'s WebKit-over-HTTP recipe.

---

## The smell: markup that has to be hand-edited when an asset arrives

```php
<!-- every card hardcodes its media type; a new screenshot = find-this-card-and-rewrite-it -->
<div class="shot shot--icon"><img src="/img/icons/<?= $slug ?>.webp" ...></div>
```

Two failure modes: (1) you forget to flip a card to a real shot after capturing it, so it stays an
icon forever; (2) you pre-wire `<img src=".../<slug>-hero.webp">` for a shot that doesn't exist yet,
and it 404s / shows a broken image until someone uploads the file. **The list of "which cards have a
shot" drifts from the actual files on disk.**

## The fix: probe the filesystem, render the branch that matches reality

Let the presence of the file decide. One `is_file()` per card; the disk *is* the source of truth for
"do we have a shot for this app."

```php
<?php foreach ($featured as $a):
        $slug = (string)($a['slug'] ?? '');
        $name = (string)($a['name'] ?? '');
        // Prefer a real main-window shot if one has been dropped into the portal
        // (<slug>-hero.webp); otherwise fall back to the app icon on a tile. Dropping
        // a future screenshot in place needs NO code change — the card upgrades itself.
        $shot     = '/img/screenshots/' . $slug . '-hero.webp';
        $hasShot  = is_file(__DIR__ . $shot);   // __DIR__ = the doc root of this .php
?>
        <a class="app-card" href="...">
<?php if ($hasShot): ?>
          <div class="shot"><img src="<?= htmlspecialchars($shot, ENT_QUOTES) ?>"
               alt="<?= htmlspecialchars($name, ENT_QUOTES) ?> main window"
               loading="lazy" width="640" height="400" /></div>
<?php else: ?>
          <div class="shot shot--icon"><img src="/img/icons/<?= htmlspecialchars($slug, ENT_QUOTES) ?>.webp"
               alt="<?= htmlspecialchars($name, ENT_QUOTES) ?> icon" loading="lazy" /></div>
<?php endif; ?>
          ...
        </a>
<?php endforeach; ?>
```

`is_file()` is a `stat()` — cheap, and fine for a page of ~15 cards. Use `__DIR__ . $webPath`, not
the web path alone: the check must hit the real file, while the `src` stays a web-absolute URL.

## Why one tile style survives both branches: `object-fit: contain` on a fixed tint

Make `.shot` a **fixed 16:10 tile on a warm tint**, and let both a wide window shot *and* a small
icon sit inside it with `object-fit: contain` — nothing crops, everything letterboxes onto the same
tint. That's what lets the two branches share a grid without the icon cards looking broken:

```css
.shot { aspect-ratio: 16 / 10; background: var(--tile-tint, #F2ECE0);
        display: grid; place-items: center; overflow: hidden; border-radius: 12px; }
.shot img          { width: 100%; height: 100%; object-fit: contain; }  /* real window shot */
.shot--icon img    { width: 40%;  height: auto; }                        /* icon, centered smaller */
```

A near-square app window (e.g. a benchmark verdict list) and a 16:10 window both just center on the
tint — graceful for whatever aspect the capture happens to be.

## Gotcha — verifying it headless: `loading="lazy"` + full-page screenshot = blank bottom rows

If you screenshot the page with Playwright WebKit (**#148**) to eyeball the grid, a `fullPage` shot
taken right after `networkidle` will show the **below-the-fold cards empty** — their `loading="lazy"`
images never entered the viewport, so they never loaded. That's a **capture artifact, not a bug**.
Scroll the page through first, then shoot:

```js
await page.evaluate(async () => {
  for (let y = 0; y < document.body.scrollHeight; y += 600) {
    window.scrollTo(0, y); await new Promise(r => setTimeout(r, 120));
  }
  window.scrollTo(0, 0);
});
await page.waitForLoadState('networkidle');
await page.screenshot({ path: 'full.png', fullPage: true });
```

Cross-check the images actually serve (`curl -o /dev/null -w '%{http_code}'`) so you don't chase a
"missing image" that's really just lazy-load.

**Source:** `apps.lucesumbrarum.com/public/index.php` (App-Websites portal, "Apps with their own
site" Featured strip), 2026-07-02. The same probe drives the 13-app grid.
