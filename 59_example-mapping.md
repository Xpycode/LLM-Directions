<!--
TRIGGERS: example mapping, discovery, requirements, edge cases, rules, complex feature
PHASE: define
LOAD: on-request
-->

# Example Mapping

**Discover requirements through concrete examples.**

*Adapted from the Example Mapping technique used in BDD and fspec.*

---

## What Is Example Mapping?

A structured discovery technique that uses concrete examples to:
- Uncover hidden requirements
- Find edge cases before they become bugs
- Clarify rules and business logic
- Surface questions early

Instead of abstract discussions, you work with specific scenarios.

---

## The Example Mapping Structure

```
┌─────────────────────────────────────────────────────┐
│                    STORY (Yellow)                    │
│            "User can reset password"                 │
└─────────────────────────────────────────────────────┘
        │                    │                    │
        ▼                    ▼                    ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│  RULE (Blue)  │  │  RULE (Blue)  │  │  RULE (Blue)  │
│ Must have     │  │ Link expires  │  │ Can't reuse   │
│ valid email   │  │ after 1 hour  │  │ old password  │
└───────────────┘  └───────────────┘  └───────────────┘
        │                    │                    │
        ▼                    ▼                    ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│EXAMPLE (Green)│  │EXAMPLE (Green)│  │EXAMPLE (Green)│
│ Valid email   │  │ Click link    │  │ Enter old pw  │
│ → sends link  │  │ at 59 min     │  │ → rejected    │
│               │  │ → works       │  │               │
├───────────────┤  ├───────────────┤  └───────────────┘
│EXAMPLE (Green)│  │EXAMPLE (Green)│
│ Unregistered  │  │ Click link    │
│ email → error │  │ at 61 min     │
│               │  │ → expired     │
└───────────────┘  └───────────────┘

┌───────────────────────────────────────────────────────┐
│                   QUESTIONS (Red)                      │
│ - What if user requests multiple reset links?         │
│ - Do we invalidate old links when new one is sent?    │
│ - How many reset attempts before lockout?             │
└───────────────────────────────────────────────────────┘
```

---

## The Four Colors

| Color | Represents | Purpose |
|-------|------------|---------|
| **Yellow** | Story | The feature being explored |
| **Blue** | Rules | Business logic and constraints |
| **Green** | Examples | Concrete scenarios for each rule |
| **Red** | Questions | Unknowns to resolve |

---

## How to Run Example Mapping

### Step 1: State the Story (2 min)

Write the feature as a user story or simple statement:

```
"As a user, I want to reset my password so I can regain access to my account."
```

### Step 2: Identify Rules (5-10 min)

Ask: "What rules govern this feature?"

Each rule becomes a blue card:
- "User must have a registered email"
- "Reset link expires after 1 hour"
- "Cannot reuse last 3 passwords"
- "Must include uppercase, lowercase, number"

### Step 3: Find Examples for Each Rule (10-15 min)

For each rule, ask: "Give me an example of this rule in action."

Then ask: "What about [edge case]?"

```
Rule: "User must have registered email"
├── Example: Valid email → receives reset link
├── Example: Unregistered email → "Email not found" message
├── Example: Malformed email → validation error
└── Example: Empty email → "Email required" error
```

### Step 4: Capture Questions (ongoing)

When something is unclear, write it as a red card:

- "Do we tell the user if email isn't registered?" (security vs UX)
- "What's the minimum password length?"
- "Rate limit on reset requests?"

---

## Example Mapping in Practice

### The Session Flow

```
1. Write story on yellow card (or header)
2. Someone proposes a rule → blue card
3. Team generates examples → green cards under the rule
4. Questions arise → red cards (park them, don't solve now)
5. Repeat until rules are covered
6. Review questions → resolve or mark as blockers
```

### Time Limits

| Story Complexity | Session Length |
|------------------|----------------|
| Simple feature | 15-20 minutes |
| Medium feature | 25-30 minutes |
| Complex feature | 30-45 minutes |

If taking longer → story might be too big. Split it.

---

## Converting to Acceptance Criteria

After example mapping, examples become Given/When/Then:

### From Example Map

```
Rule: Reset link expires after 1 hour
Example: Click at 59 min → works
Example: Click at 61 min → expired
```

### To Acceptance Criteria

```gherkin
Given user requested password reset 59 minutes ago
When user clicks reset link
Then password reset form is displayed

Given user requested password reset 61 minutes ago
When user clicks reset link
Then "Link expired" message is displayed
  And "Request new link" button is shown
```

---

## Solo Example Mapping (For AI Sessions)

When working alone with Claude:

### Step 1: State the Feature

```
"I want to build [feature]. Let's map out the examples."
```

### Step 2: Ask for Rules

```
"What rules or constraints should govern this feature?"
```

### Step 3: Generate Examples

For each rule:
```
"Give me 3-4 examples of how this rule plays out, including edge cases."
```

### Step 4: Challenge

```
"What edge cases or failure scenarios am I missing?"
```

### Step 5: Surface Questions

```
"What decisions do I need to make before implementing this?"
```

---

## Integration with /interview

Example mapping can enhance Phase 2 (Explore):

```markdown
## Phase 2.5: Example Mapping (Optional, for complex features)

After core questions, if feature has complex business logic:

1. State the feature as a story
2. Ask: "What rules govern this?"
3. For each rule, generate examples:
   - Happy path
   - Edge cases
   - Error cases
4. Capture questions
5. Resolve questions or mark as blockers

Output: Examples become acceptance criteria in spec.
```

---

## Signs You Need Example Mapping

| Signal | Why It Helps |
|--------|--------------|
| "It depends" answers | Examples make conditions explicit |
| Disagreement on behavior | Concrete scenarios reveal assumptions |
| Complex business rules | Rules + examples = clarity |
| Fear of edge cases | Systematic discovery before code |
| Vague requirements | Examples force specificity |

---

## Example Mapping Template

```markdown
# Example Map: [Feature Name]

## Story
[As a user, I want...]

## Rules & Examples

### Rule 1: [Rule description]
- Example: [Scenario] → [Outcome]
- Example: [Scenario] → [Outcome]
- Example: [Edge case] → [Outcome]

### Rule 2: [Rule description]
- Example: [Scenario] → [Outcome]
- Example: [Scenario] → [Outcome]

### Rule 3: [Rule description]
- Example: [Scenario] → [Outcome]

## Questions
- [ ] [Unresolved question]
- [x] [Resolved question] → [Answer]

## Notes
[Additional context or decisions made]
```

---

## Anti-Patterns

| Anti-Pattern | Problem | Fix |
|--------------|---------|-----|
| **Abstract rules only** | No concrete examples | Force "give me a specific example" |
| **Solving during mapping** | Gets derailed into design | Park questions, stay in discovery |
| **Too few examples** | Misses edge cases | Ask "what if [unusual input]?" |
| **No questions** | False confidence | Actively look for unknowns |
| **Giant story** | Takes forever | Split into smaller stories |

---

*Concrete examples reveal what abstract requirements hide.*
