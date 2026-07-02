## Live volume mount/unmount monitoring inside an `@Observable @MainActor` model

**Tags:** NSWorkspace, didMountNotification, @Observable, @MainActor, nonisolated(unsafe), deinit, MainActor.assumeIsolated, removeObserver

**Source:** PhotoIngest — `01_Project/PhotoIngest/PhotoIngest/IngestModel.swift` (the card-list state spine the whole ingest UI hangs off). Added 2026-06-29.

**Use case:** A SwiftUI macOS app whose UI state is an `@Observable @MainActor` model (the modern Observation shape, same as a `ThemeManager`) needs a list that **stays live** as the user inserts/ejects SD cards — or any volume — without a refresh button. The model itself owns the `NSWorkspace.didMountNotification` / `didUnmountNotification` observers (this is the "CardMonitor" layer an offline `mountedCards()`/`isCardLike` scanner can't provide), refreshes the list on every event, and removes its observers in `deinit`. Two Swift-concurrency traps make the obvious code fail — one at compile time, one only under strict concurrency.

### Trap 1 (compile error): `deinit` can't read a main-actor-isolated stored property

The observer **tokens** returned by `addObserver(forName:…)` must be removed, so you store them — but a `@MainActor` class's `deinit` is **nonisolated**, and reading an isolated `var` from it is an error:

```
error: main actor-isolated property 'mountObservers' can not be referenced from a nonisolated context
```

Fix = mark **only that storage** `nonisolated(unsafe)`. It's mutated solely on the main actor (in `beginMonitoring`) and read exactly once from `deinit` for cleanup — the precise, bounded case the annotation exists for. Don't reach for an actor, a `Task` in deinit (illegal), or `@unchecked Sendable` on the whole class.

```swift
@Observable
@MainActor
final class IngestModel {
    var mountedCards: [URL] = []
    var selectedCard: URL?

    // Mutated only on the main actor; read once from the nonisolated deinit.
    nonisolated(unsafe) private var mountObservers: [NSObjectProtocol] = []

    private func beginMonitoringMounts() {
        guard mountObservers.isEmpty else { return }          // idempotent
        let center = NSWorkspace.shared.notificationCenter
        for name in [NSWorkspace.didMountNotification, NSWorkspace.didUnmountNotification] {
            let token = center.addObserver(forName: name, object: nil, queue: .main) { [weak self] _ in
                self?.refreshCards()
            }
            mountObservers.append(token)
        }
    }

    deinit {
        let center = NSWorkspace.shared.notificationCenter
        for token in mountObservers { center.removeObserver(token) }
    }
}
```

### Trap 2 (strict concurrency): the notification closure calling a main-actor method

Above compiles as-is in **Swift 5 language mode** (`SWIFT_VERSION = 5.0`) — the common case for an xcodegen app whose services were merely *written* Sendable-clean. Under **Swift 6 strict concurrency** the `addObserver` block is `@Sendable`, so calling `self?.refreshCards()` (main-actor) directly is rejected. Because you passed `queue: .main` the block already runs on the main thread, so assert it rather than paying an async hop:

```swift
let token = center.addObserver(forName: name, object: nil, queue: .main) { [weak self] _ in
    MainActor.assumeIsolated { self?.refreshCards() }   // valid: queue == .main
}
```

(If you can't guarantee the queue, hop instead: `Task { @MainActor in self?.refreshCards() }`.)

### Keep the list coherent on every event — one `refreshCards()` does it all

The same handler fires for mount **and** unmount, plus a manual rescan button, so make it self-correcting rather than branching on the notification:

```swift
func refreshCards() {
    mountedCards = CardScanner.mountedCards()                       // re-scan from scratch

    // A selected *card* that has since unmounted vanishes from disk → drop it.
    // A manually-picked folder still exists on disk → it survives this check.
    if let sel = selectedCard, !FileManager.default.fileExists(atPath: sel.path) {
        selectedCard = nil
    }
    // Quality-of-life: auto-select the sole card when nothing is chosen yet.
    if selectedCard == nil, mountedCards.count == 1 {
        selectCard(mountedCards[0])
    }
}
```

The `fileExists` probe is what lets one code path serve both an auto-detected volume (disappears on eject) and a user-picked folder (persists) — no "is this manual?" flag to thread. Start monitoring from an **idempotent** `start()` the view calls in `.task { model.start() }`, guarded by a `hasStarted` flag so repeated view appearances don't double-register.

**Pairs with:** the **NSWorkspace → AsyncStream bridge** (Sigil) — the alternative shape when you want mount events as a structured-concurrency stream a consumer `for await`s, instead of a model mutating itself in-place; choose the stream when multiple consumers react, this in-model observer when one `@Observable` *is* the consumer. Also **#00** (App Shell Standard / `Theme` / the `ThemeManager` `@Observable` precedent), and a `mountedVolumeURLs(includingResourceValuesForKeys:options:.skipHiddenVolumes)` + removable/ejectable/`!isInternal` + `DCIM`-exists card heuristic on the scanner side.
