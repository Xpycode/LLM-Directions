## Web Lightbox — Native `<dialog>` + Delegated Click Handler

**Source:** `apps.lucesumbrarum.com/public/css/site.css` (the `.lightbox` block) + `public/js/lightbox.js` + the `<dialog>` markup in each `public/apps/*.html`. Added 2026-04-20.

**Use case:** Click any thumbnail in a gallery to enlarge it in a fullscreen overlay — the GitHub-style image viewer. Specifically for static-site marketing/portfolio pages with screenshot galleries on per-product detail pages. Single shared `<dialog>` per page, JS swaps the image source on each open. No library, no framework, ~40 lines of JS.

**When to reach for it:**
- Static or server-rendered HTML pages with 2-N screenshots in a `.gallery` / `.shot` / `.thumb` grid.
- Audience is on modern browsers (Safari 15.4+, Chrome 37+ for `<dialog>`; backdrop-filter Safari 9+ with `-webkit-` prefix). For a 2026+ marketing site this is universal.
- You want focus trapping, ESC-to-close, and proper modal a11y *for free* — without pulling in `react-modal`, `dialog-polyfill`, `headlessui`, or rolling your own.

**When *not* to use it:**
- You need next/previous navigation between images (this pattern is single-image-at-a-time; arrow-key navigation requires lifting the image list into JS state — different cookbook entry's worth).
- You need pinch-zoom or pan inside the enlarged image (use a library like PhotoSwipe or Medium-Zoom; native `<dialog>` doesn't help with gesture handling).
- The "thumbnails" are full-size already — clicking adds nothing. (Lightbox the *2× retina* version, not the same pixels.)
- You need to support IE11 or other ancient browsers. `<dialog>` requires polyfill there; at that point use a library.

---

### Anatomy

```
HTML (per page)                   CSS (once)              JS (once)
──────────────────                ─────────────           ─────────
<div class="gallery">             .shot { ... }           lightbox.js
  <div class="shot">              .lightbox { ... }       (IIFE — finds
    <img src="thumb.webp">        .lightbox::backdrop     the dialog,
    <p>caption</p>                .lightbox img           wires up clicks
  </div>                          @keyframes              + a11y attrs)
  ...                             prefers-reduced-motion
</div>

<!-- once per page, before </main> or </body> -->
<dialog class="lightbox" aria-label="Enlarged screenshot">
  <img alt="" />
</dialog>

<script src="/js/lightbox.js" defer></script>
```

The `.shot` divs stay as plain divs in HTML — JS adds `tabindex`, `role`, `aria-label`, and the keydown handler at runtime. Markup stays readable; a11y wiring lives in one place.

---

### CSS

```css
.shot {
  border-radius: 16px;
  overflow: hidden;
  background: var(--surface-card);
  border: 1px solid var(--border);
  cursor: zoom-in;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.shot:hover {
  transform: translateY(-2px);
  box-shadow: 0 2px 4px rgba(26,26,30,0.06), 0 14px 36px rgba(26,26,30,0.10);
}
.shot:focus-visible {
  outline: 2px solid var(--ink);
  outline-offset: 3px;
}
.shot img { width: 100%; display: block; }

/* Lightbox */
.lightbox {
  border: none;
  background: transparent;
  padding: 0;
  margin: 0;
  max-width: none;
  max-height: none;
  width: 100vw;
  height: 100vh;
}
.lightbox[open] {
  display: flex;
  align-items: center;
  justify-content: center;
  animation: lightbox-in 0.2s ease-out;
}
.lightbox::backdrop {
  background: rgba(26, 26, 30, 0.78);
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
}
.lightbox[open]::backdrop {
  animation: lightbox-backdrop-in 0.2s ease-out;
}
.lightbox img {
  max-width: 92vw;
  max-height: 92vh;
  width: auto;
  height: auto;
  object-fit: contain;
  border-radius: 14px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.35), 0 30px 80px rgba(0,0,0,0.45);
  cursor: zoom-out;
}
@keyframes lightbox-in {
  from { opacity: 0; transform: scale(0.96); }
  to   { opacity: 1; transform: scale(1); }
}
@keyframes lightbox-backdrop-in {
  from { opacity: 0; }
  to   { opacity: 1; }
}

/* Required — drift loops without this fail WCAG 2.3.3 */
@media (prefers-reduced-motion: reduce) {
  .lightbox[open], .lightbox[open]::backdrop { animation: none; }
}
```

---

### JS (`/js/lightbox.js`)

```js
(function () {
  const dialog = document.querySelector('dialog.lightbox');
  if (!dialog) return;
  const dialogImg = dialog.querySelector('img');
  if (!dialogImg) return;

  // A11y wiring — keep HTML clean by adding attributes at runtime.
  document.querySelectorAll('.shot').forEach((shot) => {
    if (!shot.hasAttribute('tabindex')) shot.tabIndex = 0;
    if (!shot.hasAttribute('role')) shot.setAttribute('role', 'button');
    if (!shot.hasAttribute('aria-label')) {
      const caption = shot.querySelector('.shot-caption')?.textContent.trim();
      shot.setAttribute('aria-label', caption ? `Enlarge: ${caption}` : 'Enlarge screenshot');
    }
    shot.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        shot.click();
      }
    });
  });

  // Open on click anywhere inside a .shot (delegated — handles future additions).
  document.addEventListener('click', (e) => {
    const shot = e.target.closest('.shot');
    if (!shot) return;
    const sourceImg = shot.querySelector('img');
    if (!sourceImg) return;
    dialogImg.src = sourceImg.src;
    dialogImg.alt = sourceImg.alt || '';
    dialog.showModal();
  });

  // Click anywhere on the dialog (image OR backdrop) closes — matches GitHub.
  dialog.addEventListener('click', () => dialog.close());

  // Free the image src on close so memory doesn't accumulate.
  dialog.addEventListener('close', () => { dialogImg.src = ''; });
})();
```

---

### Why these specific choices

| Decision | Why |
|---|---|
| Native `<dialog>` over a custom div | Free focus trapping, free ESC-close, free `::backdrop` pseudo-element, correct ARIA roles, correct inert-while-open semantics. Three lines of CSS replace what most React modal libs reimplement in 200 LOC. |
| Single shared dialog, swap `img.src` | Keeps DOM tiny even with N=20+ thumbnails. Prevents N preloaded full-size images bloating the page. |
| `.lightbox[open]` for `display: flex`, not bare `.lightbox` | The UA stylesheet has `dialog:not([open]) { display: none }` but author styles override it. Scoping `display: flex` to `[open]` lets the dialog stay hidden when closed without fighting the cascade. |
| `width: 100vw; height: 100vh` on the dialog itself | Default `<dialog>` sizing is "shrink-wrap to content," which would put a tiny dialog centered in the viewport — backdrop would only cover that tiny area. Forcing full-viewport size + `display: flex` + `justify-content: center` does the centering manually. |
| Image clamped to `92vw × 92vh` with `object-fit: contain` | Image never crops, never overflows, never touches the viewport edges. The 8% margin reads as "fullscreen-but-framed" rather than "edge-to-edge." |
| `backdrop-filter` *and* `-webkit-backdrop-filter` | Safari 17.x still honors the prefixed form even though unprefixed works in newer builds. Both shipped costs nothing and covers older Safari. |
| Click-image-to-close (GitHub behavior) | Users arriving from GitHub expect this. To opt out, add `e.stopPropagation()` on a click listener attached to `.lightbox img` so only the backdrop/ESC close. |
| A11y attrs at runtime, not in HTML | `tabindex`, `role`, `aria-label` for every `.shot` would mean N HTML changes per page × M pages. Doing it in the IIFE means one place to audit and the markup stays readable. The generated `aria-label` reuses the caption text so the announcement is meaningful. |
| Delegated `document.addEventListener('click', ...)` | One listener handles all current and future `.shot` elements — works even if your gallery is generated from JSON or appended after page load. |
| `dialog.close()` on `dialog.click()` | The dialog element receives the click whether the user clicks the image (which is inside) or the backdrop area (which is technically outside but still attributed to the dialog). One handler covers both. |
| `dialogImg.src = ''` on close | Frees the decoded bitmap from memory. Important if users open and close many large screenshots; matters less for 2-3 small ones. Cheap to keep regardless. |

---

### Variations

**Stop click-image-from-closing.** If users complain about accidental closes, attach a `stopPropagation` handler to the image:

```js
dialogImg.addEventListener('click', (e) => e.stopPropagation());
```

Now only backdrop click and ESC close. Add a visible close button (`<button class="lightbox-close" aria-label="Close">×</button>` in the dialog markup, position absolute top-right) for clarity.

**Next/previous navigation.** Lift the gallery into JS state:

```js
const shots = Array.from(document.querySelectorAll('.shot img'));
let currentIndex = 0;

function open(index) {
  currentIndex = index;
  dialogImg.src = shots[index].src;
  dialogImg.alt = shots[index].alt || '';
  if (!dialog.open) dialog.showModal();
}

document.addEventListener('keydown', (e) => {
  if (!dialog.open) return;
  if (e.key === 'ArrowRight') open((currentIndex + 1) % shots.length);
  if (e.key === 'ArrowLeft')  open((currentIndex - 1 + shots.length) % shots.length);
});
```

**Caption inside the lightbox.** Show the caption below the enlarged image:

```html
<dialog class="lightbox">
  <figure>
    <img alt="" />
    <figcaption></figcaption>
  </figure>
</dialog>
```

```js
const figcaption = dialog.querySelector('figcaption');
// in the open handler:
figcaption.textContent = shot.querySelector('.shot-caption')?.textContent || '';
```

Style `figcaption` with white-on-dark, centered below the image.

**Pinch-zoom / pan.** Native `<dialog>` doesn't help here. Use [PhotoSwipe](https://photoswipe.com) or [Medium-Zoom](https://github.com/francoischalifour/medium-zoom). Both work alongside `<dialog>` if you want native modal semantics + library-provided zoom.

---

### Pitfalls

- **Don't forget `[open]` in the `display: flex` selector.** `.lightbox { display: flex }` (unscoped) would make the closed dialog visible — the UA's `dialog:not([open]) { display: none }` is overridden by any author rule with same specificity. Always scope your dialog display rules to `[open]`.
- **Don't put the `<dialog>` inside a `position: relative` ancestor with `transform` or `filter` set.** That breaks the `<dialog>`'s top-layer rendering — it'll be positioned relative to the transformed ancestor, not the viewport. Put the dialog at the body root or just before `</main>` to be safe.
- **Don't use `box-shadow` on the lightbox image.** Same trap as in [41-web-hero-floating-icons.md](41-web-hero-floating-icons.md): for screenshots with rounded corners (set via `border-radius` on the image), `box-shadow` will paint a rectangle. Either keep the image rectangular and shadow it, or use `filter: drop-shadow()` instead.
- **Don't preload the full-size images.** This pattern keeps thumbnails as the only thing the page loads. The full-size only loads when the user clicks. Don't accidentally use `<picture>` with a `srcset` that puts the full-size in the page — that defeats the whole point.
- **Don't forget `prefers-reduced-motion`.** Even the 0.2s open animation can trigger vestibular issues. The `@media (prefers-reduced-motion: reduce)` rule above is mandatory, not optional.
- **Don't reuse the same image at thumbnail and lightbox sizes without checking pixel dimensions.** If your "thumbnail" is already 1200px wide, the lightbox is showing the same pixels — the user just gets the same image bigger. That's not enlargement; it's upscaling. Either ship a separate `-large.webp` source for the lightbox (set `dialogImg.src = sourceImg.dataset.large || sourceImg.src`) or ensure the thumbnail itself is rendered smaller than its native resolution (CSS `width: 100%` of a narrow grid column on a 2x retina source achieves this).

---

### Reference implementation

`apps.lucesumbrarum.com` — per-app detail pages. View source at `public/apps/cropbatch.html` (or any sibling) — search for `<dialog class="lightbox">`. JS at `public/js/lightbox.js`. CSS in `public/css/site.css` — search `.lightbox` and `.shot`.

Brand context: warm-neutral palette, frosted dark backdrop, soft shadow, screenshot grid with 2-column responsive layout.

Session log with the full design rationale: `apps.lucesumbrarum.com/docs/sessions/2026-04-20.md` ("Late evening: A closer look polish").
