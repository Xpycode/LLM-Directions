## Fail-open-aligned status codes for a client-classifying relay

**Source:** Aloft/ClipSmart — `05_Proxy/public/api/license/relay.php` (the Strato proxy fronting the Creem license API). Added 2026-06-25.

**Use case:** You put a thin proxy/relay in front of a third-party API so a secret (an API key) stays server-side instead of shipping in a distributed client (a Mac app, a browser bundle). The catch: the **client makes a decision based on the upstream's HTTP status code** — a license verdict, an entitlement, a feature flag. The proxy now sits in the path of that decision, and **its own failure modes (bad auth, rate limit, upstream down) must not be mistaken by the client for an upstream verdict.** Get this wrong and a proxy hiccup silently downgrades a paying user.

This is the server-side companion to **#131 ProGate** (the client that reads `isPro`). The licensing case is the worked example; the pattern is general — anything where a relay fronts a status-classifying client.

### The one rule

**Partition the HTTP status space into two disjoint sets and never cross them:**

1. **Verdict codes** — the codes the client attaches meaning to. The proxy may return these *only* by passing the upstream's reply through **verbatim**. It must never originate one itself.
2. **Fail-open codes** — everything the client treats as "transient, ignore, keep current state." Every error the proxy generates *itself* uses one of these.

For Aloft, the client's classifier (`LicenseClassifier.swift`, see #131) reads:

| Upstream code | Client meaning | Set |
|---|---|---|
| `200` | a verdict (active / revoked / disabled) | **verdict — pass through only** |
| `400` | verdict on activate/deactivate ("limit reached" / "disabled" / idempotent) | **verdict — pass through only** |
| `404` | verdict on validate (key revoked → start the 14-day grace clock) | **verdict — pass through only** |
| `401 / 403 / 405 / 413 / 429 / 5xx`, timeouts, garbage | `transportFailure` → **fail-open** (never downgrades) | safe for the proxy to originate |

So the proxy allocates its self-generated rejections entirely from the second set:

```php
// Every proxy-level rejection routes through ONE helper, and every caller
// passes a FAIL-OPEN code (anything except 200/400/404). That single
// constraint is the whole pattern.
function reject(int $code, string $why): void {
    http_response_code($code);
    header('Content-Type: application/json');
    echo json_encode(['proxy_error' => $why]);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST')          reject(405, 'method');      // not 400
if (!$secretsLoaded)                                reject(503, 'unconfigured');// 5xx
if (!hash_equals($appToken, $presentedToken))       reject(403, 'forbidden');   // not 401-as-verdict, but 403 is fine
if (!in_array($action, $allowed, true))             reject(404, 'unknown');     // see "the 404 nuance" below
if (strlen($body) > MAX_BODY)                        reject(413, 'too large');   // not 400
if ($rateLimited)                                   reject(429, 'slow down');   // fail-open

// ... forward to upstream ...
if ($respBody === false || $curlErr !== 0 || $status === 0)
                                                    reject(504, 'upstream down');// 5xx — the important one

// Success path: pass the upstream's EXACT status + body. This is the only
// place a verdict code (200/400/404) may appear.
http_response_code($status);
header('Content-Type: application/json');
echo $respBody;
```

### Stay dumb on purpose — don't parse the body

The strongest temptation is to validate the JSON and return your own `400` on a malformed request. **Don't.** If the proxy never parses the body, a malformed request becomes the *upstream's* `400` (a real verdict the client knows how to handle) instead of the *proxy's* `400` (which the client would misread as "activation limit reached"). The proxy forwards bytes; the upstream owns all semantics. Staying dumb is what keeps the two code-sets disjoint.

### The trap

```php
// ❌ Every one of these poisons the client's classifier:
if (badJson($body))   reject(400, ...);  // client: "activation limit reached" (a real verdict!)
if (!$found)          reject(404, ...);  // client on a validate call: "revoked → start grace clock"
echo '{"ok":false}';  http_response_code(200);  // client: a 200 verdict with a bogus body
```

The failure is invisible in every happy-path test — it only fires when the proxy itself hiccups, which is exactly when you're not looking. A throttled or misconfigured proxy returning its own `400`/`404`/`200` reads to the client as "the server has spoken," and the user is downgraded on what was actually a transient server-side condition.

### The 404 nuance (why it's still safe here)

`404` *is* a verdict code (revoked-key on validate), yet the proxy returns `404` for an unknown action path. That's safe **only because the real client never requests an unknown path** — it calls exactly the three allow-listed actions, so a proxy-originated `404` can only ever reach a scanner/bot, never a genuine `validate` call. If your client's URL set isn't fixed, route unknown paths to a non-verdict code (`422`) instead. Always check the reachability argument before reusing a verdict code for a proxy condition.

### Testing it

Assert the **codes**, not the bodies, and prove the partition holds. A tiny harness boots the proxy and checks each guard path returns a fail-open code, plus one live forward proving verbatim pass-through:

```bash
check "GET → 405"            405 "$(code -X GET  $BASE/validate)"
check "no token → 403"       403 "$(code -X POST $BASE/validate -d '{}')"
check "unknown action → 404" 404 "$(code -X POST $BASE/frobnicate -H "x-app-token: $T" -d '{}')"
check "oversize → 413"       413 "$(code -X POST $BASE/validate -H "x-app-token: $T" -d "$BIG")"
# live: invalid key forwards the UPSTREAM's real 404 verbatim (not a proxy 404)
check "forwards upstream 404" 404 "$(code -X POST $BASE/validate -H "x-app-token: $T" -d '{"key":"bad","instance_id":"x"}')"
```

(`php -S` ignores `.htaccess`, so a `dev-router.php` reproduces the rewrite locally — see #46/#49.)

### Why it matters

Inverts the usual security/UX tension. Because every proxy rejection fails open, you can tune the bot wall (`x-app-token` via timing-safe `hash_equals`) and the rate limit **aggressively** against abuse with **zero** risk of locking out a paying customer — the worst case for a real user is "stays in their current state." The actual secret-protection win isn't the gate at all; it's that the upstream key now lives in a server env var instead of inside a downloadable binary.

### Composes with

- **#131** (ProGate) — the client side: the `isPro` classifier whose verdict codes this proxy must protect.
- **#46 / #49** — the same Strato PHP toolbox (`flock` flat-file rate limit, salted-IP hashes, `.htaccess` secret denial, deploy excludes, `dev-router.php` for local `php -S`).

### Reference implementation

`05_Proxy/` in Aloft/ClipSmart — `relay.php` + `README.md` (deploy + go-live checklist) + `test-proxy.sh`. Build narrative: ClipSmart `docs/sessions/2026-06-25-session56.md`.
