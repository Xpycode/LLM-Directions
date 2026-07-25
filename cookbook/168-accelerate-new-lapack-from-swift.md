# 168 — Accelerate's current CBLAS/LAPACK from Swift: `-Xcc -DACCELERATE_NEW_LAPACK`, and never ILP64 by accident

**Tags:** ACCELERATE_NEW_LAPACK, ACCELERATE_LAPACK_ILP64, cblas_sgemm deprecated macOS 13.3, OTHER_SWIFT_FLAGS -Xcc, Accelerate clang importer, BLAS Swift, GCC_PREPROCESSOR_DEFINITIONS, xcodegen settings

**Best for:** calling BLAS/LAPACK (`cblas_sgemm`, `dgemm`, `sgesv`, …) from Swift on macOS 13.3+ and
clearing the deprecation warning without breaking every integer argument.

**Extracted from:** MacBench (2026-07-25)

---

## The warning

```
'cblas_sgemm' was deprecated in macOS 13.3: An updated CBLAS interface supporting ILP64 is
available. Please compile with -DACCELERATE_NEW_LAPACK to access the new headers and
-DACCELERATE_LAPACK_ILP64 for ILP64 support.
```

Apple's message invites you to define **both**. Define only the first.

## Why `-Xcc` and not a plain Swift flag

`ACCELERATE_NEW_LAPACK` is a **C preprocessor** macro consumed by the headers. Swift has no
preprocessor, so it must reach the **clang importer** that builds the Accelerate module for Swift —
hence `-Xcc`. `SWIFT_ACTIVE_COMPILATION_CONDITIONS` cannot do this; it only sets Swift `#if` flags.

```yaml
# project.yml (xcodegen) — target settings.base
OTHER_SWIFT_FLAGS: "$(inherited) -Xcc -DACCELERATE_NEW_LAPACK=1"
GCC_PREPROCESSOR_DEFINITIONS: "$(inherited) ACCELERATE_NEW_LAPACK=1"
```

Keep both lines: the first fixes Swift, the second any C/ObjC in the target. Preserve `$(inherited)`.
Standalone `swiftc` needs the same flag: `swiftc -Xcc -DACCELERATE_NEW_LAPACK=1 …`.

## Why **not** `ACCELERATE_LAPACK_ILP64`

ILP64 widens every BLAS integer argument from 32-bit to 64-bit. Enabling it does **not** produce a
clear error at the call site — it changes what the imported signatures expect, so existing
`Int32(...)` dimension/leading-dimension arguments become wrong. On a `sgemm` that means silently
misinterpreted `M`, `N`, `K`, `lda`. Only enable it if you are deliberately moving to 64-bit indices
and updating every argument.

```swift
import Accelerate

// Correct with NEW_LAPACK and no ILP64: dimensions stay Int32.
cblas_sgemm(
    CblasRowMajor, CblasNoTrans, CblasNoTrans,
    Int32(n), Int32(n), Int32(n),
    1, a, Int32(n),
       b, Int32(n),
    0, c, Int32(n)
)
```

## Verify with an analytic oracle, not just a clean build

The row-major/transpose/alpha/beta arguments are easy to get subtly wrong, and BLAS will happily run at
full speed computing something else. Multiply two k×k **all-ones** matrices: every element of the
product must be exactly `k`, which is exactly representable in `Float`, so this is a true equality
check needing no tolerance.

```swift
let k = 64
let a = [Float](repeating: 1, count: k * k)
let b = [Float](repeating: 1, count: k * k)
var c = [Float](repeating: 0, count: k * k)
cblas_sgemm(CblasRowMajor, CblasNoTrans, CblasNoTrans,
            Int32(k), Int32(k), Int32(k), 1, a, Int32(k), b, Int32(k), 0, &c, Int32(k))
assert(c[0] == Float(k) && c[k * k - 1] == Float(k))
```

## Two facts worth knowing about Accelerate BLAS

- **It multithreads internally**, with no public way to ask it not to. A GEMM timing is therefore a
  *multi-core* figure; labelling it single-core is a misrepresentation.
- **Because it multithreads, results are not guaranteed bit-identical between runs** — the reduction
  may be partitioned differently, changing summation order and the last bits. Compare float output with
  a tolerance (or quantise before hashing); an exact bit comparison produces false failures.
