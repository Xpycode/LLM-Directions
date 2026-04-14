## launchd Node.js Service + Scheduled Tasks

### KeepAlive Server Agent

**Source:** `X-STATUS/launchd/com.sim.x-status-server.plist`

Use for a Node.js server that should always be running. Restarts automatically if it dies.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.yourname.your-server</string>

    <key>ProgramArguments</key>
    <array>
        <string>/opt/homebrew/bin/node</string>
        <string>server.js</string>
    </array>

    <key>WorkingDirectory</key>
    <string>/Users/yourname/path/to/project</string>

    <key>KeepAlive</key>
    <true/>

    <key>RunAtLoad</key>
    <true/>

    <key>StandardOutPath</key>
    <string>/tmp/your-server.log</string>

    <key>StandardErrorPath</key>
    <string>/tmp/your-server.err</string>

    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin</string>
    </dict>
</dict>
</plist>
```

**Key fields:**
- `KeepAlive: true` — restarts if process exits
- `RunAtLoad: true` — starts when agent is loaded (login)
- `WorkingDirectory` — critical for relative paths in your script
- `EnvironmentVariables.PATH` — launchd doesn't inherit shell PATH; `/opt/homebrew/bin` needed for Apple Silicon

### Scheduled Task Agent (cron replacement)

**Source:** `X-STATUS/launchd/com.sim.x-status-collector.plist`

Use for periodic tasks like data collection, backups, cleanup.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.yourname.your-task</string>

    <key>ProgramArguments</key>
    <array>
        <string>/opt/homebrew/bin/node</string>
        <string>scripts/your-task.js</string>
    </array>

    <key>WorkingDirectory</key>
    <string>/Users/yourname/path/to/project</string>

    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>9</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>

    <key>RunAtLoad</key>
    <false/>

    <key>StandardOutPath</key>
    <string>/tmp/your-task.log</string>

    <key>StandardErrorPath</key>
    <string>/tmp/your-task.err</string>

    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin</string>
    </dict>
</dict>
</plist>
```

**Key fields:**
- `StartCalendarInterval` — fires at specific time (like cron). Omit `Hour` for every-hour, omit both for every-minute
- `RunAtLoad: false` — don't run immediately on load, only on schedule

**Common schedules:**
```xml
<!-- Every day at 9am -->
<key>Hour</key><integer>9</integer>
<key>Minute</key><integer>0</integer>

<!-- Every hour on the hour -->
<key>Minute</key><integer>0</integer>

<!-- Every Monday at 8am -->
<key>Weekday</key><integer>1</integer>
<key>Hour</key><integer>8</integer>
<key>Minute</key><integer>0</integer>
```

### Install / Uninstall Scripts

**Source:** `X-STATUS/scripts/install.sh`, `X-STATUS/scripts/uninstall.sh`

```bash
#!/bin/bash
set -e

AGENTS_DIR="$HOME/Library/LaunchAgents"
SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PLIST_DIR="$SCRIPT_DIR/launchd"

# Detect node
if [ -x /opt/homebrew/bin/node ]; then
    echo "Found node at: /opt/homebrew/bin/node"
elif [ -x /usr/local/bin/node ]; then
    echo "Found node at: /usr/local/bin/node"
else
    echo "WARNING: node not found in expected locations"
fi

# Install each plist
for plist in "$PLIST_DIR"/*.plist; do
    name=$(basename "$plist")
    label="${name%.plist}"

    # Unload if already loaded (idempotent reinstall)
    launchctl unload "$AGENTS_DIR/$name" 2>/dev/null || true

    cp "$plist" "$AGENTS_DIR/"
    launchctl load "$AGENTS_DIR/$name"
    echo "Loaded $name"
done
```

```bash
#!/bin/bash
set -e

AGENTS_DIR="$HOME/Library/LaunchAgents"

for label in com.sim.x-status-server com.sim.x-status-collector; do
    plist="$AGENTS_DIR/$label.plist"
    launchctl unload "$plist" 2>/dev/null || true
    rm -f "$plist"
    echo "Removed $label"
done
```

### Gotchas

1. **Apple Silicon PATH** — `/opt/homebrew/bin` is NOT in launchd's default PATH. Always set `EnvironmentVariables.PATH` explicitly.
2. **Working directory** — launchd defaults to `/`. Always set `WorkingDirectory`.
3. **Logs in /tmp** — use `/tmp/` for logs (auto-cleaned on reboot). For persistent logs, use `~/Library/Logs/`.
4. **Idempotent install** — always `unload` before `load` when reinstalling. Use `|| true` to suppress errors if not loaded.
5. **Debug** — `launchctl list | grep your-label` shows PID + exit code. Exit code 0 = running, non-zero = crashed.
6. **File permissions** — plist must be readable by your user (644). Scripts must be executable (755).
