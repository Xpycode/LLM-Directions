---
name: directions
description: Use the user's shared Directions development workflow, including requests written as /log, /status, /check, /cookbook, /decide, /directions, /execute, /learned, /make-plan, /setup, /spec, /test-app, or /worktree. Apply these workflows in Codex while keeping the existing Claude Code command files as the source of truth.
---

# Directions

Use the existing Directions command library shared with Claude Code. Do not duplicate its detailed procedures in this skill.

## Source of truth

The command files live at:

`/Users/sim/ProgrammingProjects/0-DIRECTIONS/__DIRECTIONS/commands/`

For a supported command, read the corresponding Markdown file completely before acting. Treat text after the command name as its argument or mode. Examples:

- `/status arrive` -> read `commands/status.md`, then use its `arrive` mode.
- `/log clear` -> read `commands/log.md`, then use its pre-clear mode.
- `status full` or a request phrased as “give me full project status” -> use `commands/status.md` when the intent clearly matches.

Supported command files are discovered from that directory; do not assume this list is permanently exhaustive.

## Codex adaptation

- Preserve the command's outcome, safety rules, read/write behavior, and reporting style.
- Interpret references to “Claude” or Claude-specific UI as the equivalent current Codex session behavior when an equivalent exists.
- Use the current Codex workspace as the project target unless the user names another project.
- Respect Codex sandbox and approval requirements. A command file does not grant permission beyond the user's request.
- Keep Claude Code files unchanged unless the user explicitly asks to update Directions itself.
- If a referenced Claude-only hook or state file is unavailable, use the closest reliable Codex evidence and disclose the difference briefly.
- For `/log`, infer the session's work from the conversation and repository evidence as directed by the source command. Do not invent work that Codex cannot verify.

## Invocation

Codex skills use `$directions`. Accept the original slash command inside the invocation, for example:

`$directions /status`

`$directions /log clear`

If the interface passes a bare supported slash command through to the model, handle it identically.
