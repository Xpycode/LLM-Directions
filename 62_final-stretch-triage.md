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

**Use the agreed outcome, evidence and task impact to decide what remains before release.**

The last 10% (often really the last 1%) drags because the bottleneck shifts. Early on, the work is
*building*. At the end, the work is *triage and specification* — the AI still fixes fast, but the
stream of "this seems off" never resolves on its own. These rules exist to control that stream, not
to write better fixes.

---

## The core trap

A visible issue can be optional refinement, a failed visual requirement or an obstacle to a core
task. Establish which before assigning priority. An inaccessible control can block completion even
when the app does not crash; deliberate aesthetic quality can be part of the agreed outcome.
New optional improvements should not silently move that finish line.

---

## Rule 1: Capture, don't fix

During the agreed finite acceptance batch, **capture findings before changing implementation**.
Keep blocked/not-run cases explicit; do not extend the batch with every new observation.

- Context-switching from *finding* to *fixing* is what makes the endgame feel infinite — you never
  complete a full pass.
- Complete the available cases in the agreed batch → triage findings → fix selected issues.
- Route confirmed actionable findings into `TASKS.md` Backlog; route one-off or unconfirmed findings
  into `TASKS.md` Inbox. Do not put either into the current diff.

```
FIND (agreed batch)  →  TRIAGE (findings)  →  FIX (selected scope)
```

---

## Rule 2: Three buckets, honestly

| Bucket | Definition | Default action |
| ------ | ---------- | -------------- |
| **1 — Ship-blocker** | Core task blocked, crash/data loss, or unmet required release criterion | Resolve before ship |
| **2 — Should-fix** | Demonstrated degradation that still meets required acceptance criteria | Fix within agreed scope, else defer |
| **3 — Polish** | Optional refinement beyond the agreed requirements | Defer by default |

Classify by demonstrated impact, relevant risk and agreed requirements, not by whether the issue
looks visual or technical. Required accessibility, security, privacy, data-integrity and distribution
obligations remain release gates. A missing required check is unresolved evidence, not a pass or
automatically a confirmed defect. The number of items in a bucket is not a quality target.

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

## Rule 4: Verify the affected behavior

Use `34_testing.md` → **Finite user acceptance** to select a finite verification batch after fixes.

- Verify the original failure and affected behavior, including shared dependencies and relevant
  failure paths. Run the core journey end to end when the change or unresolved integration risk
  warrants it; a fix batch alone does not require repeating every accepted case.
- Reuse valid evidence with source/artifact/configuration provenance. Name why a passed check needs
  repeating: changed behavior or artifact, invalid configuration, missing evidence or a regression.
- Required release-artifact checks still apply. Report passed, failed, blocked and not-run cases;
  source/unit checks do not replace missing artifact or user acceptance. Preserve existing test and
  app-control boundaries.

---

## Rule 5: Separate the visual pass from the logic pass

Don't interleave "this crashes" and "this is 3px off." They use different attention and different fix
strategies.

- **Logic pass:** one session, only behavior/crashes/state.
- **Visual pass:** one session, only spacing/alignment/typography.

Batching by *type* of off-ness (not just into one list) makes each pass faster and less draining.
Grouping does not determine severity; verify the combined journey when presentation affects behavior.

---

## Rule 6: Show, don't tell, for visual bugs

"This button is off" is expensive — the AI must guess what and by how much.

- Screenshot + annotation, or a concrete spec: "Export should be baseline-aligned with Cancel."
- For UI, showing beats describing by a wide margin. See `36_ui-changes-protocol.md`.

---

## Rule 7: A "weird stuff seen" inbox, separate from the backlog

An observation may be a defect, an unclear expectation or an optional improvement. Keep its evidence
and uncertainty visible until it can be classified.

- Keep these observations in `TASKS.md` Inbox, separate from the actionable Backlog.
- Promote when evidence establishes an actionable issue; do not require an arbitrary waiting period
  or dismiss a consequential report merely because it has occurred once.

---

## Rule 8: Define "done for v1" in writing — now

Write the intended outcome and required acceptance criteria before the final pass. Preserve personal,
commercial, learning or craft goals; do not shrink the outcome just to declare completion.

```
[App] v1 ships when:
- [ ] Intended users can complete X with the agreed result
- [ ] Required behavior and visual/accessibility criteria have supporting evidence
- [ ] Applicable security, privacy, data-integrity and distribution gates pass
Optional additions beyond these requirements → later scope by default.
```

Once required acceptance passes, defer optional refinements unless scope deliberately changes.
New evidence of a required failure still needs triage; omission from a short v1 list does not waive
an applicable obligation. Keep missing acceptance evidence open rather than declaring completion.

---

## See also

- `30_production-checklist.md` — the ship gate this feeds into
- `33_app-minimums.md` — the baseline a v1 must clear before polish even matters
- `36_ui-changes-protocol.md` — show-don't-tell for the visual bugs in Rule 6
- `57_checkpoint-discipline.md` — checkpoint before a batch fix so a regression is one `git reset` away
