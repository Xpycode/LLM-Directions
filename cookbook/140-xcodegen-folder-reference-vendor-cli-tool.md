# #140 — Vendor an opaque CLI/tool tree into a macOS app via an `xcodegen` folder-reference (+ injectable path for tests)

**Extracted from:** PhotoIngest (2026-06-28) — bundling the ExifTool 13.58 pure-Perl tree (T1.2) + the injectable `ExifToolRunner` (T2.5).

You need to ship a third-party command-line tool *and its support tree* (a Perl script + `lib/`, a Node bundle, a binary + data files) **inside** a macOS `.app` so it lands at `Contents/Resources/<tool>/` and runs at launch. Two things bite:

1. If the tree sits inside the target's compiled `sources:` path, xcodegen's glob treats every `.pl`/`.pm`/`.js`/`.rb` as a **build input** — Xcode tries to process them, or they pollute the project.
2. Copying via a `postBuildScripts` run-script works but invites the **sandbox-deny + "runs every build"** double-failure (see #58).

A **folder-reference resource** sidesteps both: it copies the directory **verbatim** into the bundle, no script, no sandbox grant, no incremental-build warning.

---

## The fix — two parts

### 1. Put the tree OUTSIDE the Swift sources path, reference it as a `type: folder`

Lay the repo out so the vendored tree is a **sibling** of the Swift source dir, not inside it:

```
01_Project/PhotoIngest/
├── project.yml
├── PhotoIngest/              # ← Swift sources (the sources: glob)
│   ├── PhotoIngestApp.swift
│   └── Services/…
└── Resources/exiftool/       # ← the vendored tree, NOT under PhotoIngest/
    ├── exiftool              #    (script auto-finds lib/ by its own path)
    └── lib/…
```

`project.yml`:

```yaml
targets:
  PhotoIngest:
    type: application
    platform: macOS
    sources:
      - path: PhotoIngest            # Swift sources
      - path: Resources/exiftool     # the vendored tree
        type: folder                 # FOLDER REFERENCE (blue folder) → copied verbatim
        buildPhase: resources        # …into Contents/Resources/exiftool/
```

`type: folder` makes a **folder reference** (verbatim recursive copy) rather than a `group` (individual file refs Xcode would try to handle). Result in the built bundle: `…/PhotoIngest.app/Contents/Resources/exiftool/exiftool` + `lib/`. Verify it actually runs *from the bundle*, not just from source:

```bash
APP=$(find ~/Library/Developer/Xcode/DerivedData/PhotoIngest-*/Build/Products/Debug -name PhotoIngest.app | head -1)
/usr/bin/perl "$APP/Contents/Resources/exiftool/exiftool" -ver   # → 13.58
```

Ship the **shippable subset only** — strip the tool's test suite / html docs / changelog before committing. (ExifTool: keep `exiftool` + `lib/` + `README` license; drop `t/`, `html/`, `Changes`, `config_files/`. Took 20 MB → much less surface to sign + notarize.) Pure-text trees (Perl/JS) seal into `CodeResources` with no per-file signing and need no entitlement to exec the system interpreter; a real Mach-O binary would instead need inside-out signing.

### 2. Make the runtime path INJECTABLE so unit tests can reach it

The natural way to find the bundled tool is `Bundle.main` — but in a **unit-test bundle, `Bundle.main` is the `xctest` runner, not your app**, so anything that hardcodes `Bundle.main` is untestable. Inject the URL; default it from `Bundle.main` only in the production factory:

```swift
struct ExifToolRunner {
    let exiftoolURL: URL                                   // injected — never read Bundle.main inside run()

    init(exiftoolURL: URL) { self.exiftoolURL = exiftoolURL }

    /// Production default: the folder-reference copy inside the app bundle.
    static func makeProduction() -> ExifToolRunner {
        let url = Bundle.main.resourceURL!.appendingPathComponent("exiftool/exiftool")
        return ExifToolRunner(exiftoolURL: url)
    }

    func run(args: [String]) async throws -> Data { /* /usr/bin/perl exiftoolURL.path + args */ }
}
```

In tests, locate the repo's copy relative to the test source file via `#filePath` (machine-independent, no Bundle, no hardcoded absolute path):

```swift
let exiftoolURL = URL(fileURLWithPath: #filePath)
    .deletingLastPathComponent()      // …/PhotoIngestTests/
    .deletingLastPathComponent()      // …/PhotoIngest/ (project dir)
    .appendingPathComponent("Resources/exiftool/exiftool")
let runner = ExifToolRunner(exiftoolURL: exiftoolURL)
let out = try await runner.run(args: ["-ver"])            // works headless
```

---

## Gotchas

- **Tree inside the `sources:` path → glob compiles it.** Keep it in a sibling `Resources/` dir, or exclude it. This is the whole reason for the layout above.
- **`xcodegen generate` after every `project.yml` edit** (the `.xcodeproj` is generated; gitignore it, commit `project.yml`).
- **Commit the vendored tree** — it's a shippable dependency, not a build artifact; make sure no `.gitignore` rule swallows it.
- **`type: folder` vs `type: group`** — folder reference (verbatim, blue folder) is what you want for an opaque tree; a group would add per-file references Xcode manages.
- **Verify from the *built bundle*, not source** — a passing source-tree invocation says nothing about whether the copy phase landed it correctly.

---

## When to use which

- **This (#140, folder reference):** an opaque tree you copy verbatim and never transform. Cleanest — no script.
- **#58 (postBuildScripts):** when you must *transform* during copy (rename, filter, codesign nested binaries) — then pay the `inputFiles`/`outputFiles` tax.

Pairs with **#58** (the run-script alternative + its sandbox/dep-analysis pitfalls), **#47** (xcodegen project setup), **#43** (the subprocess fire-and-collect call shape that runs the vendored tool).
