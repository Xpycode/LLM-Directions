# /security-audit

Run a comprehensive security audit on code before deployment. Based on [VibeSec](https://github.com/BehiSecc/VibeSec-Skill) patterns from 5+ years of bug bounty experience.

---

## When to Run

- Before deploying to production
- After adding authentication/authorization
- When handling user input or file uploads
- Building APIs or web services
- Integrating third-party services

---

## Audit Checklist

### 1. Access Control

Every authenticated endpoint must verify authorization at the resource level.

**Check for:**

| Vulnerability | What to Look For |
|---------------|------------------|
| **IDOR** | Can user A access user B's resources by changing IDs? |
| **Privilege Escalation** | Can regular users access admin functions? |
| **Mass Assignment** | Can users set fields they shouldn't (isAdmin, price)? |

**Required Checks:**
- [ ] Resource ownership verified on every request
- [ ] Role/permission checked before action
- [ ] Parent resource ownership verified (nested resources)
- [ ] No reliance on client-side role checks alone

```swift
// ❌ Vulnerable - no ownership check
func getDocument(id: String) -> Document {
    return database.fetch(id)
}

// ✅ Secure - verifies ownership
func getDocument(id: String, requestingUser: User) throws -> Document {
    let doc = try database.fetch(id)
    guard doc.ownerId == requestingUser.id else {
        throw AuthError.forbidden
    }
    return doc
}
```

---

### 2. Client-Side Vulnerabilities

#### XSS (Cross-Site Scripting)

**Input Sources to Validate:**
- URL parameters, fragments, query strings
- Form inputs, text areas
- HTTP headers (Referer, User-Agent)
- Cookies, localStorage, sessionStorage
- postMessage data
- Database content (stored XSS)

**Defenses:**
- [ ] Context-specific output encoding (HTML, JS, URL, CSS)
- [ ] Content Security Policy (CSP) headers configured
- [ ] HttpOnly flag on sensitive cookies
- [ ] Sanitization libraries for rich text (e.g., DOMPurify)
- [ ] Avoid raw HTML injection methods in frameworks

#### CSRF (Cross-Site Request Forgery)

- [ ] CSRF tokens on all state-changing requests
- [ ] Tokens are random, unpredictable, tied to session
- [ ] SameSite cookie attribute set (Lax or Strict)
- [ ] Tokens regenerated after login

#### Open Redirects

- [ ] Redirect URLs validated against allowlist
- [ ] No user-controlled full URLs in redirects
- [ ] Relative URLs preferred over absolute

```javascript
// ❌ Vulnerable
res.redirect(req.query.next)

// ✅ Secure - allowlist validation
const allowed = ['/dashboard', '/profile', '/settings']
const next = req.query.next
if (allowed.includes(next)) {
    res.redirect(next)
} else {
    res.redirect('/dashboard')
}
```

---

### 3. Server-Side Vulnerabilities

#### SSRF (Server-Side Request Forgery)

When server fetches URLs provided by users:

- [ ] URL scheme restricted (https only, no file://)
- [ ] Private IP ranges blocked (127.0.0.1, 10.x, 192.168.x, 169.254.x)
- [ ] Cloud metadata endpoints blocked (169.254.169.254)
- [ ] DNS rebinding protection (resolve before fetch)
- [ ] Redirect following disabled or limited

**Blocked Ranges:**
```
127.0.0.0/8      # Localhost
10.0.0.0/8       # Private
172.16.0.0/12    # Private
192.168.0.0/16   # Private
169.254.0.0/16   # Link-local / Cloud metadata
```

#### SQL Injection

- [ ] Parameterized queries everywhere (no string concatenation)
- [ ] ORM used correctly (no raw queries with user input)
- [ ] Stored procedures use parameters
- [ ] Database user has minimal privileges

```python
# ❌ Vulnerable
query = f"SELECT * FROM users WHERE id = {user_input}"

# ✅ Secure - parameterized
cursor.execute("SELECT * FROM users WHERE id = ?", (user_input,))
```

#### Path Traversal

- [ ] User input never directly in file paths
- [ ] Paths canonicalized and validated
- [ ] Chroot or restricted directory access
- [ ] No `../` sequences after validation

```swift
// ❌ Vulnerable
let path = "/uploads/" + userFilename

// ✅ Secure - validate and canonicalize
let safeName = URL(fileURLWithPath: userFilename).lastPathComponent
guard !safeName.contains("..") else { throw SecurityError.invalidPath }
let path = "/uploads/" + safeName
```

#### File Upload Vulnerabilities

**Validation Requirements:**
- [ ] File extension validated against allowlist
- [ ] MIME type verified (don't trust Content-Type header)
- [ ] Magic bytes checked for actual file type
- [ ] File size limited
- [ ] Filename sanitized (no path characters)
- [ ] Files stored outside web root
- [ ] Generated filename used (not user-provided)

**Magic Bytes Reference:**
| Type | Magic Bytes (hex) |
|------|-------------------|
| JPEG | `FF D8 FF` |
| PNG | `89 50 4E 47 0D 0A 1A 0A` |
| GIF | `47 49 46 38` |
| PDF | `25 50 44 46` |
| ZIP | `50 4B 03 04` |

#### XXE (XML External Entities)

Disable external entity processing in XML parsers:

```python
# Python (defusedxml)
import defusedxml.ElementTree as ET
tree = ET.parse(xml_file)

# Java
factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true)

# .NET
settings.DtdProcessing = DtdProcessing.Prohibit
```

---

### 4. Authentication

- [ ] Passwords hashed with bcrypt/Argon2 (not MD5/SHA1)
- [ ] Minimum password complexity enforced
- [ ] Account lockout after failed attempts
- [ ] Session tokens are random, sufficient length (128+ bits)
- [ ] Sessions invalidated on logout
- [ ] Sessions timeout after inactivity
- [ ] Sensitive actions require re-authentication
- [ ] Password reset tokens are one-time use, expire quickly

---

### 5. Security Headers

Verify these headers are set:

| Header | Value |
|--------|-------|
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` |
| `Content-Security-Policy` | Restrict sources appropriately |
| `X-Content-Type-Options` | `nosniff` |
| `X-Frame-Options` | `DENY` or `SAMEORIGIN` |
| `Referrer-Policy` | `strict-origin-when-cross-origin` |
| `Permissions-Policy` | Restrict features as needed |

---

### 6. Secrets & Configuration

- [ ] No secrets in code, configs, or version control
- [ ] Environment variables or secret management used
- [ ] Different credentials per environment
- [ ] Secrets rotated regularly
- [ ] `.env` files gitignored
- [ ] No secrets in client-side code or bundles

---

## Framework-Specific Notes

### React/Vue/Frontend
- Use framework's built-in escaping for rendering
- Sanitize any HTML from APIs before rendering
- Never expose API keys in frontend bundles

### Node.js/Express
- Use helmet.js for security headers
- Validate request body schemas (joi, zod)
- Rate limit authentication endpoints

### Python/Django/Flask
- CSRF middleware enabled
- DEBUG=False in production
- SECRET_KEY from environment

### Swift/iOS
- Use Keychain for secrets, not UserDefaults
- Enable App Transport Security (ATS)
- Certificate pinning for sensitive APIs

---

## Quick Scan Patterns

Search for these patterns to find common issues:

| Pattern to Find | Risk |
|-----------------|------|
| `password`, `secret`, `api_key`, `token` | Hardcoded credentials |
| SQL with string concatenation | SQL injection |
| Shell commands with user input | Command injection |
| HTTP requests with user-provided URLs | SSRF |
| Raw HTML rendering in templates | XSS |
| Redirects with user-controlled URLs | Open redirect |

---

## After Finding Issues

1. **Prioritize** - Authentication/access control first
2. **Fix** - Address vulnerability at the source
3. **Test** - Verify fix works and doesn't break functionality
4. **Document** - Log in decisions.md if architectural
5. **Prevent** - Add automated checks where possible

---

## Related

- `54_security-rules.md` - Core security rules (Swift-focused)
- `/code-review` - Includes security in review checklist
- `/review` - Production checklist with security section

---

*Based on [VibeSec-Skill](https://github.com/BehiSecc/VibeSec-Skill) by BehiSecc*
