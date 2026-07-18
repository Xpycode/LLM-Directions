<!--
TRIGGERS: design system, design tokens, palette, accent color, color ramp, looks generic, LLM-like UI, AI-looking app, dark mode, light mode, appearance, empty state, corner radius, spacing scale, elevation, shadow, motion, animation timing, banned patterns, distinctive UI
PHASE: implementation, UI review
LOAD: full
-->

# 42 — House Design System (Xpycode)

> **For the model reading this: authoritative for UI surface decisions.** Use only tokens defined
> through the app's `Theme` (structured as below). No ad-hoc hex, ad-hoc spacing, or new radii —
> if a token is missing, **ask, don't invent**. Read **§8 Banned Patterns** before writing any
> view; it overrides your defaults.
>
> Origin: a screenshot critique of DiskVerdict, Conjoyn, Penumbra, CropBatch and Magpie
> (2026-07-18) diagnosing the "generated Mac app" look. Goal: no app reads as AI-made, and no two
> of ours read as the same app.

## Scope — one home per concern

| Concern | Home |
|---|---|
| Shell structure (HSplitView, titlebar, toolbar style) | cookbook §0 + `cookbook/00-app-shell.md`; audited by `shell-check` |
| Appearance mechanism (picker, dynamic colors) | `00-app-shell.md` §2 + cookbook #113 |
| Tokens, type, spacing, radii, motion, banned patterns | **this doc** |
| Per-app identity (palette source, accent, signature element) | the app repo's `DESIGN.md` (§1 brief) |
| The audit | `/check design` |

**AppCitizenshipKit note:** the shared Feedback / Tip Jar / About screens must consume the *host
app's* Theme tokens. Five identical kit screens would undo the per-app identity this doc exists for.

## 0. Appearance standard (2026-07-18)

**Dark is the house default; light is the user's choice.** Every app ships both.

