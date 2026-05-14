<!--
TRIGGERS: @AppStorage, AppStorage, @SceneStorage, @Environment, @FocusState, @FetchRequest, DynamicProperty, ObservableObject, @Observable, @Bindable, UserDefaults, settings reset, model invariant, optimistic UI, pessimistic disk, equatable, UUID equatable, synthesized equatable, implicit action, Xcode 16 synced folders, project.pbxproj surgery, "save activate not firing", "AppStorage on class"
PHASE: implementation, debugging
LOAD: when designing iOS SwiftUI state, debugging "saved value isn't read", or wiring settings/preferences
-->

# iOS SwiftUI State Patterns

*Five state-management patterns that have bit Group Alarms (and likely will bite any iOS SwiftUI project). All trace back to the same root: SwiftUI's property wrappers were designed for `View` lifetimes, but app code reaches for them in classes and silently breaks.*

---

## Pattern 1: `@AppStorage` (and friends) is View-only

This is the cardinal rule. Get this wrong and your "saved" value is silently never read.

### Symptom

Form has a toggle declared as `@AppStorage("autoActivateOnSave") private var autoActivate = true` on a `ViewModel`. User enables the toggle in Settings, hits Save in the form. Behavior doesn't trigger. Logs show the form VM read `autoActivate = false` even though Settings shows `true`.

### Why it happens

`@AppStorage` is a SwiftUI `DynamicProperty`. Its full lifecycle — default registration via `store.register(defaults:)`, `update()` callbacks, dependency tracking — only runs when the wrapper lives inside a `View`, `App`, or `Scene`. On a non-View class (`ObservableObject`, `@Observable`, plain `final class`), the wrapper compiles fine but the value reads are unreliable. The default registration may not have fired, so the read returns `false` for missing-key Bool defaults instead of your declared `true`.

### The rule

| `@AppStorage` is OK in | `@AppStorage` is unsafe in |
|---|---|
| `struct SomeView: View` | `final class SomeViewModel: ObservableObject` |
| `@main struct App` | `@MainActor @Observable final class FooManager` |
| `Scene` | Anywhere outside a SwiftUI lifetime |

Same applies to **all** SwiftUI `DynamicProperty` wrappers — `@SceneStorage`, `@Environment`, `@FocusState`, `@FetchRequest`. None of them work reliably outside View/App/Scene.

### The fix

For ObservableObject reads of UserDefaults, use `UserDefaults.standard` directly:

```swift
@MainActor @Observable final class AlarmGroupFormViewModel {
    // ❌ BROKEN on a class — DynamicProperty lifecycle never runs
    // @AppStorage("autoActivateOnSave") private var autoActivate = true

    // ✓ Correct — direct UserDefaults read with explicit default
    private var autoActivate: Bool {
        UserDefaults.standard.object(forKey: "autoActivateOnSave") as? Bool ?? true
    }
}
```

`object(forKey:)` (returning `Any?`) plus `as? Bool` plus `?? true` is the explicit pattern — `UserDefaults.bool(forKey:)` returns `false` for missing keys with no way to declare a different default, which is the whole reason `@AppStorage` adds the registration step. Replicate that registration manually if your default isn't `false`.

In the **Settings View itself**, keep `@AppStorage` — that's its proper home and the property wrapper works correctly:

```swift
struct SettingsView: View {
    @AppStorage("autoActivateOnSave") private var autoActivate = true  // ✓ inside View
    var body: some View { Toggle("Activate on Save", isOn: $autoActivate) }
}
```

Source: Group Alarms `2026-04-28` (`AlarmGroupFormViewModel` initially used `@AppStorage` on the class; user-reported "save-activate didn't fire"; fix `0ddc592` switched to direct `UserDefaults` read).

---

## Pattern 2: Many-defaults reset — service over duplicate `@AppStorage` declarations

When a settings screen has 20+ `@AppStorage` keys spread across multiple sub-views, you'll need a "Reset to Defaults" action. The wrong reflex: declare every key in a "reset" View just so you can write to them. That duplicates every key declaration, and **every new setting needs you to remember to wire it into the reset path**.

### The pattern

A static service that uses `UserDefaults.standard` (and `UserDefaults(suiteName:)` for App Groups) directly:

