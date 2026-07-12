# 161 — "Same codec" ≠ "same encode": a remux/passthrough shortcut must honor requested encode settings

**Tags:** remux, passthrough, transcode, stream copy, rewrap, AVAssetWriter, AVAssetExportPresetPassthrough, VideoToolbox, codec match, bitrate, videoQualityMode, PlanBuilder, chroma 4:2:2, 4:2:0, 10-bit, HEVC, H.264, plan builder

**Extracted from:** Winch / Transcoder (2026-07-12)

## Problem

A transcoder had a "prefer remux over transcode when the source codec already matches the target"
optimization. Picking **HEVC Quality → Rate Control: Bitrate → 2 Mbps** on a 6.2K ~700 Mbps Fuji clip
produced an **8.4 GB** output still tagged **HEVC Main 4:2:2 10-bit @ 698 Mb/s** — the source video
stream copied verbatim. The user's 2 Mbps request was silently discarded. It *felt like a rewrap
because it was one.*

## The gotcha / why

The passthrough decision keyed on **codec identity alone**:

```swift
// WRONG — copies the stream whenever codec+container line up, ignoring the encode target.
if codecMatches, preset.resolution == nil, !hdrForcesReencode {
    return .passthrough
}
return .reencode
```

`codecMatches` (HEVC→HEVC) being true is **not** sufficient. The preset also carried a
`videoQualityMode` (a bitrate/quality target) — an explicit request to *re-encode*. A passthrough
shortcut is only correct when the preset asks for **no change to the stream at all**: same codec **and**
no resolution override **and** no quality/bitrate target.

```swift
// RIGHT — passthrough only when nothing about the encode is being asked to change.
if codecMatches,
   preset.resolution == nil,
   preset.videoQualityMode == nil,   // <-- the missing guard: no bitrate/quality target
   !hdrForcesReencode {
    return .passthrough
}
return .reencode
// Every real video preset carries a videoQualityMode, so in practice video always re-encodes.
// Container-only rewraps (if you want them) belong to a SEPARATE, explicitly-chosen path/tool —
// never a silent optimization that overrides the user's stated target.
```

**Verified fix:** same job → 27.2 MiB, HEVC **Main 4:2:0 8-bit** @ 2 183 kb/s (was 8.4 GB / 4:2:2-10 /
698 Mb/s).

## Free correctness oracle — chroma/profile the encoder can't produce

You don't need to trust the UI's "transcoding…" label. Read the OUTPUT's profile: if it keeps a
chroma subsampling or bit depth the **target encoder cannot emit**, it was a stream copy, not an encode.

- VideoToolbox HW **HEVC Main** = 4:2:0 8-bit. An output tagged **Main 4:2:2 10-bit** therefore *cannot*
  have come from that encoder → it's a verbatim copy of a 4:2:2-10 source.
- After a genuine re-encode, chroma/profile drop to what the encoder actually produces (here 4:2:0 8-bit).

So a one-line MediaInfo check (chroma + bit depth + bitrate vs. source) is a definitive "did it actually
transcode?" test — cheaper and surer than trusting progress UI or file timestamps.

## Testing note

Separate the **decision** from the **mechanism**: assert `codec-match + target → .reencode` (plus a
regression test for the exact silent-copy case) in the *planner's* tests; keep the remux/copy code
covered by *forcing* an all-passthrough plan in the copy path's tests, rather than relying on the planner
to choose passthrough (it no longer does). Otherwise those copy tests silently go dark (skip) instead of
failing loudly when the policy changes.
