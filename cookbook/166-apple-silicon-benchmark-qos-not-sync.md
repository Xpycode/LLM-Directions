# 166 — Apple Silicon timing needs an explicit QoS, and `DispatchQueue.sync` will not set it

**Tags:** DispatchQoS, DispatchQueue.sync QoS inheritance, userInitiated, background E-core, thread affinity Apple Silicon, P-core E-core migration, benchmark variance, async semaphore, qos_class_self

**Best for:** anything where run-to-run timing consistency matters on Apple Silicon — benchmarks,
latency budgets, profiling a hot path, or diagnosing "the same code is sometimes 25% slower".

**Extracted from:** MacBench (2026-07-25)

---

## The measurement

Identical work (AES-128-CBC over 4 MiB, 7 timed iterations), M1 Max, varying only the QoS of the
thread it ran on. *Dispersion* here = how far the median sits above the fastest sample.

| QoS | dispersion | fastest |
|---|---|---|
| `.userInitiated` | 0.005 – 0.024 | 3.33 ms |
| `.userInteractive` | 0.007 – 0.012 | 3.33 ms |
| **default (inherited)** | 0.010 – **0.256** | 3.34 – **3.69 ms** |
| `.background` | 0.051 – **0.522** | 4.27 ms |

Default QoS is not merely noisier — it is *unpredictably* noisier. The scheduler may move the thread
between performance and efficiency cores mid-run, and any iteration longer than a scheduling quantum
spans several. In the worst trial even the **fastest** sample drifted ~10% high.

This was the single largest measurement-quality factor found in the project — bigger than the choice
of statistic, the iteration count, or the working-set size.

## The trap: `sync` does not apply the queue's QoS

```swift
// WRONG — runs on the CALLING thread, keeps the CALLER's QoS. Silently does nothing.
DispatchQueue.global(qos: .userInitiated).sync { measure() }
```

`sync` executes the block on the current thread as an optimisation, so the queue's QoS never applies.
The code looks like it controls scheduling and does not. Use `async` and wait:

```swift
let box = ResultBox()                       // final class, one write then one read
let semaphore = DispatchSemaphore(value: 0)
DispatchQueue.global(qos: qos).async {
    box.value = measure()
    semaphore.signal()
}
semaphore.wait()
return box.value
```

The semaphore establishes the ordering — exactly one write before `signal()`, one read after
`wait()` — which is what makes `@unchecked Sendable` on the box sound rather than a wish. **Never call
this from the main thread**: it blocks for the whole run.

Allocate buffers *inside* the dispatched block so they are first-touched by the measuring thread.

## Two things not to claim

- **This is QoS, not affinity.** Apple Silicon exposes no thread-to-core pinning API. `.background` is
  *confined* to E-cores by scheduler policy; the others are merely *preferred* on P-cores. Call it an
  "efficiency-core workload", never a pinned measurement.
- **E-core runs need their own thresholds.** `.background` disperses 5–52% by nature — that is where
  the system puts its own work. A quality gate tuned for P-cores will reject every E-core run.

## Incidental, and counter-intuitive

E-cores were only **~1.3× slower** than P-cores at AES (4.27 vs 3.33 ms), because the ARMv8 crypto
units dominate and E-cores have them too. General-purpose integer/FP code shows a far wider split, so
a crypto benchmark is a poor illustration of the P/E difference.
