# 98 — SwiftUI list shows stale rows after the data filters → an `.id(index)` modifier silently overrode `ForEach`'s element identity

**Extracted from:** LaunchAway (2026-06-13)

A search/results list updates its data correctly on every keystroke — you can log `engine.results` narrowing 66 → 17 → 1 — but **the screen keeps showing the old rows**. Type "saf" and the engine holds `[Kagi for Safari]` (1 item), yet the panel still renders "Accessibility" (whatever was first in the unfiltered list). The data and the view disagree, and `body` *is* re-running. It looks like a broken `@Observable` binding; it isn't.

## Why it happens

The `ForEach` is keyed by stable element identity, but a child modifier re-keys each row by **array index**:

```swift
ForEach(Array(engine.results.enumerated()), id: \.element.id) { index, target in
    ResultRowView(target: target, isSelected: index == selectedIndex)
        .id(index)                  // ← added so ScrollViewReader could scrollTo(index)
        .onTapGesture { onLaunch(target) }
}
```

`.id(_:)` **sets the view's explicit identity** — and it **overrides** the `ForEach`'s `id: \.element.id`. So rows are now identified by **position**, not by `target.id`. When the list collapses from 116 items to 1, the row at index 0 keeps identity `.id(0)`; SwiftUI sees "same identity as before" and **reuses the cached view tree** from the previous render (the old "Accessibility" row) instead of constructing a fresh row for the new `target`. The new `target` value technically flows in, but the structural reuse leaves the rendered content stale. Filtering/reordering — exactly what a search list does every keystroke — is precisely when index identity breaks.

Why it's so confusing: `.onChange(of: engine.results)` fires correctly (Observation tracks the value independently of row identity), so you see the data change and conclude binding works — while the *rendered* `ForEach` is frozen on index-keyed identities.

## The fix — key everything on the stable element id; scroll to that id too

The reason `.id(index)` was added (so `ScrollViewReader.scrollTo` had a target) is already served by the element's own stable id. Use it for both:

```swift
ScrollViewReader { proxy in
    ScrollView {
        LazyVStack {
            ForEach(Array(engine.results.enumerated()), id: \.element.id) { index, target in
                ResultRowView(target: target, isSelected: index == selectedIndex)
                    .id(target.id)             // stable identity — matches the ForEach key
                    .onTapGesture { onLaunch(target) }
                    .onHover { if $0 { selectedIndex = index } }
            }
        }
    }
    // Scroll to the SELECTED target's stable id (not the index).
    .onChange(of: selectedIndex) { _, newIndex in
        guard engine.results.indices.contains(newIndex) else { return }
        let targetID = engine.results[newIndex].id
        withAnimation(.easeInOut(duration: 0.1)) { proxy.scrollTo(targetID, anchor: .center) }
    }
}
```

`.id(target.id)` is redundant with the `ForEach` key but harmless (same value) and gives `ScrollViewReader` a stable anchor. The list now rebuilds correctly whenever results change.

## Rules to internalize

- **Never identify list rows by array index** when the array can filter, reorder, or insert/delete. Index identity is only safe for a fixed, append-only list — and even then it's a latent trap.
- **`.id(x)` on a `ForEach` child overrides the `ForEach`'s `id:` key.** If you must attach `.id()` (for `ScrollViewReader`, transitions, forced teardown), pass the **same stable identity** the `ForEach` uses, never a positional or otherwise-derived value.
- **`ScrollViewReader` does not need index ids.** A `ForEach(_, id: \.element.id)` already assigns each row that id as its scroll anchor — `proxy.scrollTo(element.id)` just works; map your selected *index* to its *element id* at the call site.
- **Diagnosis tell:** data observably changes (log it / `onChange` fires) but the rendered list is stale → suspect a positional `.id()` or an index-based `ForEach(0..<n)` before suspecting the model or the `@Observable` binding. (Localized in LaunchAway by a `body`-level `NSLog` proving `body` re-ran while rows stayed stale — see #97.)

Source: LaunchAway `01_Project/LaunchAway/Views/LauncherView.swift` (`scrollingResults`). Pairs with #70 (data-driven tile/result strip — identity for reorder/filter), #97 (the stderr-capture diagnosis that isolated this), #00 (App Shell Standard).
