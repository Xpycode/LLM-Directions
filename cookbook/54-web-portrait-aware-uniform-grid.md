## Web Portrait-Aware Uniform Grid — `grid-auto-flow: dense` + `.portrait`

**Source:** `lucesumbrarum.photos` rebuild — `01_Source/gallery.js` + `01_Source/css/lu.css` (`.gallery-grid[data-style="uniform"]` block). Added 2026-04-23.

> *Legacy path: `01_Source/` predates the universal `01_Project/` code-home convention. New web projects put code in `01_Project/` — see `13_folder-structure.md`.*

**Use case:** A photo gallery with **mostly landscape** images plus occasional portraits. A naive uniform grid (`aspect-ratio: 3/2` on every cell) crops portraits into ugly landscapes via `object-fit: cover`. A naive masonry layout leaves big vertical gaps beside tall portraits. This pattern: portraits detected on image load get `.portrait` class → spans 2 rows × 1 column with `aspect-ratio: 2/3`; surrounding landscapes auto-fill the remaining slots via `grid-auto-flow: dense`.

Visual outcome:
```
Row 1:   [L] [L] [L]
Row 2:   [L] [P] [L]       ← P is portrait, spans rows 2+3
Row 3:   [L]  P  [L]       ← landscapes fill column 1 and 3 above/below
Row 4:   [L] [L] [L]
```

**When to reach for it:**
- Curated digital photography where most images are 3:2 landscape but some are portrait.
- You want "disciplined grid" aesthetic (uniform tile sizes) without butchering portraits.
- Portrait orientation is known *only at runtime* (from `img.naturalHeight > naturalWidth`). Baking orientation into HTML at build time is fine too, but the runtime approach is zero-config — drop in any image set.

**When *not* to use it:**
- All images share one aspect ratio — `aspect-ratio` alone is enough; no portrait class needed.
- You have mixed-aspect chaos (panoramic + square + portrait + 3:2 + 4:3) — use full masonry (cookbook #53). Uniform with one exception class assumes "mostly one aspect, few exceptions."
- You need pixel-perfect hand-curated layouts — the dense-flow reorders tiles invisibly. Source order in HTML is no longer visual order.

---

### Anatomy

```
CSS                                 HTML                         JS
─────                               ────                         ──
.gallery-grid[data-style=           <figure class=               On img load:
  "uniform"] {                        "gallery-item">              if naturalHeight >
  display: grid;                      <a class="gallery-link">       naturalWidth:
  grid-template-columns:                <img src="..."                item.classList
    repeat(3, 1fr);                       loading="lazy">              .add('portrait')
  grid-auto-flow: dense;              </a>                         → CSS reacts
  gap: 28px;                        </figure>                        instantly
}
.gallery-item { aspect = 3/2 default, implicit }
.gallery-item.portrait { grid-row: span 2; link aspect = 2/3 }
```

---

### The CSS

```css
.gallery-grid[data-style="uniform"] {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  grid-auto-flow: dense;      /* 🔑 fills gaps automatically */
  gap: 28px;
}
.gallery-grid[data-style="uniform"] .gallery-link {
  display: block;
  aspect-ratio: 3 / 2;        /* default landscape */
  overflow: hidden;
}
.gallery-grid[data-style="uniform"] .gallery-item.portrait {
  grid-row: span 2;           /* portrait cell 2 rows tall */
}
.gallery-grid[data-style="uniform"] .gallery-item.portrait .gallery-link {
  aspect-ratio: 2 / 3;        /* portrait shape */
}
.gallery-grid[data-style="uniform"] .gallery-link img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

@media (max-width: 900px) {
  .gallery-grid[data-style="uniform"] { grid-template-columns: repeat(2, 1fr); gap: 20px; }
}
@media (max-width: 600px) {
  .gallery-grid[data-style="uniform"] { grid-template-columns: 1fr; gap: 20px; }
}
```

### The JS

```js
// Inside the shared gallery.js IIFE
const unifGrid = document.querySelector('.gallery-grid[data-style="uniform"]');
if (unifGrid) {
  const markPortrait = (item) => {
    const img = item.querySelector('img');
    if (!img || !img.naturalWidth) return;
    if (img.naturalHeight > img.naturalWidth) {
      item.classList.add('portrait');
    }
  };
  unifGrid.querySelectorAll('.gallery-item').forEach((item) => {
    const img = item.querySelector('img');
    if (img.complete && img.naturalWidth) markPortrait(item);
    else img.addEventListener('load', () => markPortrait(item), { once: true });
  });
}
```

---

### Why it works

- `aspect-ratio` on `.gallery-link` (a real block `<a>`, NOT on `<picture>` — picture is transparent and ignores CSS sizing) gives the browser a concrete box to size. Images inside fill it with `object-fit: cover`.
- `grid-auto-flow: dense` tells the grid to *backfill earlier gaps* when a later item can fit an empty slot. Without `dense`, portraits spanning 2 rows would still sit in their natural source-order slot, leaving a hole beside them.
- Portrait detection on `load` (not DOMContentLoaded) ensures `naturalWidth` / `naturalHeight` are populated — before load, both are 0.
- The `.portrait` class causes a tiny layout reflow — one per detected portrait. For galleries of 100+ images with a handful of portraits, this is imperceptible.

### Common mistakes
- Setting `aspect-ratio` on `<picture>` instead of the link/img → picture is a transparent element, ignores the CSS box model. Result: no constraint, image renders at natural size.
- Forgetting `grid-auto-flow: dense` → portraits create holes in the grid.
- Testing with only 1 portrait in a short gallery → dense flow's backfill only kicks in when the grid has enough landscape items to shuffle. Test with 50+ images.
- Adding `.portrait` at DOMContentLoaded → `naturalHeight` is 0; all items get misclassified as landscape. Always wait for `load` per-image.

### Pairs well with
- **Row-first masonry** (cookbook #53) — same `<div class="gallery-grid" data-style="...">` container, switch the `data-style` attribute to toggle layout style. One set of markup, two visual languages.
- **Native `<dialog>` lightbox** (cookbook #42) — each `.gallery-link` opens a full-size view on click.

### Extending to wide / panoramic
Add a third class `.panoramic`:
```css
.gallery-item.panoramic { grid-column: span 2; }
.gallery-item.panoramic .gallery-link { aspect-ratio: 3 / 1; }
```
JS tags it when `naturalWidth / naturalHeight > 2`. Dense flow handles the layout.
