# Managed Developer ID — Xcode GUI Distribution Workflow

**Source project:** `1-macOS/Sigil/`

> **Trigger:** you want to ship a notarized macOS app via GitHub Releases (direct distribution), AND `security find-identity -p codesigning -v` doesn't show a `Developer ID Application` cert, AND you don't feel like creating one

Apple silently added a new cert type called **"Developer ID Application Managed"** (Xcode Cloud / managed signing). The private key lives on Apple's servers — you can't download it. This is why `security find-identity` doesn't show it. **It still works for direct distribution** via Xcode's GUI, just not via `xcodebuild` + `notarytool` CLI.

For a solo developer, the managed-cert + GUI path is strictly simpler than the classic local-cert + CLI pipeline. This entry documents both and explains when to use each.

---

## The two paths

| Aspect | Managed cert + Xcode GUI | Local cert + `xcodebuild` CLI |
|--------|--------------------------|-------------------------------|
| Local Keychain cert? | No — Apple holds the private key | Yes — you hold the private key |
| How to sign | Product → Archive → Distribute App → Direct Distribution | `xcodebuild archive` + `xcodebuild -exportArchive` |
| How to notarize | Automatic (Organizer shows progress) | `xcrun notarytool submit --wait` |
| How to staple | Automatic | `xcrun stapler staple` |
| Works on CI | No (no private key on the CI machine) | Yes |
| Works for GitHub Actions | No | Yes |
| Solo dev, single Mac | **This.** | Over-engineered |
| Team / CI / multi-Mac | Harder — managed cert is tied to "this machine signed into your Apple ID" | **This.** |

---

## Canonical path — Managed cert + Xcode GUI

### One-time setup

1. Enroll in the Apple Developer Program ($99/yr).
2. Sign into Xcode → Settings → Accounts with the enrolled Apple ID.
3. Make sure your Apple ID has a Developer ID Application certificate, "Managed" or otherwise. You can verify at [developer.apple.com/account/resources/certificates/list](https://developer.apple.com/account/resources/certificates/list). Xcode Cloud usually provisions the managed one automatically on first Archive.
4. In `project.yml` / Xcode build settings:
   ```yaml
   DEVELOPMENT_TEAM: YOURTEAMID
   CODE_SIGN_STYLE: Automatic
   # For Release config:
   CODE_SIGN_IDENTITY: "Developer ID Application"
   ENABLE_HARDENED_RUNTIME: YES
   ```

### Per-release steps

1. In Xcode, scheme → Sigil, configuration → Release, destination → Any Mac.
2. **Product → Archive**. Xcode builds, archives, opens Organizer.
3. In Organizer → select archive → **Distribute App → Direct Distribution**.
4. Xcode:
   - Signs with the managed Developer ID
   - Uploads to Apple for notarization
   - Waits ~1-3 minutes for Apple to return Accepted
   - Staples the notarization ticket to the .app
   - Offers to Export
5. Export the `.app` to a folder.

### Verification

```bash
xcrun stapler validate path/to/YourApp.app
# Expected: "The validate action worked!"

spctl --assess --type execute -vv path/to/YourApp.app
# Expected: "accepted" with "source=Notarized Developer ID"
```

### Package into DMG

```bash
brew install create-dmg    # one-time

create-dmg \
    --volname "YourApp 1.0.0" \
    --window-size 560 360 \
    --icon-size 100 \
    --icon "YourApp.app" 160 180 \
    --app-drop-link 400 180 \
    --hide-extension "YourApp.app" \
    --no-internet-enable \
    YourApp-1.0.0.dmg \
    path/to/export-folder/
```

The stapled ticket on the inner `.app` covers the DMG too — no separate notarization step required.

### GitHub Release

```bash
git tag v1.0.0
git push origin main --tags
gh release create v1.0.0 --title "YourApp 1.0.0" \
    --notes-file RELEASE-NOTES.md \
    YourApp-1.0.0.dmg
```

---

## Appendix — Local cert + CLI pipeline

Only needed if you're moving releases to CI (GitHub Actions, etc.). Requires a **non-managed** Developer ID Application cert installed locally.

### One-time

1. [developer.apple.com/account/resources/certificates/list](https://developer.apple.com/account/resources/certificates/list) → **+** → select "Developer ID Application" (NOT "Developer ID Application Managed")
2. Upload a CSR (Keychain Access → Certificate Assistant → Request a Certificate From a Certificate Authority)
3. Download and install the resulting `.cer`
4. Verify: `security find-identity -p codesigning -v | grep "Developer ID Application"`
5. Create an app-specific password at [appleid.apple.com](https://appleid.apple.com/account/manage/section/security) → "App-Specific Passwords"
6. Store notarytool credentials:
   ```bash
   xcrun notarytool store-credentials "yourapp-notary" \
       --apple-id "your.appleid@example.com" \
       --team-id "YOURTEAMID" \
       --password "xxxx-xxxx-xxxx-xxxx"
   ```

### Per-release

```bash
# Archive
xcodebuild -scheme YourApp -configuration Release \
           -destination 'generic/platform=macOS' \
           -archivePath build/YourApp.xcarchive archive

# Export (requires ExportOptions.plist with method: "developer-id")
xcodebuild -exportArchive \
           -archivePath build/YourApp.xcarchive \
           -exportOptionsPlist ExportOptions.plist \
           -exportPath build/export

# Notarize
(cd build/export && zip -r YourApp.zip YourApp.app)
xcrun notarytool submit build/export/YourApp.zip \
      --keychain-profile "yourapp-notary" --wait

# Staple + DMG + release (same as GUI path from here)
xcrun stapler staple build/export/YourApp.app
create-dmg ... build/YourApp-1.0.0.dmg build/export/
gh release create v1.0.0 build/YourApp-1.0.0.dmg
```

`ExportOptions.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
    "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>method</key>           <string>developer-id</string>
    <key>teamID</key>           <string>YOURTEAMID</string>
    <key>signingStyle</key>     <string>automatic</string>
</dict>
</plist>
```

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `security find-identity` shows nothing | No Developer ID Application cert installed locally | **If using GUI path:** that's fine, managed cert is server-side. **If using CLI path:** create a non-managed cert. |
| Xcode says "No profiles matching this ID" on Archive | Managed cert not yet propagated | Restart Xcode, wait 5 min, retry |
| `Distribute App` button greyed out | Archive was Debug, not Release | Scheme → Edit Scheme → Archive → Release |
| Notarization returns `Invalid` | Hardened Runtime off | Check `codesign -d --entitlements - YourApp.app` |
| Gatekeeper still warns after notarization | Stapler didn't run or didn't include the .app | Re-run `stapler staple` on the .app, rebuild DMG |
| Second Mac warns but first Mac doesn't | Local trust cache | Test on a fresh user account, not your main Mac |

---

## When to migrate GUI → CLI

You don't need to migrate if:
- You're a solo dev
- You ship from one Mac
- Release cadence is less than monthly

You SHOULD migrate if any of:
- You add a second developer to the project
- Releases become weekly/daily and manual Xcode clicks become friction
- You want automated release-on-tag via GitHub Actions
- You want reproducible builds (CI environment, not "whatever my laptop has")

---

*Discovered during Sigil Wave 9 when `security find-identity` returned only "Apple Distribution" and "Apple Development" — neither of which signs for direct distribution. The managed Developer ID Application cert was visible in the Apple Developer portal but absent from local Keychain. The GUI path worked first try.*
