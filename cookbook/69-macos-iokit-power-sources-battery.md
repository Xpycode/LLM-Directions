# Permission-free battery — IOKit Power Sources + the Copy/Get ownership rule

**Source:** `1-macOS/QuickStatsPanel/` — `Sampling/BatterySampler.swift` (2026-06-04, v0.1.1).

You want battery charge / charging state / time-remaining in a permission-free utility. The IOKit **Power Sources** API (`IOKit.ps`) is the same snapshot the menu-bar battery reads — no entitlement. Unlike CPU/disk/network counters this is **not a delta**: each read is an *absolute* state, so there's no `previous…` baseline and no first-tick zero.

```swift
import IOKit.ps

private static func readBattery() -> BatterySample {
    guard let blob = IOPSCopyPowerSourcesInfo()?.takeRetainedValue(),
          let sources = IOPSCopyPowerSourcesList(blob)?.takeRetainedValue() as? [CFTypeRef],
          let source = sources.first,
          let desc = IOPSGetPowerSourceDescription(blob, source)?.takeUnretainedValue() as? [String: Any]
    else { return .empty }                      // .empty has isPresent: false

    let current = (desc[kIOPSCurrentCapacityKey] as? NSNumber)?.doubleValue ?? 0
    let max     = (desc[kIOPSMaxCapacityKey]     as? NSNumber)?.doubleValue ?? 100
    let percent = max > 0 ? current / max * 100 : 0

    let isCharging = (desc[kIOPSIsChargingKey] as? Bool) ?? false
    let isOnAC     = (desc[kIOPSPowerSourceStateKey] as? String) == kIOPSACPowerValue

    // IOKit uses -1 for "still calculating" → surface as nil. Which key applies
    // depends on whether we're charging.
    let raw = (isCharging ? desc[kIOPSTimeToFullChargeKey]
                          : desc[kIOPSTimeToEmptyKey]) as? NSNumber
    let mins = (raw?.intValue ?? -1) > 0 ? raw?.intValue : nil

    return BatterySample(isPresent: true, percent: percent,
                         isCharging: isCharging, isOnAC: isOnAC, minutesRemaining: mins)
}
```

**The memory-ownership trap (the reason this entry exists).** The function-name prefix *is* the ARC contract — get it wrong and you leak or over-release (crash):

| API | Rule | Swift |
|-----|------|-------|
| `IOPSCopy…Info`, `IOPSCopy…List` | **Create Rule** — you own it | `.takeRetainedValue()` |
| `IOPSGetPowerSourceDescription` | **Get Rule** — you don't own it | `.takeUnretainedValue()` |

"**Copy**"/"**Create**" → retained; "**Get**" → unretained. This rule applies to *all* CoreFoundation/IOKit `Unmanaged<>` returns, not just Power Sources.

**Two display tricks worth reusing**
- **Inverted color band.** Battery is backwards from every other stat — *low* charge is the alarming one. Reuse a normal hot/calm color ramp by feeding it `100 - percent`: 90 %→`10`→calm, 12 %→`88`→hot. No separate color logic.
- **State-aware SF Symbol**, like the menu bar — bolt variant while charging, nearest fill otherwise:

```swift
var symbolName: String {
    if isCharging { return "battery.100percent.bolt" }
    switch percent {
    case ..<13: return "battery.0percent";   case ..<38: return "battery.25percent"
    case ..<63: return "battery.50percent";  case ..<88: return "battery.75percent"
    default:    return "battery.100percent"
    }
}
```

**Gotchas**
- **Desktop Macs report no source** — `IOPSCopyPowerSourcesList` is empty. Carry an `isPresent` flag and **hide the UI entirely** rather than showing 0 %. (In a data-driven strip, filter the tile out — see #70.)
- **`-1` time-remaining means "calculating"**, not "0 minutes left". Map it to nil/`"—"`.
- **`kIOPSTimeToEmpty` vs `kIOPSTimeToFullChargeKey`** — pick by charging state; the other is meaningless.
- **Capacity is already a percentage** on modern macOS, but compute `current/max` defensively in case `max` isn't exactly 100.
- Same sampler skeleton as CPU/disk/network (`DispatchSourceTimer` + value-type `Sendable` sample + `[weak self]` callback → `@MainActor`), minus the delta state.

**Best for:** a permission-free stats utility needing battery/power state, and as the canonical reminder of the Copy/Get `Unmanaged` ownership rule for any IOKit work. Sibling of #66/#68 (same sampler family). Pairs with #70 (data-driven strip that filters the battery tile on desktops), #65 (HUD), #67 (jitter-free readout).
