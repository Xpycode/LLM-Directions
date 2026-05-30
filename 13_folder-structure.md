<!--
TRIGGERS: new project setup, folder structure, "where should I put", gitignore,
          numbered folders, 01_Project, 02_Design, 03_Scripts, 04_Data, 04_Exports,
          deploy.sh placement, migrate-remote.ts placement, libSQL local replica,
          .env.local, .htaccess, vercel.json, Next.js folder layout, Vite folder layout,
          Strato deploy stage, framework project vs no-build site
PHASE: any (especially setup, migration, cleanup)
LOAD: when bootstrapping a new project, migrating a messy tree, or deciding where a new artifact belongs
-->

# Project Folder Structure

A consistent structure keeps projects clean, GitHub-friendly, and easy to navigate. Covers all three target classes — macOS, iOS, and Web (with separate patterns for no-build sites vs framework apps).

---

## The Universal Rule

**This structure applies to *every* project — macOS, iOS, and web alike. The actual code always lives in `01_Project/`.** The numbered convention (`02_Design/`, `03_Screenshots/`, `docs/`, …) wraps around it identically regardless of platform, and the **git repo lives at the project root** wrapping all of it (see `32_git-workflow.md` → "Where the Repo Lives").

| Platform | Code home |
|----------|-----------|
| macOS | `01_Project/` |
| iOS | `01_Project/` |
| Web — no-build / Strato (Pattern A) | `01_Project/` (also the lftp deploy stage) |
| Web — framework / Vercel (Pattern B) | **⚠️ Repo root — the one exception** |

**The single exception:** framework web apps (Next.js / Vite / Astro / SvelteKit) whose toolchain hard-requires `package.json`, `app/`, `public/` etc. at the repo root. Nesting them in `01_Project/` breaks the build unless you set a "Root Directory" override on the platform. For those, code stays at root and the numbered folders sit *alongside* it — see **Pattern B** below.

---

## macOS / iOS Projects

```
MyApp/                              ← Project root (GitHub repo)
│
├── 01_Project/                     ← ALL XCODE STUFF
│   ├── MyApp/                      ← Source code
│   │   ├── Views/
│   │   ├── Models/
│   │   ├── Services/
│   │   ├── Resources/
│   │   └── Assets.xcassets/
│   ├── MyApp.xcodeproj/
│   ├── MyAppTests/                 ← Unit tests
│   └── MyAppUITests/               ← UI tests
│
├── 02_Design/                      ← Design source files
│   ├── MyApp-Icon.afdesign         ← Affinity Designer source
│   ├── MyApp-Icon.icon             ← Folder icon project
│   └── Exports/                    ← Exported PNGs
│       └── AppIcon.appiconset/
│
├── 03_Screenshots/                 ← App Store / promotional
│   ├── 01-MainView.png
│   ├── 02-Settings.png
│   └── ...
│
├── 04_Exports/                     ← Builds, DMGs, IPAs (gitignored)
│   ├── MyApp-1.0.dmg
│   └── MyApp 1.0/                  ← Unzipped app for testing
│
├── docs/                           ← Directions documentation
│   ├── 00_base.md
│   ├── PROJECT_STATE.md
│   └── sessions/
│
├── old-docs/                       ← Migrated docs (if any)
│
├── .git/                          ← Repo lives HERE, at the app root — NOT inside 01_Project/
├── .gitignore
├── CLAUDE.md                       ← Project-specific Claude context
├── README.md
├── LICENSE
└── CHANGELOG.md                    ← Optional
```

> **The repo lives at the app root**, wrapping `01_Project/`, `02_Design/`, `docs/`, etc. — so source *and* Directions docs are versioned together. Cloning an existing GitHub repo often drops `.git/` inside `01_Project/MyApp/` instead, silently leaving `docs/` and design files untracked. See **`32_git-workflow.md` → "Where the Repo Lives"** for verification (`git rev-parse --show-toplevel`) and the re-rooting recovery recipe.

### iOS with Extensions

