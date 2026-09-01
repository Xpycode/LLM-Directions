# Codex Instructions for Directions

## Repository

- Directions is a documentation-first development framework for Swift/SwiftUI, macOS, iOS, and web projects.
- The repository contains shared guidance, workflow commands, templates, a pattern cookbook, and thin tool adapters. It is not itself a Swift package or application.
- Most changes are Markdown or shell-script changes. Determine validation from the files touched; do not default to `swift build`, `swiftlint`, or `swift test` in this repository.

## Instruction Ownership

- `AGENTS.md` is the Codex entry point. `CLAUDE.md` or `CLAUDE-GLOBAL-TEMPLATE.md` is the Claude Code entry point.
- Keep stable project facts such as stack, commands, and safety constraints aligned between tool entry points when both exist.
- Keep tool-specific behavior in its own entry point. Do not require line-for-line parity.
- Changing state belongs in `PROJECT_STATE.md`, `IMPLEMENTATION_PLAN.md`, specs, decisions, and session logs—not in an agent entry point.

## Directions Workflow

- `commands/*.md` is the single procedural source of truth for Directions commands.
- In Codex, use the `directions` skill and study the matching command file completely before acting.
- Treat bare Directions requests such as `/status arrive`, `status arrive`, and `log clear` as skill
  invocations; users do not need to prefix them with `$directions`.
- The thin adapter lives at `codex/skills/directions/SKILL.md`. Do not create translated or duplicated Codex command files.
- Interpret Claude-specific UI, hooks, and state as Codex equivalents only when a reliable equivalent exists; disclose any fallback.

## Working Rules

- Study relevant files and check existing behavior before proposing or implementing something; don't assume it is missing.
- Preserve user changes in a dirty worktree. Keep edits scoped and inspect overlapping diffs before modifying a file.
- Use `rg` or `rg --files` for discovery.
- Use `apply_patch` for hand edits. Do not use destructive Git commands.
- Keep universal guidance in this master repository and read it on demand; do not copy it into consumer projects.
- This is a solo-developer workflow: use small direct commits or local branches when requested; do not introduce pull-request ceremony.

## Validation

Run checks appropriate to the change, in this order where applicable:

```bash
rg -n '<relevant-pattern>' <touched-files>
bash -n <touched-script>
git diff --check
git status --short
```

Do not claim a build or test passed unless this repository actually provides and ran that command.

## Known Gotchas

- `CLAUDE-GLOBAL-TEMPLATE.md` is rendered and deployed to a machine-local Claude configuration; edit the template, not the deployed copy.
- The Codex adapter intentionally reads the live Claude command library so both tools share one workflow source.
- Universal docs are read on demand. Copies in consumer projects drift and must not be reintroduced.
- Several files may already be modified by Syncthing or another session; unrelated changes belong to the user.
