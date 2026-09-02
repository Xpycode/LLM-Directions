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
- Treat Claude model markers, model hooks, tier names, and `/model` commands as Claude-only. Do not read `~/.claude/.current-model-*` or repeat suggestions such as `/model opus` or `/model sonnet` in Codex. Skip the command's model-tier check and continue unless reliable Codex session evidence is available. When model guidance is useful, express it generically in Codex terms: use a stronger available model or higher reasoning effort for difficult planning and review, a balanced setting for routine implementation, and a faster setting for narrow low-risk work. Do not claim which Codex model or reasoning effort is active unless the session exposes it reliably.
- Use the current Codex workspace as the project target unless the user names another project.
- Respect Codex sandbox and approval requirements. A command file does not grant permission beyond the user's request.
- Keep Claude Code files unchanged unless the user explicitly asks to update Directions itself.
- If a referenced Claude-only hook or state file is unavailable, use the closest reliable Codex evidence and disclose the difference briefly.
- For `/log`, infer the session's work from the conversation and repository evidence as directed by the source command. Do not invent work that Codex cannot verify.

## Invocation

Prefer the short Directions vocabulary. Treat bare slash commands and command-like requests as
invocations of this skill, for example:

`/status arrive`

`status arrive`

`log clear`

Users do not need to add `$directions`. If the Codex interface intercepts a slash command as a
built-in instead of passing it to the model, the slashless form is the reliable fallback. Continue
to accept explicit skill syntax such as `$directions /status` for compatibility.
