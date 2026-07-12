# 160 — SwiftUI `VideoPlayer` crashes on macOS → bridge AppKit `AVPlayerView`

**Tags:** VideoPlayer, AVPlayerView, AVKit, _AVKit_SwiftUI, getSuperclassMetadata, EXC_CRASH, SIGABRT, NSViewRepresentable, video preview, macOS 26, swift metadata, AVPlayer

**Extracted from:** Winch / Transcoder (2026-07-12)

## Problem

Putting SwiftUI's `VideoPlayer(player:)` into a macOS view tree hard-crashes the app the **first
time the view is instantiated** — not on a specific file, on *any* video. The crash is a Swift
runtime fatal error, not something a `try`/`guard` can catch:

```
Exception Type:  EXC_CRASH (SIGABRT)   ·   abort() called
3  libswiftCore   swift::fatalError(...)
5  libswiftCore   getSuperclassMetadata + 828        ← runtime can't build the superclass metadata
6  libswiftCore   _swift_initClassMetadataImpl
7  _AVKit_SwiftUI  __swift_instantiateGenericMetadata ← the crashing module
...
27 SwiftUI         ViewResponderFilter.init(inputs:view:)
33 SwiftUI         NSViewRepresentable._makeView
```

## Why

`VideoPlayer` lives in the **`_AVKit_SwiftUI`** module. On some macOS builds (seen on macOS 26 /
Tahoe) the Swift runtime fails to instantiate the generic metadata for a type inside that module,
and `getSuperclassMetadata` calls `fatalError` → `abort()`. Because it's a metadata-instantiation
failure keyed on the *type*, it fires once, deterministically, the first time `VideoPlayer` enters
the view graph. Reading the stack top-down: it's not your file or your data — it's SwiftUI building
`VideoPlayer`'s underlying platform view.

## Fix

Don't use SwiftUI's `VideoPlayer`. Bridge AppKit's **`AVPlayerView`** (plain `AVKit`, *not*
`_AVKit_SwiftUI`) with a tiny `NSViewRepresentable`. It never loads the crashing module — and you get
real inline transport controls for free, which usually suits an app's preview better than
`VideoPlayer` anyway. (The App Shell Standard already lists `AVPlayerView` as a sanctioned reason to
drop to AppKit.)

```swift
import AVKit
import SwiftUI

/// AppKit's `AVPlayerView` bridged into SwiftUI. Use instead of SwiftUI's `VideoPlayer`, which
/// aborts on macOS 26 with a Swift generic-metadata fatal error (getSuperclassMetadata → abort())
/// raised from _AVKit_SwiftUI the first time it enters the view tree. AVPlayerView lives in plain
/// AVKit and never touches that code path. Do NOT swap back to VideoPlayer without re-testing on the
/// current OS.
struct PlayerView: NSViewRepresentable {
    let player: AVPlayer

    func makeNSView(context: Context) -> AVPlayerView {
        let view = AVPlayerView()
        view.controlsStyle = .inline
        view.allowsPictureInPicturePlayback = false
        view.player = player
        return view
    }

    func updateNSView(_ nsView: AVPlayerView, context: Context) {
        if nsView.player !== player {   // AVPlayer is a class → identity compare, swap on change
            nsView.player = player
        }
    }
}
```

Usage — gate on an optional `AVPlayer` so nil (audio-only / nothing selected) shows a placeholder
instead of an empty player; rebuild the player when the source URL changes and `pause()` on
disappear so no off-screen decode pipeline stays alive:

```swift
@State private var player: AVPlayer?
// ...
if let player {
    PlayerView(player: player).clipShape(RoundedRectangle(cornerRadius: 8))
} else {
    RoundedRectangle(cornerRadius: 8).fill(.black)
}
```

## Notes

- Same bug shape can appear for other `_AVKit_SwiftUI` views — the tell is `getSuperclassMetadata` /
  `_swift_instantiateGenericMetadata` in the crash under an `_AVKit_SwiftUI` frame. The fix pattern
  (drop to the AppKit/UIKit equivalent via a representable) generalizes.
- `AVPlayerView` API used here is macOS 10.15+ (`allowsPictureInPicturePlayback`), safe on a macOS 15
  deployment target.
