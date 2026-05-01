## Design Tokens — Typography, Spacing, Iconography, Radii

**Source:** `1-macOS/Penumbra/01_Project/Penumbra/` — the canonical reference implementation.
Specifically: `App/PenumbraApp.swift`, `Views/ContentView.swift`, `Views/ToolbarButtonStyles.swift`, `Utils/ThemeManager.swift`.

All numeric values below are **extracted from the live Penumbra codebase**, not invented. When Penumbra changes, this document changes. When another app disagrees with Penumbra, the other app is wrong.

**Use case:** App-wide visual consistency beyond color. Font scale, spacing scale, SF Symbol conventions, corner radii. Applies to all macOS apps using the App Shell Standard; CSS equivalents provided for web projects (`PDF2Calendar`, `X-STATUS` style apps).

**Prerequisite:** [00-app-shell.md](00-app-shell.md) — this file extends the `Theme` struct defined there.
**Narrow case:** [07-timecode-typography.md](07-timecode-typography.md) — SF Pro `.monospacedDigit()` for video timecode overrides the general body scale below.

### Penumbra's architecture — what makes it canonical

Penumbra is **SwiftUI-primary with surgical AppKit interop**. The discipline (`FCPToolbarButtonStyle`, `.hiddenTitleBar`, `.toolbarRole(.editor)`, `Theme(white: 0.10/0.15)`) is pure SwiftUI and transferable to any descendant app (Sigil, CropBatch, Mural, AutoRedact). AppKit drops in only where SwiftUI can't deliver frame-accurate or event-level control:

