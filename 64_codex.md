<!--
TRIGGERS: Codex, AGENTS.md, CODEX_HOME, Codex skill, Codex setup, Codex hooks, deploy-codex,
          statusline, permissions, usage, slashless commands
PHASE: any
LOAD: full
-->

# Codex

Directions uses Codex as a first-class host without maintaining a second command library.

## Daily controls

These are Codex CLI controls, not Directions commands:

| Control | Use it for |
|---|---|
| `/usage` | Account usage activity and available reset actions |
| `/status` | Current session model, permissions, writable roots, token use, and context capacity |
| `/model` | Model selection and reasoning effort when the active model supports it |
| `/permissions` | What Codex may do without asking; tighten to read-only for inspection-only work |
| `/statusline` | Choose and reorder persistent footer fields |
| `/plan` | Ask Codex to investigate and plan before implementation |
| `/review` | Review the current working tree |
| `/compact` | Summarise a long conversation while preserving the active task |
| `/new` or `/clear` | Start fresh when changing topics or when context is polluted |
| `/fork` | Branch the current conversation to explore another approach |
| `/side` | Ask a temporary side question without disrupting the main transcript |
| `/init` | Generate an `AGENTS.md` scaffold; adapt it rather than accepting generic instructions blindly |
| `/skills` | Browse and invoke installed skills |
| `/mcp` | Inspect configured MCP tools and servers |

Codex's built-in `/status` is not the Directions `status` workflow. Use slashless `status`, `status
arrive`, or `$directions /status` when you want project state rather than CLI session state.

Official reference: [Codex CLI commands](https://learn.chatgpt.com/docs/developer-commands?surface=cli).

### Status line

For an all-day terminal workflow, start with this conceptual layout:

```text
PROJECT | GIT | MODEL/REASONING | PERMISSIONS | PRIMARY LIMIT | SECONDARY LIMIT | CONTEXT
```

Use `/statusline` to choose the exact fields exposed by the installed client. Field names and account
limits vary by release, sign-in method, and plan; keep the concept here rather than copying a fixed
`config.toml` array into the framework.

### Plan mode is not permission mode

```text
/plan or Shift+Tab
→ changes how Codex approaches the task

