#!/bin/bash
# Build only the opt-in read-only inventory library. Never run its native query.
set -euo pipefail
umask 077
inventory_source=$(cd "$(dirname "$0")" && pwd -P)
inventory_output=$(mktemp -d /private/tmp/directions-inventory.XXXXXX)
xcrun clang -std=c11 -Wall -Wextra -Werror -dynamiclib \
  "$inventory_source/recovery_inventory.c" -o "$inventory_output/recovery_inventory.dylib"
python3 -B - "$inventory_output/recovery_inventory.dylib" <<'PY'
import hashlib
import json
from pathlib import Path
import sys

path = Path(sys.argv[1]).resolve(strict=True)
print(json.dumps(dict(library_path=str(path), library_sha256=hashlib.sha256(path.read_bytes()).hexdigest())))
PY
