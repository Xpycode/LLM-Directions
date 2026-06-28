# Probe-and-classify, not catch-all — TCC / FDA pre-flight without false positives

**Source:** `1-macOS/_Published/syncthingStatus/` — `Client.swift::StuckDeletesController.probeFolderAccess` (2026-04-29, v1.6.0 hotfix).

A pre-flight access check that uses a catch-all `catch { return false }` is a **false-positive generator** for the destructive UI it gates. The user grants Full Disk Access (FDA) in System Settings, comes back, hits the same gate, granted again, gives up — *because the actual error wasn't a permission error in the first place.*

```swift
private func canReadFolder() -> Bool {
    let fm = FileManager()
    do {
        _ = try fm.contentsOfDirectory(atPath: folder.path)
        return true
    } catch {           // ⚠️ swallows everything
        return false    // ⚠️ caller flips fdaBlocked = true
    }
}
```

Symptom we hit: the cleanup window's pre-flight failed because the *path* didn't exist on the receiving Mac (Syncthing's folder root differed between peers), not because of TCC. UI showed "Full Disk Access required". User added the daemon to FDA (the wrong app, alphabetically adjacent), still blocked, no diagnostic.

Fix: classify the error type, log the actual `NSError` domain+code+desc, and reserve the destructive UI for the case it's actually meant for.

```swift
enum AccessProbeResult: Equatable {
    case granted
    case notFound(path: String)
    case notADirectory(path: String)
    case permissionDenied                // ← only this triggers FDA gate
    case other(message: String)
}

private func probeFolderAccess() -> AccessProbeResult {
    let fm = FileManager()
    let path = folder.path

    var isDir: ObjCBool = false
    let exists = fm.fileExists(atPath: path, isDirectory: &isDir)

    if !exists {
        log.error("Probe: folder root not found at \(path, privacy: .public)")
        return .notFound(path: path)
    }
    if !isDir.boolValue {
        log.error("Probe: path exists but is not a directory: \(path, privacy: .public)")
        return .notADirectory(path: path)
    }

    do {
        _ = try fm.contentsOfDirectory(atPath: path)
        return .granted
    } catch let e as CocoaError where e.code == .fileReadNoPermission {
        log.error("Probe: permission denied (FDA needed) for \(path, privacy: .public)")
        return .permissionDenied
    } catch {
        let nsError = error as NSError
        log.error("Probe: unexpected — domain=\(nsError.domain, privacy: .public) code=\(nsError.code, privacy: .public) desc=\(nsError.localizedDescription, privacy: .public)")
        return .other(message: nsError.localizedDescription)
    }
}
```

Then translate to UI state:

```swift
switch probeFolderAccess() {
case .granted:
    fdaBlocked = false
case .permissionDenied:
    fdaBlocked = true                       // FDA gate is correct here
case .notFound(let path):
    fdaBlocked = false
    lastError = "Folder root not found on this Mac: \(path). Check Syncthing's folder configuration — the path may differ between peers."
case .notADirectory(let path):
    fdaBlocked = false
    lastError = "Path exists but isn't a directory: \(path)."
case .other(let msg):
    fdaBlocked = false
    lastError = "Couldn't access folder root: \(msg)"
}
```

---

## Why FDA is so often the wrong gate

- TCC protections only fire on a known set of paths: `~/Documents`, `~/Desktop`, `~/Downloads`, iCloud Drive, removable volumes, Time Machine backups, Network volumes. Arbitrary directories under `~/` (e.g. `~/ProgrammingProjects`, `~/Code`, `~/Sync`) are **not** TCC-protected by default.
- An app that doesn't access TCC-protected paths **never appears in the FDA list automatically** — macOS only auto-adds when the app actually triggers a TCC check. So clicking "Open System Settings" on the gate lands the user on a list where their app isn't there at all.
- Users who don't know about the "+" button in the FDA list will toggle a name-adjacent app (`syncthing` daemon vs `syncthingStatus` menu-bar app) and assume they granted access.

For non-TCC-protected paths, a permission-denied error is genuinely rare (typically: ACLs, immutable flags, or a parent directory the user can't traverse). For TCC-protected paths, your app can/should pre-add itself via a TCC reset prompt by *requesting* access (e.g. read a file in `~/Documents`) — but that's a different pattern.

---

## What the diagnostic logging buys you

The `log.error("Probe: …")` line ends up in `OSLog`, retrievable via:

```bash
log show --predicate 'subsystem == "com.example.app" AND category == "Permissions"' \
  --last 5m --style compact
```

When a remote tester reports "FDA gate keeps showing", you ask them to paste this. Three possible outputs, three different fixes:

| Log line | Real problem | Fix |
|---|---|---|
| `Probe: folder root not found at …` | Path mismatch / not synced yet | Check `~` expansion, case sensitivity, mount point |
| `Probe: permission denied (FDA needed) for …` | Real FDA case | Walk through "+ button" workflow |
| `Probe: unexpected — domain=NSPOSIXErrorDomain code=20 …` | ENOTDIR / EBUSY / etc. | Whatever the code says |

Without the classification, all three look like FDA failures.

---

## Prime the FDA list entry before opening System Settings

A second, independent UX failure (same incident): the user clicks "Open System Settings", lands on the Full Disk Access list, and **the app isn't in it** — because macOS only auto-adds an app once it has actually *attempted* a TCC-protected read. So they toggle a name-adjacent app and assume they granted access.

Radix ([github.com/colinvkim/Radix](https://github.com/colinvkim/Radix), `SystemIntegration.swift`) has the clean fix: **probe a protected path first, then open Settings.** The failed probe is what registers the app in the list, so the user arrives to find it already there, just needing the toggle.

```swift
static func prepareAndOpenFullDiskAccessSettings() -> Bool {
    primeFullDiskAccessListEntry()          // attempt a protected read → macOS adds us to the FDA list
    return openFullDiskAccessSettings()     // x-apple.systempreferences:com.apple.preference.security?Privacy_AllFiles
}

static func primeFullDiskAccessListEntry() {
    _ = probeFullDiskAccess()               // the read attempt itself is the registration side-effect
}
```

Always pair the deep-link with the prime — the deep-link alone drops the user on a list that may not contain their app.

---

## Don't let the FDA *detection* heuristic rot across OS versions

There is **no public API to ask "do I have Full Disk Access."** Every app *infers* it by reading sentinel paths that FDA unlocks (`~/Library/Mail`, `~/Library/Safari`, `/Library/Preferences/com.apple.TimeMachine.plist`, the per-app `Containers` …). Two ways this inference silently breaks:

1. **Sentinel absent → false negative.** If the chosen sentinel doesn't exist on that Mac (no Mail account, Time Machine never configured, Stocks never launched), the read fails for a reason unrelated to permission, and a catch-all reports `notGranted` *even though FDA is granted*. Require **≥2 sentinels readable** out of several candidates, and only count sentinels that actually exist (`fileExists` before adding the probe).
2. **OS-version-gated probe path that's tuned for an unreleased OS.** Radix branches on `operatingSystemVersion.majorVersion >= 27` into a *separate, unverified* probe set (TimeMachine.plist + Stocks container). On a macOS 27 **beta**, those sentinels behave differently than the code assumes, so the app can *never* report `granted` no matter how many times the user toggles the switch — the exact "I granted it but it won't recognise it" report. **Lesson:** a version-gated detection branch for an OS still in beta is a liability; prefer one stable sentinel set with a quorum, log the per-sentinel outcome (this entry's whole point), and fall back to the proven path rather than guessing the new OS's TCC layout.

Never pick a path that stays unreadable *even with FDA* (e.g. `/Library/Application Support/com.apple.TCC` itself is root-owned/SIP-protected) — matching it would suggest a grant that can never resolve the warning.

---

## When to apply this

- Any pre-flight that gates a **destructive UI** (delete, overwrite, rename) on a permission probe.
- Any error path where the user's natural recovery action depends on knowing *which* error happened (network vs permission vs missing file).
- Anywhere a `catch { return false }` is acting as a UI driver — that's almost always too lossy.

---

## Companion patterns

- **#29 disk-space-preflight** — same probe-then-classify shape for `URLResourceKey` volume APIs, but for free space rather than permissions.
- **#52 appendingpathcomponent-fs-probe** — illustrates that "fileExists" itself can have semantic surprises; pair the existence check with `isDirectory` to avoid the symlink-to-file-pretending-to-be-dir trap.

---

*Drafted 2026-04-29 from a live remote-testing incident: user granted FDA, FDA gate persisted, screenshots showed `syncthing` (the daemon) in the FDA list but not `syncthingStatus`. The fix is on the app side — never the user's responsibility to debug a misclassified error.*
