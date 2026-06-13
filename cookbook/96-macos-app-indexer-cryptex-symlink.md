# 96 — macOS app indexer silently misses Safari (and Cryptex system apps) → `contentsOfDirectory(at:)` drops symlinks, use the path variant

**Extracted from:** LaunchAway (2026-06-13)

You scan `/Applications`, `/System/Applications`, `/System/Applications/Utilities`, `~/Applications` for `.app` bundles to build a launcher/index. It finds 96 apps, everything looks right — but **Safari never appears** (typing "saf" matches "Kagi for Safari" but not Safari itself). Other system apps may be missing too. The matcher, the engine, the ranking are all provably correct; the candidate set simply doesn't contain Safari.

## Why it happens

On modern macOS (Big Sur+, and very much macOS 26 Tahoe), system apps like Safari live on the **read-only, SSV-sealed system volume inside a Cryptex** and are surfaced into `/Applications` via a **symlink**:

```
/Applications/Safari.app -> ../System/Cryptexes/App/System/Applications/Safari.app
```

The trap: the **URL-based** directory enumerator silently omits that symlink.

```swift
// URL variant — DROPS the Safari symlink. Returns 47 entries where `ls` shows 48.
let entries = try? fm.contentsOfDirectory(
    at: URL(fileURLWithPath: "/Applications"),
    includingPropertiesForKeys: [.isDirectoryKey],
    options: [.skipsHiddenFiles, .skipsSubdirectoryDescendants]
)
// entries.contains { $0.lastPathComponent == "Safari.app" }  → false
```

`ls -la /Applications` shows `Safari.app` (as `lrwxr-xr-x … -> ../System/Cryptexes/…`), and `find /Applications -maxdepth 1 -type l -name '*.app'` finds it — but `FileManager.contentsOfDirectory(at:includingPropertiesForKeys:options:)` does not return it. The URL enumerator prefetches the requested resource keys and, resolving `.isDirectoryKey` across the Cryptex mount for a symlink whose own `isDirectory` reports **false**, drops the entry. The symlink itself is perfectly readable — `Bundle(url:)` resolves it and returns `CFBundleIdentifier = com.apple.Safari` with a full `infoDictionary`. The **only** thing broken is the enumeration step.

## The fix — enumerate with the path-based API

`contentsOfDirectory(atPath:)` returns plain names (like `ls`) and **includes symlinks**. Map them back to URLs; `Bundle(url:)` / `NSWorkspace` / `openApplication(at:)` all resolve the symlink downstream with no extra work.

```swift
private func topLevelApps(in root: URL, using fm: FileManager) -> [URL] {
    guard let names = try? fm.contentsOfDirectory(atPath: root.path) else { return [] }
    return names
        .filter { !$0.hasPrefix(".") && $0.lowercased().hasSuffix(".app") }  // .skipsHiddenFiles equivalent
        .map { root.appendingPathComponent($0) }
}
```

That's it — Safari now indexes (`AppIndexer found com.apple.Safari? true name=Safari`). No need to resolve the symlink target yourself: launching `/Applications/Safari.app` (the symlink) via `NSWorkspace.shared.openApplication(at:)` works, and `NSWorkspace.shared.icon(forFile:)` / `url.resourceValues(forKeys: [.localizedNameKey])` return the right name + icon through it.

## How to confirm (don't trust the count, diff it)

The tell is a **count mismatch between the shell and FileManager**:

```bash
ls -1 /Applications | grep -c '\.app$'                          # 48  (shell sees the symlink)
find /Applications -maxdepth 1 -type l -name '*.app'            # /Applications/Safari.app
```

```swift
// In code: the URL enumerator under-counts by exactly the symlinked system apps.
let viaURL  = (try? fm.contentsOfDirectory(at: root, includingPropertiesForKeys: [.isDirectoryKey], options: [.skipsHiddenFiles, .skipsSubdirectoryDescendants]))?.count ?? 0
let viaPath = (try? fm.contentsOfDirectory(atPath: root.path))?.filter { $0.hasSuffix(".app") }.count ?? 0
// viaPath > viaURL  → you're dropping symlinked bundles.
```

## Notes / caveats

- **`.skipsHiddenFiles` has no path-API equivalent** — replicate it with `!name.hasPrefix(".")`. `.skipsSubdirectoryDescendants` is moot: the path API is already non-recursive (single level).
- **You lose cheap property prefetch.** The URL variant could prefetch `.isDirectoryKey`; the path variant can't. Fine for an app indexer that reads `Bundle(url:)`/`resourceValues` per candidate anyway.
- **Dedup still matters.** Safari may also appear under `/System/Cryptexes/App/System/Applications/` if you ever scan there — dedup by `CFBundleIdentifier` (you already should, for `/Applications` vs `/System/Applications` overlaps).
- **General rule:** to enumerate a macOS directory the way the user/Finder sees it (symlinks included), prefer `contentsOfDirectory(atPath:)`; reach for the URL variant only when you genuinely need batched resource-key prefetch and know the directory has no meaningful symlinks.

Source: LaunchAway `01_Project/LaunchAway/Index/AppIndexer.swift` (`topLevelApps`). Pairs with #74/#75 (permission-free system enumeration), #52 (appendingPathComponent FS-probe), #97 (the stderr-capture technique that surfaced this), #00 (App Shell Standard).
