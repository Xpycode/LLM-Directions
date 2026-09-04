---
name: directions
description: Use the shared Directions development workflow for project setup, status, specs, plans, execution, review, logs, decisions, cookbook patterns, testing, and worktrees. Trigger for slash or slashless Directions requests such as /status arrive, log clear, /execute, or /directions update.
---

# Directions

Use the shared Directions command library. Do not duplicate its detailed procedures in this skill.

## Source of truth

Resolve the Directions master before acting:

1. Resolve this skill's real path. A managed install symlinks
   `<master>/codex/skills/directions` into the user skill directory, so the master is three parents
   above this file's directory.
2. Otherwise read the `Local master:` value in the managed Directions block of
   `$CODEX_HOME/AGENTS.md` (default `~/.codex/AGENTS.md`).
3. If neither works, use `/Users/sim/ProgrammingProjects/0-DIRECTIONS/__DIRECTIONS` only when it
   exists. If no candidate contains `commands/`, stop and ask where Directions is cloned.

For a supported command, read the corresponding Markdown file completely before acting. Treat text after the command name as its argument or mode. Examples:

- `/status arrive` -> read `commands/status.md`, then use its `arrive` mode.
- `/log clear` -> read `commands/log.md`, then use its pre-clear mode.
- `status full` or a request phrased as “give me full project status” -> use `commands/status.md` when the intent clearly matches.

Supported command files are discovered from that directory; do not assume this list is permanently exhaustive.

## Codex adaptation

- Preserve the command's outcome, safety rules, read/write behavior, and reporting style.
- Interpret references to Claude or Claude-specific UI as the equivalent current Codex behavior only
  when a reliable equivalent exists. Skip sections marked `CLAUDE-ONLY`.
- Do not read or write `~/.claude/.current-model-*` or `~/.claude/.session-phase-*`, and do not repeat
  `/model opus` or `/model sonnet` suggestions. When model guidance is useful, express it in Codex
  terms: higher reasoning for difficult planning/review, balanced settings for routine
  implementation, and a faster model for narrow low-risk work. Do not claim the active setting
  unless the session exposes it reliably.
- Apply `60_model-selection.md` → **User-Facing Model-Fit Notice** at the workflow transitions named
  by the active command. Show it once when the recommendation changes or risk makes an upgrade
  consequential; do not repeat it while the fit is unchanged. In pre-clear or Mac-handoff mode,
  record the next action's recommended capability and reasoning in the Resume/next-session block.
- Translate generic delegation into Codex subagents only when the user or active instructions allow
  delegation. Preserve wave dependencies; use fresh task-specific context for independent work.
- Treat Claude hook output as optional convenience, not workflow state. For status and handoff, use
  repository evidence directly when a Claude-only hook or process detector is unavailable.
- Use the current Codex workspace as the project target unless the user names another project.
- Respect Codex sandbox and approval requirements. A command file does not grant permission beyond the user's request.
- Keep tool-specific files for other agents unchanged unless the user explicitly asks to update
  Directions itself.
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
