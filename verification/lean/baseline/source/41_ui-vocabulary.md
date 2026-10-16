<!--
TRIGGERS: UI element, component name, what is this called, Apple UI, SwiftUI component, UIKit, web UI, HTML element, CSS, web component, website UI, frontend
PHASE: any
LOAD: on-request
-->

# UI Vocabulary Reference

A reference for discussing Apple-platform and web UI components with precision. Merges what
were previously two separate docs (`41_apple-ui.md`, `42_web-ui.md`) — the same concepts show
up under different names on each platform, so they're tabled together with a Platform column.

**For this project's UI rules** (no Tahoe sidebar, AppKit controls over SwiftUI controls, etc.),
see `47_project-ui-conventions.md` — that's project-specific policy, not vocabulary.

Platform column: **Apple** = macOS/iOS-specific term · **Web** = web-specific term · **Both** =
same concept, same or near-same name on both.

---

## Containers, Sheets & Overlays

| Term | Platform | Description |
|------|----------|--------------|
| Window | Apple | Fundamental content container: title bar, traffic lights, content area |
| Scene | Apple (iOS) | A single instance of the app's UI; an app can have multiple |
| Sheet / Modal / Dialog | Both | Modal view blocking parent interaction until dismissed. Apple: slides from top (macOS) or bottom (iOS). Web: centered overlay with dimmed backdrop/scrim |
| Popover | Both | Floating container anchored to its trigger element, dismisses on outside click |
| Alert | Apple | Modal dialog demanding attention — informational, warning, or destructive |
| Panel | Apple (macOS) | Floating auxiliary window that stays above regular windows without blocking interaction (Fonts panel, Colors panel) |
| Inspector | Apple | Panel/sidebar showing properties of the current selection — typically right sidebar (macOS) or sheet/popover (iOS) |
| Drawer | Both | Slide-in panel from a screen edge — nav menu, cart, filters, settings |
| Lightbox | Web | Modal specifically for images/media, often with prev/next navigation |
| Backdrop / Scrim | Web | The dimmed layer behind a modal that blocks the page |
| Flyout | Web | Submenu that appears to the side of a parent menu item |
| Toast / Snackbar | Both | Brief, auto-dismissing message (Apple calls this "Toast" informally, not a native control) |
| Banner / Alert Bar | Both | Temporary/persistent message bar, often full-width at the top |

```
Modal / Sheet / Dialog:                Popover:
         ┌──────────────────────┐         [Click me]
░░░░░░░░░│   Title          [X] │░░░           ↓
░░░░░░░░░├──────────────────────┤░░░       ┌────────────┐
░░░░░░░░░│   Content here       │░░░       │ content    │
░░░░░░░░░│   [Cancel] [Confirm] │░░░       └────────────┘
░░░░░░░░░└──────────────────────┘░░░
            ↑ backdrop/scrim (dimmed)
```

---

## Navigation

| Term | Platform | Description |
|------|----------|--------------|
| Navigation Bar | Apple (iOS) | Top bar with back button, title, trailing actions |
| Navbar | Web | Horizontal navigation, typically in the header. Fixed / sticky / static |
| Toolbar | Both | Bar of actions relevant to current content — top of window (macOS), bottom of screen (iOS) |
| Tab Bar / Tabs | Both | Persistent navigation between sections/panels. Apple: bottom of screen, app-wide. Web: horizontal, one panel visible at a time |
| Sidebar | Both | Column (usually left) for navigation or filtering; can collapse |
| Source List | Apple (macOS) | Sidebar variant with grouped hierarchical navigation and disclosure triangles (Finder, Mail) |
| Outline View | Apple | Hierarchical list with expandable/collapsible rows |
| Split View | Apple | Two or more content panes side by side — two-column (sidebar\|content) or three-column (sidebar\|list\|detail) |
| Hamburger Menu | Web | ☰ icon toggling a hidden nav menu, common on mobile |
| Mega Menu | Web | Large dropdown showing multiple columns of links, often with images |
| Breadcrumbs | Web | Trail showing location in site hierarchy: `Home > Products > Phones` |
| Pagination | Web | Navigation between pages of results |
| Infinite Scroll | Web | Auto-loads more content as the user scrolls |
| Skip Link | Web | Hidden link (visible on focus) to jump past navigation to main content — accessibility |
| Back to Top | Web | Button (often bottom-right) that scrolls back to page top |

