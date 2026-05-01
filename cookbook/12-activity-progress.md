## Activity & Progress Bars

Bottom bars, progress indicators, and status displays for background tasks. Every pro app needs at least a status bar; most need progress for exports, scans, or batch operations.

---

### Pattern 1: Status Bar (Item Count + State)

**Source:** `VCR/Views/ContentView.swift`
**Use case:** Persistent bottom bar showing file count and quick actions.

```swift
.safeAreaInset(edge: .bottom) {
    HStack {
        Text("\(entries.count) \(entries.count == 1 ? "file" : "files")")
            .font(.caption)
            .foregroundStyle(.secondary)
        Spacer()
        Button("Clear All") { viewModel.removeAllEntries() }
            .font(.caption)
            .buttonStyle(.borderless)
            .disabled(entries.isEmpty)
    }
    .padding(.horizontal, 12)
    .padding(.vertical, 8)
    .background(.bar)
}
```

**Key rule:** `.safeAreaInset(edge: .bottom)` pushes content up so the bar never overlaps scroll content. Better than `.overlay` for persistent bars.

---

### Pattern 2: Inline Progress in Bottom Bar

**Source:** `Penumbra/Views/InfoStripView.swift`, `VAM/Views/Shared/StatusBarView.swift`
**Use case:** Progress bar and status text that appear in the existing bottom bar when a task is running.

```swift
HStack {
    if proxyQueue.isProcessing {
        HStack(spacing: 6) {
            ProgressView()
                .controlSize(.small)
            Text("\(proxyQueue.activeCount) encoding, \(proxyQueue.queuedCount) queued")
                .font(.system(size: 11))
                .foregroundStyle(Theme.secondaryText)
        }
    } else {
        Text("Ready")
            .font(.system(size: 11))
            .foregroundStyle(Theme.secondaryText)
    }

    Spacer()

    // Export progress when active
    if case .exporting(let progress, let message) = exportManager.exportState {
        ProgressView(value: progress)
            .progressViewStyle(.linear)
            .frame(width: 100)
        Text("\(Int(progress * 100))%")
            .font(.caption.monospacedDigit())
            .foregroundStyle(.secondary)
            .frame(width: 35, alignment: .trailing)
        Text(message)
            .font(.caption)
            .foregroundStyle(.secondary)
            .lineLimit(1)
            .truncationMode(.middle)
    }
}
.padding(.horizontal, 12)
.frame(height: 28)
.background(Theme.secondaryBackground)
.overlay(alignment: .top) { Divider() }
```

**Key rules:**
- Indeterminate spinner (`.controlSize(.small)`) for unknown-length tasks
- Determinate `ProgressView(value:)` with `.linear` style for measurable tasks
- Percentage with `.monospacedDigit()` so numbers don't jitter
- Phase/message text truncated with `.middle` so you see start and end of paths

---

### Pattern 3: Determinate Progress with Cancel

**Source:** `Phosphor/Views/Export/ExportProgressView.swift`, `CutSnaps/Views/ExportProgressView.swift`
**Use case:** Modal or inline progress for a single export/render operation.

```swift
VStack(spacing: 16) {
    Text("Exporting…")
        .font(.headline)

    ProgressView(value: progress)
        .progressViewStyle(.linear)
        .frame(width: 300)

    Text("\(Int(progress * 100))%")
        .font(.headline.monospacedDigit())
        .foregroundStyle(.secondary)

    Button("Cancel", role: .cancel) {
        onCancel()
    }
    .buttonStyle(.bordered)
}
.padding(24)
```

**Best for:** Single-task exports where the user waits. Keep it simple — progress bar, percentage, cancel.

---

### Pattern 4: Multi-Level Progress (Overall + Per-Item)

**Source:** `VideoScout/Views/BatchProgressView.swift`
**Use case:** Batch operation processing multiple items, showing both overall and per-item progress.

