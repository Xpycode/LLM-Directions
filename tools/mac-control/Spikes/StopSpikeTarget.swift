import AppKit
import Darwin

/// A disposable, in-memory AppKit target for measuring bounded input delivery and stopping.
///
/// This file deliberately has no package manifest or production dependencies. The spike harness
/// compiles it as a standalone executable during an approved desktop-test window.
@MainActor
private final class TargetEventRecorder {
    private static let timebase: mach_timebase_info_data_t = {
        var info = mach_timebase_info_data_t()
        mach_timebase_info(&info)
        return info
    }()

    func emit(_ event: String, fields: [String: Any] = [:]) {
        var record: [String: Any] = [
            "source": "target",
            "event": event,
            "ns": Self.continuousNanoseconds(),
        ]

        for (key, value) in fields {
            record[key] = value
        }

        guard let data = try? JSONSerialization.data(withJSONObject: record, options: []) else {
            return
        }

        FileHandle.standardOutput.write(data)
        FileHandle.standardOutput.write(Data([0x0A]))
    }

    /// `mach_continuous_time` continues across sleep. Split before multiplying so the normal
    /// timebase conversion does not lose precision to floating-point arithmetic.
    private static func continuousNanoseconds() -> String {
        let ticks = mach_continuous_time()
        let numerator = UInt64(timebase.numer)
        let denominator = UInt64(timebase.denom)
        guard denominator != 0 else {
            return "0"
        }

        let wholeTicks = ticks / denominator
        let remainderTicks = ticks % denominator
        let (wholeNanoseconds, wholeOverflow) = wholeTicks.multipliedReportingOverflow(by: numerator)
        let remainderNanoseconds = (remainderTicks * numerator) / denominator
        guard !wholeOverflow else {
            // A machine cannot remain up long enough to reach this in the intended spike. Keep
            // the JSON schema valid if it somehow does, rather than wrapping a monotonic value.
            return String(UInt64.max)
        }
        return String(wholeNanoseconds + remainderNanoseconds)
    }
}

@MainActor
private final class RecordingTextView: NSTextView {
    private static let disposableSample = String(repeating: "STOP SPIKE 0123456789 ", count: 5)

    private let recorder: TargetEventRecorder
    private let storage: NSTextStorage

    init(recorder: TargetEventRecorder) {
        self.recorder = recorder
        let initialSize = NSSize(width: 528, height: 260)
        let storage = NSTextStorage()
        let layout = NSLayoutManager()
        let container = NSTextContainer(containerSize: initialSize)
        storage.addLayoutManager(layout)
        layout.addTextContainer(container)
        self.storage = storage
        // The designated initializer does not create a text system when passed nil.
        super.init(frame: NSRect(origin: .zero, size: initialSize), textContainer: container)

        identifier = NSUserInterfaceItemIdentifier("stop-spike-text")
        setAccessibilityIdentifier("stop-spike-text")
        isRichText = false
        isEditable = true
        isSelectable = true
        allowsUndo = false
        isAutomaticQuoteSubstitutionEnabled = false
        isAutomaticDashSubstitutionEnabled = false
        isAutomaticTextReplacementEnabled = false
        isAutomaticSpellingCorrectionEnabled = false
        isAutomaticDataDetectionEnabled = false
        isVerticallyResizable = true
        isHorizontallyResizable = false
        autoresizingMask = [.width]
        minSize = NSSize(width: 0, height: 0)
        maxSize = NSSize(width: CGFloat.greatestFiniteMagnitude, height: CGFloat.greatestFiniteMagnitude)
        textContainer?.containerSize = NSSize(
            width: initialSize.width,
            height: CGFloat.greatestFiniteMagnitude
        )
        textContainer?.widthTracksTextView = true
        textContainer?.heightTracksTextView = false
    }

    @available(*, unavailable)
    required init?(coder: NSCoder) {
        fatalError("StopSpikeTarget creates its text view programmatically")
    }

    override func keyDown(with event: NSEvent) {
        let tag = sourceTag(in: event)
        let sourcePID = sourcePID(in: event)
        super.keyDown(with: event)
        // This is intentionally after AppKit handles the event: it records delivery to this view.
        recorder.emit(
            "keyDown",
            fields: [
                "tag": tag,
                "sourcePID": sourcePID,
                "count": Int64(string.utf16.count),
                "matchesSamplePrefix": matchesDisposableSamplePrefix(),
            ]
        )
    }

