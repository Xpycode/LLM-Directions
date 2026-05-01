# `Decodable`-only types with custom `init(from:)` need explicit `CodingKeys`

**Source:** `1-macOS/_Published/syncthingStatus/` — `Models.swift::RemoteNeedItem` (2026-04-29, v1.6.0).

A struct that conforms to `Decodable` only (not full `Codable`) and provides its own `init(from decoder:)` will **not** get a synthesized `CodingKeys` enum. The compiler error is:

```
error: cannot find 'CodingKeys' in scope
error: generic parameter 'Key' could not be inferred
```

A struct on the same project conforming to full `Codable` with the *exact same shape* compiles fine — that's the head-scratcher.

Fix: declare `CodingKeys` explicitly.

```swift
struct RemoteNeedItem: Decodable, Identifiable, Equatable {
    let name: String
    let deleted: Bool
    let type: String
    let size: Int64

    private enum CodingKeys: String, CodingKey {     // ← required
        case name, deleted, type, size
    }

    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        name = (try? c.decode(String.self, forKey: .name)) ?? ""
        deleted = (try? c.decode(Bool.self, forKey: .deleted)) ?? false
        type = (try? c.decode(String.self, forKey: .type)) ?? ""
        size = (try? c.decode(Int64.self, forKey: .size)) ?? 0
    }
}
```

---

## Why the synthesis rule looks contradictory

Swift's Codable synthesis (SE-0166) only generates a `CodingKeys` enum when it's also synthesizing at least one of `init(from:)` / `encode(to:)`. Two scenarios diverge:

| Conformance | Custom `init(from:)`? | Custom `encode(to:)`? | `CodingKeys` synthesized? |
|---|---|---|---|
| `Codable` (== `Decodable & Encodable`) | yes | no | **yes** — for the still-synthesized `encode(to:)` |
| `Codable` | yes | yes | no |
| `Decodable` only | yes | n/a | **no** — nothing left to synthesize |
| `Decodable` only | no | n/a | yes |
| `Encodable` only | n/a | yes | no |

So the `Codable` form is forgiving (you can hand-roll either side and still reference `CodingKeys`); the `Decodable`-only form bites the moment you write a custom decoder. Same compiler rule, different observable behavior.

---

## When you'll trip on this

- Defensive-decoding wrappers around external API responses where you only ever read, never write — e.g., `RemoteNeedItem`, paginated list responses, anything you fetch from a JSON endpoint.
- Refactoring a `Codable` type to `Decodable` to remove a vestigial `Encodable` requirement (the build breaks the moment the conformance narrows).
- Any type where the property names don't match the JSON keys 1:1 — you needed `CodingKeys` anyway, but on `Codable` the synthesis hid it.

---

## What doesn't work

- **Adding `Encodable` conformance just to get the synthesis** — works, but introduces a fake `encode(to:)` you never call. Worse, if your fields are `let`s with custom decode logic, the synthesized `encode(to:)` may do the wrong thing (encode default values that bypass your decode normalisation).
- **Removing the custom `init(from:)`** — defeats the purpose if you need defensive decoding (`try?` with sane defaults).
- **Letting it compile by typing `decoder.container(keyedBy: <SomeOtherType>.self)`** — only delays the problem.

---

## House-style decoder for evolving APIs

Pair this with `try?` + sane defaults so a future field rename in the upstream API degrades to "missing" rather than a hard crash. Reference: same project's `SyncthingFolderStatus` (full `Codable` with custom `init(from:)`) for the prior-art pattern; the gotcha here only surfaces when you narrow to `Decodable`-only.

---

*Drafted 2026-04-29 from a real compile error in `RemoteNeedItem` while the surrounding `SyncthingFolderStatus` (`Codable`) compiled fine.*
