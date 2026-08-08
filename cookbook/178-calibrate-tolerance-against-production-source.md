# 178 — Calibrate a tolerance against the source production reads, not the one you measured with

**Tags:** tolerance, threshold, epsilon, slack, calibration, ground truth, fixture drift, unit test blind spot, vacuous pass, ffprobe, AVFoundation, CMTime, duration, continuity check

**Extracted from:** Conjoyn (2026-08-08), GoPro chapter grouping

## The problem

You add a numeric tolerance — a slack, epsilon, threshold, timeout — and you calibrate it honestly:
you take real data, measure the actual residual, and pick a bound with orders of margin. You write
fixtures from the same measured data. Every test passes. The tolerance is still wrong.

The gap: **you measured with one tool, and production reads the value from a different one.**

Concrete instance. Segments of a recording had to be chained when the next one's start timecode
lands where the previous one's duration ends:

```
tc(N+1) − tc(N) ≈ duration(N),  within `slack`
```

Calibration came from an `ffprobe` CSV of the real corpus (`format.duration`). Residual: ~1e-11
frames. Slack set to 1 ms — nine orders of margin. Comfortable.

But production never calls `ffprobe` here. It feeds the check `AVFoundation`'s `CMTime`
(`asset.load(.duration)`). Those are **different numbers in general** — in that very corpus,
`ffprobe`'s own `format.duration` and `video` stream duration already disagreed by up to **0.667 ms**,
which would have consumed two thirds of a 1 ms budget on its own.

## Why the test suite cannot catch this

This is the part worth internalizing. The fixtures were transcribed from the **calibration source**.
So in every test:

```
residual = tc_delta − duration_from_CSV     // == 0 by construction
```

The residual is zero *because the fixture and the calibration came from the same measurement*. The
test isn't wrong; it's **vacuous with respect to this failure mode**. It can never observe the
production reader, so it can never observe the disagreement. A green suite is not evidence here — it
is silence. The bug ships and surfaces only on real input, as an intermittent refusal to chain, on
whichever files happen to fall on the wrong side of the delta.

Related trap: adding more fixtures doesn't help, because they all inherit the same bias.

## The check

Four steps, cheap, and the only thing that closes it:

1. **Name the exact production expression** that supplies each value in the comparison. Not the
   concept ("the duration") — the call. `DJIClip.durationInSeconds` → `CMTimeGetSeconds(...)` ←
   `asset.load(.duration)`.
2. **Re-measure the same real inputs through that expression**, not through your analysis tool.
3. **Require `|calibration − production| ≪ tolerance`.** If it's the same order as the tolerance,
   the tolerance is unvalidated regardless of what the tests say.
4. **Write the measured delta into the tolerance's doc comment**, so nobody re-derives it from the
   convenient-but-wrong source next time.

A ~15-line throwaway script is enough — read the real files through the production API and print:

```swift
// Throwaway: does AVFoundation agree with the ffprobe number the tolerance was calibrated on?
import AVFoundation
let sem = DispatchSemaphore(value: 0)
Task {
    for name in CommandLine.arguments.dropFirst() {
        let asset = AVURLAsset(url: URL(fileURLWithPath: name))
        let d = try await asset.load(.duration)          // ← the production path, verbatim
        print("\(name),\(String(format: "%.9f", CMTimeGetSeconds(d))),\(d.value)/\(d.timescale)")
    }
    sem.signal()
}
sem.wait()
```

Outcome in the extracted case: AVFoundation reported the format duration **exactly** on all 13
relevant files (`768.000000000` s, `2063.360000000` s at timescale 90000). The tolerance was fine —
but that was now a **measured fact rather than an assumption**, and the 0.667 ms near-miss showed how
easily it could have gone the other way.

## Generalizes to

Any threshold whose ground truth came from a different reader than production uses:

- durations / timestamps: `ffprobe` vs `AVFoundation` vs `mediainfo` vs container atoms
- file size: `stat` vs `URLResourceValues` vs an API's reported length
- time: DB server clock vs app clock vs monotonic clock, for a staleness window
- geometry: a design tool's exported px vs the layout engine's computed points
- hashes/checksums: streamed vs whole-file readers with different buffering

**Rule of thumb:** if a tolerance exists because two independently-produced numbers must agree, then
*which producer you read from is part of the tolerance's definition* — record it next to the number.

## See also

- The `-quiet` cousin: a command whose success you infer from exit code while its summary is
  suppressed. Same failure shape — absence of evidence read as evidence.
