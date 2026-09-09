// Standalone experimental worker. Build/run only in the agreed foreground window.
import AppKit
import ApplicationServices
import Darwin

private func continuousNS() -> UInt64 {
    var info = mach_timebase_info_data_t()
    mach_timebase_info(&info)
    let ticks = mach_continuous_time()
    return (ticks / UInt64(info.denom)) * UInt64(info.numer)
        + (ticks % UInt64(info.denom)) * UInt64(info.numer) / UInt64(info.denom)
}

private struct ProcessStart: Equatable {
    let seconds: UInt64
    let microseconds: UInt64
}

// All state and the CF event-tap source belong to the main run loop. AX calls are
// synchronous here; the separate supervisor process enforces the hung-call budget.
@MainActor
private final class Worker {
    var input = Data()
    var partialSince: UInt64?
    var parentHeartbeat = continuousNS()
    let parentPID = getppid()
    var lastHeartbeat: UInt64 = 0
    var target: NSRunningApplication?
    var targetStart: ProcessStart?
    var targetPath: String?
    var bound = false
    var bindDeadline: UInt64 = 0
    var lastFocusFailure = "none"
    var tagBase: Int64 = 0
    var runID = ""
    var nextSequence: Int64 = 1
    var held = false
    var heldTag: Int64 = 0
    var lastUnit: UInt16 = 0
    var stopped = false
    var stopAt: UInt64?
    var tap: CFMachPort?
    var tapSource: CFRunLoopSource?
    let eventSource = CGEventSource(stateID: .privateState)

    func emit(_ event: String, _ fields: [String: Any] = [:]) {
        var row = fields
        row["source"] = "worker"
        row["event"] = event
        row["ns"] = String(continuousNS())
        guard let data = try? JSONSerialization.data(withJSONObject: row, options: [.sortedKeys]) else {
            exit(70)
        }
        // A full pipe can block this process, never its external watchdog.
        FileHandle.standardOutput.write(data + Data([10]))
    }

    func installMonitor() -> Bool {
        let types: [CGEventType] = [.keyDown, .keyUp, .flagsChanged, .leftMouseDown,
            .rightMouseDown, .otherMouseDown, .scrollWheel, .leftMouseDragged,
            .rightMouseDragged, .otherMouseDragged]
        let mask = types.reduce(CGEventMask(0)) { $0 | (CGEventMask(1) << $1.rawValue) }
        let callback: CGEventTapCallBack = { _, type, event, context in
            guard let context else { return Unmanaged.passUnretained(event) }
            // Installed exclusively on CFRunLoopGetMain below; never moved to a thread.
            MainActor.assumeIsolated {
                let worker = Unmanaged<Worker>.fromOpaque(context).takeUnretainedValue()
                worker.observe(type, event)
            }
            return Unmanaged.passUnretained(event) // Listen only; never suppress user input.
        }
        guard let newTap = CGEvent.tapCreate(tap: .cgSessionEventTap,
            place: .headInsertEventTap, options: .listenOnly, eventsOfInterest: mask,
            callback: callback, userInfo: Unmanaged.passUnretained(self).toOpaque()),
            let source = CFMachPortCreateRunLoopSource(kCFAllocatorDefault, newTap, 0)
        else { return false }
        tap = newTap
        tapSource = source
        CFRunLoopAddSource(CFRunLoopGetMain(), source, .commonModes)
        return CGEvent.tapIsEnabled(tap: newTap)
    }

    func observe(_ type: CGEventType, _ event: CGEvent) {
        if type == .tapDisabledByTimeout || type == .tapDisabledByUserInput {
            stop("monitorLost")
            return
        }
        let tag = event.getIntegerValueField(.eventSourceUserData)
        let sourcePID = event.getIntegerValueField(.eventSourceUnixProcessID)
        if tagBase != 0 && tag > tagBase && tag < tagBase + 1024 && sourcePID == Int64(getpid()) {
            emit("ownedObserved", ["tag": tag, "type": type.rawValue])
            return
        }
        // Cleanup key-up may arrive after admission closes; it still needs origin evidence.
        guard !stopped else { return }
        // Escape is the experimental global shortcut; any other unowned key/click/
        // scroll also stops. Origins are candidates until the live tests prove them.
        let escape = type == .keyDown && event.getIntegerValueField(.keyboardEventKeycode) == 53
        stop(escape ? "escape" : "unownedInput")
    }

