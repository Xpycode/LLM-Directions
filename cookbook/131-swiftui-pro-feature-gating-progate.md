# 131 — ProGate: one-flag Pro-feature gating for a SwiftUI macOS app

**Tags:** ProGate, isPro, @Observable freemium, proGated view swap, LockedFeaturePanel, route to upsell, gate seam test, LSUIElement upsell window

**Best for:** gating paid features behind a single `isPro` flag in a freemium macOS
app — swap whole surfaces for an upsell, route individual controls to an upsell, and
never destroy the feature's backing data on downgrade. Built for Aloft/ClipSmart
(Creem licensing), but the gating layer is provider-agnostic.

---

## The shape

One `@MainActor @Observable .shared` entitlement manager exposes a derived `var isPro: Bool`.
Because it's `@Observable`, **any SwiftUI `body` that reads `LicenseManager.shared.isPro`
auto-subscribes** — no `@ObservedObject`, no `@EnvironmentObject`, no injecting the manager
across every window/panel/sheet root (the multi-root Observation trap). Gating is then two
primitives over that one read:

| Gate shape | Use for | Mechanism |
|---|---|---|
| **View-swap** (`.proGated(_:)`) | whole surfaces (a sheet, a pane) | replaces the view with a `LockedFeaturePanel` when Free |
| **Route-to-upsell** (`ProGate.allow` + `ProLabel`) | individual controls (menu items, buttons) | control stays enabled + shows a lock glyph; a Free trigger opens the upsell instead of acting |

