#!/bin/bash
#
# Claudestrator Installer
# https://github.com/bladehstream/claudestrator
#
# Usage:
#   cd my-project
#   git clone https://github.com/bladehstream/claudestrator
#   claudestrator/install.sh
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

# Get script directory (where claudestrator repo was cloned)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TARGET_DIR="$(dirname "$SCRIPT_DIR")"

echo ""
echo "Claudestrator Installer"
echo "======================="
echo ""
echo "Source: $SCRIPT_DIR"
echo "Target: $TARGET_DIR"
echo ""

# Check we're not running from inside the target
if [ "$SCRIPT_DIR" = "$TARGET_DIR" ]; then
    echo -e "${RED}Error: Clone the repo into a subdirectory first${NC}"
    echo "  git clone https://github.com/bladehstream/claudestrator"
    echo "  claudestrator/install.sh"
    exit 1
fi

# Create target directories
echo "Creating directories..."
mkdir -p "$TARGET_DIR/.claude"
mkdir -p "$TARGET_DIR/.orchestrator/complete"
mkdir -p "$TARGET_DIR/.orchestrator/reports"

# Copy commands
echo "Installing commands..."
cp -r "$SCRIPT_DIR/commands" "$TARGET_DIR/.claude/"

# Copy prompts
echo "Installing prompts..."
cp -r "$SCRIPT_DIR/prompts" "$TARGET_DIR/.claude/"

# Copy skills
echo "Installing skills..."
cp -r "$SCRIPT_DIR/skills" "$TARGET_DIR/.claude/"

# Copy CLAUDE.md
echo "Installing CLAUDE.md..."
if [ -f "$SCRIPT_DIR/templates/CLAUDE.md" ]; then
    cp "$SCRIPT_DIR/templates/CLAUDE.md" "$TARGET_DIR/.claude/CLAUDE.md"
else
    echo -e "${YELLOW}Warning: templates/CLAUDE.md not found${NC}"
fi

# Copy settings.json if it doesn't exist
if [ ! -f "$TARGET_DIR/.claude/settings.json" ]; then
    if [ -f "$SCRIPT_DIR/templates/settings.json" ]; then
        echo "Installing settings.json..."
        cp "$SCRIPT_DIR/templates/settings.json" "$TARGET_DIR/.claude/settings.json"
    fi
fi

# Copy hooks
if [ -d "$SCRIPT_DIR/templates/hooks" ]; then
    echo "Installing hooks..."
    mkdir -p "$TARGET_DIR/.claude/hooks"
    cp -r "$SCRIPT_DIR/templates/hooks/"* "$TARGET_DIR/.claude/hooks/" 2>/dev/null || true
    chmod +x "$TARGET_DIR/.claude/hooks/"*.sh 2>/dev/null || true
    chmod +x "$TARGET_DIR/.claude/hooks/"*.py 2>/dev/null || true
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Claudestrator installed successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Next steps:"
echo "  1. Start Claude Code in: $TARGET_DIR"
echo "  2. Run /prdgen to generate a PRD"
echo "  3. Run /orchestrate to start"
echo ""
echo -e "${YELLOW}Do NOT run /init - it will overwrite this configuration${NC}"
echo ""
