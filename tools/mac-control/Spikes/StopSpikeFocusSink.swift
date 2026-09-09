import AppKit
import Darwin

/// An owned, disposable receiver for focus-loss measurements. All state stays in memory.
/// Compile and launch only in the harness's approved desktop-test window.
@MainActor
private final class FocusSinkRecorder {
    private static let timebase: mach_timebase_info_data_t = {
        var info = mach_timebase_info_data_t()
        mach_timebase_info(&info)
        return info
    }()
    private var recordCount = 0

    static func continuousNanoseconds() -> UInt64 {
        let ticks = mach_continuous_time()
        let numerator = UInt64(timebase.numer)
        let denominator = UInt64(timebase.denom)
        guard denominator != 0 else { exit(70) }
        let (whole, overflow) = (ticks / denominator).multipliedReportingOverflow(by: numerator)
        let remainder = ((ticks % denominator) * numerator) / denominator
        let (result, sumOverflow) = whole.addingReportingOverflow(remainder)
        guard !overflow, !sumOverflow else { exit(70) }
        return result
    }

    func emit(_ event: String, fields: [String: Any] = [:]) {
        // Exhaustion invalidates the run; never silently drop input evidence and continue.
        guard recordCount < 8_192 else { exit(75) }
        recordCount += 1
        var record: [String: Any] = [
            "source": "focusSink", "event": event,
            "pid": Int64(ProcessInfo.processInfo.processIdentifier),
            "ns": String(Self.continuousNanoseconds()),
        ]
        for (key, value) in fields { record[key] = value }
        guard var data = try? JSONSerialization.data(withJSONObject: record),
              data.count < 2_048 else { exit(70) }
        data.append(0x0A)
        // Nonblocking, single small pipe write: a stalled supervisor cannot strand the app.
        let written = data.withUnsafeBytes { bytes in
            Darwin.write(STDOUT_FILENO, bytes.baseAddress, bytes.count)
        }
        guard written == data.count else { exit(74) }
    }
}

@MainActor
private final class FocusSinkApplication: NSApplication {
    let recorder = FocusSinkRecorder()

    override func sendEvent(_ event: NSEvent) {
        let kind: String
        switch event.type {
        case .keyDown: kind = "keyDown"
        case .keyUp: kind = "keyUp"
        case .flagsChanged: kind = "flagsChanged"
        case .leftMouseDown: kind = "leftMouseDown"
        case .leftMouseUp: kind = "leftMouseUp"
        case .rightMouseDown: kind = "rightMouseDown"
        case .rightMouseUp: kind = "rightMouseUp"
        case .otherMouseDown: kind = "otherMouseDown"
        case .otherMouseUp: kind = "otherMouseUp"
        case .mouseMoved: kind = "mouseMoved"
        case .leftMouseDragged: kind = "leftMouseDragged"
        case .rightMouseDragged: kind = "rightMouseDragged"
        case .otherMouseDragged: kind = "otherMouseDragged"
        case .mouseEntered: kind = "mouseEntered"
        case .mouseExited: kind = "mouseExited"
        case .scrollWheel: kind = "scrollWheel"
        default:
            super.sendEvent(event)
            return
        }
        let cgEvent = event.cgEvent
        recorder.emit("inputReceived", fields: [
            "kind": kind,
            "tag": cgEvent?.getIntegerValueField(.eventSourceUserData) ?? 0,
            "sourcePID": cgEvent?.getIntegerValueField(.eventSourceUnixProcessID) ?? 0,
            "hasCGEvent": cgEvent != nil,
            "active": isActive,
        ])
        // Consume input before menu/responder handling. No key characters, clipboard access,
        // text editing, or commands that could mutate user state exist in this receiver.
    }
}

@main
@MainActor
final class StopSpikeFocusSink: NSObject, NSApplicationDelegate {
    private var window: NSWindow?
    private var timer: Timer?
    private var standardInputFlags: Int32?
    private var input = Data()
    private var activationRequested = false
    private var observationComplete = false
    private var lastFocusSampleNS: UInt64 = 0
    private var stopping = false
    private let startNS = FocusSinkRecorder.continuousNanoseconds()

    private var application: FocusSinkApplication {
        guard let application = NSApplication.shared as? FocusSinkApplication else { exit(70) }
        return application
    }

    static func main() {
        guard CommandLine.arguments.count == 1 else { exit(64) }
        signal(SIGPIPE, SIG_IGN)
        let outputFlags = fcntl(STDOUT_FILENO, F_GETFL)
        guard outputFlags != -1,
              fcntl(STDOUT_FILENO, F_SETFL, outputFlags | O_NONBLOCK) != -1 else { exit(74) }
        // Use AppKit's singleton factory on the subclass. Direct init leaves its shared
        // factory uninitialized and finishLaunching then attempts a second NSApplication.
        guard let application = FocusSinkApplication.shared as? FocusSinkApplication else { exit(70) }
        let delegate = StopSpikeFocusSink()
        application.delegate = delegate
        application.setActivationPolicy(.accessory)
        withExtendedLifetime(delegate) { application.run() }
    }

