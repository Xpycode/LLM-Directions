# 104 — SwiftUI menu bar: `CommandGroup(after:)` draws **no separators** and stacks by **declaration order** → add explicit `Divider()`s (incl. a divider-only group to flank a command from a package you can't edit) — plus the family "Donate surface" recipe

**Extracted from:** Conjoyn (2026-06-14)

You add a menu item to an existing menu via `CommandGroup(after: .help) { Button("Donate") { … } }`, expecting it to appear as its own visually separated entry like the items around it. It shows up in the right **position** — but with **no separator line** above or below it. The menu reads as one undivided run of items (`Conjoyn Help` / `Send Feedback…` / `Donate`) when you wanted `Conjoyn Help` / —— / `Send Feedback…` / —— / `Donate`.

## Why it happens

Two SwiftUI `Commands` facts, both easy to assume wrong:

1. **`CommandGroup(after:/before:/replacing:)` does NOT auto-insert separators.** It only splices *your* content at the named anchor. The separators you see between Apple's own command groups are authored into those groups — not a property of `after:`. So your injected item butts directly against its neighbours.
2. **Multiple groups targeting the same anchor stack in *declaration order*** (the order they appear in the `.commands { }` builder), not reverse, not by type. This is the lever that makes precise placement possible.

A third trap sits on top: the neighbour you want to separate from is often **provided by a package** (here `FeedbackKit`'s `FeedbackCommands`, which itself does `CommandGroup(after: .help)`). You can't add a `Divider()` inside a type you don't own.

## The fix — explicit `Divider()`s, and a divider-only group for the package neighbour

`Divider()` is a valid leaf inside a `CommandGroup` builder and renders as a menu separator. For a group **you own**, just put it at the top. For a separator **between two items you don't both own**, declare a *divider-only* group at the anchor, positioned by declaration order:

```swift
.commands {
    HelpMenuCommands(content: helpContent, appName: "Conjoyn")  // replacing: .help → "Conjoyn Help"
    // Separator between "Conjoyn Help" and the package's "Send Feedback…": a divider-only group,
    // declared BETWEEN the two so it lands between their items (same-anchor = declaration order).
    CommandGroup(after: .help) { Divider() }
    FeedbackCommands(config: feedbackConfig)                    // package: after: .help → "Send Feedback…"
    DonateCommands()                                            // owns its own leading Divider()
}

struct DonateCommands: Commands {
    var body: some Commands {
        CommandGroup(after: .help) {
            Divider()                                           // separator above "Donate"
            Button("Donate") {
                if let url = URL(string: "https://apps.lucesumbrarum.com/donate.html?app=conjoyn") {
                    NSWorkspace.shared.open(url)
                }
            }
        }
    }
}
```

Result: `Conjoyn Help` / —— / `Send Feedback…` / —— / `Donate`. You can write a `CommandGroup` **inline** in `.commands { }` (the `@CommandsBuilder` accepts it directly) — no wrapper struct needed for the divider-only group.

- **Verify order empirically.** Declaration-order placement is reliable in practice (Donate declared after Feedback → renders below it), but it's worth one eyeball; if a build ever reverses same-anchor groups, swap the two declarations.
- **A leading/trailing `Divider()` can collapse** at a true menu edge (SwiftUI trims a separator with nothing beyond it). It renders fine *between* groups, which is the case here. Fallback if one ever collapses: fold the items into a single combined custom group you fully own.

## The family "Donate surface" recipe (reusable across every app)

Adding a Donate affordance to any app in the family is two cheap, independent surfaces:

- **Menu item** — the `DonateCommands` above. **No ellipsis on "Donate":** per the HIG the ellipsis marks a command that needs *further in-app input before completing* (as "Send Feedback…" does — it opens a form). Donate just hands off to the browser, so no ellipsis. Open with `NSWorkspace.shared.open(url)` (AppKit) or the SwiftUI `@Environment(\.openURL)` action.
- **Help-window topic** (if the app uses the data-driven `HelpMenu` package, cookbook pattern for that): **content-only** — a new `help-donate.md` (gracious copy + a `[Donate](…)` markdown link, which `MarkdownUI` renders clickable → `openURL` → browser) + **one row** in `help-manifest.json`. A recursive `sources: - path: <App>` folder ref in `project.yml` auto-bundles the new `.md` (no xcodegen/`project.yml` change; confirm it landed in `Contents/Resources/`).

**The URL is the load-bearing decision, and it's already solved:** every app points at the **shared apps-portal** donate page — `https://apps.lucesumbrarum.com/donate.html?app=<slug>`. That host is **already live** (it serves the feedback board, #49), so the link works **today**, independent of whether the app's *own* marketing site (`<app>.lucesumbrarum.com`) has been stood up yet. The `?app=<slug>` query tags it so the page can show app-specific context, and it matches the link the app's own website uses — keep it identical across surfaces. (Minor cost: the URL string now lives in both `help-donate.md` and `DonateCommands` — fine, just know both move if it ever changes.)

**Rules:** (1) `CommandGroup(after:/before:)` injects content but **never a separator** — add `Divider()` yourself. (2) Same-anchor command groups order by **declaration order** in `.commands { }` — use that to place an item, and to slot a **divider-only group** beside a command provided by a package you can't edit. (3) Menu-item ellipsis = "needs further in-app input"; a browser hand-off gets none. (4) For a cross-app Donate/support link, point at the **live shared portal** (`apps.lucesumbrarum.com/donate.html?app=<slug>`), not the per-app site that may not be deployed.

Source: Conjoyn `01_Project/Conjoyn/ConjoynApp.swift` (`DonateCommands` + the divider-only group) and `Help/help-donate.md` + `help-manifest.json`. Pairs with **#100 (the web centralized `donate.html?app=` hub — the server side of the exact URL this links to)**, **#102 (drop-in in-app feedback SPM → shared PHP endpoint — the sibling "Send Feedback…" Help-menu surface)**, #49 (the PHP feedback/donate backend on the same portal), #57 (`CommandGroup(replacing: .saveItem)` ⌘W override — sibling menu-command technique), #89 (base Info.plist + native chrome), #00 (App Shell Standard).
