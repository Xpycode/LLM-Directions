## SwiftUI Performance

### The Core Principle: Diffing Checkpoints

**Source:** [SwiftUI Performance Article](https://www.swiftdifferently.com/blog/swiftui/swiftui-performance-article)

SwiftUI uses a "comparison engine" that diffs view output against previous renders. When state updates, the view body re-executes and SwiftUI compares the result.

**The Problem:** Large, monolithic view bodies force SwiftUI to compare many primitives (Text, Button, Image) on every state change.

**The Solution:** Extract subviews into separate structs. Each struct becomes a "diffing checkpoint" — SwiftUI skips re-evaluating subviews whose properties haven't changed.

```swift
// ❌ BAD: Monolithic view body
struct ContentView: View {
    @State private var counter = 0

    var body: some View {
        VStack {
            Text("Header")
            Image(systemName: "star")
            Text("Count: \(counter)")
            Button("Increment") { counter += 1 }
            // 50 more views here...
            // ALL re-evaluated when counter changes
        }
    }
}

// ✅ GOOD: Separate view structs
struct ContentView: View {
    @State private var counter = 0

    var body: some View {
        VStack {
            HeaderView()        // ← Diffing checkpoint (skipped if unchanged)
            CounterView(count: counter)
            IncrementButton { counter += 1 }
        }
    }
}

struct HeaderView: View {
    var body: some View {
        VStack {
            Text("Header")
            Image(systemName: "star")
        }
    }
}
```

---

### Anti-Pattern: @ViewBuilder Methods Don't Help

**Source:** [SwiftUI Performance Article](https://www.swiftdifferently.com/blog/swiftui/swiftui-performance-article)

Methods and computed properties using `@ViewBuilder` still trigger full re-execution because they're called at runtime. Only separate structs get the optimization.

```swift
// ❌ BAD: @ViewBuilder method (no performance benefit)
struct ContentView: View {
    @State private var counter = 0

    var body: some View {
        VStack {
            headerView   // Still re-executes every time!
            Text("Count: \(counter)")
        }
    }

    @ViewBuilder
    private var headerView: some View {
        Text("Header")
        Image(systemName: "star")
    }
}

// ✅ GOOD: Separate struct (actual optimization)
struct HeaderView: View {
    var body: some View {
        VStack {
            Text("Header")
            Image(systemName: "star")
        }
    }
}
```

---

### Equatable for Views with Closures

**Source:** [SwiftUI Performance Article](https://www.swiftdifferently.com/blog/swiftui/swiftui-performance-article)

SwiftUI can't compare closures, so views with closure properties always look "changed." Use `.equatable()` with custom equality.

```swift
struct ActionButton: View, Equatable {
    let title: String
    let action: () -> Void

    var body: some View {
        Button(title, action: action)
    }

    // Custom equality ignores the closure
    static func == (lhs: ActionButton, rhs: ActionButton) -> Bool {
        lhs.title == rhs.title
    }
}

// Usage:
ActionButton(title: "Save", action: save)
    .equatable()  // ← Enables custom equality check
```

---

### Image Cache Miss Flash: Always Use .resizable()

**Source:** CropBatch `CropEditorView` (2026-04-03) — image flash on thumbnail switch.

When using a CG-scaled image cache for high-quality downscaling, the cache will miss for one render frame on every image switch (new image ID ≠ cached ID). If the fallback returns the full-resolution source image and the `Image` view lacks `.resizable()`, it renders at native pixel dimensions — causing a one-frame flash where the image fills the entire pane.

```swift
// ❌ BAD: Cache miss returns full-res image without .resizable()
@ViewBuilder
private var scaledImageView: some View {
    if currentScale >= 1.0 {
        Image(nsImage: displayedImage)
            .resizable()
            .aspectRatio(contentMode: .fill)
    } else {
        // On cache hit: pre-scaled image renders at correct size
        // On cache miss: FULL-RES image renders at native pixels → FLASH
        Image(nsImage: highQualityScaledImage)
            .interpolation(.high)
    }
}

// ✅ GOOD: Both branches use .resizable() so frame always constrains
@ViewBuilder
private var scaledImageView: some View {
    if currentScale >= 1.0 {
        Image(nsImage: displayedImage)
            .resizable()
            .aspectRatio(contentMode: .fill)
    } else {
        Image(nsImage: highQualityScaledImage)
            .interpolation(.high)
            .resizable()
            .aspectRatio(contentMode: .fill)
    }
}
```

**Why `.resizable()` matters:** SwiftUI's `Image` without `.resizable()` renders at intrinsic (pixel) size. A parent `.frame()` only affects layout positioning — it does NOT constrain the image's rendering size. With `.resizable()`, the image scales to fill its proposed frame.

**Also guard against `viewSize == .zero`:** On first render, `GeometryReader` reports size via `onChange(initial: true)` which fires *after* the first render pass. If your scale calculation falls back to `1.0` when `viewSize == .zero`, the image renders at full pixel dimensions for one frame. Guard by not rendering content until `viewSize` is populated:

```swift
GeometryReader { geometry in
    Group {
        if viewSize.width > 0, viewSize.height > 0 {
            // actual content
        }
    }
    .onChange(of: geometry.size, initial: true) { _, newSize in
        viewSize = newSize
    }
}
```

---

### Debug Technique: Random Background Colors

**Source:** [SwiftUI Performance Article](https://www.swiftdifferently.com/blog/swiftui/swiftui-performance-article)

Visualize which views are re-rendering by adding random background colors:

```swift
extension View {
    func debugRender() -> some View {
        self.background(Color(
            red: .random(in: 0...1),
            green: .random(in: 0...1),
            blue: .random(in: 0...1)
        ))
    }
}

// Usage during debugging:
HeaderView()
    .debugRender()  // Color changes = view re-rendered
```

If a view's color changes when unrelated state updates, it needs extraction into a separate struct.

---

