## Web Hero — Floating-Icon Constellation

**Source:** `apps.lucesumbrarum.com/public/index.html` + `public/css/site.css` (the `.hero-stage` / `.float-icon` block, added 2026-04-20).

**Use case:** A landing-page hero where the centered text alone leaves too much negative space, but the brand voice forbids compressing the type or pulling the cards-below up into the first viewport. Fill the negative space *around* the headline with the product's own icons, scattered at gentle angles with soft shadows, optionally drifting on slow staggered loops. Reuses existing assets — no new artwork.

**When to reach for it:**
- Boutique-software / portfolio site with an editorial voice (centered serif headline, generous whitespace, no hero CTA button).
- 2-5 products to feature. Below 2 the composition is lopsided; above 5 it's noisy.
- The products already have well-rendered icons (rounded-square macOS / iOS / app icons; brand marks; product seals). Pure logos with thin strokes won't carry the visual weight.
- Hero is text-only and the user has flagged it as "feels empty" or "too much space."

**When *not* to use it:**
- A single product (use a hero screenshot or device mockup instead — see [05-export-file-dialogs.md](05-export-file-dialogs.md)-style framed shot).
- Conversion-driven landing (SaaS pricing, lead-gen). Floating decorative elements compete with the CTA; use a directed visual instead.
- Mobile-first products. The pattern hides icons under 820px (recognition fails before fit fails), so on a phone-first audience you're shipping nothing.

---

### Anatomy

```
[                    .hero-stage (max-width: 1280px, position: relative)                ]
  [.float-1]                                                          [.float-2]
                          [          .hero (centered text)         ]
                                       [.float-3]
```

Three layers stacked by `z-index`:
- `.hero-stage` — relative, full-width container. `overflow: hidden` so absolutely-positioned icons don't trigger horizontal page scroll on narrow desktop widths.
- `.float-icon` (1, 2, 3) — `position: absolute`, `z-index: 1`, `pointer-events: none`, `user-select: none`. Decorative; never receives interaction.
- `.hero` — the existing centered-text block. `z-index: 2` so the headline sits above the icons if they ever overlap during the drift animation.

---

### HTML

```html
<div class="hero-stage">
  <img class="float-icon float-1" src="/img/icons/app-a.webp" alt="" aria-hidden="true" />
  <img class="float-icon float-2" src="/img/icons/app-b.webp" alt="" aria-hidden="true" />
  <img class="float-icon float-3" src="/img/icons/app-c.webp" alt="" aria-hidden="true" />

  <section class="hero">
    <h1>Headline.</h1>
    <p class="lede">…</p>
  </section>
</div>
```

**Accessibility — both `alt=""` and `aria-hidden="true"`.** The icons appear again in the cards below, so screen readers should announce them once (in the cards), not twice. Empty `alt` removes them from the accessibility tree; `aria-hidden` belt-and-suspenders for SR variants that still announce empty-alt images.

---

### CSS

```css
.hero-stage {
  position: relative;
  overflow: hidden;
  max-width: 1280px;
  margin: 0 auto;
}

.hero-stage .hero {
  position: relative;
  z-index: 2;
  /* override your existing hero padding if needed */
  padding-top: 80px;
  padding-bottom: 56px;
}

.float-icon {
  position: absolute;
  display: block;
  border-radius: 22%;        /* matches macOS app-icon squircle */
  filter:
    drop-shadow(0 2px 4px rgba(26, 26, 30, 0.08))
    drop-shadow(0 14px 32px rgba(26, 26, 30, 0.16));
  pointer-events: none;
  user-select: none;
  z-index: 1;
  will-change: transform;
}

.float-1 {
  width: clamp(64px, 7vw, 92px);
  top: 22%;
  left: 11%;
  transform: rotate(-9deg);
  animation: float-drift-a 7s ease-in-out infinite;
}

.float-2 {
  width: clamp(64px, 7.5vw, 100px);
  top: 14%;
  right: 12%;
  transform: rotate(8deg);
  animation: float-drift-b 8s ease-in-out infinite;
}

.float-3 {
  width: clamp(56px, 6vw, 80px);   /* slightly smaller for depth */
  bottom: 10%;
  left: 24%;
  transform: rotate(-5deg);
  animation: float-drift-c 9s ease-in-out infinite;
  opacity: 0.92;                    /* subtle recession */
}

@keyframes float-drift-a {
  0%, 100% { transform: rotate(-9deg) translateY(0); }
  50%      { transform: rotate(-9deg) translateY(-10px); }
}
@keyframes float-drift-b {
  0%, 100% { transform: rotate(8deg) translateY(0); }
  50%      { transform: rotate(8deg) translateY(-8px); }
}
@keyframes float-drift-c {
  0%, 100% { transform: rotate(-5deg) translateY(0); }
  50%      { transform: rotate(-5deg) translateY(-6px); }
}

@media (max-width: 820px) {
  .float-icon { display: none; }
  .hero-stage .hero { padding-top: 64px; padding-bottom: 48px; }
}
```

