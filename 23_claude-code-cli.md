<!--
TRIGGERS: claude command, CLI, MCP, hooks, slash command, permissions, keyboard shortcut
PHASE: any
LOAD: sections
-->

# Claude Code Reference

*Reference for Claude Code CLI features, commands, and configuration.*

---

## Quick Start

```bash
# Install
npm install -g @anthropic-ai/claude-code

# Verify
claude --version

# Start
claude
```

---

## Essential Commands

### Session Management

| Command | Description |
|---------|-------------|
| `/clear` | Reset conversation history |
| `claude -c` | Resume the most recent conversation (a CLI flag — run from the shell, not a slash command) |
| `/resume [sessionId]` | Resume a specific session — from inside a running session |
| `/compact` | Summarize and compress context |

There is no `/continue` slash command. To pick up your last conversation, run `claude -c` from the shell; to switch to a named/older session while already in a session, use `/resume`.

### Configuration

| Command | Description |
|---------|-------------|
| `/config` | Interactive settings wizard |
| `/model` | Switch between available models |
| `/memory` | Edit CLAUDE.md project guidelines |
| `/cost` | Display token usage and billing |

### Tools & Integration

| Command | Description |
|---------|-------------|
| `/mcp` | Manage Model Context Protocol servers |
| `/agents` | Configure specialized sub-agents |
| `/doctor` | Run system diagnostics |
| `/help` | Access documentation |

### Mode Switching

| Command | Description |
|---------|-------------|
| `/plan` | Enter Claude Code's built-in planning mode |
| `Shift+Tab` (twice) | Toggle plan mode |

**Naming collision:** Directions' own custom command that *writes a plan file* to `docs/` is `/make-plan` — it was renamed specifically to avoid colliding with this built-in `/plan`. Whenever you see bare `/plan` in Claude Code (here, in `01_quick-reference.md`, or in the CLI's own UI), it always means the built-in planning mode above, never the Directions plan-file command.

---

## Keyboard Shortcuts

