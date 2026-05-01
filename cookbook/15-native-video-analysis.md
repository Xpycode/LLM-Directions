## Native Video Analysis (AVFoundation)

### Shot/Scene Detection — Y-Plane Histogram Chi-Square

**Source:** `VideoScout/Services/NativeShotDetector.swift`
**Problem:** Shot boundary detection typically requires Python (PySceneDetect) or OpenCV — adding deployment burden for macOS apps. AVFoundation can decode video natively.

**Algorithm:** Stream frames via `AVAssetReader` in YCbCr format, compute 32-bin luminance histograms on the Y-plane, mark scene cuts when chi-square distance between consecutive frames exceeds a threshold.

```swift
actor NativeShotDetector {

    func detectShots(
        in videoURL: URL,
        threshold: Double = 27.0,     // chi-square threshold
        minSceneLength: Double = 3.0  // merge cuts closer than this
    ) async throws -> [SceneResult] {
        let asset = AVURLAsset(url: videoURL)
        guard let track = try await asset.loadTracks(withMediaType: .video).first else {
            throw DetectionError.noVideoTrack
        }

        let fps = Double(try await track.load(.nominalFrameRate))
        let totalSeconds = CMTimeGetSeconds(try await asset.load(.duration))

        let reader = try AVAssetReader(asset: asset)
        let output = AVAssetReaderTrackOutput(track: track, outputSettings: [
            kCVPixelBufferPixelFormatTypeKey as String:
                kCVPixelFormatType_420YpCbCr8BiPlanarVideoRange
        ])
        output.alwaysCopiesSampleData = false
        reader.add(output)
        guard reader.startReading() else { throw DetectionError.readerFailed("...") }

        var prevHistogram: [Double]?
        var cuts: [Double] = []

        while let sample = output.copyNextSampleBuffer() {
            guard let px = CMSampleBufferGetImageBuffer(sample) else { continue }
            let time = CMTimeGetSeconds(CMSampleBufferGetPresentationTimeStamp(sample))
            let hist = yPlaneHistogram(from: px)
            if let prev = prevHistogram, chiSquare(prev, hist) > threshold {
                cuts.append(time)
            }
            prevHistogram = hist
        }
        reader.cancelReading()

        // merge close cuts, build SceneResult array from boundaries
        return buildScenes(from: mergeCuts(cuts, minGap: minSceneLength),
                           duration: totalSeconds, fps: fps)
    }

    /// 32-bin histogram on Y-plane, normalized to percentage (sum ≈ 100)
    private func yPlaneHistogram(from px: CVPixelBuffer) -> [Double] {
        CVPixelBufferLockBaseAddress(px, .readOnly)
        defer { CVPixelBufferUnlockBaseAddress(px, .readOnly) }

        guard let base = CVPixelBufferGetBaseAddressOfPlane(px, 0) else {
            return [Double](repeating: 0, count: 32)
        }
        let w = CVPixelBufferGetWidthOfPlane(px, 0)
        let h = CVPixelBufferGetHeightOfPlane(px, 0)
        let bpr = CVPixelBufferGetBytesPerRowOfPlane(px, 0)

        var hist = [Double](repeating: 0, count: 32)
        var count = 0
        for y in Swift.stride(from: 0, to: h, by: 4) {       // subsample 4x
            let row = base.advanced(by: y * bpr)
            for x in Swift.stride(from: 0, to: w, by: 4) {
                let lum = row.load(fromByteOffset: x, as: UInt8.self)
                hist[min(Int(Double(lum) * 32.0 / 256.0), 31)] += 1
                count += 1
            }
        }
        if count > 0 { let s = 100.0 / Double(count); for i in 0..<32 { hist[i] *= s } }
        return hist
    }

    /// χ² = Σ (a[i] - b[i])² / (a[i] + b[i])
    private func chiSquare(_ a: [Double], _ b: [Double]) -> Double {
        var d = 0.0
        for i in 0..<a.count {
            let s = a[i] + b[i]
            if s > 0 { let diff = a[i] - b[i]; d += diff * diff / s }
        }
        return d
    }
}
```

**Key design choices:**
- **YCbCr pixel format** — `kCVPixelFormatType_420YpCbCr8BiPlanarVideoRange` decodes natively (no color space conversion). Plane 0 = pure luminance.
- **4x subsampling** — Every 4th pixel in both dimensions. 1920×1080 → ~130K samples per frame. Sufficient for histogram accuracy, ~3ms/frame on Apple Silicon.
- **Percentage normalization** — Histogram bins sum to ≈100 (not 1.0). This gives chi-square distances in a range where 27.0 is a meaningful default threshold, regardless of video resolution.
- **Threshold mapping** — If exposing a user-facing sensitivity slider (e.g. 1–10), multiply by 9 to get chi-square threshold. Default 3.0 → 27.0.
- **Post-processing** — Merge cuts closer than `minSceneLength` seconds to avoid detecting flicker/flash as boundaries.
- **Performance** — ~2–5ms/frame. A 30fps, 1-hour video ≈ 108K frames ≈ 3–9 minutes.

---

### Motion Scoring — Frame Differencing on Y-Plane

**Source:** `VideoScout/Services/NativeMotionAnalyzer.swift`
**Problem:** Optical flow (Farneback) requires OpenCV. For a scalar "how much motion" score, frame differencing on luminance is equivalent.

```swift
actor NativeMotionAnalyzer {
    func analyzeMotion(
        in videoURL: URL, startTime: Double, endTime: Double, sampleRate: Int = 5
    ) async throws -> MotionResult {
        // Same AVAssetReader setup as above, with:
        //   reader.timeRange = CMTimeRange(start:..., end:...)
        // For every Nth frame: extract subsampled Y-plane, compute mean
        // absolute pixel difference with previous frame, normalize by 255.
        // Average all pair scores → motionScore (0.0–1.0)
    }
}
```

**Motion categories** (thresholds for the 0.0–1.0 score):
| Range | Category |
|-------|----------|
| < 0.05 | static |
| 0.05–0.2 | slow |
| 0.2–0.5 | moderate |
| ≥ 0.5 | fast |

**Why not optical flow:** Farneback optical flow gives direction vectors (useful for tracking). If you only need magnitude (scalar score), mean absolute pixel difference gives equivalent categorization with zero external dependencies.

---

