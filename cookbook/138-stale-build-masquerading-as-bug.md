## A reported bug your probe can't reproduce? Check the running binary's build time FIRST

**Source:** SearchAway — `01_Project/SearchAwayTests/PhotopillsDiagnosticProbe.swift` (gated engine probe) + the diagnosis recipe below. Surfaced during the `photopills-moon` "every row is doubled" report. Added 2026-06-25.

**Use case:** A user reports a bug with a screenshot — the HUD shows every result row **twice**. You've already shipped a fix for exactly this class of bug (here: Bug B, ghost duplicates — same path, new inode). Before you re-open the code and start theorizing about where a *new* duplication path crept in, rule out the cheapest explanation: **the user is running an old binary that predates your fix.** This bites hardest when the app is launched out-of-band — a global hotkey, an `LSUIElement` agent, a login item — so a plain `xcodebuild build` (Debug) + `xcodebuild test` *does not* replace the **Release** app the user actually summons. Tests green + "BUILD SUCCEEDED" feels like done; the running process is still last week's binary.

### Why theory wastes an hour here

Every layer you trace will look correct, because it *is* correct in the current source. In this case the engine dedups by path (Bug B), the view-model `reconcile` dedups by `FileID`, and the SwiftUI `ForEach` keys on `FileID` — none of them can manufacture a duplicate row. You can burn a long time confirming each one is innocent. The duplication isn't in the code you're reading; it's in the **binary that isn't running that code yet.**

### Diagnosis recipe (cheap → decisive)

**1. Reproduce against the REAL data with a gated probe that calls the engine directly** — bypass the UI, the view-model, delivery. If the engine is clean, the bug is either above the engine *or* in a stale build:

```swift
// Gated so it never runs in a normal pass. Run under -O (Debug -Onone can livelock broad scans).
let store = try IndexStore.load(realIndexURL)         // the user's actual on-disk index
let res = store.topMatching("photopills-moon", limit: 5000, sortKey: .relevance)
var byPath: [String: Int] = [:], byID: [String: Int] = [:]
for r in res {
    byPath[r.entry.path, default: 0] += 1
    byID["\(r.entry.fileID.dev)/\(r.entry.fileID.inode)", default: 0] += 1
}
print("rows \(res.count) · dup paths \(byPath.filter{$0.value>1}.count) · dup ids \(byID.filter{$0.value>1}.count)")
// → "rows 4 · dup paths 0 · dup ids 0"  ⟹ engine is clean; the doubling is NOT here.
```

(env-gate caveat: `xcodebuild test` runs the test in a separate host process, so a shell `FOO=1` does **not** reach `ProcessInfo.environment`, and `-test-env` isn't accepted by older `xcodebuild`. To force a one-off run, temporarily replace the `XCTSkipUnless` guard, then restore it.)

**2. Find the running binary and stamp it:**

```bash
ps aux | grep -i "[M]yApp.app"        # → …/DerivedData/MyApp-…/Build/Products/Release/MyApp.app/Contents/MacOS/MyApp
stat -f "built: %Sm" "<that path>"     # → built: Jun 25 03:41:10 2026
```

**3. Compare against when the fix landed:**

```bash
git log --pretty="%h %cd %s" --date=format:'%Y-%m-%d %H:%M' -8
# 6befd0c 2026-06-25 05:42  the fix
# 44aa60c 2026-06-25 04:54  the earlier fix this bug needed
# running binary: 03:41  →  predates BOTH. Case closed.
```

Binary mtime **earlier than** the fix commit ⟹ it's a stale build, not a regression. Done.

### Fix

```bash
killall "MyApp" 2>/dev/null                 # kill the stale instance first
xcodebuild -project … -scheme MyApp -configuration Release -destination 'platform=macOS' build
open "…/Build/Products/Release/MyApp.app"   # relaunch the fresh binary
```

### The standing lesson

After any change to an **engine / ranking / core data path**, rebuild **Release and relaunch** before calling it "verified in the app." Debug-build + green tests proves the *source* is right; it says nothing about the binary the user is summoning with a hotkey. Bake `killall → Release build → open` into your post-change ritual for hotkey/agent apps. See also `73-verify-hud-without-screen-recording.md` (driving the real HUD) and `110-macos-settings-pane-deeplink-verify.md` (verify, don't assume).
