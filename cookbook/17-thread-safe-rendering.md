## Thread-Safe Offscreen Rendering

**Problem:** `NSImage.lockFocus()` is main-thread-only. Using it from `TaskGroup` background tasks causes crashes or corrupted output.

**Solution:** Use `NSBitmapImageRep` + `NSGraphicsContext(bitmapImageRep:)` for an isolated offscreen context.

```swift
// Thread-safe: each task gets its own isolated context
guard let rep = NSBitmapImageRep(
    bitmapDataPlanes: nil,
    pixelsWide: width,
    pixelsHigh: height,
    bitsPerSample: 8,
    samplesPerPixel: 4,
    hasAlpha: true,
    isPlanar: false,
    colorSpaceName: .deviceRGB,
    bytesPerRow: 0,
    bitsPerPixel: 0
) else { return image }
guard let ctx = NSGraphicsContext(bitmapImageRep: rep) else { return image }

// Draw source image via CGContext (thread-safe)
let cgContext = ctx.cgContext
cgContext.draw(sourceCGImage, in: CGRect(origin: .zero, size: imageSize))

// For NSAttributedString.draw, temporarily set NSGraphicsContext.current
// (per-thread TLS — safe when synchronous blocks don't cross await points)
let saved = NSGraphicsContext.current
NSGraphicsContext.current = ctx
attrString.draw(in: drawRect)
NSGraphicsContext.current = saved

guard let result = rep.cgImage else { return image }
return NSImage(cgImage: result, size: imageSize)
```

**Key insight:** `NSGraphicsContext.current` is per-thread TLS. Synchronous blocks in `TaskGroup` run to completion on one thread — no interleaving. The real danger is `lockFocus()` which creates screen-backed windows.

**Source:** CropBatch `ImageCropService.applyTextWatermark` (2026-03-29)

---

