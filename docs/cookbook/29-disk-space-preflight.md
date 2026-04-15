# Disk-Space Preflight

**Use when:** an app writes large files (video conversion, archive creation, backup)
that could fail mid-process with ENOSPC. Check free space up-front and fail fast with
a named-volume message instead of a cryptic libc error after minutes of work.

**Source:** `1-macOS/P2toMXF/` — `DiskSpace.swift`, `QueueManager+Processing.swift`.

---

## Why "preflight" matters

BMX rewrap of a 54 GB P2 card generates ~49 GB of intermediate files in `/var/folders/.../T/`
before concatenation. On a boot volume with 21 GB free, the conversion would run for 60+
seconds before hitting `fwrite failed: error code 28` (ENOSPC) and dying. The user then
saw a cryptic libMXF backtrace with no hint that the *boot* volume was the problem (the
output disk had 379 GB free).

A preflight check — "do we have enough space on the right volume?" — catches this before
any real work starts. 4 syscalls, ~1 ms, eliminates a whole class of slow, frustrating
failures.

## The `DiskSpace` primitive

Wrap the Apple file URL capacity/identity APIs in a tiny helper. Nothing stateful.

```swift
import Foundation

enum DiskSpace {
    /// Free bytes available for important (user-initiated) writes at the URL's volume.
    /// Falls back to the legacy key if the "important usage" key is unavailable.
    static func availableCapacity(for url: URL) -> Int64? {
        let keys: Set<URLResourceKey> = [
            .volumeAvailableCapacityForImportantUsageKey,
            .volumeAvailableCapacityKey
        ]
        guard let values = try? url.resourceValues(forKeys: keys) else { return nil }
        if let important = values.volumeAvailableCapacityForImportantUsage {
            return important
        }
        if let raw = values.volumeAvailableCapacity {
            return Int64(raw)
        }
        return nil
    }

    /// User-facing volume name ("Macintosh HD", "1TB extra") — for readable error messages.
    static func volumeName(for url: URL) -> String? {
        (try? url.resourceValues(forKeys: [.volumeNameKey]))?.volumeName
    }

    /// True if both URLs are on the same volume.
    /// Compares the volume root URLs directly — avoids brittle `/Volumes/…` string matching.
    static func sameVolume(_ a: URL, _ b: URL) -> Bool {
        guard
            let aValues = try? a.resourceValues(forKeys: [.volumeURLKey]),
            let bValues = try? b.resourceValues(forKeys: [.volumeURLKey]),
            let aVolume = aValues.volume,
            let bVolume = bValues.volume
        else { return false }
        return aVolume == bVolume
    }

    static func formatBytes(_ bytes: Int64) -> String {
        ByteCountFormatter.string(fromByteCount: bytes, countStyle: .file)
    }
}
```

## Which capacity key to use

| Key | What it reports | When to use |
|---|---|---|
| `volumeAvailableCapacityKey` | Raw free bytes | Legacy; doesn't account for purgeable storage. Use as fallback only. |
| `volumeAvailableCapacityForImportantUsageKey` | Free bytes after factoring out purgeable caches | **User-initiated writes (this is almost always what you want).** Returns larger number — purgeable space can be reclaimed. |
| `volumeAvailableCapacityForOpportunisticUsageKey` | Free bytes for low-priority writes | Pre-downloads, background caches. Returns smaller number. |

For "does this job fit?" checks, always use the **important usage** key. Users will
resent the app refusing to run when Finder shows plenty of free space — the important
usage figure matches what Finder reports.

## Preflight inside a job runner

```swift
func preflightDiskSpaceError(
    for job: ConversionJob,
    tempDir: URL,
    outputDir: URL
) -> String? {
    // Source-size proxy — OP1a rewrap is near-stream-copy of OPAtom inputs.
    let requiredBase = job.clips.reduce(Int64(0)) { $0 + $1.totalFileSize }
    // 10% safety margin covers container overhead + filesystem rounding.
    let required = Int64(Double(requiredBase) * 1.10)

    if DiskSpace.sameVolume(tempDir, outputDir) {
        // Temp + final output on same disk → need both simultaneously.
        let combined = required * 2
        guard let free = DiskSpace.availableCapacity(for: tempDir) else { return nil }
        if free < combined {
            let name = DiskSpace.volumeName(for: tempDir) ?? "the selected volume"
            return "Not enough space on \(name): \(DiskSpace.formatBytes(free)) free, " +
                   "~\(DiskSpace.formatBytes(combined)) required (temp + output on same volume)."
        }
        return nil
    }

    // Separate volumes — check each independently.
    if let freeTemp = DiskSpace.availableCapacity(for: tempDir), freeTemp < required {
        let name = DiskSpace.volumeName(for: tempDir) ?? "temp volume"
        return "Not enough space on \(name) (temp): \(DiskSpace.formatBytes(freeTemp)) free, ~\(DiskSpace.formatBytes(required)) required."
    }
    if let freeOut = DiskSpace.availableCapacity(for: outputDir), freeOut < required {
        let name = DiskSpace.volumeName(for: outputDir) ?? "output volume"
        return "Not enough space on \(name) (output): \(DiskSpace.formatBytes(freeOut)) free, ~\(DiskSpace.formatBytes(required)) required."
    }
    return nil
}
```

Call it at the **top** of the job, right after bookmarks resolve but before any process
spawns. On failure, mark the job `.failed` with the returned string — which already
contains the volume name and free capacity in human-readable form.

## Same-volume vs separate-volume

Two common cases:
- **Temp and output on same disk** (typical default — `/var/folders/...` and `/Volumes/X/output/`
  both on user's primary drive): need `required × 2` on that one disk.
- **Temp on A, output on B** (user redirected temp to a bigger drive): each needs `required`
  independently.

Use `DiskSpace.sameVolume` to pick the right branch. Don't string-match `/Volumes/…` prefixes —
that fails on boot-volume paths that live at `/` (and on symlinks, and on APFS container
sub-volumes).

## Error-message design

Bad error: `"Disk full"`. Which disk?

Good error: `"Not enough space on Macintosh HD (boot): 21 GB free, ~59 GB required. Choose a different temp folder in File → Temp Folder…"`

Three elements:
1. **Volume name** (user's own naming, from `volumeNameKey`).
2. **Quantities** (free vs. required, both formatted via `ByteCountFormatter` for consistency
   with Finder).
3. **Next-action hint** (what the user can do — change temp folder, free up space, etc.).

## Post-failure enrichment

Even with a preflight, actual ENOSPC failures can still occur (another app fills the disk
mid-run). When parsing a failed job's error text, re-query `DiskSpace` to name the culprit
volume — compare both temp and output volumes' current free capacity and label whichever is
lower. Same `DiskSpace` primitive serves both preflight and postmortem.

```swift
if errorText.lowercased().contains("error code 28") {
    let tempFree = DiskSpace.availableCapacity(for: tempURL)
    let outFree = DiskSpace.availableCapacity(for: outputURL)
    // Whichever is lower is the likely culprit.
    let culprit = (tempFree ?? Int64.max) <= (outFree ?? Int64.max) ? tempURL : outputURL
    if let name = DiskSpace.volumeName(for: culprit),
       let free = DiskSpace.availableCapacity(for: culprit) {
        return "Out of space on \(name) (\(DiskSpace.formatBytes(free)) free)"
    }
}
```
