<!--
TRIGGERS: philosophy, mindset, how to think, validate code, spot bugs, red flags, prompt developer
PHASE: any
LOAD: full
-->

# The Prompt Developer's Mental Model

**You are a director, not a coder.**

*How to think about AI-assisted development and validate the output.*

---

## Part 1: The Mental Model

### You Are a Director, Not a Coder

Think of yourself as a film director. You don't operate the camera or edit the footage yourself, but you need to:

- Know what a good shot looks like
- Communicate your vision clearly
- Recognize when something is wrong
- Know when to call "cut" and try again

The same applies to prompt-based development:

| Film Director | Prompt Developer |
|---------------|------------------|
| Knows cinematography principles | Knows software architecture patterns |
| Gives clear shot directions | Writes detailed specs and prompts |
| Reviews dailies for quality | Reviews code output adversarially |
| Uses multiple takes | Uses multiple AI models for validation |

### The Core Insight

> "AI-assisted development requires MORE discipline, not less. The tools amplify both good practices and bad practices."

What this means for you:
- Vague prompts → vague, buggy code
- No verification → bugs ship silently
- Single AI review → critical bugs missed
- Clear specs + multi-model review → working software

---

## Part 2: Working With Claude Code

### The "Brilliant But Untested Colleague" Model

Think of Claude Code as a brilliant but untested colleague. This colleague is knowledgeable, fast, and genuinely capable. But they're new. You don't know their judgement yet.

You wouldn't hand this person full access to everything and go make tea. You'd stay involved, review their work, keep your hand on the wheel.

This is pair working with someone who types faster than you — not hiring a contractor and receiving finished work.

### Trust Calibration

Not all operations carry the same risk. Calibrate your involvement:

**Higher Risk (Review Carefully):**
- File deletion (unrecoverable outside git)
- Database operations (migrations, resets)
- External commands (`git push`, publishing, network requests)
- Credential files (`.env` and friends)
- Scope creep — Claude changing files you didn't mention
- `sudo` or elevated permission commands

**Lower Risk (Generally Safe):**
- Read-only operations (viewing, analyzing, explaining)
- Visual changes (CSS, HTML — instant visual feedback)
- Test files (pass/fail is immediate)
- Documentation (minimal functional impact)
- Repeatable patterns (established, known expectations)

**The Verification Principle:** If you can't verify it, be cautious about accepting it.

### Signs to Pause

Stop and question when:
- Claude modifying files you didn't mention
- Database operations without discussing backups
- Changes to credential or configuration files
- Large numbers of files affected at once
- Commands that interact with external systems

---

## Part 3: Reading Code You Didn't Write

### Structure Over Syntax

You don't need to learn programming languages. Focus on:

**What matters:**
- Components and modules — what are the major pieces?
- Data flow — how does information move through?
- User actions — what happens when someone clicks a button?
- Dependencies — what relies on what?

**What you can safely ignore:**
- Specific syntax (curly braces, semicolons, brackets)
- Language-specific idioms
- Performance optimizations
- Low-level implementation details

### "Explain This" — Your Most Powerful Prompt

Use at different zoom levels:
- **Quick overview:** "Give me a brief summary of what this file does."
- **Full walkthrough:** "Walk me through this code step by step."
- **Specific question:** "What happens when someone enters the wrong password three times?"
- **Simplify:** "Explain this like I'm not a developer."

Don't pretend to understand more than you do. Being upfront gets you better answers.

### Building Mental Models

Five techniques for understanding code:

1. **Start with "Why"** — "What problem does this project solve?" / "Why does this file exist?"
2. **Big picture first** — "Give me a high-level overview of how this project is structured."
3. **Guess and check** — "This file looks like it handles user sessions. Is that right?" (When you're wrong, the correction teaches more than a straight explanation.)
4. **Trace user actions** — "Walk me through what happens in the code when a user clicks 'Buy Now.'" (Stories are easier to remember than abstract descriptions.)
5. **Goal-focused exploration** — "I need to change how the welcome email is formatted. What parts do I need to understand?"

### Git as Save Points

Think of git commits like video game checkpoints:

| Video Game | Git | What It Does |
|---|---|---|
| Save point | Commit | Records your files at a specific moment |
| Multiple save slots | Branches | Parallel timelines for safe experiments |
| Loading an old save | Checkout | Returns files to a previous state |

Commit when you've completed a meaningful unit of work. More commits are better than fewer — same instinct as saving before entering unknown territory.

**Key prompts:**
- "Save this progress" → commit
- "I want to try a different approach. Create a branch" → experiment safely
- "This didn't work. Go back to main" → abandon safely

### Prototyping: Describe-Refine-Iterate

Every prototype should demonstrate **one thing** clearly. If you're demonstrating multiple things, you have multiple prototypes.

**The conversation pattern:**
1. **Start broad:** "Build me a simple page that shows a list of tasks"
2. **Refine:** "The add button is too small — make it more prominent"
3. **Continue:** "Now add the ability to mark tasks as complete"

Each cycle teaches you something. You're learning by seeing and reacting, not by specifying everything upfront.

**Write an exclusion list BEFORE starting:**
```
This prototype will NOT:
- Connect to real data
- Handle error cases
- Work on mobile
- Include authentication
```

This list protects you from scope creep.

---

## Part 4: Understanding Enough to Validate

You don't need to write code, but you need to recognize problems.

### The Top 5 Bug Categories (What to Watch For)

| Category | How to Spot It | What to Tell Claude |
|----------|----------------|---------------------|
| **Coordinate mismatch** | Positions are wrong, crops are off | "Are you mixing points and pixels? Document the coordinate system." |
| **UI doesn't update** | Changes don't appear | "Is @Observable detecting the mutation? Are you mutating nested properties?" |
| **Race condition** | Intermittent bugs, crashes | "Is this thread-safe? Should this be an actor?" |
| **Silent failure** | Features don't work, no error | "Are you swallowing errors with try? Add proper error handling." |
| **Persistence bug** | Data lost on restart | "Is the save actually happening? Add logging to verify." |

### Red Flags in Code Review

When Claude shows you code, watch for:

| Red Flag | Why It's Bad |
|----------|--------------|
| `try?` everywhere | Errors are silently ignored |
| `@unchecked Sendable` | Threading safety bypassed |
| `force unwrap (!)` | Will crash on nil |
| No error handling in async | Failures disappear |
| 500+ line files | Too complex, hard to maintain |
| Multiple TODO files | Confusion, no clear priority |

### Questions to Ask Claude

When reviewing implementation:

1. "What happens if this fails?" (error handling)
2. "Is this thread-safe?" (concurrency)
3. "Will this survive app restart?" (persistence)
4. "What happens with empty input?" (edge cases)
5. "Where is the state stored?" (architecture)

---

*This guide will evolve. When you learn something the hard way, add it.*
