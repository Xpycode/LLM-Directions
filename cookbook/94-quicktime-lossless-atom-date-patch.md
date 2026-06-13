# 94 — Lossless in-place QuickTime/ISO-BMFF date patch in pure Swift (no ffmpeg), proven by AVAssetWriter + byte-diff

**Problem.** You want to change a video's **embedded** encode date (`mvhd`/`tkhd`/`mdhd` `creation_time`) on MP4/M4V/MOV. Every reference app shells out to **ffmpeg/ffprobe** — a Homebrew dependency, sandbox friction, and a full **re-mux that rewrites the whole file**. AVFoundation's `AVAssetExportSession`/`AVAssetWriter` can't write back to the source URL either: they produce a *new* file → need enclosing-**directory** sandbox access (a single user-selected *file* grant isn't that), reset the FS creation date, and may drop the sandbox grant on the new inode.

**Key realization:** those date fields are **fixed-width** integers. Overwriting them never changes a box size, never shifts `mdat`, never invalidates the `stco`/`co64` chunk-offset tables. So the edit is a handful of **same-length byte overwrites at known offsets** — lossless, instant, no re-encode, no external binary, and sandbox-correct because you mutate the exact file the sandbox granted via `FileHandle(forUpdating:)`.

## Pattern — read through a seekable `ByteSource`, locate fields, overwrite in place

**Two epochs.** QuickTime/ISO-BMFF count seconds since **1904-01-01 UTC**; Unix counts from 1970. Fixed gap = 2,082,844,800 s. Return **signed** `Int64` so a pre-1904 date is a negative sentinel you reject, not an 18-quintillion unsigned wrap.

```swift
enum QuickTimeEpoch {
    static let offset: Int64 = 2_082_844_800
    static func secondsSince1904(from d: Date) -> Int64 { Int64(d.timeIntervalSince1970.rounded(.towardZero)) + offset }
    static func date(fromSecondsSince1904 s: Int64) -> Date { Date(timeIntervalSince1970: TimeInterval(s - offset)) }
    // version-0 fields are uint32 → ceiling is 2040-02-06 06:28:15 UTC. You CANNOT widen a box to
    // version-1 in place (changes its size, shifts mdat) → reject overflow, never truncate.
    static func fitsVersion0(_ s: Int64) -> Bool { s >= 0 && s <= Int64(UInt32.max) }
}
```

**Read via an abstraction, never the whole file.** Video files are gigabytes and `moov` is often *after* `mdat`. A `ByteSource` that reads N bytes at an offset lets the same parser run over an in-memory `[UInt8]` (tests) or a seeking `FileHandle` (production, header-only reads). The box scanner handles every header form:

```swift
// size(4) | type(4) [ | largesize(8) if size==1 ] [ | usertype(16) if type=="uuid" ]
while cursor < end {
    guard cursor + 8 <= end else { throw AtomError.readOutOfBounds(...) }   // truncated header
    let size32 = Int(try src.readUInt32BE(at: cursor))
    let type = try src.readFourCC(at: cursor + 4)
    var headerSize = 8
    let total: Int
    switch size32 {
    case 1:  headerSize = 16; total = Int(try src.readUInt64BE(at: cursor + 8))  // 64-bit largesize
    case 0:  total = end - cursor                                                // runs to EOF
    default: total = size32
    }
    if type == "uuid" { headerSize += 16 }
    guard total >= headerSize else { throw AtomError.invalidBoxSize(...) }       // corrupt/lying size
    guard cursor + total <= end else { throw AtomError.boxExceedsContainer(...) } // corruption firewall
    boxes.append(Box(type: type, offset: cursor, headerSize: headerSize, size: total))
    cursor += total
}
```

**Locate the date fields.** Walk `moov → mvhd`, every `trak → tkhd`, every `trak → mdia → mdhd`. With content start `C = box.offset + headerSize`, byte `C+0` is `version`:

| version | creation_time | modification_time |
|---|---|---|
| 0 | `[C+4…C+7]` uint32 BE | `[C+8…C+11]` uint32 BE |
| 1 | `[C+4…C+11]` uint64 BE | `[C+12…C+19]` uint64 BE |

Refuse what you can't safely patch — **before touching bytes**: a `cmov` child of `moov` (movie header is zlib-compressed → dates live in a blob), a missing `moov`, an unknown `version`.

**Compute pure patches, then write in place.** Separate *compute* (`[BytePatch]`, a pure list) from *apply* — the same patch drives the in-memory test and the file write, and you can assert *only* the intended offsets changed:

```swift
struct BytePatch { let offset: Int; let bytes: [UInt8] }   // overwrite-only ⇒ length can't change

static func applyToFile(at url: URL, _ patches: [BytePatch]) throws {
    guard !patches.isEmpty else { return }
    let h = try FileHandle(forUpdating: url)
    defer { try? h.close() }
    for p in patches { try h.seek(toOffset: UInt64(p.offset)); try h.write(contentsOf: Data(p.bytes)) }
    try h.synchronize()                                    // flush to disk
}
```

**Refusal-before-write ordering** (the "never corrupt" guarantee). Open read-only to locate, **close**, compute patches (which can throw on overflow/cmov), and only *then* open for update. A crash or refusal mid-operation can never leave a half-written file:

