## Swift 6 Concurrency: @MainActor + @Observable

**Rule:** All `@Observable` model classes that drive UI should be `@MainActor`. Without it, Swift 6 permits mutation from any concurrency context — the compiler can't protect you.

```swift
// WRONG — @Observable alone doesn't enforce main-thread mutation
@Observable
final class AppState { ... }

// CORRECT — compiler enforces all mutation happens on main actor
@MainActor
@Observable
final class AppState { ... }
```

**Why `@Observable` alone isn't enough:** The `@Observable` macro rewrites property access for observation tracking, but it doesn't restrict *which thread* can mutate stored properties. You can race on them from a background Task with no warning in non-strict mode.

**The per-call patch (anti-pattern):**
```swift
// Common workaround — but misses call sites silently
Task { @MainActor in
    self?.isProcessing = false
}
```

Adding `@MainActor` to the class makes this redundant (harmless) and enforces it everywhere automatically. The compiler flags any missing `await` at a call site.

**Impact on async export patterns:** If your `@MainActor` class creates an inner `Task { }`, that Task inherits `@MainActor` isolation. Actual heavy work still runs off-thread when you `await` a `nonisolated` function — the actor is released during the `await`.

**Source:** CropBatch pre-v1.4 review (2026-04-03)

---