```swift
VStack(alignment: .leading, spacing: 12) {
    // Overall progress
    VStack(alignment: .leading, spacing: 3) {
        HStack {
            Text("Video \(pipeline.currentVideoIndex + 1) of \(pipeline.totalVideos)")
                .font(.caption)
                .foregroundStyle(.secondary)
            Spacer()
            etaLabel
        }
        ProgressView(value: overallFraction)
            .tint(.accentColor)
    }

    // Per-item progress (only during specific phases)
    if pipeline.currentStage == .captioning && pipeline.totalShots > 0 {
        VStack(alignment: .leading, spacing: 3) {
            Text("Shot \(pipeline.currentShotIndex) of \(pipeline.totalShots)")
                .font(.caption2)
                .foregroundStyle(.secondary)
            ProgressView(value: shotFraction)
                .tint(.purple)
        }
    }

    // Phase label with spinner
    HStack(spacing: 6) {
        if pipeline.currentStage != .idle && pipeline.currentStage != .complete {
            ProgressView()
                .controlSize(.mini)
                .scaleEffect(0.7)
                .frame(width: 12, height: 12)
        }
        Text(pipeline.currentStage.label)
            .font(.caption)
            .foregroundStyle(.secondary)
    }
}
.padding(16)
.background(.regularMaterial, in: RoundedRectangle(cornerRadius: 8))
```

**Key rules:**
- Two tint colors distinguish overall (accent) from per-item (purple) progress
- Per-item bar only appears during relevant phases
- Phase label changes as the pipeline advances through stages
- Material background makes it float over content

---

### Pattern 5: Progress Metrics Panel (Elapsed / ETA / Speed)

**Source:** `P2toMXF/Views/ProgressControlPanel.swift`
**Use case:** Long-running conversions where the user needs elapsed time, ETA, and throughput.

```swift
struct ProgressControlPanel: View {
    let metrics: ProgressMetrics
    let onCancel: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack(spacing: 12) {
                ProgressView(value: metrics.progress)
                    .progressViewStyle(.linear)
                Text("\(Int(metrics.progress * 100))%")
                    .font(.system(.body, design: .monospaced))
                    .foregroundStyle(.secondary)
                    .frame(width: 40, alignment: .trailing)
            }

            HStack {
                Text(metrics.phase)
                    .font(.callout)
                    .lineLimit(1)
                    .truncationMode(.middle)

                Spacer()

                HStack(spacing: 8) {
                    MetricLabel(icon: "clock", value: metrics.formattedElapsed)
                    if let remaining = metrics.formattedRemaining {
                        Divider().frame(height: 12)
                        MetricLabel(icon: "hourglass", value: "~\(remaining)")
                    }
                    if let speed = metrics.formattedSpeed {
                        Divider().frame(height: 12)
                        MetricLabel(icon: "speedometer", value: speed)
                    }
                }
                .font(.caption)
                .foregroundStyle(.secondary)
            }
        }
    }
}

private struct MetricLabel: View {
    let icon: String
    let value: String

    var body: some View {
        Label(value, systemImage: icon)
            .monospacedDigit()
    }
}
```

**ProgressMetrics model:**

```swift
struct ProgressMetrics {
    var progress: Double = 0.0
    var phase: String = ""
    var startTime: Date?

    var elapsedSeconds: TimeInterval {
        guard let start = startTime else { return 0 }
        return Date().timeIntervalSince(start)
    }

    var estimatedRemainingSeconds: TimeInterval? {
        guard progress > 0.05, elapsedSeconds > 0 else { return nil }
        let total = elapsedSeconds / progress
        return max(0, total - elapsedSeconds)
    }

    var formattedElapsed: String { formatInterval(elapsedSeconds) }
    var formattedRemaining: String? {
        estimatedRemainingSeconds.map { formatInterval($0) }
    }
    var formattedSpeed: String?

    private func formatInterval(_ seconds: TimeInterval) -> String {
        let t = Int(max(seconds, 0))
        let h = t / 3600, m = (t % 3600) / 60, s = t % 60
        if h > 0 { return "\(h)h \(m)m" }
        if m > 0 { return "\(m)m \(s)s" }
        return "\(s)s"
    }
}
```

**Key rules:**
- Don't show ETA until `progress > 0.05` — early estimates are wildly inaccurate
- Use `~` prefix on remaining time to signal it's an estimate
- Divider-separated metric chips for a clean layout
- `.monospacedDigit()` on all numbers to prevent jitter

---

### Pattern 6: Floating Progress Overlay

**Source:** `VideoScout/Views/ContentView.swift`
**Use case:** Progress panel that floats over content, appears/disappears with animation.

```swift
.overlay(alignment: .bottomTrailing) {
    if pipelineService.isRunning {
        BatchProgressView(
            pipeline: pipelineService,
            onCancel: { pipelineService.cancelBatch() }
        )
        .padding()
        .transition(.move(edge: .bottom).combined(with: .opacity))
        .animation(.easeInOut(duration: 0.3), value: pipelineService.isRunning)
    }
}
```

