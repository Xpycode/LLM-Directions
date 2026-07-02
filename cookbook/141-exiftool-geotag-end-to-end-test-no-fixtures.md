# Verify an ExifTool geotag pass end-to-end with NO binary fixtures (timezone-robust)

**Tags:** ExifTool, -geotag, GPX, DateTimeOriginal, timezone, GeoMaxExtSecs, CGImageDestination, #filePath, exit 2

**Source:** PhotoIngest — `01_Project/PhotoIngest/PhotoIngestTests/GeotaggerTests.swift` (2026-06-28, T5.2 `Geotagger`). Pairs with [[140-xcodegen-folder-reference-vendor-cli-tool]] (how the exiftool tree gets into the bundle) — this is how you *prove the tagging actually works* in CI without committing a `.jpg`/`.gpx` to the repo.

## The problem
You wrap ExifTool's `-geotag` (write GPS to a copy by correlating capture time to a GPX track) and want a test that proves coordinates really land — not just that the argv looks right. Two things make the naive test either impossible-in-repo or flaky-across-machines:

1. **No binary assets.** You don't want a sample RAW/JPEG + GPX checked into git. Generate both at runtime.
2. **The silent timezone trap.** ExifTool reads the photo's `DateTimeOriginal` as a **local wall-clock** value and matches it against the GPX's **UTC** timestamps using the *test machine's* timezone. A GPX with one fix at exactly `12:00:00Z` matches a `12:00:00` photo in London and **misses by an hour in Stockholm** — the same test goes green on your Mac and red in CI, for a reason that has nothing to do with the code.

## The recipe

**1 — Generate a JPEG with ImageIO (no fixture file).** ExifTool will create the EXIF IFD when you write into it, so the pixels can be blank:
```swift
func makeBlankJPEG(at url: URL) throws {
    let w = 4, h = 4, space = CGColorSpaceCreateDeviceRGB()
    let ctx = CGContext(data: nil, width: w, height: h, bitsPerComponent: 8, bytesPerRow: 0,
                        space: space, bitmapInfo: CGImageAlphaInfo.noneSkipLast.rawValue)!
    ctx.setFillColor(CGColor(red: 0.5, green: 0.5, blue: 0.5, alpha: 1))
    ctx.fill(CGRect(x: 0, y: 0, width: w, height: h))
    let dest = CGImageDestinationCreateWithURL(url as CFURL, UTType.jpeg.identifier as CFString, 1, nil)!
    CGImageDestinationAddImage(dest, ctx.makeImage()!, nil)
    guard CGImageDestinationFinalize(dest) else { throw … }
}
```

**2 — Stamp a known capture time. The whole `Tag=value` is ONE argv element** — the space is literal because there's no shell (`Process`, not `/bin/sh`). Quoting it would write the quotes into the tag:
```swift
_ = try await runner.run(args: ["-DateTimeOriginal=2024:01:01 12:00:00", "-overwrite_original", jpg.path])
```

**3 — Defeat the timezone trap with a WIDE, single-coordinate GPX.** Sample one lat/lon every 10 min across **±16 h** around the nominal time. Any machine offset (max ±14 h, incl. half-hour zones) still lands the photo inside coverage, and because every fix shares the coordinate, the read-back value is deterministic regardless of *which* fix matched:
```swift
func makeWideGPX(at url: URL, lat: Double, lon: Double) throws {
    var cal = Calendar(identifier: .gregorian); cal.timeZone = TimeZone(identifier: "UTC")!
    let center = cal.date(from: DateComponents(year: 2024, month: 1, day: 1, hour: 12))!
    let iso = ISO8601DateFormatter(); iso.timeZone = TimeZone(identifier: "UTC")!
    var pts = "", off = -16*3600
    while off <= 16*3600 {
        pts += "<trkpt lat=\"\(lat)\" lon=\"\(lon)\"><ele>10</ele><time>\(iso.string(from: center.addingTimeInterval(Double(off))))</time></trkpt>\n"
        off += 600
    }
    try "<?xml version=\"1.0\"?>\n<gpx version=\"1.1\" xmlns=\"http://www.topografix.com/GPX/1/1\">\n<trk><trkseg>\n\(pts)</trkseg></trk>\n</gpx>".write(to: url, atomically: true, encoding: .utf8)
}
```
Set the profile's match window `≥` half the point spacing (`GeoMaxExtSecs ≥ 300` for 600 s spacing) so the nearest fix is always in range.

**4 — Verify from the BYTES, never the exit code.** Re-read GPS with `-json -n` (numeric) and classify from the file, because ExifTool's `-if "not $GPSLatitude"` guard returns **exit 2** when every file is skipped (already-tagged) — success, not failure ([[137-swift-subprocess-strings-line-cap-deadlock]] is the sibling subprocess gotcha):
```swift
let data = try await runner.run(args: ["-json", "-n", "-GPSLatitude", "-GPSLongitude", "-GPSCoordinates", jpg.path])
// parse JSON → GPSLatitude/Longitude (stills) or the "lat lon alt" GPSCoordinates composite (video)
XCTAssertEqual(coordinate.latitude,  59.3293, accuracy: 0.001)
XCTAssertEqual(coordinate.longitude, 18.0686, accuracy: 0.001)
```
ExifTool's JSON `SourceFile` echoes the path exactly as passed on the command line, so index records by `record["SourceFile"] as? String == url.path` — no symlink resolution needed.

## Why ±0.001° and not exact
`-n` returns full-precision decimals close to the track value, but interpolation/snap (`GeoMaxIntSecs=0`) and ExifTool's internal rounding shift the last digits. A `0.001°` tolerance (~110 m) is loose enough to never flake, tight enough to prove the *right* fix was used.

## Bonus: the no-coverage case
Stamp a time a year off the track and shrink the window (`GeoMaxExtSecs=30`) → read-back has no GPS → assert your wrapper reports `noTrackCoverage`. Pairs with the positive test to pin both branches of AC-13/AC-14.

**Locate the bundled tool in tests via `#filePath`**, not `Bundle.main` (which is the XCTest harness under `xcodebuild test`): step up from the test file to the repo `Resources/exiftool/exiftool`. Same trick the runner's own tests use.
