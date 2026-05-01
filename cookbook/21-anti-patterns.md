## Anti-Patterns to Avoid

| Anti-Pattern | Problem | Solution |
|--------------|---------|----------|
| @ViewBuilder methods for subviews | No performance benefit — re-executes fully | Use separate view structs |
| Monolithic view bodies | Every state change re-evaluates all children | Extract subviews as structs |
| HSplitView layout bugs | Doesn't fill vertical space | Use HStack + Divider |
| SwiftUI controls on macOS | Capsule buttons, Catalyst look | AppKit wrappers via NSViewRepresentable |
| `try?` swallowing errors | Silent failures | Handle errors explicitly |
| Missing `stopAccessingSecurityScopedResource()` | Resource leaks | Always use `defer` or model lifecycle |
| `url.path()` for subprocesses | Percent-encodes spaces, breaks paths | Use `url.path(percentEncoded: false)` |
| Single AI review | Misses bugs | Multi-model validation |
| >500 line files | Unmaintainable | Extract managers/services |
| `@Observable` without `@MainActor` | UI mutations unprotected from background threads | Add `@MainActor` at class level |
| `DispatchQueue.main.asyncAfter` in `@MainActor` class | Bypasses actor isolation | Use `Task { @MainActor in; await Task.sleep(...) }` |
| `Image(nsImage:)` without `.resizable()` in cache fallback | Full-res flash on cache miss (one frame at native pixels) | Always add `.resizable().aspectRatio(contentMode: .fill)` |
| `var id = UUID()` on static/built-in data | IDs regenerate every access — UserDefaults stored ID matches nothing on relaunch | Use hardcoded `UUID(uuidString: "...")!` for built-in data referenced by ID |
| `AVAssetTrack.load(.naturalSize)` without `preferredTransform` | Returns encoded dimensions, ignoring rotation — portrait video displays with wrong aspect ratio | Load both: `let (size, t) = try await track.load(.naturalSize, .preferredTransform); CGSize(width: abs(size.applying(t).width), height: abs(size.applying(t).height))` |
| `.formStyle(.columns)` in narrow panes | Label column eats available width, Picker popup truncates to 1-2 chars | Use `.formStyle(.grouped)` for panes < 350px; labels stack above controls |
| `DispatchSemaphore.wait` in `@MainActor` init | N-second launch stall — spawned `Task` inherits MainActor isolation and can't run while main is blocked, so the semaphore always hits its timeout | Make the loader `async`, drop init-time call, invoke via `.task` on the consuming view (see [19-swift6-concurrency.md](19-swift6-concurrency.md) §2) |

---

