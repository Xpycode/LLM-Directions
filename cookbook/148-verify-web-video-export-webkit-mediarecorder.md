# 148 · Verify a web app's video export end-to-end (no Chrome) — Playwright WebKit + MediaRecorder + magic-byte check

**Problem.** A browser-side tool renders to `<canvas>` and exports a **video file**
via `MediaRecorder` + `canvas.captureStream()` (a test-pattern generator, a screen-
recorder UI, a GIF/clip maker). You want to prove — headless, in CI or before
handing it back — that it actually (a) renders every view, (b) throws no console
errors, and (c) produces a **playable video**, not a 0-byte blob or a WebM when you
promised MP4. Two snags:
1. **No Chrome on the machine** → the usual headless-Chrome tooling fails.
2. A screenshot proves *rendering* but says nothing about the **encode** — the risky
   part is the `MediaRecorder` round-trip, and the app's own "Saved ✓" status text is
   not evidence.

**Solution.** Drive the page with **Playwright + WebKit** (Safari's engine — the
*right* renderer to test on a Mac, and what the user's browser will actually run;
Playwright downloads it, no Chrome needed). Verify in three passes: render+console,
a **codec-support probe**, and a real **download round-trip** validated by the file's
**magic bytes** — trust the container header, not the exit code or the app's status.

Used for: **TestPatternGenerator** (`web/` prototype — SMPTE bars / ramp / grid, PNG
+ in-browser MP4). Companion to #77 (JSX→PNG via WebKit) and #73 (headless verify
without Screen-Recording): #77 screenshots, this one proves an *encode*.

---

## Serve over HTTP, not `file://`
`MediaRecorder` needs a **secure context**; `localhost` qualifies, `file://` is
flaky in WebKit. Relative `<script src>` also just works over HTTP. So:
```bash
cd web && python3 -m http.server 8781    # python3 ships with Xcode CLT
```
Keep Playwright + the WebKit build **out of the repo** (scratchpad or `/tmp`):
```bash
cd "$SCRATCH" && npm init -y >/dev/null && npm i playwright && npx playwright install webkit
```

## Pass 1 + 2 — render every view, collect errors, probe the real codec
```js
import { webkit } from 'playwright';
const b = await webkit.launch();
const page = await b.newPage({ viewport: { width: 1280, height: 800 }, deviceScaleFactor: 2 });
const errors = [];
page.on('console', (m) => m.type() === 'error' && errors.push(m.text()));
page.on('pageerror', (e) => errors.push('PAGEERROR: ' + e.message));   // uncaught JS

await page.goto('http://localhost:8781/index.html', { waitUntil: 'networkidle' });
for (const id of await page.$$eval('.pattern-btn', bs => bs.map(b => b.dataset.id))) {
  await page.click(`.pattern-btn[data-id="${id}"]`);
  await page.screenshot({ path: `${OUT}/shot_${id}.png` });          // eyeball each view
}
// What will the USER's browser actually emit? Ask MediaRecorder in-page, not from memory.
const mime = await page.evaluate(() => {
  const c = ['video/mp4;codecs=avc1.42E01E','video/mp4','video/webm;codecs=vp9','video/webm'];
  return { hasRec: typeof MediaRecorder !== 'undefined',
           supported: c.filter(m => window.MediaRecorder && MediaRecorder.isTypeSupported(m)) };
});
// WebKit → MP4/H.264 available; Chromium → WebM. This is why the app should pick, not assume.
```

## Pass 3 — the encode round-trip, validated by magic bytes
The app downloads via a blob URL + `a.download` click → Playwright surfaces that as a
**`download` event** you intercept and `saveAs`. Shorten the clip first so it's fast.
```js
await page.$eval('#duration', el => { el.value = '1'; el.dispatchEvent(new Event('input', {bubbles:true})); });
const dl = page.waitForEvent('download', { timeout: 30000 });
await page.click('#btnVideo');
const file = `${OUT}/out_${(await dl).suggestedFilename()}`;
await (await dl).saveAs(file);
await b.close();
```
Then **trust the bytes**, not the app's "Saved ✓":
```bash
xxd "$file" | head -1
# MP4  → "....ftyp" with isom/iso5/mp42 brand   (offset 4 = 'ftyp')
# WebM → "1a45 dfa3" EBML header
ffprobe -v error -show_entries stream=codec_name,width,height -of default=noprint_wrappers=1 "$file"  # if available
```
A valid `ftyp`/EBML header + non-trivial size = a real file. (A static pattern
compresses to a few KB/sec — small is expected, **zero** is the failure.)

## Gotchas
- **`canvas.captureStream(fps)` needs a redraw loop** — a static canvas may push no
  frames. Drive `requestAnimationFrame`→`draw()` for the whole duration (also makes
  future *animated* patterns "just work"). Recording a never-redrawn canvas yields an
  empty/short file that still has a valid header — so also assert **duration/size**, not just magic bytes.
- **The status text lies by omission.** `MediaRecorder` errors are async; the button
  handler can report success before a chunk fails. The downloaded file is the oracle.
- **Codec is browser-dependent** — WebKit records MP4/H.264, Chromium records WebM.
  Have the app `MediaRecorder.isTypeSupported()`-probe a preference list and name the
  output by the chosen MIME; verify the probe result rather than hard-coding `.mp4`.
- **`page.$eval`/`page.evaluate` are Playwright APIs**, not JS `eval()` — a security
  linter may flag them; they run code *in the page*, which is the whole point.
- **`deviceScaleFactor: 2`** for retina-crisp screenshots; keep `node_modules` + the
  ~100 MB WebKit build in scratchpad/`/tmp` so they never land in the repo.

## See also
- `77-jsx-prototype-to-png-webkit-playwright.md` — WebKit screenshots of a design prototype (render only)
- `73-verify-hud-without-screen-recording.md` — headless verification, same permission-free mindset
- `35-asyncstream-bounded-fanout.md` — when the export is a native fan-out instead of a browser encode