```swift
enum SettingsResetService {
    static func resetAll() {
        let standard = UserDefaults.standard
        let appGroup = UserDefaults(suiteName: SharedDataManager.appGroupIdentifier)

        // Standard defaults — keys grouped by category for readability
        for key in [
            "autoActivateOnSave",
            "selectedTheme",
            "soundEnabled",
            // ... rest of the catalog
        ] {
            standard.removeObject(forKey: key)
        }

        // App Group defaults (widget-shared)
        for key in ["defaultSnoozeDuration", "defaultPreAlertDuration"] {
            appGroup?.removeObject(forKey: key)
        }

        // Intentional non-resets — preserve user-created data
        // (don't clear: category names, user-created colors, alarm groups)
    }
}
```

Then `GeneralSettingsView`'s reset button just calls `SettingsResetService.resetAll()`. No 25-key duplicate declarations, no risk of forgetting a key when adding a new setting (the catalog is one source of truth).

### Why this dovetails with Pattern 1

`SettingsResetService` is a non-View enum. If you tried to write it with `@AppStorage` declarations to drive the resets, you'd hit Pattern 1 silently. Going direct to `UserDefaults` sidesteps that trap entirely.

Source: Group Alarms `2026-04-28` plan rewrite, `SettingsResetService.resetAll()`.

---

## Pattern 3: Pessimistic disk, optimistic memory

For state-changing operations that can fail (network call, AlarmKit registration, AVFoundation activation), splitting persistence into two phases gives you both UI snappiness and crash safety.

```
1. UI tap fires action
2. Update memory immediately (UI re-renders, feels instant)
3. Issue underlying operation (AlarmKit.schedule, network call, …)
4. On success: persist `isActive=true` to disk
   On failure: revert memory update, surface error
   On app death between step 2 and step 4: disk still reflects prior state
```

The crash-safety property is the key one: if the app dies after memory update but before disk persistence, the user sees the *prior* state on relaunch — a safe failure mode they can recover from by re-toggling. The opposite arrangement (write disk first, then attempt operation) leaves the user with phantom-on state on relaunch when the operation actually failed.

### When to apply

Any UI action that triggers a fallible underlying operation: alarm activation, push notification registration, audio session activation, cloud sync writes, file I/O. Anything where "the toggle moved" doesn't yet mean "the side effect succeeded."

### When NOT to apply

Pure preference toggles (theme, accent color) — these have no underlying operation that can fail; persist immediately. The pattern is for state with consequences, not state that's just user preference.

Source: Group Alarms `2026-04-28` (alarm activation paths after the AlarmKit / save-activate work).

---

## Pattern 4: Two-gate guard for implicit actions

When the app does something *implicitly* in response to a user action (e.g., "save-activate" auto-activating an alarm group when the user taps Save), there are two failure modes:

1. **The user didn't want that** — they just wanted to save edits, not activate.
2. **The action fires for trivial saves** — a no-op edit (open form, close form without changing anything) shouldn't trigger a side effect.

The two-gate guard:

```swift
// Gate 1: global opt-out from Settings
@AppStorage("autoActivateOnSave") private var shouldAutoActivate = true

// Gate 2: per-action no-op-detection via Equatable snapshot
private let initialSnapshot: AlarmGroupSnapshot

func save() {
    let currentSnapshot = AlarmGroupSnapshot(from: form)
    let hasUserChanges = (currentSnapshot != initialSnapshot)

    persist(form)

    if shouldAutoActivate && hasUserChanges {
        activateGroup(form)
    }
}
```

Both gates have to pass for the implicit action to fire. The `@AppStorage` opt-out lives in Settings (where the wrapper works correctly — Pattern 1). The snapshot diff lives in the form's view model (using `UserDefaults` direct or no preference at all).

The snapshot type is a small Equatable struct that captures the user-visible form fields. Hand-rolled Equatable is needed if you have UUID identifiers (Pattern 5).

Source: Group Alarms `2026-04-28` ("Two-gate guard for implicit actions" — promoted to Vestige `71c27fc4-…`).

---

## Pattern 5: UUID `Equatable` trap

Structs with `let id = UUID()` get synthesized `Equatable` that compares **all** fields including the auto-generated UUID. Two "logically equivalent" instances (same payload, different `id`) compare unequal — surprising when used in `.animation()`, `.id()`, or any diff-based SwiftUI logic.

