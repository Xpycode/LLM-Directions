## Debounced CIFilter Preview Cache

**Source:** `1-macOS/CropBatch/` — `BlurEditorView.swift` (v1.5)

When you need live preview of Core Image filters (blur, pixelate, etc.) in SwiftUI but applying CIFilter per-frame is too expensive. Pre-render all effects into a single composite at display resolution, then clip from it.

```swift
@Observable
final class FilterPreviewCache {
    var cachedImage: NSImage?
    private var cachedHash: Int = 0
    private var debounceTask: Task<Void, Never>?

    @MainActor
    func scheduleUpdate(source: NSImage, regions: [BlurRegion],
                        displaySize: CGSize, transform: ImageTransform) {
        let newHash = computeHash(regions: regions, size: displaySize)
        guard newHash != cachedHash else { return }

        debounceTask?.cancel()
        let captured = (regions, displaySize, transform, newHash)

        debounceTask = Task { @MainActor in
            try? await Task.sleep(for: .milliseconds(100))
            guard !Task.isCancelled else { return }
            // Downscale to display resolution — 2MP vs 8MP original
            let scaled = createDisplayResolutionImage(from: source, size: captured.1)
            // Transform regions from original to display coords
            let transformed = captured.0.map { r in
                BlurRegion(normalizedRect: r.normalizedRect.applyingTransform(captured.2),
                           style: r.style, intensity: r.intensity)
            }
            cachedImage = ImageCropService.applyBlurRegions(scaled, regions: transformed)
            cachedHash = captured.3
        }
    }

    @MainActor func invalidate() {
        debounceTask?.cancel()
        cachedImage = nil
        cachedHash = 0
    }
}
```

**In the view — cache hit vs. SwiftUI fallback:**

```swift
// previewContent for a blur region overlay:
if let cached = cachedBlurImage {
    // Cache hit: clip from pre-composited image (no .blur() needed)
    Image(nsImage: cached)
        .resizable()
        .frame(width: fullWidth, height: fullHeight)
        .offset(x: -regionRect.minX, y: -regionRect.minY)
        .frame(width: regionRect.width, height: regionRect.height)
        .clipped()
} else {
    // Cache miss (first frame / rapid drag): SwiftUI fallback
    Image(nsImage: originalImage)
        .resizable()
        .frame(width: fullWidth, height: fullHeight)
        .blur(radius: 30 * intensity)
        .offset(x: -regionRect.minX, y: -regionRect.minY)
        .frame(width: regionRect.width, height: regionRect.height)
        .clipped()
}
```

**Why it works:**
- Display-resolution (~2MP) processes in 5-15ms per region via GPU-backed `CIContext`
- 100ms debounce prevents thrashing during slider drags
- SwiftUI `.blur()` fallback gives zero-latency first frame
- Single composite means 5 regions = 1 image layer (not 5 full-blurred layers)
- Preview matches export exactly (same `CIGaussianBlur`/`CIPixellate` pipeline)

**Trigger:** Any time you need live CIFilter preview with multiple regions and an intensity slider.

---

