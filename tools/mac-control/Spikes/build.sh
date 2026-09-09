#!/bin/bash
# Compilation only; run after agreeing the foreground test window per task 1.3.
set -euo pipefail
umask 077
spike_source=$(cd "$(dirname "$0")" && pwd)
spike_output=$(mktemp -d "${TMPDIR:-/tmp}/directions-stop-build.XXXXXX")
spike_app="$spike_output/StopSpikeTarget.app"
spike_sink="$spike_output/StopSpikeFocusSink.app"
spike_target="$(uname -m)-apple-macosx$(sw_vers -productVersion)"
mkdir -p "$spike_app/Contents/MacOS" "$spike_sink/Contents/MacOS" "$spike_output/module-cache"

xcrun swiftc -parse-as-library -swift-version 6 -strict-concurrency=complete \
  -target "$spike_target" \
  -module-cache-path "$spike_output/module-cache" \
  "$spike_source/StopSpikeWorker.swift" -o "$spike_output/StopSpikeWorker"
xcrun swiftc -parse-as-library -swift-version 6 -strict-concurrency=complete \
  -target "$spike_target" \
  -module-cache-path "$spike_output/module-cache" \
  "$spike_source/StopSpikeTarget.swift" -o "$spike_app/Contents/MacOS/StopSpikeTarget"
xcrun swiftc -parse-as-library -swift-version 6 -strict-concurrency=complete \
  -target "$spike_target" \
  -module-cache-path "$spike_output/module-cache" \
  "$spike_source/StopSpikeFocusSink.swift" -o "$spike_sink/Contents/MacOS/StopSpikeFocusSink"

python3 - "$spike_output" <<'PY'
import hashlib
import json
from pathlib import Path
import plistlib
import sys

root = Path(sys.argv[1])
with (root / "StopSpikeTarget.app/Contents/Info.plist").open("wb") as output:
    plistlib.dump({"CFBundleIdentifier": "com.lucesumbrarum.Directions.StopSpikeTarget",
                  "CFBundleExecutable": "StopSpikeTarget", "CFBundleName": "Directions Stop Spike",
                  "CFBundlePackageType": "APPL", "CFBundleVersion": "1",
                  "NSHighResolutionCapable": True, "NSPrincipalClass": "NSApplication"}, output)
with (root / "StopSpikeFocusSink.app/Contents/Info.plist").open("wb") as output:
    plistlib.dump({"CFBundleIdentifier": "com.lucesumbrarum.Directions.StopSpikeFocusSink",
                  "CFBundleExecutable": "StopSpikeFocusSink", "CFBundleName": "Directions Focus Sink",
                  "CFBundlePackageType": "APPL", "CFBundleVersion": "1",
                  "NSHighResolutionCapable": True, "NSPrincipalClass": "NSApplication"}, output)
artifacts = {"worker": "StopSpikeWorker",
             "target": "StopSpikeTarget.app/Contents/MacOS/StopSpikeTarget",
             "focusSink": "StopSpikeFocusSink.app/Contents/MacOS/StopSpikeFocusSink"}
with (root / "artifacts.json").open("x") as output:
    json.dump({key: hashlib.sha256((root / path).read_bytes()).hexdigest()
               for key, path in artifacts.items()}, output, indent=2)
print(root)
PY
# No install, signing identity change, TCC prompt, launch or desktop action here.