/permissions
→ changes what Codex is allowed to do
```

Treat the collaboration mode and permission profile as separate session state. Verify the effective
combination with `/status` when a task needs a particular safety boundary.

Official references: [permissions](https://learn.chatgpt.com/docs/permissions) and
[Codex CLI commands](https://learn.chatgpt.com/docs/developer-commands?surface=cli).

## Models and reasoning

Model capability and reasoning effort are separate controls. Follow the provider-neutral selection and
escalation rules in `60_model-selection.md`; use this section only as a current Codex mapping.

**Current mapping, verified 2026-09-04:**

| Workflow role | Current Codex model | Typical Swift work |
|---|---|---|
| Mechanical | GPT-5.6 Luna | Search, extraction, a known rename, narrow read-only inspection |
| Implementation | GPT-5.6 Terra | Normal features, tests, routine debugging and refactoring |
| Deep reasoning | GPT-5.6 Sol | Subtle SwiftUI state, concurrency, difficult debugging, migration review |
| Frontier / end-to-end | GPT-6 Astra | Large unfamiliar systems, ambiguous multi-step work, highest-risk decisions |

This table maps workflow roles, not technical equivalence with another provider. Names, availability,
defaults, and supported reasoning levels change. Verify them in the current
[Codex model guide](https://learn.chatgpt.com/docs/models) before changing saved configuration.

### Escalation

A practical starting point for ordinary Swift work is implementation capability with medium reasoning.
Move toward deeper reasoning or a stronger model only when ambiguity, coupling, correctness risk, or
failed attempts justify it:

```text
Luna + low        → clear mechanical work
Terra + medium    → ordinary implementation
Terra + high      → moderate refactor or debugging
Sol + high/xhigh  → subtle state, concurrency, architecture, or difficult review
Astra + high/xhigh → hardest sustained end-to-end work
```

Exact effort labels differ by model and surface. Use the lowest effort that produces a reliable result.
Max, when offered, gives one task more reasoning time; Ultra, when offered, is a separate parallel
subagent mode. Neither should be the habitual default.

Before escalating, check `52_context-management.md`: missing evidence, an unclear plan, or polluted
context is often the real problem.

## Architecture

| Concern | Codex home | Repository source |
|---|---|---|
| Personal, always-on guidance | `$CODEX_HOME/AGENTS.md` (default `~/.codex/AGENTS.md`) | managed block from `CODEX-GLOBAL-TEMPLATE.md` |
| Project guidance | root or nested `AGENTS.md` | project-owned; template in `12_documentation-templates.md` |
| Directions workflow | `$CODEX_HOME/skills/directions` (default `~/.codex/skills/directions`) | `codex/skills/directions/` |
| Workflow procedures | read from the master | `commands/*.md` — single source of truth |
| Universal topic routing | generated inside global `AGENTS.md` | numbered docs + `scripts/gen-directions-index.sh` |

Codex loads global and project `AGENTS.md` files as an instruction chain. Keep global guidance
personal and cross-project, root guidance repository-wide, and nested guidance specific to its
subtree. Codex skills use progressive disclosure: metadata is always cheap to discover; the full
`SKILL.md` is read only when selected.

Official references: [AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md),
[skills](https://learn.chatgpt.com/docs/build-skills), and
[customization](https://learn.chatgpt.com/docs/customization/overview).

## Install or refresh

From the Directions master:

```bash
bash deploy-codex.sh --dry-run
bash deploy-codex.sh
```

The deployer:

1. Symlinks the versioned Directions skill into the active Codex build's user skill directory,
   `$CODEX_HOME/skills/directions` (default `~/.codex/skills/directions`).
2. Renders the local master path and live Directions Index.
3. Creates or updates only the marked Directions block in `$CODEX_HOME/AGENTS.md` (default
   `~/.codex/AGENTS.md`), preserving unrelated personal instructions.
4. Backs up an existing global `AGENTS.md` before changing it.

Start a new Codex session after deployment. Codex rebuilds the `AGENTS.md` instruction chain at the
start of a run/session, and a new session also makes skill discovery unambiguous.

For routine updates, say `directions update`. The shared command checks the master worktree, pulls
with `--ff-only`, previews the active tool's deployer, and asks before changing global files.

## Invoke Directions

Use the short workflow vocabulary:

```text
status arrive
spec deep
make-plan
execute
check ship
log clear
directions update
```

Slash forms such as `/status arrive` work when the interface passes them through. If a built-in
slash command intercepts the text, use the slashless form. Explicit `$directions` invocation remains
available but is not required.

Codex custom prompts are not the Directions integration. OpenAI documents custom prompts as
deprecated in favor of skills, and a prompt-per-command layout would recreate the duplicate command
library that Directions deliberately removed.

## Tool adaptation boundary

The adapter preserves a command's outcome, safety rules, state changes, and reporting contract. It
changes only host-specific mechanics:

- Sections marked `CLAUDE-ONLY` are skipped in Codex.
- Claude model marker files and `/model opus|sonnet` reminders are never read or repeated.
- Delegation language maps to available Codex subagents only when the user or active instructions
  authorize delegation; independent work gets fresh task-specific context.
- Claude hooks and process detectors are conveniences, not sources of project truth. Codex falls
  back to repository evidence and discloses the missing automation.
- Sandbox and approval policy still applies. A Directions command never grants extra authority.

## Project setup and migration

`setup` treats `docs/PROJECT_STATE.md` as the Directions sentinel. In an existing Directions project,
it preserves state and backfills a missing root `AGENTS.md` from the project template without
overwriting `CLAUDE.md` or other instructions. This matters for projects created before Codex became
a supported host.

Do not mass-copy universal docs or the command library into consumer repositories. Project-local
files are limited to changing state and durable project facts:

- `AGENTS.md`
- `docs/PROJECT_STATE.md`
- `docs/sessions/`
- `docs/decisions.md`
- `docs/glossary.md`
- active specs and `IMPLEMENTATION_PLAN.md`

## What is intentionally not installed yet

The first Codex deployment installs guidance and the workflow skill, not lifecycle hooks. Codex has
a native hooks system, but porting the Claude session-start, prompt-suggester, collision, and stop
hooks should be a separate verified change: hook trust, event payloads, path variables, and warning
noise all need real-session testing. Until then:

- use `status arrive` for the read-only multi-Mac preflight and handoff;
- use `log` before switching projects or Macs;
- use `worktree` when parallel sessions need different branches;
- rely on the Codex status line for model/context/token visibility when configured locally.

Official reference: [Codex hooks](https://learn.chatgpt.com/docs/hooks).

## Verify and troubleshoot

```bash
test -L "${CODEX_HOME:-$HOME/.codex}/skills/directions"
test -f "${CODEX_HOME:-$HOME/.codex}/skills/directions/SKILL.md"
rg -n 'DIRECTIONS-CODEX:(START|END)' "${CODEX_HOME:-$HOME/.codex}/AGENTS.md"
```

If Directions is not discovered:

1. Confirm the skill symlink resolves to this master and contains `SKILL.md`.
2. Check `CODEX_HOME`; a non-default value means Codex is reading another global configuration.
3. Check for `~/.codex/AGENTS.override.md`, which replaces the normal global `AGENTS.md`.
4. Start a new Codex session and ask it to summarize its active instruction sources.
5. If project behavior is wrong, look for a closer nested `AGENTS.override.md` or `AGENTS.md`.

Do not solve discovery failures by copying `commands/*.md` into every app. Fix the global skill or
instruction chain so the single source remains single.

## Related

- `00_base.md` — universal Directions workflow
- `01_quick-reference.md` — compact daily reference for both supported hosts
- `52_context-management.md` — context diagnosis and recovery
- `60_model-selection.md` — provider-neutral capability and reasoning principles
- `AGENTS.md` — repository-specific Codex instructions
