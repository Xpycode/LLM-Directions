# 122 — Tolerant `Codable` migration that can't wipe a persisted collection (hand-written `init(from:)`, legacy-key remap, `try?`-to-nil sub-blob)

**Tags:** Codable migration, init(from:), decodeIfPresent, try? nil, CodingKeys, enum rename, persisted array wipe, self-healing JSON

**Problem.** You persist a `[Job]` (or `[Item]`) as one JSON file — an export queue, a project list, a settings array. You ship a new version that **renames an enum** (`verifyLevel` → `verifyTier`), **restructures a nested value** (`VerificationResult` gets a whole new shape), or **adds required fields**. Synthesized `Codable` decoding is **all-or-nothing per container**: if *one* job in the array fails to decode (missing key, changed enum case, reshaped sub-object), `JSONDecoder().decode([Job].self, …)` **throws for the entire array** — the user's whole queue silently vanishes on the next launch. This is the single highest-blast-radius bug in any persisted-collection app: a one-field schema drift wipes everything.

**Key realization.** Synthesized `Codable` ignores your property default values and requires every non-optional key. The fix is a **hand-written `init(from:)`** that decodes *defensively*: `decodeIfPresent` + a default for every field that could be absent in an old file, a **decode-only legacy key** that migrates into the new property, and — for a nested value whose *shape* changed — a **`try?` that degrades that one sub-blob to `nil`** instead of throwing the whole element. Get this wrong and an old `queue.json` throws and wipes the queue; get it right and a legacy job loads with one missing seal.

## Pattern — hand-written `init(from:)`/`encode(to:)` with three migration moves

```swift
struct CorrectionJob: Identifiable, Codable, Sendable {
    let id: UUID
    let verifyTier: VerifyTier            // NEW name; old files wrote `verifyLevel`
    var verification: VerificationResult? // shape CHANGED this version
    var totalSourceBytes: Int64?          // field ADDED a version ago
    var status: JobStatus = .pending
    // transient run-state — deliberately NOT persisted:
    var verificationProgress: Double = 0
    var isDeepVerifying: Bool = false

    enum CodingKeys: String, CodingKey {
        case id, verifyTier
        case verifyLevel        // legacy, DECODE-ONLY (never encoded) — the migration hook
        case totalSourceBytes, status, verification
        // verificationProgress / isDeepVerifying absent ⇒ never persisted
    }

    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        id = try c.decode(UUID.self, forKey: .id)

        // MOVE 1 — renamed enum: new key wins, else migrate the legacy raw value, else default.
        if let tier = try c.decodeIfPresent(VerifyTier.self, forKey: .verifyTier) {
            verifyTier = tier
        } else if let legacy = try c.decodeIfPresent(String.self, forKey: .verifyLevel) {
            verifyTier = VerifyTier(legacyRawValue: legacy)   // pure mapper, unit-tested per arm
        } else {
            verifyTier = .standard
        }

        // MOVE 2 — added field: decodeIfPresent + default, so an older file is fine.
        totalSourceBytes = try c.decodeIfPresent(Int64.self, forKey: .totalSourceBytes)
        status = try c.decodeIfPresent(JobStatus.self, forKey: .status) ?? .pending

        // MOVE 3 — reshaped sub-blob: an old payload won't decode → swallow to nil, DON'T throw.
        verification = (try? c.decodeIfPresent(VerificationResult.self, forKey: .verification)) ?? nil
    }

    func encode(to encoder: Encoder) throws {
        var c = encoder.container(keyedBy: CodingKeys.self)
        try c.encode(id, forKey: .id)
        try c.encode(verifyTier, forKey: .verifyTier)        // never write `verifyLevel` again
        try c.encodeIfPresent(totalSourceBytes, forKey: .totalSourceBytes)
        try c.encode(status, forKey: .status)
        try c.encodeIfPresent(verification, forKey: .verification)
        // verificationProgress / isDeepVerifying never encoded — pure run-state
    }
}
```

