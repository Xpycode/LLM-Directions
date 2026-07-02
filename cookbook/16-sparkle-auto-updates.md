## Sparkle Auto-Updates (macOS)

**Tags:** Sparkle, auto-update, appcast, INFOPLIST_KEY_, SUFeedURL, updater

### Integration Checklist

1. **Add Sparkle via SPM** — `https://github.com/sparkle-project/Sparkle` (>= 2.8.1)
2. **Generate EdDSA key pair** — `./Sparkle.framework/bin/generate_keys`
3. **Configure Info.plist keys** — `SUFeedURL` and `SUPublicEDKey`
4. **Create updater controller** — `SPUStandardUpdaterController`
5. **Add "Check for Updates" menu item** — observe `canCheckForUpdates`
6. **Host appcast.xml** — with at least one valid release entry
7. **Sign releases** — `./Sparkle.framework/bin/sign_update YourApp.zip`

### Gotcha: INFOPLIST_KEY_ Prefix Does NOT Work for Custom Keys

`INFOPLIST_KEY_SUFeedURL` / `INFOPLIST_KEY_SUPublicEDKey` are silently dropped by the same
allowlist mechanism documented in
[156-xcodegen-infoplist-allowlist.md](156-xcodegen-infoplist-allowlist.md) — see that file for
the root cause and the partial-plist merge fix (Sparkle's custom keys are its worked example).

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