```
MyApp/
├── 01_Project/
│   ├── MyApp/                      ← Main iOS app
│   ├── MyAppWidget/                ← Widget extension
│   ├── MyApp Watch Watch App/      ← watchOS companion
│   ├── MyAppTests/
│   ├── MyAppUITests/
│   └── MyApp.xcodeproj/
│
├── 02_Design/
├── 03_Screenshots/
├── 04_Exports/
└── docs/
```

---

## Web Projects

Web projects split into two patterns depending on whether there's a framework build step. **Use Pattern A** for sites you SFTP/lftp to a shared host (Strato, Hetzner) and **Pattern B** for sites you `vercel deploy` or `git push` to a platform that builds for you.

### Pattern A — No-build static + PHP (Strato-style)

For sites that ship raw HTML/PHP/CSS/JS to shared hosting with no build step. The deploy is `lftp mirror -R 01_Project /htdocs/<site>/`. See `29_web-strato-hosting.md` for the deploy recipe.

Per the universal rule, the site code lives in `01_Project/` — and because there's no build step, **`01_Project/` *is* the lftp deploy stage** (source == what ships). The live SQLite DB stays in `04_Data/` (gitignored, *outside* `01_Project/`), so the upload step can never reach it (29_).

```
MySite/                             ← Project root (GitHub repo, .git/ HERE)
│
├── 01_Project/                     ← ALL SITE CODE + lftp deploy stage
│   ├── index.php                   ← (or index.html)
│   ├── .htaccess                   ← Apache directives (deployed)
│   ├── .htpasswd                   ← Basic-auth users (deployed; gitignored if real creds)
│   ├── public/
│   │   ├── app.css
│   │   ├── app.js
│   │   └── assets/                 ← Logos, OG images, favicons
│   ├── lib/                        ← PHP includes (asset cache-busters, etc.)
│   └── _src/                       ← Pre-compile sources (SCSS, partials) — only if you compile
│
├── 03_Scripts/                     ← Deploy + DB ops + utilities
│   ├── deploy.sh                   ← lftp mirror script (see 29_web-strato-hosting.md)
│   ├── migrate-remote.ts           ← libSQL/Turso DDL applier (see 39_libsql-turso-sync.md)
│   ├── clean-remote.ts             ← libSQL/Turso DML recovery
│   ├── migrations/
│   │   ├── 001_init.sql
│   │   └── 002_add_thumbnail.sql
│   └── build.sh                    ← Optional: SCSS compile, image opt
│
├── 04_Data/                        ← Local data + replicas (mostly gitignored)
│   ├── feed.db                     ← libSQL local replica (gitignored)
│   ├── content.json                ← Server-state JSON (gitignored if mutated live)
│   └── backup/                     ← Pre-migration snapshots
│
├── 02_Design/                      ← Design source (parallel to macOS pattern)
│   ├── MySite-Logo.afdesign
│   └── Exports/
│
├── 03_Screenshots/                 ← Marketing / docs screenshots
│
├── docs/                           ← Directions documentation
│   ├── 00_base.md
│   ├── PROJECT_STATE.md
│   └── sessions/
│
├── .git/                           ← Repo at the project root, wrapping everything
├── .gitignore
├── CLAUDE.md
├── README.md
├── package.json                    ← If using Node tooling (tsx, etc.)
├── tsconfig.json                   ← If scripts are TypeScript
└── .env.local                      ← TURSO_URL, TURSO_AUTH_TOKEN, etc. (gitignored)
```

> **Build step?** If you compile (SCSS, templating), keep authoring sources in `01_Project/_src/` and emit the shipped files into `01_Project/` itself — `build.sh` writes outputs next to `index.php`. `lftp` still mirrors `01_Project/`. Don't reintroduce a separate top-level source folder; one code home.

**Deploy artifact placement:**

