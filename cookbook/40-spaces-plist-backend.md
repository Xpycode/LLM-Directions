## Public Spaces Backend via `com.apple.spaces`

**Source:** `1-macOS/Mural/01_Project/Mural/Services/SpacesPlistReader.swift`
**Use case:** Any macOS app that needs to enumerate Spaces (desktops), know
which Space is currently active on each display, or key data by Space
identity — without using private CGS SPI (which blocks notarization).

---

### The problem

- **`NSWorkspace.activeSpaceDidChangeNotification` only tells you SOMETHING
  changed.** It does not say which Space is now active, does not say which
  monitor fired the change, does not expose Space identity.
- **`CGSCopySpaces` / `CGSGetActiveSpace` are private.** They work, but an app
  linking against them is unlikely to pass Apple notarization and can break
  between macOS versions without warning.
- **`System Settings → Mission Control → "Displays have separate Spaces"`**
  has two modes:
  - **ON** (default on newer macOS): each display has its own independent
    Spaces list. Display A can be on Space 3 while Display B is on Space 1.
  - **OFF** (= `spans-displays` pref = `1`): Spaces span all displays. All
    monitors swap together. There's effectively one global Space list.
  A cursor-heuristic "advance per-display counter on each notification"
  approach is WRONG in OFF mode because only one display's counter
  advances when all of them should.

### The trick: parse `com.apple.spaces` UserDefaults

macOS writes the live Space topology into a documented-format-but-
undocumented-semantics plist whose defaults-domain name is `com.apple.spaces`.
The format has been stable across Big Sur → Sequoia → Tahoe. Reading it via
`UserDefaults(suiteName:)` is **not** a private-API call — you're just
parsing a plist. Apps that ship on the App Store and are actively notarized
use this approach.

```bash
# Exploration
defaults read com.apple.spaces
defaults read com.apple.spaces spans-displays   # Int: 0 or 1
```

### Shape of the data

```
SpacesDisplayConfiguration:
  Management Data:
    Monitors: [
      {
        Display Identifier: "Main" | "<display-UUID>"
        Current Space: { uuid: String, ManagedSpaceID: Int, type: Int }
        Spaces: [
          { uuid: String, ManagedSpaceID: Int, type: Int },
          ...
        ]
      },
      ...
    ]

Top-level:
  spans-displays: 0 | 1
```

- `type = 0` → user-visible desktop Space (what you want)
- `type = 4` → tiled-fullscreen group / Mission Control tile — SKIP
- `uuid` is sometimes `""` (older Spaces predate the UUID system).
  Fall back to `"msid:<ManagedSpaceID>"` as the stable identity.
- `Display Identifier = "Main"` is the primary display's entry. When
  `spans-displays = 1`, its `Spaces` list is the global shared list.
- Other entries key on `CFUUID` — match with
  `CGDisplayCreateUUIDFromDisplayID(cgDirectDisplayID)`.

### Swift 6 reader

```swift
import Foundation
import AppKit
import CoreGraphics

@MainActor
struct SpacesPlistReader {
    private static let suiteName = "com.apple.spaces"

    struct Snapshot {
        let spansDisplays: Bool
        let monitors: [MonitorEntry]
    }

    struct MonitorEntry {
        let identifier: String             // "Main" or display UUID
        let currentSpace: SpaceDescriptor?
        let spaces: [SpaceDescriptor]
    }

    struct SpaceDescriptor: Hashable, Sendable {
        let uuid: String?
        let managedSpaceID: Int
        let ordinal: Int

        var key: String {
            if let uuid, !uuid.isEmpty { return "uuid:\(uuid)" }
            return "msid:\(managedSpaceID)"
        }
    }

    static func read() -> Snapshot {
        let defaults = UserDefaults(suiteName: suiteName)
        let spans = defaults?.bool(forKey: "spans-displays") ?? false

        guard let config = defaults?.dictionary(forKey: "SpacesDisplayConfiguration"),
              let management = config["Management Data"] as? [String: Any],
              let raw = management["Monitors"] as? [[String: Any]] else {
            return Snapshot(spansDisplays: spans, monitors: [])
        }
        return Snapshot(spansDisplays: spans, monitors: raw.compactMap(parse))
    }

    static func monitorEntry(
        for displayID: CGDirectDisplayID,
        in snapshot: Snapshot,
        isMainDisplay: Bool
    ) -> MonitorEntry? {
        if snapshot.spansDisplays {
            // All displays share "Main"'s list.
            return snapshot.monitors.first { $0.identifier == "Main" }
                ?? snapshot.monitors.first
        }
        // Separate Spaces: match by display UUID.
        if let cfuuid = CGDisplayCreateUUIDFromDisplayID(displayID)?.takeRetainedValue() {
            let uuidString = CFUUIDCreateString(nil, cfuuid) as String
            if let hit = snapshot.monitors.first(where: { $0.identifier == uuidString }) {
                return hit
            }
        }
        if isMainDisplay {
            return snapshot.monitors.first { $0.identifier == "Main" }
        }
        return nil
    }

    private static func parse(_ raw: [String: Any]) -> MonitorEntry? {
        guard let identifier = raw["Display Identifier"] as? String else { return nil }

        let spaces = (raw["Spaces"] as? [[String: Any]] ?? [])
            .enumerated()
            .compactMap { offset, rawSpace -> SpaceDescriptor? in
                parseSpace(rawSpace, ordinal: offset)
            }

        let current: SpaceDescriptor? = {
            guard let rawCurrent = raw["Current Space"] as? [String: Any],
                  let msid = rawCurrent["ManagedSpaceID"] as? Int else { return nil }
            // Prefer the descriptor from the Spaces array (keeps ordinal).
            if let match = spaces.first(where: { $0.managedSpaceID == msid }) {
                return match
            }
            return parseSpace(rawCurrent, ordinal: 0)
        }()

        return MonitorEntry(identifier: identifier, currentSpace: current, spaces: spaces)
    }

    private static func parseSpace(_ raw: [String: Any], ordinal: Int) -> SpaceDescriptor? {
        guard let type = raw["type"] as? Int, type == 0,        // desktop only
              let msid = raw["ManagedSpaceID"] as? Int else { return nil }
        let uuid = raw["uuid"] as? String
        return SpaceDescriptor(
            uuid: (uuid?.isEmpty == true) ? nil : uuid,
            managedSpaceID: msid,
            ordinal: ordinal
        )
    }
}
```

