#!/bin/bash
# Install Claude Code skills globally via skills.sh
# Run on any Mac to get the same skill set
#
# Usage: ./install-skills.sh
#
# Requires: Node.js (npx)

set -e

echo "=== Installing Claude Code Skills ==="
echo ""

# Check for npx
if ! command -v npx &> /dev/null; then
    echo "Error: npx not found. Install Node.js first."
    exit 1
fi

# Skill collections to install
SKILLS=(
    "avdlee/SwiftUI-Recipes"
    "avdlee/swift-concurrency"
    "vercel-labs/agent-skills"
    "anthropics/skills"
    "nextlevelbuilder/ui-ux-pro-max"
    "wshobson/agents"
    "giuseppe-trisciuoglio/developer-kit"
    "obra/superpowers"
    "remotion-dev/skills"
    "boristane/agent-skills"
)

echo "Installing ${#SKILLS[@]} skill collections..."
echo ""

for skill in "${SKILLS[@]}"; do
    echo "→ $skill"
    npx skills add "$skill" --yes --global --agent claude-code 2>/dev/null || {
        echo "  (already installed or unavailable)"
    }
done

echo ""
echo "=== Installation Complete ==="
echo ""
echo "Installed skills:"
npx skills list --global 2>/dev/null | head -20
echo "..."
echo ""
echo "Total: $(npx skills list --global 2>/dev/null | wc -l | tr -d ' ') skills"
echo ""
echo "Skills auto-activate based on context. Update with: npx skills update"
