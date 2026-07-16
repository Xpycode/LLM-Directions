# 164 — Verifying a running macOS app from outside: what you can't read, and what to probe instead

**Tags:** verification, debug dylib, TerminalTutorial.debug.dylib, strings, nm, Xcode 16, SIP, ps -E, ps eww, environment, lsof, cwd, pgrep, ppid, accessibility, AXTextArea, AXScrollBar, SwiftTerm, false positive, screencapture
**Extracted from:** TerminalTutorial (2026-07-16)

## Problem

You've built a change and want to prove it actually took effect in the *running* app — not just
that the build succeeded. Every obvious probe on macOS has a failure mode that produces a
**confidently wrong answer**: a good build looks broken, or an unrelated process looks like proof.

## Why it's hard / the gotchas

**1. `MacOS/<App>` is not your app** (Xcode 16 debug builds).
The executable is a ~58KB launcher stub; all the Swift code lives beside it in
`<App>.debug.dylib` (megabytes). `strings`/`nm` on the executable come back empty and make a
perfectly good build look like it never compiled your change.

```bash
# ✗ always empty                     # ✓ the actual code
strings .../MyApp.app/Contents/MacOS/MyApp
strings .../MyApp.app/Contents/MacOS/MyApp.debug.dylib | grep 'my-literal'
nm      .../MyApp.app/Contents/MacOS/MyApp.debug.dylib | grep '11MyTypeName'
```

Also: Swift **small strings** (≤15 UTF-8 bytes) are encoded inline as immediates, not in
`__cstring` — so short literals won't appear in `strings` output at all, in either file. Grep for
a longer literal, or check symbols.

**2. A live process's environment is unreadable.** SIP makes `ps -E` / `ps eww` return nothing,
even for your own processes. There is no `/proc`.

**3. `pgrep`/`ps | grep` finds other people's processes.** Terminal emulators spawn shells that
look exactly like yours — Warp launches `zsh --no_rcs`, which matched a `--no-rcs` change under
test and produced five convincing false positives. **Always confirm the ppid**:

```bash
APP=$(pgrep -x MyApp); SH=$(pgrep -P $APP | head -1)   # child of THIS app, not any zsh
ps -p $APP -o lstart=                                   # and confirm it's the fresh launch —
                                                        # pids wrap, so "higher pid = newer" is false
```

`killall` silently failing + `open` re-focusing the existing instance is the standard way to end
up testing the *old* binary. Check `lstart` against your build time.

**4. Not every view exposes text to accessibility.** SwiftTerm's terminal view offers only an
`AXScrollBar` — no `AXTextArea`, so the terminal's contents cannot be read via System Events.
Accessibility works well for structure (`role of every UI element of …`) but you cannot assume
text is there. `screencapture` needs a Screen Recording grant the session may not have.

## The technique: behaviour probes

When you can't *read* the state, make the process **reveal it by acting**. Pick an action whose
success and failure land in observably different places.

```bash
# Prove a spawned shell's $HOME without reading its env (SIP blocks that).
# `cd` with no argument is DEFINED as "go to $HOME" — so the shell reports HOME by moving.
osascript -e 'tell application "System Events" to tell process "MyApp" to keystroke "cd"' \
          -e 'tell application "System Events" to key code 36'
sleep 1
lsof -a -p $SH -d cwd -Fn | grep ^n        # where it landed IS its $HOME
```

The test is only worth running if the pass and fail states are distinguishable *before* you run
it. State both out loud first ("sandbox → pinned; `/Users/me` → my filter failed"), or you'll
read whatever you expected into the output.

## Bonus: SourceKit is not the build

`No such module 'X'`, `Cannot find 'Type' in scope` fire constantly after edits — the indexer lags
SPM resolution and cross-file scope. **`xcodebuild` is the authority.** (See #47 §5.) Don't chase
red squiggles that a clean build contradicts.

Companion: **#163** (SwiftTerm/`execve` env — the change this technique was built to verify).
