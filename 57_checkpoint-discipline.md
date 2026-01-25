<!--
TRIGGERS: checkpoint, git snapshot, rollback, save point, phase transition, safe state
PHASE: any
LOAD: on-request
-->

# Checkpoint Discipline

**Create safe rollback points at every phase transition.**

*Adapted from the fspec checkpoint system for safe experimentation.*

---

## Why Checkpoints?

| Without Checkpoints | With Checkpoints |
|--------------------|------------------|
| "We broke something, where was it working?" | "Roll back to last green state" |
| Fear of experimentation | Safe to try and fail |
| Can't undo bad decisions | Restore to before the decision |
| Lost good state during debugging | Tagged states always accessible |

---

## The Checkpoint Model

```
WORKING STATE ──checkpoint──> EXPERIMENT ──success──> NEW WORKING STATE
                                  │
                                  └──failure──> ROLLBACK TO CHECKPOINT
```

A checkpoint is a Git tag marking a known-good state.

---

## When to Checkpoint

### Mandatory Checkpoints

Create a checkpoint before:

| Transition | Why | Tag Name |
|------------|-----|----------|
| **Phase change** | Define→Plan→Build transitions | `phase/define-complete` |
| **Architecture decision** | Before committing to approach | `decision/before-[name]` |
| **Risky refactor** | Might break things | `safe/before-refactor` |
| **Merge to main** | Last known-good state | `release/v0.x.x` |
| **External integration** | Adding dependencies | `safe/before-[integration]` |

### Optional Checkpoints

Consider checkpoints at:

- End of each wave in IMPLEMENTATION_PLAN.md
- Before experimental features
- Before deleting significant code
- Before changing build configuration

---

## How to Checkpoint

### Basic Checkpoint (Tag)

```bash
# Create lightweight tag at current commit
git tag checkpoint/[name]

# Example: before starting plan phase
git tag phase/define-complete

# Example: before risky change
git tag safe/before-auth-refactor
```

### Annotated Checkpoint (With Context)

```bash
# Create annotated tag with message
git tag -a checkpoint/[name] -m "Description of state"

# Example
git tag -a phase/define-complete -m "Spec approved, ready for planning"
```

### List Checkpoints

```bash
# See all checkpoints
git tag -l "checkpoint/*"
git tag -l "phase/*"
git tag -l "safe/*"
```

---

## Rolling Back

### View Checkpoint State

```bash
# See what changed since checkpoint
git diff checkpoint/[name]

# View files at checkpoint
git show checkpoint/[name]:path/to/file
```

### Full Rollback

```bash
# Create new branch from checkpoint (safe)
git checkout -b recovery checkpoint/[name]

# Or reset current branch (destructive)
git reset --hard checkpoint/[name]
```

### Partial Rollback

```bash
# Restore specific file from checkpoint
git checkout checkpoint/[name] -- path/to/file
```

---

## Checkpoint Naming Convention

```
[category]/[description]

Categories:
- phase/     → Phase transitions
- safe/      → Before risky operations
- decision/  → Before architecture decisions
- wave/      → After implementation waves
- release/   → Release candidates
```

### Examples

```
phase/define-complete
phase/plan-approved
safe/before-database-migration
safe/before-auth-rewrite
decision/before-switching-to-coredata
wave/1-models-complete
wave/2-views-complete
release/v0.1.0-rc1
```

---

## Integration with Directions Workflow

### Phase Transitions

```
/interview complete
    └── git tag phase/define-complete

/plan complete
    └── git tag phase/plan-approved

/execute wave 1 complete
    └── git tag wave/1-complete

/review passes
    └── git tag release/v0.x.x-rc1
```

### With IMPLEMENTATION_PLAN.md

Add to wave completion:

```markdown
## Wave 1: Data Models
- [x] Task 1.1
- [x] Task 1.2
- [x] Task 1.3
**Checkpoint:** `wave/1-models` created
```

### In SESSION_LOG

```markdown
## Session Progress

### 14:30 - Completed Wave 1
- All model tasks done
- Tests passing
- Created checkpoint: `wave/1-models`

### 15:45 - Auth refactor started
- Created checkpoint: `safe/before-auth-refactor`
- Starting experimental approach
```

---

## Checkpoint Commands

Add to your workflow:

```bash
# Checkpoint before phase transition
alias phase-checkpoint='git tag -a phase/$(date +%Y%m%d)-$1'

# Quick safety checkpoint
alias safe-checkpoint='git tag safe/before-$(date +%Y%m%d-%H%M)'

# List recent checkpoints
alias checkpoints='git tag -l --sort=-creatordate | head -10'
```

---

## Recovery Patterns

### "Something broke, not sure when"

```bash
# List checkpoints in order
git tag -l "safe/*" --sort=-creatordate

# Binary search: is it broken at this checkpoint?
git stash
git checkout checkpoint/[name]
# Test...
git checkout -  # Return to current
git stash pop
```

### "This approach isn't working"

```bash
# Return to pre-decision state
git checkout -b alternative decision/before-[name]
# Try different approach
```

### "Need to undo last wave"

```bash
# Compare current to wave checkpoint
git diff wave/[n-1]-complete

# If bad, reset to previous wave
git reset --hard wave/[n-1]-complete
```

---

## Cleanup Old Checkpoints

Keep checkpoints meaningful:

```bash
# Delete old safe/ checkpoints (keep last 5)
git tag -l "safe/*" --sort=creatordate | head -n -5 | xargs git tag -d

# Keep all phase/ and release/ checkpoints
# They document project history
```

---

## Claude Instructions

Add to CLAUDE.md:

```markdown
## Checkpoint Discipline

Before these actions, create a checkpoint:
- Phase transitions (define→plan→build)
- Architecture decisions
- Risky refactors
- Deleting significant code

Use: git tag [category]/[description]

If something breaks, we can always roll back.
```

---

*The best time to create a checkpoint is before you need it.*
