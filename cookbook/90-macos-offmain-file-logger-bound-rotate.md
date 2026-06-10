# 90 — Off-main file logger: mirror an in-memory feed to disk, bounded + rotated (sandbox-aware)

**Problem.** You have an `@Observable @MainActor` logger feeding a live in-app console — newest-first array, great for a Debug Console view. But it's **in-memory only**: the moment the user quits, every log line is gone, so a bug report tells you nothing. And the array grows **unbounded** — a long session leaks RAM one log line at a time. This is a `/minimums` ship gap: *diagnostic logging to disk* is a baseline, not a nicety.

The naive fix — `try String(contentsOf:) + "\n" + line` then `.write(to:)` inside the `@MainActor log()` — is wrong twice over: it does **file I/O on the main thread** (jank when you log from a hot path like export/waveform), and it **rewrites the whole file every call** (O(n²) as the log grows).

## Pattern — a non-isolated `Sendable` writer on a private serial queue; format on the producer, append with `seekToEnd`

Keep the `@MainActor` logger for the UI feed. Hand each already-formatted line to a separate **non-isolated `Sendable`** writer whose only job is I/O, serialized on its own `DispatchQueue` — off-main, and ordered (lines land in call order without a lock).

```swift
@Observable
@MainActor
final class Logger {
    static let shared = Logger()

    private(set) var messages: [LogMessage] = []   // live feed for the console view
    private let maxInMemory = 500                   // RAM bound (oldest dropped)

    private let consoleFmt: DateFormatter           // HH:mm:ss.SSS for the on-screen feed
    private let fileFmt = ISO8601DateFormatter()    // date-stamped + sortable for disk
    private let fileWriter = LogFileWriter()

    func log(_ message: String) {
        let entry = LogMessage(timestamp: Date(), message: message)
        messages.insert(entry, at: 0)
        if messages.count > maxInMemory {           // bound #1: in-memory feed
            messages.removeLast(messages.count - maxInMemory)
        }
        // Format HERE (on the main actor), pass a plain String to the writer, so the
        // writer never touches a DateFormatter from a background queue.
        fileWriter.append("[\(fileFmt.string(from: entry.timestamp))] \(message)\n")
    }

    /// For a "Reveal in Finder" menu item — the on-disk log most users can't navigate to.
    nonisolated var diagnosticLogURL: URL { fileWriter.logURL }
}

/// All work runs on a private serial queue → off-main AND ordered, no lock needed.
/// Every stored property is immutable, so the type is genuinely `Sendable`.
private final class LogFileWriter: Sendable {
    private let queue = DispatchQueue(label: "com.acme.app.logwriter", qos: .utility)
    let logURL: URL
    let rotatedURL: URL
    private let maxBytes: UInt64 = 5 * 1024 * 1024   // bound #2: disk ceiling

    init() {
        // SANDBOX: .applicationSupportDirectory is redirected to the app's container
        // (~/Library/Containers/<bundleid>/Data/Library/Application Support/), which is
        // writable with NO entitlement — unlike network.client for Sparkle. No special-casing.
        let appSupport = FileManager.default
            .urls(for: .applicationSupportDirectory, in: .userDomainMask).first!
        let folder = appSupport.appendingPathComponent("AppName", isDirectory: true)
        try? FileManager.default.createDirectory(at: folder, withIntermediateDirectories: true)
        logURL     = folder.appendingPathComponent("diagnostic.log")
        rotatedURL = folder.appendingPathComponent("diagnostic.log.1")
    }

    func append(_ line: String) {
        queue.async { [self] in
            rotateIfNeeded()
            guard let data = line.data(using: .utf8) else { return }
            if let h = try? FileHandle(forWritingTo: logURL) {
                defer { try? h.close() }
                _ = try? h.seekToEnd()           // O(1) append, NOT a whole-file rewrite
                try? h.write(contentsOf: data)
            } else {
                try? data.write(to: logURL, options: .atomic)  // first write / post-rotation
            }
        }
    }

    /// Always on `queue` (serial) → no locking. After this returns, `append` must be
    /// able to write/create `logURL`. One generation kept; I/O errors swallowed.
    private func rotateIfNeeded() {
        let fm = FileManager.default
        guard let size = (try? fm.attributesOfItem(atPath: logURL.path)[.size]) as? UInt64,
              size >= maxBytes else { return }
        try? fm.removeItem(at: rotatedURL)        // drop stale backup (no-op if absent)
        try? fm.moveItem(at: logURL, to: rotatedURL)
    }
}
```