- First launch = dark. In-app **Light / Dark / Match System** picker via
  `NSApplication.shared.appearance` — not `.preferredColorScheme` (its `nil` can't revert a forced
  window; cookbook #113).
- Both ramps are **hand-picked, never an algorithmic flip** — warmth must survive inversion.
- Token names are **roles**, not lightness values: `neutral-0` = app background … `neutral-900` =
  highest-emphasis text. Values swap per appearance; call sites never change.
- Implementation home is the app's `Theme` struct, each token backed by an asset-catalog color set
  ("Any, Dark") or an `NSColor(name:dynamicProvider:)`.
- **System semantic colors are banned for chrome** (`windowBackgroundColor`,
  `controlBackgroundColor`, bare `Color.primary` backgrounds): they adapt for free but have no
  temperature — the statistical-average Mac look. Accepted cost: the Theme must carry appearance
  adaptation and Increase Contrast itself — test both appearances when touching chrome.

## 1. Per-App Brief — the anti-sameness contract

Copy into the app repo as `DESIGN.md`; fill **before any UI is written**:

```
App name:            <e.g. DiskVerdict>
One-line purpose:    <what it does, plainly>
Mood (3 words):      <e.g. instrument, warm, precise>
Palette source:      <a CONCRETE thing — a film stock, a photo, a material, the domain.
                      NOT "system orange nudged". e.g. "warm off-white paper + oxidised copper">
Accent hue:          <ONE accent, derived from the source above>
Distinctive element: <the ONE thing allowed to be weird for this app — instrument-gauge charts,
                      tabular mono everywhere, a custom-drawn timeline…>
Reference apps:      <2-3 real apps whose restraint to match — Panic, Flexibits, Rogue Amoeba…
                      NOT other AI-made apps>
```

**Rules:**
- Every app differs from every other of ours in at least **accent hue AND distinctive element**.
  Concrete case: orange is *Penumbra's*. Reused in Conjoyn it reads as off / too much — Conjoyn
  needs its own accent from its own palette source.
- The human picks palette source + distinctive element (§10). The model never invents them.

## 2. Color

Ramps, not single values; reference by token name; never inline a hex outside `Theme`.
The neutral ramp carries the whole UI; the accent is scarce (§8).

**Example ramps** *(illustrative — each app hand-picks its own pair from its palette source; this
pair is the warm-gray direction)*:

```
role         light      dark       use
neutral-0    #FBF9F6    #1B1814    app background
neutral-50   #F4F1EC    #23201B    raised surface / cards
neutral-100  #E9E4DB    #2E2A23    hairlines, dividers, inset wells
neutral-200  #D8D1C4    #3D382F    disabled fills, track backgrounds
neutral-400  #9A9184    #8A8172    secondary text, icon default
neutral-600  #5E574C    #C9C1B2    primary text
neutral-900  #2A251E    #EFEAE0    headings, high-emphasis text
```

**Accent — ONE per app**, derived from the brief's palette source:
```
accent        the single action color        accent-hover  +8% luminance
accent-muted  ~15% alpha, subtle tints ONLY
```
If the accent feels "too much", the fix is usually **frequency, not hue** — count the
accent-colored elements on screen before swapping colors (§8: exactly one per screen).

**Semantic (status only):** `success` / `warning` / `danger` appear **only on status** (verify
passed, disk healthy, job failed) — never to decorate layout or chrome.

## 3. Typography

Type is the fastest differentiator. Vocabulary + fundamentals → `40_typography.md`.

```
Display / H1   <per-app face>   28/32   w700   tracking -0.02em
H2             SF Pro           20/26   w600   tracking -0.01em
H3 / label     SF Pro           13/18   w600   tracking  0.02em   UPPERCASE
Body           SF Pro Text      13/18   w400
Caption        SF Pro Text      11/15   w400   neutral-400
Numeric        SF Mono / tabular — ALL metrics, sizes, timecodes, counts
```

- **Numbers are always tabular** (`.monospacedDigit()` or a mono face) — sizes, durations,
  percentages must not shift width as they tick.
- Pick a **Display face** per app where the mood fits (a grotesk, a mono, a humanist sans). If
  staying on SF, earn distinction through weight jumps + tracking — never default weight (§8).

## 4. Spacing & Layout

One scale, no off-scale values: `2 4 8 12 16 24 32 48 64`

- Content-forward, not chrome-forward: the subject (crop, waveform, disk chart, file list) gets
  the visual weight; toolbars and panels recede.
- Prefer a real content column with generous gutters over full-bleed centered blocks.

## 5. Radius & Elevation

Radius varies **by hierarchy** — one global radius is a tell (§8):

```
radius-sm 4  inputs, chips, small controls     radius-lg  14   sheets, prominent surfaces, primary CTA
radius-md 8  cards, panels                     radius-pill 999  genuine pills only (a tag) — never nav
```

Elevation = low-contrast shadow (tinted toward the ramp's temperature) + a `neutral-100` hairline:
```
elev-0  flat + hairline      elev-1  0 1 2 @ 6% + hairline      elev-2  0 4 12 @ 10% (sheets, popovers)
```

## 6. Motion

Restrained and physical; no decorative animation; respect Reduce Motion.

```
fast 120ms ease-out (hover, toggle, selection)   base 200ms ease-in-out (panel/detail)
spring stiffness 220 damping 26 (drag, reorder, sheet present)
```

## 7. Iconography

- SF Symbols are fine for controls (toolbar, inline actions); match symbol weight to adjacent text.
- **A big centered SF Symbol as a screen's personality is banned** (§8). The signature icon /
  empty state / app identity gets a custom-drawn or hand-selected treatment — that's the human 20%.

## 8. Banned Patterns — the statistical center of "generated Mac app"

These override your priors. Avoiding them is the point of this file.

- **No centered big-SF-Symbol empty states** (giant glyph + bold title + gray subtitle + accent
  button). Instead: inline hints, ghosted sample content, a first-run affordance, or a compact
  top-anchored prompt. If a view can be non-empty by showing an example, make it non-empty.
- **Exactly one accent-colored action per screen.** Toggles, selected rows, progress, secondary
  buttons are neutral. If two things are accent-colored, one is wrong.
- **No single global corner radius** — vary by hierarchy (§5).
- **No segmented pill control parked top-center as primary navigation.** Sidebar, real toolbar, or
  inline tabs; a segmented control only for a genuine small either/or, off-center.
- **No system semantic colors for backgrounds or chrome** (§0) — the app must have a temperature.
- **No default-weight SF Pro headings** — Display face or weight + tracking contrast (§3).
- **Numbers must be tabular**, never proportional (§3).
- **No stock "Import X to start" hero as the whole first screen** — give a real, small, usable
  affordance.

## 9. Self-critique

Run **`/check design`** after building or editing any screen, before calling UI "done" — the model
is much better at *spotting* these defaults on review than avoiding them during generation.

## 10. Division of Labor

- **Model:** layout, plumbing, token application, wiring, consistency enforcement, `/check design`.
- **Human:** palette source, the distinctive element, empty states, custom-drawn views, real
  iconography, micro-interactions, typographic finishing.

Do the 80%. Leave the 20% flagged for the human — don't paper over it with a default.

---
*Foundation lives here (master, read on demand). Apps carry only the filled §1 brief + Theme.*
