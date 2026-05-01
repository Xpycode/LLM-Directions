# `URL.appendingPathComponent(_:)` fs-probe gotcha (URL equality flips when the directory appears)

**Source:** `1-macOS/AvidMXFPeek/` — `Services/PreviewCache.swift::directoryURL(for:)` and its `prepareOutputDirWipesPriorContents` test (2026-04-22, Wave P5).

Two calls to `rootDir.appendingPathComponent("some-hash")` on the same actor at two different times can return **two different URLs** that compare unequal — because the single-argument overload of `appendingPathComponent` performs a filesystem probe to decide whether the result should be a *directory* URL (trailing-slash semantics) or a *file* URL. The probe result flips once the directory gets created between the two calls, so:

```
Call 1 (dir doesn't exist yet) → URL.hasDirectoryPath == false
Call 2 (dir was just created)  → URL.hasDirectoryPath == true
URL.== returns false.
```

Fix: always pass the explicit `isDirectory:` parameter for any path component that refers to a directory.

```swift
rootDir.appendingPathComponent(hash, isDirectory: true)   // ✅ stable
rootDir.appendingPathComponent(hash)                       // ⚠️ fs-probed
```

---

## The bug, in one test

```swift
actor PreviewCache {
    private let rootDir: URL

    func directoryURL(for clip: Clip) -> URL {
        rootDir.appendingPathComponent(hashKey(for: clip))   // ⚠️ single-arg form
    }

    func prepareOutputDir(for clip: Clip) throws -> URL {
        let dir = directoryURL(for: clip)
        try? fm.removeItem(at: dir)
        try fm.createDirectory(at: dir, withIntermediateDirectories: true)
        try writeState(.running, at: dir)
        return dir
    }
}

// Test:
let dir1 = try await cache.prepareOutputDir(for: c)
try Data(count: 100).write(to: dir1.appendingPathComponent("seg_000.m4s"))

let dir2 = try await cache.prepareOutputDir(for: c)
#expect(dir1 == dir2)   // ❌ fails
```

On the first call `<rootDir>/<hash>` does not exist yet — `appendingPathComponent` builds a URL with `hasDirectoryPath = false`. `prepareOutputDir` then creates the directory. On the second call the *same* string lookup returns a URL with `hasDirectoryPath = true`, because the directory is now there.

Two URLs, identical path components, different `hasDirectoryPath` flags — `URL ==` walks everything including that flag, so equality fails.

The downstream damage in our case was *multiple*:

- `dir1 == dir2` in the test — surface-level.
- `pathIfCached(for: c)` returned a URL that compared unequal against the one `prepareOutputDir` had just returned, so the `#expect(cached == prepared)` assertion failed even though both pointed at the same directory.
- Silent failures are possible too: a `Dictionary<URL, State>` or `Set<URL>` keyed off these URLs would double-count the same entry.

---

## Why this is easy to miss

`URL`'s behavior around directory-ness is documented but subtle, and Foundation evolved it several times:

| API | Behavior on existing directory | Behavior on non-existent path |
|-----|-------------------------------|-------------------------------|
| `appendingPathComponent(_:)` | stat + set `hasDirectoryPath = true` | `hasDirectoryPath = false` |
| `appendingPathComponent(_:, isDirectory:)` | honors the Bool | honors the Bool |
| `appending(path:, directoryHint:)` (macOS 13+) | honors `directoryHint` (default `.inferFromPath`) | same |

The single-argument overload's filesystem check is implicit — you don't see it, and if the path exists during every call the flag stays consistent and you don't notice. The instant your code transitions a path from not-exist to exist between two calls, URLs constructed before the transition stop equalling URLs constructed after.

This is most likely to bite when:

1. You cache URLs by deriving them from a constant root plus a known suffix.
2. Something in your code creates the directory at that URL partway through the lifetime of the cache.
3. Later code compares URLs, uses them as dictionary keys, or diffs lists.

All three happen routinely in caches, scratch-dir managers, and "prepare-then-write" pipelines.

---

## Fix

