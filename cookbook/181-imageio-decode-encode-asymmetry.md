# 181 — ImageIO decodes formats it cannot encode: probe the destination table, don't infer

**Tags:** ImageIO, CGImageDestinationCopyTypeIdentifiers, CGImageSourceCopyTypeIdentifiers, WebP, AVIF, JXL, HEIC, encode vs decode, capability probe, zero-dependency, CGImageDestination

**Extracted from:** Images2WebP (2026-08-27)

## The problem

"macOS supports WebP" is true and useless. Support is **asymmetric**: ImageIO gained WebP
*decoding*, never *encoding*. Reading the release notes, seeing WebP listed, and scaffolding an app
around `CGImageDestination` gets you to the first write call before anything fails — after the
architecture is already committed to having no encoder dependency.

The same asymmetry applies per-format and per-OS across AVIF, JXL, HEIC and others. It is not a
WebP quirk; it is how ImageIO is shaped.

## The probe

ImageIO publishes both capability tables at runtime. Ask it, in five lines, before designing
anything around it:

```swift
import ImageIO

let encodable = CGImageDestinationCopyTypeIdentifiers() as! [String]
let decodable = CGImageSourceCopyTypeIdentifiers() as! [String]

print("encode:", encodable.contains { $0.lowercased().contains("webp") })
print("decode:", decodable.contains { $0.lowercased().contains("webp") })
```

Run it with `swift file.swift` — no project, no target, no build settings.

Result on **macOS 27.0 (26A5421a)**, verified 2026-08-27:

```
encode: false      // no WebP UTI among the destination types
decode: true       // present among the source types
```

## The inference that makes it decisive

Probe on the **newest** OS you have, not your deployment target. If the newest OS in reach cannot
encode the format, no *older* supported OS can either, and the question is closed in one run — you
do not need a VM per OS version. The reverse does not hold: a newer OS encoding it tells you
nothing about your deployment target, and then you *do* need to check the floor.

## Consequences worth writing down

Once the system framework is out, the app ships an encoder — which changes the dependency, signing
and notarization conversation. Record the probe output verbatim in `decisions.md`, not the
conclusion alone: "ImageIO can't do it" invites someone to re-litigate it in a year, whereas the
two-line capability dump with an OS build number does not.

For WebP specifically, ImageIO stays useful on the **input** side — it decodes PNG/JPEG/HEIC/TIFF
*and* WebP to `CGImage`. Only the write step needs a third-party encoder. See
[182-libwebp-spm-static-no-notarization-surface.md](182-libwebp-spm-static-no-notarization-surface.md).

## The general rule

Never let "the platform supports format X" stand in for a capability check when X sits on the
output path. Support claims are about the format; `CGImageDestinationCopyTypeIdentifiers()` is
about *your* binary on *this* OS. Probe, paste the output into the decision record, then design.
