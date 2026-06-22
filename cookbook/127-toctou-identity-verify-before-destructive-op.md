# Verify file identity before a destructive op — close the scan→act TOCTOU gap

**Source:** external study — [github.com/colinvkim/Radix](https://github.com/colinvkim/Radix) (`Radix/Services/AppSystemActions.swift::verifyTrashIdentity`). Also the destructive-op sibling of [[38-destructive-copy-guard]] and [[52-appendingpathcomponent-fs-probe]].

A scan/listing is a **snapshot**. The user acts on a row seconds or minutes later — by then the path may point at a *different file* (replaced, rotated, moved-and-recreated, symlink retargeted). Acting on the stale path sends the **wrong file** to the Trash. This is a time-of-check-to-time-of-use (TOCTOU) hole, and a path string carries no identity to detect it.

The fix: capture a durable filesystem identity **at scan time**, and re-check it **immediately before** the destructive op. Identity = `(st_dev, st_ino)` via `lstat` (note: `lstat`, not `stat` — you want to identify the symlink itself, not chase it), with `fileResourceIdentifierKey` as a fallback for filesystems where inode reuse is a concern.

```swift
struct FileIdentity: Equatable {
    var device: UInt64
    var inode: UInt64
}

// Captured during the scan, stored on the node alongside its URL.
func captureIdentity(_ url: URL) -> FileIdentity? {
    var st = stat()
    let ok = url.withUnsafeFileSystemRepresentation { path -> Bool in
        guard let path else { return false }
        return lstat(path, &st) == 0          // lstat: identify the link, don't follow it
    }
    guard ok else { return nil }
    return FileIdentity(device: UInt64(st.st_dev), inode: UInt64(st.st_ino))
}
```

Then gate the destructive call on a re-check that classifies its outcome — don't collapse to a bool (same lesson as [[61-probe-classify-not-catch-all]]):

```swift
enum IdentityCheck: Equatable {
    case matches
    case mismatch          // path now resolves to a DIFFERENT file → refuse
    case missingNow        // file vanished since the scan → nothing to do
    case unverifiable(String)
}

func verifyBeforeTrash(_ node: FileNode) -> IdentityCheck {
    guard let scanned = node.identity else { return .unverifiable("no scanned identity") }
    var st = stat()
    let rc = node.url.withUnsafeFileSystemRepresentation { p -> Int32 in
        guard let p else { return -1 }
        return lstat(p, &st)
    }
    if rc != 0 {
        return (errno == ENOENT || errno == ENOTDIR) ? .missingNow
                                                      : .unverifiable(String(cString: strerror(errno)))
    }
    let current = FileIdentity(device: UInt64(st.st_dev), inode: UInt64(st.st_ino))
    return current == scanned ? .matches : .mismatch
}

func trash(_ node: FileNode) throws {
    switch verifyBeforeTrash(node) {
    case .matches:               try FileManager.default.trashItem(at: node.url, resultingItemURL: nil)
    case .missingNow:            return                              // already gone — no-op, not an error
    case .mismatch:              throw TrashError.identityChanged(node.url)   // the whole point
    case .unverifiable(let why): throw TrashError.cannotVerify(node.url, why)
    }
}
```

---

## Two guardrails that pair with the identity check

Radix layers a **static block-list** in front of the identity check — a `TrashSafetyPolicy` that refuses protected locations (`/`, `/System`, `~/Library`, volume roots) outright, before any identity logic runs. Cheap, and it catches the "user fat-fingered a volume root" case the identity check would happily pass.

```swift
func validateCanTrash(_ url: URL) throws {
    if let reason = TrashSafetyPolicy.blockReason(for: url) {
        throw TrashError.protectedLocation(reason.path)
    }
}
```

Order matters: **block-list first** (refuse dangerous *targets*), **identity check second** (refuse stale *references* to safe targets).

---

## When to apply this

- Any op that **deletes, trashes, overwrites, or moves** a file chosen from an *earlier* listing — file managers, disk analyzers, dedupe tools, batch processors, watch-folder ledgers (Conjoyn).
- Especially when the gap between listing and action is user-paced (a table the user browses) or long (a background queue draining minutes later).

**Skip when:** you stat-and-act in the same synchronous breath with no user interaction or `await` between — there's no window for the file to change.

---

## Companion patterns

- **[[38-destructive-copy-guard]]** — the copy-side sibling: guard `removeItem → copyItem` and the `src == dest` case before clobbering a destination.
- **[[52-appendingpathcomponent-fs-probe]]** — why a path string is an unreliable identity once the filesystem mutates; pairs with capturing `(dev, ino)` instead.
- **[[61-probe-classify-not-catch-all]]** — same discipline: classify the check's outcome into cases that map to distinct user-facing actions, never a lossy bool.

---

*Drafted 2026-06-22 from studying Radix's pre-trash `verifyTrashIdentity`. The insight worth keeping: a scan result is a promise about the past; re-verify identity at the moment you act, because the path is the only thing that survived and the path is not the file.*
