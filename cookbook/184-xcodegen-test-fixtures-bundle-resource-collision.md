# 184 — XcodeGen test fixtures: exclude from bundle-resource copy, load via #filePath

**Tags:** xcodegen, xctest, fixtures, bundle resources, duplicate output, test target, project.yml

## Problem

A test target's `sources:` entry in `project.yml` with no `excludes:` makes XcodeGen (and the
underlying Xcode build system) treat every file under that path — including nested test-fixture
media/data files — as a bundle resource to copy into the test bundle's `Resources/` directory.
Xcode's resource-copy phase **flattens** nested paths into one flat `Resources/` directory. If two
fixtures at different subpaths share a filename (e.g. `Core/track.wav` and `Messy/Nested/track.wav`
in a "messy folder naming" corpus, or any parallel fixture sets that intentionally reuse a name),
the build fails with:

```
Multiple commands produce '.../Resources/track.wav'
```

This is easy to hit specifically in *disposable test-fixture corpora* designed to include
same-named files at different paths on purpose (that's often the point of the fixture — testing
identity resolution across duplicate filenames).

## Fix

If the fixtures are loaded from source at test time (e.g. via `#filePath`-relative path resolution
in a `FixtureSupport`-style helper) rather than via `Bundle.module`/`Bundle(for:)` resource lookup,
they don't need to be bundle resources at all. Exclude the fixture directory from the test target's
resource copy in `project.yml`:

```yaml
targets:
  KplayTests:
    type: bundle.unit-test
    sources:
      - path: KplayTests
        excludes:
          # Fixture media/manifest files are loaded from source (see FixtureSupport.swift's
          # #filePath-relative fixturesRoot), not from bundle resources. Letting Xcode auto-copy
          # them flattens nested paths into one Resources/ directory and produces duplicate-output
          # build errors for same-named files at different fixture paths.
          - Fixtures
```

Then regenerate (`xcodegen generate`) and rebuild.

## When this doesn't apply

If test code actually needs `Bundle.module`/`Bundle(for:).url(forResource:)` lookup (e.g. an SPM
test target, or fixtures that must ship inside the built test bundle for some other reason), don't
exclude them — instead rename to avoid same-basename collisions, or nest fixtures one level deeper
under per-case subdirectories that XcodeGen/Xcode won't flatten-collide (Xcode still flattens on
copy, so renaming is usually the real fix in that case, not restructuring).

## Source

Kplay, 2026-09-12, Wave 2 task 2.2 (disposable media fixture corpus assembly) — hit while adding 30
generated fixtures including a deliberate "messy folder naming" set with same-named files at
different nested paths.
