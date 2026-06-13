# 95 — QuickLook-first video thumbnails with an FFmpeg fallback (hybrid)

**Trigger keywords:** video thumbnail in a list re-decodes every scan, FFmpeg `extractFrame`
per row spawns a subprocess, thumbnail I/O contention with scan/export, `QLThumbnailGenerator`
swap, QuickLook poster frame for a clip, system-cached thumbnail, thumbnail strip beachball on a
slow SD card, `generateBestRepresentation`, representationTypes `.thumbnail` vs `.icon` vs `.all`,
thumbnail shows generic movie-file icon, offload decode out-of-process, `QuickLookThumbnailing`
import auto-link, drop the unused last frame.

---

## The problem

A recordings/clips list draws a small poster frame per row. The obvious implementation shells out
to **FFmpeg per clip** (`-ss <t> -i file -frames:v 1 -vf scale=320:-1 -f image2pipe …`). That works,
but every visible row:

- **spawns a heavyweight subprocess in your process**, so you must hand-roll throttling (a 3-slot
  semaphore), cancellation (poll `Task.isCancelled`, SIGTERM the orphan), and once-only continuation
  resumption (`ContinuationGuard`) — a lot of machinery whose only reason to exist is that FFmpeg is
  a subprocess;
- **competes for the same disk-read budget** as the scan / metadata / SRT work firing right after a
  scan (on a UHS-I SD card capped ~95 MB/s, that contention is visible as a thumbnail-strip stall);
- **re-decodes from scratch on every scan** — there is no cache, so re-opening the same card pays the
  full decode cost again.

There's also a quiet over-extraction bug to look for: a ported `getThumbnails` may extract **both a
first and a last frame** while the row only ever displays `first ?? last`. The last frame is then
pure wasted work — a second subprocess per clip for a frame that's shown only if the first extraction
*fails*.

## The fix: hybrid, QuickLook primary

Ask **`QLThumbnailGenerator` first**, fall back to FFmpeg only when QuickLook produces nothing:

```swift
import QuickLookThumbnailing   // system framework — auto-links on import, no project.yml/xcodegen change

private func extractThumbnails(for clip: Clip) async -> ClipThumbnails {
    if let quickLook = await generateQuickLookThumbnail(for: clip.videoURL) {
        return ClipThumbnails(first: quickLook, last: nil)
    }
    // QuickLook had nothing (rare/odd file) — fall back to the throttled FFmpeg first frame.
    let frame = await extractFrameWithSemaphore(from: clip.videoURL, atSeconds: 0)
    return ClipThumbnails(first: frame, last: nil)
}

private func generateQuickLookThumbnail(for url: URL) async -> NSImage? {
    guard !Task.isCancelled else { return nil }
    let request = QLThumbnailGenerator.Request(
        fileAt: url,
        size: CGSize(width: 320, height: 180),  // ~tile size × generous, see "size/scale" below
        scale: 2,                                // Retina
        representationTypes: .thumbnail          // a REAL rendered frame — see the trap below
    )
    do {
        let rep = try await QLThumbnailGenerator.shared.generateBestRepresentation(for: request)
        return rep.nsImage
    } catch {
        return nil   // unreadable / unsupported / no content thumbnail → route to FFmpeg fallback
    }
}
```

**Why this is the win, not just "fewer processes":**

- QuickLook decodes **out-of-process** in the system Thumbnails agent
  (`com.apple.quicklook.ThumbnailsAgent`), so the decode load *leaves your app entirely* — that is
  what actually eases the I/O/CPU contention with your scan/export pipeline.
- It is **system-cached**, keyed on file + mtime + size. Re-scanning the same card returns thumbnails
  **instantly** (FFmpeg re-decodes every time). This is the user-visible "definitely faster."
- It self-manages concurrency and cancellation, so the common path needs **none** of the FFmpeg
  throttle/kill machinery.

## The load-bearing details

