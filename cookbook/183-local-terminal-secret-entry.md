# 183 — Open a local Terminal prompt for private credential entry

**Tags:** credentials, hidden input, Terminal, Keychain, security, SFTP, passwords, tokens, Codex, data entry

**Extracted from:** MacroPorn (2026-09-09), `03_Scripts/setup-deploy.command`; owner explicitly requested reuse after approving the entry experience.

## When to use

When an assistant needs the user to enter a password, token or similar private value
for later use, prepare a local interactive setup and open it in the user's Terminal.
The user types there, outside chat and captured tool output. On macOS, prefer
Keychain for retained secrets. This is the owner's preferred experience for similar
private data-entry tasks across projects.

## The workflow

1. Inspect the existing credential mechanism without displaying stored secrets.
2. Prepare a small executable `.command` file. Explain each field in plain language;
   collect host/account identifiers there too so the user can finish in one place.
3. Require a real interactive terminal. Let the credential store prompt directly
   for the secret; do not ask for it in chat, an agent input form, or a tool PTY.
4. Validate with mocks or dummy credentials first. Check failure handling, file
   permissions and Git ignore coverage without accessing real secrets.
5. Open the exact prepared file in the user's Terminal. Follow the host's normal
   approval policy; the user's request to save credentials authorizes this setup.
6. Report success without printing any secret. Keep the window open until Return,
   then ask the user to report completion in chat.
7. Distinguish saved credentials from verified connectivity and completed deployment.
   Entering credentials must not silently start an upload or publish action.

## Minimal macOS example

Save as an executable `setup-credentials.command`. This is an entry-only example;
the source implementation also validates identifiers and atomically saves local settings.

```python
#!/usr/bin/env python3
import subprocess
import sys

if sys.platform != 'darwin' or not sys.stdin.isatty():
    sys.exit('Open this file in macOS Terminal.')

account = input('SFTP username: ').strip()
if not account:
    sys.exit('Username is required.')
print('Enter the password at the hidden Keychain prompt.')
result = subprocess.run([
    '/usr/bin/security', 'add-generic-password',
    '-U', '-s', 'example-site-sftp', '-a', account,
    '-l', 'Example site SFTP', '-w',
])
print('Saved in Keychain.' if result.returncode == 0 else 'Not saved.')
input('Press Return to close. ')
sys.exit(result.returncode)
```

Open with `open -a Terminal /absolute/path/setup-credentials.command` after making
the file executable. **`-w` must be the last argument, with no password value**:
`security` then asks for it directly without echoing. Verified against local
`security help add-generic-password` during implementation. `-U` updates the matching
entry; tell the user when rerunning setup will replace an existing credential.

## Boundaries that make this work

- Do not put the secret in command arguments, environment overrides, shell history,
  tracing (`set -x`), logs, screenshots, clipboard reads, or temporary files.
- An agent-owned tool PTY can capture terminal input/output. Opening a separate
  user-facing Terminal window is the key interaction difference. Do not capture it.
- For other secret stores, use their native hidden prompt where possible. A hidden
  `getpass` prompt alone does not guarantee safe subsequent storage or logging.
- Keep settings free of passwords and tokens. Use mode 0600 and Git ignore rules
  for local account metadata; document that Git ignore is not encryption.
- Keychain also stores the account name: prefer retrieving both credential halves
  there when practical (see #180). MacroPorn initially duplicates the username in
  its ignored settings to identify the exact service/account pair.
- Future scripts should retrieve secrets internally only when needed and never
  print them into tool output. Saving securely does not excuse unsafe retrieval.
- No secret was inspected to validate this pattern. Mocked checks covered prompt
  arguments, settings permissions, absence of passwords from settings and preservation
  of existing settings after Keychain failure. Owner approved the local entry UX;
  that approval alone is not evidence of a successful server login.

Related: [#180 — Keychain credential storage](180-keychain-holds-both-credential-halves.md),
[security guidance](../54_security-rules.md).