```
Sidebar (both platforms):              Tabs / Tab View:
┌────────┬────────────────────┐        ┌─────┬─────┬─────┐
│ Nav    │                    │        │ Tab │ Tab │ Tab │ ← active differs
│ Link 1 │     Content        │        ├─────┴─────┴─────┴──────────┐
│ Link 2 │                    │        │   Tab content panel        │
└────────┴────────────────────┘        └─────────────────────────────┘
```

---

## Controls & Inputs

| Term | Platform | Description |
|------|----------|--------------|
| Button | Both | Tappable control triggering an action. Styles: primary/filled, secondary/borderless, destructive, cancel/neutral |
| Toggle / Switch | Both | Binary on/off control. iOS/Web: sliding switch `○──●`. macOS: checkbox `[✓]` |
| Slider / Range Input | Both | Selects a value from a continuous range: `Min ├────●────┤ Max` |
| Range Slider (dual handle) | Web | Selects a min/max range: `├──●━━●──┤` |
| Stepper | Both | Increment/decrement with +/− buttons: `[ − ]  42  [ + ]` |
| Picker / Select | Both | Selects from a list of options. Apple styles: wheel, segmented, menu, inline. Web: native `<select>`, custom dropdown |
| Combobox / Autocomplete | Web | Text input with a suggestions dropdown; user can type or select |
| Multi-select | Web | Choose multiple options — checkboxes, tags, or searchable list |
| Segmented Control | Both | Horizontal set of mutually exclusive options: `[ Day │ Week │ Month ]` |
| Text Field / Text Input | Both | Single-line text entry |
| Text Editor / Textarea | Both | Multi-line text input |
| Search Field | Both | Text field with search icon, clear button, optional scope bar |
| Checkbox | Both | Toggle one or more options on/off: `[✓] Option A` |
| Radio Button | Both | Select one option from a mutually exclusive group: `(●) Option A` |
| Date Picker | Both | Selects date/time. Apple styles: compact, inline, wheel, graphical |
| Time Picker | Web | Input for selecting time |
| Color Picker | Both | Selects a color |
| File Input / Upload | Web | Native file input, drag-and-drop zone, or click-to-upload area |
| OTP / Verification Code Input | Web | Segmented input for one-time passwords: `[4][8][2][9][ ][ ]` |
| Input Group | Web | Input combined with buttons/labels, e.g. a prefixed URL field |
| Floating Label | Web | Label inside the input that floats above on focus/fill |
| Password Reveal | Web | Eye icon toggling password visibility |
| Menu | Apple | List of actions/options shown on click/tap — pull-down (toolbar), pop-up (selection), context (right-click/long-press) |
| Dropdown | Web | Menu appearing below a trigger button |

---

## Feedback & Status

| Term | Platform | Description |
|------|----------|--------------|
| Label | Both | Static text displaying information |
| Badge | Both | Small indicator (usually a number) overlaid on an icon: `🔔³` |
| Activity Indicator / Spinner | Both | Animated icon showing ongoing activity/loading |
| Progress Bar / Ring | Both | Determinate `[████░░] 55%` or indeterminate (animated) progress |
| Skeleton / Shimmer | Web | Animated placeholder shape shown while content loads |
| Empty State | Web | Placeholder UI shown when there's no data, usually with a CTA |
| Pull to Refresh | Apple | Gesture reloading content by pulling down on a scroll view |
| Form Validation | Web | Visual feedback for input correctness — valid (green), invalid (red), warning (yellow) |

