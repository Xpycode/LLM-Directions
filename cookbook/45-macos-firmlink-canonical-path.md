# macOS firmlinks and `canonicalPath` (`/var` vs `/private/var` gotcha)

**Source:** `1-macOS/AvidMXFPeek/` — `MXFFolderScannerTests.withTempFolder` (2026-04-21)

When comparing a `URL` you constructed from a temp-path prefix against a `URL` that came out of `FileManager`'s enumerator, `file:///var/folders/...` can fail equality against `file:///private/var/folders/...` even though both point at the same file. The culprit is an **APFS firmlink** — `/var → /private/var` on Catalina and later — which `URL.resolvingSymlinksInPath()` deliberately ignores. Use `URLResourceValues.canonicalPath` (or `realpath(3)`) to resolve it.

---

## The bug, in one test

```swift
let folder = FileManager.default.temporaryDirectory      // /var/folders/.../T
    .appendingPathComponent("test-\(UUID().uuidString)")
try FileManager.default.createDirectory(at: folder, withIntermediateDirectories: true)

let fixture = folder.appendingPathComponent("corrupt.mxf")
try Data(count: 512).write(to: fixture)

// A scanner that uses FileManager's enumerator to discover files:
let found = scanner.scan(folder: folder).first!

#expect(found.fileURL == fixture)  // ❌ FAILS
// found.fileURL → file:///private/var/folders/.../corrupt.mxf
// fixture       → file:///var/folders/.../corrupt.mxf
```

Counts match, paths match to the eye, the file is the same file — but `==` on `URL` is byte-wise on the path string, and the two disagree on whether `/var` has been expanded.

---

## Why `resolvingSymlinksInPath()` doesn't fix it

This is the first thing you'd reach for:

```swift
let folder = FileManager.default.temporaryDirectory
    .resolvingSymlinksInPath()  // no-op
```

On macOS 10.15+ (Catalina), the read-only system volume structure turned `/var`, `/etc`, `/tmp`, `/usr/local` and friends into **firmlinks** — a new APFS mechanism that looks like a symlink to most shell tools but isn't one on disk. `resolvingSymlinksInPath()` and `realpath(1)` *without* flags both leave firmlinks alone on purpose, because the pointing-at-a-read-only-target detail is meant to be invisible to normal code.

`FileManager.default.enumerator(at:…)`, however, ends up going through the firmlink during directory traversal and yields URLs with the *resolved* form (`/private/var/...`). That's a path the kernel gave it; not a choice it made.

So: what you put in doesn't match what comes out, and the "obvious" normalizer doesn't bridge the gap.

---

## The fix

`URLResourceValues.canonicalPath` resolves firmlinks. Apply it to a path that **already exists** (the canonical-path lookup requires a stat), then use that as the base for everything you append:

```swift
let fm = FileManager.default
let rawParent = fm.temporaryDirectory
let canonical = (try? rawParent.resourceValues(forKeys: [.canonicalPathKey]).canonicalPath)
    ?? rawParent.path
let parent = URL(fileURLWithPath: canonical)
let folder = parent.appendingPathComponent("test-\(UUID().uuidString)")
try fm.createDirectory(at: folder, withIntermediateDirectories: true)
```

Now `folder.path` is `/private/var/folders/.../test-UUID`, everything you append inherits that prefix, and `URL ==` lines up with what the enumerator returns.

`realpath(3)` via C bridging works too and gives the same answer — canonical-path and `realpath` are the two Apple-supported ways:

```swift
var buf = [CChar](repeating: 0, count: 1024)
realpath(rawParent.path, &buf)
let canonical = String(cString: buf)
```

Prefer the resource-key form — it's pure Foundation, no C bridging, no buffer sizing.

---

## When this bites

- **Unit tests that build expected URLs manually and compare against `FileManager` output.** Most common case. The moment your assertion is "URL equals expected", you're exposed.
- **`Set<URL>` / `[URL: T]` keyed by URLs that come from two different sources.** One side enumerated, the other hand-built — they hash to different buckets.
- **Path-based deduplication.** If you're deduping a scan's output against a user-provided list of URLs, mixed prefixes cause duplicates.
- **`scanner` comparing a file URL against `folder.path + "/filename"` substring.** The `/var/...` substring won't match a `/private/var/...` scanner result.

Rule of thumb: **any time a `URL` crosses a boundary between hand-constructed code and `FileManager`, canonicalize both sides.**

---

## What doesn't work

| Approach | Result on `/var/folders/...` | Why |
|----------|------------------------------|-----|
| `URL.resolvingSymlinksInPath()` | no-op | Ignores firmlinks by design. |
| `(path as NSString).resolvingSymlinksInPath` | no-op | Same underlying behavior as `URL`'s version. |
| `URL.standardized` / `URL.standardizedFileURL` | no-op | Collapses `..` and `.`, doesn't resolve firmlinks. |
| `realpath(1)` from a shell | **does** resolve | Shell tool uses a different resolution path than Foundation's `resolvingSymlinksInPath`. |
| `realpath(3)` C function | **does** resolve | Blessed mechanism; `canonicalPath` is built on top. |
| `URLResourceValues.canonicalPath` | **does** resolve | Official Foundation API. Requires the path to exist. |

---

## Caveats

- **Canonical path requires an existing file/directory.** `resourceValues(forKeys:)` on a non-existent path throws (or returns a value with nil `canonicalPath` depending on OS version). Resolve the *parent* (which exists, like `/var/folders/.../T`) and append the not-yet-created leaf onto it.
- **Don't canonicalize after each append.** Once the prefix is canonical, everything appended inherits it. Re-resolving per component is wasted stats.
- **Sandbox-scoped URLs:** security-scoped bookmark URLs you get from `NSOpenPanel` already come back canonical on modern macOS — you don't need to re-canonicalize them. But the *temp-dir* URLs constructed by your test code do.

---

## Related patterns

- **`38-destructive-copy-guard.md`** — `cp` pre-delete protection. The cookbook-canonical "same-file guard" for BSD-portable shell uses `cd + pwd` for the same reason `canonicalPath` exists in Swift: to reach one truth-form before comparing paths. Different runtimes, same underlying idea.
- **`43-subprocess-fire-and-collect.md`** — if your scanner writes fixture files and then spawns `ffprobe` against them (as the source project does), combine these two patterns.

---

## History

Discovered during 5.3 adversarial-test authoring on AvidMXFPeek. Three tests that checked `row.fileURL == expectedURL` failed under the full test suite while passing in isolation — concurrency was a red herring. The xcresult-level assertion dump (not visible in the stdout summary) showed `/private/var/...` vs `/var/...` and gave the game away. First attempt at a fix — `resolvingSymlinksInPath()` on the parent — was a no-op: firmlinks are opaque to it. `URLResourceValues.canonicalPath` landed the fix in one line.

The gotcha is load-bearing for any macOS code that builds test fixtures in `/var/folders/...` and later asserts URL equality — which is basically every test suite that exercises a file scanner.
