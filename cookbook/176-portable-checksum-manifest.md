# 176 — A provenance record the user can verify without your app

**Tags:** shasum, sha256, checksum manifest, ASC-MHL, provenance, verify, relative path, integrity, file copy, backup, archive

**Extracted from:** MediaIngest (2026-08-07)

## The problem

Your app copies files and verifies them — hash the source, hash what landed, compare. The claim
"these bytes are the original bytes" is true at the moment of the copy, and then it evaporates. A
year later, holding the drive, the user has no way to re-ask the question, and neither do you. A
report saying "1,753 files verified ✓" is a *claim about the past*; it isn't checkable.

The instinct is to invent a format, or reach for a standard. Both are traps:

- **A custom format** means only your app can verify — so the record dies with the app.
- **The domain standard may not fit.** ASC-MHL is the film industry's answer to exactly this and
  cannot carry SHA-256. Check what a standard actually encodes before adopting it for its name.

## The pattern

Write a sidecar in **`shasum`'s own text mode**. It ships with macOS and every Linux box, and its
`-c` mode *is* the check rather than a description of one.

```
<64 hex chars><space><space><path>
```

Two rules make it worth writing:

**1. Paths relative to the tree root, not absolute.** Absolute paths verify one machine's mount
layout; the file breaks the moment the volume mounts elsewhere or the tree is copied to another
disk. Relative paths verify *the content*. Pick the narrowest folder that is always correct — one
job may span several subfolders, so anchor above them, and put the `cd` in the printed command:

```
cd "/Volumes/V26/00-PHOTOS X-S20" && shasum -a 256 -c "Reports/manifest.sha256"
```

**2. Digests must be final on-disk truth, not what you hashed earlier.** Any post-copy step that
rewrites files — metadata tagging, EXIF/GPS writes, transcode, permission fixups — invalidates the
copy-time digest for exactly the files you touched. Re-read those; reuse the digest you already hold
for everything else. Classify by outcome so the choice is a value, not a guess:

```swift
/// Whether a post-copy phase may have rewritten this file, so any digest taken
/// before it may no longer describe the bytes on disk.
var mayHaveBeenRewritten: Bool {
    switch self {
    // Every case reachable only through the rewriting phase — including its
    // FAILURE cases: one batch invocation covers many files, so a batch that
    // threw may still have rewritten some before it did.
    case .copiedAndTagged, .copiedNoCoverage, .copiedTagFailed,
         .taggedInPlace, .taggedInPlaceFailed:      return true
    case .copied, .alreadyTagged, .skippedIdentical: return false
    case .conflict, .failed, .notAttempted:          return false
    }
}
```

## The restraint that makes `OK` mean something

**List only what you actually verified.** A file that merely *exists* at the destination — one you
refused to overwrite, one another process put there — must not get a line. Nor may a file whose
digest you failed to read: drop the row rather than guessing or back-filling from the source hash.
A manifest is worth exactly what its weakest line is worth.

Corollaries: don't write an empty manifest (`shasum -c` rejects one anyway); include the sidecar's
extension in whatever never-overwrite/uniquify check guards your other outputs; and omit paths
containing a newline — the format is line-oriented with no escaping, so one such name corrupts every
line after it.

## Avoiding the extra full read

Re-hashing everything at the end can silently add a whole pass over the data. In MediaIngest a
re-import already hashed both sides during collision detection, so a naive manifest would have read
the destination tree a **third** time — ~62 GB and ~19 min on a real card, on the flow meant to be a
fast no-op. **Keep the digest you already computed** instead of recomputing it:

```swift
struct CollisionResult { let status: CollisionStatus; let destinationHash: String? }
```

## Test it with the real binary, then break it

A test that reimplements the format proves nothing. Shell out to the actual tool from the actual
directory, assert exit 0 — **then tamper one byte and require it to fail**:

```swift
var bytes = try Data(contentsOf: victim)
bytes[bytes.count / 2] ^= 0xFF
try bytes.write(to: victim)
let tampered = try runShasumCheck(manifest: url, from: treeRoot)
XCTAssertNotEqual(tampered.status, 0)
XCTAssertTrue(tampered.output.contains("FAILED"))
```

Mutating the source to publish stale copy-time digests must make this test fail — it did, 5 ways.
A verification that cannot fail is decoration. See also [[negative-checks-pass-vacuously]].