    override func keyUp(with event: NSEvent) {
        let tag = sourceTag(in: event)
        let sourcePID = sourcePID(in: event)
        super.keyUp(with: event)
        recorder.emit("keyUp", fields: ["tag": tag, "sourcePID": sourcePID])
    }

    override func didChangeText() {
        super.didChangeText()
        recorder.emit("changed", fields: ["count": Int64(string.utf16.count)])
    }

    // The target never reads from or writes to the pasteboard. Typed text stays in this view's
    // in-memory text storage for the life of this process only.
    override func copy(_ sender: Any?) {}

    override func cut(_ sender: Any?) {}

    override func paste(_ sender: Any?) {}

    private func sourceTag(in event: NSEvent) -> Int64 {
        event.cgEvent?.getIntegerValueField(.eventSourceUserData) ?? 0
    }

    private func sourcePID(in event: NSEvent) -> Int64 {
        event.cgEvent?.getIntegerValueField(.eventSourceUnixProcessID) ?? 0
    }

    /// Compare UTF-16 code units without emitting the view's content. The supervisor sends this
    /// known disposable sample; physical input can make the match false and is not proof of an
    /// owned event.
    private func matchesDisposableSamplePrefix() -> Bool {
        let current = string.utf16
        guard current.count <= Self.disposableSample.utf16.count else {
            return false
        }
        return current.elementsEqual(Self.disposableSample.utf16.prefix(current.count))
    }
}

@main
@MainActor
final class StopSpikeTarget: NSObject, NSApplicationDelegate, NSWindowDelegate {
    private let recorder = TargetEventRecorder()
    private var window: NSWindow?
    private var stopButton: NSButton?
    private var standardInputTimer: Timer?
    private var standardInputFlags: Int32?
    private var standardInput = Data()
    private var observationComplete = false
    private var didEmitClosed = false

    static func main() {
        if Array(CommandLine.arguments.dropFirst()) == ["--self-check"] {
            let recorder = TargetEventRecorder()
            let view = RecordingTextView(recorder: recorder)
            guard view.textStorage != nil, view.layoutManager != nil, view.textContainer != nil else { exit(2) }
            // In-memory responder call only: no window, activation, CGEvent or pasteboard.
            view.insertText("STOP", replacementRange: NSRange(location: NSNotFound, length: 0))
            guard view.string == "STOP" else { exit(2) }
            recorder.emit("textSystemSelfCheckPassed")
            return
        }
        guard CommandLine.arguments.count == 1 else { exit(64) }
        let application = NSApplication.shared
        let delegate = StopSpikeTarget()
        application.delegate = delegate
        application.setActivationPolicy(.regular)
        withExtendedLifetime(delegate) {
            application.run()
        }
    }

