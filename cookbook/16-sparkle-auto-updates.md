## Sparkle Auto-Updates (macOS)

### Integration Checklist

1. **Add Sparkle via SPM** — `https://github.com/sparkle-project/Sparkle` (>= 2.8.1)
2. **Generate EdDSA key pair** — `./Sparkle.framework/bin/generate_keys`
3. **Configure Info.plist keys** — `SUFeedURL` and `SUPublicEDKey`
4. **Create updater controller** — `SPUStandardUpdaterController`
5. **Add "Check for Updates" menu item** — observe `canCheckForUpdates`
6. **Host appcast.xml** — with at least one valid release entry
7. **Sign releases** — `./Sparkle.framework/bin/sign_update YourApp.zip`

### Gotcha: INFOPLIST_KEY_ Prefix Does NOT Work for Custom Keys

When using `GENERATE_INFOPLIST_FILE = YES` with xcconfig, the `INFOPLIST_KEY_` prefix
**only works for Apple-recognized keys** (e.g., `NSHumanReadableCopyright`, `CFBundleDisplayName`).

Custom third-party keys like `SUFeedURL` and `SUPublicEDKey` are **silently ignored**.

**Symptom:** Sparkle shows "You must specify the URL of the appcast as the SUFeedURL key
in either the Info.plist" even though you defined `INFOPLIST_KEY_SUFeedURL` in xcconfig.

**Fix:** Create a partial `Info.plist` with the custom keys and set `INFOPLIST_FILE` in xcconfig:

```xml
<!-- Config/Info.plist -->
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>SUFeedURL</key>
    <string>https://example.com/appcast.xml</string>
    <key>SUPublicEDKey</key>
    <string>YOUR_PUBLIC_KEY_HERE</string>
</dict>
</plist>
```

```
// Shared.xcconfig
GENERATE_INFOPLIST_FILE = YES
INFOPLIST_FILE = Config/Info.plist
// Xcode merges both: generated Apple keys + your custom keys
```

### Gotcha: Empty Appcast

Sparkle requires at least one valid `<item>` in the appcast feed. An empty `<channel>` (or
all items commented out) causes "An error occurred in retrieving update information."

Populate the appcast before shipping, or at minimum include the current version so Sparkle
can report "You're up to date."

### Minimal Updater Setup (SwiftUI)

```swift
import Sparkle

// Controller — create once at app launch
final class UpdaterController: ObservableObject {
    let updater: SPUStandardUpdaterController

    init() {
        updater = SPUStandardUpdaterController(
            startingUpdater: true,
            updaterDelegate: nil,
            userDriverDelegate: nil
        )
    }
}

// ViewModel for menu item state
final class CheckForUpdatesViewModel: ObservableObject {
    @Published var canCheckForUpdates = false
    private var cancellable: AnyCancellable?

    init(updater: SPUUpdater) {
        cancellable = updater.publisher(for: \.canCheckForUpdates)
            .assign(to: \.canCheckForUpdates, on: self)
    }
}

// Menu item
struct CheckForUpdatesView: View {
    @ObservedObject var viewModel: CheckForUpdatesViewModel
    let updater: SPUUpdater

    var body: some View {
        Button("Check for Updates…") {
            updater.checkForUpdates()
        }
        .disabled(!viewModel.canCheckForUpdates)
    }
}
```

---

