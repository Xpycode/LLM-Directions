# #48 — SwiftTerm Output Monitoring + PTY Input Bridge

**Extracted from:** MyOwnTerminal (2026-04-21)  
**Use case:** Intercept terminal output for pattern matching (prompt detection, attention badges, logging) without breaking SwiftTerm's internal delegate chain.

---

## The problem

`LocalProcessTerminalView` owns its own internal delegate chain. If you intercept `processDelegate` directly and don't perfectly proxy every method, you silently break the view's internal plumbing (title updates, cwd, process termination). There's no safe way to wrap it from the outside.

You also need a bridge to *write* to the PTY from model-layer code (no AppKit imports allowed there).

---

## Solution 1 — Output monitoring via `dataReceived` subclass

Override `dataReceived(slice:)` in a `LocalProcessTerminalView` subclass. This is the correct intercept point: it fires for every PTY byte chunk, before and independently of the delegate chain.

```swift
// Views/Terminal/MonitoredTerminalView.swift

import AppKit
import SwiftTerm

final class MonitoredTerminalView: LocalProcessTerminalView {
    var onDataReceived: ((String) -> Void)?

    // Call super first — terminal renders the chunk, then we observe the string.
    override func dataReceived(slice: ArraySlice<UInt8>) {
        super.dataReceived(slice: slice)
        if let str = String(bytes: slice, encoding: .utf8) {
            onDataReceived?(str)
        }
    }
}
```

Wire it in your `NSViewRepresentable.makeNSView`:

```swift
func makeNSView(context: Context) -> MonitoredTerminalView {
    let tv = MonitoredTerminalView(frame: .zero)
    // ... font, colors, etc. ...
    tv.processDelegate = context.coordinator

    tv.onDataReceived = { [weak session] chunk in
        guard let session else { return }
        // @Observable mutations must happen on main actor
        DispatchQueue.main.async {
            sessionManager.rulesEngine.process(chunk: chunk, session: session)
        }
    }

    tv.startProcess(executable: "/bin/zsh", args: ["-l"], ...)
    return tv
}
```

**Why `super` first:** The terminal processes VT/ANSI sequences and updates its internal buffer before your code runs. You observe the rendered text, not raw escape bytes. This also means your callback fires after the screen is updated — correct for "what did the user just see?" matching.

---

## Solution 2 — PTY input bridge (write to process from model layer)

Model-layer code (e.g., a rules engine responding to a matched prompt) needs to send keystrokes to the PTY, but models must not import AppKit or reference the view directly.

**Pattern:** store a write closure on the model; the `NSViewRepresentable` Coordinator sets it.

```swift
// Models/TerminalSession.swift

@Observable
final class TerminalSession: Identifiable {
    // ...existing properties...

    // Set by Coordinator in makeNSView; cleared on processTerminated.
    // Call site: session.sendInput?("y\n")
    var sendInput: ((String) -> Void)? = nil
}
```

```swift
// In NSViewRepresentable Coordinator:

func makeNSView(context: Context) -> MonitoredTerminalView {
    let tv = MonitoredTerminalView(frame: .zero)
    // ...
    // Wire the write bridge
    session.sendInput = { [weak tv] text in
        tv?.send(txt: text)
    }
    return tv
}

// Clear when the process exits so callers get a silent no-op, not a crash
func processTerminated(source: TerminalView, exitCode: Int32?) {
    DispatchQueue.main.async {
        self.session.state = .idle
        self.session.sendInput = nil   // ← clear the bridge
    }
}
```

**Why a closure, not a direct reference:** The closure captures `[weak tv]` so it's always safe to call even after the view is gone. The model stays AppKit-free. Any consumer — HUD button, keyboard shortcut, notification action — calls `session.sendInput?("text")` identically.

---

## Rolling buffer for split-pattern matching

`dataReceived` fires for arbitrary byte chunks. A pattern like `[Y/n]` can arrive split across two calls: `[Y/` then `n]`. Match against a rolling buffer, not the individual chunk.

Keep the buffer on your engine (not the session model) — buffer churn shouldn't trigger `@Observable` UI re-renders:

```swift
// In PromptRulesEngine (or wherever you match patterns):

private var matchBuffers: [UUID: String] = [:]   // not @Observable-tracked
private static let bufferMax = 512

func process(chunk: String, session: TerminalSession) {
    guard session.activePromptMatch == nil else { return }

    var buf = matchBuffers[session.id, default: ""]
    buf += chunk
    if buf.count > Self.bufferMax {
        buf = String(buf.suffix(Self.bufferMax))
    }
    matchBuffers[session.id] = buf

    // Now match against `buf`, not `chunk`
    for rule in rules where rule.isEnabled {
        if matchFound(in: buf, rule: rule) {
            session.activePromptMatch = PromptMatch(/* ... */)
            return
        }
    }
}

// Call this when a reply is sent, or when a new command starts (OSC 133;C)
func clearBuffer(for session: TerminalSession) {
    matchBuffers[session.id] = nil
    session.activePromptMatch = nil
}
```

**Buffer is on the engine, not `TerminalSession`:** `@Observable` tracks every property access in SwiftUI view bodies. If the buffer lived on the session, every PTY byte chunk would mark the session "changed" and re-render all tabs. The engine's private dictionary is invisible to SwiftUI.

---

## Gotchas

| Gotcha | Detail |
|--------|--------|
| `dataReceived` chunk encoding | UTF-8 conversion can fail mid-multibyte character (chunk split at byte boundary). `String(bytes:encoding:)` returns nil — just skip the chunk; the next one will include the remainder. |
| `onDataReceived` thread | Fires on whichever thread SwiftTerm uses internally. Always dispatch to main before touching `@Observable` properties. |
| `sendInput` after process exit | `processTerminated` fires before `session.state` is set. Clear `sendInput` there; call sites use optional chaining `session.sendInput?("y\n")` for silent no-op. |
| Re-running `makeNSView` | SwiftUI can recreate the NSViewRepresentable under certain conditions. Re-wire `sendInput` and `onDataReceived` in `updateNSView` if the coordinator's session reference changes. |
| Buffer and session close | Call `clearBuffer(for: session)` in `SessionManager.closeSession` — otherwise stale buffer entries accumulate for closed session IDs. |

---

## Best for

- Prompt detection / interactive quick-reply (pattern → action buttons)
- Attention badge triggers (background output → `.hasOutput` state)
- Session logging / transcript capture
- Any feature that needs to read from or write to a SwiftTerm PTY without coupling model to AppKit
