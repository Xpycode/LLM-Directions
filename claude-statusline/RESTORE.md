# Claude Code Status Line — Backup & Restore

A custom Claude Code status line that shows, on one row:

```
Opus 4.8 (1M context) | 📁ClaudeSessions | ███████░░░░░ 111k / 200k (55%) | ⏱ 5h 12.0M (16%) · 7d 29.5M (6%)
```

- **Context gauge** — tokens in context vs a manual `CLEAR_BUDGET` (default 200k, your `/clear` point). Blue → gold at 70% → red at 95%.
- **5h** — tokens used in the current 5h window (% of `CAP_5H`). No reset countdown: ccusage only knows clock-aligned blocks, not Anthropic's true rolling reset — check `/usage` for the real reset time.
- **7d** — rolling 7-day tokens (% of `CAP_WEEK`).

Usage numbers come from [`ccusage`](https://github.com/ryoppippi/ccusage), background-cached to `~/.claude/.usage-cache.json` and refreshed at most every 120s, so the status line never blocks.

> **Wiring (dotfiles pattern):** `~/.claude/statusline.sh` is a **symlink** into this repo — the file here *is* the live script. Editing the status line edits this backup directly (no copy step); `git commit` here snapshots a version. Keep this repo at a stable path or the symlink dangles.

## Restore after a machine reset / on a new Mac

1. **Symlink the script into place** (this repo file is the source of truth):
   ```bash
   # run from the repo root
   ln -sf "$(pwd)/claude-statusline/statusline.sh" ~/.claude/statusline.sh
   ```
   The file is already executable (git mode 755). After this, `~/.claude/statusline.sh` points into the repo, so future edits auto-sync back here.

2. **Wire it up** — merge the `statusLine` key from `settings-statusLine-snippet.json` into `~/.claude/settings.json` (top level; don't overwrite the whole file):
   ```json
   "statusLine": { "type": "command", "command": "~/.claude/statusline.sh", "padding": 0 }
   ```

3. **Dependencies** (macOS):
   - `jq` — `brew install jq`
   - `python3` — system-provided
   - `ccusage` — auto-fetched via `npx`; needs Node/`npx` on PATH and network on first run. The 5h/7d figures show `(loading…)` until the first background refresh populates the cache (~5s).

4. **Recalibrate the caps** (optional — they drift if your plan changes). The true limit % isn't exposed to scripts, so derive it:
   - Run `/usage` in Claude Code, note the 5h % and weekly %.
   - Get current tokens: `npx ccusage@latest blocks --json` (active block = 5h; sum non-gap blocks in last 7 days = weekly).
   - `CAP_5H = 5h_tokens ÷ (5h_pct/100)`, `CAP_WEEK = week_tokens ÷ (week_pct/100)`.
   - Edit the values at the top of `statusline.sh`.
   - Recalibrate when a limit is at a healthy 30–60% (a tiny % amplifies error).

## Tunables (top of `statusline.sh`)

| Setting | Meaning |
|---|---|
| `CLEAR_BUDGET` | Context budget the gauge fills toward (your `/clear` point) |
| `SHOW_LAST_MSG` | `1` adds a second row echoing your last message; `0` = single row |
| `CAP_5H` / `CAP_WEEK` | Token caps for the 5h/weekly `%` (calibrated from `/usage`) |
| `USAGE_TTL` | Min seconds between background `ccusage` refreshes |
| `COLOR` | Accent color theme |

## Caveats

- Caps are **calibrated snapshots**, not live; the real limit % lives behind `/usage` (an Anthropic API call) and is never exposed to status line scripts.
- The 5h **reset countdown** is `ccusage`'s clock-aligned block, **not** Anthropic's true session window (which starts at your first message) — trust `/usage` for the actual reset time. The token counts are accurate; only the timer can drift.

_Last calibrated 2026-06-02 — plan: Max (5x). CAP_5H=73.5M, CAP_WEEK=475M._
