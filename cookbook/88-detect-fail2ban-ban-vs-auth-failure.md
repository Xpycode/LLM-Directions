## Deploy Ops — Tell a fail2ban IP-ban from a real auth failure (without making it worse)

**Source:** Penumbra-Website Strato deploy, 2026-06-10. Spent an hour "debugging a rejected SFTP password" that was actually correct — the host had silently IP-banned the machine after a handful of failed attempts.

**Use case:** You're deploying to shared hosting (Strato, IONOS, OVH, DreamHost…) over **SFTP/SSH with password auth**, and an automated upload (`lftp`, `sshpass`, `rsync -e ssh`, a CI step) keeps failing to authenticate. You need to know **which** of these you're looking at, because the fixes are opposite:

- **The credential is wrong/disabled** → fix the password / enable SSH / authorize a key.
- **The server has temporarily banned your IP** (fail2ban, after repeated failures) → the credential may be *perfectly correct*; **stop trying** and wait.

Guess wrong and you make it worse: retrying a *correct* password against a fail2ban block **extends the ban** and convinces you the password is broken.

**When to reach for it:** any time SSH/SFTP auth "suddenly stops working" mid-session, especially right after several failed attempts; or when a GUI client (Transmit, Cyberduck, FileZilla) connects fine but your automation doesn't.

---

### The whole diagnosis is in *where* the connection dies

The OpenSSH error text tells you which side rejected you — read it precisely:

| What you see | Meaning | It's a… |
|---|---|---|
| `Authentications that can continue: publickey,password` then `Permission denied (publickey,password)` | Server **received** your credential and said no | **Auth failure** — wrong password/user, key not authorized, or that auth method is disabled |
| `Connection closed by <ip> port 22` **before any password prompt** | Server (or its firewall) **dropped you pre-authentication** | **IP ban / host deny** — your credential was never evaluated |
| `Connection timed out` / no route | Never reached sshd | Network/DNS/port, not auth |

**The progression is the tell.** Early attempts get a clean `Permission denied` (auth reached). After N failures, the *same command with the same password* flips to `Connection closed … port 22` with no prompt. That flip **is fail2ban engaging** — not a new problem with your password.

---

### Probe for the ban WITHOUT spending another failed auth

This is the key move. Drive the native client through `expect` and branch on **where** it dies. If the connection closes before the password prompt, you bail **without sending credentials** — so the probe adds **zero** failed-auth attempts and can't extend the ban:

```expect
# pen_connect.exp — detect ban vs auth, then (if open) run pwd/ls
set timeout 25
set fp [open "/tmp/pw" r]; set pw [read -nonewline $fp]; close $fp
spawn sftp -o StrictHostKeyChecking=yes -o NumberOfPasswordPrompts=1 \
           -o PubkeyAuthentication=no user@host.example
expect {
  -re "(?i)password:"           { send -- "$pw\r" }
  "Connection closed"           { puts "\n>>> CLOSED_PRE_AUTH (firewall/fail2ban — no auth sent)"; exit 2 }
  -re "(?i)permission denied"    { puts "\n>>> DENIED_EARLY"; exit 4 }
  timeout                        { puts "\n>>> TIMEOUT_BEFORE_PROMPT"; exit 3 }
}
expect {
  "sftp>"                        { send -- "pwd\r"; expect "sftp>"; send -- "bye\r"; puts "\n>>> CONNECTED_OK" }
  -re "(?i)permission denied"    { puts "\n>>> AUTH_DENIED (password rejected)"; exit 5 }
  "Connection closed"           { puts "\n>>> CLOSED_AFTER_PW"; exit 6 }
  timeout                        { puts "\n>>> TIMEOUT_AFTER_PW"; exit 7 }
}
expect eof
```

`CLOSED_PRE_AUTH` = banned (wait it out). `AUTH_DENIED` = the credential really is wrong. `CONNECTED_OK` = you're in. One run, definitive, ban-safe.

---

### Verify the password is correct *independently* (don't trust the keyboard)

Before blaming the password, confirm what the *working* GUI client actually stores. macOS keeps SFTP passwords in the login Keychain:

```bash
# Run this YOURSELF (interactively). An AGENT scanning the keychain will likely
# be blocked by the safety classifier as credential harvesting — and rightly so.
security find-internet-password -s host.example -a user -w
```

Compare it to what you've been typing **without printing either** — hash both:

```bash
printf '%s' "$TYPED" | shasum -a 256      # vs the keychain value's hash
```

Matching hashes = the password is fine and the rejection was the ban. (In the source incident the hashes matched exactly — the password was never the problem.)

---

### Recovery

1. **Stop all attempts — from the CLI *and* the GUI client** (same IP, same ban; GUI retries extend it too).
2. **Wait** the bantime. Strato/typical fail2ban jails: **10–30 min** (sometimes 1 h). Don't poll.
3. **One** attempt after the wait. `CONNECTED_OK` → it was purely the ban. `AUTH_DENIED` → now debug the credential (SSH not enabled for the package? SSH password ≠ FTP password? key not authorized?).

---

### Pitfalls

- **Don't keep hammering with `sshpass`/`lftp`/`rsync`.** Each failed (or even pre-auth-dropped) attempt can reset the fail2ban `findtime` window and lengthen the ban. The `expect` probe above is the only thing you should run while suspecting a ban — and only once.
- **Special characters wreck password passing.** `&`, `#`, `%` break `lftp`'s URL/command parser (it read `pass&rb#7` as "background `pass`, comment `rb`"); in lftp use `user 'name' 'pass'` with single quotes. And **zsh does not word-split unquoted variables** like bash — `H='-H Origin:…'; curl $H` passes one mangled arg, so your header never goes. Always feed the password from a `chmod 600` file (`sshpass -f`, or `read` in expect), never via `argv` (visible in `ps`) or an unquoted shell var.
- **`curl`'s default User-Agent trips bot filters.** If you're testing a download endpoint that filters `curl|wget|python-requests`, a "0 increments" result may be the filter working, not a bug — pass `-A "Mozilla/5.0 …"`.
- **A known_hosts entry does *not* prove a prior successful login.** The host key is saved during key exchange, *before* auth — `accept-new` on a failed attempt still records it. Don't read "host is known" as "I logged in before."
- **The agent angle:** programmatic keychain scans (`security find-…-password` across fallbacks) read as credential exfiltration to safety tooling and get blocked. Have the human read their own keychain; the agent should diagnose, not harvest.

---

### Composes with

- Cookbook **#46** / **#49** (PHP download counter / feedback form) — the things you're trying to *deploy* when you hit this.
- Cookbook **#29** (`29_web-strato-hosting.md`) — Strato-specific deploy gotchas; add "SSH may need enabling; SSH password can differ from FTP" there.
