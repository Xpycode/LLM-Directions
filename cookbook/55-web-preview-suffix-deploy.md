## Web Preview-via-Suffix Deploy — Staging Without Staging

**Source:** `lucesumbrarum.photos` rebuild — 16 pages deployed as `*-new.html` alongside live originals during multi-day migration. Added 2026-04-23.

> *Legacy path: the `01_Source/` references in the examples below predate the universal `01_Project/` code-home convention. New web projects put code (and the lftp deploy stage) in `01_Project/` — see `13_folder-structure.md`.*

**Use case:** You're rewriting a static site page-by-page over several sessions. The old site must stay live (real visitors, Google SEO, link equity) while you iterate on the new design. You don't have a staging environment, don't want to spin one up, and don't want to pay for Netlify preview deploys or Vercel branch URLs. Solution: deploy each new page with a `-new.html` suffix directly to production — shares the same origin (so images, fonts, CSS all resolve), but lives at a URL the public doesn't see. When ready, atomic rename + sitewide href-strip.

**When to reach for it:**
- Static or server-rendered site on shared hosting (Strato, Dreamhost, etc.) — no CI/CD, no preview branches.
- Migration or rebuild that spans days/weeks — you want to send yourself and maybe 1-2 reviewers a URL, not onboard a tool.
- Site has internal cross-links between pages — you need intramural preview links that *stay in preview*.
- Image/video/font assets are on the same origin and too large to duplicate — using the live assets is a feature, not a bug.

**When *not* to use it:**
- You have CI/CD with preview deploys (Vercel, Netlify, Cloudflare Pages) — those are strictly better (isolated env, branch-per-PR, automatic cleanup).
- The site is SPA-style with a build step — preview = run the dev server locally.
- You need to test destructive mutations (DB writes, outbound emails) — preview URLs share production services; use a real staging env.
- Your file names contain dots or special chars that break URL routing on your host.

---

### Anatomy

```
Live site (production)           Preview (staging shadow)
──────────────────────           ────────────────────────
index.html                       index-new.html
analog.html                      analog-new.html
dias.html                        dias-new.html
schnecke.html                    schnecke-new.html
...                              ...

Internal hrefs on preview pages point to OTHER -new.html pages:
  <a href="dias-new.html">       ← not "dias.html"

Same assets:
  css/site.css                   (shared — preview uses the new version;
                                  if CSS changes are backward-compatible,
                                  old site stays correct too)
  images/*.webp                  (shared, untouched)
```

---

### Build-time convention

All internal hrefs in preview files use `-new.html` suffix:

```html
<!-- In analog-new.html (deployed as /analog-new.html on server) -->
<a href="index-new.html">Home</a>
<a href="dias-new.html">Dias</a>
<a href="digital-new.html">Digital</a>
```

This is the *only* coordination cost. Every deploy session, every new cross-link must remember to use `-new.html`. Easy to get wrong — grep before each deploy:

```bash
# Verify no preview page accidentally links to a production page
grep -rn 'href="[a-z][^"]*\.html"' 01_Source/*.html \
  | grep -v '\-new\.html\|https\?://\|youtube\.'
# Should return only the brand link in the index file pointing to itself.
```

### Deploy (SFTP pattern for Strato)

```bash
sshpass -p '...' sftp -o StrictHostKeyChecking=no -o BatchMode=no user@host <<EOF
put index.html           index-new.html
put analog.html          analog-new.html
put dias.html            dias-new.html
put css/site.css         css/site.css    # shared; live takes updates too
bye
EOF
```

The trick: `put <local> <remote>` lets the local file keep its plain name (`analog.html` in your working dir) while uploading under the `-new` suffix on the server. No source-file renaming, no duplicate copies to maintain.

### Ship = atomic swap

When the preview is ready:

```bash
# 1. On the server, rename -new.html → .html (overwrites the live versions)
sshpass -p '...' sftp user@host <<EOF
rename index-new.html     index.html
rename analog-new.html    analog.html
rename dias-new.html      dias.html
...
bye
EOF

# 2. On the local source files, strip the -new suffix from internal hrefs
find 01_Source -name '*.html' -exec sed -i '' 's|-new\.html|.html|g' {} \;

# 3. Re-upload the now-fixed files to their production names (no -new)
```

Alternatively, build a script that does both in one pass:

```bash
# 03_Scripts/ship.sh
#!/usr/bin/env bash
set -euo pipefail
cd 01_Source
for f in *-new.html; do
  prod="${f%-new.html}.html"
  sed 's|-new\.html|.html|g' "$f" > "/tmp/$prod"
done
# Upload the /tmp/*.html files to production names
```

---

### Why it works

- **Same origin = same assets.** You're not duplicating `/images/`, `/video/`, `/fonts/` — the preview pages reference them via the same relative paths as production. Saves bytes, saves bandwidth, guarantees visual parity.
- **No DNS, no certificates, no environment config.** The preview URL is just `https://yoursite.com/analog-new.html` — same TLS cert, same CDN, same everything.
- **Search engines don't surface preview URLs organically** (no internal links from the live site point to them) but you *can* share the URL with reviewers directly. If you're worried about crawlers stumbling in, add `<meta name="robots" content="noindex">` to the preview pages.
- **Backward compatibility check is built-in.** If a CSS change breaks an old page, you see it immediately because the old page uses the same stylesheet.

### Common mistakes
- **Forgetting to update a cross-link to `-new`** → preview user clicks Dias → lands on old `dias.html` and thinks the whole preview is broken. Grep before every deploy.
- **Uploading CSS changes that break the live site** → the shared CSS file means live site also gets your new rules. Make CSS additions, not modifications to existing selectors used by the old site. Or: use a separate CSS filename for preview (`site-new.css`) and switch to the production name on ship.
- **Public links to preview URLs on social media** → they get indexed. If the preview is sensitive/unfinished, use a `<meta name="robots" content="noindex">` tag or `X-Robots-Tag` header.
- **Not cleaning up `-new` files after ship** → the server accumulates stale shadows. Add a cleanup step to the ship script.

### Pairs well with
- **`gen_*.py` build scripts** that emit HTML with `-new.html` baked in by default, stripped by the ship script. The preview convention becomes invisible machinery.
- **Any sed-driven flip** — once internal hrefs follow a predictable suffix pattern, atomic site-wide renames are trivial.

### Related cookbook
- **`/preview/` subfolder** variant: put previews in a `/preview/` subdirectory with production filenames. Relative links "just work" without suffix games. Cleaner if your migration spans weeks, but requires more path-aware asset references (`../images/` instead of `images/`). Trade-off.
