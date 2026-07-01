# #133 — Labeled on/off "pill" for a toolbar `Menu` — `.menuStyle(.button)` replaces the macOS pull-down bezel with your own `ButtonStyle`

**Extracted from:** Magpie (2026-06-25)

You have several `Menu`s in a macOS toolbar (each a feature with sub-options). Two problems:

1. **They read as bare icons.** A SwiftUI `Label("Subtitles", systemImage:)` in a toolbar renders **icon-only** by default — the name shows only as a hover tooltip. Four similar glyphs whose sole on/off cue is a teal-vs-gray tint aren't self-describing ("the buttons aren't indicative of what they're set to").
2. **You can't just paint a background behind the label.** A `Menu` draws macOS's standard **pull-down bezel** around its label. Add your own colored capsule inside and you get a **pill-inside-a-bezel double background** (same family of bug as #89's Liquid-Glass double background).

## The fix — `.menuStyle(.button)` + a custom `ButtonStyle`

`.menuStyle(.button)` makes a `Menu` honor the surrounding `.buttonStyle`, so a `ButtonStyle` **replaces** the pull-down chrome entirely — your pill *is* the button — while the dropdown arrow and the menu of options are kept. Force the label to show text with `.labelStyle(.titleAndIcon)`.

```swift
// Always show name + icon (toolbar Labels default to icon-only).
private struct ExtrasMenuLabel: View {
    let title: String; let symbol: String; let isActive: Bool
    var body: some View {
        Label(title, systemImage: isActive ? "\(symbol).fill" : symbol)
            .labelStyle(.titleAndIcon)
    }
}

private struct ExtrasPillStyle: ButtonStyle {
    let isActive: Bool
    var activeTint: Color = Theme.accent          // default "on" colour…
    var activeForeground: Color = Theme.textPrimary // …paired with its text colour
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(Theme.Typo.control)
            .foregroundStyle(isActive ? activeForeground : Theme.textSecondary)
            .padding(.horizontal, 10).padding(.vertical, 4)
            .background(RoundedRectangle(cornerRadius: Theme.rButton, style: .continuous)
                .fill(isActive ? activeTint : .clear))                 // filled when on
            .overlay(RoundedRectangle(cornerRadius: Theme.rButton, style: .continuous)
                .strokeBorder(isActive ? .clear : Theme.hairline(0.12), lineWidth: 1)) // outline when off
            .brightness(configuration.isPressed ? -0.04 : 0)
    }
}

Menu { /* Toggles / Pickers — the modes */ } label: {
    ExtrasMenuLabel(title: "Subtitles", symbol: "captions.bubble", isActive: isActive)
}
.menuStyle(.button)                                  // <- lets ButtonStyle replace the bezel
.buttonStyle(ExtrasPillStyle(isActive: isActive))
```

## Extension — an **amber caution** pill for a high-consequence toggle

When one control does something drastic (here: "Split into chapter files" writes **one file per chapter**, easily mistaken for adding navigation markers), make the *output consequence* — not the toggle — look different. Give it a distinct tint via the **defaulted** style params, so every other call site compiles unchanged and only this one opts in:

```swift
.buttonStyle(ExtrasPillStyle(
    isActive: isActive,
    activeTint:       isSplitting ? Theme.amber : Theme.accent,   // amber = caution, vs teal = active / red = error
    activeForeground: isSplitting ? Color(white: 0.12) : Theme.textPrimary // near-black contrasts on bright amber
))
```

Spell out the consequence **at the point of choosing** with a two-`Text` menu-item label (title + plain-language subtitle):

```swift
Toggle(isOn: $prefs.splitByChapters) {
    Text("Split into separate files")
    Text("One file per chapter — a 15-chapter video makes 15 files.")
}
```

## Gotchas

- **`.labelStyle(.titleAndIcon)` is mandatory** — without it the toolbar shows icon-only and the names stay invisible (the whole complaint).
- **`.menuStyle(.button)` is what makes `.buttonStyle` apply to a `Menu`.** Without it, `.buttonStyle` is ignored and you keep the system bezel.
- **Contrast is a property of the (fill, foreground) pair**, not the text alone: `textPrimary` is near-white in dark mode → unreadable on bright amber → pair amber with a near-black foreground. Teal (mid-tone) takes the adaptive `textPrimary` fine.
- **The two-`Text` subtitle is platform-rendered.** macOS *usually* shows the second line as a gray subtitle, but it's the OS's call — if it ever renders bare, fall back to an explicit non-interactive caption `Text` row (the pattern already used elsewhere in the same menu).
- Editing this file, **SourceKit may flag cross-file `Cannot find type 'PreferencesStore'/'DownloadOptions'`** while analyzing it in isolation — bogus; `xcodebuild` is truth (#47).
- **Pre-Tahoe glass:** on the macOS 26 SDK, native toolbar items get Liquid Glass capsules — opt the app out (#89) or your pill is double-glassed.

Source: Magpie `Views/ExtrasToolbar.swift`. Pairs with **#89** (toolbar Liquid-Glass opt-out — read first if on the macOS 26 SDK), **#00** (App Shell / `Theme`), **#70** (data-driven control strips), **#125** (`Menu`-not-`Picker` for an action-bearing chooser).
