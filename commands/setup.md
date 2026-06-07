# Project Setup

Run the project detection flow:

1. Check if `docs/PROJECT_STATE.md` exists (Directions already set up)
2. Check if `/docs` folder exists without Directions structure
3. Check for scattered `.md` files
4. Determine if this is a new empty project

Based on what you find, offer the appropriate options as described in the global CLAUDE.md under "Project Detection".

## Read-on-demand, do NOT copy the universal docs

The universal guidance docs (`00`–`61`: gotchas, checklists, templates, references) are the **single
source of truth in the Directions master repo** and are read **on demand** via the **"Directions
Index"** in the global `~/.claude/CLAUDE.md`. **Do not copy them into the project.** Copies drift —
an already-set-up project never receives new house-style — which is exactly the flaw this avoids.

`/setup` scaffolds **only project-specific files** (read the matching master template on demand):
- `docs/PROJECT_STATE.md` — the source-of-truth position digest (also the "is Directions set up?" sentinel); use the master's `PROJECT_STATE.md` as the structural template
- `docs/sessions/_index.md` — session history index
- `docs/decisions.md` — this project's decision log
- `docs/glossary.md` — *project-specific* terms only (the personal glossary lives globally)

**Important:** For new projects, after scaffolding those files and running the interview, **always create the project folder structure** (read `13_folder-structure.md` from the master on demand). The actual code always lives in `01_Project/` (the one exception is framework web apps — code at repo root):
- macOS/iOS: `01_Project/`, `02_Design/Exports/`, `03_Screenshots/`, `04_Exports/`
- Web (no-build/Strato): `01_Project/` (code + lftp deploy stage), `02_Design/`, `03_Scripts/migrations/`, `04_Data/`
- Web (framework/Vercel): scaffold the framework at the repo root, add `02_Design/`, `03_Scripts/`, `04_Data/` alongside
- Create `.gitignore` using the comprehensive template from `13_folder-structure.md`
- **`git init` at the project root** (never inside `01_Project/`), then make the initial commit — see `32_git-workflow.md` → "Where the Repo Lives"

This is a **solo developer** workflow: branch → commit → merge to `main` locally. Do **not** open pull requests or suggest a PR-based flow.

Execute the detection now and guide me through setup.
