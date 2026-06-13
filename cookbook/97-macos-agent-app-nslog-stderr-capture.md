# 97 — Debugging a launched macOS app: `NSLog` is invisible to `log show` for an `open`-launched app → run the binary directly and capture stderr

**Extracted from:** LaunchAway (2026-06-13)

You're debugging a running macOS app (especially an `LSUIElement` agent app with no console UI). You sprinkle `NSLog("DIAG: …")` to trace state, then read it back with:

```bash
log show --predicate 'process == "LaunchAway"' --last 2m --info --debug
```

…and get **zero lines** — not "no failures," literally **no output at all**. You misread that absence as "the bad branch never ran" and chase ghosts. The logging itself is silently going nowhere you're looking.

## Why it happens

How you launch the app determines where `NSLog`/stderr goes and whether the `process ==` predicate matches:

- **`open /path/to/App.app`** hands launch to **LaunchServices**; the process is reparented under `launchd`, and `NSLog` output does **not** reliably surface under a `log show --predicate 'process == "<Name>"'` query (the predicate frequently matches nothing for an `open`-spawned debug build). You end up blind.
- The unified-log story for `NSLog` from a third-party signed-for-dev app is inconsistent across launch contexts; **don't trust `log show` as your only channel.**

The dangerous part isn't "no logs" — it's that **absence looks like a clean result**. An `|| echo "no failures"` guard that never fires, a grep that returns nothing — both read as success when the truth is your probe was disconnected.

## The fix — launch the binary directly, redirect stderr to a file

`NSLog` (and Swift `print` to stderr) writes to the process's stderr. Launch the executable **inside** the `.app` bundle directly from the shell and redirect — now every line lands in a file you fully control, with no unified-log indirection:

```bash
APP=$(find ~/Library/Developer/Xcode/DerivedData/<Proj>-*/Build/Products/Debug \
        -maxdepth 1 -name '<Proj>.app' | head -1)
BIN="$APP/Contents/MacOS/<Proj>"

killall <Proj> 2>/dev/null || true
nohup "$BIN" > /tmp/app_stdout.log 2> /tmp/app_stderr.log &
disown                       # survive the shell that launched it
sleep 2
grep "DIAG" /tmp/app_stderr.log     # ← your NSLog lines, reliably
```

- **`nohup … & disown`** keeps the app alive after the launching shell exits, while stderr stays attached to `/tmp/app_stderr.log`. (A bare `… &` inside a one-shot script gets orphaned/killed when the script returns; `nohup`+`disown` is what makes the capture persist across separate tool calls.)
- The app still runs as a **real GUI app** (it's the same Mach-O, same bundle, same `Info.plist`/`LSUIElement`) — you can summon its hotkey, type, click — but its `NSLog`/stderr is now in a file you can `grep` between interactions.
- A **borderless/`log stream … | grep > file &`** pipeline is fragile here: the backgrounded stream gets orphaned and "completes" immediately. Prefer the direct-launch redirect; it's a plain file, not a live pipe.

## The bug-hunt discipline this enables (layered diagnostics)

With a reliable channel, drive a runtime bug to ground in layers, each ruling out a stratum, **removing every probe afterward**:

1. **A real-dependency unit test** to prove the backend (index/matcher/engine) is correct in isolation → e.g. "96 apps indexed, `saf` → expected result." If green, the bug is in the view/binding/runtime, not the model.
2. **A `body`-level `NSLog`** (`let _ = NSLog("render: …"); return ZStack { … }`) to prove whether SwiftUI `body` re-runs on each interaction — separates "data didn't change" from "view didn't re-render" from "view rendered stale."
3. **A targeted reachability probe** (e.g. "can `Bundle(url:)` read this exact path? does the enumerator list it?") to localize an OS-level quirk.

Each layer is `NSLog`-driven, read via the stderr file, then deleted. (In LaunchAway this sequence proved the engine was perfect, isolated the bug to a SwiftUI `ForEach` identity issue — see #98 — and separately surfaced the Cryptex-symlink indexing miss — see #96.)

## Caveats

- For a **release/notarized** build or a genuinely backgrounded daemon, the unified log (with `OSLog`/`Logger`, not `NSLog`) is the right durable channel — see #90 for an off-main file logger you ship. This pattern is a **dev-loop** technique: fast, zero-infrastructure, throwaway.
- Remove all `DIAG` `NSLog`s before committing (`grep -rn DIAG Sources/` as a gate).
- `print(…)` in Swift goes to **stdout**, `NSLog`/`FileHandle.standardError` to **stderr** — redirect both (`> out 2> err`) so you don't lose half your trace.

Source: LaunchAway debugging session (`AppDelegate`/`LauncherView` `DIAG` probes, all removed). Pairs with #96 (the indexing miss this surfaced), #98 (the SwiftUI identity bug this localized), #90 (the durable shipped logger, for contrast), #73 (verify-without-screen-recording — the other "observe a running app" technique).