```swift
let src = try FileByteSource(url: url)
let layout: MovieDateLayout
do { layout = try AtomLocator.locate(in: src) } catch { src.close(); throw error }
src.close()
let value = QuickTimeEpoch.secondsSince1904(from: date)
let patches = try AtomDatePatcher.patches(for: layout, secondsSince1904: value, setModification: true) // may throw
try AtomDatePatcher.applyToFile(at: url, patches)          // file opened forUpdating only now
```

## Verifying losslessness with NO ffprobe installed — AVAssetWriter + byte-diff

ffprobe is the very dependency you're avoiding, so don't rely on it for the test. Generate a **real** movie with macOS's own `AVAssetWriter` (it writes `moov`-after-`mdat` — the exact layout that trips naive parsers), patch it, and assert byte-for-byte that *only* the date offsets changed. This is **stronger** than ffprobe's single-field readout — it catches any stray write to `mdat` or a box size:

```swift
let before = try Data(contentsOf: url)
let layout = try EmbeddedDateEditor.setDate(target, forFileAt: url)
let after  = try Data(contentsOf: url)
#expect(after.count == before.count)                       // 1. lossless: same length
let patches = try AtomDatePatcher.patches(for: layout, secondsSince1904:
    QuickTimeEpoch.secondsSince1904(from: target), setModification: true)
let changed = Set(patches.flatMap { $0.offset ..< ($0.offset + $0.bytes.count) })
for i in before.indices where !changed.contains(i) {
    #expect(after[i] == before[i])                         // 2. only date-field bytes differ
}
// 3. re-parse the real file from disk → reads target back
```

`TinyMovie` helper: `AVAssetWriter(fileType: .mov)`, one 16×16 H.264 frame via `AVAssetWriterInputPixelBufferAdaptor`, `startWriting()` → `startSession(atSourceTime: .zero)` → append one `CVPixelBuffer` → `markAsFinished()` → `await finishWriting()`. ~40 lines, no committed binary fixture.

## Why each decision

- **In-place overwrite, not export/atomic-replace.** Fixed-width fields ⇒ no box-size change ⇒ no `mdat` shift ⇒ `stco`/`co64` stay valid. Export needs *directory* sandbox access and resets the FS creation date; in-place mutates the granted file only.
- **`ByteSource` abstraction, not a whole-file buffer.** Read only 8–16-byte headers and seek past a multi-GB `mdat`; one parser, in-memory for tests + `FileHandle` for production. `moov`-after-`mdat` falls out for free.
- **Signed `Int64` for 1904-seconds.** Pre-1904 → negative sentinel you reject; never wraps into a plausible far-future unsigned value that would corrupt the file.
- **Refuse version-0 overflow (2040), don't truncate.** Widening to version-1 in place would change the box size. Atomic all-or-nothing beats silently leaving `mvhd`/`tkhd`/`mdhd` disagreeing (the #1 "it didn't really work" complaint).
- **Compute (`[BytePatch]`) separate from apply.** Pure, testable, and proves losslessness by construction (overwrite-only can't resize). Same patch list for memory + disk.
- **Locate → close → compute → open-for-update.** Every refusal (`cmov`/`noMoov`/overflow) happens with the file never opened for writing.
- **AVAssetWriter + byte-diff as the proof.** No external tooling, real-world container layout, and catches losslessness violations ffprobe can't see.

## Gotchas

- **`moov` may be after `mdat`.** Always scan top-level boxes from offset 0; handle `free`/`skip`, `size==1` largesize (big `mdat`), `size==0` (EOF), `uuid` (skip its 16-byte usertype). AVAssetWriter output is non-fast-start (`moov` last) — a great adversarial fixture.
- **Two date layers, two stores.** This patches the **binary** integer fields (Get Info "Content created" via Spotlight reimport). The `udta`/`com.apple.quicktime.creationdate` ISO-8601 **string** is the only variable-length case — overwrite it **only if it already exists AND the new string is the same byte length** (Apple's `YYYY-MM-DDThh:mm:ss±HHMM` is fixed 24 bytes); else skip + warn, never resize in place. Filesystem Created/Modified is a *third* layer (`FileManager.setAttributes`, with read-back verify — `setAttributes` silently ignores rejected changes).
- **`cmov` = refuse.** Compressed movie header; dates are inside a zlib blob — can't patch in place.
- **Corruption firewall.** A lying `size` field must throw before any read/write past the box's real bounds (`boxExceedsContainer`/`invalidBoxSize`) — never trust declared sizes.
- **FileHandle seek/read/write throw on macOS 10.15.4+** (`read(upToCount:)`, `write(contentsOf:)`, `seek(toOffset:)`); `synchronize()` to flush. The source `FileByteSource` holds a mutable seek position → one instance per sequential parse, not thread-safe.

**Source.** VEDC (Video Encode Date Changer) `VEDCFeature/Engine/` (`QuickTimeEpoch`, `ByteSource`/`FileByteSource`, `BoxWalker`, `AtomLocator`, `AtomDatePatcher`, `EmbeddedDateEditor`) + `Dates/` (`FilesystemDates` read-back verify), 2026-06-13. 38 tests, TDD. The lossless-atom-edit differentiator vs. the ffmpeg-based reference apps. Pairs with **#52** (`appendingPathComponent` FS-probe), **#38** (destructive-copy guard) for the file-handling side.
