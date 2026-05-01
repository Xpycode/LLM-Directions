# Pattern 25: Extension File Splitting

**Source:** P2toMXF (2026-04-13)
**Use when:** Any Swift file exceeds ~500 lines, or a class has clearly separable responsibilities

---

## Problem

Large Swift files (800-1200+ lines) become hard to navigate and maintain. Common offenders:
- ViewModels mixing card loading, grouping logic, conversion, and queue integration
- Service classes mixing queue management, job processing, and verification
- Model files containing 20+ types from different domains

## Solution

Split using Swift `extension ClassName { }` in separate files. The convention is `ClassName+Feature.swift`.

### Step 1: Identify Natural Boundaries

Look for MARK sections — they're usually the split points:

```
QueueManager.swift (1166 lines)
├── Core state, init, properties, persistence   → QueueManager.swift (391)
├── addJob, removeJob, retry, cancel             → QueueManager+Operations.swift (165)
├── processQueue, processJob, time estimation    → QueueManager+Processing.swift (357)
└── verify, cancelVerification, file search      → QueueManager+Verification.swift (265)
```

### Step 2: Move Methods to Extension Files

Each new file follows this template:

```swift
import Foundation

extension QueueManager {
    // MARK: - Queue Operations

    func addJob(_ job: ConversionJob, autoStart: Bool = false) {
        // ... exact same code, no changes
    }

    func removeJob(_ jobId: UUID) {
        // ...
    }
}
```

### Step 3: Fix Access Levels

**This is the only code change required.** Swift's `private` is file-scoped — methods/properties marked `private` in the main file are invisible to extensions in other files.

| Accessed from extension? | Current access | Change to |
|--------------------------|---------------|-----------|
| No | `private` | Keep `private` |
| Yes (method) | `private` | Remove keyword (becomes `internal`) |
| Yes (property) | `private` | Remove keyword (becomes `internal`) |
| Yes (@Published) | `@Published private(set)` | `@Published` (widen setter) |

**Rule of thumb:** If a method is only called within its own MARK section, keep it `private`. If called across sections that will be in different files, make it `internal`.

Common candidates for widening:
- Helper methods like `log()`, `saveQueue()`
- Lookup helpers like `updateJob(id:)`, `jobIndex(for:)`
- Service properties like `ffmpeg`, `parser`

### Step 4: Add to Xcode Project

New `.swift` files need to be registered in `project.pbxproj`:
1. Add `PBXFileReference` entry
2. Add `PBXBuildFile` entry
3. Add to parent `PBXGroup` children
4. Add to `PBXSourcesBuildPhase` files

### Step 5: Build and Verify

```bash
xcodebuild -scheme "AppName" build
wc -l Sources/**/*.swift  # Confirm all under 500
```

## Splitting Strategy by File Type

### Model Files (structs/enums)
Split by **domain** — each file gets related types:

```
P2Clip.swift (1067 lines)
├── P2Clip.swift         → P2Clip, P2Card, RecordGroup, ConversionSettings, Timecode (412)
├── ConversionJob.swift  → JobStatus, ConversionJob (309)
├── ProgressModels.swift → ProgressMetrics, ConversionEstimate, SpeedRecord (237)
└── VerificationModels.swift → VerificationMode, VerificationStatus, VerificationResult (113)
```

### ViewModel/Service Classes
Split by **lifecycle phase** or **responsibility**:

```
ConversionViewModel.swift (1068 lines)
├── ConversionViewModel.swift              → Properties, init, logging, selection (212)
├── ConversionViewModel+CardManagement.swift → Load, discover, remove cards (224)
├── ConversionViewModel+RecordGroups.swift   → Grouping, timecode, validation (229)
└── ConversionViewModel+Conversion.swift     → Convert, queue integration (415)
```

### Wrapper/Service Classes
Split by **feature surface**:

```
FFmpegWrapper.swift (885 lines)
├── FFmpegWrapper.swift              → Core infra, runFFmpeg, OutputCollector (324)
├── FFmpegWrapper+Conversion.swift   → convertClip, mergeClips, parsing (482)
└── FFmpegWrapper+Thumbnails.swift   → extractFrame, ContinuationGuard (90)
```

## Key Gotchas

1. **@MainActor inheritance**: Extensions on an `@MainActor` class automatically inherit the annotation. No need to re-annotate.

2. **Nested types stay in main file**: Types nested inside the class (like `OutputCollector`, `AccessResult` enum) must remain in the file with the class definition.

3. **Stored properties only in main file**: Swift extensions cannot add stored properties. All `@Published`, `let`, and `var` declarations stay in the main class file.

4. **No behavior changes**: This is a pure structural refactoring. Don't combine it with logic changes — if something breaks, you want to know it was the split, not a logic change.

5. **Build after each wave**: Split one class at a time and build between each. Don't split all 4 files at once — cascading errors are harder to debug.

---

*Pattern extracted from P2toMXF production review session. Split 4 files (1067, 1166, 1068, 885 lines) into 15 files, all under 500 lines. Zero behavior changes, clean build.*
