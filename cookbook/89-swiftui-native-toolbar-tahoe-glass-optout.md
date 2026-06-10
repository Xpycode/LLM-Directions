# #89 — Native titlebar toolbar grows Liquid Glass "bubbles" on the macOS 26 SDK → opt out with `UIDesignRequiresCompatibility`

**Extracted from:** Conjoyn (2026-06-10g)

You migrate a macOS app's top bar from a **custom `HStack` titlebar** (the FCP-style "the source bar IS the titlebar" pattern: `.hiddenTitleBar` + a 52 pt view + traffic lights overlaying a hand-tuned leading inset) to a **native SwiftUI `.toolbar { }`** (App Shell Standard: `.toolbar` + `.toolbarRole(.editor)`). The toolbar works — but **every toolbar item now sits in its own translucent rounded capsule** ("bubbles" behind the buttons / path well). The custom bar never had them; sibling apps (Penumbra, CropBatch) don't have them either.

## Why it happens

The capsules are **macOS 26 (Tahoe) Liquid Glass**. The OS auto-enrolls *native* toolbar items into the Liquid Glass treatment — but **only for apps linked against the macOS 26 SDK**. So:

- **Your old custom `HStack` titlebar** never went through the native toolbar machinery → no glass, ever (it just drew your own background).
- **Penumbra / CropBatch** look flat because they were **built against a pre-Tahoe SDK** → not enrolled. *(This is the tell: "but the other apps don't do it" almost always means SDK skew, not a code difference.)*
- **Your app, rebuilt today**, links the macOS 26 SDK → the moment you adopt the native toolbar, the glass kicks in.

When your toolbar items already carry their own backgrounds (a custom path-well rounded-rect, an `FCPToolbarButtonStyle`/`.cjStandard` pill), you get an ugly **double background**: the system glass capsule *behind* your custom chrome.

## The fix — opt the whole app out of Liquid Glass

`UIDesignRequiresCompatibility = true` in the **Info.plist** renders the entire app in the legacy (pre-Tahoe) design language — i.e. identical to the older-SDK sibling apps. It's **app-wide and Info.plist-only**, by design: Liquid Glass is a system-wide rendering opt-in tied to the SDK you link, not a per-view modifier. For an app with a fully bespoke dark theme that never wants glass anywhere, opting out wholesale is the *intended* use, not a hack. (Apple's sanctioned "stay on the old look" escape hatch for the 26 transition.)

## The trap that wastes the most time: you can't inject the key the easy way

With `GENERATE_INFOPLIST_FILE = YES` (the modern default — no physical Info.plist), the obvious move is a build setting:

```yaml
INFOPLIST_KEY_UIDesignRequiresCompatibility: YES   # ← SILENTLY DOES NOTHING
```

**This fails silently.** The `INFOPLIST_KEY_*` mechanism only injects an **allowlist** of Apple-recognized keys (CFBundleDisplayName, NSHumanReadableCopyright, LSApplicationCategoryType, …). `UIDesignRequiresCompatibility` is **not** on it, so the build drops it with no error. Always verify:

```bash
/usr/libexec/PlistBuddy -c "Print :UIDesignRequiresCompatibility" "$APP/Contents/Info.plist"
# → "Does Not Exist"  ← the build setting was ignored
```

### Working fix (keeps GENERATE_INFOPLIST_FILE + all your INFOPLIST_KEY_* settings)

Point `INFOPLIST_FILE` at a **minimal hand-managed base plist holding only the one key**, and keep `GENERATE_INFOPLIST_FILE: YES`. Xcode uses the base file as the seed and **merges the generated/allowlisted keys on top** — you get both.

`project.yml` (xcodegen):
```yaml
settings:
  base:
    GENERATE_INFOPLIST_FILE: YES
    INFOPLIST_FILE: MyApp/Info.plist          # ← minimal base, see below
    INFOPLIST_KEY_CFBundleDisplayName: myapp  # ← still works, merged on top
    INFOPLIST_KEY_LSApplicationCategoryType: "public.app-category.video"
```

`MyApp/Info.plist` (the *entire* file — let Xcode generate everything else):
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>UIDesignRequiresCompatibility</key>
    <true/>
</dict>
</plist>
```

Regenerate, rebuild, **verify the merge** (both keys present proves it worked):
```bash
/usr/libexec/PlistBuddy -c "Print :UIDesignRequiresCompatibility" "$APP/Contents/Info.plist"  # → true
/usr/libexec/PlistBuddy -c "Print :CFBundleDisplayName"             "$APP/Contents/Info.plist"  # → myapp
```

**xcodegen note:** set `INFOPLIST_FILE` as a plain **build setting** (above) so xcodegen leaves your file alone. Do **not** use xcodegen's `info: { path:, properties: }` block here unless you also drop `GENERATE_INFOPLIST_FILE` and move *all* `INFOPLIST_KEY_*` values into `properties` — that block makes xcodegen **own and overwrite** the plist (see #47 gotcha #2), which fights the generate-and-merge approach.

## The migration itself (what to delete)

Going native deletes code rather than adding it — the native toolbar provides for free what the custom bar faked:

- **Remove** the custom `TitleBar` `HStack` (wordmark/tagline included — the window already identifies the app) and the `Spacer().frame(width: 64)` traffic-light inset (AppKit owns that zone under `.toolbarRole(.editor)`).
- **Remove** the `NSViewRepresentable` `WindowConfigurator` that set `titlebarAppearsTransparent` / `titleVisibility = .hidden` / `isMovableByWindowBackground = true` — the native toolbar supplies the window **drag region** itself, and `.hiddenTitleBar` hides the title. (Trade-off: dragging an empty *content* area no longer moves the window — that was `isMovableByWindowBackground`; native behavior is drag-from-toolbar only, which is standard macOS.)
- **Add** `.toolbar { ToolbarItemGroup(placement: .principal) { … }; ToolbarItemGroup(placement: .primaryAction) { … } }` to the root view + `.toolbarRole(.editor)`. `.toolbar` attaches to the window's toolbar on macOS even without a `NavigationStack`.
- **Cleanup tells:** the old bar's background color token (`Theme.titlebar`) is now orphaned — grep for it (only comments should remain) and delete it; refresh now-stale "the source bar IS the titlebar" comments.

## Decision: app-wide opt-out vs. living with glass

There is **no clean public per-item opt-out** for the toolbar glass on macOS 26 — the compat flag is the supported lever and it's all-or-nothing. That's fine when the app's whole aesthetic is bespoke (custom `Theme`, custom buttons, forced dark mode) — glass would clash everywhere, so opting out wholesale is correct and makes you match the older-SDK reference apps exactly. If instead you *want* the native Tahoe look, do the opposite: **drop your custom item backgrounds** and let the glass capsule *be* the background (no double layer).

## Verify without Screen Recording permission

A CLI `screencapture` of your own app often fails (no Screen Recording perm for the shell). You can't see the bubbles yourself — drive a **user eyeball** instead, but make it a *correctness* check by reading the values out of the source first, and confirm the build/plist facts programmatically (PlistBuddy above). The visual "are the capsules gone?" is the only part that needs a human.

Pairs with: #47 (xcodegen Info.plist `properties` vs file-overwrite), #00 (App Shell Standard / `FCPToolbarButtonStyle`), #71 (LSUIElement self-managed window), VAM (the repo's macOS-26-SDK titlebar-injection reference).
