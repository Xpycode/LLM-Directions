<!--
TRIGGERS: main menu, menu bar, NSMenu, Commands, CommandMenu, CommandGroup, keyboard shortcut, menu item, "add a menu", "should this be in the menu", Help search, menu validation, discoverability
PHASE: any (especially Spec + Implement + UI review)
LOAD: full
-->

# Main Menu — The Complete Command Inventory

*This is about the **main menu bar** (top of screen: App · File · Edit · View · Window · Help)
— not the status-item "menu bar extra", not context menus. For menu **styling/types**
(pull-down, pop-up, context) see [`41_apple-ui.md`](41_apple-ui.md).*

---

## The principle

> **The main menu is the complete, canonical inventory of the app's commands.**
> Any meaningful action reachable in the window — a button, toolbar item, gesture, or
> context-menu entry — should **also** exist as a main-menu command, in the right menu.

This is a **rule, not a nicety**, because on macOS the menu bar is load-bearing for four
things the in-window UI cannot provide:

1. **Keyboard shortcuts have no other home.** The menu item is where a shortcut is *shown
   and discovered*. A shortcut bound to a button that isn't in a menu is invisible to the user.
2. **Help → Search only indexes menu items.** An action absent from the menu is literally
   **unsearchable**. This is the killer argument — it's a discoverability dead-end.
3. **Discoverability.** Users learn an unfamiliar app by *browsing its menus*, not by hunting
   for buttons or memorising right-click gestures.
4. **Accessibility + automation.** VoiceOver menu navigation and "click menu item X" UI
   automation/AppleScript both rely on the command actually being in the menu.

## Corollaries (the usable rules)

- **Right menu, standard slots.** Document ops → **File** · editing/undo/find → **Edit** ·
  display/layout toggles → **View** · window management → **Window** · everything app-specific →
  a **named app menu or a verb-named `CommandMenu`** (not jammed into File or a junk-drawer).
  Follow HIG ordering: standard menus first, custom menus before Window/Help.
- **The menu item is the source of truth for the shortcut.** Define `.keyboardShortcut` on the
  *command*; the in-window button **mirrors** it, never defines its own. One shortcut, one home.
- **Context menus are a subset/shortcut of main-menu commands**, never a separate command
  universe. If it's worth a right-click, it's worth a menu command.
- **Validate enabled/disabled to current context** — no perpetually-dead items. SwiftUI:
  `FocusedValue` / `@FocusedBinding` gate the command; AppKit: menu validation
  (`validateMenuItem(_:)` / `NSMenuItemValidation`).
- **Keep them in sync both ways.** Don't ship a menu item with no UI equivalent, or a UI action
  with no menu command. Drift in either direction is the bug.

## The mechanism (SwiftUI)

`Commands` / `CommandMenu` / `CommandGroup` attached to the `Scene`, `.keyboardShortcut` on each
command, and `FocusedValue`/`@FocusedBinding` to make commands context-sensitive. Buttons in the
window reference the *same* action and shortcut. (A copy-first scaffold belongs in
`PATTERNS-COOKBOOK.md`; this doc is the principle.)

## Audit checklist (run an app against itself)

- [ ] Every toolbar button / primary in-window action has a corresponding main-menu command.
- [ ] Every context-menu entry has a main-menu equivalent.
- [ ] Every keyboard shortcut is defined on a menu command (none orphaned on a bare button).
- [ ] App-specific features live in a named/verb menu, **not** buried in File or an Appearance pane.
- [ ] No menu item is permanently disabled or dead; all validate to context.
- [ ] Help → Search finds every user-facing action by name.

> **Typical failure:** an action that lives *only* as a window button or a buried Settings
> control (e.g. a hotkey recorder with no `Edit ▸` / app-menu command) — invisible to Help
> search and shortcut discovery. That's exactly the gap this rule closes.