Wire the reveal affordance into the menu (Help is the conventional bug-report slot):

```swift
CommandGroup(after: .help) {
    Button("Reveal Diagnostic Log in Finder") {
        NSWorkspace.shared.activateFileViewerSelecting([Logger.shared.diagnosticLogURL])
        // activateFileViewerSelecting SELECTS the file (doesn't open it) — right for a .log,
        // which would otherwise launch Console.app / a text editor the user didn't ask for.
    }
}
```

## Why each decision

- **Separate writer class, not inline I/O.** The logger is `@MainActor`; any file work inside it blocks the main thread. The writer is *non-isolated* + `Sendable` with its own serial queue, so appends run off-main while still landing in order.
- **Serial queue = ordering for free.** No `NSLock`, no actor hop. The queue *is* the synchronization; concurrent `log()` calls from many threads enqueue and drain in order.
- **`seekToEnd` + append, not `String.write(to:)`.** The latter is O(n) per call → O(n²) over the session. Seek-and-append is O(1)/line.
- **Two bounds, two lifetimes.** The in-memory array is capped (~500) for RAM; the *file* is rotated at a byte ceiling for disk. Different resources, different limits — don't conflate them.
- **Format on the producer.** Build the timestamped string on the main actor and pass a plain `String`; the writer never shares a `DateFormatter`/`ISO8601DateFormatter` across threads.
- **ISO-8601 on disk, `HH:mm:ss` on screen.** The disk log spans days and gets diffed/grepped → needs a date-stamped, sortable timestamp; the live console only needs wall-clock.
- **Swallow I/O errors (`try?`).** A *diagnostic* logger must never crash or stall the app it observes. Best-effort is correct here — the opposite of where you'd normally avoid `try?`.
- **Public API unchanged.** `log(_:)` / `clearLogs()` / `messages` keep the same signatures, so existing call sites and the console view need zero edits — you're adding a sink, not reshaping the type.

## Gotchas

- **Don't go looking in `~/Library/Application Support/AppName/` for a sandboxed app** — it's in `~/Library/Containers/<bundleid>/Data/Library/Application Support/AppName/`. That's exactly why the "Reveal in Finder" menu item matters: users can't navigate there, and Library is hidden by default. Ship the log *and* its discoverability together.
- **Marking the writer `Sendable` (not `@unchecked`) is honest here** only because every stored property is a `let` of a `Sendable` type (`URL`, `DispatchQueue`, `UInt64`). Add a `var` and you owe a real synchronization story.
- **Rotation keeps one generation** → disk bounded at ~2× `maxBytes`. Want history? Add `.log.2`/`.log.3` (ring), but each generation is more disk and more code — one is usually enough for bug reports.
- **`clearLogs()` clears the in-memory feed only** by design (it's a UI affordance); the on-disk log is the durable record and isn't erased by it. Decide explicitly if you want a separate "clear on disk" path.

**Source.** Penumbra `Utils/Logger.swift` + `App/PenumbraApp.swift` (Help-menu reveal), 2026-06-10. Distinct from **#16** (Sparkle auto-update) — this is the *diagnostic logging* `/minimums` baseline, the other is *auto-update*. Pairs with **#85** (phase-aware subprocess watchdog) and **#75** (permission-free system stats) as the macOS-ship infrastructure cluster.
