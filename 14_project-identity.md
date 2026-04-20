# Project Identity & Signing Conventions

Canonical identifiers, signing settings, and Info.plist defaults for Luces Umbrarum apps. Use this when scaffolding a new macOS/iOS project or auditing an existing one before shipping.

---

## Apple Developer

| Field                | Value                 |
|----------------------|-----------------------|
| Team ID              | `FDMSRXXN73`          |
| Developer name       | `Luces Umbrarum`      |
| Copyright line       | `Copyright © <YEAR> Luces Umbrarum. All rights reserved.` |

---

## Bundle Identifier Patterns

**Canonical (use for all new apps):**

```
com.lucesumbrarum.<AppName>
```

Example: `com.lucesumbrarum.DesktopStats`

**Legacy — leave in place, don't migrate unilaterally:**

```
LucesUmbrarum.<AppName>
```

Apps currently on the legacy pattern:

- `LucesUmbrarum.Penumbra`
- `LucesUmbrarum.LogCountdowner`
- `LucesUmbrarum.ProjectProgressTracker`

Rename only if the user explicitly asks — bundle ID changes break Sparkle update feeds, Keychain access, sandboxed storage, and App Store linkage.

**Red flags (placeholders to replace):**

- `com.yourdomain.<AppName>` — Xcode template default
- `com.yourname.<AppName>` — Xcode template default
- `com.<generic>.app` — fix to follow canonical pattern
- `DEVELOPMENT_TEAM = ""` — not wired up yet; set before building/signing

---

## Recurring Xcode Build Settings

These appear across the Luces Umbrarum macOS apps. Use as defaults when scaffolding:

| Setting                             | Value                    |
|-------------------------------------|--------------------------|
| `DEVELOPMENT_TEAM`                  | `FDMSRXXN73`             |
| `CODE_SIGN_STYLE`                   | `Automatic`              |
| `ENABLE_HARDENED_RUNTIME`           | `YES`                    |
| `ENABLE_APP_SANDBOX`                | `YES` (App Store target) |
| `GENERATE_INFOPLIST_FILE`           | `YES`                    |
| `MARKETING_VERSION`                 | `1.0` (initial)          |
| `CURRENT_PROJECT_VERSION`           | `1` (initial)            |
| `SWIFT_VERSION`                     | `6.0` (new), `5.0` (legacy, don't migrate blind) |

Deployment target is **per-app** — pick based on feature requirements, not a blanket rule. Observed values: 13.0, 14.0, 15.0, 15.5, 26.0 (Tahoe-only). Penumbra is deliberately `26.0`.

---

## Info.plist Keys (GENERATE_INFOPLIST_FILE workflow)

| Key                                         | Value                                                                 |
|---------------------------------------------|-----------------------------------------------------------------------|
| `INFOPLIST_KEY_NSHumanReadableCopyright`    | `Copyright © 2025 Luces Umbrarum. All rights reserved.`               |
| `INFOPLIST_KEY_LSApplicationCategoryType`   | `public.app-category.utilities` — general tools                       |
|                                             | `public.app-category.video` — video/media apps                        |
|                                             | `public.app-category.productivity` — workflow/planner apps            |
|                                             | `public.app-category.developer-tools` — dev utilities                 |

Set these as build settings (prefixed `INFOPLIST_KEY_`) rather than editing an Info.plist file. Xcode generates the plist at build time.

---

## Checklist: Scaffolding a New macOS App

1. Create project with `PRODUCT_BUNDLE_IDENTIFIER = com.lucesumbrarum.<AppName>`
2. Set `DEVELOPMENT_TEAM = FDMSRXXN73` on all targets
3. Confirm `CODE_SIGN_STYLE = Automatic`
4. Enable `ENABLE_HARDENED_RUNTIME` and (if App Store) `ENABLE_APP_SANDBOX`
5. Set `INFOPLIST_KEY_NSHumanReadableCopyright` and the appropriate `LSApplicationCategoryType`
6. Apply the **App Shell Standard** (`docs/cookbook/00-app-shell.md`)
7. Commit the project template before writing feature code

---

## Checklist: Auditing an Existing App Before Shipping

- [ ] Bundle ID matches canonical or intentional legacy pattern (not a template placeholder)
- [ ] `DEVELOPMENT_TEAM = FDMSRXXN73` (not empty)
- [ ] Copyright line present and current year
- [ ] Category type set
- [ ] `MARKETING_VERSION` and `CURRENT_PROJECT_VERSION` reflect the intended release
- [ ] `ENABLE_HARDENED_RUNTIME = YES` if distributing outside the App Store (Developer ID / notarization)

---

*Related: `13_folder-structure.md` (project layout), `30_production-checklist.md` (shipping gate), `PATTERNS-COOKBOOK.md` → `00-app-shell.md` (UI shell standard).*