    func sameInstance() -> Bool {
        guard let target, !target.isTerminated, let current = NSRunningApplication(
            processIdentifier: target.processIdentifier), !current.isTerminated,
            let start = processStart(target.processIdentifier), start == targetStart,
            processExecutable(target.processIdentifier) == targetPath
        else { return false }
        return true
    }

    func processStart(_ pid: pid_t) -> ProcessStart? {
        // Directly spawned AppKit executables can have no Launch Services launchDate.
        // Bind the kernel start identity instead; PID reuse or reparenting must stop input.
        var info = proc_bsdinfo()
        let size = Int32(MemoryLayout<proc_bsdinfo>.size)
        guard proc_pidinfo(pid, PROC_PIDTBSDINFO, 0, &info, size) == size,
            info.pbi_pid == UInt32(pid), info.pbi_uid == geteuid(),
            info.pbi_ppid == UInt32(parentPID), info.pbi_start_tvsec > 0 else { return nil }
        return ProcessStart(seconds: info.pbi_start_tvsec, microseconds: info.pbi_start_tvusec)
    }

    func processExecutable(_ pid: pid_t) -> String? {
        // PROC_PIDPATHINFO_MAXSIZE is (4 * MAXPATHLEN); Swift cannot import that macro.
        var bytes = [CChar](repeating: 0, count: 4 * Int(MAXPATHLEN))
        let count = proc_pidpath(pid, &bytes, UInt32(bytes.count))
        guard count > 0, count < bytes.count,
            let end = bytes.firstIndex(of: 0), end > 0,
            let path = String(bytes: bytes[..<end].map { UInt8(bitPattern: $0) }, encoding: .utf8),
            path.hasPrefix("/"), let canonical = realpath(path, nil) else { return nil }
        defer { free(canonical) }
        // Foundation standardization rewrites /private/var to /var on this Mac;
        // POSIX realpath matches the supervisor's pathlib.resolve contract exactly.
        return String(cString: canonical)
    }

    func attribute(_ element: AXUIElement, _ name: String) -> CFTypeRef? {
        var value: CFTypeRef?
        guard AXUIElementCopyAttributeValue(element, name as CFString, &value) == .success else { return nil }
        return value
    }

    func element(_ value: CFTypeRef?) -> AXUIElement? {
        guard let value, CFGetTypeID(value) == AXUIElementGetTypeID() else { return nil }
        return (value as! AXUIElement)
    }

    func expectedFocus() -> Bool {
        guard sameInstance(), let target else { lastFocusFailure = "instance"; return false }
        guard NSWorkspace.shared.frontmostApplication?.processIdentifier == target.processIdentifier
        else { lastFocusFailure = "frontmost"; return false }
        let app = AXUIElementCreateApplication(target.processIdentifier)
        guard let window = element(attribute(app, kAXFocusedWindowAttribute))
        else { lastFocusFailure = "windowUnavailable"; return false }
        guard attribute(window, kAXIdentifierAttribute) as? String == "stop-spike-window",
            attribute(window, kAXRoleAttribute) as? String == kAXWindowRole
        else { lastFocusFailure = "windowSelector"; return false }
        guard let focus = element(attribute(app, kAXFocusedUIElementAttribute))
        else { lastFocusFailure = "elementUnavailable"; return false }
        guard attribute(focus, kAXIdentifierAttribute) as? String == "stop-spike-text",
            attribute(focus, kAXRoleAttribute) as? String == kAXTextAreaRole
        else { lastFocusFailure = "elementSelector"; return false }
        guard let focusWindow = element(attribute(focus, kAXWindowAttribute)), CFEqual(window, focusWindow)
        else { lastFocusFailure = "elementWindow"; return false }
        lastFocusFailure = "none"
        return true
    }

