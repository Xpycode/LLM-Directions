# Directions repository

Directions is a documentation-first framework. Procedures live in `commands/*.md`; changing
state belongs in project state, plans and logs. Keep durable guidance in entry points. Preserve
dirty work; inspect overlapping diffs before editing. Use `apply_patch` for hand edits. Read
universal guidance here, never copy it to consumers. Validate Markdown/shell changes with relevant
searches, shell syntax and diff checks, not Swift builds. Prefer requested direct commits over PRs.

Without globals, resolve this repository's root as the master. Read `commands/<name>.md`
completely for slashless/slash commands; approved plan continuation and “next wave” use
`commands/execute.md`. For topical guidance read only the routing section of
`CLAUDE-GLOBAL-TEMPLATE.md`. Resolve `reference/...` from the master root, not a consumer
directory. Report missing guidance instead of substituting copied guides. Preserve explicit
scope/no-agent/no-commit limits. Do not remotely control apps without explicit permission or
expose secrets. Before multi-Mac recovery read `37_multi-mac-discipline.md`; UI changes require
`36_ui-changes-protocol.md` and `47_project-ui-conventions.md`.

Edit global templates, not deployed copies. Codex preserves personal text outside its managed
block; Claude backs up and replaces its global file. Preserve unrelated Syncthing/session changes.
Align stable facts and safety with `AGENTS.md`; retain host-specific behavior separately.