**Don't forget:** the existing global `prefers-reduced-motion` rule should already kill these animations:

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation: none !important; transition: none !important; }
}
```

If your project doesn't have it, add it. Drift loops without that escape hatch fail WCAG 2.3.3.

---

### Why these specific values

| Decision | Why |
|---|---|
| `filter: drop-shadow(...) drop-shadow(...)` instead of `box-shadow` | App icons are rounded-squircle PNGs/WebPs with transparency. `box-shadow` paints a rectangle around the bounding box, which looks visibly *wrong* under the icon's curved corners. `drop-shadow` follows the alpha shape. Stacked (small/sharp + large/soft) it mimics how Apple renders app icons in marketing pages. |
| Two stacked `drop-shadow`s, not one | A single shadow either floats too high (small + harsh) or smudges too soft (large + diffuse). Stacking gives the icon both *contact* (the small shadow grounds it) and *lift* (the large shadow conveys the elevation). |
| `clamp(64px, 7vw, 92px)` widths | Icons must scale with viewport but never get smaller than ~56px (recognizability floor for app icons) or larger than ~100px (would compete with the headline). The `vw` middle term means desktop sizes track screen width without breakpoint hops. |
| Tilts of -9°/+8°/-5° | Different magnitudes per icon defeats the "wallpaper" feel of identical rotations. Keep all tilts under 12° — past that they read as "tossed/sloppy" rather than "casually placed." |
| Animation periods 7s / 8s / 9s | Coprime-ish periods so the three icons never sync. If all three drift at 8s they march together and the eye reads them as one object. Different periods = ambient breathing. |
| Drift amplitude 6-10px | Below 4px the motion isn't perceptible; above 14px it's distracting from reading. 6-10px registers as life without pulling focus. The bottom icon (`float-3`) gets the smallest amplitude because it's closest to the lede text. |
| Hide under 820px | Below 820px the centered text already fills its `max-width: 820px` container; absolutely-positioned icons would either overlap the text (bad) or push outside the viewport (worse). Recognition fails before fit fails — better to remove than to shrink past usefulness. |
| `.float-3` at 92% opacity + smaller size | Cheap depth cue: the icon furthest from the headline (and closest to the lede) sits visually "behind" the others. Without this the three icons read as the same plane. |
| `overflow: hidden` on `.hero-stage` | Absolutely-positioned children with negative offsets or large rotation can poke past the wrapper edge. On wide desktop monitors that becomes horizontal scroll. `overflow: hidden` on the stage is harmless (the icons are inside the 1280px max-width anyway) and bulletproof. |

---

### Variations

**Static (no animation).** Remove all three `animation:` lines. The composition still works as a still life — the drift is a nicety, not a load-bearing element. Try this first if `prefers-reduced-motion` users are a large share of your audience, or if you want a more "premium-print" feel.

**More icons (4-5).** Add `.float-4`, `.float-5` with new positions. Recommended placements for a 5-icon layout: top-left (-9°), top-right (+8°), middle-left (smaller, -4°), bottom-right (-3°), bottom-center (smaller, +6°). Alternate which side the smaller "depth" icons sit on — symmetry is boring.

**Bigger tilts ("scattered" feel).** Push tilts to -15° / +12° / -8°. Do this when the brand voice is playful (creative tools, indie game studios) rather than editorial.

**No tilts ("grid" feel).** Set all `transform: rotate(0)` (and remove rotation from the keyframes). Reads as more corporate / Vercel-ish. Lose some character; gain some authority.

**Add a screenshot, drop the icons.** If icons aren't doing enough lifting (e.g., they're too generic), replace the three `<img class="float-icon">` with a single tilted screenshot in a faux-window frame, positioned right of the centered text. This is the linear.app / raycast.com pattern. Different cookbook entry's worth — see when written.

---

### Pitfalls

- **Don't put the icons inside the `.hero` `<section>`.** That section has `max-width: 820px` (or similar) — icons would be confined to that narrow box and bunch around the text. The whole point of `.hero-stage` as a separate wider wrapper is to give icons the full ~1280px to scatter across.
- **Don't forget `pointer-events: none`.** Without it, the icons intercept hover/click events in the negative space — users hovering near the headline get a "wrong cursor" feel, and any links nearby become harder to hit.
- **Don't reuse the same icon image in the hero and in cards without `alt=""` + `aria-hidden`.** Screen-reader users will hear the same product name 6+ times on page load (once per icon in the hero, once per card). Decorative duplicates must be silenced.
- **Don't use `box-shadow` on the icons.** Re-stating because it's the most common mistake. The shadow will be a rectangle. It will look wrong. Use `filter: drop-shadow()`.
- **Don't animate `top`/`left`.** Those trigger layout. Use `transform: translateY()` (composited, GPU-accelerated). The keyframes above all do this — keep them that way if you copy/modify.
- **Don't forget the `transform: rotate()` *inside* the keyframes.** Each keyframe needs to restate the rotation, otherwise the animation overrides the static `transform: rotate(...)` and the icon snaps upright when the animation starts. (Easy bug to ship; CSS animations don't compose with the base transform — they replace it.)

---

### Reference implementation

`apps.lucesumbrarum.com` — landing hero. View source for the live values; the file lives at `public/index.html` and the styles at `public/css/site.css` (search `.hero-stage` and `.float-icon`). Brand context: warm-neutral linen palette, Instrument Serif headline, Inter body.

Session log with the design rationale and research: `apps.lucesumbrarum.com/docs/sessions/2026-04-20.md` (the "Evening: hero visual" section).
