# 121 — Web: clone-and-retint a new single-app marketing site

**Problem.** You ship a family of single-app marketing/download sites that share one design
system (`css/site.css`) and one deploy mechanism, hosted as sibling document roots on one
webspace. Each new app needs its own site. Building from scratch re-litigates solved problems;
copying carelessly drags the donor app's *facts* (architecture, bundle id, pricing) into the new
site as silent lies. This is the repeatable routine — validated across Conjoyn → DiskVerdict →
TimeCodeEditor (3rd time = a pattern).

> Scope: a static HTML/CSS/JS site (no build step) + a PHP download redirect, Sparkle auto-update,
> one accent color per app. Composes #39/#62 (tokens/dark theme), #46 (`dl.php`), #49 (feedback),
> #100 (donate hub), #103 (roster), #105 (nav/footer partials), #16 (Sparkle), #76 (app icon),
> #99 (lftp deploy).

---

## The one trap that bites: clone COLORS, scrub FACTS

A site clone inherits three kinds of content. Two are safe to keep; one is a landmine:

| Kind | Action |
|------|--------|
| **Structure** (layout, sections, JS, shared `site.css`) | Keep verbatim — that's the point |
| **Color** (the one accent) | Retint in ONE place (below) |
| **Facts** (arch, bundle id, min OS, pricing, tagline, category, screenshots) | **SCRUB — every one is donor-specific** |

The facts that have actually shipped wrong when skipped:
- **Architecture** — donor says "Universal (Apple Silicon & Intel)"; the new app is `ARCHS: arm64`
  → **Apple Silicon only**. Read the app's `project.yml`, don't assume.
- **Bundle id / prefix** — `com.xpycode.*` vs `com.lucesumbrarum.*`. Pull from `project.yml`.
- **Min macOS**, **app category** (`LSApplicationCategoryType`), **pricing** (JSON-LD `offers`).
- **Tagline / one-liner / feature copy** — rewrite from the app's **spec**, not from memory. The
  spec's problem statement is the most honest, highest-converting source (every claim is one the
  app can back up). Don't ship the donor's copy lightly reworded.

**Catch leftover donor refs both ways** (the slug appears in two casings):
```bash
grep -rin "donorslug" 01_Source/      # lowercase → URLs, paths, ?app=, dl.php
grep -rn  "DonorApp" 01_Source/        # CamelCase → display text, titles, alt, JSON-LD
```
The only acceptable hits are intentional comment references to sibling sites.

---

## Step-by-step

### 1. Clone the NEWEST sibling, not the original
The most recently shipped site has the accumulated fixes (imprint page, full favicon set, lightbox,
verified-appcast workflow, deploy gotchas). Clone that, then strip git + caches + the app-side
design folders:
```bash
cp -R APPS/DonorApp APPS/NewApp
cd APPS/NewApp && rm -rf .git .fastembed_cache 02_Design 03_Screenshots 04_Exports
```

### 2. Scrub donor binaries + rename the per-site stylesheet
```bash
cd 01_Source
mv css/donorapp.css css/newapp.css
rm -f downloads/*.dmg appcast.xml img/og/*.jpg img/icons/* \
      img/screenshots/*.webp favicon.ico favicon-*.png apple-touch-icon.png
```

### 3. Retint — ONE file, never `site.css`
All color lives in `css/newapp.css` `:root` + the `@media (prefers-color-scheme: dark)` block:
`--accent`, `--accent-soft`, and their dark twins. Pull the value from the app's `Theme`/палитра.
Two gotchas:
- **Accent collision.** If the literal app color equals a sibling site's accent (e.g. two warm
  oranges), the sites look like twins. Pick a *distinct* color from the app's own palette (its
  secondary/highlight accent) rather than the exact primary. Document the choice.
- **Light accents need dark CTA text.** `site.css` uses `--accent` two ways: as a soft *wash*
  behind dark text (`.highlight::after`, safe at any hue) and as a *background* for the nav CTA
  with white text. White-on-gold/yellow **fails WCAG**. Before trusting the clone, check:
  ```bash
  grep -n "var(--accent)\|\.nav-cta\|\.btn-download\|\.highlight" css/site.css
  ```
  If the accent is light, override `.nav-cta { color: #241F18 !important; }` (dark ink) in the
  per-site CSS. The main download button uses `--ink` (already dark) so it's unaffected.

