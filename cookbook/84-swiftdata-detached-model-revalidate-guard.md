# 84 — A row-level closure that re-runs on a deleted `@Model` must guard `modelContext != nil`

**Problem.** A SwiftUI list of SwiftData `@Model` rows. A per-row closure — `.task(id:)`, `.onReceive(...)`, `.onChange`, an `onAppear` async — reads one of the row's **persisted properties** (`item.imageData`, `item.fileURL`, `item.tags`, …). Most of the time it's fine. Then, seemingly at random — after a **Clear All**, a **cap-trim**, or any bulk delete, and often triggered by an *unrelated* action like copying a new item — the app **hard-crashes**:

```
EXC_BREAKPOINT (SIGTRAP)
libswiftCore  _assertionFailure(_:_:file:line:flags:)
SwiftData     <internal>
YourApp       ClipboardItem.imageData.getter        ← reading a persisted property
YourApp       Row.revalidate()                       ← your per-row closure
YourApp       closure in Row.body.getter
```

No stack frame in *your* logic looks wrong. The getter itself traps.

---

## Why a deleted model is still in your view tree

SwiftData sets a model's `modelContext` to **nil** the moment it's deleted **and saved**. But SwiftUI's view identity does **not** disappear at the same instant — there's a window where:

1. You delete N rows (`context.delete` + save) → their `@Model` objects are now **detached** (context == nil).
2. SwiftUI hasn't yet re-diffed the list, so the deleted rows **still exist in the view tree**.
3. Something fires every row's closure during that window — a `.task(id:)` re-eval, or (the reliable reproducer) a **broadcast notification** every row is subscribed to:

```swift
.onReceive(NotificationCenter.default.publisher(for: .myOverlayDidShow)) { _ in
    Task { await revalidate() }        // fires for EVERY row, including the just-deleted ones
}
```

4. `revalidate()` reads `item.imageData` — a persisted property on a detached model — and SwiftData's getter **`precondition`s that the model is alive**. It isn't → `_assertionFailure` → `EXC_BREAKPOINT`.

**The root mismatch:** *view-identity lifecycle outlives `@Model` lifecycle.* `.task(id:)` / `.onReceive` are bound to the view's identity, which lingers; the data they touch is bound to the model's context, which is already gone. A broadcast notification widens the window from "unlucky" to "every time the panel reopens after a delete."

**Why it looks like the new feature's fault:** the closure is usually *recently added* (a staleness re-check, a thumbnail refresh, a live badge). The feature that needs to re-read the row on every reopen is exactly the feature that re-reads a *deleted* row on every reopen. The capture/skip logic that "caused" it is often a red herring — the crash is in re-validation, not in the triggering action.

---

## Fix — one early guard, before any persisted read

`modelContext == nil` is SwiftData's canonical "this model is deleted/detached" signal. Bail on it **before touching any persisted property**:

```swift
@MainActor
private func revalidate() async {
    // .myOverlayDidShow fires this for EVERY row, including rows whose @Model was just
    // deleted/cap-trimmed but still linger in the view tree. Reading a persisted property
    // (imageData / fileURL) on a detached @Model traps in _assertionFailure (EXC_BREAKPOINT).
    guard item.modelContext != nil else { return }     // ← the whole fix

    switch item.contentType {
    case .image where item.imageData == nil:           // safe now: model is alive
        ...
    case .file:
        let info = await loadInfo(for: item.fileURL)    // safe now
        ...
    }
}
```

One line. It must be **first** — note the crash here was in the `case .image where item.imageData == nil` *pattern match*, which evaluates `imageData` before any case body runs. A guard placed inside a case is too late.

The same guard belongs on **every** row-level reader of a persisted property — context menus that read `item.tags`, `@ViewBuilder` branches that switch on persisted state, etc. Treat `guard item.modelContext != nil` as the **mandatory preamble** for any row closure that outlives a single render pass:

```swift
// context menu built in the row body — re-evaluated on disappearing rows after a bulk delete
if item.modelContext != nil, !item.tags.isEmpty {     // tags.getter would trap without this
    Menu("Remove Tag") { ... }
}
```

---

## Why not the obvious alternatives

- **`@Query` instead of a passed-in `[Model]`.** The real cure — `@Query` hands the view only live results and dissolves this class of bug — but it's a structural migration (the view must own the fetch). The `modelContext != nil` guard is the **local, zero-risk** mitigation you apply *now*; schedule the `@Query` move separately.
- **Snapshot the value into the struct.** Copying `imageData`/`fileURL` into a plain `let` at row-init avoids the live read — but you *want* the live read here (the whole point is to re-validate current filesystem/state on reopen). Snapshotting defeats the feature.
- **Catch / `try?` the access.** You can't — it's a `precondition` trap (`EXC_BREAKPOINT`), not a Swift `throw`. There is nothing to catch. Prevention is the only option.
- **Unsubscribe deleted rows from the notification.** You don't get a clean "I'm about to be removed" hook before the broadcast fires; the row is still subscribed during the danger window. Guarding the read is simpler and complete.

---

## Verifying it's *this* bug (not a different `EXC_BREAKPOINT`)

A `SIGTRAP` is any Swift runtime trap (force-unwrap, OOB, `fatalError`). It's **this** one when the crash report's faulting thread shows **`<YourModel>.<property>.getter` → `SwiftData` → `_assertionFailure`** with one of *your* row closures just below. Pull it without Xcode:

```bash
ls -t ~/Library/Logs/DiagnosticReports/*.ips | head -1   # newest crash
# parse the .ips (header json line + body json): find the triggered thread,
# look for "<Model>.<prop>.getter" directly under a SwiftData frame.
```

If the getter is the faulting frame, you have a detached-model read — add the guard.

---

**Pairs with** the broader "SwiftData `@ViewBuilder` footgun" family — any persisted read in a view that SwiftUI may re-evaluate on a deleted row. Reach for `@Query` when you can; guard `modelContext != nil` everywhere you can't yet.

**One-line tell:** *crash report shows `<Model>.<prop>.getter → SwiftData → _assertionFailure` under one of your row closures, reproducible by deleting rows then triggering a per-row re-eval (a broadcast notification is the classic widener) → the row's `@Model` is detached; `guard item.modelContext != nil` before any persisted read.*
