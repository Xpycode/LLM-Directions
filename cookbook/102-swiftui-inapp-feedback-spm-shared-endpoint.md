# 102 — Drop-in in-app feedback sheet (SPM package → shared multi-app PHP endpoint)

**Best for:** adding a **"Send Feedback / Report a Bug"** sheet to a macOS app that POSTs to the shared
self-hosted `feedback-submit.php` (cookbook **#49** — multi-app, keyed by an `app` field +
`ALLOWED_APPS`, brings the admin board / public board / rate-limit / email-notify for free). This is the
**Swift consumer half** of #49: package it **once** as a Sparkle-style SPM remote dependency, reuse it in
every app with a per-app `FeedbackConfig`. Shipped as **FeedbackKit** (`Xpycode/FeedbackKit` 0.1.0),
first consumer **Conjoyn** (Help › Send Feedback…).

Composes with **#49** (the web/PHP backend + admin), **#46** (`?app=` convention), and the host app's
existing **#33** diagnostic logger (optional "Attach recent log").

---

## Architecture — config injected, zero host-app coupling

The package depends on **nothing** from the host app (no `Theme`, no logger type). Everything app-specific
arrives through one `Sendable` config struct, so the same package drops into a dark FCP-style app and a
stock-chrome app alike:

```swift
public struct FeedbackConfig: Sendable {
    public let appID: String          // sent as `app`; MUST be in the server's ALLOWED_APPS
    public let endpoint: URL          // the shared feedback-submit.php
    public let accent: Color          // injected tint — defaults to .accentColor (no Theme import)
    public let logProvider: (@Sendable () -> String?)?   // optional "Attach recent log" source
}
```

Host wires it at launch and drops the command into `.commands { }`:

```swift
private let feedbackConfig = FeedbackConfig(
    appID: "conjoyn",
    endpoint: URL(string: "https://apps.lucesumbrarum.com/feedback-submit.php")!,
    accent: Theme.acc2,
    logProvider: { MainActor.assumeIsolated { DiagnosticLogger.shared.recentTail(maxLines: 80) } }
)
// …
.commands { FeedbackCommands(config: feedbackConfig) }   // adds Help › Send Feedback…
```

`FeedbackCommands` uses `CommandGroup(after: .help)` and hosts its own `.sheet` on a **zero-size
`Color.clear` anchor** driven by a private `@State` flag — so the menu item presents the sheet with **no
binding threaded from the host**:

```swift
Button("Send Feedback…") { showing = true }
    .background(Color.clear.frame(width: 0, height: 0)
        .sheet(isPresented: $showing) { FeedbackView(config: config) })
```

---

## The non-obvious bit — bridging a `@Sendable` closure to a `@MainActor` logger

The log hook is typed `@Sendable () -> String?` so the **package stays actor-agnostic** (reusable from any
isolation domain, sandboxed or not). But a host's diagnostic logger is usually a `@MainActor` singleton.
Calling its method directly inside the `@Sendable` closure **fails under `SWIFT_STRICT_CONCURRENCY: complete`**.

Don't make the package `@MainActor` to "fix" it — that's the library bending to one consumer. Instead, the
**integrator supplies the proof**, because the integrator knows the call site. Here FeedbackKit only ever
invokes `logProvider` from its SwiftUI **view body** (the `.onChange` of the attach-log toggle), which is
`@MainActor`-isolated. So:

```swift
logProvider: { MainActor.assumeIsolated { DiagnosticLogger.shared.recentTail(maxLines: 80) } }
```

`assumeIsolated` asserts the known-main call site (crashes only if ever called off-main, which the view-body
contract guarantees). Read the tail **lazily inside the closure**, not as a snapshot at config-build time —
the attached log is then whatever's freshest when the user ticks the toggle (i.e. right after the bug).
If your logger is write-only (#33 was), add a `recentTail(maxLines:)` reader: read the current generation
only, never throw (nil on any failure), and remember the text is sent verbatim → the caller owns redaction.

---

## Engine detail — 302-on-success vs a real 200

`feedback-submit.php` answers a good POST with a **302 redirect** to `/feedback.html?submitted=1`. Let
`URLSession` follow it and you can't tell success from a generic 200. **Disable redirects** with a
`URLSessionTaskDelegate` that returns `nil`, then map the status yourself:

```swift
case 200..<400: return                 // 302 success (redirect refused) or a real 2xx
case 429:       throw .rateLimited(serverText)
case 400..<500: throw .rejected(serverText)   // validation — surface the server's plain-text reason
default:        throw .server(serverText)
```

Form-encode against the **RFC 3986 unreserved set only** (`A–Z a–z 0–9 - . _ ~`) so `+ & =` in user text
survive intact. Send the exact field set #49 validates, including the empty `website` honeypot.

---

## SPM over a PRIVATE repo

The package repo can be **private** (matches a closed app family) — SPM still resolves it on your Macs via
the `gh` credential helper; nothing extra in `project.yml`:

```yaml
packages:
  FeedbackKit: { url: https://github.com/Xpycode/FeedbackKit, from: "0.1.0" }
```

Remember SPM versions are **git tags, not branches** — `git tag -a 0.1.0 && git push origin 0.1.0`, or
resolution fails with "no such version" even though `main` has the code.

---

## Verify the allow-list WITHOUT creating a submission

After deploying the server-side `ALLOWED_APPS` change (#49/#99), confirm the new `app` slug passes the gate
**without** writing a board row or sending an email. Exploit that the PHP collects **all** validation errors
before responding: POST a valid payload but **omit one downstream field** (e.g. `consent`). If the app
passed the allow-list, the response carries only the *other* error — never "choose an app from the list":

```bash
curl -s -X POST --data-urlencode "app=conjoyn" --data-urlencode "type=bug" \
  --data-urlencode "title=probe" --data-urlencode "body=gate check" --data-urlencode "website=" \
  https://apps.lucesumbrarum.com/feedback-submit.php
# ✅ "Please acknowledge the public listing."   ← passed the gate, created nothing
# ❌ "...Please choose an app from the list."    ← still blocked
```

**Operational note:** running the site's `deploy.sh` is a **production deploy** — expect the agent
auto-mode classifier to block it until you explicitly authorize. The app code and the server allow-list are
**independently deployable**: the Mac app sends `app=<slug>` blind, and the server flips behavior the moment
it's allow-listed — no app rebuild needed.

---

## Gotchas

- **App ↔ server split:** clicking Send before the server allow-lists your slug fails *loudly* with the
  server's reason ("choose an app from the list"), not silently — that's the gate doing its job.
- **`representationTypes`/icons:** N/A here, but keep the dropdown (`feedback.html`), the JS name+placeholder
  maps (`feedback.js`), and `ALLOWED_APPS` (`.php`) **balanced** — add a new app to all three or the web
  form and the board display drift out of sync.
- **First-class reuse:** to add a 2nd consumer, just publish nothing new — add the SPM dep + one
  `FeedbackCommands(config:)`, then allow-list its slug. The package is the single source of truth.

Source: `zPackages/FeedbackKit` (`FeedbackConfig`/`FeedbackSubmitter`/`FeedbackView`/`FeedbackCommands`),
Conjoyn `ConjoynApp.swift` + `DiagnosticLogger.recentTail`, App-Websites `feedback-submit.php`. Pairs with
**#49** (backend), **#33** (logger), **#99** (deploy).
