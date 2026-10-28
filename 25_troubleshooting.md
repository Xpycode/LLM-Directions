<!--
TRIGGERS: stuck, broken, error, loop, freeze, not working, something broke, crash, troubleshoot, bug, debug, fix, mistake
PHASE: any
LOAD: when stuck
-->

# Troubleshooting Claude Code & App Bugs

*Systematic recovery guide — from quick fixes to nuclear options. Covers both Claude Code CLI
recovery (loops, freezes, context issues) and debugging the app you're building.*

---

## Step Zero: Run /doctor

Before anything else:
```
/doctor
```

It checks: installation, version, settings files (malformed JSON), MCP server errors, keybinding problems, context usage warnings, plugin/agent loading errors.

---

## The 5-Step Diagnostic

| Step | Command | What It Checks |
|------|---------|----------------|
| 1 | `claude --version` | Is Claude Code installed and running? |
| 2 | Visit `status.claude.com` | Is the Anthropic service up? |
| 3 | `/doctor` | Configuration problems? |
| 4 | `/status full` | Context nearly full? |
| 5 | `/clear` | Does a fresh session fix it? |

If step 5 fixes it, the problem was context — not a bug.

---

## Recovery Hierarchy

When something goes wrong, follow this order (quickest to most thorough):

### 1. Escape (Immediate Stop)
Press `Escape` once. Claude stops immediately. Preserves conversation.

Also: `Ctrl+C` during any phase (thinking, reading, making changes).

### 2. Rewind (Undo Recent Changes)
Double-tap `Escape` or run `/rewind`.

Opens an interface showing conversation history and file changes at each point. Restores both conversation context and file changes.

**Important limitation:** Rewind only tracks **direct file edits** made through Claude's editing tools. If Claude ran a **bash command** that modified files, those modifications are NOT tracked by rewind.

- File edits Claude makes directly: CAN be rewound
- File changes from bash commands: CANNOT be rewound
- Git is the ultimate safety net for bash changes

### 3. Git Restore (Reliable Rollback)
```
Show me what changed since my last commit
Discard all changes and go back to my last commit
Restore the config.json file to how it was before
```

Git tracks everything. This is why we commit before anything ambitious.

### 4. Fresh Session (Clean Slate)
```
/clear
```

Wipes conversation. Gives you a clean context. A clean session with a well-written prompt almost always outperforms a long, tangled session where you've been correcting Claude for thirty minutes.

**Before clearing:** Ask Claude to summarize current progress, copy key decisions to CLAUDE.md or notes, commit any working code.

---

## Common Issues

### "It's Not Doing What I Asked"

**Problem: Prompt too vague**

| Vague | Specific |
|-------|----------|
| "Fix the login page" | "The login page shows a blank white screen when users click Submit. Find why and fix it." |
| "Make it better" | "Reduce loading time by optimizing the database queries in this function" |
| "Add some tests" | "Write tests for calculateTotal covering empty carts and discounted items" |

One prompt, one job.

**Problem: Context is full**
- `/clear` between unrelated tasks
- `/compact` when things feel sluggish
- Treat sessions like focused work sprints, not open-ended chats

**Problem: Wrong folder**
```
pwd
```
Check where your terminal is pointed.

**Problem: Keeps forgetting preferences**
Claude doesn't carry preferences between sessions unless told to. Add them to your project CLAUDE.md.

### "Something Broke"

1. **Hit Escape** — press it first, always
2. **Assess** — what actually changed?
3. **Rewind** — `Esc+Esc` or `/rewind` for direct file edits
4. **Git Restore** — if you have a recent commit (more reliable for bash-triggered changes)
5. **Fresh Session** — `/clear` with a better prompt

Most problems come from unclear instructions, not tool failure.

### "The Output Looks Wrong"

- Claude modifying files you didn't mention → **scope creep** (tell it to stop)
- `sudo` or elevated permission commands → **pause and ask why**
- Database operations without discussing backups → **refuse until backups discussed**
- Changes to credential or configuration files → **extra caution**
- Large numbers of files affected → **review each change**

---

## Debugging Application Bugs

This section covers debugging *the app you're building* — distinct from the Claude Code CLI
recovery covered elsewhere in this doc.

### Debugging Workflow

1. **Establish the failure.** Record the action, expected and observed result, frequency and
   relevant source/build/configuration. Check the intended behavior against requirements and the
   implementation; distinguish a product defect from a build, harness or environment failure.

2. **Inspect available evidence first.** Read relevant existing logs, crash reports and build/test
   results before adding instrumentation or asking the user to reproduce or paste output. Verify
   actual locations and supported read commands from the project; examples are not proof that a
   diagnostic exists. If access is denied or evidence is missing, report the specific gap and ask
   only for the smallest useful excerpt or action. Avoid collecting secrets or unrelated data.

