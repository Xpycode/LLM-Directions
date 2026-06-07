# Truncation in an HStack is a priority contest, not a maxWidth ceiling — fix it with layoutPriority

**Source:** `1-macOS/ClipSmart/` (Aloft) — `Views/ContentView.swift` surface pills (2026-06-05).

**Symptom:** a row of labels (pills, chips, breadcrumb segments) inside an `HStack` with `Spacer`s. One label truncates ("Current App" → "Curre…") even though the math says it should fit, and bumping its `.frame(maxWidth:)` does nothing.

**Why:** `.frame(maxWidth: 84)` is a *ceiling*, not a *reservation* — the frame is flexible `0...84` and sizes to content only if it's *granted* the width. In an `HStack`, SwiftUI hands out the proposed width to children by **layout priority** (default `0` for everyone), and `Spacer` is greedy. When the row is even slightly over-budget (a narrow/resizable window), the flexible text frames are the ones that give — so the label you care about loses space and tail-truncates. Raising `maxWidth` can't help: the binding constraint is the *grant*, not the cap.

**Fix:** give the element you want readable a **higher `layoutPriority`** so it claims its ideal size *before* lower-priority siblings (and before the greedy-but-low-priority Spacers). Make the *less important* element (here, an inactive preview that's reachable another way) the one that yields.

```swift
HStack(spacing: 6) {
    Spacer(minLength: 0)                    // greedy, priority 0 → yields first

    historyPill                             // short, .fixedSize → always whole

    // Two "menu" pills. Exactly one is active at a time. The ACTIVE one is the
    // focus, so it wins the width; the inactive PREVIEW yields and truncates
    // (its full text is still reachable via its chevron/picker).
    Text(savedName)
        .lineLimit(1).truncationMode(.tail)
        .frame(maxWidth: savedActive ? 160 : 90, alignment: .leading)
        .layoutPriority(savedActive ? 2 : 1)        // ← the real fix

    Text(listName)
        .lineLimit(1).truncationMode(.tail)
        .frame(maxWidth: listActive ? 160 : 90, alignment: .leading)
        .layoutPriority(listActive ? 2 : 1)

    Spacer(minLength: 0)
}
```

**Why this composition works:**

- **`layoutPriority` decides the contest.** Active pill `2` > inactive pill `1` > Spacers `0`. Under pressure the Spacers collapse to `0`, then the inactive pill truncates, and the active pill keeps its text last. Raising the *number* on `maxWidth` would not have changed the ordering.
- **`maxWidth` (not a fixed slot) keeps short labels compact.** A *fixed* `width:` ×2 reserves worst-case width for both pills simultaneously and overflows the header; `maxWidth` lets each take only what it needs, so two long names never both reserve at once.
- **State-driven budget.** The active element gets the big ceiling (160) *and* the high priority; flip both with the same `isActive` flag.

**Orthogonal lever — make the value shorter.** Before reaching for layout, ask if the label can just be *smaller and more useful*. ClipSmart's built-in "Current App" list re-labels its pill with the **actual frontmost app** ("TextEdit", `~52pt`) instead of the literal "Current App" (`~78pt`) — it stops being the first thing to truncate *and* answers the user's real question ("whose clips am I seeing?"). The readability fix and the UX fix were the same edit. Do this *and* the priority fix; they're complementary.

**Debugging tell:** if a label truncates but `Spacer`s are clearly absorbing slack elsewhere in the same row, it's a priority problem, not a sizing problem. Reach for `layoutPriority` before `maxWidth`.

Pairs with #78 (the state-aware pill these budgets live in), #67 (jitter-free fixed-width readouts), #70 (data-driven tile strip).
