## Template Round-Trip Invariant — Admin-Write Safety Net for Static Sites

**Source:** `lucesumbrarum.photos/admin/regen-leaf.php` + `admin/_test-regen.php` + `admin/templates/leaf.html.tpl`. Added 2026-04-23.

> *Legacy path: the `01_Source/` reference in the example below predates the universal `01_Project/` code-home convention. New web projects put code in `01_Project/` — see `13_folder-structure.md`.*

**Use case:** A static site (vanilla HTML, no framework) grows an admin layer whose writes must *regenerate* the public HTML — typically so public pages stay fast and SEO-friendly without client-side JS rendering. The admin deletes/reorders/uploads content and rewrites `slug.html` from a template + JSON manifest on every mutation. The risk is silent corruption: a template drift or a renderer bug breaks *every subsequent write* and may not surface until users notice a layout regression weeks later.

The pattern: before you write any admin mutation endpoint, prove that `parse(committed_leaf) → render(manifest) == committed_leaf` **byte-for-byte** for every representative page. That test then becomes a permanent regression guard — every future template or renderer edit must keep it green. It also proves *constructively* that the parser (used by init-manifest) and the renderer (used by delete/reorder/upload) are consistent with each other, which is the hardest bug to catch by spot-checking output.

**When to reach for it:**
- You have an existing body of hand-written static pages that share a structural template (photo gallery leaves, article pages, product listings).
- You're introducing an admin that will regenerate those pages on every write.
- Hand-editing the generated HTML for tweaks is rare or deliberately forbidden — the template is the one source of truth.
- Zero-tolerance for "the admin accidentally reformatted my whole site" is worth a small upfront test scaffold.

**When *not* to use it:**
- Content is stored in a database and the template is only rendered at request-time (Wordpress, Rails, Laravel blade). The invariant doesn't apply because nothing is "committed HTML."
- Pages drift naturally (heavy hand-edits, per-page custom CSS classes). You can't round-trip what you don't encode; pick a different admin architecture (client-side JSON render, or skip regeneration entirely).
- One-off site with no existing pages to protect — the invariant degenerates to "renderer doesn't crash."

---

### Anatomy

```
admin/
├── regen-leaf.php            ← renderer: manifest + template → HTML (pure function)
├── _test-regen.php           ← CLI-only round-trip harness (parse committed HTML → render → diff)
└── templates/
    ├── leaf.html.tpl         ← parametrised copy of one representative source file
    └── README.md             ← placeholder reference + invariant restatement

images/
└── <gallery-slug>/
    └── manifest.json         ← per-leaf data (not written until admin init-manifest runs)
```

