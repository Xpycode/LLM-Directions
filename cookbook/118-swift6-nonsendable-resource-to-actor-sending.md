# 118 — Hand a non-Sendable resource to an actor with `sending` (and observe it *through* the actor)

**Best for:** giving a single non-`Sendable` resource — an `mmap`'d store, a file handle, a DB
connection, a C stream — to a Swift 6 `actor` that becomes its sole accessor, without tripping
"sending '…' risks causing data races." The companion rule is the one that actually bites: once you
transfer it, **you may never touch it directly again** — reads go through the actor.

**Discovered in:** SearchAway Wave 3 — `IndexStore` (a non-`Sendable` `final class` wrapping an
`mmap`) is *written* by `LiveUpdater` (an FSEvents actor) and *read* by `QueryEngine` (a query actor).
Handing it to either actor failed to compile at 3 call sites until the ownership transfer was made
explicit and the tests stopped reading the store after handing it over.

---

## The error

```
error: sending 'store' risks causing data races
    let engine = QueryEngine(store: store)
                                    ^~~~~
```

Swift 6 region-based isolation has *proven* a race is possible: the same non-`Sendable` reference now
lives in two isolation domains — the caller's and the actor's. It is not a false positive. A `@unchecked
Sendable` slapped on the resource would silence it and ship the race. Don't.

## The fix — two halves, both required

### 1. Mark the transfer point `sending`

`sending` on a parameter means "the caller gives up its claim; ownership moves into the callee's
isolation region." That is exactly an actor taking sole custody of a resource.

```swift
actor QueryEngine {
    private var store: IndexStore?            // non-Sendable, owned

    init(store: sending IndexStore) {         // ← ownership transfers in
        self.store = store
    }

    /// Swap the store (e.g. after a full index rebuild). Old one closed first.
    func setStore(_ newStore: sending IndexStore) {
        store?.close()
        store = newStore
    }

    /// Deterministically release the mmap'd file. Queries return empty until re-attached.
    func close() {
        store?.close()
        store = nil
    }
}
```

```swift
actor LiveUpdater {
    private let store: IndexStore             // non-Sendable, owned for the actor's lifetime

    init(roots: [URL], store: sending IndexStore) {
        self.roots = roots
        self.store = store
    }
}
```

### 2. Stop touching the resource after you transfer it — observe *through* the actor

This is the part people miss. After `LiveUpdater(roots:store:)` the store belongs to the actor. A test
(or any caller) that then reads `store` directly — in `tearDown`, a `defer`, or a post-mutation
assertion — re-introduces the exact cross-domain access `sending` just outlawed, and won't compile.

Expose the *narrow* thing callers need as an actor-isolated method that returns a `Sendable` value:

```swift
extension LiveUpdater {
    /// Observe store state from tests/diagnostics WITHOUT touching the transferred store.
    func snapshotContainsName(_ substring: String) -> Bool {
        store.substringSearch(substring).count > 0     // Bool is Sendable — safe to return
    }
    func closeStore() { store.close() }                // teardown goes through the actor too
}
```

`Set<FileID>`, `Int`, `Bool`, a small value struct — all fine to hand back. Never return the resource
itself or a non-`Sendable` view into it.

## Test shape that compiles (the ownership discipline)

Build the resource as a **local**, transfer it, and from then on go through the actor. Track only
**`Sendable` cleanup handles** (the file `URL`, not the open store) in test properties.

```swift
override func setUpWithError() throws {
    // Property holds only the URL (Sendable). NOT the open store.
    indexFileURL = FileManager.default.temporaryDirectory
        .appendingPathComponent("Test-\(ProcessInfo.processInfo.globallyUniqueString).sawx")
    try IndexStore.write([], to: indexFileURL)
}

func testCreateIsIndexed() async throws {
    let store = try IndexStore.load(indexFileURL)        // local, single region
    let updater = LiveUpdater(roots: [fixture.root], store: store)  // ← consumed here
    updater.delegate = NullDelegate()
    await updater.start()
    defer { Task { await updater.stop(); await updater.closeStore() } }

    // … mutate the filesystem …

    // Observe THROUGH the actor — never `store.…` again.
    let found = await poll { await updater.snapshotContainsName("created_file") }
    XCTAssertTrue(found)
}
```

`QueryEngine` tests mirror this: `let store = try IndexStore.load(url)` → `QueryEngine(store: store)`
→ `defer { Task { await engine.close() } }`. No `var store` property that `tearDown` closes — that
property would alias the transferred value and reintroduce the race.

> **Why a `var store: IndexStore?` property fails where a local succeeds:** the property is reachable
> from `tearDown`, so the region that includes it is still "live" after the send. A `let` local that is
> never named again after the call site is a *disconnected* region — the compiler can prove the caller
> released it. Prefer locals at transfer points.

---

## Sibling gotcha — local var written in a `@MainActor` callback, read after `await`

Same family of diagnostic, different cause. A common test idiom captures a result in a local `var` from
an `@escaping @MainActor` callback, then reads it after `await fulfillment(...)`:

```swift
func test…() async throws {                 // ← non-isolated test body
    var delivered: [RankedResult] = []
    engine.submit(query: "x") { @MainActor results in
        delivered = results                 // written on MainActor
        expectation.fulfill()
    }
    await fulfillment(of: [expectation], timeout: 2)
    XCTAssertEqual(delivered.count, …)      // read off MainActor → "sending 'delivered' risks…"
}
```

**Fix:** put the body in the *same* isolation domain as the callback by annotating the method
`@MainActor` — now the var and the closure are co-isolated:

```swift
@MainActor
func test…() async throws {
    var delivered: [RankedResult] = []
    engine.submit(query: "x") { @MainActor results in delivered = results; expectation.fulfill() }
    await fulfillment(of: [expectation], timeout: 2)
    XCTAssertEqual(delivered.count, …)      // co-isolated read — clean
}
```

(Alternative: funnel deliveries through an `actor Collector { … }` and `await collector.value` — use
that when the callback fires multiple times or from mixed isolation.)

---

## Checklist

- [ ] Resource is genuinely single-owner? → give it to one actor; mark `init`/setter params `sending`.
- [ ] Removed every direct read of the resource after the transfer (tearDown, defer, assertions)?
- [ ] Added narrow actor-isolated accessors returning `Sendable` values for the reads callers need?
- [ ] Test properties hold only `Sendable` cleanup handles (URLs), not the open resource?
- [ ] Transfer happens from a `let` local that is never named again — not from a stored property?
- [ ] Test result vars written in a `@MainActor` callback → method marked `@MainActor`?
- [ ] Did **not** reach for `@unchecked Sendable` to silence it.

## Anti-patterns

- **`@unchecked Sendable` on the resource** — silences a real, proven race. The whole point of the
  single-owner-actor design is that you *don't* need it.
- **Keeping a second reference "just for cleanup."** That reference is the race. Close through the actor
  (`await x.close()` / `closeStore()`).
- **Returning the resource (or a non-Sendable slice) from the accessor.** Return a computed `Sendable`
  snapshot instead.

## See also

- `19-swift6-concurrency.md` — `@MainActor` + `@Observable` for main-thread-only mutation.
- `20-actor-reentrancy.md` — when a synchronous sequence inside an actor *can't* race.
- `86-single-flight-async-dedup-actor.md` — actor as the single coordination point for async work.