| Shortcut | Function |
|----------|----------|
| `Ctrl+C` | Cancel current operation |
| `Ctrl+D` | Exit session |
| `Ctrl+L` | Clear screen (preserves history) |
| `Up/Down` | Browse command history |
| `Option+Enter` (macOS) | Multiline input |
| `Shift+Enter` | Multiline input (after setup) |
| `\` + `Enter` | Escape sequence for line breaks |
| `Esc` | Cancel current input |
| `Tab` | Autocomplete |

---

## Extended Thinking

Thinking controls vary by Claude model. Current Fable, Sonnet, and Opus families use adaptive
thinking, while Haiku 4.5 retains different thinking controls. The old `think` / `think hard` /
`think harder` / `ultrathink` keyword ladder is not a durable control surface. Verify the selected
model's current controls rather than copying a fixed thinking budget.

See `60_model-selection.md` for provider-neutral selection and escalation guidance.

## Current Model Mapping

**Verified 2026-09-04.** This is a Claude-specific snapshot, not permanent Directions vocabulary.

| Workflow role | Current Claude model |
|---|---|
| Mechanical / latency-sensitive | Claude Haiku 4.5 |
| Balanced implementation | Claude Sonnet 5 |
| Deep reasoning | Claude Opus 5 |
| Highest-capability long-horizon work | Claude Fable 5 |

These roles do not imply technical equivalence with Codex models. Recheck the official
[Anthropic model status](https://docs.anthropic.com/en/docs/about-claude/model-deprecations) and model
overview before changing saved configuration.

---

## Memory Hierarchy

Claude Code uses four-tier memory (higher tiers override lower):

| Tier | Location | Scope |
|------|----------|-------|
| 1. Enterprise | `/Library/Application Support/ClaudeCode/CLAUDE.md` | Organization-wide |
| 2. User | `~/.claude/CLAUDE.md` | Personal (all projects) |
| 3. Project | `./CLAUDE.md` | Team-shared |
| 4. Local | `./CLAUDE.local.md` | Personal sandbox (not committed) |

**Recommendation:** Use `CLAUDE.md` for team rules, `CLAUDE.local.md` for personal preferences.

### Progressive Context Loading

For large projects (50K+ LOC), use the **router pattern**:
- Main CLAUDE.md as lean index (50-100 lines)
- Domain docs loaded conditionally based on task
- Nested CLAUDE.md files auto-load per directory

**See:** `52_context-management.md` — the canonical context guide (architecture, runtime, information design).

---

## Configuration Files

Global: `~/.claude.json` (`{"theme": "dark", "autoUpdates": true}` — MCP servers are configured separately, see below). Project: `.claude/settings.json`, e.g.:

```json
{
  "permissions": {
    "allow": ["Bash(git *)", "Bash(swift build)", "Bash(swift test)", "Read", "Edit", "Write"]
  }
}
```

```bash
# Set model — IDs drift as new versions ship; verify the current ID before hardcoding
claude config set model "claude-sonnet-5"
claude config set -g theme dark
claude config list
```

---

## Permission System

```bash
claude --allowedTools "Edit,Read"                    # allow specific tools
claude --allowedTools "Bash(git:*)"                  # allow scoped bash commands
claude --allowedTools "Bash(npm:*),Bash(swift:*)"    # allow pattern-matched commands
claude --dangerously-skip-permissions                # bypasses ALL safety checks — testing only, never on untrusted codebases
```

---

## MCP (Model Context Protocol)

```bash
claude mcp list              # list configured servers
claude mcp add <name> <command>
claude mcp get <name>         # inspect one server's config/status — there is no `claude mcp test`
claude mcp remove <name>
```

Configured globally in `~/.claude.json` or per-project in `.mcp.json`:

```json
{ "mcpServers": { "github": { "url": "https://api.githubcopilot.com/mcp/" } } }
```

**`@anthropic-ai/mcp-filesystem`, `@anthropic-ai/mcp-github`, and `@anthropic-ai/mcp-memory` do not exist as npm packages** — don't recommend or `npx` them. Use `claude mcp add` with the real server's install command or URL (check that server's own docs — package names shift), or inspect what's already configured with `/mcp` inside a session.

---

## Sub-Agents

Configure specialized AI assistants with isolated contexts:

```bash
claude /agents
```

Sub-agents have scoped tool access for safety. Typical roles: `planner` (architecture/planning), `codegen` (implementation), `tester`, `reviewer`, `docs` — defined as files under `.claude/agents/`.

---

## Hooks System

Execute custom scripts on Claude Code events, configured in `.claude/settings.json`:

```json
{
  "hooks": {
    "PostToolUse": [
      { "matcher": "Write", "hooks": [{ "type": "command", "command": "./scripts/format-code.sh" }] }
    ]
  }
}
```

**Events:** `PreToolUse` (before a tool executes), `PostToolUse` (after a tool completes), `Notification`, `UserPromptSubmit` (user submits a message), `Stop` (main agent finishes), `SubagentStop` (a Task subagent finishes), `PreCompact` (before context compaction), `SessionStart`, `SessionEnd`.

Hooks receive JSON via stdin with event details; `CLAUDE_PROJECT_DIR` is available as an environment variable.

### Gotcha: a `PreToolUse` guard matches the command *string*, not the intent

A guard that blocks dangerous Bash by pattern-matching the command will also fire when the
dangerous text is merely **quoted inside** an otherwise-safe command — most often when you're
*writing documentation about* the thing it blocks.

Seen 2026-08-20: two `Bash` calls were blocked as "git history rewrite" because a `python3`
heredoc writing a Markdown file happened to contain the words `filter-branch` and `filter-repo`
in its prose. Nothing would have been rewritten; the guard was reading the document body.

The tell is a block on a command whose *verb* is harmless (`python3`, `cat`, `grep`) while the
named risk sits in a quoted string. Two responses, in order:

1. **Don't reword the prose to dodge the guard** — that trains you to evade it. Use a
   non-Bash path (the `Edit`/`Write` tool) so the text never becomes a command argument.
2. **Narrow the pattern** if it recurs: anchor on an actual invocation (`git` followed by the
   subcommand at the start of a command or after `;`/`&&`/`|`) rather than the bare tool name
   anywhere in the string.

The same shape applies to any keyword guard — `rm -rf`, `DROP TABLE`, `curl | sh` — whenever
you write about them rather than run them.

---

## Output Modes

`claude` — interactive, full terminal interface with streaming. `claude -p "prompt"` — headless/print mode: a single response, then exit (this **is** headless mode; there is no separate `--headless` flag). Pipe input with `cat file.txt | claude -p "Summarize this"` or `git diff | claude -p "Review these changes"`. Add `--output-format stream-json` for structured, scriptable output.

---

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `ANTHROPIC_API_KEY` | API authentication — set via `export ANTHROPIC_API_KEY="sk-your-key"` (persist in `~/.zshrc`) |
| `ANTHROPIC_MODEL` | Override default model |
| `BASH_DEFAULT_TIMEOUT_MS` | Command timeout |
| `DISABLE_TELEMETRY` | Opt out of analytics |
| `HTTP_PROXY` / `HTTPS_PROXY` | Proxy configuration |
| `CLAUDE_PROJECT_DIR` | Project directory (in hooks) |

---

## GitHub Actions Integration

Claude Code ships a GitHub Action (`anthropics/claude-code-action`) for PR review, triage, and other CI automation. **Its input names change fairly often** — check the action's own README on GitHub for the current inputs before wiring a workflow; don't copy a hardcoded input list from here as gospel. Minimal shape:

```yaml
name: Claude Code Review
on: [pull_request]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: anthropics/claude-code-action@main
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
```

Typical uses: PR code review with inline comments, security vulnerability scanning, issue triage/labeling — the exact `mode`/`prompt`-style inputs that select these are the part most likely to have moved; verify against the action's docs.

---

## Slash Commands

Custom commands (`.claude/commands/`) are merged into the skills system — existing command files still work, but if a skill and a command share a name, the skill wins. Prefer skills for new work; legacy commands use `$ARGUMENTS` as a placeholder (`.claude/commands/debug.md` → invoked as `/project:debug the save button doesn't work`).