The renderer is **pure**: given `(manifest, template_path)` it returns the rendered HTML string. No file writes, no side effects. Side-effectful atomic writes live in a separate `regen_leaf_write()` wrapper (cookbook #49 tmp-rename pattern).

---

### Step 1 — Parametrise one source file into the template

Pick a representative leaf and replace varying strings with `{{PLACEHOLDER}}` tokens. Don't design a new template; reproduce the existing HTML exactly. Every placeholder must be substitutable back to the source value without losing a single byte — whitespace, attribute order, quoting style, comments all matter.

```html
<title>{{TITLE}} — {{PARENT}} — Luces Umbrarum</title>
<meta name="description" content="{{DESCRIPTION}}" />
…
<nav>
  <a href="analog-new.html"{{NAV_ANALOG}}>Analog</a>
  <a href="digital-new.html"{{NAV_DIGITAL}}>Digital</a>
  <a href="videos-luces-umbrarum-new.html"{{NAV_VIDEOS}}>Videos</a>
</nav>
…
<div class="gallery-grid" data-style="{{STYLE}}">
{{FIGURES}}
      </div>
```

Active-nav state is represented as three independent placeholders, each substituted to ` aria-current="page"` (space-prefixed) or empty string, rather than a single `{{NAV_ACTIVE}}` placeholder with conditional logic. This keeps the template and renderer structurally 1:1 with the source HTML — no conditional branches means the diff surface shrinks to just string substitution.

The repeating-block placeholder (`{{FIGURES}}`) sits on its own line with no leading whitespace. The block content itself carries all indentation. That's the only way to avoid a spurious leading-space on the first repeating element.

---

### Step 2 — Build the renderer (pure function)

```php
// regen-leaf.php
function regen_leaf_html(array $manifest, string $template_path): string {
    $tpl = file_get_contents($template_path);

    $parent_slug = $manifest['parent_slug'];
    $active = ' aria-current="page"';
    $nav_analog  = ($parent_slug === 'analog')  ? $active : '';
    $nav_digital = ($parent_slug === 'digital') ? $active : '';
    $nav_videos  = ($parent_slug === 'videos')  ? $active : '';

    $figures = build_figures_block($manifest['photos'] ?? []);

    return strtr($tpl, [
        '{{TITLE}}'       => $manifest['title']       ?? '',
        '{{PARENT}}'      => $manifest['parent']      ?? '',
        '{{PARENT_SLUG}}' => $parent_slug,
        '{{DESCRIPTION}}' => $manifest['description'] ?? '',
        '{{STYLE}}'       => $manifest['style']       ?? 'masonry',
        '{{NAV_ANALOG}}'  => $nav_analog,
        '{{NAV_DIGITAL}}' => $nav_digital,
        '{{NAV_VIDEOS}}'  => $nav_videos,
        '{{FIGURES}}'     => $figures,
    ]);
}
```

Key choice: `strtr()` for substitution, not `str_replace()`. `strtr()` does a **single pass** over the template — it cannot re-substitute output of a previous key, which is the classic `str_replace` footgun (substitute `{{TITLE}}` to `Mr {{PARENT}}` and the second call clobbers what the first produced).

For the repeating block, write the HTML literally with exact whitespace:

```php
function build_figures_block(array $photos): string {
    $blocks = [];
    foreach ($photos as $p) {
        $blocks[] =
              "      <figure class=\"gallery-item\">\n"
            . "        <a href=\"images/{$p['files']['full_jpeg']}\" class=\"gallery-link\" aria-label=\"{$p['alt']}\">\n"
            . "          <picture>\n"
            . "            <source type=\"image/webp\"\n"
            . "              srcset=\"images/{$p['files']['thumb_1x_webp']} 1x, images/{$p['files']['thumb_2x_webp']} 2x\">\n"
            // … every line indented exactly as it appears in the source HTML
            . "      </figure>";
    }
    return implode("\n", $blocks);  // no trailing newline
}
```

Heredoc (`<<<HTML`) would read nicer but has two traps: PHP 7.3+ indented-heredoc syntax strips leading whitespace based on the terminator column (easy to misalign), and editors often auto-reformat heredoc bodies. Literal string concatenation with `\n` is uglier but leaves zero ambiguity about indentation.

---

### Step 3 — Build the parser (reverse direction)

Needed because `init-manifest.php` has to read every existing leaf and write its per-gallery `manifest.json`. Use a single regex over the whole figure block, not a DOM parser — you want brittleness to shape, so a structural change that would break the renderer *also* breaks the parser and surfaces immediately.

```php
function parse_figures(string $html): array {
    $pattern = '/<figure class="gallery-item">\s*'
             . '<a href="images\/([^"]+)" class="gallery-link" aria-label="([^"]*)">\s*'
             . '<picture>\s*<source type="image\/webp"\s*'
             . 'srcset="images\/([^"]+) 1x, images\/([^"]+) 2x">\s*'
             . '<img src="images\/([^"]+)"\s*'
             . 'srcset="images\/([^"]+) 1x, images\/([^"]+) 2x"\s*'
             . 'alt="[^"]*" loading="lazy">\s*'
             . '<\/picture>\s*<\/a>\s*<\/figure>/';
    // Returns one entry per <figure> with full_jpeg, alt, webp/jpeg variants
}
```

The parser is 90% of what `init-manifest.php` will eventually do; the test harness gives you a head start on that endpoint.

---

### Step 4 — The round-trip harness

```php
// _test-regen.php — CLI-only, checked into the admin/ directory
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }  // never run via HTTP
require_once __DIR__ . '/regen-leaf.php';

$cases = [
    ['slug' => 'dias',        'title' => 'Dias',        'parent' => 'Analog',  …],
    ['slug' => 'schnecke',    'title' => 'Schnecke',    'parent' => 'Analog',  …],
    ['slug' => 'morocco-2023','title' => 'Morocco 2023','parent' => 'Digital', …],  // different style
    ['slug' => 'und-viel-mehr','title' => 'Und viel mehr','parent' => 'Analog',…],  // largest
];

$failures = 0;
foreach ($cases as $meta) {
    $src_html = file_get_contents("{$SOURCE}/{$meta['slug']}.html");
    $photos   = parse_figures($src_html);                  // reverse direction
    $manifest = $meta + ['photos' => $photos];
    $rendered = regen_leaf_html($manifest, $TEMPLATE);     // forward direction

    if ($rendered === $src_html) {
        echo "PASS {$meta['slug']}: " . count($photos) . " figures\n";
    } else {
        $failures++;
        // Print first-diff byte offset + 80-char context on each side
        for ($i = 0; $i < min(strlen($src_html), strlen($rendered)); $i++) {
            if ($src_html[$i] !== $rendered[$i]) {
                echo "  first diff at byte {$i}:\n";
                echo "  src:      " . json_encode(substr($src_html, max(0, $i - 40), 80)) . "\n";
                echo "  rendered: " . json_encode(substr($rendered, max(0, $i - 40), 80)) . "\n";
                break;
            }
        }
    }
}
exit($failures === 0 ? 0 : 1);
```

The CLI-only guard (`PHP_SAPI !== 'cli'`) matters because this file lives inside `admin/` and is therefore deployed alongside the rest of the scaffold. Running it via HTTP would (a) serve a stack of pass/fail lines to the network, and (b) expose the server's absolute filesystem paths through the `$SOURCE` resolution. The guard makes it a no-op over HTTP.

Run it:

```bash
$ php 01_Source/admin/_test-regen.php
PASS dias: 47 figures, byte-identical round-trip
PASS schnecke: 8 figures, byte-identical round-trip
PASS und-viel-mehr: 243 figures, byte-identical round-trip
PASS morocco-2023: 138 figures, byte-identical round-trip
```

One pass is enough to prove the template handles that gallery's structure. Running across *all* representative variants (masonry + uniform styles, Analog + Digital parents, 8 → 243 photos) is what proves the template captures the full variation surface, not just the sample you parametrised.

---

### Why byte-identical matters

"Looks the same" is an insufficient bar:

- **Whitespace drift compounds.** A template that emits `\n  ` where the original had `\n    ` renders visually identically but changes every figure's indentation forever. Over months this becomes impossible to reconcile if you ever need to compare a template-generated page against an old backup.
- **Invisible attributes.** A renderer that drops `loading="lazy"` or swaps attribute order (`alt="x" src="y"` vs `src="y" alt="x"`) produces visually identical output but loses browser optimisations and breaks future regex-based tooling.
- **Diff-based review is free.** After you deploy the admin's first write, a `diff -r public/before/ public/after/` on just the committed leaves tells you *exactly* what mutations happened. If your template is lossy, every diff shows noise + real changes mixed together; the noise drowns out the signal you care about.
- **Future template edits are testable.** The hard part of a template isn't writing it — it's knowing you haven't broken it six months later when you add a placeholder. Re-running the test gives you a go/no-go answer in one second.

The test's cost is one file, ~100 lines. It's paid back the first time a subagent or contributor edits the template and the test catches a regression you'd otherwise find in production.

---

### Gotchas

- **Active-state placeholders must be space-prefixed.** The template has `<a href="analog.html"{{NAV_ANALOG}}>` (no space before the `{{`). The placeholder substitutes to ` aria-current="page"` (leading space) when active, `""` when inactive. If you forget the leading space in the active value, you get `href="analog.html"aria-current="page"` — valid HTML but different bytes. The round-trip test catches this instantly.

- **`strtr()` does not recurse.** If `{{FIGURES}}` content happens to contain a literal `{{TITLE}}` (it won't in this use case, but if you're templating user-supplied content, it could), the second substitution pass never sees it because `strtr` is one-pass. That's the safe default. If you *want* recursive substitution, you have a different (worse) problem.

- **Trailing-newline-on-last-repeating-block.** The figure block is `implode("\n", ...)` — explicitly no trailing newline. The template supplies the `\n` before `</div>` implicitly. Getting this wrong produces a 1-byte diff on every page. Pin it in the README and in a comment in `build_figures_block()`.

- **Hand-edited leaves can't round-trip.** If one leaf got a custom `<style>` block or bespoke class, the test fails on that leaf. The honest path is to either (a) add a `{{EXTRA_STYLES}}` placeholder and widen the template, or (b) document that leaf as "admin-locked" and refuse to mutate it. Don't silently bypass — lying to the test invites the corruption it exists to prevent.

- **CLI-only guard is not a security feature.** It's a "don't embarrass yourself" guard. Never put sensitive data in the test harness (no credentials, no production manifests). Treat it as code that might get served publicly by mistake.

- **Heredoc-based string construction in the renderer is brittle.** Editors auto-reformat heredoc bodies; PHP 7.3's indented-heredoc syntax strips leading whitespace based on terminator column. Use literal concatenation with explicit `\n` for the repeating-block builder — uglier, zero ambiguity. The round-trip test will catch indentation bugs either way, but concatenation never introduces them in the first place.

- **Widen the test across all styles you use.** This pattern's value scales with coverage. Running the test on one leaf proves one gallery's shape. Running it across every structural variant (layout style, parent section, edge sizes like 1-photo and 500-photo galleries) is what certifies the template handles the full variation surface.

---

### Composes with

- Cookbook **#49** (feedback form with admin) — Basic-Auth + flat-file JSON + same-origin CSRF guard + `flock`/tmp-rename atomicity. Use as the HTTP-handler shell around the renderer. The round-trip invariant lives one layer inside that.
- Cookbook **#42** (`<dialog>` lightbox) and **#53** / **#54** (masonry / uniform grids) — the template captures these layout choices via the `{{STYLE}}` placeholder. The round-trip test proves the template substitution is lossless across both.
- Cookbook **#55** (preview-via-suffix deploy) — if you're rolling out an admin migration, the `-new.html` preview suffix lets you run the admin on a shadow copy of the site before swapping. The round-trip test on the preview branch validates that the shadow === production before you rename.

---

### Reference implementation

- Renderer: `lucesumbrarum.photos/admin/regen-leaf.php` (PHP 8.x, ~90 lines)
- Harness: `admin/_test-regen.php` (CLI-only, ~95 lines)
- Template: `admin/templates/leaf.html.tpl` (68 lines, 9 placeholders)
- Validation run 2026-04-23: 4 leaves × {47, 8, 243, 138} figures = 436 total, zero-diff on all four. See `docs/sessions/2026-04-23.md` Session 4 for build narrative.