1. **`representationTypes: .thumbnail` is a correctness trap, not a preference.** `.thumbnail` forces
   a real rendered frame. `.icon` and `.all` are *allowed to hand back the generic movie-file icon*
   when no content thumbnail exists — and crucially that returns **successfully**, so your
   `?? FFmpeg` fallback **never fires** and every row shows the same filmstrip glyph. "Best
   representation" may not be a picture of the video at all. Use `.thumbnail` only; let the throw be
   the miss.

2. **Throwing → `nil` is the fallback hinge, not error-swallowing.** QL throws for
   unreadable/unsupported files. Catching to `nil` is exactly the control flow that routes that clip
   to FFmpeg — that catch is what makes "hybrid" hybrid.

3. **Demote the FFmpeg machinery, don't delete it.** Keep the semaphore, the kill-polling, and the
   once-only `ContinuationGuard` — but now they throttle *only* the rare QuickLook miss. You get the
   safety net's robustness (no blank tiles ever) while the common path bypasses all of it. (If you go
   *pure* QL with no fallback, you can delete that machinery — at the cost of a permanent placeholder
   tile on any file QL can't read.)

4. **Drop the unused last frame.** If the UI only renders `first ?? last`, extract only `first`; keep
   the `last` field on the struct (always nil now) so call sites and the `ClipThumbnails` shape don't
   churn. This alone roughly halves per-clip work.

5. **size / scale is the deal you make with the daemon.** Match the display tile, generously: a
   ~67×38 pt tile drawn `.aspectRatio(.fill)` on Retina stays crisp at 320×180 @ scale 2 (the same
   `maxWidth: 320` the FFmpeg path used). Too small → soft crop; too large → you ask the daemon to
   render and cache near-source-res posters for a thumbnail strip.

6. **`import QuickLookThumbnailing` auto-links** via Clang module auto-linking — no `dependencies:`
   entry in `project.yml`, no xcodegen regen, no explicit `.framework`. Confirm with a real build, not
   SourceKit (a fresh edit often shows false "Cannot find type" / "No such module" until the
   whole-module index loads).

## Caveats / behavior changes to flag

- **QuickLook picks its *own* representative poster frame**, not exactly frame 0. For most footage
  that's an improvement (it avoids black leader/clapper frames), but it *is* a behavior change — the
  thumbnail will now match Finder's poster, which can differ from the old exact-first-frame. Tell the
  user; tune via the FFmpeg fallback timestamp if a specific clip looks wrong.
- **Sandbox:** QuickLook reads the file, so a *sandboxed* app needs the file inside its granted scope
  (security-scoped bookmark / user-selected). A non-sandboxed app (e.g. one bundling GPL FFmpeg, so
  MAS is already out) reads arbitrary card paths freely — no extra entitlement.
- **Cancellation:** the actor's existing `Task.isCancelled` guard before the request is enough for
  scroll-off cancellation; you don't need `QLThumbnailGenerator.cancel(_:)` for a short request, and
  the result is cached anyway.

## Test impact

An integration test that asserted *both* frames now encodes obsolete behavior. Flip it: `first` must
be non-nil (QuickLook **or** FFmpeg fallback — either is fine, the test shouldn't care which),
`last` must be **nil** (intentionally no longer extracted). A "missing source yields empty
thumbnails, but the empty result is still cached" test is unchanged: QL throws → FFmpeg fallback also
nil → both nil, result still cached so you don't relaunch on every scroll.

Source: Conjoyn `Services/ThumbnailManager.swift` (+ `FFmpegWrapper+Thumbnails.swift` kept as the
fallback). Pairs with **#86** (single-flight async dedup — the `inFlight`/cache ledger this manager
already uses to coalesce duplicate requests), **#43** (subprocess fire-and-collect, the FFmpeg
fallback), **#93** (keep the view-feed pure / push expensive work off-main), **#75** (permission-free
system work).
