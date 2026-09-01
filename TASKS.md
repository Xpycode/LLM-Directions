# Tasks

> **Persistent task tracker.** Lives in `docs/`. Progress syncs to PROJECT_STATE.md.

## Backlog
<!-- Ideas and future work. Added by /spec deep, user input, or discovered during development. -->
<!-- Priority: top = highest, bottom = lowest -->

- [ ] [Task description]

## Current Sprint
<!-- Active work. Populated by /make-plan or /execute. Keep focused (3-7 tasks). -->
<!-- When done: /log moves to tasks-archive.md -->


---

## Ideas
<!-- Undeveloped concepts, not yet scoped into a task. Optional phase tag, e.g. "(Phase 2)". -->

- [ ] [Idea description] (Phase: [phase])

---

## Progress Calculation

```
Sprint Progress = checked in Current Sprint / total in Current Sprint
Overall Progress = (archived count + checked) / (backlog + current + archived)
```

Archived task count is read from `tasks-archive.md` header.

## Workflow Integration

| Command | Action |
|---------|--------|
| `/spec deep` | Adds tasks to Backlog |
| `/make-plan` | Moves Backlog → Current Sprint |
| `/execute` | Checks off tasks as waves complete |
| `/log` | Archives checked tasks, updates PROJECT_STATE.md progress bar |
| `/status` | Reports progress from checkbox counts |

---
*Location: `docs/TASKS.md`. Parsed by Directions app.*
