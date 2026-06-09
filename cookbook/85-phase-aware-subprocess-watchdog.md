# 85 — A no-progress watchdog that doesn't false-alarm during legitimately-silent phases

**Problem.** You run a long subprocess (ffmpeg/ffprobe export, a batch encode, a big upload) and want to warn the user when it's *genuinely* stuck. The naive rule —

```swift
if Date().timeIntervalSince(lastProgress) > 30 { showStuckDialog() }
```

— fires **false positives** during phases that legitimately emit no progress. A real export has at least three:

1. **ANALYZING** (pre-encode) — e.g. an ffprobe keyframe scan reads the whole source file *before* ffmpeg ever spawns. No `out_time`, no bytes out, often 1–2 min on a large clip on a slow volume.
2. **ENCODING** — ffmpeg emits `-progress` lines; this is the only phase where a no-activity stall is actually suspicious.
3. **FINALIZING** (post-encode) — after ffmpeg prints `progress=end`, the muxer flushes the `moov` atom and bytes settle to disk. Progress already pinned 100%; the file isn't done.

A watchdog that only knows "no progress = stuck" will pop a red dialog at 30s during phase 1 or 3 even though the process is working perfectly. (Penumbra shipped exactly this bug twice — once for FINALIZING, then again for ANALYZING — because each silent phase had to be taught to the watchdog separately.)

## Pattern — a pure, phase-aware verdict with a strict precedence ladder

Split the watchdog into (a) a **pure function** that maps `(elapsed-since-activity, current-phase)` → a verdict, and (b) a thin MainActor loop that reads live state and acts on the verdict. The pure function is the whole design; it's `nonisolated static` so every branch and boundary is unit-testable **without spawning a subprocess or touching a volume**.

```swift
enum WatchdogVerdict: Equatable {
    case active          // healthy; recent liveness
    case analyzing       // pre-encode scan / pre-flight → calm, never alert
    case advisoryStall   // mid-encode no-activity → the red "stuck" alert (manual)
    case finalizing      // post-`progress=end` flush tail → calm, never alert
    case hung            // zero-activity past the hard timeout → self-heal
}

/// Ordering matters. The hard-timeout `.hung` backstop OUTRANKS every phase —
/// a scan or flush that never settles is still a hang, so genuine wedges are
/// always reclaimable. Below it, the calm phases suppress the alert; only
/// mid-work no-activity raises the advisory. `nonisolated static` = pure +
/// fully unit-testable.
nonisolated static func watchdogAssessment(
    secondsSinceActivity: TimeInterval,
    isAnalyzing: Bool,
    isFinalizing: Bool,
    encodeStall: TimeInterval,   // e.g. 30s
    hardTimeout: TimeInterval    // e.g. 300s
) -> WatchdogVerdict {
    if secondsSinceActivity > hardTimeout { return .hung }   // backstop wins in EVERY phase
    if isAnalyzing  { return .analyzing }                    // calm
    if isFinalizing { return .finalizing }                   // calm
    if secondsSinceActivity > encodeStall { return .advisoryStall }
    return .active
}
```

**The precedence ladder is the load-bearing decision.** Put the `hardTimeout` check *first*, above the calm phases. That way a genuinely-wedged analysis/flush (e.g. a process stuck in uninterruptible `U`-state I/O on a dying volume) is still declared `.hung` and handed to your self-heal/recovery path — the calm phases only suppress the *advisory* alert, never the hard backstop. (Trade: a *legitimately* huge scan that runs past `hardTimeout` gets falsely abandoned. Size the timeout generously vs. real worst-case, and keep it tunable.)

## Phase signals are dumb per-job flags, set at the transitions

Don't infer the phase — set a flag at each boundary. Two booleans + the "is a job active" check fully disambiguate all three phases:

```swift
private var didStartEncoding = false   // false → ANALYZING window
private var sawProgressEnd   = false   // true  → FINALIZING flush tail

// set false when the job is marked .exporting (BEFORE the pre-encode scan)
// set true at subprocess spawn:           self.didStartEncoding = true
// set true on the `progress=end` line:     self.sawProgressEnd   = true

var isAnalyzing:  Bool { currentJob != nil && !didStartEncoding && !sawProgressEnd }
var isFinalizing: Bool { sawProgressEnd && currentJob != nil }
```

The subtlety that caused the bug: the job is marked `.exporting` (so `currentJob != nil`) **before** the pre-encode scan runs and before the subprocess spawns. If your watchdog only resets its activity clock "when no job is active," it won't reset during that window → 30s later it false-alarms. `didStartEncoding` is what tells the watchdog "the encode clock hasn't legitimately started yet — stay calm."

## The MainActor loop just maps verdict → action

```swift
let verdict = Self.watchdogAssessment(
    secondsSinceActivity: Date().timeIntervalSince(lastActivity),
    isAnalyzing: self.isAnalyzing,
    isFinalizing: self.sawProgressEnd,
    encodeStall: stuckThreshold, hardTimeout: hardTimeout)

switch verdict {
case .active, .analyzing, .finalizing:           // calm — clear any prior alert
    if isStuck { isStuck = false }
case .advisoryStall:                             // the ONLY path that alarms the user
    isStuck = true
case .hung:                                      // genuine wedge → self-heal
    declareHung()                                // SIGTERM→SIGKILL→abandon→advance queue
}
```

## Surface the calm phases in the UI (don't show a frozen bar)

When a phase emits no percentage, show its name + an **indeterminate** bar, not a bar stuck at 0% or 100%:

```swift
if isAnalyzing       { Text("Analyzing…"); ProgressView() }      // indeterminate
else if isFinalizing { Text("Finalizing…") }
else                 { Text("\(Int(progress * 100))%") }
```

## Why this shape

- **Testable core.** The verdict is a pure function over `(TimeInterval, Bool, Bool, TimeInterval, TimeInterval)`. The 30s wait that bit you in the app is a single integer comparison in a test — the whole false-positive regression suite runs in milliseconds. Cover each phase's never-advisory property + the hard-timeout boundary + the precedence (`hung` beats every phase).
- **Extensible.** A new silent phase = one more `if isX { return .x }` line + one flag, slotted into the ladder. You don't re-derive the watchdog.
- **Safe by construction.** Because `hung` sits above the phases, adding a calm phase can never accidentally suppress your genuine-hang recovery.

**Pairs with** a self-healing recovery for the `.hung` verdict (SIGTERM → grace → SIGKILL → grace → resume the suspended `export()` continuation with a non-retryable `.abandoned` error → advance the queue; orphan the PID if it's in un-killable `U`-state I/O). The watchdog *detects*; the recovery *reclaims*.

**One-line tell:** *a subprocess "stuck" dialog fires at your no-progress threshold even though the process is doing real work (a pre-encode scan or a post-encode flush) → the watchdog is phase-blind. Make the verdict a pure phase-aware function with the hard-timeout backstop ranked above the calm phases, drive the phases off flags set at the spawn / `progress=end` transitions, and only `.advisoryStall` (mid-work no-activity) ever alarms the user.*

---
*Source: Penumbra `ExportManager.swift` (`watchdogAssessment`, `WatchdogVerdict`, `startStuckDetection`, `isAnalyzing`/`isFinalizing`) + `ExportWatchdogAssessmentTests.swift`. Shipped + smoke-verified 2026-06-09; suite 285/1/0.*
