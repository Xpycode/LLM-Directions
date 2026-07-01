# Strip `<?php …?>` before feeding source to an HTML parser — or it captures the whole script as "text"

**Source:** Translations (`81-Translations`, `01_Project/translations/extract_web.py`) — a Python string-extractor scanning `.php` site files for user-facing HTML copy. General gotcha for any **text/string extraction over PHP-templated sites**; sibling-in-spirit to [[24-web-gotchas]].

`html.parser.HTMLParser` (Python) — like most lenient HTML parsers — has **no concept of PHP**. Anything that isn't a recognized tag becomes a **data node**, so it fires `handle_data` on it. A `.php` file is mostly server code with small islands of HTML, so an HTML parser **inverts what you want**: it hands you the PHP source (regex literals, SQL, `$variables`, `=>` arrays) as "visible text" and ignores almost nothing. In the Translations scan this dumped **entire admin scripts** into the term table as 35 backslash-laden blobs (hundreds of junk "terms").

The fix is to remove PHP blocks **before** parsing. The trap is the regex: pure-PHP files (admin endpoints, includes) follow the PHP convention of **omitting the closing `?>`** — the file opens with `<?php` and just ends. A naive `<\?.*?\?>` requires a closing tag, matches **nothing**, and the whole file sails through unchanged. Anchor the alternation to `?>` **or** end-of-file (`\Z`):

```python
import re

# PHP code blocks are not HTML. Match to "?>" OR end-of-file (\Z) —
# pure-PHP files omit the closing tag, so "?>"-only would miss them entirely.
_PHP_BLOCK = re.compile(r"<\?.*?(?:\?>|\Z)", re.DOTALL)

def extract_html(path):
    src = path.read_text(encoding="utf-8", errors="replace")
    src = _PHP_BLOCK.sub(" ", src)        # drop PHP; keep only the template HTML a user sees
    parser = _Collector(str(path))
    parser.feed(src)
    ...
```

Two details that matter:
- **`re.DOTALL`** so `.*?` spans newlines (PHP blocks are multi-line). Without it the block only strips to the end of its first line.
- **Non-greedy `.*?`** so a file with several `<?php …?> … <?php …?>` islands strips each block, not everything between the first `<?` and the last `?>` (which would also eat the HTML in between).
- Replace with a **space**, not empty string, so two tokens that hugged a PHP block (`<li><?=$x?></li>`) don't fuse into one bogus word.

---

## The general lesson

A parser only protects you from the grammar it knows. Feeding it a **superset language** (HTML-with-PHP, HTML-with-template-tags, Markdown-with-frontmatter) silently reclassifies the foreign syntax as content. Before parsing, **strip the foreign islands** (`<?php ?>`, `{{ }}`, `<% %>`, `---\n…\n---`) — and when you write the stripper, account for the **unterminated-at-EOF** case, because that's the one a closing-delimiter regex misses.

## When to apply this

- Extracting visible text / i18n strings / word counts from `.php`, `.erb`, `.ejs`, `.twig`, `.blade.php`, or any server-templated HTML with a lenient HTML parser.
- Any time "I parsed the HTML but got code/garbage in the output" — check whether the source carries a template language the parser doesn't understand.

**Skip when:** the source is genuinely pure HTML (`.html` with no embedded server tags), or you're using a PHP-aware tool (`token_get_all()`, a real Blade/Twig compiler) that already separates code from markup.

## Companion patterns

- **[[24-web-gotchas]]** — the broader web-platform gotcha file this belongs alongside.
- The same "strip the foreign island, handle the unterminated case" shape recurs for YAML frontmatter and `<script>`/`<style>` bodies (the latter handled by skipping those tags inside the parser, not pre-stripping).

---

*Drafted 2026-06-24 from the Translations string-extractor. The keeper: an HTML parser will faithfully report PHP source as user-visible text, and the regex that strips it must match to end-of-file, not just `?>`, because pure-PHP files don't write the closing tag.*