| Artifact | Lives in | Notes |
|---|---|---|
| `deploy.sh` (lftp script) | `03_Scripts/` | Runs `chmod 644/755` normalize before `lftp mirror -R` |
| `$STAGE_DIR` for lftp | `01_Project/` | What ships; never edit on server, never `--delete` |
| `.htaccess` | `01_Project/` root | DirectoryIndex, rewrites, basic-auth references |
| `.htpasswd` | `01_Project/` (deployed) | Real one gitignored; commit only sample with placeholder hashes |
| Path-probe PHP | Anywhere temporary | **Delete after use** — leaks server topology (29_) |
| libSQL local replica `.db` | `04_Data/` | Gitignored; rebuilt by `db.sync()` on fresh checkout |
| Migration SQL files | `03_Scripts/migrations/NNN_name.sql` | Committed; applied to BOTH local + remote (39_ Rule 1) |
| Server-state JSONs | `04_Data/` | If mutated by live endpoints, gitignore + re-pull-and-migrate before each deploy (29_) |

---

### Pattern B — Framework app (Next.js / Vite / Astro / SvelteKit) — ⚠️ the `01_Project/` exception

**This is the one project type where code does NOT live in `01_Project/`.** A framework owns the build and the platform (Vercel, Netlify, Cloudflare Pages) owns the deploy. The framework expects its own files at the **repo root** — `package.json`, `next.config.ts`, `vercel.json`, `app/`, `src/`, `public/` can't be tucked inside `01_Project/` without breaking the toolchain (you'd need a "Root Directory" override on every platform and forced `rootDirectory` config everywhere). So code stays at root; the numbered convention applies *around* it.

```
MyWebApp/                           ← Project root (GitHub repo)
│                                     ← Framework files live HERE, not nested
├── app/                            ← Next.js App Router (or src/ for Vite)
│   ├── page.tsx
│   ├── layout.tsx
│   └── api/
├── components/
├── lib/
├── public/                         ← Framework-served static assets (favicons, OG)
│
├── .next/                          ← Build output (gitignored)
├── dist/                           ← OR Vite/Astro build output (gitignored)
├── node_modules/                   ← (gitignored)
│
├── 02_Design/                      ← Design source — numbered convention still applies
│   ├── MyApp-Logo.afdesign
│   └── Exports/
│
├── 03_Scripts/                     ← Non-framework scripts (DB ops, one-offs)
│   ├── migrate-remote.ts           ← libSQL/Turso (39_)
│   ├── clean-remote.ts
│   └── migrations/
│       └── 001_init.sql
│
├── 04_Data/                        ← Local fixtures, replica DBs
│   └── feed.db                     ← (gitignored)
│
├── 03_Screenshots/                 ← Marketing screenshots
│
├── docs/                           ← Directions documentation
│   ├── 00_base.md
│   ├── PROJECT_STATE.md
│   └── sessions/
│
├── .vercel/                        ← Vercel link state (gitignored)
├── .env.local                      ← TURSO_URL, OAuth secrets, etc. (gitignored)
├── .env.example                    ← Committed template with placeholders
├── .gitignore
├── CLAUDE.md
├── README.md
├── package.json
├── tsconfig.json
├── next.config.ts                  ← (or vite.config.ts / astro.config.mjs)
├── vercel.json                     ← Routing/headers if customizing
└── middleware.ts                   ← Next.js middleware/proxy (if used)
```

**Why framework files live at the root, not inside `01_Project/`:** Next.js, Vite, Astro all expect a specific layout relative to `package.json` (the framework finds `app/`, `pages/`, `src/`, `public/` by path). Vercel reads `vercel.json` from the project root. Moving these into a subfolder either breaks the toolchain or forces `rootDirectory` overrides everywhere. The numbered convention then applies *around* the framework — `02_Design/`, `03_Scripts/`, `04_Data/`, `docs/` sit next to it.

**Deploy artifact placement:**

