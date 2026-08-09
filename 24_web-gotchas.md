<!--
TRIGGERS: web, website, HTML, CSS, JavaScript, responsive, layout broken, styling issue, frontend
PHASE: implementation
LOAD: full
-->

# Web Development Gotchas

**Common web issues and how to fix them.**

*The problems you'll encounter when building websites with AI assistance.*

---

## The Big Five Web Issues

### 1. CSS Specificity Wars

**Symptom:** Your styles don't apply, or wrong styles win.

**Why it happens:** CSS has specificity rules. More specific selectors override less specific ones.

```css
/* This loses (less specific) */
.button { color: blue; }

/* This wins (more specific) */
div.container .button { color: red; }

/* This always wins (avoid!) */
.button { color: green !important; }
```

**What to tell Claude:**
```
The button color isn't changing. Check CSS specificity.
Don't use !important - fix the specificity properly.
```

**Prevention:** Use consistent, simple selectors. Avoid deep nesting.

---

### 2. Flexbox/Grid Not Behaving

**Symptom:** Elements aren't aligning, layout breaks on resize.

**Common causes:**
- Missing `display: flex` or `display: grid` on parent
- Forgetting `flex-wrap: wrap` for responsive
- Using `width: 100%` when you need `flex: 1`

**What to tell Claude:**
```
This layout should be [describe desired layout].
Currently it [describe what's wrong].
Use flexbox/grid - show me the container AND children styles.
```

**Quick fixes:**
```css
/* Center anything */
.container {
  display: flex;
  justify-content: center;
  align-items: center;
}

/* Equal columns */
.container {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
}
```

---

### 3. Responsive Breakage

**Symptom:** Looks good on desktop, broken on mobile (or vice versa).

**Common causes:**
- Fixed pixel widths instead of relative units
- Missing viewport meta tag
- Not testing at different sizes

**Required in HTML head:**
```html
<meta name="viewport" content="width=device-width, initial-scale=1">
```

**What to tell Claude:**
```
This needs to work on mobile and desktop.
Use relative units (rem, %, vw) not fixed pixels.
Add media queries for breakpoints.
Test at 375px, 768px, and 1200px widths.
```

**Mobile-first pattern:**
```css
/* Base styles (mobile) */
.container { padding: 1rem; }

/* Tablet and up */
@media (min-width: 768px) {
  .container { padding: 2rem; }
}

/* Desktop */
@media (min-width: 1200px) {
  .container { max-width: 1200px; margin: 0 auto; }
}
```

---

### 4. Z-Index Chaos

**Symptom:** Modal appears behind other elements, dropdowns hidden.

**Why it happens:** z-index only works on positioned elements, and creates "stacking contexts."

**What to tell Claude:**
```
The modal should appear above everything.
Check that it has position: fixed/absolute/relative.
What z-index values are other elements using?
```

**Pattern for z-index:**
```css
:root {
  --z-dropdown: 100;
  --z-modal: 200;
  --z-tooltip: 300;
  --z-toast: 400;
}

.modal {
  position: fixed;
  z-index: var(--z-modal);
}
```

---

### 5. JavaScript Not Running

**Symptom:** Click handlers don't work, dynamic content doesn't appear.

**Common causes:**
- Script loaded before DOM exists
- Script error stopping execution
- Wrong event listener setup

**What to tell Claude:**
```
The button click isn't doing anything.
Check the browser console for errors.
Is the script loading after the DOM?
```

**Fix: Load script properly:**
```html
<!-- At end of body (recommended) -->
<body>
  ...content...
  <script src="app.js"></script>
</body>

<!-- Or with defer -->
<head>
  <script src="app.js" defer></script>
</head>
```

**Fix: Wait for DOM:**
```javascript
document.addEventListener('DOMContentLoaded', () => {
  // Your code here - DOM is ready
});
```

---

## More Common Issues

### Form Submission Refreshes Page

**Problem:** Form submits, page reloads, data lost.

**Fix:**
```javascript
form.addEventListener('submit', (e) => {
  e.preventDefault(); // Stop the reload
  // Handle form data here
});
```

