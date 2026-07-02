# Privileged subprocess: detect the privilege-failure, don't show a false "running" — and `fs_usage` needs root, not Full Disk Access

**Source:** `1-macOS/StatsWindow/` — `Sampling/FSUsageSampler.swift` + `AppStore.swift` (2026-07-01).

You spawn a **root-only** CLI tool (here `/usr/bin/fs_usage`) with `Foundation.Process` and stream its stdout. The trap: **`process.run()` succeeds when the binary merely _launches_**, not when it's actually doing its job. `fs_usage` without root prints `'fs_usage' must be run as root...` to **stderr** and exits milliseconds later — but `run()` already returned success, so a naive app sets `state = .running` and shows a green "live" badge over a table that will never fill. There's no way for the user to tell "no activity" from "denied privileges."

**Fix: treat launch-success and data-flowing as two different facts.** Detect the early exit via `terminationHandler`, classify it from stderr, and report it back. Only claim "running" once the **first parsed event** actually arrives.

```swift
func start(
    onEvent: @escaping @Sendable (IOEvent) -> Void,
    onTerminate: @escaping @Sendable (String) -> Void      // called if it dies on its own
) async throws {
    guard process == nil else { throw SamplerError.alreadyRunning }

    let p = Process()
    p.executableURL = URL(fileURLWithPath: "/usr/bin/fs_usage")
    p.arguments = ["-w", "-f", "filesys"]
    let pipe = Pipe(), errorPipe = Pipe()
    p.standardOutput = pipe
    p.standardError = errorPipe

    // fs_usage refuses to run without root: prints to stderr and exits immediately,
    // yet p.run() still succeeds because the binary launched. Catch that here.
    p.terminationHandler = { proc in
        let err = String(data: errorPipe.fileHandleForReading.readDataToEndOfFile(),
                         encoding: .utf8) ?? ""
        let reason: SamplerError =
            err.range(of: "root", options: .caseInsensitive) != nil
            || err.range(of: "permission", options: .caseInsensitive) != nil
            ? .privilegesRequired
            : .terminatedUnexpectedly(status: proc.terminationStatus)
        onTerminate(reason.errorDescription ?? "subprocess stopped unexpectedly")
    }

    do { try p.run() } catch { throw SamplerError.launchFailed(underlying: error) }
    self.process = p
    // … detached read loop calls onEvent(parse(line)) …
}

func stop() {
    readTask?.cancel(); readTask = nil
    process?.terminationHandler = nil   // detach FIRST, so our own terminate() isn't a "failure"
    process?.terminate(); process = nil
}
```

Caller (an `@Observable @MainActor` store) drives a four-state machine — the badge only goes green on real data:

```swift
try await fs.start(
    onEvent: { [weak self] event in
        Task { @MainActor in
            guard let self else { return }
            if self.samplerState == .starting { self.samplerState = .running } // first event = proof
            self.ioEvents.ingest(event)
        }
    },
    onTerminate: { [weak self] message in
        Task { @MainActor in
            guard let self, self.samplerState != .stopped else { return }        // ignore our own stop()
            self.samplerState = .failed(message)
        }
    }
)
// NOTE: do NOT set .running right after start() returns — that's the false-"live" bug.
// State stays .starting until the first event (fs_usage streams nothing until it's really running).
```

**The companion gotcha — root ≠ Full Disk Access (this wastes an afternoon):**

- **`fs_usage` needs root (uid 0).** `man fs_usage`: *"requires root privileges due to the kernel tracing facility it uses to operate."* The binary is **not setuid** (`-rwxr-xr-x root wheel`).
- **Full Disk Access does NOT substitute.** FDA is a TCC **file-access** consent; it never changes your uid. Granting a normal double-click app FDA leaves `fs_usage` still printing "must be run as root." (If your app's error text says "run with sudo *or* grant Full Disk Access" — that half is wrong for `fs_usage`.) These are two orthogonal privilege systems people constantly conflate.
- **`sudo`-launching the GUI app is a dead end too.** A root GUI process launched from Terminal can't attach to the logged-in user's WindowServer → no window draws → your view's `.onAppear` never fires → the sampler never starts (you'll see the app process alive but **no child `fs_usage`**, the tell-tale).
- **Pragmatic workaround — stdin-bridge:** run the privileged tool in the shell and pipe into the user-run app, which reads stdin instead of spawning the tool: `sudo fs_usage -w -f filesys | MyApp`. `fs_usage` gets root; the app runs as you with a normal window. Great for dev/testing and a usable daily wrapper.
- **Shipping answer:** a small **root helper installed via `SMAppService`** (one-time admin auth) that runs the tool and streams data back over a pipe/XPC — so the app works by double-click. Bigger build; defer until you actually ship.

**Gotchas**
- **`SamplerError` stays non-`Sendable`-safe by passing a `String` across the callback**, not the enum (it has an `Error` associated value). The sampler formats the user-facing message; the store just displays it.
- **Read stderr inside the `terminationHandler`**, after exit — the write end is closed, so `readDataToEndOfFile()` returns promptly instead of blocking.
- **Classify by stderr text, fall back on exit status.** An unprompted early exit of a streaming tool is almost always a privilege problem; the `root`/`permission` check just gives the nicer message.
- **Verifying without Screen Recording permission:** you can't `screencapture` the window, but `pgrep -lf <tool>` (child present or not) and `ps -axo user,pid,comm | grep <App>` (owner = root vs user) tell you what actually happened. See **#73**.

**Best for:** any macOS app that shells out to a privileged/root-only CLI (`fs_usage`, `dtrace`, `powermetrics`, `nettop -P`) and needs its status indicator to be **honest** — green only when data is truly flowing, and a real "needs root" message otherwise. The **inverse** of **#66** (which avoids `fs_usage` entirely for a permission-free HUD); reach for this one when you genuinely need the per-file-path granularity only the privileged trace gives.
