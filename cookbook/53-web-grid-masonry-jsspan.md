## Web Masonry — CSS Grid + JS-Computed `grid-row-end: span N`

**Source:** `lucesumbrarum.photos` rebuild — `01_Source/gallery.js` + `01_Source/css/lu.css` (`.gallery-grid[data-style="masonry"]` block). Added 2026-04-23.

> *Legacy path: `01_Source/` predates the universal `01_Project/` code-home convention. New web projects put code in `01_Project/` — see `13_folder-structure.md`.*

**Use case:** A photo gallery where images have varying aspect ratios (landscape, portrait, panoramic) and you want **masonry-style packing with reading order preserved** (left-to-right, top-to-bottom). CSS `column-count` masonry is dead-simple but fills column 1 entirely before column 2 — breaks narrative flow for a chronological photo series. This pattern uses CSS Grid with a tiny 8px row unit + JS that measures each image after load and sets `grid-row-end: span N`.

**When to reach for it:**
- Row-first reading order matters (photo series, a diary of images, blog post thumbnails).
- Image aspect ratios vary and you don't want uniform cropping.
- You're OK with a tiny layout-settle as `loading="lazy"` images stream in (masonry resolves progressively, not in one thrash).
- No framework, no build step. ~15 lines of JS, browser-native CSS Grid.

**When *not* to use it:**
- Firefox's experimental `grid-template-rows: masonry` is in your target matrix (it's Firefox-only in 2026; if Chrome adopts it, simpler).
- You genuinely want column-first flow — use `column-count` which is 2 lines of CSS and zero JS.
- Images are all identical aspect ratio — use uniform grid with `aspect-ratio` + `object-fit: cover`.
- You need SSR-perfect layout with zero shift — bake `width`/`height` attributes on each `<img>` at build time so the browser can pre-compute the span via CSS alone (requires knowing every image's natural dimensions).

---

### Anatomy

```
CSS (once)                         HTML (per page)              JS (once, shared)
─────────                          ──────────────               ────────────────
.gallery-grid[data-style=          <section class="gallery">    gallery.js (IIFE):
  "masonry"] {                       <div class="gallery-grid"    - find grid
  display: grid;                          data-style="masonry">    - for each item:
  grid-template-columns:               <figure class="gallery-item">   - on img load,
    repeat(3, 1fr);                      <img src="...">                measure
  grid-auto-rows: 8px;                   <!-- lazy, naturalWidth        naturalHeight/Width
  row-gap: 28px;                              kicks in async -->         * clientWidth
  column-gap: 28px;                    </figure>                   - span = ceil(
}                                      ...                             (h + gap) /
.gallery-item {                      </div>                          (8 + gap))
  margin: 0;                         </section>                  - item.style.gridRowEnd
  display: block;                                                   = 'span ' + span
}
```

---

### The CSS

```css
.gallery-grid[data-style="masonry"] {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  grid-auto-rows: 8px;               /* small row unit — images span many rows */
  column-gap: 28px;
  row-gap: 28px;
}
.gallery-item { margin: 0; display: block; }
.gallery-link { display: block; overflow: hidden; }
.gallery-link img {
  width: 100%;
  height: auto;
  display: block;
}

/* Mobile */
@media (max-width: 900px) {
  .gallery-grid[data-style="masonry"] {
    grid-template-columns: repeat(2, 1fr);
    column-gap: 20px; row-gap: 20px;
  }
}
@media (max-width: 600px) {
  .gallery-grid[data-style="masonry"] {
    grid-template-columns: 1fr;
    row-gap: 20px;
  }
}
```

### The JS

```js
// gallery.js (IIFE) — runs once per page
const grid = document.querySelector('.gallery-grid[data-style="masonry"]');
if (grid) {
  const ROW = 8; // must match grid-auto-rows in CSS

  const sizeItem = (item) => {
    const img = item.querySelector('img');
    if (!img || !img.naturalWidth) return;
    const w = item.clientWidth;
    if (!w) return;
    const h = w * (img.naturalHeight / img.naturalWidth);
    const gap = parseInt(getComputedStyle(grid).rowGap) || 0;
    const span = Math.ceil((h + gap) / (ROW + gap));
    item.style.gridRowEnd = 'span ' + span;
  };

  const items = grid.querySelectorAll('.gallery-item');
  items.forEach((item) => {
    const img = item.querySelector('img');
    if (img.complete && img.naturalWidth) sizeItem(item);
    else img.addEventListener('load', () => sizeItem(item), { once: true });
  });

  // Debounced re-layout on resize
  let rTO;
  window.addEventListener('resize', () => {
    clearTimeout(rTO);
    rTO = setTimeout(() => items.forEach(sizeItem), 150);
  });
}
```

---

### Why it works

- `grid-auto-rows: 8px` makes every implicit row 8px tall. An image needing 400px of height spans `ceil((400 + gap) / (8 + gap))` ≈ 49 rows. The quantization error is max 8px (invisible in practice).
- The span is computed from the image's **natural aspect ratio times the item's rendered width**, so the layout is correct even before the image paints pixels — as soon as `naturalWidth/naturalHeight` are populated on `load`, we know final dimensions.
- `loading="lazy"` on `<img>` means images fire `load` progressively as they scroll into view, so the page settles in waves (top fills first, then as user scrolls lower sections arrive). This is UX-positive, not a bug.
- Resize debounced at 150ms: `resize` fires rapidly during window drag; without the debounce you'd re-measure on every pixel change.

### Common mistakes
- Forgetting to sync `ROW` in JS with `grid-auto-rows` in CSS → spans are off by a factor.
- Not accounting for `rowGap` in the span formula → items consistently short by one gap per span.
- Measuring via `item.getBoundingClientRect().height` before the span is set — the cell is 8px tall with no span, measurement is wrong. Use `naturalWidth/naturalHeight * clientWidth` instead; it's independent of current row span.
- Firing the sizer on every image-load callback AND on every resize fires a layout thrash. Debounce resize, and run sizer once per image on its single `load` event.

### Pairs well with
- **Native `<dialog>` lightbox** (cookbook #42) — each `.gallery-link` is an `<a>` with `href` pointing to the full-size image; lightbox swaps `img.src` on click.
- **Uniform grid variant** (cookbook #54) — use `[data-style="uniform"]` instead; same page markup, different layout.
