## Subprocess & URL Patterns

### URL Path for Subprocesses — Avoid `url.path()`

**Source:** `CutSnaps/Services/FFmpegService.swift`
**Problem:** Swift's `URL.path()` method (macOS 13+) defaults to `percentEncoded: true`, encoding spaces as `%20`. When passed to `Foundation.Process` or any subprocess, the path is garbled.

```swift
// BAD — spaces become %20, subprocess gets "No such file"
let args = ["-i", url.path()]

// GOOD — decoded path, spaces preserved
let args = ["-i", url.path(percentEncoded: false)]

// Also applies to embedded paths in filter strings:
let filter = "metadata=print:file=\(tempFile.path(percentEncoded: false))"
```

**Why it's subtle:** The deprecated `url.path` property (no parens) auto-decodes. The new `url.path()` method does not. Migrating from `.path` to `.path()` silently breaks paths with spaces.

---

### Security-Scoped Access Across Async Pipelines

**Source:** `CutSnaps/Models/VideoFile.swift`
**Problem:** File pickers and drag-and-drop grant security-scoped access, but calling `stopAccessingSecurityScopedResource()` before an async pipeline completes kills access for the entire chain.

```swift
// BAD — access revoked before async processing finishes
for url in urls {
    let accessing = url.startAccessingSecurityScopedResource()
    importVideo(url: url)  // enqueues async work
    if accessing { url.stopAccessingSecurityScopedResource() }  // too early!
}

// GOOD — manage access lifecycle on the model
@Observable
class VideoFile: Identifiable {
    let url: URL
    private var isAccessingSecurityScope = false

    func startAccess() {
        guard !isAccessingSecurityScope else { return }
        isAccessingSecurityScope = url.startAccessingSecurityScopedResource()
    }

    func stopAccess() {
        guard isAccessingSecurityScope else { return }
        url.stopAccessingSecurityScopedResource()
        isAccessingSecurityScope = false
    }

    deinit {
        if isAccessingSecurityScope {
            url.stopAccessingSecurityScopedResource()
        }
    }
}

// Call startAccess() on import, stopAccess() when processing completes or model removed
```

**Rule:** If `startAccessingSecurityScopedResource()` and the work using that resource are on different async boundaries, the access token must outlive the async chain.

---

