## Actor Re-Entrancy: When TOCTOU is NOT Possible

**Rule:** Between two lines with no `await`, an actor cannot re-enter. Two callers cannot interleave in a synchronous sequence.

```swift
actor ThumbnailCache {
    private var inFlight: [String: Task<NSImage?, Never>] = [:]

    func thumbnail(for url: URL) async -> NSImage? {
        // ✅ SAFE — no await between check and write
        if let existing = inFlight[key] {
            return await existing.value  // <- re-entry CAN happen here (at the await)
        }

        let task = Task { ... }
        inFlight[key] = task          // <- atomic with the check above, no interleave possible

        let result = await task.value  // <- re-entry CAN happen here
        inFlight.removeValue(forKey: key)
        return result
    }
}
```

**Re-entry only happens at `await` points.** A code reviewer (or AI model) may flag `check → create → write` as a TOCTOU race. It isn't one if there's no `await` between check and write. The actor serializes synchronous sequences.

**Where re-entry IS a real concern:** After an `await`, a second caller can enter. If your post-await code reads state that the second caller might mutate, that's a real race. Design around it with snapshot captures before the `await`.

**Source:** CropBatch `ThumbnailCache` review (2026-04-03) — false positive correctly dismissed.

---

