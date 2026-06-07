# 82 — A key panel that synth-pastes into another app must reactivate its target

**Problem.** A borderless overlay/launcher panel (a clipboard picker, a snippet palette, a command bar) **needs to be the key window** so it can host a search field and keyboard navigation. The user picks an item → you write the pasteboard → close the panel → synthesize ⌘V into "the frontmost app." It works most of the time, but **intermittently nothing pastes** — and it's most visible when the target is **Finder** (the file lands sometimes, not others), or any app whose window visibly deactivates when your panel appears.

This is the **mirror image of #81**. #81 is a HUD that must *never* take key. This is a panel that *must* take key — and that's exactly what breaks the paste.

---

## Why a non-activating panel can still leave YOUR app frontmost

You summon the panel with the usual non-activating recipe, then make it key so the search field accepts typing:

```swift
panel.orderFrontRegardless()
panel.makeKey()                 // ← required: the search field / key-nav needs key status
```

`makeKey()` on a `.nonactivatingPanel` is documented as not activating your app — but in practice, combined with `orderFrontRegardless()` and depending on how you were summoned (global hotkey, a click), **your app can become the frontmost application anyway**. So by the time the paste fires:

```swift
AppDelegate.shared?.closeOverlay()
DispatchQueue.main.async { _ = AutoPasteService.paste() }
```

`NSWorkspace.shared.frontmostApplication` returns **your own bundle id**, and the paste service's self-guard correctly refuses:

```
REFUSED wouldPasteIntoSelf (frontmost=com.yourapp)   // pasteboard was perfect; nothing lands
```

The guard is right — it *can't* know which app should have received the paste. The bug is that you threw away that knowledge when the panel grabbed focus.

**Why it looks app-specific (but isn't):** text pastes into a text field often survive because focus happens to stay; **Finder windows visibly deactivate**, so the refusal is reliably reproducible there. The root cause is general — it can silently drop text pastes too.

---

## Fix — capture the summon-time target, fall back to reactivating it

Two pieces. **(1)** At summon, remember who was frontmost *before* your panel took over (a value, captured once):

```swift
private(set) var pasteTargetApp: NSRunningApplication?

func showOverlay() {
    if let front = NSWorkspace.shared.frontmostApplication,
       front.bundleIdentifier != Bundle.main.bundleIdentifier {
        pasteTargetApp = front          // the real target, captured before makeKey() steals focus
    }
    panel.orderFrontRegardless()
    panel.makeKey()
}
```

**(2)** A **fallback ladder** at the commit site: try the fast plain `paste()` first (zero added latency for the common case where focus stayed), and *only* when it refuses on self do you hand focus back to the captured target and re-post ⌘V:

```swift
private func pasteOrReactivate(_ target: NSRunningApplication?) {
    if AutoPasteService.paste() == .wouldPasteIntoSelf, let target {
        _ = AutoPasteService.paste(reactivating: target)
    }
}
// commit paths:  ... ; closeOverlay(); DispatchQueue.main.async { pasteOrReactivate(target) }
```

The reactivating path activates the target, waits for it to come up front, **re-checks secure input** (it's app-scoped — a target like Terminal re-enables it on regaining focus), then posts ⌘V:

```swift
static func paste(reactivating target: NSRunningApplication) -> Refusal? {
    guard AXIsProcessTrusted(), !IsSecureEventInputEnabled() else { return /* refusal */ }
    guard target.bundleIdentifier != Bundle.main.bundleIdentifier, !target.isTerminated else { return /* refusal */ }
    target.activate()
    DispatchQueue.main.asyncAfter(deadline: .now() + 0.12) {
        guard !IsSecureEventInputEnabled() else { return }   // re-check AFTER reactivation
        postPasteKeystroke()
    }
    return nil
}
```

---

## Why the ladder, not "always reactivate"

You *could* route every paste through `paste(reactivating:)`. Don't — it adds `activate()` + a ~0.12 s settle to **every** paste and re-introduces the post-Sonoma *activate-is-a-request* behavior the non-activating panel was designed to dodge. The ladder keeps the tuned zero-delay path for the 80 % case and pays the reactivation cost only when your own `makeKey()` actually stole frontmost. The same `pasteTargetApp` also serves the **right-click context-menu** paste path, where opening the menu *always* activates you (so that path skips straight to `reactivating:`).

---

## Two cautions for the captured target

- **Capture an `NSImage`/value, not the live `NSRunningApplication`, if you need its icon/name for UI** — `NSWorkspace.frontmostApplication` is autoreleased and a `weak` ref zeroes almost instantly (see #nsrunningapplication-weak-zeroes). For *reactivation* you do hold the `NSRunningApplication` strongly; guard `!isTerminated` before `activate()`.
- **Verify in a unified-log-blind env by appending to `/tmp`** — sandboxed/agent apps often can't read their own `os.Logger` output live; a 6-line `FileHandle` append to `/tmp/foo.log` at each decision point (frontmost bundle id, refusal reason, pasteboard types) gives ground truth in minutes. Remove before merge.

---

**Pairs with** #81 (the non-key HUD sibling — same synthetic-paste stack, opposite focus requirement), #65 (cursor-anchored non-activating panel), #08 (keyboard/event synthesis). Memories: `secure-input-recheck-after-reactivation`, `nsrunningapplication-weak-zeroes`, `hud-panel-must-be-non-key`.

**One-line tell:** *a key picker panel that pastes elsewhere will refuse `wouldPasteIntoSelf` whenever `makeKey()` left it frontmost — capture the summon-time target and fall back to reactivating it.*
