## Design Tokens — Typography, Spacing, Iconography, Radii

**Source:** `1-macOS/Penumbra/` (`Theme` struct extension)
**Use case:** App-wide visual consistency beyond color. Font scale, spacing scale, SF Symbol conventions, corner radii. Applies to all macOS apps using the App Shell Standard; CSS equivalents provided for web projects (`PDF2Calendar`, `X-STATUS` style apps).

**Prerequisite:** [00-app-shell.md](00-app-shell.md) — this file extends the `Theme` struct defined there.
**Narrow case:** [07-timecode-typography.md](07-timecode-typography.md) — SF Pro `.monospacedDigit()` for video timecode overrides the general body scale below.

---

### Why tokens, not raw values

A magic number like `padding: 16` spreads across the codebase and ossifies. A token like `Theme.Space.md` can be renamed in one place, compared against `Theme.Space.lg`, and *read* by a future you. Every large UI toolkit (Apple HIG, Material, Atlassian, Fluent) converges on this.

**Rule of thumb:** if you type a number inside a `.padding()`, `.font(.system(size:))`, or `.cornerRadius()` and it isn't a one-off asymmetry, it belongs in `Theme`.

---

### 1. Typography Scale

**Principle — semantic names, not pixel values.** Name the *role* (`body`, `caption`, `title`), not the size. This lets you retune the scale without editing every call site.

**macOS convention:** prefer SwiftUI's built-in `Font.title`, `.body`, `.caption` for anything that respects Dynamic Type. Override to fixed sizes only when the design demands it (dense pro-tool UIs, timecode displays, toolbar labels).

**Web convention:** use `clamp(min, preferred, max)` fluid typography so the scale breathes across viewport widths without breakpoint churn. Minimum body size 16px (WCAG readability floor).

**Modular ratio choice:** pick *one* ratio and stick with it. Common choices:
- `1.125` (major second) — tight, dense UIs (pro tools, editors)
- `1.25` (major third) — balanced default, most apps
- `1.333` (perfect fourth) — editorial, content-heavy sites
- `1.5` (perfect fifth) — marketing pages, generous hierarchy

**TODO — fill in your values:** The scale below is a scaffold. Pick a base size, ratio, and weights that match your taste. Your existing apps use SF Pro heavily; the `Theme.Font` struct should reflect that. You are filling in 5–10 lines of opinionated design tokens here.

```swift
// TODO (you): choose your type scale. Suggested shape:
extension Theme {
    struct Font {
        // Base (matches SwiftUI .body default — don't fight the system)
        static let base: CGFloat = 13   // macOS default; web would use 16

        // Ratio — pick one and commit (1.125 / 1.25 / 1.333 / 1.5)
        static let ratio: CGFloat = ???

        // Semantic sizes — derive from base * ratio^n, or pick explicitly
        static let caption: CGFloat   = ???  // smallest readable (tooltip, metadata)
        static let body: CGFloat      = base
        static let title3: CGFloat    = ???  // section header
        static let title2: CGFloat    = ???  // pane header
        static let title1: CGFloat    = ???  // window title
        static let display: CGFloat   = ???  // hero / empty-state

        // Weights — which weights do you actually use? Penumbra uses .thin/.light/.regular
        // TODO: list weights here so designers don't reach for .black by accident
    }
}
```

**Anti-pattern flags to watch for:**
- `.font(.system(size: 14))` — unnamed size, now you have to grep to find all "14"s
- Using `.monospaced` design for anything that isn't code — [07-timecode-typography.md](07-timecode-typography.md) explains why
- More than 5–6 weights in active use — pick a subset (e.g. `.thin`, `.regular`, `.semibold`) and enforce it

---

### 2. Spacing Scale (8pt grid)

**Rule:** all spacing is a multiple of a base unit. Apple, Google, Atlassian, and Material all converge on 8pt (with 4pt as a half-step for dense UI). This is not dogma — it's what makes eyes read rhythm.

**Internal ≤ external rule:** padding *inside* an element must be less than or equal to the margin *around* it. Otherwise groups visually merge instead of separating. This is the single most-broken rule in ad-hoc layouts.

**TODO — fill in your values:** Most apps only need 5–7 spacing tokens. More than that and the system stops being a system.

```swift
extension Theme {
    struct Space {
        // TODO (you): pick your scale. Common shape (8pt grid with 4pt half-step):
        static let xxs: CGFloat = 2   // hairline — icon-to-label, inline adjustments
        static let xs: CGFloat  = 4   // tight — chip padding, compact rows
        static let sm: CGFloat  = 8   // default small — button padding
        static let md: CGFloat  = 16  // default — pane padding, card interior
        static let lg: CGFloat  = 24  // section spacing — between cards, around groups
        static let xl: CGFloat  = 32  // window-level — sidebar padding, empty state
        static let xxl: CGFloat = 48  // hero / marketing only

        // Pane-specific (macOS — tune to your layouts)
        static let toolbarHeight: CGFloat  = ???
        static let infoStripHeight: CGFloat = ???
        static let sidebarMinWidth: CGFloat = ???
    }
}
```

**Usage examples:**
```swift
// Good — semantic
.padding(Theme.Space.md)
HSplitView { ... }.padding(.horizontal, Theme.Space.lg)

// Bad — magic numbers
.padding(16)           // is this "md"? or a one-off?
.padding(.leading, 14) // off-grid, breaks rhythm
```

---

### 3. SF Symbols — Weight & Scale Conventions