    func post(down: Bool, tag: Int64, unit: UInt16) -> Bool {
        guard let target, let eventSource,
            let event = CGEvent(keyboardEventSource: eventSource, virtualKey: 0, keyDown: down)
        else { return false }
        event.flags = []
        var value = unit
        event.keyboardSetUnicodeString(stringLength: 1, unicodeString: &value)
        event.setIntegerValueField(.eventSourceUserData, value: tag)
        event.postToPid(target.processIdentifier)
        emit("posted", ["tag": tag, "down": down])
        return true
    }

    func stop(_ reason: String) {
        guard !stopped else { return }
        stopped = true // Admission closes before any cleanup or notification.
        stopAt = continuousNS()
        emit("stopping", ["reason": reason, "focusCheck": lastFocusFailure])
        if held {
            // The paired up tag is reserved by the supervisor before the down event.
            // Release only to the bound target, even if it no longer owns foreground.
            if sameInstance() && post(down: false, tag: heldTag + 1, unit: lastUnit) {
                held = false
            }
        }
        emit("stopped", ["heldKeysEmpty": !held, "clipboard": "untouched"])
        // This acknowledgement proves admission closure, NOT target delivery/drain.
    }

    func receive(_ data: Data) {
        guard !stopped, let row = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
            let op = row["op"] as? String else { stop("invalidMessage"); return }
        switch op {
        case "bind":
            guard target == nil, Set(row.keys) == ["op", "pid", "path", "tagBase", "run"],
                let pid = row["pid"] as? Int32, pid > 1,
                let run = row["run"] as? String, run.utf8.count == 32,
                run.utf8.allSatisfy({ (48...57).contains($0) || (97...102).contains($0) }),
                let path = row["path"] as? String, let base = row["tagBase"] as? Int64,
                base > 0, base < Int64.max - 1024
            else { stop("invalidBindingMessage"); return }
            guard let app = NSRunningApplication(processIdentifier: pid) else {
                stop("targetLookupUnavailable"); return
            }
            guard let start = processStart(pid) else { stop("processIdentityUnavailable"); return }
            guard let executable = processExecutable(pid),
                executable == path, URL(fileURLWithPath: executable).lastPathComponent == "StopSpikeTarget"
            else { stop("artifactMismatch"); return }
            target = app
            targetStart = start
            targetPath = executable
            tagBase = base
            runID = run
            // Launch activation/AX publication is asynchronous. This is a one-use,
            // two-second initial transition, never permission to reclaim lost focus.
            bindDeadline = continuousNS() + 2_000_000_000
        case "heartbeat":
            guard Set(row.keys) == ["op"] else { stop("invalidMessage"); return }
            parentHeartbeat = continuousNS()
        case "stop":
            stop("requested")
        case "event":
            guard Set(row.keys) == ["op", "sequence", "unit", "down"],
                let sequence = row["sequence"] as? Int64, sequence == nextSequence,
                sequence <= 256, let unit = row["unit"] as? UInt16, (32...126).contains(unit),
                let down = row["down"] as? Bool, down == !held,
                down || unit == lastUnit else { stop("invalidEvent"); return }
            guard bound, continuousNS() - parentHeartbeat < 3_000_000_000,
                getppid() == parentPID, let tap, CGEvent.tapIsEnabled(tap: tap),
                AXIsProcessTrusted(), CGPreflightPostEventAccess(), CGPreflightListenEventAccess(),
                expectedFocus()
            else { stop("readinessLost"); return }
            // AX may have taken time. Recheck time and process/focus before each post.
            guard !stopped, continuousNS() - parentHeartbeat < 3_000_000_000,
                sameInstance()
            else { stop("readinessLost"); return }
            guard NSWorkspace.shared.frontmostApplication?.processIdentifier == target?.processIdentifier
            else { lastFocusFailure = "frontmost"; stop("wrongFocus"); return }
            let tag = tagBase + sequence
            nextSequence += 1 // Consumed even if post fails. Never retry unknown input.
            if down { held = true; heldTag = tag; lastUnit = unit }
            guard post(down: down, tag: tag, unit: unit) else { stop("postFailed"); return }
            if !down {
                held = false
                // Distinct from `posted`, which is emitted inside post(). This
                // main-run-loop boundary follows both return and held-state update.
                emit("checkpoint", ["run": runID, "sequence": sequence,
                    "tag": tag, "heldKeysEmpty": !held])
            }
        default:
            stop("unknownOperation")
        }
    }

