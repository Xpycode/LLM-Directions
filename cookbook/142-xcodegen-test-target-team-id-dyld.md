# 142 — xcodegen unit-test target won't load: dyld "different Team IDs"

**Best for:** any macOS xcodegen project where you add a `bundle.unit-test` target and `xcodebuild test`
suddenly fails at *load* time (the code compiles fine) with a `dlopen` / "different Team IDs" error.

## Symptom

`xcodebuild test` builds successfully, then dies before any test runs:

```
Failed to load the test bundle. … The bundle "AppTests" couldn't be loaded.
dlopen(.../AppTests.xctest/Contents/MacOS/AppTests, 0x0109): tried: …
  '.../AppTests.xctest/Contents/MacOS/AppTests'
  (code signature … not valid for use in process:
   mapping process and mapped file (non-platform) have different Team IDs)
** TEST FAILED **
```

The wall of `dlopen` "tried:" paths is noise — the **only** line that matters is
**`different Team IDs`**. This is a code-signing problem, not a build or path problem.

## Why it happens

A macOS unit-test bundle is a **plugin loaded into the host app's process** (`TEST_HOST` /
`BUNDLE_LOADER`). dyld refuses to map a bundle whose signing **Team ID** differs from the process it's
being injected into. So the host app and the `.xctest` bundle MUST sign with the **same**
`DEVELOPMENT_TEAM`.

The trap with xcodegen: you typically wire `DEVELOPMENT_TEAM` into the app target via a
`configFiles:` xcconfig (so it can be overridden per-machine). When you add a test target, it's easy to
give it `TEST_HOST`/`BUNDLE_LOADER` and **forget the xcconfig** — so the test target has no team set.
Automatic signing then picks a *default* team, which on a machine with **more than one** Apple
Development identity (e.g. a personal team AND an org team) is often a **different** team than the app's.
App = team A, test bundle = team B → dyld rejects the load.

## Fix

Give the test target the **same** `configFiles` xcconfig the app uses (so it inherits the same
`DEVELOPMENT_TEAM`, including any per-machine `*.local.xcconfig` override) **plus**
`CODE_SIGN_STYLE: Automatic` (the test target does not inherit the app target's `settings.base`):

```yaml
targets:
  App:
    type: application
    platform: macOS
    settings:
      base:
        CODE_SIGN_STYLE: Automatic
        # DEVELOPMENT_TEAM comes from the xcconfig (per-machine override friendly)
    configFiles:
      Debug: Config/Debug.xcconfig          # contains: DEVELOPMENT_TEAM = XXXXXXXXXX

  AppTests:
    type: bundle.unit-test
    platform: macOS
    sources: [path: AppTests]
    dependencies:
      - target: App
    settings:
      base:
        GENERATE_INFOPLIST_FILE: YES
        # Must sign with the SAME team as the host app or dyld refuses to load the
        # .xctest into the app process ("different Team IDs"). Inherit team (+ any
        # per-machine override) from the SAME xcconfig the app uses.
        CODE_SIGN_STYLE: Automatic
        BUNDLE_LOADER: $(TEST_HOST)
        TEST_HOST: $(BUILT_PRODUCTS_DIR)/App.app/Contents/MacOS/App
    configFiles:
      Debug: Config/Debug.xcconfig          # <-- the line everyone forgets
```

Then `xcodegen generate` and re-run. (`Config/Debug.xcconfig` holds `DEVELOPMENT_TEAM = XXXXXXXXXX`;
keeping it in the xcconfig — not in `settings.base` — lets a gitignored `Debug.local.xcconfig` override
the team per-machine, and because BOTH targets read the same file they can never disagree.)

## Verify

```bash
xcodebuild test -scheme App -destination 'platform=macOS' -derivedDataPath build \
  2>&1 | grep -E "Executed [0-9]+ test|TEST SUCCEEDED|different Team IDs"
# -> "** TEST SUCCEEDED **"
```

Sanity-check what you're actually verifying: a single placeholder test that does `@testable import App`
+ `XCTAssertTrue(true)` proves the bundle loads AND the app module is reachable before you write real
tests. (`@testable import` needs Debug `ENABLE_TESTABILITY=YES`, which is on by default.)

## Notes / related

- The "Cannot find type X in scope" / "'main' attribute cannot be used…" / "No such module 'XCTest'"
  editor errors that appear while wiring this up are **SourceKit/LSP false positives** (the index
  analyzes files without the target's compile context). The compiler (`xcodebuild`) is authoritative.
- Pairs with #47 / #58 / #119 / #140 (xcodegen recipes) and #00 (App Shell Standard).

*Source: CompressPhotos `01_Project/project.yml`, Wave 1, 2026-06-29.*
