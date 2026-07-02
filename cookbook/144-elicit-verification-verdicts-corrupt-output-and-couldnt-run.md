# Elicit specific verification verdicts on demand — corrupt-output via 1-frame `-c copy`, and `chmod 000` the source for the "couldn't-run" state

**Tags:** -f streamhash, -c copy, chmod 000, EACCES, security-scoped bookmark, verification ladder, tmcd, packet count

**Source:** TimeCodeEditor — `01_Project/TimeCodeEditorTests/FFmpegCorrectionIntegrationTests.swift` (2026-06-30, Verification V2 phase 6). Pairs with [[141-exiftool-geotag-end-to-end-test-no-fixtures]] (the no-fixtures sibling), [[134-ffmpeg-copy-trim-timecode-author-verify]] (the same `-c copy`/`tmcd` toolbox), and [[73-verify-hud-without-screen-recording]] (driving a verdict without Screen-Recording permission).

## The problem
You built a **source↔output verification ladder** — cheap structural checks (packet count/bytes, duration, codec params) that **escalate** to an authoritative byte-exact `-f streamhash` only when something looks off, plus a 3-valued seal: ✓ **verified** / ⚠ **couldn't fully verify** / ✗ **disproved**. Now prove it actually discriminates. Two verdicts are *hard to produce on purpose*:

1. **A genuine ✗** — an output that the cheap tier *suspects* (a warning) and the hash then *condemns* (a fail) — **without an encoder** (an LGPL ffmpeg build has none) and without it just failing the timecode check (which would short-circuit the escalation you're trying to exercise).
2. **A genuine ⚠ "couldn't run"** — the honest middle state, deliberately rare by design (the hash funnels most warnings to ✓ or ✗). You need it to **visually** confirm the amber row/chips in the real app, where tests can't see pixels.

## Technique 1 — a deterministic corrupt output with NO re-encode: 1-frame `-c copy`
Stream-copy **one** video packet of the source, carrying the *correct* timecode. Same codec/geometry, a valid single `tmcd`, fully decodable — so every cheap check stays clean **except the media** (1 packet vs the source's N). That isolates exactly the escalation path: structural anomaly → warning → hash fails.

```swift
// Build via the bundled ffmpeg directly (NOT the production runner — you want to own the corruption).
process.arguments = [
    "-y", "-v", "error", "-i", source.path,
    "-map", "0:v:0",     // video only (drop audio/data so it's a clean 1-stream file)
    "-c", "copy",        // stream-copy — no encoder needed (LGPL-safe)
    "-frames:v", "1",    // keep ONE packet of the source's N ⇒ media diverges
    "-timecode", assign, // write the CORRECT TC ⇒ the anomaly is purely structural
    output.path,
]
```

Then assert the **chain**, not just the outcome:
```swift
let fast = await verifier.verifyFast(job)
XCTAssertEqual(fast.overall, .warning)                 // cheap tier suspects, never hard-fails
XCTAssertEqual(checkSeverity(fast, .timecodeWriteBack), .pass)   // TC is fine — flag is structural
XCTAssertEqual(checkSeverity(fast, .packetCount),       .warning)
XCTAssertFalse(fast.checks.contains { $0.kind == .streamHash })  // didn't pay for the hash yet

let escalated = await verifier.verify(job)             // auto-escalates on the warning
XCTAssertEqual(escalated.seal, .failed)
XCTAssertEqual(checkSeverity(escalated, .streamHash), .fail)     // the hash is the authority
XCTAssertEqual(checkSeverity(escalated, .timecodeWriteBack), .pass)  // only the hash failed
```

**Why this works — the load-bearing fact:** `-f streamhash -hash md5` digests the **coded packet bytes per stream**, so a clean `-c copy` rewrite (new container, fresh `tmcd`, re-based PTS) yields a hash **identical to the source's** — verify this once at the shell before trusting it (`good-copy hash == source hash`). The 1-frame copy changes the *set* of packets, so its hash diverges while it still decodes cleanly and reads back the right TC. No other corruption is this surgical without an encoder.

> With tiny fixtures (2 packets), `-frames:v 1` is the only truncation; for longer clips use `-frames:v N` or `-t <dur>`. Anchor the warning assertion on **packet count** (robust 2→1), not **duration** — duration's ±1-frame tolerance can sit right on the boundary (e.g. 34 ms vs a 33.3 ms frame) and flip `.info`/`.warning`.

## Technique 2 — force the ⚠ "couldn't-run" state for a live visual check: `chmod 000` the source
The ⚠ state means *a check could not run* (not "bad"). To stage it in the running app: complete a job ✓ (source readable), then make the **source** unreadable and trigger a **manual re-verify**. The output's TC read-back passes (output is fine), but the source-side hash/packet probes hit `EACCES` → `.warning` → the row flips **green → amber** with the flagged-check chips.

```bash
chmod 000 "/path/to/source.MOV"   # ffprobe/ffmpeg get EACCES; fully reversible
# → click the app's "Thorough verify" button on the completed row → amber caution + chips
chmod 644 "/path/to/source.MOV"   # restore immediately after the screenshot
```

**Why `chmod`, not rename or delete** — the two intuitive moves both fail:
- **Rename / move is unreliable.** A macOS **security-scoped bookmark follows the file by identity** (inode), so `URL(resolvingBookmarkData:)` re-resolves to the *new* path (with `bookmarkDataIsStale = true`) and the app reads it anyway → the re-verify comes back **green**, not amber.
- **Deletion is destructive** (and the bookmark may even briefly resolve a Trash path).

Read-blocking is reliable **and** non-destructive, and it routes through the exact real-world scenario the ⚠ state exists to report: *the source lived on a drive that's no longer readable at re-verify time.* It also stays ⚠ not ✗ because the verdict splits by **which file each check reads** — output-side checks (TC write-back, single-`tmcd`, full decode) pass; source-side checks (hash, packet compare) can't run → worst severity is `.warning`.

## Traps
- **Don't transcode to corrupt.** It needs an encoder (absent from LGPL ffmpeg) and changes codec params too, so you no longer prove *structural-anomaly→hash* in isolation. Truncate.
- **A wrong-TC output is the wrong test for escalation** — the fast tier hard-fails on the TC check directly and never escalates. Keep the TC correct so the *only* thing forcing escalation is the structural signal and the *only* thing failing is the hash.
- **The queue (copy) path can't produce ⚠ from an unreadable source** — it reads the source *while copying*, so an unreadable source fails the copy (✗ red). ⚠ comes only from the **manual re-verify on an already-completed row**.
- **Locate the bundled binary in tests via `#filePath`/`BundledToolResolver`, not `Bundle.main`** (the xctest harness), same as [[141-exiftool-geotag-end-to-end-test-no-fixtures]].
- **No Screen-Recording permission in the terminal?** The amber pixels are the user's sign-off; tests + a window-alive check can't prove the tint. Stage it deterministically (above) so the user needs one click + one screenshot.

**Best for:** proving any source↔output verification/integrity ladder (media correction, file conversion, backup/restore) genuinely discriminates pass / couldn't-verify / fail — when you need a *corrupt-but-otherwise-valid* artifact without an encoder, and a *reliably-but-reversibly unverifiable* one for a live UI check.
