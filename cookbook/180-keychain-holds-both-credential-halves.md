# 180 — One Keychain entry holds *both* credential halves; netrc can't (it keys by host)

**Tags:** macOS Keychain, security add-generic-password, find-generic-password, ~/.netrc, lftp, sftp, deploy credentials, secrets out of git, multiple accounts same host, acct blob, Strato

**Extracted from:** PRIVAT (2026-08-24), after LUCESUMBRARUM's password ended up inline for exactly this reason

## The problem

`~/.netrc` is keyed by **host**:

```
machine NNNNNNNN.ssh.wN.strato.hosting
  login  stuAAAAAAAAA
  password ...
```

One `machine` block, one `login`. Shared hosting hands out **several SFTP users on one hostname** —
one per site, or a jailed deploy user beside an SSH-enabled one. The moment a second project needs
the same host under a different account, netrc has nowhere to put it.

What happens next is predictable, and it happened here: the second project gave up and inlined the
password in `ship.sh` and in its `CLAUDE.md`. Its own audit note records the reasoning — *"netrc
cannot hold it: netrc keys by host, and this host already has a different account registered"* —
which is an accurate diagnosis and the wrong conclusion. The password then sat in plaintext for
months, was flagged by an audit, survived the audit, and was eventually read into an LLM transcript.

## The fix

The macOS Keychain keys by **service name**, which you choose. Two accounts on one host are two
entries. And a generic-password entry carries an **account** field alongside the secret — so it
holds *both* halves, and the username never enters the repo either.

```bash
# Once per Mac. -w with no value prompts, so nothing lands in shell history.
security add-generic-password -s privat-strato   -a stuBBBBBBBBB -w
security add-generic-password -s luces-strato    -a stuAAAAAAAAA -w   # same host, no conflict
```

Read both halves back at deploy time:

```bash
# account = SFTP username, secret = password. Neither exists in the tree.
SFTP_USER="$(security find-generic-password -s "$SERVICE" \
             | awk -F'"' '/"acct"<blob>/{print $4}')"
SFTP_PASS="${STRATO_PASS:-$(security find-generic-password -s "$SERVICE" -w)}"

[[ -n "$SFTP_USER" && -n "$SFTP_PASS" ]] || {
  echo "no Keychain entry '$SERVICE' — run: security add-generic-password -s $SERVICE -a <user> -w" >&2
  exit 1
}
```

The `${STRATO_PASS:-...}` override keeps CI and one-off runs working without a Keychain.

## Why the username matters too

A dedicated deploy username is half a credential and identifies the hosting account. Conventional
advice ("secrets in netrc, identifiers in a gitignored `.env`") leaves it in the tree, where a
gitignore typo, a `git add -f`, or making a previously-untracked folder into a repo publishes it.
Since the Keychain entry already carries an account field, keeping it there costs nothing.

Non-secret connection details still belong in a gitignored env file, with an `.example` committed:

```bash
STRATO_HOST="XXXXXXXX.ssh.w1.strato.hosting"
KEYCHAIN_SERVICE="privat-strato"
REMOTE_DIR="/"
```

## Trade-offs

| | `~/.netrc` (#99) | Keychain (this) |
|---|---|---|
| Keyed by | host | service name you pick |
| Two accounts, one host | **impossible** | fine |
| Username location | connection URL / repo `.env` | inside the entry |
| Read by other tools | yes — curl, ftp, lftp natively | no, script must fetch it |
| Portable off macOS | yes | no (`security` is macOS-only) |

netrc stays the better choice when a tool reads it natively and there is one account per host.
Reach for the Keychain the moment a host carries more than one account — the alternative isn't
netrc, it's a plaintext password in a script.

## Migrating an already-exposed password

Order matters: the old value is compromised the moment it was committed or pasted.

1. **Rotate first** in the hosting panel. Moving a leaked secret to the Keychain protects nothing.
2. Add the new one via `security add-generic-password`.
3. Strip it from every copy — script, `CLAUDE.md`, `.claude/settings.local.json`, docs.
4. `git log -S '<fragment>' --all` — if it was ever committed, the history still has it.

## Related

- **#99** — the netrc multi-site deploy this supersedes for the multiple-accounts-per-host case;
  its "user in the URL, password in netrc" insight still applies, since `lftp`'s ssh backend takes
  the username from the URL regardless of where you stored it.
- **#179** — the exclusion half of the same deploy script.
