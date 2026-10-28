# Project Setup

First distinguish a new commitment from adding Directions to existing work. For a genuinely new
project, even with draft notes or a README already present, follow `commands/spec.md` → **New-project
assessment** before any setup writes and honor its selected route. Reuse prior decisions; adopting
Directions for existing work does not reopen them. Then detect files for the selected setup below.

Run the project detection flow (this file is the full flow; global tool instructions carry only
the sentinel check and route here):

1. Check if `docs/PROJECT_STATE.md` exists (Directions already set up) → preserve it, then ensure the
   active tool's project entry point exists. In Codex, create a missing root `AGENTS.md` from the
   master template; in Claude Code, create a missing root `CLAUDE.md`. Never overwrite an existing
   entry point. Report what was added, then report status.
2. Check if `/docs` folder exists without Directions structure, or scattered `.md` files → **Existing docs** (below)
3. Existing implementation without those docs → scaffold only the project-specific Directions
   files below using inspected context; ask only for documentation gaps. Missing Directions files
   do not make existing work a new commitment. Preserve code/layout and skip the new-project assessment.
4. Otherwise → **New project** (below)

## Existing docs: migrate or skip

Offer two options:
> "Found existing documentation. How should I proceed?
> 1. **Migrate** (recommended) - Back up to /old-docs, set up Directions in /docs, extract useful info
> 2. **Skip** - Don't set up Directions, just work with what's here"

If they choose Migrate:
- Create git commit: "Pre-Directions backup"
- Move existing /docs (or scattered .md files except README.md) to `/old-docs`
- Set up Directions in `/docs` (scaffold list below)
- Read `/old-docs` and extract into the new files:

| Look For | Extract To |
|----------|------------|
| Project description, goals | PROJECT_STATE.md |
| Technical decisions, "we chose X" | decisions.md |
| Architecture notes, stable project rules | Keep aligned in CLAUDE.md and AGENTS.md |
| TODOs, plans, phases | PROJECT_STATE.md current focus |
| Bug notes, issues found | Session log or debugging notes |
| API docs, specs | Keep in /old-docs for reference |

- After extraction, run a **gap interview**:
> "I've read your existing docs. Here's what I found: [summary].
> I still need to understand: [list gaps].
> Can we fill these in?"

## New project

Before scaffolding, read `commands/spec.md` and follow **New-project assessment**, reusing answers
and choices already supplied. Honor its route: use existing or park ends setup; improve existing
returns to that project; an experiment gets only its bounded setup. For build now, continue discovery
and set up Directions within the user's authorized scope; ask about setup only if not already requested.
Carry the conclusion into the existing spec fields and scaffold below only for the selected scope.
Read `00_base.md` on demand for the system overview. After actual project setup, finish with:
> "✓ **Setup complete!** Your project is ready.
>
> **Quick start:**
> - `/status` - See current focus
> - `/log` - Start your first session log
> - Or just tell me what you want to build!"

## Read-on-demand, do NOT copy the universal docs

The numbered universal guidance docs (gotchas, checklists, templates, references) are the **single
source of truth in the Directions master repo** and are read **on demand** via the generated
**Directions Index** in the active tool's global instructions (`$CODEX_HOME/AGENTS.md`, default
`~/.codex/AGENTS.md`, for Codex; `~/.claude/CLAUDE.md` for Claude Code). **Do not copy them into the
project.** Copies drift — an
already-set-up project never receives new house-style — which is exactly the flaw this avoids.

`/setup` scaffolds **only project-specific files** (read the matching master template on demand):
- `CLAUDE.md` — Claude Code project instructions, when Claude Code is in use; preserve an existing file
- `AGENTS.md` — Codex project instructions, when Codex is in use; preserve an existing file
- `docs/PROJECT_STATE.md` — position digest and setup sentinel: Identity, Now (Focus/Next/Execution),
  Recent, and a Current handoff link. Do not copy the master's live project history or deferred work.
- `docs/sessions/_index.md` — session history index
- `docs/decisions.md` — this project's decision log
- `docs/glossary.md` — *project-specific* terms only (the personal glossary lives globally)
- `docs/TASKS.md` — Active plan link, Backlog and Inbox; no duplicate plan checkboxes or copied master tasks

Use the master `reference/task-state.md` contract. The selected plan owns tasks/gates/evidence;
state selects it and one current handoff. Existing projects keep legacy records until scoped
preservation/reconciliation; setup is not permission to bulk-migrate other projects.

Use the entry-point templates in `12_documentation-templates.md`. Keep stable project facts aligned
between them, but keep tool-specific behavior separate. The live `commands/*.md` library remains the
single workflow source: Claude Code invokes its deployed command adapter and Codex reaches the live
files through the Directions skill. Do not copy or translate the command files into the project.
Write the resolved **absolute** `Local master:` path into generated project entry points; never leave
a placeholder or rely on global installation. Without globals, resolve natural/slashless commands
to that master's `commands/<name>.md`; topical guidance uses the appropriate master
`CODEX-GLOBAL-TEMPLATE.md` or `CLAUDE-GLOBAL-TEMPLATE.md` for routing only, without installing it.
Resolve conditional `reference/…` paths from that same verified master, not the consumer directory.
If the master is unavailable, report the missing guidance rather than using stale local mirrors.

**For a selected new build:** after discovery, create the project folder structure (read
`13_folder-structure.md` from the master on demand). A bounded experiment gets only the structure it
needs; use-existing/park outcomes get none. The actual code lives in `01_Project/` (the one exception
is framework web apps — code at repo root):
- macOS/iOS: `01_Project/`, `02_Design/Exports/`, `03_Screenshots/`, `04_Exports/`
- Web (no-build/Strato): `01_Project/` (code + lftp deploy stage), `02_Design/`, `03_Scripts/migrations/`, `04_Data/`
- Web (framework/Vercel): scaffold the framework at the repo root, add `02_Design/`, `03_Scripts/`, `04_Data/` alongside
- Create `.gitignore` using the comprehensive template from `13_folder-structure.md`
- **`git init` at the project root** (never inside `01_Project/`), then make the initial commit — see `32_git-workflow.md` → "Where the Repo Lives"

This is a **solo developer** workflow: branch → commit → merge to `main` locally. Do **not** open pull requests or suggest a PR-based flow.

Execute the detection now and guide me through setup.
