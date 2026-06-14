# 101 — In-app Settings search: result→control highlight pulse + ⌘F focus + Form scroll-to

**Best for:** a macOS Settings window (sidebar `NavigationSplitView` of `Form`-based panes) that gains a
**search field** which, on a query, lists *individual controls* across every pane; clicking a result
opens that pane and **pulses the matched control** — the macOS Ventura+ System Settings behavior. Covers
three non-obvious quirks that bite when you build this: (1) highlighting a control *after navigating to
its pane*, (2) focusing a `.searchable` field with ⌘F when SwiftUI gives no focus binding, (3) scrolling
a target row into view inside a `Form`. Shipped in **Aloft/ClipSmart** settings-search (Waves 0–3).

Composes with #71 (LSUIElement self-managed Settings window) and the data side: a pure index of
`(id, title, keywords, tab)` entries + a `results(for:)` matcher (derive the keyboard-shortcut slice from
your `CaseIterable` action enum so it can't drift). This file is the **UI** half.

---

## Quirk 1 — the pulse must fire on BOTH `onAppear` and `onChange`

A search result does two things in one tap: switch the pane **and** set a "pending highlight" flag. The
targeted control therefore **mounts fresh with the flag already set**, so a plain
`.onChange(of: pendingHighlight)` *never fires* — the value didn't change *after* that view began
observing. You need `onAppear` (cross-pane nav) **and** `onChange` (tapping a 2nd result while already on
the pane). Missing `onAppear` is the classic "highlight works within a pane but not when navigating to
it" bug.

```swift
@MainActor
final class SettingsRouter: ObservableObject {
    static let shared = SettingsRouter()
    @Published var selectedTab: SettingsTab = .general
    @Published var pendingHighlight: String?   // anchor id a result wants to spotlight
    private init() {}
}

private struct SettingsHighlightModifier: ViewModifier {
    let id: String
    @ObservedObject private var router = SettingsRouter.shared   // observe the shared singleton
    @State private var litOpacity: Double = 0

    func body(content: Content) -> some View {
        content
            .background(
                RoundedRectangle(cornerRadius: 6)
                    .fill(Color.accentColor.opacity(litOpacity))
                    .padding(.vertical, -4).padding(.horizontal, -10)
                    .allowsHitTesting(false)
            )
            .onAppear { if router.pendingHighlight == id { pulse() } }          // cross-pane nav
            .onChange(of: router.pendingHighlight) { _, new in                  // same-pane re-tap
                if new == id { pulse() }
            }
    }

    /// Quick rise → hold → gentle fade. Deterministic — avoids phaseAnimator(trigger:)'s
    /// phase-restart semantics. Clear the flag at the end so a repeat tap of the same result
    /// re-triggers onChange (nil → id is a change; id → id is not).
    private func pulse() {
        withAnimation(.easeOut(duration: 0.2)) { litOpacity = 0.28 }
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.7) {
            withAnimation(.easeIn(duration: 0.7)) { litOpacity = 0 }
        }
        DispatchQueue.main.asyncAfter(deadline: .now() + 1.5) {
            if router.pendingHighlight == id { router.pendingHighlight = nil }
        }
    }
}

extension View {
    /// id MUST equal the search-index entry's id. Apply to every indexed control; section/pane-level
    /// entries (multi-row sections, non-Form VStacks) anchor on their section header Text.
    func settingsHighlight(id: String) -> some View { modifier(SettingsHighlightModifier(id: id)) }
}
```

On result tap, **set both fields and keep the query** (System Settings keeps results visible so a second
pick needs no re-type — clearing the field on tap reads as abrupt):

```swift
private func openResult(_ entry: SettingsIndexEntry) {
    router.selectedTab = entry.tab
    router.pendingHighlight = entry.id
    // do NOT clear searchQuery — results persist (System Settings convention)
}
```

## Quirk 2 — ⌘F focuses a `.searchable` field via an invisible command + AppKit

`.searchable` exposes **no `@FocusState` binding on macOS** (the `isPresented:` overload only helps
toolbar search that appears on demand, not an always-visible sidebar field). Reach through the window to
the underlying `NSSearchField`. A zero-opacity `Button` with `.keyboardShortcut` placed in `.background`
registers the key equivalent at **window** level, so ⌘F works regardless of which control holds focus,
without intercepting clicks.

```swift
// In the NavigationSplitView body:
.searchable(text: $searchQuery, placement: .sidebar, prompt: "Search Settings")
.background(searchFocusHotkey)

private var searchFocusHotkey: some View {
    Button("") { focusSidebarSearchField() }
        .keyboardShortcut("f", modifiers: .command)
        .opacity(0).accessibilityHidden(true)
}

private func focusSidebarSearchField() {
    guard let window = NSApp.keyWindow,
          let field = Self.firstSearchField(in: window.contentView) else { return }
    window.makeFirstResponder(field)
}

private static func firstSearchField(in view: NSView?) -> NSSearchField? {
    guard let view else { return nil }
    if let field = view as? NSSearchField { return field }
    for sub in view.subviews { if let f = firstSearchField(in: sub) { return f } }
    return nil
}
```

## Quirk 3 — scroll a target row into view inside a `Form`

Highlight-only doesn't scroll, so on a **long** pane the pulse fires below the fold and looks like nothing
happened. `ScrollViewProxy.scrollTo` is documented-unreliable inside a `Form` — but it works **row-level**
on current SDKs in practice (verified macOS 15/26). Wrap *only* the long pane's `Form`; the row's scroll
id comes free from the existing `ForEach(_, id: \.self)` (no per-row `.id()` needed). Map the pending
string id back to the `ForEach` element and `scrollTo(_, anchor: .center)`, deferred one runloop hop so
rows are laid out after a cross-pane mount.

```swift
var body: some View {
    ScrollViewReader { proxy in
        form
            .onAppear { scrollToPending(using: proxy) }
            .onChange(of: router.pendingHighlight) { _, _ in scrollToPending(using: proxy) }
    }
}

private func scrollToPending(using proxy: ScrollViewProxy) {
    guard let p = router.pendingHighlight, p.hasPrefix("kbd."),
          let action = ShortcutAction(rawValue: String(p.dropFirst(4))) else { return }
    DispatchQueue.main.async {
        withAnimation(.easeInOut(duration: 0.25)) { proxy.scrollTo(action, anchor: .center) }
    }
}
// where the rows are:  ForEach(actions, id: \.self) { action in Row(action).settingsHighlight(id: "kbd.\(action.rawValue)") }
```

---

## Gotchas

- **`@ObservedObject` not `@StateObject`** for the shared `SettingsRouter` singleton inside the modifier —
  the modifier doesn't own the object's lifecycle.
- **Clear the flag after the pulse**, or a repeat tap of the same result won't re-fire (`onChange` needs a
  value transition; `id → id` is a no-op).
- **Section/pane-level index entries** (a multi-row section, or a pane that's a plain `VStack` not a
  `Form`) have no single control to pulse — anchor `.settingsHighlight` on the **section header `Text`** or
  the representative editor. Honest behavior for a section-level hit.
- **Don't fold `.id()` into `.settingsHighlight`** to enable scrolling everywhere — `.id()` resets a view's
  identity/state. Only the panes that actually need scroll get a `ScrollViewReader`; keep short panes
  highlight-only.
- **Pulse animation:** explicit `@State` opacity (two `withAnimation` steps) beats `phaseAnimator([0,1,0],
  trigger:)` for predictability — though `[0,1,0]` is robust *if* you use it, because index 0 and 2 share
  opacity 0 so the phase-restart ambiguity doesn't show.

**Source:** Aloft/ClipSmart `Views/SettingsView.swift` (`SettingsHighlightModifier`, `searchFocusHotkey`),
`Views/KeyboardSettingsView.swift` (`ScrollViewReader`), `docs/specs/settings-search.md`.
