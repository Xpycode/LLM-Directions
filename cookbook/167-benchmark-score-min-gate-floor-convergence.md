# 167 — Score a timing run by its **minimum**; gate trust on **floor convergence**, not dispersion

**Tags:** benchmark minimum vs median, one-sided timing noise, floor convergence, dispersion gate, ratio scoring, geometric mean, calibration reference time, discard first sample, uniform contamination

**Best for:** deciding what single number represents N timed samples, and how to know when not to
trust it. Applies to any benchmark that compares a measured time against a stored reference.

**Extracted from:** MacBench (2026-07-25)

**Pairs with:** #165 (make the kernel irreducible first) and #166 (control QoS, or none of this helps).

---

## Take the minimum

Timing noise is **one-sided**. An interrupt, a scheduler migration, or a background daemon can only
make a run *slower*; nothing makes it faster than the silicon allows. Model a sample as
`true + noise, noise >= 0` and the fastest run is the best estimate of true capability — and it
improves as samples accumulate, which neither mean nor median does.

**The decisive argument, if you score by ratio.** A score of `reference ÷ measured`, with the reference
captured on a *quiesced* machine, must compare like with like. Min-against-min compares two estimates
of the same noise-free floor. Median-against-median divides a **quiet** median by a **noisy** one and
systematically penalises any user who had a browser open. That asymmetry does not exist for the
minimum. This is not a taste call — it follows from the scoring scheme.

Taking the min also settles "should I discard the first measured sample?" — no need, a slow first run
is ignored automatically.

## Do not gate on dispersion

The obvious quality gate is "median vs min" (how busy the machine was). Measured, it **rejects good
scores**:

| Run | samples (ms) | min | dispersion | verdict |
|---|---|---|---|---|
| contaminated | 3.347 … 4.560 | **3.347** | 0.130 | min matched the cleanest runs to 0.5% |
| clean | 3.331 … 3.470 | 3.331 | 0.005 | — |

13% dispersion, perfect score. A min-based score is largely immune to a slow tail, so dispersion
answers a question you did not ask.

## Gate on floor convergence

Ask what the minimum actually needs: **did at least two independent samples agree on the floor**, or is
it one lucky outlier?

```swift
/// (2nd fastest − fastest) / fastest. `.infinity` below 2 samples: one measurement
/// cannot corroborate a floor, and treating that as convergence is exactly backwards.
var floorConvergence: Double {
    guard samples.count >= 2 else { return .infinity }
    let sorted = samples.sorted()
    guard sorted[0] > 0 else { return .infinity }
    return Double(sorted[1] - sorted[0]) / Double(sorted[0])
}

var isTrustworthy: Bool {
    !validation.isFailure                       // wrong output ⇒ timing is meaningless
        && !samples.isEmpty                     // empty set has dispersion 0 — would sail through
        && floorConvergence <= 0.02             // primary gate
        && dispersion <= 0.25                   // catastrophe backstop only
}
```

Keep dispersion as a **loose** backstop: at 26% (seen with uncontrolled QoS) the floor genuinely had
drifted ~10% high. Report it as a diagnostic — "how busy the machine was" — not as the gate.

**Do not tune the threshold until your dev machine stops failing.** That is fitting the limit to a
noisy machine. Derive it on the quiesced reference machine.

## The blind spot — document it, do not pretend

**Uniform contamination is undetectable from inside a single run.** If all samples are 4% slow they
agree with each other, so *every* statistic reports a clean run on a floor that is simply wrong.
Observed: a multithreaded GEMM whose min wandered 5% between runs while each run looked internally
tight. There is no in-run reference to compare against, so no statistic can fix it. The only defences
are external: calibrate on a quiesced machine, and distrust a lone anomalous result.

## Corollary: multithreaded kernels need longer iterations

A single-threaded test needs one core free; a multithreaded one needs **every** core free for its whole
duration, so the same hiccup hurts it far more. A 1.2 ms GEMM failed convergence in 3 runs of 5 while
single-threaded AES held its floor to 0.2%. Raising the kernel 8× (1.2 → 10 ms) fixed it with
**identical throughput** — proof it was a stability fix, not a different measurement. Lengthen the
iteration; do not loosen the gate.

## Failed subtests are excluded, never zero

If a composite is a geometric mean of ratios, an untrustworthy subtest must be **dropped from the
product**. Scoring it as zero annihilates the whole composite.