Audit every `appendingPathComponent(_:)` whose string is a **directory** and add `isDirectory: true`. File paths can stay on the single-argument form — `hasDirectoryPath` is always false for a leaf regardless of whether the file exists, so the equality risk doesn't apply. (You could be explicit with `isDirectory: false` for completeness, but the code reads more noisily.)

```swift
/// Absolute path to a clip's cache directory (whether or not it exists).
/// `isDirectory: true` is load-bearing: without it, `appendingPathComponent`
/// does a filesystem probe and the returned URL's `hasDirectoryPath` flag
/// flips based on whether the directory currently exists — which breaks
/// URL equality across `prepareOutputDir` calls on the same clip.
nonisolated func directoryURL(for clip: Clip) -> URL {
    rootDir.appendingPathComponent(Self.hashKey(for: clip), isDirectory: true)
}
```

On macOS 13+ the modern call is `appending(path:directoryHint:)` which is strictly better — you can use `.isDirectory` explicitly or `.inferFromPath` if the path ends with `/`. Prefer it for new code:

```swift
rootDir.appending(path: hash, directoryHint: .isDirectory)
```

---

## What doesn't work

| Approach | Still broken? | Why |
|----------|--------------|-----|
| `URL.standardizedFileURL` on each call | **yes** | Standardization collapses `..` and `.`, doesn't touch `hasDirectoryPath`. |
| `url.path` comparison (drop `==`) | works, but | loses the URL-equality contract everywhere else; inconsistent. |
| `url.absoluteString` comparison | **partially** | String form may or may not include trailing slash depending on `hasDirectoryPath` — same root cause, different surface. |
| Call `directoryURL(for:)` once and cache the result inside the actor | works, but | turns a value-like computed lookup into stateful bookkeeping; brittle if the rootDir changes. |
| Create the directory eagerly in `init()` so probe is always `true` | works, sort of | ties cache creation to disk state; breaks if you want to construct multiple caches without touching disk. |

The only clean fix is to make the URL's directory-ness explicit and never let Foundation guess.

---

## When this bites

- **Any actor/struct with a `pathFor(...)` accessor** whose derived URL is consumed by later callers for equality checks.
- **`Set<URL>` or `[URL: T]` caches** where entries are added before vs after the directory materialises.
- **Tests that round-trip through `prepareOutputDir` twice** — the "clean slate" assertion is exactly the call pattern that tickles the flip.
- **Diff algorithms** that compare `FileManager.default.contentsOfDirectory(at:)` output against a hand-built expected list — one side comes with `hasDirectoryPath` set, the other doesn't.

Rule of thumb: **if the code path crosses a "directory may or may not exist" boundary, always use `isDirectory: true` for directories.**

---

## Related patterns

- **`45-macos-firmlink-canonical-path.md`** — the sibling URL-equality gotcha: two URLs that resolve to the same file still compare unequal because of firmlink-vs-raw path-prefix differences. The two patterns compose — tests that hit *both* at once (e.g. a test that writes fixtures under `/var/folders/...` into a directory that materialises mid-test) will fail for either reason. Apply both fixes: canonicalize at boundary, and pass `isDirectory: true` when appending directories.
- **`35-asyncstream-bounded-fanout.md`** — another context where cached-path objects cross actor/task boundaries. Same discipline applies.

---

## History

Discovered during Wave P5 of the v1.2 player plan. Three tests in `PreviewCacheTests` failed after writing an otherwise-clean `PreviewCache` actor: `prepareOutputDirWipesPriorContents`, `pathIfCachedReturnsURLForCompleteEntry`, and `evictToFitRemovesOldestCompleteEntriesFirst`. The pattern of the failures — each involved a URL-equality check after a `prepareOutputDir` call — was the tell.

The fix was one line. The recognition was the work: "it only fails after a directory got created" is not the first hypothesis you reach for when three `#expect(dir1 == dir2)` assertions fail in a cache test.

Worth noting: SwiftUI/Swift concurrency diagnostics don't catch this — the compiler has no opinion on `hasDirectoryPath`, and `URL ==` is a perfectly normal operation. Runtime assertions are the only signal. Cookbook this pattern aggressively; the diff is invisible at a casual read, and the failure mode is non-obvious.
