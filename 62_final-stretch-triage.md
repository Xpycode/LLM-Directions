<!--
TRIGGERS: final stretch, last 10%, last 1%, almost done, can't ship, endgame drags,
          "this seems off", polish, nitpicks, bikeshedding, ship-blocker, triage,
          v1 vs v1.1, "define done", scope creep at the end, fixed one broke two,
          regression pass, misaligned button feels urgent, Startschwierigkeiten
PHASE: ship (the final stretch before release)
LOAD: when a project is "nearly done" but won't close out, when the stream of "this seems off"
      feels infinite, when deciding what is a ship-blocker vs polish, or when defining "done for v1"
-->

# Final-Stretch Triage

**In the final stretch, your job is to manage a queue, not to chase symptoms. Visible ≠ important.**

The last 10% (often really the last 1%) drags because the bottleneck shifts. Early on, the work is
*building*. At the end, the work is *triage and specification* — the AI still fixes fast, but the
stream of "this seems off" never resolves on its own. These rules exist to control that stream, not
to write better fixes.

---

## The core trap

A misaligned button feels urgent because you see it every time you open the app. It is almost never a
ship-blocker. The eye snags on it, the brain files it as critical, but it is just *visible*. Most
"off" feelings are bucket 2 or 3 (below) wearing bucket-1 clothing. The exhaustion is from treating
cosmetic items with crash-level urgency.

---

## Rule 1: Capture, don't fix

When testing surfaces "this seems off," **write it down and keep testing.** Do not switch into fix
mode mid-pass.

- Context-switching from *finding* to *fixing* is what makes the endgame feel infinite — you never
  complete a full pass.
- One full testing pass → collect everything → triage the batch → then fix.
- Route into `ideas.md` (or the active backlog), not into the current diff.

```
FIND (full pass)  →  TRIAGE (whole batch)  →  FIX (by bucket)
```

---

## Rule 2: Three buckets, honestly

| Bucket | Definition | Default action |
| ------ | ---------- | -------------- |
| **1 — Ship-blocker** | Crash, data loss, core feature broken | Fix before ship |
| **2 — Should-fix** | Annoying but survivable | Fix if cheap, else v1.1 |
| **3 — Polish** | Nobody will notice or care | v1.1 by default |

**Principle:** Bucket 3 is supposed to be large. That is the sign you built something with depth — a
crooked button is the worst problem left.

---

## Rule 3: Reproduce before fix

"This seems off" is unspecified. Handed to the AI as-is, it will guess, fix the wrong thing, and risk
a regression. Force the loop:

```
reproduce  →  confirm cause in logs  →  fix  →  verify repro is gone
```

Make the model **read the logs first** as step one, not invent a hypothesis. The logging system is the
leverage here — use it.

---

## Rule 4: Batch, then regression-pass

Solo + AI means it is easy to fix ten things and quietly break two — the AI edits without holding full
context.

- After each batch of fixes, re-run the core happy-path flow end to end.
- "Fixed one, broke two" is the real reason late stage drags. The regression pass is non-optional.

---

## Rule 5: Separate the visual pass from the logic pass

Don't interleave "this crashes" and "this is 3px off." They use different attention and different fix
strategies.

- **Logic pass:** one session, only behavior/crashes/state.
- **Visual pass:** one session, only spacing/alignment/typography.

Batching by *type* of off-ness (not just into one list) makes each pass faster and less draining.

---

## Rule 6: Show, don't tell, for visual bugs

"This button is off" is expensive — the AI must guess what and by how much.

- Screenshot + annotation, or a concrete spec: "Export should be baseline-aligned with Cancel."
- For UI, showing beats describing by a wide margin. See `36_ui-changes-protocol.md`.

---

## Rule 7: A "weird stuff seen" log, separate from the backlog

Not every "off" is real. Half are misremembered intended behavior or a one-off that never recurs.

- Keep an inbox separate from `ideas.md`.
- Let items sit ~a day before promoting them to the actionable backlog.
- This filters out a surprising amount of noise for free.

---

## Rule 8: Define "done for v1" in writing — now

The single highest-leverage move. Without a written line, "off" has no floor and polish expands to
fill all available time.

```
[App] v1 ships when:
- [ ] X works without crashing
- [ ] Y works without crashing
- [ ] Z works without crashing
Everything not on this list → v1.1 by default.
```

**Principle:** v1.1 is a feature, not a failure. It exists to give you permission to *not* fix
everything now. Startschwierigkeiten go there on purpose.

---

## See also

- `30_production-checklist.md` — the ship gate this feeds into
- `33_app-minimums.md` — the baseline a v1 must clear before polish even matters
- `36_ui-changes-protocol.md` — show-don't-tell for the visual bugs in Rule 6
- `57_checkpoint-discipline.md` — checkpoint before a batch fix so a regression is one `git reset` away
