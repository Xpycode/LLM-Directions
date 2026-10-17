#!/usr/bin/env bash
# Headless fixtures only; no live deployment or application control.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
python3 verification/lean/measure.py --check-baseline
bash verification/lean/test-session-index.sh
bash verification/lean/test-guidance-index.sh
bash verification/lean/test-legacy-install.sh
bash verification/lean/test-safety/check.sh
python3 verification/lean/test-task-state.py
python3 verification/lean/test-status-references.py
bash verification/lean/test-deployment.sh
python3 verification/lean/measure.py --routing
python3 verification/lean/test-integration.py
for script in scripts/sync-session-index.sh scripts/gen-directions-index.sh install-directions.sh deploy-codex.sh redeploy.sh verification/lean/test-*.sh verification/lean/test-safety/check.sh verification/lean/run-checks.sh; do
  bash -n "$script"
done
git diff --check
printf '%s\n' 'PASS: integrated local fixtures and shell syntax; E1 host acceptance remains separate'
