---
name: directions
description: Use the shared Directions development workflow for project setup, status, specs, plans, execution, review, logs, decisions, cookbook patterns, testing, and worktrees. Trigger for slash or slashless Directions requests such as status arrive, log clear, execute, or directions update, and requests to execute or resume an approved plan in a Directions project. In Mistral Vibe, slashless forms are primary because built-in commands intercept /status and /log.
user-invocable: true
---

# Directions

Use the shared Directions command library. Do not duplicate its detailed procedures in this skill.

## Source of truth

Resolve the Directions master before acting:

1. Resolve this skill's real path. A managed install symlinks
   `<master>/.vibe/skills/directions` into a Vibe skill directory, so the master is three parents
   above this file's directory.
2. Otherwise read the `Local master:` value in the managed Directions block of
   `$VIBE_HOME/AGENTS.md` (default `~/.vibe/AGENTS.md`).
3. If neither works, use `/Users/sim/ProgrammingProjects/0-DIRECTIONS/__DIRECTIONS` only when it
   exists. If no candidate contains `commands/`, stop and ask where Directions is cloned.

For a supported command, read the corresponding Markdown file completely before acting. Treat text after the command name as its argument or mode. Examples:

- `/status arrive` -> read `commands/status.md`, then use its `arrive` mode.
- `log clear` -> read `commands/log.md`, then use its pre-clear mode.
- `status full` or a request phrased as "give me full project status" -> use `commands/status.md` when the intent clearly matches.
- "continue implementation", "execute the plan" or "next wave" in a Directions project -> read
  `commands/execute.md` and preserve the requested scope. Status/planning discussion alone does
  not authorize execution; a small standalone fix does not require wave planning.

Supported command files are discovered from that directory; do not assume this list is permanently exhaustive.

Resolve relative `reference/...`, guide and command links in shared procedures from the
resolved master root, never the consumer working directory or installed skill symlink.
Keep that absolute master path in generated project instructions so commands also work without
global instructions. Without globals, topical discovery may read the master's
`CODEX-GLOBAL-TEMPLATE.md` for its routing section only; do not install or apply unrelated
template behavior. If the master is unavailable, report it rather than using copied guides.

## Vibe adaptation

- Preserve the command's outcome, safety rules, read/write behavior, and reporting style.
- Interpret references to Claude or Claude-specific UI as equivalent Mistral Vibe behavior only
  when a reliable equivalent exists. Skip sections marked `CLAUDE-ONLY`.
- Do not read or write `~/.claude/.current-model-*` or `~/.claude/.session-phase-*`, and do not repeat
  `/model opus` or `/model sonnet` suggestions. When model guidance is useful, express it in Vibe
  terms: higher thinking for difficult planning/review, balanced settings for routine
  implementation, and a faster model for narrow low-risk work. Do not claim the active model or
  thinking level unless the session exposes it reliably.
- Apply `60_model-selection.md` -> **User-Facing Model-Fit Notice** at the workflow transitions named
  by the active command. Show it once when the recommendation changes or risk makes an upgrade
  consequential; do not repeat it while the fit is unchanged. In pre-clear or Mac-handoff mode,
  record the next action's recommended capability and reasoning in the Resume/next-session block.
- Translate generic delegation into Vibe subagents (`agents.spawn`) only when the user or active
  instructions allow delegation. Apply the execution command's authorization and fallback rules.
  Vibe subagents start with a fresh session, so supply the task packet explicitly instead of
  relying on a conversation fork. Disclose when delegation is unavailable.
- Vibe has no session-start hook event. Treat hook output as optional convenience, not workflow
  state. When the master provides `hooks/session-start.sh` and shell use is allowed, run it once
  at session start for the concurrency check; otherwise use repository evidence directly for
  status and handoff.
- Use the current Vibe working directory as the project target unless the user names another project.
- Respect Vibe tool permissions and the session agent's approval flow. A command file does not
  grant permission beyond the user's request. The user's no-desktop-control preference still applies.
- Keep tool-specific files for other agents unchanged unless the user explicitly asks to update
  Directions itself.
- For `log`, infer the session's work from the conversation and repository evidence as directed by
  the source command. Do not invent work that Vibe cannot verify.

## Invocation

Prefer the short Directions vocabulary in its slashless form:

`status arrive`

`log clear`

`directions update`

Mistral Vibe intercepts `/status` and `/log` as built-in commands, so slashless requests are the
reliable path. `/directions` has no built-in collision and loads this skill with the trailing
text as instructions. Continue to accept explicit skill syntax for compatibility.