### Images Not Loading

**Checklist:**
- [ ] Path is correct (relative vs absolute)
- [ ] File extension matches actual file
- [ ] File exists in the right location
- [ ] No typos in filename (case-sensitive on servers)

### CORS Errors

**Symptom:** "Access-Control-Allow-Origin" error in console.

**What it means:** Browser blocking request to different domain.

**What to tell Claude:**
```
Getting CORS error when fetching from [API].
Is this a backend issue or do I need a proxy?
```

### Content Flashes/Jumps on Load

**Causes:**
- CSS loading after content
- Fonts loading late (FOUT/FOIT)
- Images without dimensions

**Prevention:**
```html
<!-- Always specify image dimensions -->
<img src="photo.jpg" width="800" height="600" alt="...">
```

```css
/* Reserve space for images */
.image-container {
  aspect-ratio: 16/9;
}
```

### requestAnimationFrame Stops When the Window Is Hidden

**Symptom:** A long-running loop (video capture, export, countdown) works while you watch it,
but hangs forever if the window is minimized or another app covers it.

**What it means:** Every engine (Chrome, WKWebView, WebView2, WebKitGTK) throttles or fully
suspends `requestAnimationFrame` for hidden/occluded windows. If the loop's *completion check*
lives inside the rAF callback, nothing ever finishes. Desktop webviews (Tauri/Electron) are the
worst case — users routinely minimize during a long export.

**Fix:** Drive time-based work off `setInterval`/`setTimeout` + `performance.now()`; timers are
throttled (≈1 Hz) but keep firing. Reserve rAF for purely visual updates that may pause.
(Found: TestPatternGenerator 2026-07-03 — in-browser video export hung when minimized.)

### Resizing a Canvas Kills a Live Capture/Recording

**Symptom:** Corrupted or mixed-resolution frames in a `MediaRecorder` +
`canvas.captureStream()` recording; sometimes a frozen track.

**What it means:** Setting `canvas.width`/`height` **resets the bitmap** (HTML spec) under the
live capture stream. Any control that can trigger a resize or repaint mid-recording races the
recorder.

**Fix:** Disable *every* control that can touch the canvas (size, pattern, params, overlays)
for the duration of the capture, and wrap the whole export in `try/finally` so the UI always
unlocks. (Found: TestPatternGenerator 2026-07-03.)

---

## Quick Diagnostic Questions

| Symptom | Ask Claude |
|---------|-----------|
| Styles not applying | "Check CSS specificity and selector accuracy" |
| Layout broken | "Show me the flexbox/grid container setup" |
| Works on desktop only | "Are we using responsive units and media queries?" |
| Click does nothing | "Check browser console for JavaScript errors" |
| Content hidden | "Check z-index and overflow properties" |

---

## Browser DevTools Checks

Tell Claude to check:

```
Open browser DevTools (F12) and:
1. Console tab - any red errors?
2. Elements tab - is the element actually there?
3. Styles panel - are styles being applied/overridden?
4. Network tab - are all resources loading?
```

---

## Prevention Rules for CLAUDE.md

```markdown
## Web Development Rules
- Mobile-first: base styles for mobile, media queries for larger
- Use relative units (rem, %, vw/vh) not fixed px for layout
- Always include viewport meta tag
- Test at 375px, 768px, 1200px minimum
- Keep z-index organized with CSS variables
- Scripts at end of body or with defer
- Check browser console before saying "it works"
```

---

*Web development has many moving parts. When something breaks, check the browser console first.*

## CSS custom properties: `var()` resolves where DECLARED, not where used

A custom property whose value contains `var()` (or `color-mix(… var(--x) …)`) substitutes those
inner `var()`s **on the element where the property is declared** — not on the element that finally
uses it. So `:root { --plate: color-mix(in srgb, var(--card) 75%, var(--line)) }` bakes in
`:root`'s card/line forever; a descendant override like `.sheet { --card: … }` changes nothing.
**Fix:** put the `color-mix()` directly in the `background:` declaration at the usage site — there
the `var()`s resolve against the element's inherited values, so scoped token overrides work.
(Found 2026-07-13 deriving the App-Websites screenshot-plate color per theme variant.)

