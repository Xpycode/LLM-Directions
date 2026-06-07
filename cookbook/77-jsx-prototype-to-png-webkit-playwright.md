# 77 · Render a Babel-in-browser JSX design prototype to PNGs (no Chrome)

**Problem.** A design handoff ships as a React + `@babel/standalone` prototype
(`.html` that `<script type="text/babel" src="*.jsx">`-loads sibling modules from a
CDN). You want static PNGs of each design section — to drop in docs, compare
against your build, or review offline. Two snags:
1. The prototype is a **pan/zoom design canvas** — a normal screenshot captures the
   zoomed viewport, not the artboards at natural size.
2. **No Chrome on the machine** → the usual headless-Chrome screenshot tools fail.

**Solution.** Two parts: (a) a **flat-render harness** HTML that mounts the section
components in normal document flow (bypassing the pan/zoom canvas), and (b)
**Playwright driving WebKit** (Safari's engine — already the right renderer on a
Mac, and Playwright will download it; no Chrome needed).

Used for: **QuickStatsPanel** (`02_Design/render-all.html` → `design-renders/*.png`).

---

## Why `file://` fails, and the serving requirement
Babel-in-browser prototypes **fetch** the sibling `.jsx` files at runtime, which the
browser blocks under `file://`. Serve the folder over HTTP:
```bash
cd <design-folder> && python3 -m http.server 8765   # python3 ships with Xcode CLT
```

## Part A — flat-render harness
Most design-canvas wrappers guard their context access (`ctx && ...`) so the section
components render fine **without** the canvas provider. Make a sibling HTML that
loads the same modules but renders the sections stacked in flow:

```html
<style>
  #root { width: max-content; }            /* let wide artboard rows extend */
  .dc-header { display: none !important; }  /* hide per-artboard editor chrome */
</style>
<!-- same <script src> includes as the prototype (KEEP the SRI integrity= hashes) -->
<script type="text/babel">
  function FlatApp() {
    return <div style={{padding:40}}>
      {/* wrap each section so it can be screenshotted individually */}
      <div data-flat-section="hero"><SecHero active={null} onTile={()=>{}} onGear={()=>{}}/></div>
      {window.SecIcon && <div data-flat-section="icon"><SecIcon/></div>}
      {/* …the rest… */}
    </div>;
  }
  function boot() {                                  // Babel compiles async — poll, then render
    if (!window.SecHero) { setTimeout(boot, 50); return; }
    ReactDOM.createRoot(document.getElementById('root')).render(<FlatApp/>);
    requestAnimationFrame(()=>requestAnimationFrame(()=>
      document.body.setAttribute('data-render-ready','1')));   // capture-ready flag
  }
  boot();
</script>
```
Place the harness **one level up** from the bundle and reference jsx via subpath
(`src="bundle/tokens.jsx"`) to keep the handoff bundle pristine. Carry over the
`integrity="sha384-…"` SRI hashes from the original HTML (security hooks flag bare
CDN tags).

## Part B — Playwright + WebKit capture
```bash
mkdir -p /tmp/shot && cd /tmp/shot && npm init -y >/dev/null
npm i playwright && npx playwright install webkit     # ~100MB one-time, kept out of repo
```
```js
const { webkit } = require('/tmp/shot/node_modules/playwright');
(async () => {
  const b = await webkit.launch();
  const page = await b.newPage({ deviceScaleFactor: 2 });          // 2× = retina-crisp
  await page.goto('http://localhost:8765/render-all.html', { waitUntil: 'networkidle' });
  await page.waitForSelector('body[data-render-ready="1"]');        // wait for Babel+paint
  await page.waitForTimeout(600);                                   // fonts/gradients settle
  await page.screenshot({ path: OUT+'/00-all.png', fullPage: true });
  for (const el of await page.$$('[data-flat-section]'))            // tight per-section PNGs
    await el.screenshot({ path: `${OUT}/${await el.getAttribute('data-flat-section')}.png` });
  await b.close();
})();
```

## Gotchas
- **`deviceScaleFactor: 2`** is what makes text/gradients sharp; without it PNGs look soft.
- Wait on an explicit **ready flag** the harness sets after first paint, not a fixed
  sleep — Babel-standalone compile time varies.
- `element.screenshot()` clips to the element box → clean per-section crops without
  cropping math. `fullPage` gives the whole stack.
- Keep `npm`/browser install in `/tmp` (or `.gitignore` it) so `node_modules` and the
  ~100MB WebKit build never land in the repo.
- WebKit ≈ Safari, so it renders the design exactly as the user's default browser would.

## See also
- `76-macos-appicon-coregraphics-generator.md` — build the app icon from the same handoff
- `73-verify-hud-without-screen-recording.md` — headless verification, related tooling mindset
