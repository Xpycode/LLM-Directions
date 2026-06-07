# State-aware menu pill — one tap means "go here" or "switch here" depending on where you are

**Source:** `1-macOS/ClipSmart/` (Aloft) — `Views/ContentView.swift` `reservoirMenu` / `listsMenu` (2026-06-05).

A header "pill" that is **both a navigation target and a switcher**: it represents a surface (Saved / a Smart List) *and* offers a menu of alternatives (other groups / lists). The naive designs both annoy:

- **Whole pill always opens the picker** → reaching the default costs two taps (open menu → pick the obvious first row).
- **Body-tap always navigates to the default** → there's no fast way to switch, and a tiny chevron becomes the only menu affordance.

**Pattern — make the gesture's meaning follow the current state:**

| You are… | Body tap | Chevron |
|---|---|---|
| **not** on this surface | **navigate** onto it in one tap (its default/last target) | open picker |
| **already** on this surface | **open the picker** (re-navigating would be a no-op, so reuse the tap) | open picker |

The chevron *always* opens the picker, so switching is reachable from any state; the body tap is the cheap path that does the obvious thing. (This is the same idiom as Finder: clicking an already-selected filename starts a rename rather than re-selecting — the inactive meaning becomes meaningless once active, freeing the gesture for a second job.)

**Two rules that make it robust:**

### 1. One `tapTarget` expression drives label + tap + accessibility

The control must never *say* one thing and *do* another. Compute the target once; derive everything from it. (An earlier bug: the pill read "Saved" while a tap — with an "open last" pref on — went to a different group. The label was lying.)

```swift
private var reservoirMenu: some View {
    let activeCollection = viewModel.selectedCollection

    // The single source of truth: what a tap would open.
    //   active surface  →  itself
    //   else            →  last-used (if the pref is on) ?? the default
    let tapTarget: ClipboardCollection? = activeCollection
        ?? (savedOpensLastGroup ? viewModel.lastUsedReservoir : nil)
        ?? viewModel.savedGroup

    // Label PREVIEWS the target, so an inactive pill shows where a tap lands
    // ("SHC") instead of a generic category word ("Saved").
    let targetIsNamed = (tapTarget?.id).map { $0 != .savedGroupID } ?? false
    let pillName = targetIsNamed ? (tapTarget?.name ?? "Saved") : "Saved"
    let pillIcon = targetIsNamed ? (tapTarget?.icon ?? "bookmark.fill") : "bookmark.fill"

    return HStack(spacing: 4) {
        HStack(spacing: 4) {
            Image(systemName: pillIcon)
            Text(pillName).lineLimit(1).truncationMode(.tail)
                .frame(maxWidth: activeCollection != nil ? 160 : 90, alignment: .leading)
                .layoutPriority(activeCollection != nil ? 2 : 1)   // see #79
        }
        .contentShape(Rectangle())
        .onTapGesture {
            if activeCollection != nil { showPicker = true }       // active → switch
            else { viewModel.setReservoir(tapTarget) }             // inactive → go (same target as the label)
        }

        // Chevron: ALWAYS opens the picker. Enlarge the hit target with a fixed
        // frame kept within the line height so it stays easy to hit without
        // growing the pill (a caption2 glyph alone is a ~8×8pt target — too small).
        Image(systemName: "chevron.down")
            .font(.caption2)
            .frame(width: 18, height: 16)
            .contentShape(Rectangle())
            .onTapGesture { showPicker = true }
    }
    .popover(isPresented: $showPicker, arrowEdge: .bottom) { pickerContent }
}
```

### 2. "Last-used" must span the whole control after a merge

If two pills (e.g. "Saved" + "Groups") get merged into one, any "open last-used" memory must include **every** target the merged control can reach — including the formerly-separate default. The original code excluded the default from last-used tracking (correct when it was its own pill); after the merge that exclusion made an explicit pick of the default fail to "stick":

```swift
// persistSurface: record ANY reservoir (incl. the default) as last-used —
// after the merge "last-used" means "last-used reservoir", not "last-used named group".
private func persistSurface(_ collection: Collection?) {
    guard let c = collection else { /* history sentinel */ return }
    d.set(c.id.uuidString, forKey: lastSurfaceKey)
    d.set(c.id.uuidString, forKey: lastGroupKey)   // ← no `if c.id != defaultID` guard
}
```

**Keyboard parity:** route the keyboard shortcut through the *same* `tapTarget` resolution as the body tap, so `⌘2` and a pill click land identically (see #08). Pair a "select by position" (`⌘1/2/3`) with a "cycle" (`⌘]`/`⌘[`) — note `⌘Tab` is reserved by macOS and never reaches an in-app monitor.

**Gotcha — setting-gated bugs hide on the default path.** The "open last-used" behaviour is opt-in (off by default), so the stale-target and doesn't-stick bugs were invisible until the toggle was flipped. Live-test the *non-default* branch of any preference.

Pairs with #79 (the active-pill width budget used above), #08 (keyboard tiers), #10 (selection models).