| Artifact | Lives in | Notes |
|---|---|---|
| Build output | `.next/` or `dist/` or `build/` | Always gitignored; the platform regenerates |
| `vercel.json` | Repo root | Routing rules, headers, region pinning |
| `.vercel/` | Repo root (gitignored) | Local Vercel link state |
| `.env.local` | Repo root (gitignored) | Local dev secrets |
| `.env.example` | Repo root (committed) | Placeholders showing required keys |
| GitHub Actions | `.github/workflows/` | If running CI outside the deploy platform |
| libSQL local replica | `04_Data/feed.db` (gitignored) | Same pattern as Pattern A |
| Migration SQLs | `03_Scripts/migrations/` | Same pattern as Pattern A (39_ Rule 1) |

---

## Folder Numbering Logic

| Number | Purpose | Examples |
|--------|---------|----------|
| 01_ | Source/Project | Xcode project, source code |
| 02_ | Design | Affinity files, icons, mockups |
| 03_ | Screenshots | App Store, promotional |
| 04_ | Exports/Output | DMGs, IPAs, built apps |
| docs/ | Documentation | Directions (has own numbering) |

Numbers keep folders sorted logically in Finder and terminals.

---

## What Goes Where

| Item | Location | Git? |
|------|----------|------|
| **— macOS / iOS —** | | |
| Source code | `01_Project/MyApp/` | Yes |
| Xcode project | `01_Project/MyApp.xcodeproj/` | Yes (mostly) |
| Design source (.af, .afdesign) | `02_Design/` | Optional |
| Icon exports | `02_Design/Exports/` | No (generated) |
| Screenshots | `03_Screenshots/` | Yes (if for App Store) |
| Built apps, DMGs, IPAs | `04_Exports/` | No |
| Crash logs (.ips) | Delete | No |
| Trace files (.trace) | Delete | No |
| Per-machine signing config | `Debug.local.xcconfig` (next to project) | No (28_) |
| **— Web, Pattern A (no-build) —** | | |
| Site code + deploy stage (lftp source) | `01_Project/` | Yes |
| `.htaccess` | `01_Project/` | Yes |
| `.htpasswd` (real) | `01_Project/` | **No** (gitignore; commit only `.example`) |
| Cache-buster helper (`asset.php`) | `01_Project/lib/` | Yes |
| Pre-compile sources (SCSS, partials) | `01_Project/_src/` | Yes (only if you compile) |
| Deploy script (`deploy.sh`) | `03_Scripts/` | Yes |
| **— Web, Pattern B (framework) —** | | |
| Framework source (`app/`, `src/`) | Repo root | Yes |
| Public assets (`public/`) | Repo root | Yes |
| `vercel.json` / `next.config.ts` | Repo root | Yes |
| Build output (`.next/`, `dist/`, `build/`) | Repo root | **No** |
| Vercel link state (`.vercel/`) | Repo root | **No** |
| **— Web, both patterns —** | | |
| libSQL local replica (`.db`) | `04_Data/` | **No** (rebuilt by `db.sync()`) |
| Migration SQL files | `03_Scripts/migrations/NNN_*.sql` | Yes (39_) |
| Remote-migration helper (`migrate-remote.ts`) | `03_Scripts/` | Yes (39_) |
| Local secrets (`.env.local`) | Repo root | **No** |
| Secrets template (`.env.example`) | Repo root | Yes |
| Server-state JSONs (mutated live) | `04_Data/` | No (re-pull from prod, see 29_) |
| Design source (web logo, OG) | `02_Design/` | Optional |
| **— Both targets —** | | |
| Documentation | `docs/` | Yes |
| Planning/review MDs | `docs/` or root | No (temporary) |
| Python venv | `venv/` | No |
| Node modules | `node_modules/` | No |

---

## Naming Conventions

### Folders
- Numbered: `01_Project/`, `02_Design/`
- Lowercase for non-numbered: `docs/`, `venv/`

### Files
- Screenshots: `01-MainView.png`, `02-Settings.png` (numbered for order)
- Design files: `MyApp-Icon.afdesign` (project name prefix)
- Exports: `MyApp-1.0.dmg` (with version)

---

## Comprehensive .gitignore

