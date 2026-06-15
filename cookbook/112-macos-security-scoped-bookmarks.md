# 112 — Security-scoped bookmarks: re-open user-picked files/folders across launches (sandboxed macOS)

**Extracted from:** Penumbra (canonical — the only sandboxed one), Conjoyn, TimeCodeEditor, DiskVerdict (2026-06-15)

A **sandboxed** macOS app loses access to a user-picked file the moment it relaunches. `NSOpenPanel` (Powerbox) grants access for *this session only*; the path you saved is just a string with no permission behind it. To re-open the file next launch — recents, watched folders, a persisted job queue, "last project" — you persist a **security-scoped bookmark** (an opaque `Data` blob carrying the grant), not the path.

> **First question: are you actually sandboxed?** `.withSecurityScope` bookmarks and `start/stopAccessingSecurityScopedResource()` are **no-ops outside the App Sandbox**. Of the four apps this was extracted from, **only Penumbra is sandboxed** — the other three are Developer-ID/non-MAS (Hardened Runtime only) and their bookmark code is correct-but-inert belt-and-suspenders; they work from path strings alone. Check the entitlement before cargo-culting the machinery:
> ```bash
> grep -l 'com.apple.security.app-sandbox' **/*.entitlements
> ```
> If the app isn't sandboxed, you don't need any of this — a plain path round-trips. The pattern below is for when you *are* sandboxed (MAS, or you opted into the sandbox for some capability).

## The canonical mint → store → resolve cycle

All four apps converge on the exact same API calls (nobody uses `.minimalBookmark` or resource keys):

```swift
// MINT — at pick time, while you still hold the Powerbox grant.
// (start/stop here is the no-op-outside-sandbox pair; harmless, and required inside it.)
let didStart = url.startAccessingSecurityScopedResource()
defer { if didStart { url.stopAccessingSecurityScopedResource() } }
let bookmark = try url.bookmarkData(options: .withSecurityScope,
                                    includingResourceValuesForKeys: nil,
                                    relativeTo: nil)        // store this Data

// RESOLVE — next launch.
var isStale = false
let resolved = try URL(resolvingBookmarkData: bookmark,
                       options: .withSecurityScope,
                       relativeTo: nil,
                       bookmarkDataIsStale: &isStale)
guard resolved.startAccessingSecurityScopedResource() else {
    // access denied — treat the entry as permission-lost (see below), don't crash
    throw BookmarkError.accessDenied
}
defer { resolved.stopAccessingSecurityScopedResource() }
```

**Where to store the `Data`** is the only real divergence — pick by use case:

| App | Storage | Scope unit |
|-----|---------|------------|
| DiskVerdict | `UserDefaults`, per-volume key `…scopedBookmark.<mountPath>` | one folder per volume |
| Conjoyn / TimeCodeEditor | JSON `queue.json` in App Support (Codable job model) | a persisted queue, 2 bookmarks/job |
| Penumbra | versioned JSON `Envelope` in App Support + in-folder sidecar | per-file + a folder anchor |

A single recent → `UserDefaults`. A list/queue → JSON in `~/Library/Application Support/`. **Store the path string alongside the bookmark** — `URL`'s Codable form is lossy, plain paths round-trip exactly and give you a degraded fallback when the bookmark is nil.

## Always re-mint on `isStale` (this is how a bookmark survives a file move)

Unanimous across all four apps: when `bookmarkDataIsStale` comes back `true`, the bookmark still resolved (the file moved/renamed but is reachable) — **re-create it and persist the fresh `Data`**, or it will eventually rot. The resolved URL inherits the original grant, so you can re-mint immediately:

```swift
if isStale {
    // we already hold scope on `resolved` from the guard above
    if let refreshed = try? resolved.bookmarkData(options: .withSecurityScope,
                                                  includingResourceValuesForKeys: nil,
                                                  relativeTo: nil) {
        persist(refreshed)   // write back to UserDefaults / the job model / the JSON
    }
}
```
**Corrupt ≠ stale:** if `URL(resolvingBookmarkData:)` *throws* (unresolvable), the entry is dead → discard the key (DiskVerdict) or mark the job `.failed("permission lost")` at load (the queue apps). Never let it crash the launch.

