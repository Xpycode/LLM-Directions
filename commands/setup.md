# Project Setup

Run the project detection flow (this file is the full flow — the global CLAUDE.md's "Project
Detection" section deliberately carries only the sentinel check and points here):

1. Check if `docs/PROJECT_STATE.md` exists (Directions already set up) → report status, done.
2. Check if `/docs` folder exists without Directions structure, or scattered `.md` files → **Existing docs** (below)
3. Otherwise → **New project** (below)

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

> "This looks like a new project. What are you building? (One sentence is fine - I'll ask follow-up questions.)"

Then offer to set up Directions; if yes, scaffold (below), run the discovery interview (read
`00_base.md` from the master on demand for the system overview), and finish with:
> "✓ **Setup complete!** Your project is ready.
>
> **Quick start:**
> - `/status` - See current focus
> - `/log` - Start your first session log
> - Or just tell me what you want to build!"

## Read-on-demand, do NOT copy the universal docs

The universal guidance docs (`00`–`61`: gotchas, checklists, templates, references) are the **single
source of truth in the Directions master repo** and are read **on demand** via the **"Directions
Index"** in the global `~/.claude/CLAUDE.md`. **Do not copy them into the project.** Copies drift —
an already-set-up project never receives new house-style — which is exactly the flaw this avoids.

`/setup` scaffolds **only project-specific files** (read the matching master template on demand):
- `CLAUDE.md` — Claude Code project instructions, when Claude Code is in use; preserve an existing file
- `AGENTS.md` — Codex project instructions, when Codex is in use; preserve an existing file
- `docs/PROJECT_STATE.md` — the source-of-truth position digest (also the "is Directions set up?" sentinel); use the master's `PROJECT_STATE.md` as the structural template
- `docs/sessions/_index.md` — session history index
- `docs/decisions.md` — this project's decision log
- `docs/glossary.md` — *project-specific* terms only (the personal glossary lives globally)

Use the entry-point templates in `12_documentation-templates.md`. Keep stable project facts aligned
between them, but keep tool-specific behavior separate. The live `commands/*.md` library remains the
single workflow source: Claude invokes it directly and Codex reaches it through the thin Directions
skill adapter. Do not copy or translate the command files into the project.

**Important:** For new projects, after scaffolding those files and running the interview, **always create the project folder structure** (read `13_folder-structure.md` from the master on demand). The actual code always lives in `01_Project/` (the one exception is framework web apps — code at repo root):
- macOS/iOS: `01_Project/`, `02_Design/Exports/`, `03_Screenshots/`, `04_Exports/`
- Web (no-build/Strato): `01_Project/` (code + lftp deploy stage), `02_Design/`, `03_Scripts/migrations/`, `04_Data/`
- Web (framework/Vercel): scaffold the framework at the repo root, add `02_Design/`, `03_Scripts/`, `04_Data/` alongside
- Create `.gitignore` using the comprehensive template from `13_folder-structure.md`
- **`git init` at the project root** (never inside `01_Project/`), then make the initial commit — see `32_git-workflow.md` → "Where the Repo Lives"

This is a **solo developer** workflow: branch → commit → merge to `main` locally. Do **not** open pull requests or suggest a PR-based flow.

Execute the detection now and guide me through setup.
