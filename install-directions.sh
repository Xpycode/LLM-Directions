#!/usr/bin/env bash
# Retired compatibility entry point. Intentionally performs no writes.
set -euo pipefail
if [ "$#" -gt 1 ] || { [ "$#" -eq 1 ] && [ "$1" != '--help' ] && [ "$1" != '-h' ]; }; then
  echo 'Unsupported argument. Use --help for supported deployment commands.' >&2
  exit 2
fi
INSTALL_MASTER="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cat <<EOF
install-directions.sh is retired; nothing was installed or changed.
Codex preview: bash "$INSTALL_MASTER/deploy-codex.sh" --dry-run
Claude preview: bash "$INSTALL_MASTER/redeploy.sh" --dry-run
Vibe preview: bash "$INSTALL_MASTER/deploy-vibe.sh" --dry-run
After reviewing the preview, invoke the chosen script without --dry-run to install.
Claude redeploy replaces CLAUDE.md with a backed-up rendered template. Preserve personal
instructions with --skip-claude-md; --skip-settings preserves existing settings.
Codex and Vibe refresh their managed block; --skip-agents-md skips that block.
This entry point exits 1 without arguments, 0 for help, 2 for invalid arguments.
EOF
if [ "$#" -eq 1 ]; then exit 0; fi
exit 1