**Related cascade rule that pays rent:** a token set on a *closer ancestor* (`.sheet { --accent }`,
`.site-header { --accent }`) always beats the same token on `:root` — regardless of which
stylesheet loads last. That's the whole App-Websites variant mechanism: one byte-identical shared
stylesheet, per-site/per-surface token overrides by inheritance distance, zero `!important`.

## Two design generations sharing a stylesheet: class-name collisions leak OLD properties

When a redesign reuses a class name (`.featured`, `.shot`), the new rules only override properties
they *mention* — anything the legacy block set and the new block doesn't (a `max-width`, a
`border-radius`, a `background`) silently survives and corrupts the new layout. Found twice on one
page (App-Websites portal, 2026-07-13): a legacy `max-width: 1080px` capped the new carousel, and
a vestigial `class="shot"` dressed datasheet screenshots in the old marketing card chrome.
**Rule:** when porting a page onto new CSS, grep the OLD stylesheet for every class the new markup
keeps — either delete the dead legacy block or rename the new component.

## `aspect-ratio` on a FLEX child loses to the default `stretch` — and it reads as an image bug

A child of a flex row is stretched to the line's height by default (`align-items` initial value is
`normal`, behaving as `stretch`). That stretch wins over `aspect-ratio`, so the box silently renders
at whatever height the *sibling content* dictates. Declaring `aspect-[2/3]` (or `aspect-ratio: 2/3`)
does not protect you.

**Flex-specific — grid does not do this.** Measured side by side (WebKit/Safari 2026-08-09), with an
`aspect-ratio: 2/3; width: 64px` box next to a 300px-tall sibling:

| Container | `align-self` | Result | Ratio held? |
|---|---|---|---|
| `display:flex` | default | **64×300** | ✗ 0.213 |
| `display:flex` | `start` | 64×96 | ✓ 0.667 |
| `display:grid` (same row track) | default | 64×96 | ✓ 0.667 |
| `display:grid` (same row track) | `start` | 64×96 | ✓ 0.667 |

So "flex and grid both default to stretch, therefore both break aspect-ratio" is the intuitive
guess and it is **wrong** — verify per container type rather than reasoning from the shared default.
Only measured in WebKit here; re-measure before relying on the grid row cross-browser.

The reason this burns time is the **symptom points at the wrong layer**. Put `object-fit: cover` on
an image inside that box — the normal, correct pairing — and cover does exactly its job: fill the
box, crop the overflow. You see a cropped photo and start investigating the image, the CDN, the
source dimensions, `object-position`. Nothing there is wrong. The box is.

It also hides on desktop and appears on mobile, which invites a "responsive" theory: the taller the
text column beside it, the more the frame is stretched, and text is tallest when it wraps on a
narrow viewport. Same bug at every width — just proportional to the neighbour's height.

**Diagnose by measuring the box, never by looking at the image:**
```js
const r = frame.getBoundingClientRect();
r.width / r.height                       // vs. the ratio you declared
Math.abs(r.height - (row.height - padY)) // ~0 ⇒ it's being stretched, that's the tell
getComputedStyle(frame.parentElement).alignItems  // 'normal' == stretch
```

**Fix:** `align-self: start` on the child (Tailwind `self-start`), or `align-items: flex-start` on
the container if every child should keep its own height. Keep `object-fit: cover` — once the box is
the right shape, cover is what you wanted. Reach for `contain` only if letterboxing is acceptable.

**Rule:** any element that declares an `aspect-ratio` *and* is a flex child needs an explicit
cross-axis alignment. The ratio is a wish; the parent's alignment is the law.

(Found 2026-08-09 on KinoBerlin's featured-film banner, reported from a phone: the poster frame
measured 64×200 — ratio 0.319 — against the declared 0.667, because the wrapped title/tagline/credit
made the row 200px tall. One `self-start` restored 64×96 mobile / 112×168 desktop.)