## Start/stop discipline for a queue — defend against over-release

The recurring bug in multi-item apps is **double-stop**: two jobs reference the same folder, both `stop`, and the second stop releases a scope that's still in use. Conjoyn and TimeCodeEditor solve it identically — a central tracking `Set<URL>` keyed on `standardizedFileURL` plus a tri-state result so a *borrower* never stops a scope it didn't open:

```swift
enum AccessResult { case newlyGranted, alreadyActive, denied }

private var accessed: Set<URL> = []          // keyed on standardizedFileURL — see #52

func startAccessingIfNeeded(_ url: URL) -> AccessResult {
    let key = url.standardizedFileURL
    if accessed.contains(key) { return .alreadyActive }   // someone else owns it
    guard key.startAccessingSecurityScopedResource() else { return .denied }
    accessed.insert(key)
    return .newlyGranted
}

func stopAccessingIfNeeded(_ url: URL) {
    let key = url.standardizedFileURL
    guard accessed.remove(key) != nil else { return }      // only stop what we started
    key.stopAccessingSecurityScopedResource()
}

// caller stops ONLY a scope it newly opened:
let access = startAccessingIfNeeded(folder)
defer { if access == .newlyGranted { stopAccessingIfNeeded(folder) } }
```

> **`await` does not run `defer` early** (Conjoyn's hard-won lesson). If you `await` work that needs the scope, it must complete *before* the enclosing function returns — a `defer { stop }` fires at function exit, not at the `await` suspension, but if you structured the teardown wrong the scope can be gone by the time an awaited continuation runs. Keep the scoped work synchronous within the `defer`'s function, or hold scope explicitly across the async boundary.

## Notes / caveats (the consolidated gotcha list)

- **Bookmark a *directory* when you need to write a new file into it.** For an output you haven't created yet, bookmark the output's **parent folder**, not the not-yet-existing file. And when you resolve that folder bookmark, don't clobber the stored output *file path* — copy back only the refreshed bookmark fields, not the whole model (you'll wipe `.preparing`/`startedAt`).
- **Child URLs from `contentsOfDirectory` carry no Powerbox grant of their own** — `startAccessingSecurityScopedResource()` returns `false` on them. Rely on the *parent's* transitive scope to mint child bookmarks; don't bail just because the child's `start` returned false.
- **Resolving is slow synchronous I/O** that can wake a sleeping external volume (Penumbra saw ~20s cold, hit 3–4× per open). Cache the resolved URL (resolve-once), invalidate only when the bookmark changes, and keep resolution off the main actor.
- **macOS 26 `.nofollow` bug** (Penumbra): a bookmark to a *volume root* can resolve to `file:///.nofollow/` — detect and treat as dead rather than trusting it.
- **Sandboxed XCTest can't round-trip real security-scoped bookmarks** — make the resolver an injectable seam so tests can stub it.
- **Entitlements:** under the sandbox you need `com.apple.security.files.user-selected.read-write`; the explicit `com.apple.security.files.bookmarks.app-scope` / `…document-scope` keys are technically the formal declaration for minting `.withSecurityScope` bookmarks (Penumbra ships without them and relies on the implicit user-selected grant — works, but a potential audit flag, so add them if you want to be correct-by-the-book).

Source: Penumbra `Penumbra/Models/Video.swift` (`resolveOnce`/`accessibleURL`/`detectBookmarkStatus`/`relink`, the `.live`/`.stale`/`.dead` status enum — the most complete lifecycle, cite this first); Conjoyn `Services/QueueManager.swift` + TimeCodeEditor `Services/CorrectionQueue.swift` (the `AccessResult` + tracking-`Set` queue discipline, near-identical); DiskVerdict `Engine/ScopedTarget.swift` (tidy single-folder textbook version, but dormant/non-sandbox — minimal illustration only). Pairs with #52 (`standardizedFileURL` / `appendingPathComponent` URL-identity that the tracking `Set` depends on), #05 (file pickers / import that mint the bookmark), #11 (drag-drop, the other entry point), #37 (effective-source fallback), #00 (App Shell Standard).
