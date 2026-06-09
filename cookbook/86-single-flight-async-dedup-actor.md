# 86 — Single-flight async dedup in an actor (kill a check-then-act-across-`await` race)

**Problem.** Several callers each want the same expensive async result for the same key — N tasks calling "load keyframes for this clip / fetch this URL / generate this thumbnail." The obvious guard looks safe:

```swift
func loadIfNeeded() async {
    guard cache == nil else { return }            // ← check
    let value = await expensiveScan()             // ← every caller suspends HERE...
    cache = value                                 // ← ...before any caller writes
}
```

It isn't. **A synchronous `guard` is worthless once an `await` separates the check from the write.** Every caller passes `guard cache == nil` *before* any of them reaches the assignment, so all N run `expensiveScan()` concurrently. In Penumbra this meant a single clip got **3 simultaneous ffprobe scans** (batch pre-load + per-clip export + the retry's second export all raced the `keyframes == nil` guard) — three whole-file reads competing for one slow volume, each ~3× slower, each hitting the 120s cap and returning *partial* data (`Saved 535/594/594`).

This is the live-TOCTOU counterpart to entry **#20** (*synchronous sequences can't race*): the instant you add an `await` between the check and the act, the race is back.

## Pattern — hold an in-flight ledger in an actor; store the Task *before* awaiting

The dedup state (`who is already scanning key K?`) is shared mutable state, so it needs a serialized home. An **actor** is the right one — and often you already have it (a disk-cache actor). Key an `inFlight` dictionary of `Task`s by the work key. First caller starts the Task and stores it *before* awaiting; everyone else joins the same Task.

```swift
actor KeyframeCache {
    static let shared = KeyframeCache()

    // The single-flight ledger. Concurrent callers for the same URL join the
    // SAME running Task instead of each spawning its own scan. Must live in the
    // actor — the model that calls it is @unchecked Sendable with no isolation,
    // so a synchronous guard there can't serialize anything.
    private var inFlight: [URL: Task<[TimeInterval]?, Never>] = [:]

    func keyframes(for url: URL,
                   scan: @escaping @Sendable () async -> [TimeInterval]?) async -> [TimeInterval]? {
        // 1. Fast path: already on disk.
        if let cached = load(for: url) { return cached }

        // 2. Join an in-flight scan if one is already running for this key.
        if let existing = inFlight[url] { return await existing.value }

        // 3. Start the single-flight scan. Store the Task BEFORE awaiting it, so a
        //    caller entering during the scan (step 2) joins instead of starting a
        //    second one. One key = one scan.
        let task = Task<[TimeInterval]?, Never> { await scan() }
        inFlight[url] = task
        let result = await task.value

        // Persist BEFORE releasing the slot (clear-after-save): while the disk
        // write is in flight, late callers still join the completed Task; once we
        // clear the slot, load(for:) is guaranteed to hit the freshly-written
        // cache rather than racing a fresh scan against an unwritten file.
        if let result, !result.isEmpty { save(result, for: url) }
        inFlight[url] = nil
        return result
    }
}
```

The caller collapses to a thin wrapper — the dumb guard stays only as a cheap fast-out, no longer load-bearing:

```swift
func loadKeyframesIfNeeded() async {
    guard keyframes == nil else { return }
    guard let url = accessibleURL else { return }
    let loaded = await KeyframeCache.shared.keyframes(for: url) { [url] in
        await self.fetchKeyframesWithFFprobe(url: url)   // the caller's expensive pass
    }
    if keyframes == nil { keyframes = loaded }
}
```

## The two ordering decisions that *are* the pattern

1. **Insert the Task before the `await`.** Inside an actor, every `await` is a suspension point where another caller can enter. Store `inFlight[key]` *before* `await task.value` and the second caller finds the slot occupied and joins. Store it *after* and you've built nothing — the slot is empty for the whole scan and caller #2 starts a duplicate. The ordering is the fix.
2. **Clear the slot *after* the save, not before.** Holding the slot through the (sub-millisecond) disk write means a caller arriving in that window joins the completed Task and gets the value; the slot only reopens once the durable cache is guaranteed populated. Clear before the save and a caller in that window sees an empty slot *and* a cache miss → fresh duplicate scan.

## Why an actor and not a `Bool`/`NSLock`

- A **`Bool` flag** ("isFetching") can only make late callers *bail* (skip the work — here, exporting without keyframe snapping), never *await the result*. You need to hand them the in-flight `Task` so they get the value. That's why Penumbra's pre-existing `isFetchingKeyframes` flag was dead code. The `Task` handle is the join primitive; the dictionary of handles is the dedup.
- A lock around a synchronous critical section doesn't span the `await`; you'd be hand-rolling what the actor gives you. Put the ledger in the actor that already owns the resource (here, the disk cache) and the read, the dedup, and the write are all serialized in one place.

## Testable without the real subprocess

Point it at a **non-existent key** so the cache read/write degrade to no-ops (here `cacheKey` fails `attributesOfItem` → `load` returns nil, `save` is a no-op), isolating pure in-flight behaviour. Then assert the two failure modes that bracket a single-flight:

```swift
// dedup too weak → 50 racing callers must trigger exactly ONE scan
let n = NSCounter()
await withTaskGroup(of: [TimeInterval]?.self) { g in
    for _ in 0..<50 { g.addTask { await cache.keyframes(for: url) {
        n.increment(); try? await Task.sleep(nanoseconds: 50_000_000); return [0,1,2] } } }
    for await r in g { XCTAssertEqual(r, [0,1,2]) }      // every joiner gets the shared result
}
XCTAssertEqual(n.value, 1)

// dedup too strong → slot must release so a later call can scan again
_ = await cache.keyframes(for: url2, scan: s); _ = await cache.keyframes(for: url2, scan: s)
XCTAssertEqual(n2.value, 2)                               // never permanently held
```

The sleep inside `scan` holds the in-flight window open so the other 49 callers provably arrive mid-scan.

## Gotchas

- **`@Sendable` closure.** The `scan` is stored in a `Task`, so it must be `@Sendable`; capturing a `@unchecked Sendable` model (`self`) + the key is fine. Capture the key explicitly (`{ [url] in … }`) rather than reaching through `self`.
- **`Task<_, Never>`** when the scan already encodes failure as `nil`/empty — no throwing, no cancellation propagation to reason about. If you *do* want cancellation to cancel the shared scan, that's a deliberate escalation (the first caller's cancellation would cancel everyone's) — usually you don't.
- **Only the originator clears the slot.** Joiners take the early `return await existing.value` branch and never touch `inFlight`, so there's no double-clear.

**One-line tell:** *several callers each kick off the same expensive async work for one key even though one result would do (duplicate fetches/scans/encodes in the log) → a `guard cache == nil` can't stop it because they all pass the guard before any assigns, across the `await`. Move an `inFlight: [Key: Task]` ledger into an actor, store the Task before awaiting it so latecomers join, and clear the slot after you persist.*

**Pairs with** #20 (the synchronous case where TOCTOU is genuinely impossible — the boundary this one crosses), #19 (@MainActor + @Observable isolation), #43 (subprocess fire-and-collect — the kind of expensive work you'd dedup), #85 (the export watchdog that surfaced this bug).

---
*Source: Penumbra `Utils/KeyframeCache.swift` (`inFlight`, `keyframes(for:scan:)`) + `Models/Video.swift` (`loadKeyframesIfNeeded`) + `PenumbraTests/KeyframeSingleFlightTests.swift`. Shipped 2026-06-09 (branch `fix/export-t8-closeout`, `fe33389`); suite 287/1/0.*
