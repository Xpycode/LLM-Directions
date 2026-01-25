# Agents Configuration

> **Loaded by subagents every iteration.** Keep this tight - every token counts.
> This file captures operational learnings, not project requirements (those go in specs/).

## Project Context
<!-- Minimal context for subagents. 5-10 lines max. -->
- **Stack:** [Swift/SwiftUI | TypeScript/React | etc.]
- **Build:** `[build command]`
- **Test:** `[test command]`
- **Lint:** `[lint command]`

## Backpressure Commands
<!-- Run these to validate work. Order matters. -->
```bash
# 1. Type check / compile
swift build

# 2. Lint
swiftlint

# 3. Unit tests
swift test

# 4. Integration tests (if applicable)
# [command]
```

## Code Patterns
<!-- Project-specific patterns subagents should follow -->

### Do
- Use `async/await` for all network calls
- Services are `actor` types, not `class`
- Error handling with `Result` type, not `try?`

### Don't
- No force unwraps without nil checks
- No `@unchecked Sendable` without justification
- No files over 500 lines

## Naming Conventions
- ViewModels: `[Feature]ViewModel`
- Services: `[Domain]Service`
- Views: `[Feature]View`

## Known Gotchas
<!-- Things that have bitten us before -->
- Image coordinates use bottom-left origin on macOS
- `@Published` updates must happen on main thread
- [Add as discovered]

## LLM-Specific Notes
<!-- Steering language that works -->
- Say "Study the file" not "Read the file" - triggers deeper comprehension
- Say "Don't assume not implemented" - prevents duplicate work
- Say "Using parallel subagents" for fan-out
- Say "Only 1 subagent for build/tests" to serialize validation

---
*Updated when patterns emerge. Subagents inherit this context each iteration.*
