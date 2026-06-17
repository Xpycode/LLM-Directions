# App Minimums Check

Quick baseline features checklist before shipping.

## Step 1: Load Checklist

Read `docs/33_app-minimums.md` and display the Quick Reference section.

## Step 2: Interactive Check

Go through each category from the doc:
- **Deployment** (auto-update, version visibility, signing, icons)
- **Infrastructure** (logging, preferences, error handling, progress)
- **UI Polish** (empty states, loading states, error states, shortcuts, About)
- **Platform-Specific** (menu bar, window state, review prompts, etc.)

For each category, ask: "**[Category]** - all good, or missing something?"

## Step 3: Note Gaps

If anything is missing, **capture it — don't fix mid-check** (see `docs/62_final-stretch-triage.md`,
Rule 1). Sort each gap into a bucket so a cosmetic miss isn't treated like a ship-blocker:
- **Bucket 1 (ship-blocker)** — a missing minimum that breaks core use or risks data → fix before ship
- **Bucket 2/3** — survivable or cosmetic → route to v1.1 by default

Then ask:
- "Want to add the bucket-1 gaps to the current session's tasks?"
- "Should I create TODOs for the rest (v1.1)?"

## Step 4: Summary

Display what's complete vs what needs work.

If everything is checked:
> "All minimums covered. Ready for /review to check code quality."
