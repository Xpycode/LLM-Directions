## Pipeline Extraction Pattern

**Problem:** Multiple code paths reimplement the same processing pipeline (e.g., normal export vs. rename-on-conflict export). Pipelines drift apart — one path adds a step, the other doesn't.

**Solution:** Extract the pipeline into a method that returns processed results WITHOUT saving. Callers handle I/O (URL construction, saving) independently.

```swift
// Shared pipeline — single source of truth
static func processImageThroughPipeline(
    item: ImageItem,
    settings: ProcessingSettings
) throws -> [(gridPosition: (row: Int, col: Int)?, image: NSImage, format: UTType)] {
    var image = item.originalImage
    // Step 1: blur, Step 2: transform, Step 3: crop, Step 4: mask
    // Step 5: grid split, Step 6: per-tile resize + watermark
    // Step 7: resolve format
    return tiles  // No saving — caller decides where/how to write
}

// Normal export path
func processSingleImage(...) throws -> [URL] {
    let tiles = try processImageThroughPipeline(...)
    return tiles.map { tile in
        let url = buildOutputURL(...)     // caller controls naming
        try save(tile.image, to: url)
        return url
    }
}

// Rename-on-conflict path
func processConflicting(...) throws -> [URL] {
    let tiles = try processImageThroughPipeline(...)  // same pipeline!
    return tiles.map { tile in
        let url = buildRenamedURL(...)    // different naming strategy
        try save(tile.image, to: url)
        return url
    }
}
```

**Rule:** If two code paths share >3 processing steps, extract the pipeline. Let callers own I/O.

**Source:** CropBatch `ImageCropService.processImageThroughPipeline` (2026-03-31)

---

