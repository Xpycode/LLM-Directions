# Pattern Cookbook

Manage the reusable code patterns cookbook.

## Structure (read this first)

The cookbook is **split**, not a monolith:

- **`cookbook/NNN-*.md`** — one file per pattern. Each starts with an H1 title, then a
  `**Tags:**` line (searchable keywords), then the full write-up + code.
- **`PATTERNS-COOKBOOK.md`** — a lean **router index**: one row per pattern
  (`| # | File | one-line summary |`). Search it on demand and keep it small.
  **Never paste full patterns or code into it.**

**Location:** the cookbook lives only in the Directions master, including when invoked from a
consumer project. Resolve `<master>` from the Directions adapter or the managed instructions'
`Local master:` value; in this repository, its root is the master. Verify it contains
`commands/cookbook.md`, `PATTERNS-COOKBOOK.md` and `cookbook/`. If unavailable, report the missing
master and ask for its location; do not substitute consumer copies or create a replacement cookbook.
Expand `<master>` to an absolute path before reading or writing. All cookbook paths below are
relative to that master; source-project code and extraction credits remain in their own project.

## Looking a pattern up (grep-first — never read the whole index)

1. Grep the index for a keyword, then read only the matching file:
   `rg -i -- '<keyword>' '<master>/PATTERNS-COOKBOOK.md'` → open the matching file under
   `<master>/cookbook/` from the row's link.
2. Or grep the files' `**Tags:**` lines directly, skipping the index:
   `rg -n -i -- '^\*\*Tags:\*\*.*<keyword>' '<master>/cookbook/'`

Read **only** the one matching file. Do not load `PATTERNS-COOKBOOK.md` wholesale.

## Commands

### `/cookbook add`

Quick-add a pattern you just built.

1. Ask (one turn): "What pattern did you just build, which file has the working code, and what's it
   best for in one line?"
2. Compute the next number `NNN` = highest existing `cookbook/NNN-*.md` + 1.
3. Create `cookbook/NNN-<kebab-slug>.md`:
   - `# NNN — <title>`
   - `**Tags:** <5–10 comma-separated search keywords>` (APIs, symbols, error strings, concepts)
   - `**Extracted from:** <project> (<date>)`
   - The write-up: the problem, the gotcha/why, and a **≤~50-line** code snippet. Keep the whole
     file **≤~10KB**.
4. Add **exactly one** row to `PATTERNS-COOKBOOK.md`:
   `| NNN | [NNN-slug.md](cookbook/NNN-slug.md) | <≤200-char summary> |`
   Add it in numeric order. The summary is a distillation — the detail lives in the file.
5. Confirm: "Added #NNN to the cookbook (file + index row)."

### `/cookbook update`

Rescan `~/ProgrammingProjects` for new reusable patterns not yet captured.

1. Look for Swift/web files with reusable, non-obvious patterns (a gotcha that took >30 min, code
   copied across projects, a SwiftUI/AppKit quirk).
2. Compare against existing `cookbook/` files (grep Tags + filenames).
3. For each genuinely new one, ask before adding, then follow `/cookbook add` steps 2–4.

### `/cookbook search <query>`

Use the absolute-path `rg` searches above for the index and files' Tags lines; present
the matching rows and read the top file(s).

## When to add a pattern

**Add when:** you built something that took >30 min to figure out · you copied code across projects ·
you solved a SwiftUI/AppKit/web quirk · you want to remember "how we did X in project Y".

**Don't add:** one-off hacks · project-specific logic · obvious/trivial code.

## Size discipline (keep the router lean)

- Index row summary ≤ 200 chars — no code, no pairs-with lists, no source credits.
- Pattern file ≤ ~10KB; if a pattern is genuinely huge, split it and cross-reference (see #00).
- The index never carries a changelog — history lives in git.