| File | Why AppKit |
|---|---|
| `KeyInputView.swift` | `NSEvent` monitors for JKL scrubbing (SwiftUI `.onKeyPress` is too coarse) |
| `ShortcutRecorder.swift` | Raw key-chord capture for user-customizable shortcuts |
| `PlayerViewController.swift` | `AVPlayerView` for frame-accurate video |
| `Views/MouseTrackingView.swift` | `NSTrackingArea` for sub-pixel hover |
| `Utils/View+SplitViewAutosave.swift` | `NSSplitView` autosave (SwiftUI `HSplitView` can't persist dividers natively) |

**Rule:** stay in SwiftUI. Drop to AppKit only when a concrete capability forces it (see the five files above). Don't use "Penumbra is AppKit-based" as an excuse to write an `NSViewController` you don't need.

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

**Values — derived from Penumbra/Sigil in-use sizes, base 13 × ratio 1.25:**

The ratio `1.25` (major third) is chosen because it snaps cleanly to the 8pt grid at the top of the scale (16, 24, 32) while still giving distinguishable small-end sizes. Tighter ratios (1.125) make captions indistinguishable from body; looser ratios (1.333+) break the grid and feel editorial rather than pro-tool.

```swift
extension Theme {
    enum Font {
        // Base — macOS system default (NSControl regular size)
        static let base: CGFloat = 13

        // Ratio (major third — fits macOS 8pt grid at large sizes)
        static let ratio: CGFloat = 1.25

        // Semantic sizes (base * ratio^n, rounded to grid-friendly values)
        static let caption: CGFloat = 11  // tooltip, metadata, timestamp strip
        static let body: CGFloat    = 13  // default — do not override in most views
        static let title3: CGFloat  = 16  // section header, info-strip emphasis
        static let title2: CGFloat  = 20  // pane header
        static let title1: CGFloat  = 24  // window title (when shown in custom strip)
        static let display: CGFloat = 32  // timecode hero, empty-state glyph label

        // Allowed weights — Penumbra's FCP-flavoured hierarchy.
        // Do NOT use .bold / .heavy / .black — they break the pro-tool aesthetic.
        // .ultraLight is allowed only for dimmed leading zeros (see 07-timecode-typography.md).
        enum Weight {
            static let hairline: SwiftUI.Font.Weight = .thin       // display-size only (≥24pt)
            static let subtle: SwiftUI.Font.Weight   = .light      // secondary TC, large captions
            static let normal: SwiftUI.Font.Weight   = .regular    // body default
            static let prominent: SwiftUI.Font.Weight = .medium    // toolbar buttons, active labels
            static let emphatic: SwiftUI.Font.Weight = .semibold   // destructive actions, strong emphasis
        }
    }
}
```

**Rule — thin weights are size-gated:** `.thin` and `.light` read as hairlines at small sizes (≤16pt) and fail WCAG contrast. Use `.thin` only at `title1` (24pt) or `display` (32pt). Below that, `.regular` is the floor.

**Anti-pattern flags to watch for:**
- `.font(.system(size: 14))` — unnamed size, now you have to grep to find all "14"s
- Using `.monospaced` design for anything that isn't code — [07-timecode-typography.md](07-timecode-typography.md) explains why
- More than 5–6 weights in active use — pick a subset (e.g. `.thin`, `.regular`, `.semibold`) and enforce it

---

### 2. Spacing Scale (8pt grid)

**Rule:** all spacing is a multiple of a base unit. Apple, Google, Atlassian, and Material all converge on 8pt (with 4pt as a half-step for dense UI). This is not dogma — it's what makes eyes read rhythm.

**Internal ≤ external rule:** padding *inside* an element must be less than or equal to the margin *around* it. Otherwise groups visually merge instead of separating. This is the single most-broken rule in ad-hoc layouts.

**Values — 8pt grid with 4pt half-step, grounded in `FCPToolbarButtonStyle` (horizontal 8, vertical 6, icon 16×16):**

```swift
extension Theme {
    enum Space {
        // General scale (8pt grid, 4pt half-step for tight controls)
        static let xxs: CGFloat = 2   // hairline — icon-to-label, separator insets
        static let xs: CGFloat  = 4   // tight — chip padding, compact row vertical
        static let sm: CGFloat  = 8   // default small — button horizontal padding
        static let md: CGFloat  = 16  // default — pane interior, card padding, icon size
        static let lg: CGFloat  = 24  // section — between cards, around groups
        static let xl: CGFloat  = 32  // window-level — sidebar padding, empty-state
        static let xxl: CGFloat = 48  // hero only — not used in dense pro-tool layouts

        // Off-grid tolerances (documented exceptions, grounded in Penumbra)
        static let buttonVertical: CGFloat = 6   // FCPToolbarButtonStyle:20 — tighter than 8, looser than 4
        static let dividerInlinePadding: CGFloat = 4  // ContentView:257 — inline divider horizontal padding

        // ─── Window ─────────────────────────────────────────────────
        // PenumbraApp.swift:19 — canonical window minimum
        static let windowMinWidth: CGFloat  = 1400
        static let windowMinHeight: CGFloat = 800

        // ─── Vertical bars (ContentView.swift — actual Penumbra values) ─
        static let infoStripHeight: CGFloat  = 25   // ContentView:220 — deliberately 25, not 28
        static let controlsRowHeight: CGFloat = 50  // ContentView:319
        static let timelineHeight: CGFloat   = 50   // ContentView:333
        static let bottomPanelHeight: CGFloat = 250 // ContentView:368 (queue settings + queue)
        static let actionBarHeight: CGFloat  = 40   // ContentView:373
        static let inlineDividerHeight: CGFloat = 20 // ContentView:256

        // ─── Pane widths (HSplitView constraints from ContentView.swift) ──
        // Main content pane (video / primary workspace)
        static let mainPaneMinWidth: CGFloat = 650  // ContentView:302, :365

        // Right-side inspector (metadata, properties)
        static let inspectorMinWidth: CGFloat   = 220  // ContentView:305
        static let inspectorIdealWidth: CGFloat = 300
        static let inspectorMaxWidth: CGFloat   = 500

        // Settings / utility pane (narrower than inspector)
        static let settingsPaneMinWidth: CGFloat   = 220  // ContentView:361
        static let settingsPaneIdealWidth: CGFloat = 250
        static let settingsPaneMaxWidth: CGFloat   = 400

        // ─── Icon canvas sizes (paired with SF Symbol scale) ────────
        static let iconSm: CGFloat = 12  // inline, status-strip glyphs
        static let iconMd: CGFloat = 16  // toolbar default — CONFIRMED ContentView:230 (FCPToolbarButtonStyle frame)
        static let iconLg: CGFloat = 24  // section headers, sidebar section icons
        static let iconXl: CGFloat = 48  // empty-state hero glyph
    }
}
```

**Internal ≤ external check on these values:** card padding (`md = 16`) ≤ gap between cards (`lg = 24`) ✓. Toolbar icon (`iconMd = 16`) + top/bottom `buttonVertical = 6` × 2 = 28pt total button height, fits within a stock 38–40pt toolbar row ✓.

**Note on `infoStripHeight = 25`:** This is deliberately *off* the 8pt grid. Penumbra chose 25 so that the InfoStrip reads as a *ribbon* rather than a full toolbar row — tight enough to feel like metadata, loose enough to stay readable. If you're tempted to "fix" it to 24 or 32, read `InfoStripView.swift` first and verify the content still fits.

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

**Values — tight radii, anti-Tahoe. `FCPToolbarButtonStyle` already uses 4, so `sm = 4` is empirically confirmed.**

```swift
extension Theme {
    enum Radius {
        static let none: CGFloat = 0
        static let sm: CGFloat   = 4   // CONFIRMED — FCPToolbarButtonStyle, chips, inline tags
        static let md: CGFloat   = 6   // small cards, info strips, popovers
        static let lg: CGFloat   = 8   // panels, sheets, main content cards
        static let xl: CGFloat   = 12  // modals (upper bound — never go round/capsule)
    }
}
```

**Rule — nested surfaces decrement radii:** a panel at `.lg` (8) contains a card at `.md` (6) which contains a chip at `.sm` (4). Never nest a larger radius inside a smaller one — the inner element appears to burst out of its container.

**Explicit non-rule:** no value above 12. Tahoe's round capsule chrome (radius = height/2) is rejected by the App Shell Standard. If a surface "feels like it wants" to be a capsule, reconsider the component — it's probably an `FCPToolbarButtonStyle` in disguise.

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
