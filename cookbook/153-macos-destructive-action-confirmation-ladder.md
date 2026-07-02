# 153 — Gate a destructive, irreversible macOS action with a confirmation *ladder* (one-time first-run warning → per-run count-confirm → the OS's own dialog) — and report the outcome honestly

**Extracted from:** CompressPhotos (2026-07-02)

You're shipping an action that **deletes the user's data** (here: compress photos, then delete the
originals). A single "Are you sure?" is not enough, and neither is nagging the full warning every time.
The reliable shape is a **three-rung ladder** plus an **honest result** — and a subtle correctness trap
when the user cancels a streamed run.

## The ladder

1. **One-time first-run warning (persisted).** The very first time the user ever triggers the action,
   show an unmissable sheet that explains exactly what deletion means (where the data goes, how long it's
   recoverable, whether it syncs to other devices). Require an explicit "I understand" tick. Persist the
   acknowledgment so it **never nags again**. This warning *doubles as the confirmation for that first
   run* — don't stack a redundant count-confirm on top of it.
2. **Per-run count-confirm (forever).** Every run — including all runs after the first — gets a light
   dialog that **states the count** ("Delete N photos?"). This rung is permanent because it's the guard
   against a footgun: e.g. a scan that auto-selects *everything*, one stray click away from a
   whole-library delete. The visible N is the backstop.
3. **The OS's own dialog.** PhotoKit/`deleteAssets` (and many system APIs) raise their own confirmation
   you must not suppress. Treat it as the final rung, not something to work around.

```swift
// ContentView — the button only routes; every presentation lives on the BODY (see #147).
@AppStorage("didAcknowledgeDestructiveRun") private var acked = false
@State private var showFirstRunWarning = false
@State private var showRunConfirm = false

private func requestRun() {
    if acked { showRunConfirm = true }        // rung 2 (every later run)
    else      { showFirstRunWarning = true }  // rung 1 (first ever; also confirms this run)
}

var body: some View {
    HSplitView { /* … */ }
        .toolbar { /* run Button just calls requestRun() */ }
        .toolbarRole(.editor)
        // Rung 2 — lightweight count-confirm, states N:
        .confirmationDialog("Compress and DELETE \(model.selection.count) selected photo\(model.selection.count == 1 ? "" : "s")?",
                            isPresented: $showRunConfirm, titleVisibility: .visible) {
            Button("Compress + Delete Originals", role: .destructive) { model.startRun(settings: settings) }
            Button("Cancel", role: .cancel) {}
        } message: { Text("…deletes the original. Goes to Recently Deleted (~30 days). You'll still get the system's own delete confirmation.") }
        // Rung 1 — one-time heavy warning that also starts the run:
        .sheet(isPresented: $showFirstRunWarning) {
            FirstRunWarningView(photoCount: model.selection.count,
                onConfirm: { acked = true; showFirstRunWarning = false; model.startRun(settings: settings) },
                onCancel:  { showFirstRunWarning = false })
        }
        // Result — sheet keyed off a non-nil model value (below):
        .sheet(isPresented: Binding(get: { model.lastResult != nil },
                                    set: { if !$0 { model.lastResult = nil } })) {
            if let r = model.lastResult { RunSummaryView(result: r, onDone: { model.lastResult = nil }) }
        }
}
```

The first-run sheet forces a deliberate acknowledgment — a `role: .destructive` confirm that stays
`.disabled` until an "I understand" checkbox is ticked:

```swift
struct FirstRunWarningView: View {
    let photoCount: Int; let onConfirm: () -> Void; let onCancel: () -> Void
    @State private var understood = false
    var body: some View {
        VStack(spacing: 20) {
            Image(systemName: "exclamationmark.triangle.fill").font(.system(size: 44)).foregroundStyle(.orange)
            Text("This deletes your original photos").font(.title2.bold())
            // • makes a smaller copy, verifies it, then DELETES the original
            // • originals → Recently Deleted, recoverable ~30 days, then gone
            // • on an iCloud library this syncs to ALL devices
            // • you'll still get macOS's own delete confirmation
            Toggle("I understand my originals will be deleted", isOn: $understood).toggleStyle(.checkbox)
            HStack {
                Button("Cancel", role: .cancel, action: onCancel).keyboardShortcut(.cancelAction)
                Spacer()
                Button("Compress + Delete \(photoCount) Original\(photoCount == 1 ? "" : "s")",
                       role: .destructive, action: onConfirm)
                    .keyboardShortcut(.defaultAction).disabled(!understood)   // ← the deliberate gate
            }
        }.padding(28).frame(width: 480)
    }
}
```

