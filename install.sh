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

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

# Get script directory (where claudestrator repo was cloned)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TARGET_DIR="$(dirname "$SCRIPT_DIR")"

# Copy directory contents, skipping symlinks at destination
# Usage: copy_dir <source_dir> <dest_dir>
copy_dir() {
    local src="$1"
    local dst="$2"
    local copied=0
    local skipped=0

    # Create destination if it doesn't exist
    mkdir -p "$dst"

    # Process each item in source directory
    for item in "$src"/*; do
        [ -e "$item" ] || continue  # Skip if glob didn't match

        local name=$(basename "$item")
        local dest_path="$dst/$name"

        # Skip if destination is a symlink
        if [ -L "$dest_path" ]; then
            skipped=$((skipped + 1))
            continue
        fi

        if [ -d "$item" ]; then
            # Recursively copy directory
            copy_dir "$item" "$dest_path"
        else
            # Copy file (force overwrite if exists)
            cp -f "$item" "$dest_path"
            copied=$((copied + 1))
        fi
    done

    if [ $skipped -gt 0 ]; then
        echo "  (skipped $skipped symlinks in $(basename "$dst"))"
    fi
}

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
mkdir -p "$TARGET_DIR/.claudestrator"
mkdir -p "$TARGET_DIR/.orchestrator/complete"
mkdir -p "$TARGET_DIR/.orchestrator/reports"

# Copy commands (skip symlinks)
echo "Installing commands..."
copy_dir "$SCRIPT_DIR/commands" "$TARGET_DIR/.claude/commands"

# Copy prompts (skip symlinks)
echo "Installing prompts..."
copy_dir "$SCRIPT_DIR/prompts" "$TARGET_DIR/.claude/prompts"

# Copy skills (skip symlinks)
echo "Installing skills..."
copy_dir "$SCRIPT_DIR/skills" "$TARGET_DIR/.claude/skills"

# Copy CLAUDE.md (skip if symlink)
echo "Installing CLAUDE.md..."
if [ -f "$SCRIPT_DIR/templates/CLAUDE.md" ]; then
    if [ -L "$TARGET_DIR/.claude/CLAUDE.md" ]; then
        echo "  (skipped - is symlink)"
    else
        cp -f "$SCRIPT_DIR/templates/CLAUDE.md" "$TARGET_DIR/.claude/CLAUDE.md"
    fi
else
    echo -e "${YELLOW}Warning: templates/CLAUDE.md not found${NC}"
fi

# Copy settings.json if it doesn't exist (never overwrite user settings)
if [ ! -e "$TARGET_DIR/.claude/settings.json" ]; then
    if [ -f "$SCRIPT_DIR/templates/settings.json" ]; then
        echo "Installing settings.json..."
        cp "$SCRIPT_DIR/templates/settings.json" "$TARGET_DIR/.claude/settings.json"
    fi
else
    echo "Skipping settings.json (already exists)"
fi

# Copy hooks
if [ -d "$SCRIPT_DIR/templates/hooks" ]; then
    echo "Installing hooks..."
    mkdir -p "$TARGET_DIR/.claude/hooks"
    copy_dir "$SCRIPT_DIR/templates/hooks" "$TARGET_DIR/.claude/hooks"
    chmod +x "$TARGET_DIR/.claude/hooks/"*.sh 2>/dev/null || true
    chmod +x "$TARGET_DIR/.claude/hooks/"*.py 2>/dev/null || true
fi

# Copy issue_reporter (required by /issue command)
if [ -d "$SCRIPT_DIR/issue_reporter" ]; then
    echo "Installing issue_reporter..."
    copy_dir "$SCRIPT_DIR/issue_reporter" "$TARGET_DIR/.claudestrator/issue_reporter"
fi

# Copy prd_generator (required by /prdgen command)
if [ -d "$SCRIPT_DIR/prd_generator" ]; then
    echo "Installing prd_generator..."
    copy_dir "$SCRIPT_DIR/prd_generator" "$TARGET_DIR/.claudestrator/prd_generator"
fi

# Copy templates to .claudestrator (required by /dashboard, /issue, etc.)
if [ -d "$SCRIPT_DIR/templates" ]; then
    echo "Installing claudestrator templates..."
    copy_dir "$SCRIPT_DIR/templates" "$TARGET_DIR/.claudestrator/templates"
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