```gitignore
# === macOS ===
.DS_Store
.AppleDouble
.LSOverride
._*
.Spotlight-V100
.Trashes

# === Xcode ===
*.xcodeproj/project.xcworkspace/
*.xcodeproj/xcuserdata/
*.xcworkspace/xcuserdata/
xcuserdata/
DerivedData/
build/
*.moved-aside
*.pbxuser
!default.pbxuser
*.mode1v3
!default.mode1v3
*.mode2v3
!default.mode2v3
*.perspectivev3
!default.perspectivev3
*.hmap
*.ipa
*.dSYM.zip
*.dSYM
timeline.xctimeline
playground.xcworkspace
.build/
*.xcuserstate
*.xcscmblueprint
*.xccheckout

# === Swift Package Manager ===
.swiftpm/
Packages/
Package.pins
Package.resolved

# === CocoaPods / Carthage ===
Pods/
Carthage/Build/

# === Build Outputs ===
04_Exports/
*.dmg
*.app
*.o
*.a

# === Design Assets (Optional - uncomment if not tracking) ===
# 02_Design/
# *.afdesign
# *.af
# *.icon
# *Exports/

# === Debug / Profiling ===
*.ips
*.trace
*.crash
Instruments/

# === Temporary / Planning Files ===
*PLAN*.md
*CHECKLIST*.md
code-review*.md
SESSION-LOG*.md
fix-plan*.md
*-addition.md
TODO-*.md

# === Claude / AI Tools ===
.claude/
.serena/
.aider*
.gemini*

# === Python ===
venv/
__pycache__/
*.pyc
*.pyo
.env

# === Node ===
node_modules/
npm-debug.log
yarn-error.log
pnpm-debug.log
.pnpm-store/
.npm/
.yarn/cache/
.yarn/build-state.yml
.yarn/install-state.gz

# === Next.js ===
.next/
out/                                 # Next.js static export
next-env.d.ts                        # Generated

# === Vite / Astro / SvelteKit ===
dist/
build/
.astro/
.svelte-kit/
.vite/

# === Vercel ===
.vercel/

# === Web Build Output (generic) ===
public/build/                        # If your framework emits here
*.bundle.js
*.bundle.css
*.map                                # Source maps (optional — some teams commit these)

# === Strato / lftp deploy ===
*.PRE-RE-MIGRATE.bak                 # Re-pull-and-migrate backups (29_)
*.pre-merge-backup                   # General safe-merge backups
_path-probe.php                      # Server-topology probe — never commit
.lftp-cache/

# === libSQL / Turso ===
*.db                                 # Local replicas (rebuilt by db.sync())
*.db-journal
*.db-wal
*.db-shm
04_Data/*.db                         # Explicit: never commit replica DBs

# === IDE ===
.idea/
.vscode/
*.swp
*.swo
*~

# === Secrets ===
*.pem
*.key
.env                                 # Never commit any .env file with real values
.env.local
.env.*.local
.env.production
.env.development
.htpasswd                            # Real basic-auth hashes (commit only .htpasswd.example)
credentials.json
secrets.json
```

---

## Cleanup Checklist

When a project gets messy:

1. **Move Xcode stuff** into `01_Project/`
2. **Move design files** to `02_Design/`
3. **Move screenshots** to `03_Screenshots/`
4. **Move builds** to `04_Exports/`
5. **Move loose MDs** to `docs/` or delete if obsolete
6. **Delete debug artifacts** (.ips, .trace, crash logs)
7. **Update .gitignore** if new patterns emerged
8. **Run `git status`** to verify nothing unwanted is tracked

---

## Quick Setup Scripts

### macOS / iOS