    func tick() {
        let now = continuousNS()
        if getppid() != parentPID { stop("parentLost") }
        if now - parentHeartbeat >= 3_000_000_000 { stop("heartbeatLost") }
        if let tap, !CGEvent.tapIsEnabled(tap: tap) { stop("monitorLost") }
        if target != nil && !stopped {
            let focus = expectedFocus()
            if !bound {
                if focus && now < bindDeadline {
                    bound = true
                    emit("bound")
                } else if now >= bindDeadline { stop("wrongFocus") }
            } else if !focus { stop("wrongFocus") }
        }
        if let partialSince, now - partialSince >= 3_000_000_000 { stop("partialFrameTimeout") }
        if now - lastHeartbeat >= 100_000_000 {
            emit("heartbeat")
            lastHeartbeat = now
        }
        // Focus checks above can call stop() during this tick, after `now` was sampled.
        // Resample before subtracting so a newly recorded stop cannot underflow UInt64.
        if let stopAt, continuousNS() - stopAt >= 200_000_000 { exit(held ? 2 : 0) }
        var bytes = [UInt8](repeating: 0, count: 1024)
        let count = Darwin.read(STDIN_FILENO, &bytes, bytes.count)
        if count == 0 { stop("parentEOF"); return }
        if count < 0 {
            if errno != EAGAIN && errno != EWOULDBLOCK && errno != EINTR { stop("readFailed") }
            return
        }
        for byte in bytes.prefix(count) {
            if byte == 10 {
                receive(input)
                input.removeAll(keepingCapacity: true)
                partialSince = nil
            } else {
                if input.isEmpty { partialSince = now }
                guard input.count < 1024 else { stop("oversizedFrame"); return }
                input.append(byte)
            }
        }
    }

    func run(preflightOnly: Bool) {
        let accessibility = AXIsProcessTrusted()
        let inputMonitoring = CGPreflightListenEventAccess()
        let eventPosting = CGPreflightPostEventAccess()
        emit("preflight", ["accessibility": accessibility,
            "inputMonitoring": inputMonitoring, "eventPosting": eventPosting])
        // Diagnostic mode never opens a tap, touches stdin, binds a target or posts input.
        if preflightOnly { return }
        signal(SIGPIPE, SIG_IGN)
        let flags = fcntl(STDIN_FILENO, F_GETFL)
        guard flags >= 0, fcntl(STDIN_FILENO, F_SETFL, flags | O_NONBLOCK) == 0 else { exit(70) }
        guard accessibility, inputMonitoring, eventPosting else {
            emit("unavailable", ["reason": "workerPermissionPreflightFailed"])
            return // Never request permission or change TCC automatically.
        }
        guard AXUIElementSetMessagingTimeout(AXUIElementCreateSystemWide(), 0.05) == .success,
            installMonitor() else { emit("unavailable", ["reason": "monitorOrAXTimeoutUnavailable"]); return }
        emit("ready", ["pid": getpid()])
        while true {
            tick()
            CFRunLoopRunInMode(.defaultMode, 0.01, false)
        }
    }
}

@main
private struct StopSpikeWorkerMain {
    @MainActor static func main() {
        let arguments = Array(CommandLine.arguments.dropFirst())
        guard arguments.isEmpty || arguments == ["--preflight"] else { exit(64) }
        Worker().run(preflightOnly: !arguments.isEmpty)
    }
}