The legacy enum mapper is a separate, exhaustively-tested initializer (the migration's correctness crux — every arm changes how an old item behaves):

```swift
enum VerifyTier: String, Codable, Sendable, CaseIterable {
    case off, standard, thorough
    init(legacyRawValue raw: String) {           // old: off/quick/streamIntegrity/deep
        switch raw {
        case "off":             self = .off
        case "quick":           self = .standard
        case "streamIntegrity": self = .thorough // preserve "always byte-hash" intent over cost
        case "deep":            self = .thorough
        default:                self = .standard  // unknown legacy value ⇒ safe default, never crash
        }
    }
}
```

## The test that proves it (hand-build the OLD file from the NEW one)

Don't commit a stale fixture — derive the legacy JSON by encoding a current object and rewriting its dict, so the Date/enum/nested encodings are exactly what an old build wrote:

```swift
func testBackCompat_legacyJSON_migratesAndTolerates() throws {
    var dict = try JSONSerialization.jsonObject(
        with: JSONEncoder().encode(sampleJob())) as! [String: Any]
    dict.removeValue(forKey: "verifyTier")          // pre-migration never wrote this…
    dict["verifyLevel"] = "deep"                     // …it wrote the legacy key
    dict["verification"] = ["level": "deep", "seal": "warning", "summary": "old shape"]  // old blob

    let decoded = try JSONDecoder().decode(
        CorrectionJob.self, from: JSONSerialization.data(withJSONObject: dict))

    XCTAssertEqual(decoded.verifyTier, .thorough,  "legacy 'deep' must migrate")
    XCTAssertNil(decoded.verification, "unreadable legacy blob degrades to nil, never throws the load")
}
```

## Why each decision

- **Hand-written `init(from:)`, not synthesized.** Synthesized `Codable` ignores property defaults and requires every non-optional key — so adding one field retroactively breaks every old file. `decodeIfPresent` + default is the only way an N-versions-old file still loads.
- **Decode-only legacy `CodingKey`.** Keep `case verifyLevel` in `CodingKeys` but read it **only** in `init` and **never** write it in `encode`. New files are pure new-shape; old files migrate forward on first load (and are rewritten clean on next save).
- **`try?`→`nil` for a reshaped *sub-blob*, not the element.** A changed nested struct (new required fields) can't decode from old JSON. Wrapping just that one `decodeIfPresent` in `try?` turns "whole job throws" into "this job shows no seal." The element survives; one derived value is lost (recomputable).
- **Transient run-state excluded from `CodingKeys`.** Progress/`isVerifying`-style fields are recomputed each run; persisting them bloats the file and resurrects stale spinners. Give them stored defaults and leave them out of the keys (a struct property with a default need not be set in a custom `init`).
- **Pure legacy-mapper, unit-tested per arm.** The enum collapse is where intent silently changes (`streamIntegrity → thorough` vs `→ standard` is a real product call). Isolate it so each arm is one assertion.
- **Derive the legacy fixture, don't commit one.** Re-serializing a current object then mutating the dict keeps Date/enum encodings honest and the test self-maintaining.

## Gotchas

- **`try?` of an `Optional` already flattens** (Swift 5+): `(try? c.decodeIfPresent(T.self, …))` is `T?`, so the trailing `?? nil` is belt-and-suspenders, not required — but harmless and reads as intent.
- **`decodeIfPresent` still throws on a *present-but-malformed* value** — that's exactly why MOVE 3 needs `try?`. A key that's *absent* returns nil cleanly; a key that's there with the wrong shape throws unless you swallow it.
- **The blast radius is the container, not the element.** `decode([Job].self)` aborts on the first bad element. There's no per-element recovery from the array decoder — robustness must live **inside each element's `init(from:)`**.
- **Round-trip the *new* shape in a separate test** so you don't accidentally make `encode` lossy while hardening `decode`.
- **If you must drop a truly unreadable element**, decode into `[FailableBox<Job>]` (a wrapper whose own `init(from:)` does `value = try? Job(from:)`) and `compactMap` — but prefer per-field tolerance so you lose a *field*, not a *job*.

**Source.** TimeCodeEditor `Models/CorrectionJob.swift` + `CorrectionJobTests.swift` (Verification V2 phase 1, 2026-06-18): `VerifyLevel{off,quick,streamIntegrity,deep}` → `VerifyTier{off,standard,thorough}` enum collapse with a reshaped `VerificationResult` (stored `seal`/`summary` → computed from `[VerificationCheck]`). The top migration risk flagged in the plan was "a throwing decode of an old `queue.json` wipes the user's queue" — this pattern is the guard, proven by the hand-built pre-V2 decode test. Pairs with **#43** (data-structures) for the value-type modelling and **#52** (`appendingPathComponent` FS-probe) on the persisted-URL side.
