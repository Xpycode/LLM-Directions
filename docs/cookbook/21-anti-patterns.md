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

---

