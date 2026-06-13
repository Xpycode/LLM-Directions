# 93 — Sorting a list beachballs: keep the computed view-feed pure, prewarm the expensive key off-main

**Problem.** A list is sorted by a computed property the view reads in `body`:

```swift
var filteredGroups: [RecordGroup] {
    visible.sorted { resolvedDate(for: $0) < resolvedDate(for: $1) }   // ← resolvedDate does file I/O
}
```

Sorting by "Date" hangs the whole window for ~1s. The date isn't stored — it's *resolved* (read the
first `.SRT` cue + a filesystem stat) per group. With the source on slow media (an SD card) and dozens
of rows, that's dozens of synchronous file opens **on the main thread, inside view-body evaluation**.
It looks like the thumbnails are to blame because the freeze coincides with their loading — but
thumbnails run on an `actor` with async extraction and never touch the main thread. The real blocker is
the I/O hiding in the sort comparator.

## Pattern — the sort reads only an in-memory cache; an off-main prewarm fills it and bumps a published token

Split responsibilities: the **sort is pure** (cache lookup + an in-memory fallback, zero I/O, can't
freeze); a **background prewarm** does the expensive resolution off the main thread and then nudges the
view to re-sort into corrected order.

```swift
private var resolvedCache: [UUID: Date?] = [:]      // NOT @Published (mutated off the render path)

/// Bumped only to trigger a re-render once the prewarm lands — the observable signal for the cache.
@Published private var resolvedRevision = 0

// 1. Pure sort field — read the cache, fall back to an already-in-memory value. No resolve here:
//    this runs in `filteredGroups` during view body on the main thread.
private func sortField(for g: RecordGroup) -> SortField {
    let date: Date? = resolvedCache[g.id] ?? g.embeddedDate   // Date?? ?? Date? → Date?
    return SortField(index: g.groupIndex, name: g.title, date: date, …)
}

// 2. Off-main prewarm: resolve everything after a scan, publish on the main actor, bump the token.
private func prewarmDates() {
    let items: [(id: UUID, clip: Clip?)] = groups.map { ($0.id, $0.clips.first) }  // Sendable only
    guard !items.isEmpty else { return }
    let override = settings.dateOverride
    Task.detached(priority: .utility) { [weak self] in
        var resolved: [UUID: Date?] = [:]
        for item in items {
            let d = item.clip.flatMap { Resolver.resolve(for: $0, override: override).date }
            resolved.updateValue(d, forKey: item.id)         // stores `.some(nil)`, not a delete
        }
        await MainActor.run {
            guard let self else { return }
            for (id, d) in resolved where self.resolvedCache[id] == nil {
                self.resolvedCache.updateValue(d, forKey: id)
            }
            self.resolvedRevision &+= 1                       // forces one clean re-sort
        }
    }
}
```

Call `prewarmDates()` at the end of the scan. Result: every sort is instant (pure memory); the Date
order shows an embedded-date approximation for a beat, then snaps to corrected order when the prewarm
finishes — no freeze, ever.

## Why the token works

`resolvedCache` is deliberately **not** `@Published` (it mutates outside the render path; publishing it
would re-render on every fill). But updating a non-published property won't refresh the view. Bumping
**any** `@Published` property fires `objectWillChange`, which re-renders every observer of the
`ObservableObject` regardless of which property it reads — so the view re-evaluates `filteredGroups`
and re-sorts with the now-warm cache. One private `@Published Int` is the whole mechanism.

## Gotchas

- **`Dictionary[key] = nil` deletes the key.** With a `[UUID: Date?]` cache, store a resolved-to-nil
  result with `updateValue(nil, forKey:)`, not `cache[id] = nil`. And distinguish "absent" from
  "resolved to nil": `cache[id]` is `Date??` — `?? fallback` treats only the *outer* `.none` (absent)
  as a miss, preserving a cached `.some(nil)`.
- **Cross-actor capture must be `Sendable`.** Build the work list (`[(UUID, Clip?)]` + a `Date?`) on the
  main actor *before* `Task.detached`; never send the non-`Sendable` row/model aggregate itself.
- **Decorate-sort-undecorate** if the key is even moderately costly to read: `map` each item to
  `(item, field)` once, sort the pairs, drop back — so the key is computed O(n), not O(n log n).
- Keep a synchronous resolve available for **user-triggered, small** paths (e.g. a rename preview over
  the *selected* rows) — same cache, two access patterns. Only the all-rows sort path must stay pure.
- General rule: **a SwiftUI computed view-feed runs on the main thread inside `body`.** No file/network
  I/O, no blocking work there — ever. Push it to an async prewarm.

## When to reach for it

Sorting/filtering a list by a key that's computed (file read, parse, network, heavy derivation) rather
than stored; any "the list hangs when I sort/filter" symptom; any place you're tempted to do I/O inside
a computed property a view reads.

— Extracted from Conjoyn (`ConversionViewModel.swift` `filteredGroups`/`prewarmStartDates`, sortable
recordings columns, 2026-06-12).
