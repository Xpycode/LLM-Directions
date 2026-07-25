# 165 — An optimiser barrier is not enough: a benchmark kernel must be *irreducible*

**Tags:** blackHole, optimiser barrier, withExtendedLifetime, dead code elimination, induction variable, closed form, benchmark reports 0 ns, Gauss formula, -O whole-module, benchmark body

**Best for:** any hand-written timing loop under `-O`. If a subtest reports an impossibly fast time —
especially **0 ns** — while your barrier is correctly applied, this is why.

**Extracted from:** MacBench (2026-07-25)

**Pairs with:** #124 (benchmark under `-O`, never Debug). #124 gets you to a build where numbers mean
something; this is the trap waiting once you're there.

---

## The standard advice, and why it is incomplete

Everyone knows a benchmark body whose result is unused can be deleted, so you add a barrier:

```swift
@inline(never)
func blackHole<T>(_ value: T) {
    withExtendedLifetime(value) {}
}
```

That is correct and necessary. It is also **not sufficient**, and the failure is silent.

`blackHole` protects the **result**. It says nothing about the **work that produced it**. If the
computation has a closed form, LLVM's induction-variable optimisation replaces the loop with the
formula, hands `blackHole` a perfectly correct value, and the barrier is satisfied — by a value
computed in constant time.

## Observed

```swift
var acc = 0
for i in 0..<50_000 { acc &+= i }
blackHole(acc)                       // barrier applied correctly
```

Measured: **0 ns**. The invocation counter confirmed the closure ran all 9 times (2 warmup +
7 measured), so the *body* executed — but `sum(0..<n)` is Gauss's formula, `n*(n-1)/2`, and the loop
was gone. A benchmark that reports 0 ns is obvious; one that reports 40× too fast is not.

## The fix: a serial dependency chain

Make each iteration consume the previous iteration's output. There is then no closed form to collapse
to, and no instruction-level parallelism to exploit either.

```swift
// Irreducible: xorshift, each step depends on the last.
var x: UInt64 = 0x9E37_79B9_7F4A_7C15
for _ in 0..<200_000 {
    x ^= x << 13
    x ^= x >> 7
    x ^= x << 17
}
blackHole(x)                          // 0.49 ms — a real number
```

Real workloads are usually safe: AES-CBC (block chaining is inherently serial), FFT, `cblas_sgemm`,
compression. **Synthetic filler loops usually are not** — summations, counters, `reduce(+)`, anything
with an arithmetic identity.

## Sanity check for any new kernel

> Scale the iteration count. If the reported time barely moves, the work was optimised away.

Cheap, and it catches partial elimination that a single absolute number never reveals.

## Related trap: the checksum inside the timed region

Returning a checksum from the body is a good barrier payload *and* lets you verify every iteration
computed the same thing. But keep the checksummed region **small** — folding a 4 MiB buffer measures
the fold as much as the kernel. Pick a value that already depends on all the work: with CBC, the final
16-byte block is a function of every preceding block, so 16 bytes verify the whole buffer.