```swift
// ❌ Synthesized Equatable compares id too — two logically-equal items return false
struct AlarmTimelineItem: Identifiable, Equatable {
    let id = UUID()
    let label: String
    let scheduledFor: Date
}
let a = AlarmTimelineItem(label: "Wake", scheduledFor: .now)
let b = AlarmTimelineItem(label: "Wake", scheduledFor: .now)
a == b  // false — different UUIDs

// ✓ Hand-roll Equatable to compare only the payload
struct AlarmTimelineItem: Identifiable, Equatable {
    let id = UUID()
    let label: String
    let scheduledFor: Date

    static func == (lhs: Self, rhs: Self) -> Bool {
        lhs.label == rhs.label && lhs.scheduledFor == rhs.scheduledFor
    }
}
```

Same trap if you used `let id: UUID` and assigned at init — any two instances with newly-generated UUIDs compare unequal even with identical payloads.

Use cases where this bites:
- Snapshot-diffing for the two-gate guard (Pattern 4) — `currentSnapshot != initialSnapshot` returns `true` for unchanged payloads if you forgot to hand-roll `==`.
- SwiftUI `ForEach` with `.animation(value:)` — diff fires constantly because every render has new UUIDs in the array.

Source: Group Alarms `2026-04-28` (`AlarmTimelineItem` gained hand-rolled Equatable; "synthesized would compare UUID `id` and always return false").

---

## Bonus: Xcode 16 synced folders

Not strictly state, but worth documenting because it inverts a long-standing iOS pain:

> **Xcode 16's synced folders auto-track filesystem changes. Deleting a `.swift` file from the project tree removes it from the build automatically — no `project.pbxproj` surgery required.**

For projects bootstrapped on Xcode 16+, the historical `pbxproj`-corruption-during-merge problem mostly evaporates. You can `git rm` source files and the project keeps building.

**Caveat:** if the project was created on Xcode 14 or earlier and migrated, it may still have the old "group reference" structure where pbxproj still tracks file membership explicitly. Check by inspecting whether folders show with the synced-folder icon in Xcode's navigator, or by the absence of file lists in `project.pbxproj`.

Source: Group Alarms `2026-05-12` (AWAKE extraction — deleted 21 source files via `git mv`/`rm`, no pbxproj edits needed; xcodebuild still passed).

---

## Quick-reference cheatsheet

| Symptom | Pattern | Fix |
|---|---|---|
| `@AppStorage` value reads as Bool default (false) on a non-View class | Pattern 1 | Switch to `UserDefaults.standard.object(forKey:) as? Bool ?? true` |
| `@SceneStorage` / `@Environment` / `@FetchRequest` "doesn't work" outside Views | Pattern 1 | Same — DynamicProperty wrappers are View-only |
| Adding a new setting means editing 3 files (declaration, view, reset) | Pattern 2 | Migrate reset to a `SettingsResetService` enum that touches `UserDefaults` directly |
| App dies mid-save → relaunch shows phantom-on state | Pattern 3 | Persist disk only after the underlying op confirms |
| Implicit action fires on no-op saves | Pattern 4 | Add the snapshot-diff gate alongside the user-opt-out gate |
| `someStruct == otherStruct` returns `false` when payloads are equal | Pattern 5 | Hand-roll `==` to skip the UUID `id` field |
| `git rm`'d a Swift file but Xcode still tries to build it | (legacy project) | Project predates synced folders; manually remove from `project.pbxproj` or migrate the folder reference |

---

## The cross-cutting rule

> **SwiftUI's property wrappers were designed for `View` lifetimes. Any time you reach for `@AppStorage`, `@SceneStorage`, `@Environment`, `@FocusState`, or `@FetchRequest` from a class — pause.** Either move the read into a View (correct usage), or replace with the underlying primitive (`UserDefaults.standard.object`, `EnvironmentValues` passed in via init, etc.).

The pattern shows up because it *looks* like the right tool — `@AppStorage` reads simpler than UserDefaults, and a `ViewModel` "feels" like the right place to read settings. But the wrapper's machinery is silently absent on classes, so you get a default value back when you expected your saved one. The only safe rule is: **wrappers stay in Views.**

---

*Related: `20_swiftui-gotchas.md` (broader SwiftUI pitfalls), `34_testing.md` (snapshot diffing for view-model unit tests), `54_security-rules.md` (when to use Keychain over UserDefaults).*
