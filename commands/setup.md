# Project Setup

Run the project detection flow:

1. Check if `docs/00_base.md` exists (Directions already set up)
2. Check if `/docs` folder exists without Directions structure
3. Check for scattered `.md` files
4. Determine if this is a new empty project

Based on what you find, offer the appropriate options as described in the global CLAUDE.md under "Project Detection".

**Important:** For new projects, after copying Directions docs and running the interview, **always create the project folder structure** from `docs/13_folder-structure.md`:
- macOS/iOS: `01_Project/`, `02_Design/Exports/`, `03_Screenshots/`, `04_Exports/`
- Web: `01_Source/`, `02_Frontend/`, `03_Scripts/`, `04_Data/`
- Create `.gitignore` using the comprehensive template from `13_folder-structure.md`
- Create `docs/sessions/_index.md`, `docs/PROJECT_STATE.md`, `docs/decisions.md`

Execute the detection now and guide me through setup.
