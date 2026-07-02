# 124 — Benchmark perf-critical Swift under `-O` (never Debug); allocation-free folded-byte scan over an mmap

**Tags:** SWIFT_OPTIMIZATION_LEVEL, -O benchmark, @testable Release, allocation-free scan, mmap bytes, ASCII case-fold, top-N selection, xcodebuild test

**Best for:** any hot path you hand-optimize in Swift — a byte scanner, parser, hash, image kernel,
or a linear scan over a memory-mapped blob — where you need a *trustworthy* latency number and an
allocation-free inner loop. Two linked lessons: (1) **never trust a Debug benchmark** of hand-rolled
Swift, and (2) the technique that actually made the scan fast.

**Discovered in:** SearchAway Wave 5 — `allMatching(query:)` over a 1M-entry `mmap`'d filename index
was **25× over a 100 ms budget (~2.4 s)**. It re-ran NFC normalization + materialized a `String` for
*every entry, every keystroke*. The "fix" first measured *worse*, then 30× better — because of the
build configuration, not the code.

---

## Lesson 1 — `xcodebuild test` defaults to Debug `-Onone`, which lies about hand-rolled loops

The naive version called Foundation: `Normalization.canonical(name).lowercased().contains(q)`. The
optimized version was a hand-rolled byte loop over the raw mmap. Measured p99 at 1M entries:

| Build | Foundation `.contains` | Hand-rolled byte scan |
|-------|------------------------|------------------------|
| Debug `-Onone` | ~2.4 s | **~11–15 s (worse!)** |
| `-O` | — | **65–89 ms (passes)** |

Under `-Onone` Swift keeps **array/buffer bounds-checks**, does **no inlining**, and retains
**ARC retain/release** inside tight loops. Your hand-written loop pays all of that per iteration.
Foundation/stdlib methods are **pre-compiled optimized library code**, so they look fast in Debug even
though they allocate — making your optimization look like a regression. **A Debug benchmark of
hand-rolled Swift points the wrong way.**

### The fix — measure under `-O`, but you can't just switch to Release for tests

```bash
# ❌ Release test bundle fails: Release doesn't set -enable-testing, so @testable import breaks:
#    error: unable to resolve Swift module dependency to a compatible module: 'SearchAway'
xcodebuild test -scheme App -destination 'platform=macOS' -configuration Release   # DON'T

# ✅ Stay on the Debug config (keeps -enable-testing → @testable import works) and override
#    ONLY the optimization level. You get optimized code AND a resolvable testable module.
xcodebuild test -scheme App -destination 'platform=macOS' \
  SWIFT_OPTIMIZATION_LEVEL=-O \
  -only-testing:AppTests/BenchmarkTests1M
```

Routine full runs should **skip the heavy synth benchmark** (the 1M build is slow in Debug):
`-skip-testing:AppTests/BenchmarkTests1M`. Gate giant cases behind an env var
(`ProcessInfo.processInfo.environment["BENCH_5M"]` → else `throw XCTSkip(...)`).

### Make the benchmark self-classify so "known-slow" doesn't either fail CI or hide

Split query/inputs into **`scanBound`** (cost dominated by the per-element work → a **hard** assert,
guards the optimization) vs **broad/known-deferred** (cost dominated by something else → **measure +
log, never silently pass**). A broad query that matches a huge fraction is *not* testing your scan.

```swift
if p99 > limit {
    if hardFail && qc.scanBound { XCTFail("scan-cost regression: \(qc.label) \(p99) ms") }
    else if !qc.scanBound { print("BENCH \(qc.label)_KNOWN_DEFERRED p99=\(p99) ms — needs bounded top-N (task X)") }
}
```

---

## Lesson 2 — allocation-free folded-byte scan over the mmap

The per-query cost was 2 × N `String` allocations + a full NFC pass per entry. But the blob was
**already stored NFC** at write time, so `canonical()` was pure waste. Only **case** remained.

```swift
// Fold the QUERY once, before the scan — not per entry.
let needle = Normalization.canonical(rawQuery).lowercased()       // NFC + lowercase, once
let needleBytes = Array(needle.utf8)

// Per entry: compare directly against raw mmap bytes — NO String per entry.
// ASCII fast path: case-fold a byte branch-free (`b | 0x20` maps A–Z → a–z).
@inline(__always) func asciiFold(_ b: UInt8) -> UInt8 {
    (b >= 0x41 && b <= 0x5A) ? (b | 0x20) : b
}
// hay = UnsafeRawBufferPointer into the mmap'd name/path blob for this entry (zero copy).
func asciiCIContains(_ hay: UnsafeRawBufferPointer, _ needle: [UInt8]) -> Bool { /* folded byte search */ }
```

- **Fold the query once**; the data is already NFC, so you only fold **case** at compare time.
- **ASCII fast path** covers ~all real filenames; for bytes ≥ 0x80 fall back to the `String` +
  `lowercased()` path (rare → negligible). Correctness holds: NFC (from the blob) + case folding.
- **Materialize the full struct only on a match**, never per candidate.
- **Do NOT store a second "folded" copy of the blob** — for big fields (paths) that blows your disk
  budget. Fold-compare in place against the existing NFC bytes; zero extra storage.

Result: ~18× faster under `-O`, and RAM dropped **173 → 92 MB** (no per-query allocation).

---

## Lesson 3 — scan cost ≠ match-set cost

After the scan was fixed, *broad* queries (a common prefix matching ~25 % of 1M = 250k hits) were
still 270–600 ms — because the path **materialized every match into a struct and fully sorted it**.
The scan is no longer the bottleneck; **handling a huge result set is.** Fix = **bounded top-N
selection** (a partial-sort/heap over the ranking comparator — only the product's top 5–10 ever need
full materialization) and/or a sorted index for binary-search prefix. Don't conflate the two costs;
the benchmark's `scanBound` classification (Lesson 1) keeps them separate.

**Gotchas:** SourceKit shows phantom "No such module XCTest" / "cannot find type" after `xcodegen
generate` — `xcodebuild` is truth (#47, #28). Static `var` in an XCTest needs
`nonisolated(unsafe)` under Swift 6 strict concurrency (XCTest serializes setUp/test/tearDown, so
there's no real race). Pairs with **#118** (single-owner mmap store → actor), **#73** (headless
permission-free verification), **#34** (testing).