```bash
# Create folder structure
mkdir -p 01_Project 02_Design/Exports 03_Screenshots 04_Exports docs/sessions

# Create minimal .gitignore
cat > .gitignore << 'EOF'
.DS_Store
DerivedData/
build/
04_Exports/
*.dmg
*.ips
*.trace
venv/
node_modules/
.claude/
.serena/
xcuserdata/
*.xcuserstate
EOF

# Create placeholder files
touch docs/PROJECT_STATE.md
touch docs/decisions.md
echo "# Session Index" > docs/sessions/_index.md

# Initialize git AT THE PROJECT ROOT (never inside 01_Project/ — see 32_git-workflow.md)
git init
git add -A
git commit -m "Initial commit: Directions structure + .gitignore"

echo "Created: 01_Project/ 02_Design/ 03_Screenshots/ 04_Exports/ docs/  +  git repo at root"
```

### Web — Pattern A (no-build static + PHP)

```bash
# Numbered folders + framework-free web layout (01_Project is code home AND deploy stage)
mkdir -p 01_Project/{public,lib} 02_Design/Exports 03_Screenshots \
         03_Scripts/migrations 04_Data docs/sessions

# Stub the deploy stage so lftp has something to mirror
touch 01_Project/index.php 01_Project/.htaccess

# .htpasswd template (real one is gitignored)
cat > 01_Project/.htpasswd.example << 'EOF'
# Generate with: htpasswd -nbB <user> <password>
# admin:$2y$10$REPLACEME
EOF

# Minimal Strato-aware .gitignore
cat > .gitignore << 'EOF'
.DS_Store
node_modules/
venv/
04_Data/*.db
*.db-journal
*.db-wal
*.db-shm
.env
.env.local
.htpasswd
*.PRE-RE-MIGRATE.bak
_path-probe.php
.claude/
.serena/
EOF

# Env template (real .env.local stays uncommitted)
cat > .env.example << 'EOF'
# Strato deploy
STRATO_USER=stuNNNNNNN
STRATO_HOST=ssh.strato.de
STAGE_DIR=./01_Project
SITE_NAME=mysite

# libSQL/Turso (if used)
TURSO_URL=libsql://your-db.turso.io
TURSO_AUTH_TOKEN=
EOF

# Directions placeholders
touch docs/PROJECT_STATE.md docs/decisions.md
echo "# Session Index" > docs/sessions/_index.md

# Deploy-script skeleton (see 29_web-strato-hosting.md for the full recipe)
cat > 03_Scripts/deploy.sh << 'EOF'
#!/usr/bin/env bash
set -euo pipefail
source ./.env.local

# Normalize perms (macOS editors sometimes leave 0600)
find "$STAGE_DIR" -type f -exec chmod 644 {} \;
find "$STAGE_DIR" -type d -exec chmod 755 {} \;

lftp -u "$STRATO_USER","$STRATO_PASS" -e "
  set sftp:auto-confirm yes;
  mirror -R --verbose --parallel=4 $STAGE_DIR /htdocs/$SITE_NAME/;
  bye
" sftp://$STRATO_HOST
EOF
chmod +x 03_Scripts/deploy.sh

# Initialize git AT THE PROJECT ROOT (never inside 01_Project/ — see 32_git-workflow.md)
git init
git add -A
git commit -m "Initial commit: Directions structure + Strato deploy skeleton"

echo "Created Pattern A web project. Next: bind subdomain in control panel, then run 03_Scripts/deploy.sh"
```

### Web — Pattern B (framework app: Next.js / Vite / Astro)

```bash
# Scaffold the framework first (Next.js example — adapt for Vite/Astro)
npx create-next-app@latest . --typescript --app --no-eslint --no-tailwind \
    --no-src-dir --import-alias "@/*"

# Add the numbered convention AROUND the framework
mkdir -p 02_Design/Exports 03_Screenshots \
         03_Scripts/migrations 04_Data docs/sessions

# Extend the framework's .gitignore with our additions
cat >> .gitignore << 'EOF'

# === Directions additions ===
.DS_Store
04_Data/*.db
*.db-journal
*.db-wal
*.db-shm
.env.local
.env.production
.vercel/
.claude/
.serena/
EOF

# Env template
cat > .env.example << 'EOF'
# libSQL/Turso (if used)
TURSO_URL=libsql://your-db.turso.io
TURSO_AUTH_TOKEN=

# OAuth / API keys
# NEXT_PUBLIC_xxx=
EOF

# Directions placeholders
touch docs/PROJECT_STATE.md docs/decisions.md
echo "# Session Index" > docs/sessions/_index.md

echo "Created Pattern B web project. Framework lives at root; 02-04 numbered folders sit alongside."
```

