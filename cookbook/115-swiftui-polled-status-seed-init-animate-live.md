# 115 — SwiftUI polled-status feedback: seed state in `init` (no flash on open), animate only on a live change

**Problem.** A permission / status row reflects something you can only learn by *polling* — e.g.
Accessibility trust (`AXIsProcessTrusted()`), which fires **no** system notification when it flips.
You want two things at once, and the naïve wiring gives you neither cleanly:

1. **On open: show the correct state immediately, with no flash.** If the user already granted, the
   row should be its "granted" state on the very first frame.
2. **While open: a live change should animate** — the reward moment (user grants the permission in
   System Settings and tabs back) should *spring in*, not snap.

The obvious wiring fails both:

```swift
@State private var axTrusted = false                       // ① default is a LIE for granted users
var body: some View { … }
    .onAppear { refreshAX() }                              // runs AFTER the first frame renders

private func refreshAX() {
    withAnimation { axTrusted = CaretLocator.hasAccessibilityPermission() }  // ② animates on OPEN too
}
```

- ① SwiftUI renders the initial `@State` (`false`) **before** `.onAppear` runs, so an already-granted
  user sees **one frame of the wrong (amber "not granted") state** before it flips. Invisible when the
  change is text-only — **glaring** the moment you give the granted state a distinct color / background
  (the whole point of "feedback like other apps do").
- ② Wrapping *every* refresh in `withAnimation` means the row **animates on open** even though nothing
  actually changed — gratuitous, and it cheapens the real grant moment.

**Fix — seed the truth in `init`; animate only when the value genuinely changes.**

```swift
struct WelcomeView: View {
    @State private var axTrusted = false
    @State private var pollTimer: Timer?

    init(hotkeyDisplay: String, onClose: @escaping () -> Void = {}) {
        self.hotkeyDisplay = hotkeyDisplay
        self.onClose = onClose
        // Seed the granted state on first build so an already-granted user never sees a
        // one-frame "not granted" flash before the success state. `_state = State(initialValue:)`
        // is the only way to set @State from init — the first frame is now CORRECT.
        _axTrusted = State(initialValue: CaretLocator.hasAccessibilityPermission())
    }

    private func refreshAX() {
        let trusted = CaretLocator.hasAccessibilityPermission()
        if trusted != axTrusted {
            // A LIVE grant/revoke while the window is open — the reward moment. Animate it.
            // Init already seeded the opening state, so this fires only on a genuine change
            // (poll tick or tab-back-from-Settings), never on open.
            withAnimation(.spring(response: 0.42, dampingFraction: 0.72)) { axTrusted = trusted }
        }
        if trusted { stopPolling() }
    }
}
```

The granted state then reads as a real "done" affordance, and the glyph swap gets free polish from
SF Symbol effects:

```swift
Image(systemName: axTrusted ? "checkmark.shield.fill" : "exclamationmark.shield.fill")
    .foregroundStyle(axTrusted ? success : theme.warning)
    .contentTransition(.symbolEffect(.replace))   // crossfade shield ⇄ check
    .symbolEffect(.bounce, value: axTrusted)        // little celebratory pop on the change
// …row background flips too: .fill(axTrusted ? success.opacity(0.12) : theme.control)
//                            .stroke(axTrusted ? success.opacity(0.55) : theme.hairline)
```

**Why polling at all (and the belt-and-suspenders).** Accessibility-trust has no KVO/Notification
hook, so you sample it. A ~1 s `Timer` started *when the user heads off to grant* (not always-on),
**plus** a `didBecomeActiveNotification` observer to catch the tab-back:

```swift
.onAppear { refreshAX() }
.onReceive(NotificationCenter.default.publisher(for: NSApplication.didBecomeActiveNotification)) { _ in
    refreshAX()                                     // user tabbed back from System Settings
}
private func startPolling() {                        // started by the "Open … Settings" button
    guard pollTimer == nil else { return }
    pollTimer = Timer.scheduledTimer(withTimeInterval: 1.0, repeats: true) { _ in
        Task { @MainActor in refreshAX() }
    }
}
// CaretLocator.hasAccessibilityPermission() == AXIsProcessTrusted() — LIVE, uncached.
```

**Gotchas.**

- **Reused single-instance window (cookbook #71):** the self-managed `NSWindow` is built **once**
  (`if window == nil`, `isReleasedWhenClosed = false`), so `init` runs once and `@State` persists
  across re-opens — `.onAppear` may **not** re-fire on a later show. That's fine here: `init`-seed
  covers the first build, and the `didBecomeActive` observer + poll cover anything that changed since.
  (If you *rebuild* the view each show instead, `init`-seed covers every open on its own.)
- **The "feature looks broken but is correct" trap — stale TCC grant after a rebuild.** During dev
  the row can show **"not granted"** even though System Settings ▸ Privacy ▸ Accessibility lists your
  app **toggled on**. The feedback is *right*: TCC keys the grant on the binary's **code signature**
  (cdhash for ad-hoc/debug), and every rebuild re-signs → the old grant no longer matches the running
  binary → `AXIsProcessTrusted()` is genuinely `false`. Don't "fix" the code. Re-grant (toggle off/on,
  or remove + let the prompt re-add), or build with a **stable Developer ID** signature whose grant
  survives rebuilds. Verify reality before debugging the view.
- **No semantic success token?** Many `Theme`s expose only accent/warning/danger (cookbook #39). A
  local `success` green (`Color(red: 0.22, green: 0.72, blue: 0.43)`) reads as "done" on both light
  and dark control surfaces regardless of the theme's accent hue — keep it local, or promote to a real
  `theme.success` later.

**Best for:** any polled permission/status surface (Accessibility, Screen Recording, Input Monitoring,
Full-Disk, network reachability, login-item state) that must (a) open in the correct state with no
flash and (b) celebrate a live change — onboarding/Welcome screens especially.

Source: Aloft/ClipSmart `Views/WelcomeView.swift` (`init`-seed + animated `refreshAX`, green §0
success callout) + `Utilities/CaretLocator.swift` (`hasAccessibilityPermission` = `AXIsProcessTrusted`),
commit `23ae4b9`. Pairs with **#71** (self-managed `LSUIElement` settings/welcome window — built once,
reused, why `init`-seed beats `onAppear`), **#110** (settings-pane deep-link verify — the "Open
Settings" button this row pairs with), **#73** (verifying AX-driven behavior without Screen Recording),
**#39** (design tokens — the missing semantic `success` color), **#113/#114** (appearance — same live
`effectiveAppearance` discipline). The stale-TCC-after-rebuild gotcha also bites any AX/synthetic-paste
work (Aloft's signing notes).
