# Fast Preview + Heavy Commit Split

**Use when:** your app has both a live-updating preview **and** an expensive commit step (subprocess, network POST, disk-write-and-fsync). Naive approach wires both through the same async pipeline; slider/gesture-driven previews become laggy.

**Source:** `1-macOS/CVI/` (Sigil) — `IconRenderer.swift`, `VolumeDetailView.swift`.

---

## The split

Expose two entry points at the API level — full pipeline vs. last-in-memory step:

```swift
enum IconRenderer {
    /// Full pipeline: normalize → write iconset → run iconutil subprocess.
    /// Used on Apply. ~300 ms, writes .icns to disk.
    static func render(source: URL, mode: FitMode, zoom: Double = 1.0) async throws -> Data {
        if source.pathExtension.lowercased() == "icns" {
            return try Data(contentsOf: source)
        }
        let image = try ImageNormalizer.normalize(source: source, mode: mode, zoom: zoom)
        return try await renderInternal(image: image)  // runs iconutil
    }

    /// Fast path: returns the normalized NSImage only.
    /// Skips iconutil subprocess. Used for live slider feedback (~15 ms).
    static func preview(source: URL, mode: FitMode, zoom: Double) throws -> NSImage {
        if source.pathExtension.lowercased() == "icns" {
            guard let img = NSImage(contentsOf: source) else {
                throw ImageNormalizer.Error.unreadable(source)
            }
            return img
        }
        return try ImageNormalizer.normalize(source: source, mode: mode, zoom: zoom)
    }
}
```

## Synchronous UI wiring

Because `preview` is fast enough (<16 ms) and throws instead of `async throws`, the UI side can skip all `Task` + cancel infrastructure:

```swift
.onChange(of: pendingZoom) { _, _ in renderPreview() }
.onChange(of: pendingSource) { _, _ in renderPreview() }

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
        errorMessage = "Couldn't render preview: \(error.localizedDescription)"
    }
}
```

Each slider tick runs `renderPreview` to completion on the MainActor. No races, no stale tasks, no debouncing needed.

## Why it matters

Earlier versions of this code routed the preview through `IconRenderer.render` (the full subprocess pipeline) inside a `Task` with cancel-on-value-change. The result: a queue of in-flight `iconutil` processes behind every slider drag, each taking ~300 ms. Even with cancellation, the last visible preview often lagged the slider by 1–2 frames per tick.

Splitting the API into `render` (heavy, async) vs. `preview` (light, sync) removed the whole class of latency problems. The slider now feels native.

## Gotchas

- **Don't share the same Task infrastructure between preview and commit.** Different APIs, different cancellation semantics.
- **Preview may diverge slightly from final output.** `iconutil` generates multi-resolution `.icns` with its own mipmap rendering; the single-NSImage preview won't show pixel-level differences between sizes. Acceptable for framing previews; not for pixel-peeping.
- **Threshold for synchronous is ~16 ms.** Above that, go back to `async` + Task cancellation, or stream updates via `AsyncStream`.

## Generalization

The pattern applies to any app with:

| Preview step | Commit step |
|---|---|
| In-memory Core Image chain | Export PNG/JPEG to disk |
| Live markdown render | PDF via Pandoc/LaTeX subprocess |
| Mock HTTP response | Real POST to production API |
| Client-side diff highlight | Server-side `git commit` |

Keep the preview lightweight and synchronous; keep the commit full-fidelity and async.
