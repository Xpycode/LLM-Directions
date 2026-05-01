# Inherited-project dead-code sweep

**Source:** `1-macOS/AvidMXFPeek/` — Wave 4.6-B (2026-04-20). Project was forked from `P2toMXF` using the [34-xcodeproj-clone-rename](34-xcodeproj-clone-rename.md) recipe; ~65% of the inherited Swift code was dead at the destination project's runtime but still compiled as an internal cluster.

Bulk-remove dead Swift files from an Xcode project when the dead-code graph is **self-contained** (dead files reference each other but nothing live references them). Combines disk-level `rm`, sed-based pbxproj cleanup, in-place trim of partially-dead files, and a unit-test safety net. Handles the cases that doing it one file at a time through the Xcode navigator doesn't.

---

## When to use

You have:
- An Xcode project forked or cloned from another project (via [34-xcodeproj-clone-rename](34-xcodeproj-clone-rename.md) or similar)
- A meaningful chunk of the inherited code is dead at the new project's runtime — different feature set, different UI, different pipeline
- The dead code forms a cluster (dead files reference each other, but no live file references them) — this is common after forks
- You want to keep the pbxproj well-formed (not just ignore the dead files)
- You have (or will add) tests that cover the live-code paths — critical for this sweep because mistakes land silently

Typical shapes: forked an Xcode app → pruning; removed a major feature → stripping its view tree and backing services; migrating from an old architecture → retiring the legacy path.

**Don't use this pattern** when the dead-vs-live boundary is fuzzy (some code is called conditionally by a feature flag, some code is reachable only in specific build configurations). Resolve the boundary first, then sweep.

---

## Prerequisites

1. **Know the live-code set.** Walk the reachability graph from your entry point (`@main` → `ContentView` → services). Anything NOT reachable is a deletion candidate. Use `grep -rln 'TypeName' --include='*.swift'` to find external references per type.

2. **Know the cluster's self-references.** For each dead type, check if anything LIVE references it. If yes → not dead, don't delete. If only other dead types reference it → part of the cluster.

3. **Have a regression safety net.** Unit tests covering the live paths before the sweep. The pattern of "delete, then test" vs "test, then delete, then test" is the difference between "I broke something and know it" and "I broke something silently." Write the tests first.

4. **Commit or backup.** `cp pbxproj /tmp/pbxproj-pre-sweep.bak`. Disk delete is reversible with git; pbxproj surgery is too small to care about with version control but large enough to want rollback.

---

## The recipe

### Step 1 — Enumerate the dead files

```bash
# In this example: 30 dead files across 4 directories
DEAD_FILES=(
  "ConversionViewModel.swift"
  "ConversionViewModel+CardManagement.swift"
  # ... 4× ConversionViewModel, 4× Models, 13× Services, 9× Views ...
  "QueueListView.swift"
)
```

### Step 2 — Strip pbxproj references via sed

Xcode's pbxproj format references each file in exactly **4 places**, and each of those references contains the filename as a `/* comment */`. That means one sed per file handles all four:

```bash
PBXPROJ=path/to/project.xcodeproj/project.pbxproj

for f in "${DEAD_FILES[@]}"; do
  # Escape regex metachars — `+` appears in extension-file names like FFmpegWrapper+Conversion.swift
  escaped=$(printf '%s' "$f" | sed 's/[+.]/\\&/g')
  sed -i '' "/$escaped/d" "$PBXPROJ"
done
```

This removes:
- The `PBXBuildFile` entry (`<ID> /* filename in Sources */ = { ... };`)
- The `PBXFileReference` entry (`<ID> /* filename */ = { ... };`)
- The `PBXGroup` child entry (`<ID> /* filename */,`)
- The `PBXSourcesBuildPhase` files entry (`<ID> /* filename in Sources */,`)

in one pass, because each of them contains the filename in a visible comment.

**Why this works:** Xcode-generated pbxprojs are consistent about putting the filename comment on every ID reference. Any hand-edited pbxproj may not follow this convention, but the auto-generated ones reliably do.

**Failure modes to watch for:**
- Filename appears in an unrelated context (e.g. a custom build-phase shell script that mentions the filename by string). Spot-check before running: `grep "filename.swift" pbxproj`.
- Filename contains regex-meta characters (`+`, `.`, `[`). Escape them (the `[+.]` class in the sed above covers the common cases for Swift filenames).
- Two files with similar names where one is a prefix of the other (`Foo.swift` vs. `FooBar.swift`). sed's `/pattern/d` will match BOTH on the shorter pattern. Anchor your patterns or delete the longer names first.

### Step 3 — Delete the actual files

```bash
for f in "${DEAD_FILES[@]}"; do
  for dir in . Services Models Views; do
    if [ -f "$dir/$f" ]; then rm "$dir/$f"; fi
  done
done

# If a directory is now empty, drop it too
rmdir Models 2>/dev/null || true
rmdir Views 2>/dev/null || true
```

### Step 4 — Trim files that hold both live and dead code

Some inherited files straddle the fence: an old class + a new class in the same file, or a cluster of related extensions where some extension methods are dead and others live. Don't delete the whole file — trim it.

Find the boundary with a MARK-aware grep:
```bash
grep -n '^// MARK:\|^struct\|^class\|^enum\|^func' some_file.swift
```

Identify the line N at which the live code starts. Trim with `sed`:
```bash
{
  echo "import Foundation"  # if lost when dropping the head
  echo ""
  sed -n "${N},\$p" some_file.swift
} > /tmp/trimmed
mv /tmp/trimmed some_file.swift
```

