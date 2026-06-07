# Top processes by CPU / memory / disk, grouped by app — two engines (in-process vs. `top`)

**Source:** `1-macOS/QuickStatsPanel/` — `Sampling/TopProcessSampler.swift` (2026-06-05, v0.1.x). Sequel to #74 (top-by-memory): adds **CPU% + disk-I/O rates**, **app grouping**, and folds the lists into the CPU/Mem/Disk tile popovers (iStat-Menus style) instead of a standalone tile.

> ## ⚖️ Decide first: which engine?
> There are **two** ways to build these lists, and the choice is forced by a hard OS limit (proven below), not preference:
>
> | | **Engine A — in-process `rusage`** | **Engine B — shell out to `/usr/bin/top`** |
> |---|---|---|
> | Sees | **Only YOUR processes** (same-user gate) | **Every** process incl. WindowServer, kernel_task |
> | Permission | None | None (entitlement rides with the `top` binary) |
> | Sandbox-safe | ✅ Yes | ❌ **No** — can't spawn `top` under App Sandbox |
> | Cost | Cheap (~1–3 ms/tick), can run always | Costly (`top` itself ~8% CPU) → gate to UI-visible |
> | Per-process disk I/O | ✅ Yes (`ri_diskio_*`) | ❌ No — `top` has no disk column |
> | CPU% math | **You** convert mach units (the trap, below) | `top` does the delta — no math |
>
> **Pick A** if you're sandboxed (Mac App Store) or only care about the user's own apps. **Pick B** if you need the system-process picture Activity Monitor shows (on an idle Mac the *real* CPU hogs — WindowServer, kernel_task — are exactly the ones A can't see) **and** you ship outside the sandbox (direct/notarized). A common move: **B with an A fallback** when `top` can't be spawned.

Both engines share the **app-grouping** machinery (`appGroupName(forPath:)` + `proc_pidpath`, below) and the **popover shape** (#70). Engine A is the original (builds on #74's libproc same-user gate — read that for *why* it's "top **user** processes"); its three research-hard parts are the **mach-time-units gotcha**, **grouping helper PIDs by app**, and **why XPC services can't be tied to their host app**. Engine B is the escape hatch when you need system processes.

## Engine A — in-process `rusage`: one pass → three rankings

The same struct #74 reads for memory also carries CPU time and disk bytes. Read it once per PID, rank three ways. Memory is a snapshot (correct on tick 1); CPU and disk are **two-tick rates** (cumulative→delta, like #66 disk / #68 network, but keyed per-PID).

```swift
let cpuMach   = info.ri_user_time &+ info.ri_system_time           // mach units — see trap
let diskBytes = info.ri_diskio_bytesread &+ info.ri_diskio_byteswritten   // bytes, cumulative
let mem       = info.ri_phys_footprint                             // bytes, snapshot
```

State carried between ticks: `prevCPU[pid]`, `prevDisk[pid]`, and `prevWall` (a `mach_absolute_time()` stamp). Prune the per-PID maps to live PIDs each tick so they can't grow unbounded and a recycled PID can't carry a stale baseline.

## ⚠️ The trap: `ri_user_time`/`ri_system_time` are MACH UNITS, not nanoseconds

Verified in XNU `osfmk/kern/bsd_kern.c` `fill_task_rusage` — the kernel assigns `rm_time_mach` straight through with **no `absolutetime_to_nanoseconds()`**. On Apple Silicon a mach tick ≈ 41.67 ns (timebase 125/3), so treating these as nanoseconds under-reports CPU **~24×**. (Intel's timebase is 1:1, which is why the bug only shows on Apple Silicon — see osquery #7459.) `ri_diskio_*` and `ri_phys_footprint` *are* bytes; only the time fields are mach units.

```swift
// Compute once — timebase is fixed for the process lifetime.
private static let secondsPerMachTick: Double = {
    var tb = mach_timebase_info_data_t(); mach_timebase_info(&tb)
    return Double(tb.numer) / Double(tb.denom) / 1_000_000_000
}()

let wall = mach_absolute_time()
let elapsedSec = prevWall == 0 ? 0 : Double(wall &- prevWall) * Self.secondsPerMachTick
// ... per PID, with a previous sample:
let cpuPct = Double(cpuMach &- prev) * Self.secondsPerMachTick / elapsedSec * 100   // >100% on multicore
let diskRate = Double(diskBytes &- prev) / elapsedSec                                // bytes/sec
```

For CPU% the timebase actually cancels (mach÷mach), but converting both to seconds keeps the formula explicit and reusable for the disk rate, which genuinely needs real seconds.

## Engine B — shell out to `/usr/bin/top` (system-inclusive)

**The hard limit that forces this engine.** Engine A is "top **user** processes" not by choice but because XNU same-user-gates *every* per-process CPU/mem API — not just `proc_pid_rusage`. Proven with two throwaway probes (`swift file.swift`, run unprivileged):

```swift
proc_pid_rusage(pid, RUSAGE_INFO_V4, …)          // foreign UID → EPERM
proc_pidinfo(pid, PROC_PIDTASKINFO, 0, &ti, sz)  // foreign UID → rc 0 (fails); rc==size only for OUR pids
// kernel_task (pid 0) and WindowServer (_windowserver) → both fail; our own pid → both succeed
```

So **no in-process libproc call can ever read a foreign process's CPU/mem.** `top` and Activity Monitor see everything only because they're Apple-signed binaries carrying the **private `com.apple.private.proc_info-list` entitlement** (unobtainable by third parties). The escape: the entitlement rides with the **binary**, so *shelling out* to `/usr/bin/top` runs the subprocess with top's credentials — you get the full list, still **no permission prompt to the user**. (`proc_pidpath`, used for grouping, is the one exception that *does* work cross-user — see below.)

**Spawn + parse.** `top` computes its own CPU% delta, so run `-l 2` (two samples) and parse the **second** — instantaneous, no rate math, no prev-tick state. Put `command` **last** in `-stats` so process names with spaces survive a whitespace split:

```swift
// per tick, on a background queue (blocks ~1s until top exits — fine off-main):
let p = Process(); p.executableURL = URL(fileURLWithPath: "/usr/bin/top")
p.arguments = ["-l","2","-s","1","-o","cpu","-stats","pid,cpu,mem,command"]
let pipe = Pipe(); p.standardOutput = pipe; p.standardError = .nullDevice
try? p.run()
let myTopPID = p.processIdentifier                       // for the observer-effect filter
let out = String(data: pipe.fileHandleForReading.readDataToEndOfFile(), encoding: .utf8) ?? ""
p.waitUntilExit()

// rows of the LAST sample = everything after the final "PID …" header line:
let lines = out.split(separator: "\n", omittingEmptySubsequences: false)
guard let hdr = lines.lastIndex(where: { $0.hasPrefix("PID") }) else { return }
for line in lines[(hdr+1)...] {
    let f = line.split(separator: " ", omittingEmptySubsequences: true)   // pid cpu mem command…
    guard f.count >= 4, let pid = pid_t(f[0]), let cpu = Double(f[1]) else { continue }
    if pid == myTopPID { continue }                      // skip our own probe (see Gotchas)
    let mem = parseMem(f[2])                             // "13M"/"3360K"/"1.2G" → bytes (binary; strip trailing +/-)
    let app = appGroupName(forPath: path(of: pid), fallback: f[3...].joined(separator: " "))
    cpuByApp[app, default: 0] += cpu; memByApp[app, default: 0] += mem
}
```

**Grouping survives** — `proc_pidpath` *is* permission-free for any PID (verified: it resolved WindowServer's real `/System/Library/PrivateFrameworks/SkyLight…` path), so the same `appGroupName(forPath:)` below works. Add a **fallback to `top`'s COMMAND** for pathless procs like `kernel_task` (pid 0, no path).

**Disk I/O is gone in Engine B** — `top` has no per-process disk column, and the only source is the entitled API behind Activity Monitor's *Disk* tab. So Engine B does CPU + memory only; show aggregate Read/Write on the disk tile instead.

**Gate it to UI-visible.** `top` itself costs ~8% CPU, so unlike Engine A's cheap always-on sampler, only run Engine B **while the panel/popover is on screen** — start on show, stop + clear the stale list on hide (in QuickStatsPanel: `StatsStore.setPanelVisible()` driven by the panel's visibility hook, the same one that scopes the Esc hotkey, #72). Cadence `max(2 s, interval)` to leave a gap between the ~1 s `top` runs; the list populates ~1 s after each summon (headline tiles stay instant).

**⚠️ Sandbox kills this engine.** Spawning `/usr/bin/top` is blocked under the App Sandbox — verify your entitlements (`com.apple.security.app-sandbox` = false) before relying on it, and keep Engine A as the Mac-App-Store fallback.

## Group helper PIDs by app — sum FIRST, rank SECOND
*(shared by both engines — Engine A feeds it readable PIDs, Engine B feeds it `top`'s rows)*

A browser/editor spawns N helper PIDs; a flat list just repeats `… Helper (Renderer)`. Group by app. **Order matters:** twenty Chrome helpers at 2% each are individually below any top-N cutoff, but **summed** they're 40% and should lead. So aggregate every readable PID into an `[appName: Double]` map, *then* rank — ranking individuals first would drop the siblings before they could add up.

```swift
var byApp: [String: Double] = [:]
for pid in readablePIDs {
    byApp[appGroupName(of: pid), default: 0] += value(pid)   // sum across the app's PIDs
}
let top = byApp.sorted { $0.value > $1.value }.prefix(5)     // rank the groups
```

Grouping defeats #74's "resolve the name for the winner only" optimization — you must know every PID's app *before* ranking. Restore the cost with a **per-PID name cache** (`proc_pidpath` is stable for a PID's life): resolve once, dictionary-hit forever after, prune to live PIDs each tick.

## `appGroupName(forPath:)` — three tiers for three executable layouts

```swift
static func appGroupName(forPath path: String) -> String {
    let parts = path.split(separator: "/")
    // 1. Outermost .app bundle (first from the root) = owning app — helpers in
    //    deeper nested .apps roll up to the top-level app (how Activity Monitor groups).
    if let app = parts.first(where: { $0.hasSuffix(".app") }) { return String(app.dropLast(4)) }
    // 2. .xpc/.appex service with no .app ancestor → prettify the bundle id
    //    e.g. com.apple.WebKit.WebContent.xpc → "Web Content".
    if let svc = parts.first(where: { $0.hasSuffix(".xpc") || $0.hasSuffix(".appex") }) {
        return prettify(svc.hasSuffix(".appex") ? svc.dropLast(6) : svc.dropLast(4))
    }
    // 3. Plain executable — but climb past version-like tokens + generic launcher
    //    dirs so …/claude/versions/2.1.165 → "claude", not "2.1.165".
    var i = parts.count - 1
    while i > 0 {
        let c = parts[i]
        if isVersionLike(c) || genericPathComponents.contains(String(c)) { i -= 1; continue }
        return String(c)
    }
    return parts.last.map(String.init) ?? "—"
}

private static func prettify(_ id: Substring) -> String {        // reverse-DNS → last comp → camelCase split
    let leaf = id.split(separator: ".").last ?? id               // com.apple.WebKit.WebContent → WebContent
    var out = ""
    for ch in leaf {
        if ch.isUppercase, let p = out.last, !p.isUppercase || p.isNumber { out.append(" ") }
        out.append(ch)                                           // WebContent → "Web Content"
    }
    return out.isEmpty ? String(id) : out
}
private static let genericPathComponents: Set<String> =
    ["versions","version","bin","sbin","libexec","current","MacOS","Contents","Resources"]
private static func isVersionLike(_ s: Substring) -> Bool {
    !s.isEmpty && s.allSatisfy { $0.isNumber || $0 == "." } && s.contains(where: \.isNumber)
}
```

The three tiers map to the three ways macOS actually lays out executables — each was forced by a real process: Chrome helpers (`.app` nesting), `com.apple.WebKit.WebContent` (`.xpc` reverse-DNS), and the Claude CLI's `…/versions/2.1.165` version-named binary. **Unit-test the path logic standalone** (`swift file.swift` with hardcoded real paths) before rebuilding the app — far faster than summon-screenshot loops.

For Engine B, give this a `fallback:` parameter (top's COMMAND text) and return it instead of `"—"` when `path` is empty — `kernel_task` (pid 0) and a few daemons have no `proc_pidpath`, but `top` still names them.

## Why XPC services can't be tied to their host app (permission-free)

WebKit content/networking procs are XPC services: no `.app` in their path, and their **parent is `launchd` (pid 1)**, so `ppid` (`proc_pidinfo`) is useless for attribution. The only thing that maps `WebContent` → Safari is the responsible-PID lineage, exposed by:
- `responsibility_get_pid_responsible_for_pid()` — **private** (libquarantine, no header; permission-free for same-user but App-Store-rejecting and OS-fragile). What Activity Monitor uses.
- ES `responsible_audit_token` — public but needs an Apple-granted entitlement + Full Disk Access.

Neither fits a clean permission-free utility, so **prettify the name and accept partial data**: all browsers' content procs group into one summed **"Web Content"** row, not split per host. (exelban/Stats hit the same wall — closed both "group by app" and "name the website" as not-planned.)

## iStat-Menus shape: lists live in the metric's popover

No standalone "top process" tile — the CPU dropdown shows top-by-CPU, Memory shows top-by-memory, Disk shows top-by-disk. With a data-driven strip (#70) this is an optional `ProcessSection` on the descriptor, rendered under the detail rows and **auto-hidden while empty** so two-tick CPU/disk rates don't flash an empty header on the first summon. Retiring the old standalone `StatKind` needs **no migration** — `compactMap(StatKind.init(rawValue:))` silently drops the stale persisted rawValue.

## Gotchas

- **CPU% can exceed 100%** (per-core, like Activity Monitor) — don't clamp or divide by core count if you want the familiar "742%" reading. (Both engines; `top`'s column is already per-core.)
- **Memory grouping double-counts shared pages** (summing `phys_footprint` / `top`'s MEM across helpers) — the same over-count Activity Monitor's non-grouped view has; fine for a glance.
- **Threshold the group, not the process** — drop sub-cutoff groups *after* summing, else you'd discard helpers that matter in aggregate. **On an idle Mac, drop the threshold entirely** (show genuine top-N even at "0,4%"), or the list reads near-empty — display 1-decimal locale percent so small values don't all round to "0%".
- **Rate lists are blank on the first tick of every summon** — Engine A: memory fills immediately, CPU/disk on tick 2 (#74's note). Engine B: the whole list lands ~1 s after summon (top's 2-sample window).
- **Engine B — filter your own probe by PID, not name.** The `top` you spawn reports *itself* (~8%, observer effect); exclude `Process.processIdentifier`, never by the string `"top"` (a user's terminal `top` is legitimate).
- **Engine B — popover height jitters** as the active-process count bounces tick to tick; reserve a fixed slot count and pad empties invisibly (#67's worst-case-reserve, applied vertically).
- Engine A only: same `withMemoryRebound(to: rusage_info_t?.self)` dance and EPERM-skip as #74.

**Best for:** a permission-free stats HUD wanting Activity-Monitor-style top-process lists. **The headline lesson:** foreign-process CPU/mem is *impossible* in-process (XNU same-user gate covers all libproc calls) — your only routes are **Engine A** (user-only, sandbox-safe) or **Engine B** (`top` subprocess, system-inclusive, needs sandbox OFF). Also the canonical reference for the **rusage mach-time-units trap** and **path→app grouping** (shared by both engines). Sequel to #74 (same-user gate, top-by-memory); siblings #66/#68/#69 (sampler family); pairs with #70 (data-driven strip + `ProcessSection`), #65 (HUD), #67 (jitter-free readout), #72 (visibility-scoped lifecycle, reused to gate Engine B).
