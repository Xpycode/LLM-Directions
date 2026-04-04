## App Lifecycle & Initialization

### Standard App Entry Point

**Source:** `MusicServer/MusicServerApp.swift`

```swift
@main
struct MusicServerApp: App {
    // Services as @State (order matters for dependencies)
    @State private var folderManager = FolderManager()
    @State private var driveMonitor = DriveMonitor()
    @State private var bonjourAdvertiser = BonjourAdvertiser()

    @NSApplicationDelegateAdaptor(AppDelegate.self) private var appDelegate

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environment(folderManager)
                .environment(driveMonitor)
                .environment(bonjourAdvertiser)
                .onAppear {
                    restoreFolderAndSetupMonitoring()
                }
        }
        .commands {
            CommandGroup(replacing: .newItem) { }
        }
    }

    private func restoreFolderAndSetupMonitoring() {
        let restored = folderManager.restoreBookmark()
        if restored, let folderURL = folderManager.selectedFolderURL {
            _ = driveMonitor.startMonitoring(folderURL: folderURL)
        }
    }
}
```

---

### Service Initialization Order with .task

**Source:** `MusicClient/MusicClientApp.swift`

```swift
@main
struct MusicClientApp: App {
    @State private var serverDiscovery = ServerDiscovery()
    @State private var audioPlayer = AudioPlayer()
    @State private var nowPlayingInfoManager = NowPlayingInfoManager()
    @StateObject private var apiClient = MusicAPIClient()

    var body: some Scene {
        WindowGroup {
            RootView()
                .environment(serverDiscovery)
                .environment(audioPlayer)
                .environment(nowPlayingInfoManager)
                .environmentObject(apiClient)
                .task {
                    // ORDER OF INITIALIZATION:
                    // 1. Start server discovery
                    serverDiscovery.startDiscovery()

                    // 2. Configure dependent managers
                    nowPlayingInfoManager.configure(
                        audioPlayer: audioPlayer,
                        apiClient: apiClient
                    )
                }
                .onChange(of: serverDiscovery.selectedServer) { _, newServer in
                    // 3. React to changes
                    if let server = newServer, let url = server.baseURL {
                        apiClient.setBaseURL(url)
                    }
                }
        }
    }
}
```

---

### Scene Phase Handling (iOS)

**Source:** `Group Alarms/GroupAlarmsApp.swift`

```swift
@main
struct GroupAlarmsApp: App {
    @StateObject private var alarmKitManager = AlarmKitManager.shared
    @Environment(\.scenePhase) private var scenePhase

    var body: some Scene {
        WindowGroup {
            MainTabView()
                .task {
                    // Launch initialization
                    await cancelLegacyNotifications()
                    await requestAlarmPermissions()
                    await synchronizeAlarmsOnLaunch()
                }
                .onChange(of: scenePhase) { _, newPhase in
                    switch newPhase {
                    case .active:
                        // App came to foreground
                        Task { await synchronizeAlarmsOnLaunch() }
                    case .background:
                        // App went to background
                        Self.scheduleExpirationCheckTask()
                    case .inactive:
                        break
                    @unknown default:
                        break
                    }
                }
        }
    }
}
```

---

### Manager with Configure Pattern

**Source:** `MusicClient/Services/NowPlayingInfoManager.swift`

```swift
@MainActor
@Observable
final class NowPlayingInfoManager {
    private weak var audioPlayer: AudioPlayer?
    private weak var apiClient: MusicAPIClient?
    private var observationTask: Task<Void, Never>?

    init() {
        setupRouteChangeObserver()
    }

    /// Configure after managers are created
    func configure(audioPlayer: AudioPlayer, apiClient: MusicAPIClient) {
        self.audioPlayer = audioPlayer
        self.apiClient = apiClient
        setupRemoteCommands()
        startObservingAudioPlayer()
    }

    func cleanup() {
        observationTask?.cancel()
        clearNowPlayingInfo()
    }

    private func startObservingAudioPlayer() {
        observationTask?.cancel()
        observationTask = Task { [weak self] in
            while !Task.isCancelled {
                self?.checkForAudioPlayerChanges()
                try? await Task.sleep(for: .seconds(1))
            }
        }
    }
}
```

---

### FolderManager with Bookmark Restoration

**Source:** `MusicServer/Services/FolderManager.swift`

```swift
@MainActor
@Observable
public final class FolderManager {
    private enum Constants {
        static let bookmarkKey = "musicFolderBookmark"
    }

    public private(set) var selectedFolderURL: URL?
    public private(set) var isAccessingFolder: Bool = false

    /// Call on app launch to restore access
    @discardableResult
    public func restoreBookmark() -> Bool {
        guard let bookmarkData = userDefaults.data(forKey: Constants.bookmarkKey) else {
            return false
        }
        do {
            var isStale = false
            let url = try URL(resolvingBookmarkData: bookmarkData,
                            options: .withSecurityScope,
                            relativeTo: nil,
                            bookmarkDataIsStale: &isStale)
            selectedFolderURL = url
            startAccessingFolder()
            return true
        } catch {
            clearBookmark()
            return false
        }
    }

    public func startAccessingFolder() {
        guard let url = selectedFolderURL, !isAccessingFolder else { return }
        if url.startAccessingSecurityScopedResource() {
            isAccessingFolder = true
        }
    }

    public func stopAccessingFolder() {
        guard let url = selectedFolderURL, isAccessingFolder else { return }
        url.stopAccessingSecurityScopedResource()
        isAccessingFolder = false
    }
}
```

---