### Wiring live updates

Trigger re-reads on `activeSpaceDidChangeNotification`. **Add a ~100–150 ms
settle delay** — macOS writes the plist *after* posting the notification,
so reading too fast returns stale state.

```swift
@MainActor
@Observable
final class PublicSpacesBackend {
    private(set) var snapshot: SpacesPlistReader.Snapshot
    private var continuations: [UUID: AsyncStream<ActiveSpaceChange>.Continuation] = [:]
    private var observationTask: Task<Void, Never>?

    init() {
        self.snapshot = SpacesPlistReader.read()
        observationTask = Task { [weak self] in
            let stream = NSWorkspace.shared.notificationCenter.notifications(
                named: NSWorkspace.activeSpaceDidChangeNotification
            )
            for await _ in stream {
                self?.handleSpaceChange()
            }
        }
    }

    private func handleSpaceChange() {
        Task { @MainActor [weak self] in
            try? await Task.sleep(for: .milliseconds(120))
            self?.snapshot = SpacesPlistReader.read()
            // fan out events to continuations...
        }
    }
}
```

### Persistence & migration

Key your slots/slots/data by `SpaceDescriptor.key` string:
- `"uuid:6E06931C-307B-4420-A7CA-6B83CB112269"` → stable forever (UUID)
- `"msid:7"` → stable for older Spaces where macOS hasn't assigned a UUID

If you previously keyed on `spaceIndex: Int` (an ordinal counter), migrate
by reading the plist at load time and mapping `oldIndex` → `spaces[oldIndex].key`.
Back up the old file first — migration failures shouldn't drop user data.

### Known limits

- **Mission Control Space add/remove while app is running.** The plist
  updates, but there's no notification. You only see the new topology on
  the next `activeSpaceDidChangeNotification`. For immediate detection,
  watch the plist file with kqueue / `DispatchSource.makeFileSystemObjectSource`.
- **Reorder via Mission Control drag.** UUIDs survive the reorder; the
  `ordinal` field does not. Always key by `uuid` / `msid`, never by
  `ordinal`.
- **Never synthesize a `uuid:` key yourself.** If `uuid` is missing from
  the plist, use `msid:<managedID>`. Inventing a UUID means no other
  process can recognize it as a macOS-assigned Space identity.
- **"type" values may grow.** Current known: `0` = desktop, `4` = tiled
  fullscreen group. Accept future unknown types by filtering strictly on
  `type == 0`.

### Alternatives considered

| Approach | Result |
|----------|--------|
| Cursor-location heuristic + per-display counter | Broken under `spans-displays=1` (all monitors swap together but only one counter advances) |
| User-settable "N spaces" via Stepper | Works but can't auto-detect Mission Control changes; bad UX |
| Private CGS (`CGSCopySpaces`, `CGSGetActiveSpace`) | Works but risks notarization rejection; undocumented behavior between macOS versions |
| **Plist parse + `activeSpaceDidChangeNotification`** | Correct for both `spans-displays` modes, no private SPI, stable across current macOS versions |

### Credits

First developed during Mural v1.5 (2026-04-20) after realizing the initial
Wave-3 cursor-heuristic model was wrong for `spans-displays=1` (discovered
during user testing with 6 Spaces on 2 displays).
