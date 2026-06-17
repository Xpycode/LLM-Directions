# Production Review Checklist

Run through the production checklist interactively.

## Step 1: Load Checklists

Read both source documents:
- `docs/30_production-checklist.md` - Code quality and release prep
- `docs/33_app-minimums.md` - Baseline features (updates, logging, UI polish)

Also read `docs/62_final-stretch-triage.md` — the methodology for this pass. The review *finds*;
#62 governs what you do with what you find (capture-don't-fix, the three buckets, define-done).

Display the checklist sections from these files.

## Step 2: Interactive Review

Go through each section, asking:

"**[Section Name]** - Ready to review this section?"

For each item:
- Ask "✓ [Item]?"
- User confirms or flags issue
- If issue flagged, **note it and move on — do not fix mid-pass** (#62 Rule 1: capture, don't fix).
  Complete the full pass first; fixing comes after triage.

## Step 3: Triage the batch (per `docs/62_final-stretch-triage.md`)

Now that the pass is complete, sort every flagged issue into one of the three buckets — honestly.
Most "this seems off" items are bucket 2 or 3 wearing bucket-1 clothing; visible ≠ important.

| Bucket | Definition | Default |
| ------ | ---------- | ------- |
| **1 — Ship-blocker** | Crash, data loss, core feature broken | Fix before ship |
| **2 — Should-fix** | Annoying but survivable | Fix if cheap, else v1.1 |
| **3 — Polish** | Nobody will notice or care | v1.1 by default |

A large bucket 3 is expected and good — it means the worst problem left is cosmetic.

## Step 4: Generate Report

Create a summary, grouping issues by bucket:

```markdown
## Production Review: YYYY-MM-DD

### Passed
- [x] Item 1
- [x] Item 2

### Bucket 1 — Ship-blockers (fix before ship)
- [ ] Item 3 - [note about issue]

### Bucket 2 — Should-fix (fix if cheap, else v1.1)
- [ ] Item 4 - [note about issue]

### Bucket 3 — Polish (v1.1)
- [ ] Item 5 - [note about issue]

### Summary
X of Y items passed. Ship-blockers: N. [Ready to ship once bucket 1 is clear / N blockers remain]
```

If there's no written "done for v1" line yet, this is the moment to write one (#62 Rule 8) — it's
what gives the bucket-3 list permission to wait.

## Step 5: Save or Display

Ask: "Save this report to docs/sessions/review-YYYY-MM-DD.md?"

If yes, save it. Either way, display the summary.