**The cardinal rule: gates swap the VIEW only — never delete the feature's backing model.**
A downgraded user's snippets/groups/tags stay on disk and reappear intact on renewal. A
view-swap modifier gets this for free (the gated view isn't even instantiated while locked,
so it can't mutate data behind the lock).

---

## 1. A catalogue enum — upsell copy in one place

```swift
enum ProFeature: String, Identifiable {
    case snippets, smartLists, analytics, exportImport, transforms,
         tagsCollections, linkPreviews, reservoirGroups, pasteQueue
    var id: String { rawValue }
    var title: String { /* per-case */ }
    var blurb: String { /* one-line value statement */ }
    var icon: String  { /* SF Symbol */ }
}
```

## 2. View-swap modifier

```swift
extension View {
    func proGated(_ feature: ProFeature) -> some View {
        modifier(ProGateModifier(feature: feature))
    }
}

private struct ProGateModifier: ViewModifier {
    let feature: ProFeature
    func body(content: Content) -> some View {
        // Reading .isPro here subscribes this view to the @Observable manager.
        if LicenseManager.shared.isPro { content }
        else { LockedFeaturePanel(feature: feature) }
    }
}

// Usage — wrap a whole sheet body:
.sheet(isPresented: $showSnippets) { SnippetsView().proGated(.snippets) }
```

## 3. Inline gating — active → route-to-upsell

Chosen over "disable + lock badge" because it works uniformly for **menu items AND
buttons** (a disabled `Button` inside a `Menu` just greys out and swallows the click —
it can't host a tappable badge), and it converts at the point of intent.

```swift
enum ProGate {
    /// Call at the TOP of a Pro-only action. Returns true when entitled; otherwise
    /// opens the upsell for `feature` and returns false so the caller bails.
    @MainActor @discardableResult
    static func allow(_ feature: ProFeature) -> Bool {
        if LicenseManager.shared.isPro { return true }
        AppDelegate.shared?.showUpsell(for: feature)   // see §5
        return false
    }
}

/// A label that appends a lock glyph while Free — the visual half. Action + badge
/// share one source of truth (isPro), so they can never drift.
struct ProLabel: View {
    let title: String; var systemImage: String?
    init(_ title: String, systemImage: String? = nil) { self.title = title; self.systemImage = systemImage }
    var body: some View {
        HStack(spacing: 6) {
            if let systemImage { Image(systemName: systemImage) }
            Text(title)
            if !LicenseManager.shared.isPro {
                Image(systemName: "lock.fill").font(.caption2).foregroundStyle(.secondary)
            }
        }
    }
}

// Usage — a menu item:
Button { guard ProGate.allow(.exportImport) else { return }; doExport() }
    label: { ProLabel("Export") }
```

## 4. The locked panel (kept a standalone View — type-checker ceiling)

```swift
struct LockedFeaturePanel: View {
    let feature: ProFeature
    @Environment(\.theme) private var theme
    @Environment(\.openURL) private var openURL
    @State private var showingActivation = false
    var body: some View {
        VStack(spacing: 14) {
            Image(systemName: feature.icon).font(.system(size: 40)).foregroundColor(theme.accent)
            Text(feature.title).font(.title2.bold())
            Text(feature.blurb).foregroundColor(theme.textSecondary).multilineTextAlignment(.center)
            Button { openURL(LicenseConfig.checkoutURL) } label: { Text("Upgrade — \(LicenseConfig.priceLabel)").frame(maxWidth: .infinity) }
                .buttonStyle(.borderedProminent)
            Button { showingActivation = true } label: { Text("Enter License Key").frame(maxWidth: .infinity) }
                .buttonStyle(.bordered)
            if LicenseManager.shared.isTrialAvailable {
                Button { Task { await LicenseManager.shared.startTrial() } } label: { Text("Start 30-day Pro trial").frame(maxWidth: .infinity) }
                    .buttonStyle(.bordered)
            }
        }
        .padding(32).frame(maxWidth: .infinity, maxHeight: .infinity).background(theme.surface)
        .sheet(isPresented: $showingActivation) { ActivationSheet() }
    }
}
```

Keep it a **separate `View` struct**, not inlined into a busy parent body — wrapping a
large body in a gating ternary trips SwiftUI's "unable to type-check in reasonable time"
ceiling (see #70).

## 5. Gating a service-triggered workflow (no host view) → self-managed upsell window

Some Pro workflows are engaged from a **service**, not a view — e.g. a paste queue driven
by a singleton with no SwiftUI surface to attach a sheet to. Gate the **engage path** (one
chokepoint) and present the upsell in a self-managed `NSWindow` (mirrors the app's
Welcome-window controller — essential for `LSUIElement` accessory apps where SwiftUI
sheets/`showSettingsWindow:` no-op; cookbook #71).

```swift
// In the service — gate BEFORE any state mutation:
func enqueue(_ items: [ClipboardItem]) {
    guard !items.isEmpty else { return }
    guard isProProvider() else { AppDelegate.shared?.showUpsell(for: .pasteQueue); return }
    /* …mutate… */
}

// AppDelegate.showUpsell(for:) → UpsellWindowController.shared.show(feature:),
// which hosts LockedFeaturePanel(feature:).frame(width: 360, height: 420) in an
// NSHostingController. A maxWidth/maxHeight:.infinity panel needs a FIXED outer
// frame or its windowed fittingSize collapses.
```

## 6. ⚠️ The bite: a gate that reads global state breaks tests silently

The gate reads `LicenseManager.shared.isPro`, and `.shared` is **Free** in the test host.
So every existing test that exercised the gated path (e.g. `enqueue`) now **silently
no-ops** — entries never get added, asserts fail with no obvious cause. Don't force the
license state in tests; **inject a gate seam** (mirrors the manager's own injected-seam
style, #126):

```swift
final class PasteQueueManager {
    /// Pro-gate seam. Defaults to the live flag; tests force it open.
    var isProProvider: () -> Bool = { LicenseManager.shared.isPro }
}

// In the test:
override func setUp()    { super.setUp(); PasteQueueManager.shared.isProProvider = { true } }
override func tearDown() { PasteQueueManager.shared.isProProvider = { LicenseManager.shared.isPro }; super.tearDown() }
```

**Rule:** any gate that reads a global singleton needs a test seam, or it turns green
tests red the moment you add it.

---

## Decisions that aged well

- **Maintenance is never paywalled.** Gate the value-producing path (rich link-preview
  fetch), but leave cleanup/maintenance (clear-cache) **free** — paywalling a delete/cleanup
  can trap a downgraded user's data. For link previews specifically: render the existing
  plain fallback row + **skip the network fetch** when Free (cheaper, not just hidden).
- **Stage the rollout.** Gate the high-value chokepoints first (whole-surface sheets + the
  one engage path) as one commit, then the fiddly inline affordances as a second — easy
  rollback, and the headline value lands first.
- **`checkoutURL` is `#if DEBUG`-split**: test product in Debug (drive the whole upgrade flow
  with fake money), a one-edit live placeholder in release. ⚠️ never ship the `/test/` URL.

**Source:** Aloft/ClipSmart `Views/ProGate.swift`, `Utilities/UpsellWindowController.swift`,
`Services/PasteQueueManager.swift` (2026-06-23, session 46). Pairs with **#70** (type-checker
ceiling — keep the locked panel a separate struct), **#71** (self-managed window for
`LSUIElement` accessory apps), **#126** (closure/struct dependency-injection seam), **#65**
(non-key HUD panel the queue engages), **#00**.