### 4. Generate LABELLED placeholder assets (pre-launch is legitimate)
The site should render and smoke-test before the app's real artifacts exist (Conjoyn and
DiskVerdict both lived as drafts for days). Generate clearly-labelled placeholders:
- **Icon** — hand-author a tasteful on-theme SVG pair (light + dark, swapped by `<picture>`),
  legible at 16px. Favicons from it: `qlmanage -t -s 1024 -o /tmp icon.svg` →
  `magick` to `.ico` (16/32/48) + `favicon-16/32.png` + `apple-touch-icon.png` (180). (Real icon
  later via #76.) ImageMagick needs an explicit `-font /System/Library/Fonts/SFNS.ttf`.
- **Screenshots** — `magick` a branded card stamped "placeholder — real screenshot pending" → `cwebp
  -q 82`, one per slot, light + dark. A **dark-only app** (`.preferredColorScheme(.dark)`) → the
  same capture fills both the `-light` and `-dark` slot (like Conjoyn).
- **NEVER ship a placeholder `appcast.xml`.** A fake EdDSA signature is worse than none — omit the
  file and document it as a gate. Generate it app-side once the DMG exists.

### 5. Adapt the small files
- `imprint.html` — bulk `sed` the slug/brand (keep the §5 TMG / DDG legal text; it's shared).
- `deploy.sh` — target folder = the app name in **ALLCAPS** (`NEWAPP`); update the comment URL.
- `CLAUDE.md` — rewrite Project/URL/accent/app-reference and **list the four go-live gates**.
- A `make-screenshots.sh` helper (captures → `cwebp` → slots) so the gate is a one-liner later.

### 6. Smoke test (php -S) before committing
```bash
php -S 127.0.0.1:8791 & sleep 1
for p in / /css/site.css /css/newapp.css /img/icons/newapp-light.svg \
         /img/screenshots/newapp-hero-light.webp /favicon.ico /imprint.html; do
  curl -s -o /dev/null -w "%{http_code} $p\n" "http://127.0.0.1:8791$p"; done
curl -s -o /dev/null -w "dl.php → %{http_code}\n" "http://127.0.0.1:8791/dl.php?app=newapp"
```
Expect every asset **200**; `dl.php` **404** with no DMG yet (becomes **302**→DMG once staged).
Visually confirm light + dark (the retint + scheme-swapped icon/screenshots).

---

## The four go-live gates (all app-side — the site waits on the app)
A scaffold is *build-complete* but **not deployable** until the app produces:
1. **Notarized DMG** → `01_Source/downloads/newapp.dmg` (gitignored; deploy mirrors the working tree).
2. **`appcast.xml`** — generated app-side with a **FRESH Sparkle EdDSA key per app** (never reuse a
   sibling's). Verify the `edSignature` against the app's baked-in `SUPublicEDKey` and that `length`
   matches the DMG (#16; OpenSSL 3 `pkeyutl -rawin` — LibreSSL can't do Ed25519).
3. **Real screenshots** — run `make-screenshots.sh`.
4. **Real app icon** — replace the two placeholder SVGs, regenerate favicons (#76).

Deploy: `DRY_RUN=1 ./deploy.sh` (confirms the folder maps), then `./deploy.sh`. ⚠️ The lftp mirror
has **no `--delete`** (#99) — renamed/removed files linger on the server; prune by hand. Adding the
app to the portal roster is a separate one-line `apps.json` edit (#103), not part of the site.

---

## Why this works
Each new site is a day, not a week, because the expensive parts (design system, PHP backends, deploy,
legal pages) are *shared and stable* — only copy, color, and the app's own artifacts change. The
discipline is entirely in **not letting the donor's facts ride along**: clone the skeleton, transplant
the truth.

*Source: App-Websites monorepo — `APPS/{Conjoyn,DiskVerdict,TimeCodeEditor}/`.*
