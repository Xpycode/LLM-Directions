# Effective Source Fallback in Editors

**Use when:** an editor operates on either a freshly-picked file (drop / Browse) **or** an already-persisted one loaded from cache. Typical case: asset editors where changing framing / settings of a previously-saved item shouldn't require re-importing the source.

**Source:** `1-macOS/CVI/` (Sigil) — `VolumeDetailView.swift`, `IconCache.swift`.

---

## The problem

Editor state has two possible inputs:

- `pendingSource: URL?` — user just picked a new file this session
- `cachedSource: URL?` — previously-applied source, loaded when the record is selected

Branching on `pendingSource != nil` in every render/apply/validate path gets unwieldy. The fix: collapse to a single derived URL.

```swift
/// Pending (user-picked) takes precedence over cached. When neither is
/// set, the editor shows the empty state.
private var effectiveSource: URL? {
    pendingSource ?? cachedSource
}

/// Some ops don't make sense on already-rasterized inputs (e.g. .icns).
private var isZoomableSource: Bool {
    guard let src = effectiveSource else { return false }
    return src.pathExtension.lowercased() != "icns"
}
```

## Loading cached source on selection

When the record is selected, resolve any cached source and stash it. The cache helper returns `nil` if none exists (legacy records, reset volumes, etc.).

```swift
private func loadInitialState(for info: VolumeInfo) {
    if let id = info.identity,
       let record = appState.remembered.first(where: { $0.identity == id }) {
        pendingMode = record.fitMode
        pendingZoom = record.zoom
        cachedSource = try? IconCache.sourceURL(for: id)
    } else {
        pendingMode = .fit
        pendingZoom = 1.0
        cachedSource = nil
    }
    pendingSource = nil
    renderPreview()  // uses effectiveSource
}
```

## Dirty detection for the commit gate

Apply should be enabled when *either* the user picked a new file *or* they moved settings away from what's stored. Prevents no-op re-applies:

```swift
private func canApply(_ info: VolumeInfo) -> Bool {
    guard !isApplying else { return false }
    guard let id = info.identity else { return false }
    if pendingSource != nil { return true }        // new file always applies
    guard let cached = cachedSource,
          cached.pathExtension.lowercased() != "icns" else { return false }
    guard let record = appState.remembered.first(where: { $0.identity == id }) else { return false }
    return pendingMode != record.fitMode || pendingZoom != record.zoom
}
```

## Commit reads through `effectiveSource`

```swift
private func performApply(_ info: VolumeInfo) async {
    guard let source = effectiveSource else { return }
    try await appState.applyIcon(source: source,
                                  mode: pendingMode,
                                  zoom: pendingZoom,
                                  to: info)
}
```

## Self-healing on missing cache

If the cached file disappears externally (another app deleted it, disk issue), clear the stale reference so later renders don't re-fail:

```swift
private func renderPreview() {
    guard let source = effectiveSource else {
        previewImage = nil
        return
    }
    do {
        previewImage = try IconRenderer.preview(source: source,
                                                mode: pendingMode,
                                                zoom: pendingZoom)
        errorMessage = nil
    } catch {
        previewImage = nil
        if pendingSource == nil, let cached = cachedSource,
           !FileManager.default.fileExists(atPath: cached.path) {
            cachedSource = nil  // drop stale reference
            errorMessage = nil
        } else {
            errorMessage = "Couldn't render preview: \(error.localizedDescription)"
        }
    }
}
```

## Why it matters

Without this fallback, a user who wants to tweak framing of an already-applied asset is forced to re-import the file — even though the app already has a copy. `pending ?? cached` makes the editor feel **live** on persisted data while preserving the usual drop-to-replace UX on top.

## Storage requirement

The cache needs to hold the original source (not just the rendered output). Pattern — store source alongside output, discover via directory scan:

```swift
// Save source with identity-prefixed filename
static func saveSource(_ sourceURL: URL, for identity: VolumeIdentity) throws -> URL {
    let ext = sourceURL.pathExtension.lowercased()
    let destURL = try iconsDir().appendingPathComponent("\(identity.raw).src.\(ext)")
    // ... (see cookbook 38 for the same-file guard)
    try FileManager.default.copyItem(at: sourceURL, to: destURL)
    return destURL
}

// Look up by prefix (extension is unknown at read time)
static func sourceURL(for identity: VolumeIdentity) throws -> URL? {
    let dir = try iconsDir()
    let prefix = "\(identity.raw).src."
    let contents = (try? FileManager.default.contentsOfDirectory(atPath: dir.path)) ?? []
    guard let name = contents.first(where: { $0.hasPrefix(prefix) }) else { return nil }
    return dir.appendingPathComponent(name)
}
```

## Related

- **cookbook 36**: pair this with the fast-preview-heavy-commit split so slider changes on a cached source feel live.
- **cookbook 38**: `saveSource` must guard against `src == dest` — re-apply from cache passes the already-cached URL back through this function.
