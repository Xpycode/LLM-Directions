# Ideas & Task Flow

> **miniPM-style progression:** ideas/ -> specs/ -> doing/ -> done/
> Move items through phases as they progress.

---

## Ideas (Undeveloped)
<!-- Raw concepts, brainstorms, "what if" thoughts -->
<!-- Format: Brief description, date added, any initial notes -->

### [Idea Name]
**Added:** [Date]
**Type:** [Feature | Tool | Refactor | Exploration]

[Brief description of the idea]

**Initial thoughts:**
- [Note]
- [Note]

**Next step:** [What would move this to specs/]

---

## Specs (Ready to Plan)
<!-- Ideas that have been through discovery interview -->
<!-- Each should have acceptance criteria and scope defined -->

*See `specs/` folder for full spec documents*

| Spec | Status | Created |
|------|--------|---------|
| [spec-name.md] | ready | [date] |

---

## Doing (Active Work)
<!-- Currently being implemented -->
<!-- Should have IMPLEMENTATION_PLAN.md entry -->

| Feature | Plan | Started | Wave |
|---------|------|---------|------|
| [name] | IMPLEMENTATION_PLAN.md | [date] | 2/3 |

---

## Done (Completed)
<!-- Recently completed, before archiving -->

| Feature | Completed | Commits | Session |
|---------|-----------|---------|---------|
| [name] | [date] | abc123 | 2026-01-26.md |

---

## Archived
<!-- Old ideas that were dropped or superseded -->
<!-- Keep brief notes on why -->

| Idea | Reason | Date |
|------|--------|------|
| [name] | [why dropped] | [date] |

---

## Auto-Detection Triggers

When user says... | Action
------------------|--------
"I have an idea" | Create entry in Ideas section
"Let's spec this out" | Run `/interview`, create in specs/
"Let's build [X]" | Move to Doing, create/update IMPLEMENTATION_PLAN.md
"[X] is done" | Move to Done, update PROJECT_STATE.md
"Drop [X]" | Move to Archived with reason

---

## Flow Commands

| Command | Action |
|---------|--------|
| `/ideas` | List all ideas with status |
| `/ideas add [name]` | Quick-add to Ideas section |
| `/ideas promote [name]` | Run interview, move to specs/ |
| `/ideas start [name]` | Move to Doing, create plan |
| `/ideas done [name]` | Move to Done, archive |

---

*Ideas are cheap. Specs are commitment. Plans are execution.*