    func applicationDidFinishLaunching(_ notification: Notification) {
        let textView = RecordingTextView(recorder: recorder)
        let scrollView = NSScrollView()
        scrollView.hasVerticalScroller = true
        scrollView.autohidesScrollers = true
        scrollView.borderType = .bezelBorder
        scrollView.documentView = textView

        let instruction = NSTextField(labelWithString: "Disposable text only — Stop or close to end")
        instruction.lineBreakMode = .byTruncatingTail

        let stopButton = NSButton(title: "Stop", target: self, action: #selector(stopClicked(_:)))
        stopButton.keyEquivalent = ""
        stopButton.setAccessibilityIdentifier("stop-spike-stop-button")

        let controls = NSStackView(views: [instruction, NSView(), stopButton])
        controls.orientation = .horizontal
        controls.alignment = .centerY
        controls.spacing = 12
        controls.setHuggingPriority(.defaultLow, for: .horizontal)

        let content = NSView()
        content.addSubview(scrollView)
        content.addSubview(controls)
        scrollView.translatesAutoresizingMaskIntoConstraints = false
        controls.translatesAutoresizingMaskIntoConstraints = false
        NSLayoutConstraint.activate([
            scrollView.leadingAnchor.constraint(equalTo: content.leadingAnchor, constant: 16),
            scrollView.trailingAnchor.constraint(equalTo: content.trailingAnchor, constant: -16),
            scrollView.topAnchor.constraint(equalTo: content.topAnchor, constant: 16),
            scrollView.bottomAnchor.constraint(equalTo: controls.topAnchor, constant: -12),
            controls.leadingAnchor.constraint(equalTo: content.leadingAnchor, constant: 16),
            controls.trailingAnchor.constraint(equalTo: content.trailingAnchor, constant: -16),
            controls.bottomAnchor.constraint(equalTo: content.bottomAnchor, constant: -16),
        ])

        let window = NSWindow(
            contentRect: NSRect(x: 0, y: 0, width: 560, height: 360),
            styleMask: [.titled, .closable, .miniaturizable],
            backing: .buffered,
            defer: false
        )
        window.identifier = NSUserInterfaceItemIdentifier("stop-spike-window")
        window.setAccessibilityIdentifier("stop-spike-window")
        window.title = "Directions Stop Spike"
        window.contentView = content
        window.delegate = self
        window.isReleasedWhenClosed = false
        window.minSize = NSSize(width: 400, height: 240)
        self.window = window
        self.stopButton = stopButton

        window.makeKeyAndOrderFront(nil)
        NSApplication.shared.activate(ignoringOtherApps: true)
        window.makeFirstResponder(textView)
        recorder.emit("ready", fields: ["pid": Int64(ProcessInfo.processInfo.processIdentifier)])
        beginStandardInputEOFObservation()
    }

    func applicationDidBecomeActive(_ notification: Notification) {
        recorder.emit("becameActive")
    }

    func applicationDidResignActive(_ notification: Notification) {
        recorder.emit("resignedActive")
    }

    @objc private func stopClicked(_ sender: Any?) {
        recorder.emit("stopClicked")
        stopButton?.isEnabled = false
        stopButton?.title = "Stop requested"
    }

    func windowWillClose(_ notification: Notification) {
        endStandardInputEOFObservation()
        emitClosedIfNeeded()
        NSApplication.shared.terminate(nil)
    }

    func applicationWillTerminate(_ notification: Notification) {
        endStandardInputEOFObservation()
        emitClosedIfNeeded()
    }

    private func emitClosedIfNeeded() {
        guard !didEmitClosed else {
            return
        }
        didEmitClosed = true
        recorder.emit("closed")
    }

    /// The harness owns this pipe. It can request one evidence-stream fence; EOF closes the app.
    private func beginStandardInputEOFObservation() {
        let flags = fcntl(STDIN_FILENO, F_GETFL)
        guard flags != -1, fcntl(STDIN_FILENO, F_SETFL, flags | O_NONBLOCK) != -1 else {
            failStandardInput("stdinUnavailable")
            return
        }
        standardInputFlags = flags

        let timer = Timer(
            timeInterval: 0.05,
            target: self,
            selector: #selector(pollStandardInput(_:)),
            userInfo: nil,
            repeats: true
        )
        RunLoop.main.add(timer, forMode: .common)
        standardInputTimer = timer
    }

    private func endStandardInputEOFObservation() {
        standardInputTimer?.invalidate()
        standardInputTimer = nil
        if let standardInputFlags {
            _ = fcntl(STDIN_FILENO, F_SETFL, standardInputFlags)
            self.standardInputFlags = nil
        }
    }

    @objc private func pollStandardInput(_ timer: Timer) {
        var buffer = [UInt8](repeating: 0, count: 256)
        let count = buffer.withUnsafeMutableBytes { bytes in
            Darwin.read(STDIN_FILENO, bytes.baseAddress, bytes.count)
        }
        if count == 0 {
            window?.close()
            return
        }
        if count < 0 {
            if errno != EAGAIN && errno != EWOULDBLOCK && errno != EINTR {
                failStandardInput("stdinReadFailed")
            }
            return
        }
        standardInput.append(contentsOf: buffer.prefix(count))
        guard standardInput.count <= 512 else {
            failStandardInput("commandTooLarge")
            return
        }
        while let newline = standardInput.firstIndex(of: 0x0A) {
            let line = Data(standardInput[..<newline])
            standardInput.removeSubrange(...newline)
            guard !observationComplete,
                  let object = try? JSONSerialization.jsonObject(with: line),
                  let command = object as? [String: String],
                  command == ["op": "observeEnd"] else {
                failStandardInput("invalidOrRepeatedCommand")
                return
            }
            observationComplete = true
            recorder.emit("observationComplete", fields: [
                "pid": Int64(ProcessInfo.processInfo.processIdentifier),
                "isActive": NSApplication.shared.isActive,
                "frontmostPID": Int64(NSWorkspace.shared.frontmostApplication?.processIdentifier ?? 0),
            ])
            // Keep recording after the fence; only the owner's later EOF ends this app.
        }
    }

    private func failStandardInput(_ reason: String) {
        recorder.emit("error", fields: ["reason": reason])
        window?.close()
    }
}