---

## Content Display

| Term | Platform | Description |
|------|----------|--------------|
| List / Table View | Both | Rows of content. Apple styles: plain, grouped, inset grouped. Web `Table`: sortable columns, selectable rows |
| Collection View / Grid | Both | Grid or flexible layout of items, more flexible than a list |
| Data Grid | Web | Advanced table — virtual scrolling, cell editing, column resizing |
| Card | Web | Contained content unit with image/title/text/actions and defined boundaries |
| Accordion | Web | Vertically stacked headers that expand/collapse to reveal content |
| Carousel | Web | Horizontally scrolling content with prev/next controls and indicators |
| Gallery | Web | Grid of images, often clickable to open a lightbox |
| Avatar | Web | Small image representing a user, often circular, or initials fallback |
| Chip / Tag / Pill | Web | Small pill-shaped element for labels, filters, or status |
| Split Button | Web | Button with a main action plus a dropdown for alternatives |
| Button Group | Web | Multiple related buttons visually joined together |
| Icon Button | Both | Button with only an icon, no text |
| FAB (Floating Action Button) | Web | Circular button floating above content, usually bottom-right, for the primary action |
| CTA (Call to Action) | Web | Prominent button/link urging user action — key conversion element |
| Step Indicator | Web | Shows progress through a multi-step process: `(1)──(2)──(●)──( )──( )` |

---

## Layout & Structure

| Term | Platform | Description |
|------|----------|--------------|
| Stack View | Apple | Arranges subviews horizontally (HStack) or vertically (VStack); auto-handles spacing/alignment |
| Scroll View | Apple | View whose content can exceed its frame; scrolls to reveal hidden content |
| Header / Footer | Web | Top section (logo, nav, actions) / bottom section (secondary nav, legal, contact) |
| Hero | Web | Large prominent banner at the top of a landing page — headline, subtext, CTA |
| Section | Web | Thematic content grouping, often full-width with a distinct background |
| Container | Web | Centered, max-width wrapper constraining content width for readability |
| Main Content Area | Web | The primary content region of the page |
| Grid | Both | Two-dimensional arrangement in rows and columns. Web: 12-column, CSS Grid auto-fit/auto-fill |
| Gutter | Web | Gap between grid columns or elements |
| Safe Area | Apple | Portion of the screen not obscured by system UI (notch, home indicator, status bar) |
| Margins | Apple | Padding from container edge; system provides "readable content" margins for text |
| Spacing | Apple | Distance between elements — Apple uses an 8pt grid baseline |
| Alignment | Apple | How items line up: leading, center, trailing, top, bottom, baseline |
| Padding | Web | Space inside an element, between content and border |
| Margin | Web | Space outside an element, between it and adjacent elements |
| Gap | Web | Space between flex/grid items (CSS `gap`) |
| Whitespace | Web | Empty space used intentionally for clarity and visual hierarchy |
| Z-index | Web | Stacking order of overlapping elements — higher values render on top |
| Corner Radius | Apple | Rounded corners; Apple uses continuous (squircle) curves. Common: 10pt (buttons), 12pt (cards), 20pt+ (sheets) |

---

## Media

| Term | Platform | Description |
|------|----------|--------------|
| Image | Both | Static visual content; consider lazy loading on web |
| Video Player | Both | Embedded video with play/pause/scrub/volume/fullscreen controls |
| Audio Player | Both | Controls for audio playback |
| Embed / iFrame | Web | External content embedded in the page (maps, videos, widgets) |
| Figure / Caption | Web | Image/media with descriptive text below |

---

## Gestures (Apple)

| Gesture | Action |
|---------|--------|
| Tap | Primary action |
| Double-tap | Secondary action, zoom |
| Long press | Context menu, drag initiation |
| Swipe | Delete, actions, navigation |
| Pinch | Zoom in/out |
| Rotate | Rotation (maps, images) |
| Pan / Drag | Move content or objects |
| Edge swipe | Back navigation (iOS) |

