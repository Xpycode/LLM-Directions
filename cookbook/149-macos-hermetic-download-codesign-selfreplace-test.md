# Hermetically test a macOS download → codesign-check → self-replace flow (no network, no mocks, no real apps)

**Source:** AppUpdater — `01_Project/AppUpdaterPackage/Tests/AppUpdaterFeatureTests/SparkleExecutorEndToEndTests.swift` (2026-07-01, Wave 5). Proves `SparkleExecutor.downloadAndInstall(...)` — the download→EdDSA-verify→extract→Team-ID-check→quit→Trash→swap flow — end to end. Pairs with [[150-sparkle-eddsa-cryptokit-silent-selfupdate]] (the flow being tested).

## The problem
You have code that downloads an archive over the network, checks its code signature, and replaces an installed `.app` on disk. Every instinct says "that's not unit-testable" — it hits the network, shells out to `codesign`, and mutates real bundles. So it ends up covered only by a crypto unit test in isolation, and the *orchestration* (the part that actually deletes and swaps files) ships untested. That orchestration is exactly the part that can eat a user's app.

You can test the whole thing hermetically — no network, no mock objects, no touching the user's real apps — with three macOS-specific tricks.

## The three tricks

**1 — `URLSession.download(from:)` accepts `file://` URLs.** Point the "download" at a locally-synthesized archive and the real download code path runs with zero network:
```swift
let update = UpdateInfo(downloadURL: localZipURL /* file:// */, edSignature: sigB64, archiveLength: bytes, …)
```
No `URLProtocol` subclass, no injected networking seam. The production code doesn't even know it isn't talking to a server.

**2 — Ad-hoc code-sign a throwaway `.app` at runtime.** `codesign -s -` (the `-` identity = ad-hoc) validates cleanly under `SecStaticCodeCheckValidityWithErrors`, and carries **`TeamIdentifier=not set`**. So if your "same developer" check compares Team-IDs, both sides are `nil`, `nil == nil` passes, and you never need a real Developer ID cert in the test:
```swift
// verified assumptions (probe before you build on them):
//   codesign -s - --force Dummy.app        → exit 0
//   codesign --verify --strict Dummy.app   → "valid on disk"
//   codesign -d --verbose=4 Dummy.app      → TeamIdentifier=not set
```
Build the bundle from Swift: a `Contents/MacOS/<exec>` shell script (`#!/bin/sh\nexit 0`, chmod 0755) + a `Contents/Info.plist` with `CFBundleExecutable`/`CFBundleIdentifier`/`CFBundleShortVersionString`. That's a launchable, signable app.

**3 — `ditto -c -k --keepParent` preserves the signature across the zip round-trip.** A shell-script main executable stores its signature in **extended attributes** (scripts can't embed a signature in a Mach-O). Plain `zip` drops xattrs and the signature vanishes on extraction. `ditto` (both directions) preserves them — and it's the exact tool Sparkle-style zips are made and unpacked with:
```swift
// make:    ditto -c -k --keepParent  MyApp.app  update.zip
// extract: ditto -x -k               update.zip destDir
codesign --verify --strict destDir/MyApp.app   // still "valid on disk" ✅
```
Sign the archive's *bytes* (EdDSA/whatever) **after** the `ditto -c -k`, since that's the file that gets downloaded and verified.

## Two assertions that matter
- **Happy path proves the swap really happened** — don't assert on the return value alone; read the on-disk bundle's `CFBundleShortVersionString` back and check it flipped to the new version. The value moving from `1.0.0`→`2.0.0` is the only proof the file was actually replaced.
- **Tamper path proves the safety invariant** — corrupt one byte *after* signing, expect the install to throw, then assert the on-disk version is **still the old one**. This is the test that proves a bad download can't clobber a good app. It's more valuable than the crypto unit test because it exercises the abort-before-replace ordering in the real orchestration.

## The one side effect to clean up
If the flow moves the old app to the Trash (`FileManager.trashItem` — a good "undo" design), the test litters `~/.Trash`. Production discards the resulting-URL, so you can't read it back. Fix: name the fixture bundle uniquely (`MyApp-<uuid>.app`) and delete `~/.Trash/<thatName>` in teardown:
```swift
func cleanUp() {
    try? FileManager.default.removeItem(at: tempRoot)
    let trashed = FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent(".Trash/\(bundleName)")
    try? FileManager.default.removeItem(at: trashed)   // the successful run's original
}
```

## Gotchas
- `UpdateExecutionResult`-style enums with associated values aren't `Equatable` — match with `if case .installedSilently = result {} else { Issue.record(…) }`, not `==`.
- A public struct's memberwise init is `internal`; fine from tests via `@testable import`.
- Probe the CLI assumptions (`codesign`, `ditto`) in a shell **before** writing the Swift — measure twice. All three tricks above were shell-verified first.
- These are integration tests (they run real subprocesses). They're fast (~0.1 s each) and hermetic, but they assume `/usr/bin/codesign` and `/usr/bin/ditto` exist — always true on macOS, absent on Linux CI. Gate the suite to macOS.
