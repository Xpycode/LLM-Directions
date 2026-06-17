# 120 — Add a memory-hard KDF (Scrypt/PBKDF2) via swift-crypto — verify the PR actually shipped, and never mix `import CryptoKit` with `import Crypto`

**Best for:** wiring a password-stretching KDF (Scrypt or PBKDF2) into a macOS app — a password
manager's `VaultCrypto`, an encrypted store, anything that derives an AES key from a passphrase. Two
traps bite before you write a single line of real crypto: (1) depending on an API that was *proposed*
but never merged, and (2) the silent type-identity clash between Apple's **system** `CryptoKit` and the
**swift-crypto SPM package**.

**Discovered in:** Passwordy (v1 KDF selection + Wave 1 scaffold). The spec confidently cited
swift-crypto `KDF.Argon2id` "landed via PR #427" as the primary KDF. On verification the PR was still
**OPEN** — Argon2id is not in any release. Pivoted to Scrypt, and immediately hit the second trap when
the crypto core mixed `import CryptoKit` (for AES-GCM) with `_CryptoExtras` (for Scrypt).

---

## Trap 1 — a cited PR number is a *proposal*, not a shipped API

A spec/issue/ticket that says "use `KDF.Argon2id` (PR #427)" is a landmine. PRs sit open for years.
**Verify against the release tree before you design around it**, not after the build fails:

```bash
gh pr view 427 --repo apple/swift-crypto --json state,mergedAt      # → "state":"OPEN", mergedAt:null
gh release view --repo apple/swift-crypto --json tagName            # → latest tag (e.g. 4.5.0)
# Does the API's source file exist in the latest tag? (404 = not shipped)
gh api 'repos/apple/swift-crypto/git/trees/main?recursive=1' \
  --jq '.tree[].path | select(test("Argon|Scrypt|PBKDF"; "i"))'
```

Result for swift-crypto (as of 4.5.0): the `Key Derivation` tree contains **only** `HKDF`, `PBKDF2`,
and `Scrypt`. **No Argon2.** A repo-wide code search for "Argon2" returns zero hits. The rule:
*the existence of a PR proves someone wanted the feature, not that you can `import` it.* Confirm the
symbol is in a **tagged release**, then pin to that tag.

## Trap 2 — `CryptoKit.SymmetricKey` ≠ `Crypto.SymmetricKey` (the type-identity clash)

swift-crypto's `Crypto` module is a **source-compatible re-implementation** of Apple's system
`CryptoKit` — same API shapes (`AES.GCM`, `SymmetricKey`, `HKDF`), **different types**. The KDF
extras (`KDF.Scrypt`, `KDF.Insecure.PBKDF2`) live in the package's `_CryptoExtras` and return a
**`Crypto.SymmetricKey`**. If you reach for AES-GCM via the *system* framework:

```swift
import CryptoKit          // ← system framework: AES.GCM, CryptoKit.SymmetricKey
import _CryptoExtras      // ← package extras: KDF.Scrypt → Crypto.SymmetricKey

let key = try KDF.Scrypt.deriveKey(...)          // Crypto.SymmetricKey
let box = try AES.GCM.seal(data, using: key)     // AES.GCM here is CryptoKit's → wants CryptoKit.SymmetricKey
// error: cannot convert value of type 'Crypto.SymmetricKey' to expected argument type 'SymmetricKey'
```

The diagnostic is maddening because **both types are literally named `SymmetricKey`** — the compiler
prints `'Crypto.SymmetricKey'` vs `'SymmetricKey'` and it reads like a compiler bug. It isn't.

**Fix — pick ONE crypto provider for the whole module. Use the package for everything:**

```swift
import Crypto             // AES.GCM + SymmetricKey, ALL from swift-crypto
import _CryptoExtras      // KDF.Scrypt / KDF.Insecure.PBKDF2
// NO `import CryptoKit` anywhere in this file.
```

Now `KDF.Scrypt.deriveKey` returns the same `SymmetricKey` that `AES.GCM.seal` consumes. swift-crypto's
`Crypto` mirrors CryptoKit's AES-GCM surface exactly, so you lose nothing by dropping the system import.
(Going the other way — system `CryptoKit` for the cipher + a *separate* Argon2/scrypt C lib — is the
same clash with extra audit surface; don't.)

## The exact Scrypt API (verified against source — labels are NOT N/r/p)

```swift
import Crypto
import _CryptoExtras      // KDF.Scrypt lives here (swift-crypto package, ≥ 4.0.0)

func deriveVaultKey(password: Data, salt: Data) throws -> SymmetricKey {
    try KDF.Scrypt.deriveKey(
        from: password,        // any DataProtocol (Data / [UInt8])
        salt: salt,            // 16 random bytes
        outputByteCount: 32,   // 256-bit key for AES-256-GCM
        rounds: 1 << 18,       // N (cost) — MUST be a power of 2; 2^18 ≈ 256 MB at r=8
        blockSize: 8,          // r
        parallelism: 1         // p
        // maxMemory: nil      // omit → package computes the cap from N/r/p
    )                          // returns SymmetricKey; THROWS — fail closed, never `try!`
}
```

Gotchas inside the call: the labels are **`rounds`/`blockSize`/`parallelism`**, not `N`/`r`/`p`.
`rounds` **must be a power of 2** → write `1 << 18`, never a literal like `262000`. Scrypt memory ≈
`128 · N · r` bytes (so N=2¹⁸, r=8 ≈ 256 MB). `deriveKey` **throws** — propagate it; a KDF failure in a
security path must fail closed. (`SymmetricKey(data:)` does *not* validate length and does *not* throw —
enforce `key.bitCount == 256` yourself.)

## xcodegen wiring (the part that makes the import work)

```yaml
packages:
  SwiftCrypto:
    url: https://github.com/apple/swift-crypto
    from: "4.0.0"            # Scrypt landed in 4.0.0 — pinning 3.x compiles then can't find KDF.Scrypt
targets:
  YourApp:
    dependencies:
      - package: SwiftCrypto
        product: Crypto
      - package: SwiftCrypto
        product: _CryptoExtras   # the KDF extras product — without it, KDF.Scrypt is "not in scope"
```

After editing `project.yml`, re-run `xcodegen generate`. The first build will throw SourceKit
false-positives (`No such module 'Crypto'`, `Cannot find 'KDF' in scope`) until the index warms —
`xcodebuild` is the source of truth (see #47). `_CryptoExtras` is a real, linkable `.library` product
(verify in the resolved `checkouts/swift-crypto/Package.swift` if it ever fails to link).

## Tells

- "Cannot convert `Crypto.SymmetricKey` to `SymmetricKey`" with two same-named types → you have BOTH
  `import CryptoKit` and `import Crypto`/`_CryptoExtras` in scope. Drop the system import.
- "Cannot find `KDF` in scope" but `import Crypto` is present → you forgot `import _CryptoExtras` (KDF
  extras live there, not in core `Crypto`).
- A spec/teammate cites a KDF/cipher "from PR #N" → `gh pr view N` before you build on it.

Pairs with **#47** (xcodegen SPM setup + SourceKit-false-positive discipline), **#00** (App Shell
Standard for the host app), **#58** (xcodegen resource/script gotchas). Security-rule companion:
`54_security-rules.md` (never log key material; `memset_s` the password/key buffers — a `final class`
with `deinit{ wipe() }`, never a COW `struct`; `String` is unwipeable).