3. **Choose a bounded diagnostic batch.** State the question, the next discriminating check and
   a short time/attempt budget appropriate to the problem. Prefer an existing failing case, small
   fixture, saved trace or minimal harness when it exercises the reported behavior. For intermittent
   failures, record observation conditions and a justified sample bound; absence in a sample is
   not proof of a fix. Apply [34_testing.md](34_testing.md#test-types) before running checks:
   inspected effects, isolation and current app-control authority still govern diagnostics.

4. **Test one hypothesis at a time.** Explain what evidence supports it, what result would refute
   it and what the check will distinguish. Inspect the relevant component boundary; add narrow
   temporary logging only when existing evidence cannot answer the question. Change one causal
   variable at a time so the result can support or reject the hypothesis.

5. **Stop or replan when the batch ends.** If the budget is exhausted, the same approach repeats
   without new evidence, or the next action exceeds authorization, record what was learned,
   rejected hypotheses and the remaining gap. Select a materially different check within scope,
   replan broader work, or report the exact blocker. Do not silently restart the budget or hand
   the user another equivalent testing loop; elapsed time does not grant more authority.

6. **Fix and verify the reported behavior.** Make the smallest supported correction, rerun the
   original failure and check affected behavior. Use [finite user acceptance](34_testing.md#finite-user-acceptance)
   for remaining manual cases: reuse valid evidence and name why any passed case must repeat.
   Keep failed, blocked and not-run checks explicit; source checks cannot close missing user or
   artifact acceptance. Remove temporary instrumentation unless it has an ongoing diagnostic
   purpose, and document a non-obvious cause or constraint in its existing project home.

### The "It Used to Work" Trap

**Danger:** Assuming a previous version was correct.

Often, "it used to work" means "it used to appear to work but was never properly tested."

Instead of reverting blindly:
```
Let's understand why it broke before reverting.
What changed between the working and broken versions?
```

### When the Codebase Itself Needs a Fresh Start

Sometimes the codebase is too tangled. Signs:

- Every fix causes two new bugs
- Claude keeps contradicting its previous suggestions
- You've lost track of what's supposed to work
- The architecture has grown "organically" into chaos

**Solution:** Start a new project. Copy working patterns from old code. Don't copy the mess.

---

## Loop Types and Escapes

### Compaction Loop
Context fills, auto-compact fires, but conversation immediately fills again.

**Escape:** Press `Escape` when you see the message. If that doesn't break it, `/clear`.

### Image Processing Loop
Claude keeps trying to process an image that's causing errors.

**Escape:** Press `Escape` twice. If that fails, `/clear`.

### "Let Me Try That Again" Loop
Claude keeps retrying the same failing approach.

**Escape:** Press `Escape`, then tell it explicitly: "That approach isn't working. Try something different."

### Complete Freeze
No response to any input.

**Escape:** Try `Ctrl+C`, then force quit the terminal app, relaunch.

**General rule:** Keep an eye on context usage — loops tend to happen when you're near the limit.

---

## When to Just Start Fresh

This should be your first instinct more often than it is.

**When:**
- Context above 85% and `/compact` isn't helping
- Three approaches tried, none worked
- Claude acting strangely for no apparent reason
- Responses slow and getting worse

**Before you wipe:**
1. Ask Claude to summarize current progress
2. Copy key decisions to CLAUDE.md or a notes file
3. Commit any working code
4. `/clear`

A clean session with a well-written prompt is almost always faster than continuing a tangled one.

---

## Trust Calibration

### Higher Risk (Be Especially Careful)

- File deletion (unrecoverable outside git)
- Database operations (migrations, resets, data modifications)
- External commands (`git push`, publishing packages, network requests)
- Credential files (`.env` and friends) — careful about Claude even *reading* these
- Scope creep — Claude proposes changes to files you didn't mention

### Lower Risk (Generally Safe)

- Read-only operations (viewing, analyzing, explaining)
- Visual changes (CSS, HTML — instant visual feedback)
- Test files (pass/fail is immediate)
- Documentation (minimal functional impact)
- Repeatable patterns (established pattern, known expectations)

**The verification principle:** If you can't verify it, be cautious about accepting it.

---

## Plan Mode: Think First, Touch Nothing

`Shift+Tab` cycles through three modes:

| Mode | Claude Can | Activate |
|------|-----------|----------|
| **Normal** | Read and write (with permission prompts) | Default |
| **Plan** | Read only — creates plans, waits for approval | `Shift+Tab` twice |
| **Auto-accept** | Read and write without individual approval | `Shift+Tab` once more |

Use plan mode for: significant builds, unfamiliar territory, uncertain approaches, high stakes.
Skip for: small fixes, routine operations, quick tweaks.

---

## Quick Recovery Reference

```
Something wrong?
├── Still responding → Escape (stop current action)
├── Need to undo → Esc+Esc (rewind file changes)
├── Bigger rollback → "Discard all changes since last commit"
├── Context is full → /compact (or /clear if over 85%)
├── Tangled session → /clear (start fresh with better prompt)
├── Complete freeze → Ctrl+C → force quit → relaunch
├── Nothing works → claude --version → /doctor → reinstall if needed
```

---

## Xcode / Swift build errors (minimal-diff resolution)

When a build fails, **fix only the error — no refactoring, no cleanup.** Get it green, then move on.

- **Collect all errors first** — `xcodebuild -scheme "X" -destination "platform=macOS" build 2>&1 | grep -E "error:|warning:"`. Don't stop at the first; one root cause often spawns many.
- **Fix import/module errors first** — "Cannot find 'X' in scope" cascades into dozens of false errors; resolving the import clears them. Then type mismatches (`Int(text ?? "0") ?? 0`), then optionals (`?? default` / `guard let`).
- **Common → fix:** "has no member 'Y'" → check optional/spelling · "Ambiguous use" / "expression type is ambiguous" → add explicit type, break into typed lines · "Escaping closure captures mutating 'self'" → `[weak self]` or restructure · "Modifying state during view update" → move mutation to `.onAppear`/an action · SwiftUI opaque-return "no return statements" → every `if` needs an `else` (see `20_swiftui-gotchas.md`).
- **Use only for compilation errors.** Logic bugs, architecture, and perf are debugged/planned/profiled — not "build-fixed."

---

*Based on "Claude Code for the Rest of Us" by Harry Munro (2026) and practical experience.*