---

## Migrating Existing Projects

### macOS / iOS

If you have an existing messy project:

```bash
# Create new structure
mkdir -p 01_Project 02_Design/Exports 03_Screenshots 04_Exports

# Move Xcode stuff (adjust names as needed)
mv MyApp 01_Project/
mv MyApp.xcodeproj 01_Project/
mv MyAppTests 01_Project/

# Move design files
mv *.afdesign 02_Design/
mv *.af 02_Design/
mv *.icon 02_Design/
mv *Exports/ 02_Design/

# Move screenshots
mv Screenshots/* 03_Screenshots/
mv *.png 03_Screenshots/  # be careful with this one

# Move exports
mv APP/* 04_Exports/
mv *.dmg 04_Exports/
```

Then update your `.xcodeproj` paths if needed (or recreate the project).

### Web — Pattern A (no-build → numbered convention)

Existing flat web project that ships to Strato/shared hosting:

```bash
# Create the numbered layout (01_Project = code home AND deploy stage)
mkdir -p 01_Project/{public,lib} 02_Design/Exports 03_Screenshots \
         03_Scripts/migrations 04_Data docs/sessions

# Move what ships to the host into 01_Project (it IS the deploy stage)
mv index.php index.html .htaccess 01_Project/ 2>/dev/null || true
mv css js images public/* 01_Project/public/ 2>/dev/null || true
mv lib/* 01_Project/lib/ 2>/dev/null || true

# Move scripts (deploy, migrations) — anything you wouldn't ship
mv deploy.sh build.sh 03_Scripts/ 2>/dev/null || true
mv migrations/* 03_Scripts/migrations/ 2>/dev/null || true

# Move data and replicas (gitignore them)
mv *.db *.sqlite 04_Data/ 2>/dev/null || true
mv content.json manifests/* 04_Data/ 2>/dev/null || true

# Move design source
mv *.afdesign *.af 02_Design/ 2>/dev/null || true

# Delete server-topology probes if any survived in the tree
rm -f _path-probe.php _phpinfo.php

# Verify lftp still finds the deploy stage — update STAGE_DIR in deploy.sh
grep -n STAGE_DIR 03_Scripts/deploy.sh
```

Then update your deploy script's `STAGE_DIR` to point at `./01_Project`, and verify `lftp mirror -R "$STAGE_DIR" /htdocs/<site>/` still resolves correctly.

### Web — Pattern B (framework → numbered convention alongside)

Existing Next.js / Vite / Astro project. **Do NOT move framework files** — they need to stay at root for the toolchain. Just add the numbered folders alongside:

```bash
# Add numbered folders without touching framework layout
mkdir -p 02_Design/Exports 03_Screenshots \
         03_Scripts/migrations 04_Data docs/sessions

# Move any loose scripts into 03_Scripts/
mv migrate-remote.ts clean-remote.ts 03_Scripts/ 2>/dev/null || true
mv scripts/* 03_Scripts/ 2>/dev/null || true

# Move local SQLite replicas into 04_Data/ (and gitignore them)
mv *.db 04_Data/ 2>/dev/null || true

# Move design source files
mv *.afdesign *.af 02_Design/ 2>/dev/null || true

# Update package.json script paths if you moved migrate-remote.ts etc.
# e.g. "migrate-remote": "tsx 03_Scripts/migrate-remote.ts"
```

Then update any `package.json` script that references the old paths (e.g. `tsx scripts/migrate-remote.ts` → `tsx 03_Scripts/migrate-remote.ts`).

---

*Keep it clean. Future you will thank present you.*
