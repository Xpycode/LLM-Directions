# 108 — Consolidate per-app Feedback/Donate/About menu wiring into one shared SPM `Commands` — and migrate the *source* app first to harden the package (proving-ground)

**Extracted from:** Conjoyn × AppCitizenshipKit (2026-06-14)

You have several apps that each **hand-assemble** the same "app citizenship" menu surfaces — a `FeedbackCommands` (from a feedback SPM, #102), a hand-rolled `DonateCommands`, divider-only groups to flank them (#104), maybe a custom About. You package the common shape behind one config (`AppCitizenshipKit`: `CitizenshipCommands(config)` → Feedback + Tip Jar + About in one line) and now want to adopt it. **Which app do you integrate first, and what does "integrate" actually cost?**

The counter-intuitive answer: integrate the **app the patterns were extracted from first** — even though it already has all the surfaces (so it's a *migration*, not fresh wiring, with a noisier diff). That app is the **proving ground**: it already encodes the polish the package must reproduce, so wiring the package back into it surfaces every gap between "what the package ships" and "what the reference app already does" — *before* any greenfield app consumes the package and inherits the gaps.

## What the migration replaces

```swift
// BEFORE — hand-assembled, ~3 Commands + 2 dividers + a dead struct
.commands {
    HelpMenuCommands(content: helpContent, appName: "Conjoyn")   // vendored Help — stays (not wrapped)
    CommandGroup(after: .help) { Divider() }                     // Help | Feedback divider
    FeedbackCommands(config: feedbackConfig)                     // FeedbackKit, direct dep
    DonateCommands()                                             // hand-rolled: Divider() + "Donate" button
    UpdaterCommands(updater: updaterController)                  // Sparkle — stays
}

// AFTER — one line for Feedback + Tip Jar + About
.commands {
    HelpMenuCommands(content: helpContent, appName: "Conjoyn")
    CommandGroup(after: .help) { Divider() }                     // Help | Feedback divider — STILL host-owned
    CitizenshipCommands(citizenship)                             // ← Feedback + Tip Jar + About
    UpdaterCommands(updater: updaterController)
}
// import FeedbackKit → import AppCitizenshipKit; delete the dead DonateCommands struct;
// citizenship = CitizenshipConfig(appID:"conjoyn", appName:"Conjoyn", accent:…, websiteURL:…, privacyURL:…, logProvider:…)
```

## The load-bearing technical finding: a nested `Commands` can't be split from outside

#104 says same-anchor `CommandGroup(after:)` groups order by **declaration order**, so you place a divider by declaring a divider-only group between two siblings. **That breaks down the moment the two siblings are emitted *inside* a nested `Commands` struct.** `CitizenshipCommands.body` emits Feedback then the Tip-Jar group, both `after: .help`. Any standalone `CommandGroup(after: .help) { Divider() }` you declare in the *host* `.commands` lands either before or after the whole `CitizenshipCommands`, never *between* its two internal items — you have no declaration-order handle on items the package emits internally.

**Consequence:** the Feedback ↔ Tip-Jar separator **must be emitted by the package itself** (a leading `Divider()` inside its donate group). The host can only own the dividers that flank package boundaries it controls (here: Help | Feedback, because Help and the package are two separate top-level entries). So adopting the package *as-is* — when it shipped divider-free — would **regress** the #104 polish the reference app already had. That regression is invisible at the call site; you only see it by reading the live menu.

## Why "migrate the source app" pays for itself: three defects caught before any 2nd consumer

The package was generalized from this exact app, so the migration is a differential test. It surfaced three things the package shipped wrong, each fixed **up in the package** (re-tagged), not patched in the app:

1. **An ellipsis the package's own cookbook forbids.** The shared donate item shipped as `"Support <App>…"` — but #104 (extracted from this same app) says *no ellipsis* for a browser hand-off (ellipsis ⇒ needs further in-app input). The package contradicted its own rule. → drop the ellipsis.
2. **The missing internal divider** (above) → package emits its own leading `Divider()`.
3. **A naming collision.** `"Support <App>"` reads as a help-desk word and **collided with the web side's** "Support" page (the user-help meaning; the web nav had the same ambiguity, #105). `"Donate"` reads as charity/begging. → **tip-jar framing: menu = "Leave a Tip", compact About link = "Tip Jar".** It's the macOS-indie idiom for "optional money, no pressure," and it agrees with the Ko-fi-style backend (#100). The label lives in the package, so the decision propagates to every future app at once.

Fixing in the package (0.1.1: ellipsis + divider; 0.1.2: doc comments) means consumer #2..N inherit the corrected version for free. Patching it in the app would have left the package wrong and let the next adopter re-discover all three.

## Mechanics & gotchas

- **Dev loop without premature publish.** Consume the package via a **local `path:`** dep first (`path: ../../../zPackages/AppCitizenshipKit`), iterate the package + app together, prove the live menu, *then* tag the package on GitHub and flip the app to `url / from: "x.y.z"`. SPM resolves versions from **git tags**, not branches (#102) — `git push origin 0.1.1` or resolution 404s. Verify the flip resolved the right commit: `git -C <DerivedData>/SourcePackages/checkouts/<Pkg> rev-parse HEAD` == the tag's commit (a checkout may lack the new tag ref locally and `describe` as `x.y.(z-1)-N-g…` while sitting on the right commit — trust the commit, not describe).
- **Drop the now-transitive direct dep.** The umbrella package re-exports the feedback package, so the app's *direct* FeedbackKit dep + `import FeedbackKit` become redundant → `import AppCitizenshipKit` instead. **Grep for other usages first** (`FeedbackConfig`/`FeedbackCommands` elsewhere) before removing the package edge; SPM dedupes the transitive copy by URL so versions can differ harmlessly (`from: 0.1.2` in the umbrella, app had `0.1.3` → resolves to the higher).
- **`replacing: .appInfo` coexists with `after: .appInfo`.** The package's link-rich About replaces the stock About item; an existing Sparkle `"Check for Updates…"` declared `after: .appInfo` still renders right below it — the anchor survives the replace. Verify live (it's a plausible conflict).
- **Verify the MENU, not the build.** `Commands` structs have no headless unit test (SwiftUI exposes no way to assert menu text), so a green build proves nothing about the menu. Read the **live** menu via AppleScript/System Events — `missing value` between items = a separator:
  ```bash
  osascript -e 'tell application "System Events" to tell process "Conjoyn" to get name of every menu item of menu 1 of menu bar item "Help" of menu bar 1'
  # → Send Feedback… | missing value | Leave a Tip   (divider present, no ellipsis on the tip item)
  ```
  An unsigned `CODE_SIGNING_ALLOWED=NO` build launches locally on the dev Mac, enough to drive the menu — useful when this Mac lacks the signing cert (a multi-Mac gap, orthogonal to the change).
- **Strict-concurrency bridge carries verbatim.** The feedback log hook (`logProvider: @Sendable () -> String?` + `MainActor.assumeIsolated { Logger.shared.recentTail(80) }`, #102) moves unchanged from `FeedbackConfig` into the umbrella's `CitizenshipConfig` — no new `Sendable` plumbing under Swift 6 complete checking.
- **Comment rot after a label rename.** Renaming the user-facing label leaves doc comments *quoting* the old label ("Support Conjoyn", "Support <App>…") silently lying — the compiler can't catch a comment. **Grep the OLD term after any rename, including `//`/`///` lines** (it's easy to exclude comments from the sweep and miss exactly these). For a **shared package read as the portfolio template**, a comment-only fix still warrants a release (0.1.2) — the published artifact's comments are part of its teaching surface.
- **About links forward-looking.** Pass `websiteURL`/`privacyURL` at the canonical portal even if the per-app marketing site isn't deployed yet — harmless (the links just resolve once it ships), and feedback/tip-jar already point at that live host.

## Multi-Mac: the cookbook index is a shared central file

`/cookbook` adds from *many* projects all write `PATTERNS-COOKBOOK.md` + `cookbook/NNN-*.md` in one central repo, so two Macs/sessions routinely pick the **same next number** independently. **Fetch before adding** (Rule 1, `37_multi-mac-discipline.md`); on `ahead+behind` with a duplicate number, the **published entry keeps its number, the unpushed one yields** (renumber file + H1 + index row). Don't push while diverged. (Real instance: two #106s — one unpushed local, one already on origin — reconciled by renumbering the local one to #107.)

**Rules:** (1) Integrate a shared menu/UI package into the **app its patterns came from first** — the migration is a differential test that hardens the package before any greenfield consumer. (2) A divider/separator **between two items a nested `Commands` emits internally must be emitted by that package** — the host has no declaration-order handle on it. (3) Fix defects the integration surfaces **up in the package + re-tag**, never patched per-app. (4) Verify the **live menu** (AppleScript), not the build — `Commands` aren't unit-testable. (5) After any user-facing label rename, **grep the old term including comments**; for a shared package, ship the comment fix as a release. (6) Tip-jar framing ("Leave a Tip"/"Tip Jar") beats "Donate" (charity) and "Support" (help-desk collision). (7) Local `path:` dep to iterate, flip to `url/from:` tag to ship.

Source: Conjoyn `01_Project/Conjoyn/ConjoynApp.swift` (migration) + `zPackages/AppCitizenshipKit` `CitizenshipCommands`/`CitizenshipConfig`/`CitizenshipAbout` (0.1.0 → 0.1.2 hardening). Pairs with **#104 (the divider/declaration-order rules this generalizes — and the ellipsis rule the package violated)**, **#102 (the feedback SPM the umbrella re-exports — sibling "Send Feedback…" surface)**, **#100 (the `donate.html?app=` tip-jar hub the About/menu link targets)**, #105 (the web "Support"-ambiguity fix that motivated the tip-jar wording), #49 (the shared PHP backend), #89 (base Info.plist + native chrome), #00 (App Shell Standard).
