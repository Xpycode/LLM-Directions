# Volume Enumeration — The "External Drive" Heuristic

**Source project:** `1-macOS/Sigil/`

> **Trigger:** listing mounted volumes in a macOS app, distinguishing "external drives" from "system/boot/DMG"

macOS exposes five volume flags via `URLResourceKey` that all sound like "external drive" but mean subtly different things. Getting this wrong filters out the drives users expect to see. Getting it right is ~15 lines of Swift.

---

## The confusion — what the flags actually mean

| Flag | True for | False for |
|------|----------|-----------|
| `volumeIsRemovableKey` | **Physical media** is removable: SD cards, DVDs, floppies | External SSD/HDD (sealed enclosure), network shares, DMGs |
| `volumeIsEjectableKey` | User can eject it: external drives, DMGs, network shares | Internal partitions, boot, ramdisks |
| `volumeIsInternalKey` | Connected via internal bus: built-in SSD partitions | Everything else (external, network, DMG) |
| `volumeIsRootFileSystemKey` | The boot volume mount `/` | All other mount points |
| `volumeIsBrowsableKey` | User-visible in Finder | System-hidden mounts |

**The trap:** `isRemovable` sounds like "the user can unplug it" — but that's `isEjectable`. Most external SSDs report `isRemovable=false, isEjectable=false, isInternal=false` because:
- The storage media is sealed inside the enclosure (→ not "removable")
- The OS treats it as fixed storage (→ not "ejectable" in the physical-media sense)
- It's not on the internal bus (→ not "internal")

A filter of `isRemovable && !isInternal` **excludes every external SSD on the planet.**

---

## The pattern

```swift
import Foundation

struct VolumeInfo: Sendable, Hashable, Identifiable {
    let identity: String?          // URLResourceKey.volumeUUIDStringKey
    let url: URL
    let name: String
    let capacityBytes: Int?
    let isInternal: Bool
    let isRootFileSystem: Bool
    let format: String?            // "APFS", "exFAT", etc.

    var id: String { identity ?? url.path }

    /// Mounted disk image heuristic — tagged for filtering out Time Machine
    /// snapshots, Apple system DMGs, and third-party mounted DMGs.
    var isLikelyDiskImage: Bool {
        let path = url.path
        return path.contains("/.timemachine/") ||
               path.contains("/Snapshots/") ||
               path.hasPrefix("/Volumes/com.apple.")
    }

    /// The right heuristic for "user's external drives by default".
    var isExternalForDefaultListing: Bool {
        !isRootFileSystem && !isInternal && !isLikelyDiskImage
    }

    /// Human-readable type label for a detail pane.
    var typeLabel: String {
        if isRootFileSystem { return "Boot" }
        if isLikelyDiskImage { return "Disk image" }
        if isInternal { return "Internal" }
        return "External"
    }
}

actor VolumeEnumerator {
    private static let resourceKeys: Set<URLResourceKey> = [
        .volumeUUIDStringKey,
        .volumeNameKey,
        .volumeTotalCapacityKey,
        .volumeIsInternalKey,
        .volumeIsBrowsableKey,
        .volumeIsRootFileSystemKey,
        .volumeLocalizedFormatDescriptionKey,
    ]

    func currentVolumes(includeSystem: Bool = false) -> [VolumeInfo] {
        let urls = FileManager.default.mountedVolumeURLs(
            includingResourceValuesForKeys: Array(Self.resourceKeys),
            options: [.skipHiddenVolumes]
        ) ?? []

        return urls.compactMap { url -> VolumeInfo? in
            guard let info = Self.makeInfo(from: url) else { return nil }
            if !includeSystem, !info.isExternalForDefaultListing {
                return nil
            }
            return info
        }
    }

    private static func makeInfo(from url: URL) -> VolumeInfo? {
        guard let v = try? url.resourceValues(forKeys: resourceKeys) else {
            return nil
        }
        return VolumeInfo(
            identity: v.volumeUUIDString,
            url: url,
            name: v.volumeName ?? url.lastPathComponent,
            capacityBytes: v.volumeTotalCapacity,
            isInternal: v.volumeIsInternal ?? false,
            isRootFileSystem: v.volumeIsRootFileSystem ?? false,
            format: v.volumeLocalizedFormatDescription
        )
    }
}
```

---

## The 3 heuristics this resolves

### 1. "Show me external drives by default"

`!isRootFileSystem && !isInternal && !isLikelyDiskImage`

Excludes:
- Boot volume (`/`)
- Internal SSD partitions (Data, Recovery, Preboot, etc.)
- Time Machine local snapshots
- Mounted `com.apple.*` DMGs
- System-managed mount points

Includes everything a user thinks of as "a drive I plugged in."

### 2. "Show me everything" (power-user toggle)

Drop the filter, return all `mountedVolumeURLs`. Still useful because it includes `Macintosh HD`, `Recovery HD`, mounted DMGs, etc.

### 3. Type label for a detail pane

`typeLabel` returns "Boot" / "Internal" / "Disk image" / "External" — a compact, honest description without claiming a sealed USB SSD is "removable."

---

## Volume UUID stability across filesystems

`URLResourceKey.volumeUUIDStringKey` returns:
- **APFS / HFS+:** a proper UUID, stable across rename/remount, regenerated on reformat
- **exFAT / FAT32:** the 32-bit DOS Volume Serial Number (shown as a UUID-ish string), regenerated on reformat
- **NTFS:** the NTFS Volume Serial Number, stable across remount
- **RAM disks:** often `nil` — handle this case as "can't remember this volume"

For apps that need to *remember* a volume (keyed storage), use the UUID as the primary key. Fall back to showing but not remembering when UUID is nil.

---

*Discovered during Sigil Wave 3 implementation when the default-filter sidebar turned up empty despite four external drives being plugged in. Initial filter was `isRemovable && !isInternal`; corrected after checking Apple's URLResourceKey docs against actual runtime values on APFS externals.*