SF Symbols ships in **9 weights** (ultralight → black) and **3 scales** (small/medium/large). The weight of your symbol should match the weight of the text next to it; the scale controls relative size without changing stroke thickness.

**App Shell Standard conventions:**

| Context | Weight | Scale | Why |
|---------|--------|-------|-----|
| Toolbar button (`FCPToolbarButtonStyle`) | `.medium` | `.medium` | Default — matches toolbar label weight |
| Sidebar row icon | `.regular` | `.small` | Recedes behind label |
| Info strip status | `.semibold` | `.small` | Pops out of dense bar |
| Large empty-state glyph | `.thin` | `.large` | Generous, inviting |
| Destructive action (trash, delete) | `.semibold` | `.medium` | Signal weight = action weight |

**Rule:** if the icon sits next to text, match `font(...)` size and weight so baselines align. SF Symbols are designed to inherit font attributes — use that instead of fighting it.

```swift
// Good — symbol inherits from the font context
Label("Export", systemImage: "square.and.arrow.up")
    .font(.system(size: Theme.Font.body, weight: .medium))

// Avoid — decoupled sizing drifts from the label
Image(systemName: "square.and.arrow.up")
    .font(.system(size: 14))   // magic number, misaligned
```

**Do not use SF Symbols in:** app icons, logos, trademark-adjacent marks. Apple's license forbids it.

---

### 4. Corner Radii

Tiny surface, big consistency win. Pick a handful of radii and stick to them.

**TODO — fill in your values:**

```swift
extension Theme {
    struct Radius {
        static let none: CGFloat  = 0
        static let sm: CGFloat    = ???  // chips, inline tags (4?)
        static let md: CGFloat    = ???  // buttons, small cards (6–8?)
        static let lg: CGFloat    = ???  // panels, sheets (10–12?)
        static let xl: CGFloat    = ???  // hero cards, modals (16?)
    }
}
```

**Rule:** nested surfaces use smaller radii than their containers. A card at `.lg` contains a chip at `.sm`. Never the reverse — it looks like the inner element is bursting out of its container.

---

### 5. Web Translation (for `PDF2Calendar`, `X-STATUS`, future web projects)

The same tokens expressed as CSS custom properties. Keeps cross-project vocabulary consistent.

```css
:root {
    /* Typography — fluid with clamp() */
    --font-base: clamp(1rem, 0.95rem + 0.25vw, 1.125rem);  /* 16–18px */
    --font-ratio: 1.25;  /* same ratio as Swift side */

    --font-caption: clamp(0.75rem, 0.7rem + 0.2vw, 0.875rem);
    --font-body:    var(--font-base);
    --font-title-3: clamp(1.125rem, 1rem + 0.5vw, 1.375rem);
    --font-title-2: clamp(1.375rem, 1.2rem + 0.7vw, 1.75rem);
    --font-title-1: clamp(1.75rem, 1.5rem + 1vw, 2.25rem);

    /* Spacing — same 8pt grid */
    --space-xxs: 0.125rem;  /* 2px  */
    --space-xs:  0.25rem;   /* 4px  */
    --space-sm:  0.5rem;    /* 8px  */
    --space-md:  1rem;      /* 16px */
    --space-lg:  1.5rem;    /* 24px */
    --space-xl:  2rem;      /* 32px */

    /* Radii */
    --radius-sm: 4px;
    --radius-md: 8px;
    --radius-lg: 12px;

    /* Line height — multiples of base grid unit, NOT of font size */
    --leading-tight:  1.2;  /* headings */
    --leading-normal: 1.5;  /* body — readable default */
    --leading-loose:  1.75; /* long-form reading */
}
```

**Web-specific rules:**
- Body line-height between 1.4 and 1.6 (web.dev Baseline recommendation)
- Minimum body 16px — smaller triggers iOS Safari zoom-on-focus and fails WCAG comfortable-read
- Use `rem` for sizing, never `px`, so users' browser font-size preferences still work

---

### 6. Migration Checklist (existing apps)

When retrofitting an app to these tokens:

- [ ] Extend `Theme` with `Font`, `Space`, `Radius`, `Icon` sub-structs
- [ ] Grep the project for numeric literals in `.padding(`, `.font(.system(size:`, `.cornerRadius(` — replace with tokens
- [ ] Audit SF Symbol usage: are weights matching adjacent text? Are scales consistent per context?
- [ ] Check "internal ≤ external" rule on any nested layout — if a card's padding ≥ the gap between cards, widen the gap
- [ ] Verify timecode displays still use [07-timecode-typography.md](07-timecode-typography.md) overrides, not the general body scale

---

### Key Rule

**Name the role, not the value.** `Theme.Space.md` not `16`. `Theme.Font.body` not `.system(size: 13)`. The token name is the contract; the number is an implementation detail you're free to retune.

---

### References

- [Apple HIG — SF Symbols](https://developer.apple.com/design/human-interface-guidelines/sf-symbols)
- [web.dev — Fluid typography with CSS clamp()](https://web.dev/articles/baseline-in-action-fluid-type)
- [Atlassian — Spacing tokens](https://atlassian.design/foundations/spacing)
- [Cieden — 8pt grid + internal ≤ external rule](https://cieden.com/book/sub-atomic/spacing/spacing-best-practices)
- [UX Collective — Typography in design systems](https://uxdesign.cc/mastering-typography-in-design-systems-with-semantic-tokens-and-responsive-scaling-6ccd598d9f21)

---
