# Permission-free disk stats — `statfs` capacity + IOKit I/O counters (not `fs_usage`)

**Source:** `1-macOS/QuickStatsPanel/` — `Sampling/DiskSampler.swift` (2026-06-04, v0.1.0).

You want live disk stats — **free/used capacity** and **read/write throughput** — in a utility that must stay **permission-free** (no prompts, agent app). The obvious "reuse" is shelling out to `/usr/bin/fs_usage`, but that **requires root or Full Disk Access** and runs a continuous subprocess parsing syscall traces. Wrong tool for a glanceable HUD. Both stats are available permission-free through lower-level APIs:

**1. Capacity → `statfs("/")`.** A single syscall, no permission, no allocation. `f_bavail` is blocks available to a non-root process (the honest "free" number); multiply by `f_bsize`.

```swift
private static func readCapacity() -> (used: UInt64, free: UInt64, total: UInt64)? {
    var fs = statfs()
    guard statfs("/", &fs) == 0 else { return nil }
    let blockSize = UInt64(fs.f_bsize)
    let total = UInt64(fs.f_blocks) * blockSize
    let free  = UInt64(fs.f_bavail) * blockSize      // available to non-root
    let used  = total > free ? total - free : 0
    return (used, free, total)
}
```

**2. Throughput → IOKit `IOBlockStorageDriver` statistics.** Each block-storage driver publishes a `Statistics` dictionary with cumulative-since-boot `Bytes (Read)` / `Bytes (Write)` counters. Sum across drivers, then report the **delta between ticks** over the sample interval (same shape as CPU load ticks — the first tick only seeds a baseline, so rates are 0 until tick #2).

```swift
import IOKit

private static func readBlockStorageBytes() -> (read: UInt64, written: UInt64)? {
    guard let matching = IOServiceMatching("IOBlockStorageDriver") else { return nil }
    var iterator: io_iterator_t = 0
    guard IOServiceGetMatchingServices(kIOMainPortDefault, matching, &iterator) == KERN_SUCCESS
    else { return nil }
    defer { IOObjectRelease(iterator) }

    var totalRead: UInt64 = 0, totalWritten: UInt64 = 0, found = false
    var service = IOIteratorNext(iterator)
    while service != 0 {
        var props: Unmanaged<CFMutableDictionary>?
        if IORegistryEntryCreateCFProperties(service, &props, kCFAllocatorDefault, 0) == KERN_SUCCESS,
           let dict  = props?.takeRetainedValue() as? [String: Any],
           let stats = dict["Statistics"] as? [String: Any] {
            // String keys per <IOKit/storage/IOBlockStorageDriver.h>.
            if let r = (stats["Bytes (Read)"]  as? NSNumber)?.uint64Value { totalRead    += r; found = true }
            if let w = (stats["Bytes (Write)"] as? NSNumber)?.uint64Value { totalWritten += w; found = true }
        }
        IOObjectRelease(service)            // release every service, including on the skip path
        service = IOIteratorNext(iterator)
    }
    return found ? (totalRead, totalWritten) : nil
}
```

Then in the timer `tick()`: hold `previousIO`, and `rate = Double(current - previous) / interval` (guard `current >= previous` against a wrap/reset).

**Gotchas**
- **`fs_usage` is a trap for permission-free apps.** It needs root / Full Disk Access *and* spawns a subprocess. If your product is "glanceable, not a monitoring suite," capacity + IOKit counters give you the numbers worth glancing at with zero permission cost.
- **Counters are cumulative since boot** — you want the per-interval delta, not the raw value. First tick seeds the baseline → report 0 that tick.
- **Cast stats values via `NSNumber`**, not `as? UInt64` directly — the dictionary values are CFNumbers bridged to `NSNumber`; `.uint64Value` is the reliable read.
- **Release every `io_object_t`.** `IOObjectRelease(service)` on *every* loop iteration (including the `continue`/skip path) and `IOObjectRelease(iterator)` via `defer`, or you leak Mach ports.
- **`kIOMainPortDefault`** (not the deprecated `kIOMasterPortDefault`) on macOS 12+.
- **`ByteCountFormatter` spells out zero** — an idle disk reads "Zero KB/s". Set `allowsNonnumericFormatting = false` for "0 KB/s".
- Both helpers are `static` and run on the sampler's background `DispatchQueue` — they touch no shared mutable state, so they stay clean under `SWIFT_STRICT_CONCURRENCY = complete` (mirror the CPU/Memory sampler shape: non-Sendable final class, `[weak self]` timer handler, hop to `@MainActor` to publish).

**Best for:** a permission-free stats utility (HUD, menu-bar monitor) that needs disk capacity and/or I/O rate without tripping a TCC prompt. Same sampler shape as host CPU/VM stats (`DispatchSourceTimer` + `Sendable` value sample + callback). Pairs with #65 (NSPanel HUD), #64 (global hotkey), #67 (jitter-free numeric readout for displaying the values).
