## Metal shader in a Swift package — compile from an embedded source string

**Source:** zPackages — `Sources/PlayerKit/MetalVideoRenderer.swift` (PlayerKit Phase 1, the AVFoundation+Metal video engine lifted from Penumbra). Added 2026-06-26.

**Use case:** You're moving Metal-rendering code **out of an app and into a Swift package** (a reusable renderer, an image filter, a video engine). The app loaded its shader with `device.makeDefaultLibrary()`, which reads the **app's main bundle** — but a package has no main bundle of its own, and the obvious fix (`device.makeDefaultLibrary(bundle: .module)`) fails to even compile:

```
error: type 'Bundle' has no member 'module'
```

### Why `.module` isn't there

`Bundle.module` is a SwiftPM-synthesized accessor that only exists when the target has a **recognized resource bundle**. SwiftPM creates one when you declare `resources:` — but a lone `.metal` file dropped into `Sources/` did **not** trigger bundle/accessor generation here (no `Package_PlayerKit.bundle`, no `default.metallib`, no `resource_bundle_accessor.swift` got generated). So `Bundle.module` is undefined, and there's no metallib to point a bundle-based lookup at anyway. You can chase this with explicit `resources:` declarations and bundle-finder helpers, but for a small shader there's a simpler, bulletproof route.

### The fix — embed the shader source, compile at setup

Put the `.metal` source in a Swift string constant and compile it once with `device.makeLibrary(source:options:)`. No resource bundle, no metallib, no `Bundle.module` — the package is fully self-contained and behaves identically in unit tests, in any consumer app, anywhere.

```swift
final class MetalVideoRenderer: NSObject, MTKViewDelegate {

    // Single source of truth — was Shaders.metal in the app. Delete the .metal file
    // from Sources/ so SwiftPM doesn't pick it up as a build input (which re-creates
    // the resource-bundle situation and leaves an unused metallib).
    private static let shaderSource = """
    #include <metal_stdlib>
    using namespace metal;

    struct VertexOut { float4 position [[position]]; float2 texCoord; };

    vertex VertexOut vertexShader(const device float2* vertexPositions [[buffer(0)]],
                                  const device float2* textureCoordinates [[buffer(1)]],
                                  uint vertexID [[vertex_id]]) {
        VertexOut out;
        out.position = float4(vertexPositions[vertexID], 0.0, 1.0);
        out.texCoord = textureCoordinates[vertexID];
        return out;
    }

    fragment float4 fragmentShader(VertexOut in [[stage_in]],
                                    texture2d<float> tex [[texture(0)]]) {
        constexpr sampler s(coord::normalized, address::clamp_to_edge, filter::linear);
        return tex.sample(s, in.texCoord);
    }
    """

    private func setupPipelineState(for mtkView: MTKView) {
        // App version was: device.makeDefaultLibrary()  ← reads the app main bundle
        let library = try? device.makeLibrary(source: Self.shaderSource, options: nil)
        let vertexFunction = library?.makeFunction(name: "vertexShader")
        let fragmentFunction = library?.makeFunction(name: "fragmentShader")
        // ... build MTLRenderPipelineDescriptor as before ...
    }
}
```

### The trade you're making

| | `.metal` file + `Bundle.module` | embedded string + `makeLibrary(source:)` |
|---|---|---|
| Shader errors caught | at **build** time | at **runtime** (first `setup`) |
| SwiftPM plumbing | resource bundle + accessor must generate | **none** |
| Works in unit tests / any consumer | only if the bundle resolves | **always** (self-contained) |
| Cost | zero runtime | one-time compile at engine init (negligible) |

For a small, stable shader compiled **once** at engine init, deferring error-catching to runtime is a fine trade for total portability. For a large shader library where build-time validation matters, invest in the `resources:` + `Bundle.module` route instead (and verify `default.metallib` actually lands in the bundle).

### The trap

```swift
// ❌ Lifted straight from the app — compiles in the app, undefined in a package:
let lib = device.makeDefaultLibrary()                       // reads MAIN bundle (none in a package)
let lib = try device.makeDefaultLibrary(bundle: .module)    // 'Bundle' has no member 'module'
```

And the silent one: **leave `Shaders.metal` sitting in `Sources/` after you've embedded the string.** SwiftPM treats `.metal` as a build input and compiles it into a stray (unused) metallib — wasted work, and it can re-introduce the half-built resource-bundle state. Remove the file; the embedded string is the only copy.

### Why it matters

This is a recurring tax on the app→package extraction path (cookbook theme: the "real funnel" — a package isn't proven until it's lifted out and builds standalone). Anything that vends a shader from a package hits it: a video render backend, a Core Image-adjacent Metal filter, a custom `MTKView` effect. The embedded-source route makes the package link **zero** resource bundles and stay drop-in across tests and consumers.

### Composes with

- **App→package extraction generally** — same class of fix as swapping app singletons (`Logger.shared`) for injected closures when lifting code into a package: sever every dependency on the app's ambient environment (main bundle, singletons, app models).

### Reference implementation

`Sources/PlayerKit/MetalVideoRenderer.swift` in zPackages (the `shaderSource` constant + `setupPipelineState`). Extraction narrative: zPackages `docs/sessions/2026-06-26.md` (PlayerKit Phase 1).
