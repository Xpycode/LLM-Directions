# Destructive-Copy Guard (`src == dest`)

**Use when:** you have a file-copy utility that overwrites its destination (remove-then-copy, truncate-then-write, or rename-replace), and callers might sometimes pass a source URL that happens to equal the destination URL.

**Source:** `1-macOS/CVI/` (Sigil) — `IconCache.swift`. Discovered via the re-apply-from-cache flow introduced in cookbook 37.

---

## The bug

Naive "overwrite" helper:

```swift
// BAD — destructive when sourceURL.standardizedFileURL == destURL.standardizedFileURL
static func saveSource(_ sourceURL: URL, for identity: VolumeIdentity) throws -> URL {
    let destURL = try iconsDir().appendingPathComponent("\(identity.raw).src.\(ext)")
    let fm = FileManager.default
    if fm.fileExists(atPath: destURL.path) {
        try fm.removeItem(at: destURL)
    }
    try fm.copyItem(at: sourceURL, to: destURL)
    return destURL
}
```

When `sourceURL` resolves to the same path as `destURL`:
1. `removeItem(destURL)` succeeds — deletes the file.
2. `copyItem(sourceURL → destURL)` fails with `NSFileReadNoSuchFileError`: *"The file X couldn't be opened because there is no such file."*
3. The cached file is **gone**. The error message points at the file rather than the aliasing bug — puzzling to debug.

In Sigil's case this happened when a user re-applied an already-cached icon: the "effective source" (cookbook 37) handed back the cached URL, which the apply path fed to `saveSource`, which tried to re-copy onto itself.

## The fix

Short-circuit before the destructive step:

```swift
static func saveSource(_ sourceURL: URL, for identity: VolumeIdentity) throws -> URL {
    let ext = sourceURL.pathExtension.lowercased().isEmpty
        ? "bin"
        : sourceURL.pathExtension.lowercased()
    let destURL = try iconsDir().appendingPathComponent("\(identity.raw).src.\(ext)")

    // Self-aliasing: source and destination refer to the same file.
    if sourceURL.standardizedFileURL == destURL.standardizedFileURL {
        return destURL
    }

    // Clear any stale `.src.*` for this identity — different extensions
    // can accumulate otherwise (e.g. jpg → png on re-import).
    let dir = try iconsDir()
    let prefix = "\(identity.raw).src."
    let contents = (try? FileManager.default.contentsOfDirectory(atPath: dir.path)) ?? []
    let fm = FileManager.default
    for name in contents where name.hasPrefix(prefix) {
        try? fm.removeItem(at: dir.appendingPathComponent(name))
    }

    try fm.copyItem(at: sourceURL, to: destURL)
    return destURL
}
```

## Why `standardizedFileURL` specifically

`URL.==` compares the raw string. Two URLs can reference the same file while `==` returns false:

| `URL` A | `URL` B | `==` | same file? |
|---|---|---|---|
| `file:///Users/x/foo.png` | `/Users/x/foo.png` | no | yes |
| `file:///Users/x/./foo.png` | `file:///Users/x/foo.png` | no | yes |
| `file:///Users/x/dir/../foo.png` | `file:///Users/x/foo.png` | no | yes |
| `file:///Users/x/symlink-to-foo` | `file:///Users/x/foo.png` | no | sometimes (symlinks) |

`standardizedFileURL` normalizes the path (collapses `.`/`..`, ensures `file://` scheme, but does NOT resolve symlinks — if you need symlink resolution, use `resolvingSymlinksInPath()` on top).

For cache-alias detection, `standardizedFileURL` is usually enough: the cache writes canonical paths and reads them back; no symlinks involved.

## Regression test

```swift
func testSaveSourceHandlesSelfAliasing() throws {
    let identity = VolumeIdentity("TEST-UUID")
    let original = try createTempPNG()

    // First save: copies original into the cache.
    let cached1 = try IconCache.saveSource(original, for: identity)
    XCTAssertTrue(FileManager.default.fileExists(atPath: cached1.path))

    // Second save with the cached URL as the "source" — must not corrupt.
    let cached2 = try IconCache.saveSource(cached1, for: identity)
    XCTAssertTrue(FileManager.default.fileExists(atPath: cached2.path))
    XCTAssertEqual(cached1.standardizedFileURL, cached2.standardizedFileURL)
}
```

## Generalization

Any helper matching this shape needs the guard:

- `overwrite(src, to: dest)` via remove-then-copy
- `moveItem(src, to: dest)` where callers might have aliased the paths
- `writeAtomically(data, to: url)` where `data` came from reading `url`
- Database UPSERT where the "new" row is actually the current row loaded as draft

The alternative — *"don't call this with `src == dest`"* — pushes a non-local invariant onto every caller. The guard keeps the invariant local to the helper and makes self-aliased calls a no-op instead of data loss.

## Related

- **cookbook 37** (Effective-source fallback) — the caller pattern that naturally aliases source and destination.
