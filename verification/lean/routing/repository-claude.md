# Directions repository

Directions is a documentation-first framework, not an application. Use `commands/*.md` as the procedural source. Preserve dirty changes; inspect overlapping diffs before editing. Validate Markdown and shell changes with relevant searches, shell syntax checks and diff checks; do not default to Swift builds. Keep universal guidance in the master and changing state in project state, plans and logs. Do not remotely control apps without explicit permission. Do not expose secrets. For UI work read the master UI constraints; for multi-Mac recovery read `37_multi-mac-discipline.md` before reconciliation.

## Standalone Directions discovery

Master: `[LOCAL_DIRECTIONS_PATH]`. If global instructions are absent, use the master `commands/<name>.md` for slash or slashless Directions commands. Execute/resume an approved plan, “continue implementation”, and “next wave” use `commands/execute.md`; honor explicit scope/no-agent/no-commit limits. For topical guidance read the master `CODEX-GLOBAL-TEMPLATE.md` (Codex) or `CLAUDE-GLOBAL-TEMPLATE.md` (Claude), applying its routing only; do not install it. Missing master: report unavailable guidance; do not substitute stale consumer copies.