**Key rules:**
- `.bottomTrailing` so it doesn't block the main content
- `.move(edge: .bottom).combined(with: .opacity)` for a polished slide-up entrance
- Animate on the boolean (`isRunning`), not the progress value

**Best for:** Non-modal progress that doesn't block interaction with the rest of the app.

---

### Pattern 7: Phase Indicator (Scan/Process Stages)

**Source:** `VOLTLAS/Sources/Views/Components/ScanProgressPanel.swift`, `VCR/Models/ScanProgress.swift`
**Use case:** Multi-phase operations where each phase has a distinct icon and label.

```swift
enum ScanPhase: String, Sendable {
    case enumerating, persisting, completed, cancelled
    case failed(String)
}

struct ScanPhaseIndicator: View {
    let phase: ScanPhase

    var body: some View {
        HStack(spacing: 6) {
            switch phase {
            case .enumerating:
                Image(systemName: "folder.badge.gearshape").foregroundStyle(.blue)
                Text("Enumerating files…")
            case .persisting:
                Image(systemName: "cylinder.split.1x2").foregroundStyle(.orange)
                Text("Writing to database…")
            case .completed:
                Image(systemName: "checkmark.circle.fill").foregroundStyle(.green)
                Text("Completed")
            case .cancelled:
                Image(systemName: "xmark.circle.fill").foregroundStyle(.yellow)
                Text("Cancelled")
            case .failed(let message):
                Image(systemName: "exclamationmark.triangle.fill").foregroundStyle(.red)
                Text("Failed: \(message)").lineLimit(2)
            }
        }
        .font(.caption)
        .foregroundStyle(.secondary)
    }
}
```

**Progress data model:**

```swift
struct ScanProgress: Sendable, Equatable {
    let currentFrame: Int
    let estimatedTotalFrames: Int?
    let phase: ScanPhase
    let startTime: Date

    var percentage: Double {
        guard let total = estimatedTotalFrames, total > 0 else { return 0 }
        return min(1.0, Double(currentFrame) / Double(total))
    }

    var framesPerSecond: Double {
        let elapsed = Date().timeIntervalSince(startTime)
        guard elapsed > 0 else { return 0 }
        return Double(currentFrame) / elapsed
    }
}
```

**Color convention:** Blue = active, Orange = processing, Green = done, Yellow = cancelled, Red = failed.

---

### Pattern 8: Footer with Progress + Stop Controls

**Source:** `P2toMXF/Views/FooterControlsView.swift`
**Use case:** Bottom bar that swaps between normal actions and progress+cancel during operations.

```swift
@ViewBuilder
private var footerContent: some View {
    if isAnyConversionActive {
        // Progress mode
        HStack(spacing: 16) {
            ProgressControlPanel(
                metrics: activeProgressMetrics,
                onCancel: cancelActiveConversion
            )

            if queueManager.pendingCount > 0 {
                Button("Stop All") {
                    queueManager.stopAllProcessing()
                }
                .buttonStyle(.bordered)
                .controlSize(.large)
            } else {
                Button("Stop") {
                    cancelActiveConversion()
                }
                .buttonStyle(.bordered)
                .controlSize(.large)
            }
        }
    } else {
        // Normal mode
        HStack {
            if let feedback = viewModel.queueFeedback {
                Label(feedback, systemImage: "checkmark.circle.fill")
                    .font(.caption)
                    .foregroundStyle(.green)
                    .transition(.opacity)
            }
            Spacer()
            Button("Add to Queue") { viewModel.addToQueue() }
                .disabled(!viewModel.canAddToQueue)
        }
    }
}
```

**Key rule:** The footer **swaps entirely** between normal state and progress state — don't try to squeeze both into the same layout. Use `if`/`else` at the top level.

---

### Choosing a Pattern

| Need | Pattern | Example |
|---|---|---|
| Always-visible file count / status | **1: Status Bar** | `safeAreaInset` bottom bar |
| Progress in existing bar | **2: Inline** | Spinner + text when busy, "Ready" when idle |
| Single export/render task | **3: Determinate** | Progress bar + % + cancel |
| Batch of N items | **4: Multi-level** | Overall bar + per-item bar + phase |
| Long conversion with ETA | **5: Metrics Panel** | Elapsed / remaining / speed chips |
| Non-blocking background task | **6: Floating Overlay** | Slide-up panel, bottom-trailing |
| Multi-phase pipeline | **7: Phase Indicator** | Color-coded phase icons |
| Footer that transforms | **8: Footer Swap** | Normal actions ↔ progress+stop |

---

