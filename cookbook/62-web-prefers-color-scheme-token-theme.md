## Web Auto Dark Theme — Remap Design Tokens, Not Components

**Source:** `aloft.lucesumbrarum.com` (Aloft marketing site) — retrofitting dark mode onto a token-based static site that shipped light-only. Added 2026-06-03.

**Use case:** A static site built on CSS custom properties (`--surface`, `--ink`, `--accent`, …) needs to follow the visitor's OS appearance. You want the *whole page* to re-theme on `prefers-color-scheme: dark` with no JS, no toggle, no per-component dark rules — and you want app screenshots to swap to their dark variants at the same time.

**When to reach for it:**
- The site already reads colours through CSS variables at `:root` (a design-token system). The payoff scales with how disciplined that tokenisation is.
- You're shipping screenshots of a dark-mode-capable native app and a dark-Mac visitor on a light page would look inconsistent.
- You're on shared/static hosting — no build step, no theming framework.

**When *not* to use it:**
- The site hardcodes colours inline/per-component — a token flip reaches nothing; fix the tokenisation first or you'll be writing `.dark .foo` rules forever.
- You need a *manual* toggle (sun/moon button) with persisted preference — that's a different pattern (JS + `localStorage` + a `data-theme` attribute overriding the media query). This one is OS-driven only.
- Brand demands a single fixed appearance regardless of OS.

---

### The core move: override tokens inside one media query

Every component already reads `var(--token)`. So re-theming the entire site is ~20 property overrides in **one** block — the cascade does the rest. Put it in the project's *override* stylesheet (not the shared base) so a multi-app design system stays undiverged.

```css
:root {
  color-scheme: light dark;   /* lets UA controls/scrollbars/form widgets follow OS */
  /* …light token values inherited from the base stylesheet… */
}

@media (prefers-color-scheme: dark) {
  :root {
    --surface:            #14161A;   /* cool slate */
    --surface-card:       #1E2228;
    --border:             #2B313B;
    --ink:                #ECEEF1;    /* near-white, never pure #fff */
    --ink-muted:          #A0A6AF;
    --accent:             #0a84ff;    /* Apple's dark-mode system blue */
    --accent-soft:        rgba(10, 132, 255, 0.22);
    --ghost:              rgba(255, 255, 255, 0.06);  /* was rgba(0,0,0,…) */
    --shadow-soft:        0 1px 2px rgba(0,0,0,.35), 0 8px 24px rgba(0,0,0,.45);
  }
}
```

`color-scheme: light dark` is not optional — without it, native scrollbars, `<input>`/`<select>` widgets, and form autofill keep rendering in light UA chrome on your dark page.

---

### Step 2 — audit the colours that bypass the tokens

**A token flip only re-themes what uses tokens.** Every hardcoded hex is invisible to it and will glare light-on-dark. Find them mechanically:

```bash
# hardcoded colours that are NOT var(...) — these need explicit dark patches
grep -nE "#[0-9A-Fa-f]{3,6}|rgba?\(" css/*.css | grep -vi "var("
```

On the Aloft site this surfaced exactly six, all patched inside the same `@media` block:

```css
@media (prefers-color-scheme: dark) {
  /* white input-focus background → glares; pull to a token */
  .form input:focus { background: var(--surface-card); }

  /* a pill whose base inverts via --ink but whose :hover is hardcoded dark */
  .btn-download:hover { background: #D4D7DC; }

  /* semantic status chips: keep the hue, drop to translucent dark fills */
  .status--open  { background: rgba(245,196,70,.16); color:#E8C56B; border-color: rgba(245,196,70,.32); }
  .status--wip   { background: rgba(10,132,255,.16); color:#7FB4FF; border-color: rgba(10,132,255,.34); }
  .status--fixed { background: rgba(60,200,120,.15); color:#6FCB80; border-color: rgba(60,200,120,.32); }
}
```

The grep *is* the pattern — every match is either fine (already token-derived) or a bug waiting for dark mode.

---

### Step 3 — switch screenshots with `<picture>`, fix the lightbox

Pure-CSS, no JS, lazy-load friendly, downloads only the matching file:

```html
<picture>
  <source srcset="/img/shot-dark.webp" media="(prefers-color-scheme: dark)" />
  <img src="/img/shot-light.webp" alt="…" />   <!-- light is the fallback -->
</picture>
```

**The gotcha that bites everyone:** an `<img>` inside `<picture>` keeps its literal `src` *attribute* (the light fallback) forever. The browser renders whatever `<source>` matched, exposed only as **`currentSrc`**. Any JS that copies the image elsewhere must read `currentSrc`:

```js
// lightbox: enlarge the variant the browser actually chose, not the fallback
dialogImg.src = sourceImg.currentSrc || sourceImg.src;   // NOT just .src
```

With plain `.src`, a dark-mode visitor sees a dark thumbnail but the lightbox enlarges the *light* image.

---

### Why it works
- **Tokens centralise the theme.** One `:root` override under a media query cascades to every selector. The alternative — `.dark .component {}` rules — scales linearly with component count and rots as you add features.
- **`prefers-color-scheme` reads the OS directly.** No permission, no JS, every modern browser. `matchMedia('(prefers-color-scheme: dark)')` is only needed if you want runtime *reaction* to the user flipping appearance mid-visit (add a `change` listener) — the static `<picture>`/CSS path doesn't.
- **Page + screenshots share one signal.** Both keyed on the same media query → a dark-Mac visitor gets a dark page *and* dark screenshots, automatically consistent.

### Common mistakes
- **Forgetting `color-scheme`** → form controls and scrollbars stay light. Symptom: a perfect dark page with a jarring white scrollbar.
- **Diverging the shared base stylesheet** → put the dark block in the per-app override file, loaded *after* the base, so a multi-app design system isn't forked. Equal-specificity `:root` in the later file wins when the media query matches.
- **Pure `#fff`/`#000` in the dark palette** → use near-white (`#ECEEF1`) and near-black (`#14161A`); pure values vibrate and crush shadows.
- **Reading `img.src` in screenshot-swapping JS** → always `currentSrc`. (See Step 3.)
- **Translucent `rgba(0,0,0,…)` "ghost" tokens** carried into dark mode → invert to `rgba(255,255,255,…)` or they vanish.
- **No render check** → `prefers-color-scheme` can't be eyeballed without a dark OS/browser. Verify in Safari (Appearance → Dark) or `chrome --force-dark-mode` equivalents; brace-balance alone proves nothing about appearance.

### Pairs well with
- **#39 design-tokens** — this pattern is the dividend of having done tokens properly.
- **#42 native `<dialog>` lightbox** — the `currentSrc` fix lives in that lightbox's open handler.
- **#41 web hero floating icons** — decorative `aria-hidden` icons usually use tokens already, so they re-theme for free.
