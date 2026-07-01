# Verify a Sparkle appcast update with CryptoKit (no Sparkle.framework) + swap the app in safely

**Source:** AppUpdater — `01_Project/AppUpdaterPackage/Sources/AppUpdaterFeature/Services/{SparkleSignatureVerifier,SparkleExecutor,CodeSigningVerifier,AppQuitter}.swift` (2026-07-01, Waves 1–4). For a tool that *checks other apps' updates* MacUpdater-style, not an app self-updating via its own Sparkle. Existing [[16-sparkle-auto-updates]] is the opposite case (integrating Sparkle.framework into your own app). Test it hermetically with [[150-sparkle-eddsa-cryptokit-silent-selfupdate]]'s sibling, [[149-macos-hermetic-download-codesign-selfreplace-test]].

## Why not just link Sparkle?
Sparkle.framework self-updates *the app it's embedded in*. If you're building an updater that installs updates *for other people's apps*, you can't embed their Sparkle — you only have their appcast URL (`SUFeedURL`) and their public key (`SUPublicEDKey`, both in the target app's `Info.plist`). You re-implement just the verify + install, and it's small.

## 1 — Verify the EdDSA signature with CryptoKit
Sparkle 2 signs the **raw archive bytes** with Ed25519. `sparkle:edSignature` (base64, 64 bytes) is in the appcast `<enclosure>`; `SUPublicEDKey` (base64, 32 bytes) is in the installed app's `Info.plist`. That's a plain `Curve25519.Signing` check — no framework:
```swift
import CryptoKit
let key = try Curve25519.Signing.PublicKey(rawRepresentation: Data(base64Encoded: suPublicEDKey)!)
let sig = Data(base64Encoded: edSignatureBase64)!
let bytes = try Data(contentsOf: archiveURL, options: .mappedIfSafe)   // mmap — DMGs are 100+ MB
guard key.isValidSignature(sig, for: bytes) else { throw .signatureMismatch }
```
Do it in an `actor`, off the main thread — the read+verify of a large DMG blocks.

## 2 — The verify-order that makes silent install safe
The whole point is nothing destructive happens until every check passes. Order is the security property:
```
1. download to temp (file size == appcast `length`?  guards truncation)
2. EdDSA verify over archive bytes            ← present-but-bad = HARD ABORT, never a fallback
3. extract (ditto -xk / hdiutil for dmg / tar -xJf for tar.xz)
4. codesign Team-ID of extracted .app == Team-ID of installed .app   ← second, independent floor
5. strip com.apple.quarantine  (xattr -dr) — safe, we just verified it two ways
6. quit the running app  (see §3)
7. move CURRENT app → ~/.Trash   (recoverable undo, not an adjacent _backup)
8. move NEW app into place; on failure, restore from Trash
```
Two independent trust floors (EdDSA *and* Team-ID match) matter: EdDSA proves the download matches what the vendor signed; Team-ID match proves the extracted bundle is signed by the *same developer* as the app already installed. Either alone is weaker.

**D1 — no `edSignature` in the appcast?** Don't silently install on Team-ID alone. Fall back to launching the app's own updater. Team-ID match confirms *who signed it*, not *that the bytes weren't swapped in transit*.

**D3 — target in `/Applications` (not user-writable)?** Detect with `FileManager.isWritableFile(atPath: parentDir)` and fall back to launch-for-update; a privileged `SMAppService` helper is a separate, much larger security surface. User-writable locations (`~/Applications`, `~/Downloads`) install silently.

## 3 — Quit the running app without a bail-out
`NSRunningApplication.terminate()` returns **false when Automation (Apple Events) TCC is denied** — the quit event was never delivered. Treat that as "skip to force-terminate", not "it's quitting":
```swift
let apps = NSRunningApplication.runningApplications(withBundleIdentifier: bundleID)
if apps.isEmpty { return .alreadyQuit }
let delivered = apps.reduce(false) { $0 || $1.terminate() }   // false ⇒ TCC denied
if delivered { /* poll .isTerminated up to 10s */ }
apps.filter { !$0.isTerminated }.forEach { $0.forceTerminate() }   // poll ~2s more
```
Needs `NSAppleEventsUsageDescription` + entitlement `com.apple.security.automation.apple-events`. The TCC prompt fires once, then macOS caches consent.

## Gotchas
- **Signature is over the archive bytes, format-agnostic** — verify the `.zip`/`.dmg`/`.tar.xz` as downloaded; don't extract first.
- **Vendor rotates their EdDSA key** → the `SUPublicEDKey` baked into the *installed* Info.plist is stale and verification fails forever. This is a real Sparkle edge case, not your bug — surface it as `signatureMismatch` and fall back to launch-for-update.
- **`~/.Trash` move fails on some network mounts** — fall back to an adjacent temp dir you delete on success.
- **`isWritableFile` is the cheap correct gate** for the admin-required decision — don't try the move and catch EPERM after you've already trashed the original.
