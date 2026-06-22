# Closure-struct dependency injection — `.live` / `.inert` for system side-effects

**Source:** external study — [github.com/colinvkim/Radix](https://github.com/colinvkim/Radix) (`Radix/Services/AppSystemActions.swift`, `AppQuickLookActions`). An LLM-built disk analyzer; this is the one pattern worth lifting wholesale.

Every side-effecting system call an app makes — `open`, `reveal`, `moveToTrash`, `fullDiskAccessStatus`, `presentOpenPanel`, volume capacity — is a **closure field on a plain struct**, not a method on a singleton and not behind a protocol. The struct ships with two prebuilt instances: `.live` (wires each closure to the real `SystemIntegration` call) and `.inert` (every closure is a safe no-op / fixed return).

```swift
@MainActor
struct AppSystemActions {
    var open: (URL) throws -> Void
    var reveal: (URL) -> Void
    var moveToTrash: (URL) throws -> Void
    var fullDiskAccessStatus: () -> FullDiskAccessStatus
    var presentOpenPanel: () -> ScanTarget?
    // …one field per side-effect the app performs

    static let live = AppSystemActions(
        open:                 { try SystemIntegration.open($0) },
        reveal:               { SystemIntegration.reveal($0) },
        moveToTrash:          { try SystemIntegration.moveToTrash($0) },
        fullDiskAccessStatus: { SystemIntegration.fullDiskAccessStatus() },
        presentOpenPanel:     { SystemIntegration.presentScanPanel() }
    )

    static let inert = AppSystemActions(
        open:                 { _ in },
        reveal:               { _ in },
        moveToTrash:          { _ in },
        fullDiskAccessStatus: { .unknown },
        presentOpenPanel:     { nil }
    )
}
```

The ViewModel takes one in its initializer and never touches `SystemIntegration`, `NSWorkspace`, `NSOpenPanel`, or `FileManager` directly:

```swift
@MainActor @Observable
final class WorkspaceModel {
    private let system: AppSystemActions
    init(system: AppSystemActions = .live) { self.system = system }

    func trash(_ url: URL) throws { try system.moveToTrash(url) }
}
```

---

## Why a struct of closures, not a protocol

This is the **protocol-witness** pattern without the protocol boilerplate. A protocol approach needs the protocol + a live conforming class + a mock conforming class per test; here `.live` and `.inert` are the only two declarations, and a test overrides exactly the one behavior it cares about by mutating a single field:

```swift
func testTrashFailureSurfacesError() {
    var sys = AppSystemActions.inert
    sys.moveToTrash = { _ in throw SystemIntegrationError.protectedTrashLocation(path: "/") }
    let model = WorkspaceModel(system: sys)
    // assert the model presents the error — no mocking framework, no subclass
}
```

You cannot do that surgical single-method swap with a class mock without writing a whole new conformance.

---

## `.inert` does double duty as the SwiftUI preview environment

The reason Radix's `#Preview`s don't accidentally fire `NSOpenPanel`, open System Settings, or trash files is that previews construct the model with `.inert`. A preview is just another non-production caller:

```swift
#Preview { WorkspaceView(model: WorkspaceModel(system: .inert)) }
```

Name it `.inert` (or `.disabled`), not `.mock` — it signals "does nothing", which is exactly what both tests *and* previews want as a baseline before overriding specific fields.

---

## Pair it with a sync + async seam for blocking work

Where a closure does blocking disk I/O (an FDA probe, a capacity stat walk), add an **optional** async sibling and a capability flag, so callers on the main actor can hop off without forcing every caller async:

```swift
var fullDiskAccessStatus: () -> FullDiskAccessStatus
var asyncFullDiskAccessStatus: (@Sendable () async -> FullDiskAccessStatus)?  // .live wraps Task.detached(priority: .utility)

func loadCurrentFullDiskAccessStatus() async -> FullDiskAccessStatus {
    if let asyncFullDiskAccessStatus { return await asyncFullDiskAccessStatus() }
    return fullDiskAccessStatus()
}
```

`.inert` leaves the async field `nil`, so previews/tests stay fully synchronous and deterministic.

---

## When to apply this

- Any app with a **ViewModel layer** that calls into `NSWorkspace` / `FileManager` / `NSOpenPanel` / TCC — i.e. anything you'd want to unit-test without touching the real disk or popping real panels.
- Apps with **destructive actions** (trash, overwrite, rename): the seam lets you test the error-handling branches deterministically (see [[127-toctou-identity-verify-before-destructive-op]]).

**Altitude check — skip it when:** a single-window, ~200-line menu-bar utility with no ViewModel layer. A struct-of-closures over three system calls is ceremony there; call `SystemIntegration` directly. The pattern earns its keep once you have logic worth testing *between* the UI and the syscall.

---

## Companion patterns

- **[[00-app-shell]]** — the standard app skeleton this DI seam slots into; satisfies the "test the real user flow" rule by making the flow drivable with fakes.
- **[[06-app-lifecycle]]** — where `.live` gets constructed and injected at `@main` / scene setup.
- **[[19-swift6-concurrency]]** — `@MainActor` on the struct keeps the closures main-isolated; the optional async field is the documented escape hatch.

---

*Drafted 2026-06-22 after diagnosing an FDA bug in Radix (external app) and finding its DI architecture cleaner than typical hand-rolled code. Adopt the seam; do not adopt its macOS-27 FDA probe — that's the bug, see [[61-probe-classify-not-catch-all]].*
