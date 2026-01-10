# Project Folder Structure

> **Trigger:** New project setup, "where should I put", folder organization, gitignore

A consistent structure keeps projects clean, GitHub-friendly, and easy to navigate.

---

## macOS / iOS Projects

```
MyApp/
├── MyApp/                      ← Source code (Xcode project folder)
│   ├── Views/
│   ├── Models/
│   ├── Services/
│   ├── Resources/
│   └── Assets.xcassets/
│
├── MyApp.xcodeproj/            ← Xcode project file
│   └── (xcuserdata/ ignored)
│
├── APP/                        ← Exports (builds, DMGs, IPAs)
│   ├── MyApp-1.0.dmg
│   └── MyApp 1.0/              ← Unzipped app for testing
│
├── Design/                     ← Design source files
│   ├── MyApp-Icon.afdesign     ← Affinity Designer source
│   ├── MyApp-Icon.icon         ← Folder icon project
│   └── Exports/                ← Exported PNGs for icon
│       └── AppIcon.appiconset/
│
├── Screenshots/                ← App Store / promotional
│   ├── 01-MainView.png
│   ├── 02-Settings.png
│   └── ...
│
├── docs/                       ← Directions documentation
│   ├── 00_base.md
│   ├── PROJECT_STATE.md
│   └── sessions/
│
├── old-docs/                   ← Migrated docs (if any)
│
├── .git/
├── .gitignore
├── CLAUDE.md                   ← Project-specific Claude context
├── README.md
├── LICENSE
└── CHANGELOG.md                ← Optional
```

### iOS-Specific Additions

```
MyApp/
├── MyApp/                      ← Main iOS app
├── MyAppWidget/                ← Widget extension
├── MyApp Watch Watch App/      ← watchOS companion
├── MyAppTests/                 ← Unit tests
├── MyAppUITests/               ← UI tests
└── ...
```

---

## Web Projects

```
MyWebsite/
├── frontend/                   ← Built site / app
│   ├── index.html
│   ├── css/
│   ├── js/
│   └── assets/
│
├── src/                        ← Source (if using build tools)
│   ├── components/
│   ├── pages/
│   └── styles/
│
├── scripts/                    ← Build/utility scripts
│   ├── build.py
│   └── deploy.sh
│
├── data/                       ← Data files (JSON, CSV)
│   ├── content.json
│   └── backup/
│
├── docs/                       ← Directions
│
├── venv/                       ← Python virtual env (gitignored)
├── node_modules/               ← Node deps (gitignored)
│
├── .gitignore
├── README.md
├── requirements.txt            ← Python deps
└── package.json                ← Node deps
```

---

## What Goes Where

| Item | Location | Git? |
|------|----------|------|
| Source code | `MyApp/` | Yes |
| Xcode project | `MyApp.xcodeproj/` | Yes (mostly) |
| Built apps, DMGs | `APP/` | No |
| Design source (.af, .afdesign) | `Design/` | Optional |
| Icon exports | `Design/Exports/` | No (generated) |
| Screenshots | `Screenshots/` | Yes (if for App Store) |
| Documentation | `docs/` | Yes |
| Planning/review MDs | `docs/` or root | No (temporary) |
| Crash logs (.ips) | Delete or `Debug/` | No |
| Trace files (.trace) | Delete | No |
| Python venv | `venv/` | No |
| Node modules | `node_modules/` | No |

---

## Naming Conventions

### Folders
- PascalCase for app folders: `MyApp/`, `Screenshots/`
- lowercase for utility: `docs/`, `scripts/`, `venv/`

### Files
- Screenshots: `01-MainView.png`, `02-Settings.png` (numbered for order)
- Design files: `MyApp-Icon.afdesign` (project name prefix)
- Exports: `MyApp-1.0.dmg` (with version)

### Icon Export Folders
Consistent pattern:
```
MyApp-Icon Exports/         ← Exported PNGs
MyApp-Icon.afdesign         ← Source file
```

Not:
```
MyApp-icon-NanoBanana Exports/    ← Too specific
AppIcon.appiconset/               ← Only inside Exports/
```

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
APP/
*.dmg
*.app
*.o
*.a

# === Design Assets (Optional - uncomment if not tracking) ===
# Design/
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

# === IDE ===
.idea/
.vscode/
*.swp
*.swo
*~

# === Secrets ===
*.pem
*.key
.env.local
.env.*.local
credentials.json
secrets.json
```

---

## Cleanup Checklist

When a project gets messy:

1. **Move loose MDs** to `docs/` or delete if obsolete
2. **Move design files** to `Design/`
3. **Move builds** to `APP/`
4. **Delete debug artifacts** (.ips, .trace, crash logs)
5. **Update .gitignore** if new patterns emerged
6. **Run `git status`** to verify nothing unwanted is tracked

---

## Quick Setup Script

For new projects:

```bash
# Create folder structure
mkdir -p APP Design/Exports Screenshots docs/sessions

# Create minimal .gitignore
cat > .gitignore << 'EOF'
.DS_Store
DerivedData/
build/
APP/
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
```

---

*Keep it clean. Future you will thank present you.*
