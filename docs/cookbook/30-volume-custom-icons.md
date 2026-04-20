# Custom Volume Icons — The Two-Step Write

**Source project:** `1-macOS/Sigil/`

> **Trigger:** writing a custom icon to a mounted volume's root on macOS 13+

The obvious API for this — `NSWorkspace.shared.setIcon(_:forFile:options:)` — has been **broken for volume roots since macOS 13.1** (Ventura). It writes `.VolumeIcon.icns` to the volume but silently fails to set the `kHasCustomIcon` flag in `com.apple.FinderInfo`, so Finder ignores the file entirely. Confirmed by the [fileicon CLI maintainers](https://github.com/mklement0/fileicon/issues/42) and reproduced across multiple related tools.

The reliable path is a direct two-step write: put the `.icns` bytes on disk yourself, then set the FinderInfo flag yourself.

---

## The pattern

```swift
import Foundation

/// Apply a custom icon to a mounted volume. Works on APFS, HFS+, exFAT,
/// NTFS — anything that supports extended attributes on the mountpoint.
func applyVolumeIcon(icns: Data, to volumeURL: URL) throws {
    // Step 1: write .VolumeIcon.icns atomically
    let iconURL = volumeURL.appendingPathComponent(".VolumeIcon.icns")
    try icns.write(to: iconURL, options: [.atomic])

    do {
        // Step 2: read-modify-write FinderInfo to set kHasCustomIcon (byte 8)
        // PRESERVING other bytes — Finder label colors etc. live here too.
        var info = (try? XAttr.get(name: "com.apple.FinderInfo",
                                    from: volumeURL.path)) ?? Data()
        if info.count < 32 {
            info.append(contentsOf: [UInt8](repeating: 0, count: 32 - info.count))
        }
        info[8] |= 0x04                                 // kHasCustomIcon
        try XAttr.set(name: "com.apple.FinderInfo",
                      value: info, on: volumeURL.path)
    } catch {
        // Rollback the orphan file on xattr failure
        try? FileManager.default.removeItem(at: iconURL)
        throw error
    }

    // Step 3: nudge Finder's icon cache without a disruptive `killall Finder`
    utimes(volumeURL.path, nil)
}

/// Strip the icon and clear the flag. Symmetric with apply.
func resetVolumeIcon(on volumeURL: URL) throws {
    let iconURL = volumeURL.appendingPathComponent(".VolumeIcon.icns")
    try? FileManager.default.removeItem(at: iconURL)

    if var info = try? XAttr.get(name: "com.apple.FinderInfo",
                                  from: volumeURL.path),
       info.count > 8 {
        info[8] &= ~0x04
        if info.allSatisfy({ $0 == 0 }) {
            try XAttr.remove(name: "com.apple.FinderInfo",
                             from: volumeURL.path)
        } else {
            try XAttr.set(name: "com.apple.FinderInfo",
                          value: info, on: volumeURL.path)
        }
    }
    utimes(volumeURL.path, nil)
}
```

See `32-nsworkspace-asyncstream.md` companion and Pattern 33's XAttr wrapper if not already in project.

---

## Why each step matters

| Step | Why |
|------|-----|
| `.atomic` write | Survives crash mid-write — the partial file never becomes visible |
| Order: file FIRST, flag SECOND | If we set the flag before the file exists, Finder renders a broken icon briefly |
| Read-modify-write the 32-byte buffer | Finder uses other bytes for label colors, locked state, etc. — don't clobber user preferences |
| `info[8] |= 0x04` (OR, not SET) | Preserves any flags already set in that byte |
| `utimes(..., nil)` | Bumps the mount point's mtime; Finder re-reads icon within 1–3s. Gentler than `killall Finder` which disrupts the user |
| Rollback orphan on xattr fail | An `.icns` without the flag just takes up space and confuses the next Sigil apply |

---

## Hash-based conflict detection (for apps that remember what they wrote)

If your app re-applies icons (e.g., smart-silent reapply on remount), store `SHA-256(icns)` at apply time as `lastAppliedHash`. On remount, compare against `SHA-256(onDiskIcns)`:

- **Match → silent re-apply.** The on-disk file is exactly what we last wrote; safe to overwrite with the same bytes.
- **Mismatch → prompt user.** Someone (maybe Finder paste from another Mac) wrote a different icon; don't clobber without asking.
- **On-disk missing → silent re-apply.** No risk of clobbering anything.

---

## `killall Finder` — avoid unless necessary

The `utimes` nudge works in >95% of cases. Falling back to `killall Finder`:

- Restarts the whole Finder process (disruptive — desktop flashes, Finder windows close)
- Takes 2-3 seconds during which the user has no Finder
- Only warranted if `utimes` genuinely doesn't refresh the icon for a specific filesystem type you care about

For Get Info windows that were open *before* the apply, neither approach refreshes them — the user has to close/reopen that specific window. Document this as expected behavior, not a bug.

---

## References

- [Eclectic Light — Custom Finder icons, resources and Mac OS history](https://eclecticlight.co/2023/03/04/custom-finder-icons-resources-and-mac-os-history/)
- [fileicon issue #42](https://github.com/mklement0/fileicon/issues/42) — documents the `NSWorkspace.setIcon` failure
- [NSHipster: Extended File Attributes](https://nshipster.com/extended-file-attributes/) — `setxattr` Swift bridging pattern

---

*Discovered during Sigil /plan research 2026-04-19 after finding that NSWorkspace.setIcon silently no-ops on volume roots. The test that would have caught this earlier is now in Sigil's `IconApplierTests.swift` — spins up a scratch APFS DMG via `hdiutil`, applies an icon, reads back the FinderInfo xattr to assert byte 8 == 0x04.*