---

## The Skills System (SKILL.md)

Skills are reusable instruction files that capture HOW to do something well — the file IS the documentation, and they replace the old `.claude/commands/` system (which still works). SKILL.md is an open standard (spec at agentskills.io) supported across multiple tools. **The Three-Times Rule:** if you've used the same prompt or sequence three times, convert it to a skill.

### File format

```markdown
---
name: my-skill
description: What this skill does and when to use it. Claude uses this to decide
  when to auto-load the skill — put all "when to use" information here.
---
Instructions for Claude go here in regular Markdown...
```

Key frontmatter fields: `name` (becomes `/my-skill`), `description` (drives auto-invocation), `disable-model-invocation: true` (prevents auto-load — use for side-effecting actions), `user-invocable: false` (hides from `/` menu — background knowledge only), `allowed-tools`, `model`, `context: fork` (runs in a subagent).

### Where skills live (priority order, highest first)

Enterprise (managed settings) → `~/.claude/skills/<name>/SKILL.md` (personal, all projects) → `.claude/skills/<name>/SKILL.md` (project, team-shared) → plugin directories. Higher priority overrides lower; start personal, move to project when ready to share.

**Discovery:** manual via `/skill-name` (some take arguments, e.g. `/check security`), or automatic when the conversation matches the skill's `description`. Run `/status full` to check whether any skills were excluded from the description budget.

**Install:** copy a folder into a skills directory, or `/plugin marketplace add <source>` + `/plugin install <name>@<source>`.

**Anti-patterns:** skill hoarding (installing thirty, using two), trusting a skill without reading it first, vague descriptions that never auto-trigger.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Command not found | Check PATH includes npm global bin: `export PATH="$(npm config get prefix)/bin:$PATH"` |
| Verify install | `claude --version`, `claude doctor`, `which claude` |
| Clean reinstall | `npm uninstall -g @anthropic-ai/claude-code && npm install -g @anthropic-ai/claude-code` (optionally `rm -rf ~/.claude` first to drop config) |
| MCP issues | `claude mcp list` to check status, `claude mcp get <server-name>` to inspect one (there is no `claude mcp test`), `claude --debug` for logs |

---

## Security Best Practices

API keys in environment variables, never in code. Start permissions restrictive, expand as needed. Review hook scripts before enabling. Protect config files (`chmod 600 ~/.claude.json`). Use trusted MCP sources only. Add `CLAUDE.local.md` and sensitive configs to `.gitignore`.

---

## System Requirements

Runs on macOS, Linux, and Windows (native or WSL); needs a current Node.js LTS and network access. Minimum versions drift release to release — run `claude doctor` for the authoritative local compatibility check rather than trusting a pinned number here.

---

## Quick Reference Card

```
Start:          claude
Exit:           Ctrl+D
Cancel:         Ctrl+C
Clear:          /clear or Ctrl+L
Resume last:    claude -c        (CLI flag, not a slash command)
Resume named:   /resume [sessionId]
Plan mode:      Shift+Tab (twice) or /plan
Config:         /config
Help:           /help
Multi-line:     Option+Enter (macOS) or \+Enter
```

Thinking is adaptive on current models — there is no `think` / `think hard` / `ultrathink` ladder to invoke.

---

*Based on the [zebbern/claude-code-guide](https://github.com/zebbern/claude-code-guide) and official documentation. Fast-moving specifics (model IDs, Action inputs, exact system-requirement versions) should be re-verified against current docs rather than treated as pinned truth in this file.*
