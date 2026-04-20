# NSWorkspace Notifications → AsyncStream Bridge

**Source project:** `1-macOS/Sigil/`

> **Trigger:** you want to `for await` on mount/unmount/space-change/app-launch notifications from `NSWorkspace.shared.notificationCenter` inside modern structured-concurrency code

`NSWorkspace` ships notifications via the classic `NotificationCenter.addObserver(forName:object:queue:using:)` callback API. That doesn't compose with `async/await` / actors / AsyncStream. Bridging it correctly requires getting four small things right: actor isolation, observer ownership, stream termination, and Sendable crossing.

---

## The pattern

```swift
import Foundation
import AppKit

enum MountEvent: Sendable {
    case mounted(URL)
    case unmounted(URL)
}

actor MountWatcher {
    private var observers: [NSObjectProtocol] = []

    /// Returns an AsyncStream of mount/unmount events. Observers are installed
    /// on first call and torn down automatically when the stream is cancelled
    /// OR via explicit `stop()`.
    func events() -> AsyncStream<MountEvent> {
        let (stream, continuation) = AsyncStream<MountEvent>.makeStream()
        let nc = NSWorkspace.shared.notificationCenter

        let mountObs = nc.addObserver(
            forName: NSWorkspace.didMountNotification,
            object: nil,
            queue: .main
        ) { note in
            if let url = Self.volumeURL(from: note) {
                continuation.yield(.mounted(url))
            }
        }

        let unmountObs = nc.addObserver(
            forName: NSWorkspace.didUnmountNotification,
            object: nil,
            queue: .main
        ) { note in
            if let url = Self.volumeURL(from: note) {
                continuation.yield(.unmounted(url))
            }
        }

        observers.append(contentsOf: [mountObs, unmountObs])

        // Clean up observers when the consumer stops iterating.
        let observersToCleanup = observers
        continuation.onTermination = { _ in
            for obs in observersToCleanup {
                nc.removeObserver(obs)
            }
        }

        return stream
    }

    /// Manual teardown if the watcher is being released without the stream
    /// being consumed to completion.
    func stop() {
        let nc = NSWorkspace.shared.notificationCenter
        for obs in observers { nc.removeObserver(obs) }
        observers.removeAll()
    }

    private static func volumeURL(from note: Notification) -> URL? {
        if let url = note.userInfo?[NSWorkspace.volumeURLUserInfoKey] as? URL {
            return url
        }
        // Older SDK key fallback
        if let url = note.userInfo?["NSWorkspaceVolumeURLKey"] as? URL {
            return url
        }
        return nil
    }
}
```

Consumer side:

```swift
@MainActor
@Observable
final class AppState {
    private let watcher = MountWatcher()
    private var streamTask: Task<Void, Never>?

    func startWatching() {
        streamTask?.cancel()
        streamTask = Task { [weak self] in
            guard let self else { return }
            let stream = await self.watcher.events()
            for await event in stream {
                await self.handle(event)
            }
        }
    }

    private func handle(_ event: MountEvent) async {
        // react to mount/unmount
    }
}
```

---

## What the four gotchas are

### 1. Actor isolation vs. `NotificationCenter` closure capture

The `addObserver(forName:...:using:)` closure runs on whatever queue you pass. If you pass `.main` it runs on the main thread — safe to capture main-actor-isolated state. But inside an `actor MountWatcher`, the closure is NOT implicitly isolated to the actor. Just `continuation.yield(...)` inside — that's `Sendable` and always safe.

### 2. Observer ownership

`NotificationCenter.removeObserver` requires the exact token returned by `addObserver`. Store the tokens in an array owned by the watcher. On `stop()`, iterate and remove. On `stream.onTermination`, pass the tokens through to the cleanup closure (captured by value at registration time).

### 3. Stream termination → observer cleanup

If the consumer cancels their iterating `Task`, the stream terminates, and `continuation.onTermination` fires. The watcher MUST remove its observers there — otherwise they keep firing into a dead continuation forever (silent memory leak, no user-visible bug, just slow drift).

### 4. `NSObjectProtocol` is not `Sendable`

Under Swift 6 strict concurrency, capturing `[NSObjectProtocol]` in a `@Sendable` closure emits a warning. Under `targeted` strict concurrency (recommended for Swift 5.9 projects), it's a warning-you-can-live-with. Future fix: wrap in a `@unchecked Sendable` struct if Swift 6 compliance is required. Apple is expected to mark `NSObjectProtocol` `Sendable` in a future SDK.

---

## Why not `NotificationCenter.default.notifications(named:)`?

`NotificationCenter.notifications(named:)` already returns an `AsyncSequence`. So why wrap?

- **You can only observe ONE notification name per call** with the built-in method. We need mount AND unmount — so two separate sequences, two separate for-loops. Noisy.
- **`NSWorkspace.shared.notificationCenter` is a distinct instance** from the default `NotificationCenter`. Apple's built-in async API only works on `NotificationCenter.default`. Workspace notifications DON'T fire on `.default`.

For workspace, this bridge is the clean way.

---

## Other notifications that benefit from this pattern

Same wrapper works for:

- `NSWorkspace.didLaunchApplicationNotification` / `didTerminateApplicationNotification`
- `NSWorkspace.didWakeNotification` / `willSleepNotification`
- `NSWorkspace.screensDidSleepNotification` / `screensDidWakeNotification`
- `NSWorkspace.didChangeFileLabelsNotification`

Just change the notification names and event cases.

---

*Extracted from `Sigil/Services/MountWatcher.swift`. Tested with `Task` cancellation (start task, cancel task, plug in drive → observers correctly torn down, no zombie notifications).*