## The Stop-race trap (streamed / cancellable runs) — ⚠️ superseded by #154

**Do NOT wire Stop as "cancel the consuming task".** This section originally recommended exactly
that plus a `stoppedEarly(processed, total)` fallback for the dropped final summary — a same-day
review found the wiring itself is the bug, not just the lost summary: the stream dies instantly, so
the UI declares "Run stopped" **while the producer is still winding down** — the OS delete dialog
can appear *after* the "stopped" report, the `runTask == nil` re-entry guard releases early (a
second concurrent run can start), and whatever the wind-down actually committed is never reported.

**The fix is the run-handle pattern — see `#154`:** `start()` returns `(events, stop())`; Stop
cancels the *producer*, the consumer keeps folding events into a visible "Stopping…" phase until
the genuine `.finished(summary)` arrives, and the in-flight state stays up (re-entry blocked,
progress bar visible) through the wind-down. Keep `stoppedEarly` only as a *defensive* fallback for
a stream that dies without its terminal event — and word it honestly (don't claim work was
committed; you don't know).

## Report the result honestly — headline keyed to *how* it ended

A destructive op has more terminal states than "done". Key the summary's icon+headline off the actual
stop reason, and **always surface the messy leftovers** (duplicates kept, unverified stray copies) so the
user can clean up:

```swift
switch result {
case .stoppedEarly:                                       ("stop.circle.fill", .orange, "Run stopped")
case let .summary(s): switch s.stoppedReason {
    case .completed:      ("checkmark.circle.fill", .green,  "Run complete")
    case .cancelled:      ("stop.circle.fill",      .orange, "Run stopped")
    case .deleteDeclined: ("hand.raised.fill",       .orange, "Originals kept")   // OS dialog declined
    case .diskRefusal:    ("externaldrive.badge.exclamationmark", .orange, "Stopped — low disk space")
    case .deleteFailed:   ("exclamationmark.triangle.fill", .red, "A delete failed — originals kept")
}}
// rows: copies verified · originals deleted · space freed · skipped-by-reason · failed
//       · ⚠️ duplicates kept · ⚠️ unverified stray copies (delete by hand)
```

## Rules to internalize

- **A destructive action = a ladder, not a dialog.** One-time persisted warning (first run) → per-run
  count-confirm (every run) → the OS's own dialog. The one-time warning *is* the first run's confirm;
  don't double it.
- **Persist the first-run ack** (`@AppStorage`) and gate the confirm on an explicit "I understand" tick.
  The tick makes the first acknowledgment deliberate; the persistence stops it nagging.
- **Keep the count-confirm forever** — it's the backstop against select-all / mis-click footguns. Always
  show the count.
- **Present every dialog/sheet from the content body, never a toolbar item** (see #147) or the modal
  soft-locks the window.
- **Stop must cancel the producer, not the consumer** (#154). Consumer-cancel ends the UI while the
  engine winds down (post-"stopped" dialogs, re-entry race, lost tally). Keep an honest
  `stoppedEarly` fallback for a stream that dies without its terminal event; never fabricate numbers.
- **Report all terminal states, including the ugly ones** — declined, disk-refusal, delete-failed, and
  any kept-duplicates / unverified stray copies the user must clean up by hand.

Source: CompressPhotos — `01_Project/CompressPhotos/ContentView.swift` (ladder + body-level presentations),
`Views/FirstRunWarningView.swift` (one-time gate), `AppModel.swift` (`startRun`/`stopRun` — now the #154
run-handle design), `Views/RunSummaryView.swift` (headline by stop reason). Pairs with **#147** (present
from body, not toolbar), **#35** (`AsyncStream` bounded fan-out — the producer), **#154** (Stop = cancel
the producer; run-handle), **#36** (fast-preview / heavy-commit split); the footer progress+Stop UI is the
existing "Progress: footer swap" quick-ref pattern.
