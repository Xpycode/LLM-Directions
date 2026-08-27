# 182 — A SwiftPM *source* target adds zero notarization surface: verify with `otool`, not intuition

**Tags:** libwebp, libwebp-Xcode, SwiftPM, SPM source target, static linking, otool -L, notarization, hardened runtime, xcodegen packages, binaryTarget, XCFramework, cwebp

**Extracted from:** Images2WebP (2026-08-27)

## The problem

"Bundling a C library means another binary to sign and declare for notarization" is a reasonable
assumption and often wrong. It holds for an XCFramework, a `.dylib`, or a bundled CLI. It does
**not** hold for a Swift package that declares a plain `.target` over C sources — SwiftPM compiles
those into your app binary and links them **statically**. There is nothing extra in the bundle,
so there is nothing extra to sign, and notarization is unchanged.

Assuming otherwise pushes you toward the worse option (a bundled CLI, a prebuilt framework) to
avoid a cost that was never there.

## How to tell which kind of package you have

Read its `Package.swift` before deciding anything. The distinction is one keyword:

```swift
// SOURCE target -> compiled into your binary, static, no bundle artifact.
.target(
    name: "libwebp",
    path: ".",
    sources: ["libwebp/src", "libwebp/sharpyuv"],   // <- real C sources
    publicHeadersPath: "include",
    cSettings: [.headerSearchPath("libwebp")]
)

// BINARY target -> a prebuilt artifact that DOES land in the bundle and DOES need signing.
.binaryTarget(name: "Something", url: "...", checksum: "...")
```

Also check whether the vendored code is a **git submodule of upstream** rather than a fork —
`SDWebImage/libwebp-Xcode` points `libwebp` at `webmproject/libwebp`, so you compile Google's
source at a tag that tracks upstream, not somebody's snapshot.

## Wiring it (xcodegen)

```yaml
packages:
  libwebp:
    url: https://github.com/SDWebImage/libwebp-Xcode
    from: "1.6.0"

targets:
  YourApp:
    dependencies:
      - package: libwebp
        product: libwebp
```

## Verify — the whole point of the pattern

Do not conclude "statically linked" from the package manifest. Check the built product:

```bash
otool -L "$APP/Contents/MacOS/YourApp" | grep -i webp   # expect: no output
find "$APP" -name "*webp*"                              # expect: no output
```

No dynamic reference and no file in the bundle means the encoder is part of the app binary,
universal for whatever architectures you already build, with no separate signing step.

## Prove the library actually works before adopting it

A one-file SwiftPM executable settles resolution, submodule fetch, compilation on your real
toolchain, and the C interop in about a minute — cheaper than discovering any of it inside an app
target. Verify the *output* with an independent decoder (`file`, `dwebp`) rather than trusting the
encoder's own non-zero return.

## Rejected alternatives, and why

- **Bundled `cwebp` CLI** — spawns a process per file (bad across a batch), turns error handling
  into string parsing, and genuinely *does* add a signed executable to the bundle.
- **Vendored XCFramework** — must be rebuilt and re-signed per upstream release, with worse
  provenance than compiling upstream source.
- **Homebrew's copy** — `/opt/homebrew` paths are not distributable and not signed by you. Keep it
  as a *test oracle* (`dwebp` verifying your encoder's output), never as a dependency.

Pairs with [181-imageio-decode-encode-asymmetry.md](181-imageio-decode-encode-asymmetry.md), which
is what sends you looking for an encoder in the first place.