    func applicationDidFinishLaunching(_ notification: Notification) {
        let window = NSWindow(
            contentRect: NSRect(x: 80, y: 80, width: 420, height: 160),
            styleMask: [.titled], backing: .buffered, defer: false
        )
        window.title = "Directions Stop Spike — Focus Sink"
        window.identifier = NSUserInterfaceItemIdentifier("stop-spike-focus-sink-window")
        window.setAccessibilityIdentifier("stop-spike-focus-sink-window")
        window.isReleasedWhenClosed = false
        window.acceptsMouseMovedEvents = true
        window.contentView = NSView(frame: window.contentLayoutRect)
        self.window = window
        // Keep the receiver hidden and inactive until its owner's explicit stdin command.
        guard !application.isActive else { stop(reason: "unexpectedInitialActivation"); return }
        let flags = fcntl(STDIN_FILENO, F_GETFL)
        guard flags != -1,
              fcntl(STDIN_FILENO, F_SETFL, flags | O_NONBLOCK) != -1 else {
            stop(reason: "stdinUnavailable")
            return
        }
        standardInputFlags = flags
        let timer = Timer(
            timeInterval: 0.01, target: self, selector: #selector(pollStandardInput(_:)),
            userInfo: nil, repeats: true
        )
        RunLoop.main.add(timer, forMode: .common)
        self.timer = timer
        application.recorder.emit("ready", fields: ["active": false])
    }

    func applicationDidBecomeActive(_ notification: Notification) {
        application.recorder.emit("becameActive", fields: focusFields())
        if !activationRequested { stop(reason: "unexpectedActivation") }
    }

    func applicationDidResignActive(_ notification: Notification) {
        application.recorder.emit("resignedActive")
    }

    @objc private func pollStandardInput(_ timer: Timer) {
        guard !stopping else { return }
        let now = FocusSinkRecorder.continuousNanoseconds()
        guard now - startNS < 30_000_000_000 else {
            stop(reason: "lifetimeExceeded")
            return
        }
        if activationRequested && now - lastFocusSampleNS >= 100_000_000 {
            lastFocusSampleNS = now
            application.recorder.emit("focusSample", fields: focusFields())
        }
        // Bound each polling turn so a malformed/flooding owner cannot starve the deadline.
        var buffer = [UInt8](repeating: 0, count: 256)
        let count = buffer.withUnsafeMutableBytes { bytes in
            Darwin.read(STDIN_FILENO, bytes.baseAddress, bytes.count)
        }
        if count == 0 { stop(reason: "stdinEOF"); return }
        if count < 0 {
            if errno != EAGAIN && errno != EWOULDBLOCK && errno != EINTR {
                stop(reason: "stdinReadFailed")
            }
            return
        }
        input.append(contentsOf: buffer.prefix(count))
        guard input.count <= 512 else { stop(reason: "commandTooLarge"); return }
        while let newline = input.firstIndex(of: 0x0A) {
            let line = Data(input[..<newline])
            input.removeSubrange(...newline)
            guard let object = try? JSONSerialization.jsonObject(with: line),
                  let command = object as? [String: String] else {
                stop(reason: "invalidOrRepeatedCommand")
                return
            }
            if command == ["op": "activate"] && !activationRequested {
                activationRequested = true
                application.recorder.emit("activationRequested")
                window?.makeKeyAndOrderFront(nil)
                application.activate(ignoringOtherApps: true)
            } else if command == ["op": "observeEnd"] && activationRequested && !observationComplete {
                observationComplete = true
                application.recorder.emit("observationComplete", fields: focusFields())
                // This is an evidence-stream fence, not shutdown: keep receiving until EOF.
            } else {
                stop(reason: "invalidOrRepeatedCommand")
                return
            }
        }
    }

    private func focusFields() -> [String: Any] {
        [
            "isActive": application.isActive,
            "frontmostPID": Int64(NSWorkspace.shared.frontmostApplication?.processIdentifier ?? 0),
        ]
    }

    private func stop(reason: String) {
        guard !stopping else { return }
        stopping = true
        application.recorder.emit("closed", fields: ["reason": reason])
        cleanUp()
        application.terminate(nil)
    }

    func applicationWillTerminate(_ notification: Notification) {
        if !stopping {
            stopping = true
            application.recorder.emit("closed", fields: ["reason": "applicationTermination"])
        }
        cleanUp()
    }

    private func cleanUp() {
        timer?.invalidate()
        timer = nil
        if let standardInputFlags {
            _ = fcntl(STDIN_FILENO, F_SETFL, standardInputFlags)
            self.standardInputFlags = nil
        }
        window?.orderOut(nil)
    }
}
