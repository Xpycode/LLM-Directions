# 158 — Web: a last-loaded `:root` token file wins — override by specificity, not source order

**Tags:** web, css, custom-properties, css-variables, :root, cascade, source-order, specificity, prefers-color-scheme, dark-mode, design-tokens, --ink, --accent, datasheet, light-only, inheritance-distance, dark-on-dark, contrast

**Extracted from:** App-Websites monorepo — the shared `datasheet.css` layer over Conjoyn / DiskVerdict (2026-07-10)

## The setup

A site loads **two** stylesheets that both define global design tokens on `:root`:

```html
<link rel="stylesheet" href="/css/site.css">        <!-- base tokens: --ink, --accent, --surface -->
<link rel="stylesheet" href="/css/conjoyn.css">     <!-- per-site: brand accent + @media dark remap -->
<link rel="stylesheet" href="/css/datasheet.css">   <!-- shared "printed sheet" layer, linked LAST -->
```

`datasheet.css` is linked **last on purpose** so its `:root { --accent: … }` wins — that's how the
shared layer sets defaults. The trap: because it's last *and* also targets `:root`, it silently wins
over **everything** earlier that targets `:root` — including a per-site dark-mode remap.

## The gotcha — `:root` vs `:root` is decided by source order, and media queries add no specificity

```css
/* conjoyn.css */
@media (prefers-color-scheme: dark) {
  :root { --ink: #ECEEF1; }   /* light ink for dark chrome */
}
/* datasheet.css — loaded AFTER conjoyn.css */
:root { --ink: #1A1A1E; }     /* dark ink for the always-light sheet */
```

Both rules are `:root` → **equal specificity (0,1,0)**. A `@media` wrapper adds **zero** specificity.
So in dark mode the winner is simply *whichever came later in the cascade* = `datasheet.css` →
`--ink` stays **dark**. Two failures fell out of this one mechanism:

- **Accent didn't take** — per-site `:root { --accent: #F0622A }` was defeated; the sheet showed the
  shared default terracotta.
- **Dark-on-dark chrome** — the dark block still applied the tokens `datasheet.css` *doesn't* redefine
  (`--header-surface`, `--surface` → dark backgrounds), but its light `--ink` lost → **dark ink on a
  dark header**: wordmark contrast **1.00**, invisible. (The control: a sibling page with no dark
  block rendered fine — its chrome stayed light.)

## The fix — out-specify `:root`, or delete the loser

You have two clean moves. **Never** reach for `!important` or reordering `<link>`s (both are
load-bearing here).

```css
/* FIX A — win by specificity, independent of source order.
   A class/element selector on the element that needs the token beats :root,
   so it wins no matter which file loads last. (This kept the accent per-site.) */
.sheet { --accent: #F0622A; }        /* .sheet (0,1,0 class) out-specifies :root */

/* FIX B — if the override shouldn't exist at all, remove it.
   The .sheet is a deliberately-light "printed datasheet", so the whole page
   should stay light: just delete the competing @media dark block. Leave a
   comment so nobody re-adds it. Light mode is byte-identical (block only ran
   in dark), so zero regression. */
/* (no @media prefers-color-scheme:dark here — light-only by design) */
```

**Rule of thumb:** *whoever owns the global `:root` tokens and loads last owns them.* To override a
token for one region, target that region with any selector more specific than `:root`
(`.sheet {…}` — "inheritance distance / specificity wins"), not source order. If the override is a
whole theme you don't actually want, remove it rather than refereeing the cascade.

## Diagnose it fast (no OS toggle needed)

```js
// Who actually won for a token?
getComputedStyle(document.documentElement).getPropertyValue('--ink').trim();
// Catch dark-on-dark: compute WCAG contrast of text vs its background.
// A wordmark reading ~1.00 means same-lightness → invisible.
```

If your browser is already in dark mode, just serve the files and probe. To force the opposite mode
faithfully, invert the media condition in a scratch copy (`dark`→`light`) — it preserves source order
and specificity, only flipping the trigger.

## Pairs with

- **#62** Web Auto Dark Theme — Remap Design Tokens, Not Components (the happy-path this is the
  failure-mode of; a second `:root`-owning file breaks its assumption).
- **#39** Design Tokens.
