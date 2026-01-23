# App Minimums Check

Quick baseline features checklist.

## Step 1: Load Checklist

Read `docs/33_app-minimums.md` and display the quick reference section.

## Step 2: Interactive Check

Go through each category:

```
DEPLOYMENT
├── [ ] Auto-update mechanism (Sparkle/App Store)
├── [ ] Version visible in UI (About window or Settings)
├── [ ] Notarized and code-signed (macOS)
└── [ ] App icon at all required sizes

INFRASTRUCTURE
├── [ ] Diagnostic logging (to ~/Library/Application Support/)
├── [ ] Preferences system (@AppStorage)
├── [ ] Error handling with user feedback
└── [ ] Progress feedback for async operations

UI POLISH
├── [ ] Empty states with clear CTAs
├── [ ] Loading states (not blank screens)
├── [ ] Error states with retry option
├── [ ] Keyboard shortcuts (and document them)
└── [ ] About window

PLATFORM-SPECIFIC (pick relevant)
├── macOS: Menu bar (About, Preferences, Quit)
├── macOS: Window state restoration
├── iOS: Review prompt (at the right moment)
├── iOS: What's New on update
└── Web: Favicon, meta tags, 404 page
```

For each category, ask: "**[Category]** - all good, or missing something?"

## Step 3: Note Gaps

If anything is missing, ask:
- "Want to add this to the current session's tasks?"
- "Should I create a TODO for this?"

## Step 4: Summary

Display what's complete vs what needs work.

If everything is checked:
> "All minimums covered. Ready for /review to check code quality."
