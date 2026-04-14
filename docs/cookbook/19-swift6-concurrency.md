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

## MainActor init + blocking semaphore = multi-second launch stall

**Signature:** An `@MainActor` class has an `init()` that calls a synchronous method which wraps async work behind `DispatchSemaphore.wait(timeout: N)`. Cold launch time equals N seconds, almost exactly.

**Why it stalls:**
- `@MainActor init` runs on the main thread.
- The sync wrapper spawns `Task { ... }` which inherits `@MainActor` isolation.
- `semaphore.wait()` blocks the main thread.
- The Task needs the main thread to run — it can't.
- `wait()` sits until its timeout fires, then returns fallback/default data.

**Anti-pattern:**
```swift
@MainActor
class ViewModel: ObservableObject {
    @Published var items: [String] = []
    init() { loadItems() }   // ← blocks N seconds every launch

    func loadItems() {
        let semaphore = DispatchSemaphore(value: 0)
        var result: [String] = []
        Task {   // inherits @MainActor — can't run while main is blocked
            result = await Service.getItems()
            semaphore.signal()
        }
        _ = semaphore.wait(timeout: .now() + 5)
        items = result
    }
}
```

**Fix:**
1. Delete the sync wrapper; expose only an `async` API.
2. Remove the work from `init()`.
3. Attach `.task { await viewModel.loadItems() }` to the SwiftUI view that reads the data — ideally the narrowest view that actually needs it, so launch doesn't pay for screens the user hasn't opened.

```swift
@MainActor
class ViewModel: ObservableObject {
    @Published var items: [String] = []
    init() {}   // no work at launch

    func loadItems() async {
        items = await Service.getItems()
    }
}

// In the consuming view:
MyView(items: viewModel.items)
    .task { await viewModel.loadItems() }
```

**Diagnostic shortcut:** When a SwiftUI app has a consistent multi-second launch delay on fast hardware (M-series), grep for `DispatchSemaphore` before reaching for Instruments. The observed delay will equal the `timeout:` value almost exactly — that's the smoking gun.

**Why `.task` over `.onAppear { Task { ... } }`:** `.task` participates in structured concurrency — the view owns the Task and SwiftUI auto-cancels it on disappear. An unstructured `Task {}` inside `.onAppear` leaks if the view unmounts mid-work.

**Source:** NetworkQuality v1.0.2 fix (2026-04-14) — cold launch dropped from 3–5s to ~197ms on M4 Pro.

---