---

## Visual Styling & Adaptive Layout

| Term | Platform | Description |
|------|----------|--------------|
| Materials | Apple | Translucent blurred backgrounds — ultra-thin, thin, regular, thick, chrome |
| Vibrancy | Apple | Text/icons blending with the blurred material behind them for readability |
| SF Symbols | Apple | Apple's vector icon system; scales with text, supports weights/variants |
| Accent / Tint Color | Apple | The app's primary interactive color — buttons, links, selections |
| Semantic Colors | Apple | Colors that adapt to light/dark mode and accessibility settings (label, systemBackground, …) |
| Size Classes | Apple | Compact/regular width or height — drives adaptive layout |
| Breakpoints | Web | Viewport widths where layout changes — mobile <640px, tablet 640-1024px, desktop >1024px |
| Media Query | Web | CSS rules applying at specific viewport sizes |
| Mobile-first | Web | Design for mobile first, add complexity for larger screens |
| Fluid / Fixed Layout | Web | Stretches with viewport width, vs. a set pixel width |
| Responsive Images | Web | Images that load different sizes based on screen/device |
| Aspect Ratio | Both | Proportional width:height relationship — 16:9 (video), 4:3, 1:1 |

---

## Accessibility

| Term | Platform | Description |
|------|----------|--------------|
| Focus Ring / Outline | Web | Visual indicator of which element has keyboard focus |
| ARIA Labels | Web | Attributes providing accessible names/descriptions for screen readers |
| Alt Text | Web | Descriptive text for images, read by screen readers |
| Landmark Regions | Web | Semantic regions (header, main, nav, aside, footer) aiding screen-reader navigation |
| Focus Trap | Web | Keeping keyboard focus within a modal/component until dismissed |
| Live Region | Web | Area that announces dynamic content changes to screen readers |

---

## Quick Reference: Same Concept, Different Name

| Web term | Apple equivalent |
|----------|-------------------|
| Modal / Dialog | Sheet |
| Select | Picker |
| Dropdown | Pop-up Menu |
| Card | (no direct equivalent — closest: grouped List row) |
| Navbar | Toolbar / Navigation Bar |

---

## Related Terms & Glossary

- **HIG**: Human Interface Guidelines (Apple's design documentation)
- **UIKit**: iOS/iPadOS UI framework (imperative)
- **AppKit**: macOS UI framework (imperative)
- **SwiftUI**: Declarative UI framework (cross-platform, Apple)
- **Catalyst**: Run iPad apps on macOS
- **Trait Collection**: Environment info (size class, appearance, accessibility)
- **Component Library**: Pre-built UI components (Material UI, Chakra, shadcn)
- **Design System**: Complete set of design standards and components
- **Atomic Design**: Methodology — atoms → molecules → organisms → templates → pages
- **BEM**: CSS naming convention (Block__Element--Modifier)
- **Semantic HTML**: Using the correct HTML element for meaning (nav, article, aside)
- **Progressive Enhancement**: Basic functionality first, enhance for capable browsers
- **Graceful Degradation**: Build for modern browsers, ensure older ones still work
- **Responsive vs. Adaptive**: Responsive adapts continuously; adaptive serves distinct layouts per breakpoint
- **SPA**: Single Page Application (loads once, updates dynamically)
- **SSR / CSR**: Server-Side Rendering (HTML from server) vs. Client-Side Rendering (HTML in browser)
- **Hydration**: Making server-rendered HTML interactive with JavaScript

## CSS Layout Methods

| Method | Best For |
|--------|----------|
| Flexbox | One-dimensional layouts (row or column) |
| CSS Grid | Two-dimensional layouts (rows and columns) |
| Float | Legacy; text wrapping around images |
| Position | Overlays, fixed elements, precise placement |
