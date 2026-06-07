# Phone ↔ Watch full-state mirror over WatchConnectivity (App Groups don't cross devices)

**Source:** `2-iOS/Group Alarms/` — `PhoneConnectivityManager.swift`, `Group Alarms Watch Watch App/WatchConnectivityManager.swift`, `SharedDataManager.swift`, `Group_Alarms_WatchApp.swift` (2026-06-05).

A paired-device app keeps its data in an **App Group** (`UserDefaults(suiteName:)`) so the app, its widgets, and its watch app all read the same store. The trap: **App Group containers are per-device.** `group.X` on the iPhone and `group.X` on the Apple Watch are *separate sandboxes* — they do **not** sync. The only bridge is **WatchConnectivity**. If you never push the data across, the watch app (and any watch complication) reads a store that only its **own** local writes ever populated → empty on a fresh install, stale forever after.

This bites silently when the connectivity layer was built as a *control channel* (watch taps a button → pings the phone to "do the thing") and nobody ever sent the **data** back the other way. A complication makes it impossible to ignore, because a complication is a pure data *consumer* — it has no other way to learn state.

**The fix: mirror the full state phone → watch on every change.** Four pieces.

### 1. Hook the push at the persistence choke point — not the iCloud callback

Fire the watch push from the single function every save funnels through, so **local edits AND remotely-received (iCloud) changes** both propagate. Don't reuse an existing "on save" callback if something else already owns it (here `CloudSyncManager` claims `onGroupsSaved` — last assignment wins, so a second `=` would silently clobber iCloud upload). Add a *separate* hook.

```swift
// SharedDataManager.swift  (compiled into app + watch + widget targets)
static let watchGroupsPayloadKey = "alarmGroupsData"

/// Fires after groups persist to disk. Set by the phone only; nil (no-op) on watch/widget.
var onGroupsPersisted: (([AlarmGroup]) -> Void)?

func saveAlarmGroupsWithoutSync(_ groups: [AlarmGroup], skipNotification: Bool = false) {
    // …encode + write to shared UserDefaults…
    reloadWidgets()                 // WidgetCenter.shared.reloadAllTimelines()
    onGroupsPersisted?(groups)      // ← mirror to watch (phone only)
    if !skipNotification { NotificationCenter.default.post(name: .alarmGroupsDidChange, object: nil) }
}
```

### 2. Push with `updateApplicationContext` (latest-state-wins), seed on activation

`updateApplicationContext` holds the *most recent* payload and delivers it when the watch is reachable — even if it was asleep when the change happened. That's exactly right for full-state mirroring: the watch never needs the intermediate states, only the newest. (Use `transferUserInfo` only if you need a guaranteed-ordered *queue*; use `sendMessage` only for live foreground round-trips.) Also push once when the session **activates**, so a plain phone launch re-seeds the watch.

```swift
// PhoneConnectivityManager.swift
override init() {
    super.init()
    if WCSession.isSupported() { session = .default; session?.delegate = self; session?.activate() }
    SharedDataManager.shared.onGroupsPersisted = { [weak self] in self?.pushGroupsToWatch($0) }
}
func pushGroupsToWatch(_ groups: [AlarmGroup]) {
    guard let session, session.activationState == .activated else { return }
    do {
        let data = try JSONEncoder().encode(groups)
        try session.updateApplicationContext([SharedDataManager.watchGroupsPayloadKey: data])
    } catch { /* log */ }
}
func session(_ s: WCSession, activationDidCompleteWith state: WCSessionActivationState, error: Error?) {
    if state == .activated { pushGroupsToWatch(SharedDataManager.shared.loadAlarmGroups()) }  // seed
}
```

### 3. ⚠️ Eagerly activate the WCSession at `@main` — or you drop the first push

The bug that costs an afternoon: `didReceiveApplicationContext` only fires on a session whose **delegate was set before the context arrived.** If your `WatchConnectivityManager` is a lazy singleton touched only inside a toggle handler, its delegate isn't wired on cold launch → the phone's very first (seed) push is dropped, and the watch looks empty until the user happens to interact. **Hold the singleton in the watch App struct so it activates at launch.** Also drain `receivedApplicationContext` on activation (the phone may have pushed while the watch app was dead).

```swift
@main
struct Group_Alarms_Watch_Watch_AppApp: App {
    private let connectivityManager = WatchConnectivityManager.shared   // ← eager activation
    var body: some Scene { WindowGroup { ContentView() } }
}

// Watch side, WCSessionDelegate:
func session(_ s: WCSession, activationDidCompleteWith _: WCSessionActivationState, error: Error?) {
    if !s.receivedApplicationContext.isEmpty { handleReceivedGroups(from: s.receivedApplicationContext) }
}
func session(_ s: WCSession, didReceiveApplicationContext ctx: [String: Any]) { handleReceivedGroups(from: ctx) }
func session(_ s: WCSession, didReceiveMessage msg: [String: Any])           { handleReceivedGroups(from: msg) }

private func handleReceivedGroups(from payload: [String: Any]) {
    guard let data = payload[SharedDataManager.watchGroupsPayloadKey] as? Data,
          let incoming = try? JSONDecoder().decode([AlarmGroup].self, from: data) else { return }
    DispatchQueue.main.async {  // persist + notify on main; the notification drives SwiftUI
        let merged = Self.mergeReceivedGroups(incoming: incoming, local: SharedDataManager.shared.loadAlarmGroups())
        SharedDataManager.shared.saveAlarmGroupsWithoutSync(merged)  // → reloadWidgets() refreshes complications
        NotificationCenter.default.post(name: WatchConnectivityManager.didReceiveGroups, object: nil)
    }
}
```

### 4. Pick a merge rule — phone-authoritative vs `lastModified`-aware

`return incoming` (phone-authoritative) is simplest and always consistent — fine when the phone owns the source of truth and pushes are frequent. The risk: a value the user just changed *on the watch* can be reverted in the ~1s before it round-trips. If that matters (e.g. an alarm toggle → oversleep), merge per-item by the newer `lastModified` instead. Keep it one swappable function so the decision is isolated.

```swift
static func mergeReceivedGroups(incoming: [AlarmGroup], local: [AlarmGroup]) -> [AlarmGroup] {
    return incoming   // phone-authoritative. Upgrade: keep max(lastModified) per id.
}
```

## Gotchas / tells

- **Tell you have this bug:** the watch app / complication shows empty on a real device but works in isolation, *or* a class named `…ConnectivityManager` on one side has only send methods and no `didReceive*`. Grep both sides for `updateApplicationContext` / `didReceiveApplicationContext` — if the push direction is missing, the data never crosses.
- **No loop back:** the watch's receive→`saveAlarmGroupsWithoutSync` must NOT re-trigger a watch→phone sync ping, or you ping-pong. Keep the "request sync" call only on explicit user toggles, never inside the receive path.
- **Same App Group on every target.** The watch widget extension needs `group.X` in its entitlements too, or `getWidgetData()` reads an empty suite (falls back to `.standard`).
- **`updateApplicationContext` is plist-only.** `Data` is fine; encode your model to JSON `Data` rather than shoving structs in.
- **Complication freshness == last push.** A watch complication is only as current as the most recent phone push; `reloadAllTimelines()` in the receive path is what nudges it. Frequent pushes (every save + every launch) keep it honest.

Pairs with #06 (app lifecycle / activation order), #29 (App Group / shared storage mindset).
