<!--
TRIGGERS: notarization, notarytool, "Developer ID", Developer ID Application, staple, stapler, gatekeeper, spctl, DMG, disk image, hdiutil, direct distribution, ship, release, gh release, codesign DMG, "not notarized", OSStatus -26276, .p8, App Store Connect API key, app-specific password
PHASE: distribution, ship
LOAD: when packaging a direct-download macOS app (DMG/zip) outside the App Store, or when a Gatekeeper / notarization step fails
-->

# 61 — Notarization & Direct Distribution (CLI)

> How to sign, notarize, staple, and publish a direct-download macOS app
> (DMG → GitHub Release) **from the command line**, without Xcode Organizer.
> Written from the Manifest v1.0.0 ship on 2026-05-29.
>
> Build-time / per-machine signing lives in `28_xcode-signing-and-sourcekit.md`.
> This doc is about *distribution*: getting a notarized artifact to users.

## When you need this

| Distribution path | Signing identity | Notarize the DMG/zip yourself? |
|---|---|---|
| **App Store / TestFlight** | Apple Distribution | No — App Store handles it |
| **Xcode → Distribute → Direct Distribution** | Developer ID Application | No — Xcode does it silently |
| **Hand-built DMG / CLI release** *(this doc)* | **Developer ID Application** | **Yes** |

Key insight: **notarization binds to a specific file.** Xcode's "Distribute"
flow notarizes the exact artifact it hands you and caches the credentials it
used. The moment you wrap that app in a **new DMG**, you've created a file Apple
has never seen — so the DMG itself must be signed + notarized + stapled
separately, with credentials Xcode never exposed to you. That's why CLI release
needs a one-time setup that Organizer never asked for. (The `.app` inside can be
already-notarized and that's fine — but the DMG wrapper still needs its own pass.)

## One-time setup

### 1. Developer ID Application certificate (login keychain)

Direct download requires a **Developer ID Application** cert — *not* Apple
Development and *not* Apple Distribution (those are for dev/App Store).

Create it so the private key lands in **this Mac's** login keychain:

> Xcode → Settings → Accounts → (team) → **Manage Certificates** →
> **`+ ˅` → Developer ID Application**

Verify:
```bash
security find-identity -v -p codesigning | grep "Developer ID Application"
# → Developer ID Application: GREGOR MÜLLER (FDMSRXXN73)
```

### 2. notarytool credential profile (keychain)

Generate an **App Store Connect API key**: App Store Connect → Users and Access →
Integrations → App Store Connect API → **+** → role **Developer** → download the
`AuthKey_XXXXXXXXXX.p8` (one-time download). Note the **Key ID** (in the filename)
and the **Issuer ID** (UUID at the top of the Keys page).

Store it once (caches in keychain under a profile name):
```bash
xcrun notarytool store-credentials "Manifest" \
  --key /path/AuthKey_XXXXXXXXXX.p8 \
  --key-id XXXXXXXXXX \
  --issuer <ISSUER_UUID>
```
Test: `xcrun notarytool history --keychain-profile "Manifest"`.

> Manifest's stored profile is named **`Manifest`**; key at
> `~/ProgrammingProjects/99-AUTH/AuthKey_6HTCUZ9L7L.p8` (Key ID `6HTCUZ9L7L`,
> Issuer `935e3a4d-b8fc-4110-a24f-89d7da84b6ab`).

## The release chain

Scripted at `scripts/package-dmg.sh` — or by hand:

```bash
APP="04_Exports/Manifest v1.0.0/Manifest.app"   # already notarized+stapled by Xcode export

# 1. Build the DMG (drag-to-Applications layout)
STAGING="$(mktemp -d)"
cp -R "$APP" "$STAGING/"
ln -s /Applications "$STAGING/Applications"
hdiutil create -volname "Manifest 1.0.0" -srcfolder "$STAGING" \
  -ov -format UDZO "04_Exports/Manifest-1.0.0.dmg"
rm -rf "$STAGING"

# 2. Sign the DMG with Developer ID
codesign --force --timestamp \
  --sign "Developer ID Application: GREGOR MÜLLER (FDMSRXXN73)" \
  "04_Exports/Manifest-1.0.0.dmg"

# 3. Notarize (waits for Apple's verdict)
xcrun notarytool submit "04_Exports/Manifest-1.0.0.dmg" \
  --keychain-profile "Manifest" --wait        # → status: Accepted

# 4. Staple the ticket onto the DMG
xcrun stapler staple "04_Exports/Manifest-1.0.0.dmg"

# 5. Verify Gatekeeper sees it as notarized
spctl -a -vvv -t open --context context:primary-signature \
  "04_Exports/Manifest-1.0.0.dmg"
# → accepted / source=Notarized Developer ID

# 6. Publish the GitHub Release with the DMG attached
gh release create v1.0.0 "04_Exports/Manifest-1.0.0.dmg" \
  -R Xpycode/Manifest --title "Manifest 1.0.0" \
  --notes-file notes.md --latest
```

For the next version this is just `scripts/package-dmg.sh 1.0.1` + one
`gh release create`.

## Gotchas (each cost real time on the first run)

- **Import code-signing `.p12` into the *login* keychain, never iCloud.** iCloud
  keychain rejects PKCS#12 private-key material with **`OSStatus -26276`**. In
  Keychain Access, select **login** in the sidebar before File → Import; or use
  `security import file.p12 -k ~/Library/Keychains/login.keychain-db -T /usr/bin/codesign`.
- **A `.p12` that imports only "Developer ID Certification Authority"** brought in
  the Apple *intermediate CA*, not your *leaf* signing cert/key — usually because
  no Developer ID cert existed yet. Create the cert (step 1) first.
- **"Managed by Xcode" cert ≠ usable on this Mac.** A Developer ID cert managed by
  Xcode may have its private key on a *different* machine; it won't sign here. The
  `+ ˅` create flow (step 1) generates a fresh key locally — simplest fix.
- **App Store ≠ Developer ID.** Having Apple Development + Apple Distribution certs
  does NOT mean you can notarize a direct download. Developer ID Application is a
  separate identity you may have to create the first time.
- **`gh release view --json isLatest` is invalid** — the JSON field is
  `isPrerelease` (no `isLatest`).
- **DMGs / .app / .p8 / .p12 stay out of git** — see `.gitignore`; ship via GitHub
  Releases, not the repo.

## Alternative: zip instead of DMG

A zipped, already-stapled `.app` needs **no further notarization** — the staple
travels inside the app and Gatekeeper validates it on launch. That's the simplest
possible distribution (`ditto -c -k --keepParent App.app App.zip` → attach to the
release). Use a DMG only when you want the drag-to-Applications UX; it's the only
reason the DMG-signing/notarization dance above is needed.

## See also

- `scripts/package-dmg.sh` — the scripted version of the chain above.
- `28_xcode-signing-and-sourcekit.md` — build-time / per-machine signing.
- `27_mcp-gotchas.md` — sibling "things that bit us once" reference.