Or: just rewrite the whole file via the `Write` tool with just the surviving content.

In the AvidMXFPeek example, two files needed trimming:
- `P2CardParser.swift` (613 → 242 LOC): old P2CardParser class lines 1–373 deleted; kept MXFFolderScanner + Clip + ClipAggregator.
- `ReportGenerator.swift` (401 → 199 LOC): old P2 report generator lines 1–199 deleted; kept AuditReportExporter + DTO.

### Step 5 — Trim classes that hold both live and dead methods

Same idea, one level down. A class that inherited 15 methods from the cloned project where 12 are dead: delete the 12, keep the 3, and the properties/types they need. Rewriting the whole file (via `Write`) is often cleaner than surgical method-by-method deletion.

`BMXWrapper.swift` in this example went from ~650 LOC to ~300 LOC — the `info(url:)` method (live, ffprobe-backed) stayed; `rewrapClip` / `rewrapClips` / `runBMX` / `OutputCollector` / `cancel` / `resetCancellation` / `getVersionInfo` / cancellation state / `bmxTranswrapPath` / `mxf2rawPath` properties / legacy `BMXError` cases all went.

### Step 6 — Clean the entry point

Your `@main` struct or AppDelegate may carry stubs that only existed to satisfy the dead code's compile references — notification names the dead views subscribed to, protocol conformances nothing now implements. Remove them.

```swift
extension Notification.Name {
    static let openFolder = Notification.Name("...")
    // DELETE: legacy notifications referenced only by now-deleted views
    // static let openP2Card = ...
    // static let chooseTempFolder = ...
}
```

### Step 7 — Build + test

```bash
xcodebuild -project X.xcodeproj -scheme X -destination 'platform=macOS' clean build
xcodebuild -project X.xcodeproj -scheme X -destination 'platform=macOS' test
```

- `clean` matters: stale derived-data object files from the deleted sources will confuse the incremental build.
- If build fails with "Build input files cannot be found": a reference in pbxproj didn't get removed — grep the pbxproj for the failing filename.
- If build fails with "Cannot find type 'Foo' in scope": a live file still references a dead type you just deleted. Either the file wasn't actually live (re-check), or the reference is in code that should be trimmed too.
- If tests fail: compare before-and-after. The whole point of the safety net is to catch this.

---

## Sizing up the win

For AvidMXFPeek's Wave 4.6-B specifically:

| Metric | Before | After |
|---|---|---|
| Swift source files | 37 | 7 |
| Total LOC | ~4500 | 1507 |
| pbxproj lines | 706 | 586 |
| `.app` clean-build size | 78 MB | 74 MB |
| Dead directories | 2 (Models/, Views/) | 0 |

Time: ~20 minutes including the 5-minute safety-net validation run.

---

## Gotchas

### "Build input files cannot be found" means you forgot a pbxproj reference
`xcodebuild` is strict about missing file refs. If you deleted a file from disk but didn't strip its pbxproj entries, compile fails at input validation, not at Swift compile. The sed pattern above catches all four references per file, but if you added a file manually and the filename comment isn't in the standard format, sed can miss it. Grep verifies: `grep filename.swift pbxproj` should return zero hits post-sweep.

### Don't trust Xcode's "remove references" UI for bulk work
Xcode's navigator can delete 1–2 files cleanly. For 30 files, the UI is slow and you can't see what it actually changes in pbxproj. Sed is faster and auditable.

### PBXFileSystemSynchronizedRootGroup complicates things
Folders wired as `PBXFileSystemSynchronizedRootGroup` (Xcode 16+) auto-discover files — contents aren't listed in pbxproj individually. If the dead code lives in such a folder, deleting files from disk is enough; no pbxproj surgery needed. But if the folder ITSELF is going away, you have to remove the sync-root-group entry, its `PBXFileSystemSynchronizedBuildFileExceptionSet` (if present), and references from `fileSystemSynchronizedGroups` in the target.

### `sed -i ''` vs `sed -i`
macOS's BSD sed requires the empty string after `-i` (backup suffix — '' means no backup). GNU sed doesn't. If you're writing the recipe for cross-platform use, branch on `uname`.

### Rename-file-types and renames via sed
If you also want to RENAME surviving files as part of the sweep (e.g. `BMXWrapper.swift` → `MXFProber.swift`), the sed approach doesn't help — you need to update every occurrence of the old name AND the internal type name AND the pbxproj `path = ...;` line. Consider Xcode's refactor-rename for that, or do it in a separate pass.

### Don't sweep during a dev session that's in-flight
These deletions touch pbxproj, which is shared with Xcode. If Xcode is open on the project during the sweep, it may see inconsistent state and write over your changes. Close Xcode (or at least close the project) before running the sed loop.

---

## Complementary patterns

- **Before sweeping**: write tests covering the live paths ([Swift Testing + `@Test` + inline fixtures](../swift-testing-fixtures.md) if useful)
- **During sweeping**: the 4.6-A step removed bundled binaries via the same pbxproj-surgery discipline; the sed pattern above applies to any `<ID> /* name */` pbxproj reference
- **After sweeping**: use [04-swiftui-performance](04-swiftui-performance.md) to find and remove any now-redundant `@ViewBuilder` / ObservableObject plumbing left behind
- **Renames**: If you want to follow up with type/file renames, [34-xcodeproj-clone-rename](34-xcodeproj-clone-rename.md) covers the in-file sed + pbxproj `path` field updates
