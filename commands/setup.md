# Project Setup

Run the project detection flow:

1. Check if `docs/00_base.md` exists (Directions already set up)
2. Check if `/docs` folder exists without Directions structure
3. Check for scattered `.md` files
4. Determine if this is a new empty project

Based on what you find, offer the appropriate options as described in the global CLAUDE.md under "Project Detection".

**Important:** For new projects, after copying Directions docs and running the interview, **always create the project folder structure** from `docs/13_folder-structure.md`. The actual code always lives in `01_Project/` (the one exception is framework web apps — code at repo root):
- macOS/iOS: `01_Project/`, `02_Design/Exports/`, `03_Screenshots/`, `04_Exports/`
- Web (no-build/Strato): `01_Project/` (code + lftp deploy stage), `02_Design/`, `03_Scripts/migrations/`, `04_Data/`
- Web (framework/Vercel): scaffold the framework at the repo root, add `02_Design/`, `03_Scripts/`, `04_Data/` alongside
- Create `.gitignore` using the comprehensive template from `13_folder-structure.md`
- Create `docs/sessions/_index.md`, `docs/PROJECT_STATE.md`, `docs/decisions.md`
- **`git init` at the project root** (never inside `01_Project/`), then make the initial commit — see `docs/32_git-workflow.md` → "Where the Repo Lives"

This is a **solo developer** workflow: branch → commit → merge to `main` locally. Do **not** open pull requests or suggest a PR-based flow.

Execute the detection now and guide me through setup.
