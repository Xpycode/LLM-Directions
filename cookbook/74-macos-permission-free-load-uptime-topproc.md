# Permission-free load average / uptime / top-process — and the libproc same-user gate

**Source:** `1-macOS/QuickStatsPanel/` — `Sampling/{LoadAverageSampler,UptimeSampler,TopProcessSampler}.swift` (2026-06-05, v0.1.x). Phase A of the stat-tile roadmap; siblings of #66 (disk), #68 (network), #69 (battery) — same sampler family.

Three more permission-free Mac stats for a HUD/utility. Load average and uptime are one-call libc/sysctl reads. Top-process is the interesting one: it *looks* like it needs elevated privileges (it doesn't, mostly) and the exact reason is a kernel-source detail worth writing down.

All three are **absolute snapshots** — no `previous…` baseline, no first-tick zero (unlike the delta-based CPU/disk/network counters). Same skeleton as #66/#68/#69: `DispatchSourceTimer` + value-type `Sendable` sample + `[weak self]` callback → `@MainActor`.

## Load average — `getloadavg(3)` (libc, no entitlement)

```swift
private static func readLoad() -> LoadSample {
    var samples = [Double](repeating: 0, count: 3)
    let count = getloadavg(&samples, 3)            // fills 1/5/15-min; returns # written (or -1)
    guard count == 3 else { return .empty }
    return LoadSample(one: samples[0], five: samples[1], fifteen: samples[2])
}

// Load is a RUN-QUEUE DEPTH, not a %. Normalize against online cores for a color band:
var saturationPercent: Double {
    let cores = max(1, ProcessInfo.processInfo.activeProcessorCount)   // active, not total
    return min(100, one / Double(cores) * 100)     // load == cores → ~100% busy
}
```

Guard on `count == 3` — never trust all three slots blindly. Use `activeProcessorCount` (cores online *now*), not `processorCount` (total incl. parked).

## Uptime — `kern.boottime`, **NOT** `ProcessInfo.systemUptime`

```swift
private static func readUptime() -> UptimeSample {
    var tv = timeval()
    var size = MemoryLayout<timeval>.stride
    guard sysctlbyname("kern.boottime", &tv, &size, nil, 0) == 0 else { return .empty }
    let boot = Double(tv.tv_sec) + Double(tv.tv_usec) / 1_000_000.0
    return UptimeSample(seconds: max(0, Date().timeIntervalSince1970 - boot))
}
```

**The trap:** `ProcessInfo.systemUptime` only counts time the Mac has been *awake* — it silently drops sleep time, so on any laptop it reads hours/days low. `kern.boottime` is the wall-clock boot instant, so `now - boottime` matches `uptime(1)` and Activity Monitor. (Trade-off: it shifts if the system clock is adjusted — which *is* the conventional meaning of uptime.)

Format two largest units for a stable readout that doesn't churn every second: `"3d 4h"` / `"4h 12m"` / `"12m 30s"` / `"45s"`.

## Top process by memory — `libproc` (the reason this entry exists)

```swift
import Darwin   // libproc

private static func readTopByMemory() -> TopProcessSample {
    let needed = proc_listallpids(nil, 0)                       // size, then fill with slack
    guard needed > 0 else { return .empty }
    let capacity = Int(needed) / MemoryLayout<pid_t>.stride + 32
    var pids = [pid_t](repeating: 0, count: capacity)
    let filled = proc_listallpids(&pids, Int32(capacity * MemoryLayout<pid_t>.stride))
    let count = Int(filled) / MemoryLayout<pid_t>.stride

    var bestPid: pid_t = 0; var bestMem: UInt64 = 0
    for i in 0..<count where pids[i] > 0 {
        var info = rusage_info_v4()
        let rc = withUnsafeMutablePointer(to: &info) { ptr -> Int32 in
            ptr.withMemoryRebound(to: rusage_info_t?.self, capacity: 1) {   // see note
                proc_pid_rusage(pids[i], RUSAGE_INFO_V4, $0)
            }
        }
        guard rc == 0 else { continue }                          // EPERM for foreign uid → skip
        if info.ri_phys_footprint > bestMem { bestMem = info.ri_phys_footprint; bestPid = pids[i] }
    }
    guard bestPid != 0 else { return .empty }
    return TopProcessSample(name: name(of: bestPid), memoryBytes: bestMem, pid: bestPid)
}

private static func name(of pid: pid_t) -> String {            // proc_pidpath, not proc_name
    var buf = [CChar](repeating: 0, count: Int(4 * MAXPATHLEN))  // proc_name truncates to 16 chars
    if proc_pidpath(pid, &buf, UInt32(buf.count)) > 0 {
        return (String(cString: buf) as NSString).lastPathComponent
    }
    return "pid \(pid)"
}
```

**The permission gate (verified in XNU `bsd/kern/proc_info.c` → `proc_security_policy`).** Each `proc_info` flavor is tagged `NO_CHECK_SAME_USER` or `CHECK_SAME_USER`. The same-user check is bypassed only by `PRIV_GLOBAL_PROC_INFO`, which **root** holds and ordinary apps do not. There is **no Hardened-Runtime entitlement** that grants it (`com.apple.security.cs.debugger` is a different code path — `task_for_pid`, not `proc_pidinfo`).

| Call / flavor | Gate | Other users' procs unprivileged? |
|---|---|---|
| `proc_listallpids`, `proc_pidpath`, `PROC_PIDT_SHORTBSDINFO` | `NO_CHECK_SAME_USER` | **YES** — full PID list + name/path for anything |
| `PROC_PIDTASKINFO`, `proc_pid_rusage` (memory/CPU) | `CHECK_SAME_USER` | **NO → EPERM (-1)** |

So unprivileged you get a clean per-call **EPERM** for foreign-UID processes (kernel_task, WindowServer, root daemons) and full data for **your own** processes — i.e. honestly **"top *user* process"** (the apps the user launched), not literally the heaviest thing on the machine. This is exactly how `top`/htop behave without `sudo`. True system-wide top needs a **privileged root helper** (`sysmond`, how Activity Monitor does it) — which breaks a zero-permission stance, so reject it for a glance HUD.

**Memory before CPU.** `ri_phys_footprint` (matches Activity Monitor's "Memory" column; plain `pti_resident_size` over-reports shared pages) is a **snapshot** → correct on the very first summon. Per-process CPU% is **delta-based** (two ticks ≥1 interval apart) → reads blank on the first frame of every summon unless you keep sampling while hidden. Ship memory first; CPU is the fast-follow.

## Gotchas

- **`proc_pid_rusage` needs the rebind dance.** Its C param is `rusage_info_t *` where `rusage_info_t` is an opaque `void *`, so Swift imports it as `UnsafeMutablePointer<UnsafeMutableRawPointer?>`. You can't pass `&info` directly — `withMemoryRebound(to: rusage_info_t?.self, capacity: 1)` reinterprets your typed `rusage_info_v4` buffer as the pointer the kernel fills.
- **`proc_name` truncates to 16 chars** (the `comm` field) → every Electron helper looks identical. Use `proc_pidpath().lastPathComponent` for a real name.
- **Cost:** ~600 PIDs/tick, one syscall each ≈ 1–3 ms on Apple Silicon — fine on a ≥1 s timer. EPERM-skips are *cheaper* than successful calls (kernel bails at the gate). Resolve the name only for the single winner, not every PID. Note it runs even while the panel is hidden (consistent with other always-on samplers) — gate to visibility later if power matters.
- **`getloadavg`/`kern.boottime`/`libproc` are all sandbox-safe + Hardened-Runtime-safe**, no `NSUsageDescription`, no TCC prompt.

## Bonus: the `knownStats` settings-migration trap

Adding a stat to a data-driven strip (#70) that persists user enable/disable: a **disabled** stat and a **brand-new** stat are indistinguishable if you only persist the *enabled* set (both are simply absent). Naively unioning "missing" cases re-enables anything the user turned off — forever. Fix: persist a separate `knownStats` record (every kind ever shown); new = `allCases − known` → default those on, honor the rest. Seed `known` with the legacy set on first upgrade.

```swift
let legacyKnown: Set<StatKind> = [.cpu, .memory, .disk, .network, .battery]
let known = (defaults.array(forKey: Keys.knownStats) as? [String])
    .map { Set($0.compactMap(StatKind.init(rawValue:))) } ?? legacyKnown
enabled.formUnion(StatKind.allCases.filter { !known.contains($0) })   // new kinds default ON
defaults.set(StatKind.allCases.map(\.rawValue), forKey: Keys.knownStats)
```

**Best for:** a permission-free stats utility wanting load/uptime/top-process, and as the canonical reference for the **libproc same-user gate** (any "list processes" feature). Siblings #66/#68/#69 (sampler family). Pairs with #70 (data-driven strip + the `knownStats` migration), #65 (HUD), #67 (jitter-free readout — top-process puts the variable-width name in a popover, value stays fixed-width).
