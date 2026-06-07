# Permission-free network throughput — `getifaddrs` `AF_LINK` byte counters (delta per tick)

**Source:** `1-macOS/QuickStatsPanel/` — `Sampling/NetworkSampler.swift` (2026-06-04, v0.1.1).

You want live up/down network throughput in a **permission-free** utility (agent app, no TCC prompts). Packet capture (`libpcap`/`BPF`) needs elevated rights and is overkill for a glanceable readout. The kernel already exposes cumulative per-interface byte counters through `getifaddrs(3)` — no permission, one call. Like IOKit disk I/O (#66), the counters are **cumulative-since-boot**, so you report the **delta between ticks** over the sample interval.

**Key subtlety:** `getifaddrs` returns *several* records per interface (one per address family). The byte counters live **only on the link-layer (`AF_LINK`) record**, whose `ifa_data` points to an `if_data` struct with `ifi_ibytes` / `ifi_obytes`. Skip every other record.

```swift
import Foundation

private static func readInterfaceBytes() -> (received: UInt64, sent: UInt64)? {
    var head: UnsafeMutablePointer<ifaddrs>?
    guard getifaddrs(&head) == 0, let first = head else { return nil }
    defer { freeifaddrs(head) }                       // always free the list

    var totalReceived: UInt64 = 0, totalSent: UInt64 = 0
    for ptr in sequence(first: first, next: { $0.pointee.ifa_next }) {
        let ifa = ptr.pointee
        // Counters live ONLY on the link-layer (AF_LINK) record.
        guard let addr = ifa.ifa_addr,
              addr.pointee.sa_family == UInt8(AF_LINK),
              let dataPtr = ifa.ifa_data else { continue }

        let name  = String(cString: ifa.ifa_name)
        let flags = Int32(ifa.ifa_flags)
        guard shouldCount(interfaceName: name, flags: flags) else { continue }

        let data = dataPtr.assumingMemoryBound(to: if_data.self).pointee
        totalReceived += UInt64(data.ifi_ibytes)
        totalSent     += UInt64(data.ifi_obytes)
    }
    return (totalReceived, totalSent)
}
```

Then in the timer `tick()`: hold `previousBytes`, and `rate = Double(current - previous) / interval` (guard `current >= previous` against an interface bounce/reset; first tick only seeds the baseline → rates are 0 that tick).

**The interface filter is a real design decision — make it a pluggable predicate**, don't hardcode it inline:

```swift
private static func shouldCount(interfaceName: String, flags: Int32) -> Bool {
    // Count everything (incl. lo0) → simplest, but loopback inflates idle reads.
    // Internet-only → drop loopback:        return (flags & IFF_LOOPBACK) == 0
    // Physical only →                        return interfaceName.hasPrefix("en")
    return true
}
```

**Gotchas**
- **Counters are on `AF_LINK`, not the IPv4/IPv6 records.** Summing every record double-counts or reads garbage. Test `sa_family == AF_LINK` first.
- **Loopback (`lo0`) is included if you count everything** — local-only traffic (apps talking to localhost) keeps the reading off zero even when "offline". For an internet-traffic reading, drop it with `(flags & IFF_LOOPBACK) == 0`. Test flag *bits* (`IFF_LOOPBACK`, `IFF_UP`) rather than string-matching names — more robust.
- **`assumingMemoryBound(to: if_data.self)`** is the correct rebind for `ifa_data`; it's an `UnsafeMutableRawPointer`.
- **Always `freeifaddrs(head)`** via `defer` — the list is heap-allocated by the call.
- **VPN tunnels (`utun*`) can double-count** VPN bytes (tunnel + the physical interface carrying it). Decide per product whether that matters.
- Same concurrency shape as the other samplers: `static` helper on a background `DispatchQueue`, non-`Sendable` final class, `[weak self]` timer handler, hop to `@MainActor` to publish.

**Best for:** a permission-free stats utility (HUD, menu-bar monitor) needing network up/down rate without a TCC prompt or packet-capture entitlement. Direct sibling of #66 (disk stats) — same cumulative-counter → delta-per-tick shape. Pairs with #65 (NSPanel HUD), #64 (global hotkey), #67 (jitter-free readout), #69 (battery sampler), #70 (data-driven stat strip).
